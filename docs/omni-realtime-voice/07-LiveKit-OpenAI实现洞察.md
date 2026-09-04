# 07 LiveKit Agents × OpenAI：他们是怎么实现的

入口文档：[OpenAI and LiveKit](https://docs.livekit.io/agents/integrations/openai/)
（`docs.livekit.io/agents/integrations/openai/`）。

定位先说清楚：**LiveKit 不是 GPT‑Live，也不是全双工模型。**
它是开源的 **Agents 编排框架**：用户侧走 LiveKit WebRTC，模型侧走 OpenAI
Realtime WebSocket；中间的 worker 负责媒体转换、会话状态、打断截断、工具转发
和前端字幕对齐。OpenAI 负责"听懂并说话"，LiveKit 负责"把这段语音会话接到
真实产品里"。

对照本目录前几章：04 讲的是 OpenAI Realtime API 的会话/事件模型；本章讲的是
**谁把那套事件接到 WebRTC 房间、接到 Agent 工作流**。两者叠在一起，才是业界
今天真正能上线的"第二代 S2S + 产品外壳"。

源码以 `livekit/agents` 主线为准，核心文件：

- 插件：`livekit-plugins-openai/.../realtime/realtime_model.py`
  （`RealtimeModel` + `RealtimeSession`）
- 编排：`livekit-agents/.../voice/agent_session.py`、`agent_activity.py`
- 示例：`examples/voice_agents/realtime_turn_detector.py`

## 一、官方自己怎么定义这条集成

集成页把 LiveKit Agents 写成一座桥：

```text
App / Phone  ══ LiveKit WebRTC ══▶  Agent worker
                                       ║
                                       ║ WebSocket
                                       ▼
                                 OpenAI Realtime API
```

官方列出的附加价值（相对"自己直连 Realtime API"）是产品层，不是模型层：

| LiveKit 宣称补上的 | 实际落在哪一层 |
| --- | --- |
| 噪声消除一行接入 | RoomIO 音频输入（BVC），在送进模型之前 |
| SIP 电话 | LiveKit 媒体基础设施，与模型无关 |
| 打断时自动截断上下文 | AgentActivity + `conversation.item.truncate` |
| 文本与音频播放对齐 | Realtime 文本 delta 同步到 WebRTC 播放时钟 |
| 工具转发给前端 | function call 在 worker 执行，也可 RPC 到 client |

OpenAI 在 LiveKit 里出现四次，不要混成一条管道：

| 组件 | 用途 | 典型接入 |
| --- | --- | --- |
| **Realtime API** | 语音进、语音出的 S2S | `llm=openai.realtime.RealtimeModel(...)` |
| **Chat LLM** | 级联管道里的文本脑 | `llm="openai/chat-latest"` 或 plugin LLM |
| **STT** | `gpt-realtime-whisper` / `gpt-4o-transcribe` | `stt=openai.STT(...)` |
| **TTS** | `gpt-4o-mini-tts` 等 | `tts=openai.TTS(...)` |

后面默认讨论第一条：**Realtime 作为 `llm=`**。这是他们和 OpenAI 实时语音
最深的耦合点。

## 二、三种管道，Realtime 只是其中一种 `llm`

LiveKit 把语音 Agent 收成三种管道（[Pipeline types](https://docs.livekit.io/agents/models/pipelines/)），
对开发者暴露的却是**同一个** `AgentSession`：

| 管道 | 配置形态 | 延迟 | 能做的 | 代价 |
| --- | --- | --- | --- | --- |
| **STT‑LLM‑TTS 级联** | 分别填 `stt` / `llm` / `tts` | 中 | 可审计、可 `say()` 念稿、工具成熟、实时字幕 | 韵律在 STT 处丢失 |
| **纯 Realtime** | 只填 `llm=RealtimeModel()` | 最快 | 听语气、输出带情感 | 字幕滞后、不能精确念稿、难审计 |
| **半级联 half-cascade** | `RealtimeModel(modalities=["text"])` + 独立 TTS | 中 | 输入仍听音频，输出完全可控 | 两套模型；并非所有 Realtime 提供商支持纯文本输出 |

关键设计：**Realtime 模型不是第三套 Session 类型，而是实现了 `llm.RealtimeModel`
接口的 LLM。** `AgentSession` 发现 `isinstance(llm, RealtimeModel)` 就走
`_rt_session` 双向音频路径，否则走 STT→LLM→TTS。编排、SpeechHandle 队列、
工具、多 Agent 交接，三条管道共用。

他们自己的生产默认仍是级联——"most production agents"走 STT‑LLM‑TTS。
Realtime 被定位为"延迟和表现力优先"。半级联是对 OpenAI 一个已知坑的工程绕过：
**往 Realtime 会话灌长文本历史后，模型容易改用纯文本回答**；官方建议改成
text 模态 + 独立 TTS（可用 Azure OpenAI TTS 保住同一套音色）。

这和 01 章的三代架构对得上：LiveKit 今天交付的是**第二代 S2S 的产品化**，
外加一条可插拔的第一代级联。它没有第三代全双工模型，也没有 GPT‑Live 的
说/想双时钟。

## 三、运行时分层：Session 编排，Activity 干活，Plugin 翻译协议

### 3.1 两级编排

| 对象 | 职责 |
| --- | --- |
| **`AgentSession`** | 房间 I/O、Agent 切换、对外状态与事件、生命周期 |
| **`AgentActivity`** | 单个 Agent 的运行时：音频识别、语音调度队列 `_speech_q`、RealtimeSession、工具执行、假打断恢复 |

一个 Session 同一时刻只有一个 active Agent；Workflows 做交接时，旧 Activity
drain，新 Activity 接管。这是"多专家工作流"，不是全双工里的委托时钟。

### 3.2 Agent / User 对外只暴露很粗的状态

Session 生命周期：

```text
initializing ──start()──▶ listening
listening ──用户说完──▶ thinking ──首包音频──▶ speaking
speaking ──说完 / 被打断──▶ listening
```

| 角色 | 公开状态 | 事件 |
| --- | --- | --- |
| Agent | `initializing` / `listening` / `thinking` / `speaking` | `agent_state_changed` |
| User | `speaking` / `listening` / `away` | `user_state_changed` |

`away` 是产品态：默认 15 s 双方都静音后标用户离开，用来做"还在吗"回访，
不是轮次模型里的 MUTED。

Realtime 路径上，`thinking → speaking` 的触发点是**第一帧音频（或第一段文本）
到达播放器**，不是 `response.created`。源码里 `_AudioOutput.first_frame_fut`
的回调才把 agent 标成 `speaking`。这是正确的产品时钟：用户听到声音才算在说。

### 3.3 插件声明能力，编排按能力分支

`RealtimeModel` 构造时向框架登记 `llm.RealtimeCapabilities`：

| 能力位 | OpenAI 插件的取值 | 编排层怎么用 |
| --- | --- | --- |
| `turn_detection` | `create_response is not False` 则为真 | 为真则把打断权交给模型 |
| `can_disable_turn_detection` | 调用方没显式传 `turn_detection` 时为真 | 才能改用 LiveKit TurnDetector |
| `audio_output` | `"audio" in modalities` | 假则走半级联 TTS |
| `user_transcription` | 配置了 input transcription | 有则跳过并行 STT 的字幕 |
| `message_truncation` | 恒真 | 打断后可 `conversation.item.truncate` |
| `auto_tool_reply_generation` | 假 | 工具结果要由框架再 `response.create` |

这是整套集成最重要的抽象：**提供商差异收进 capabilities，AgentActivity 不写
OpenAI 专用分支**（Gemini Live、Nova Sonic 走同一套）。

## 四、OpenAI 插件到底做了什么

文件：`realtime_model.py`。可以看成一台**协议翻译机**。

### 4.1 连接：HTTP(S) 改 WS，定时拆线重连

- `process_base_url()` 把 `https://api.openai.com/v1` 改成 WebSocket，拼上
  model；Azure 则走部署名 + `api-version`。
- `_main_task` 循环：建连 → 收发 → 异常则按 `APIConnectOptions` 退避重试。
- 配额/密钥类错误进 `_FATAL_ERROR_CODES`，**禁止重连**，避免死循环烧钱。
- `max_session_duration`（有默认值）到期主动拆线重连。Realtime 会话有时长
  上限；LiveKit 把"换一条 WS"做成常规操作，而不是等服务端踢人。

重连时 `_reconnect()` 按固定顺序重放：

1. `session.update`（模型、音色、VAD、模态……）
2. 工具列表
3. 本地 `chat_ctx` 镜像（去掉 function call / instructions / 空消息）

同时清空 per-connection 的 item_id 索引。服务端重连后会发新的 item id，
旧 id 对不上就会把上一轮的 `speech_started` 时间戳错配到下一轮——源码注释
写得很明确。

### 4.2 音频：24 kHz / mono / 100 ms / base64

OpenAI Realtime 要的是 24 kHz PCM16。`push_audio`：

1. 必要时 `rtc.AudioResampler` 把 WebRTC 帧（常见 48 kHz）降到 24 kHz；
2. `AudioByteStream` 切成 **100 ms** 一块；
3. 每块 `input_audio_buffer.append`，payload 是 base64。

视频（仅 Python）：用户说话时默认 1 fps、静音 0.3 fps，每帧打成
`conversation.item.create` 的 image item。这是"旁路视觉"，不是全双工视频
理解时钟。

### 4.3 事件：OpenAI 的九步响应，收成两条 channel

插件注释里写死了他们认定的顺序（并假设**一次 response 只产出一条 message**）：

```text
response.created
  → response.output_item.added
  → conversation.item.added
  → response.content_part.added
  → response.output_audio_transcript.delta  × N
  → response.output_audio.delta             × N
  → response.content_part.done
  → response.output_item.done
  → response.done
```

`_handle_response_created` 建一个 `_ResponseGeneration`：`message_ch` +
`function_ch`。之后的 audio/text delta 写进对应 `Chan`，AgentActivity
从 channel 读，再经 `realtime_audio_output_node` / `transcription_node`
送到 RoomIO。

Azure 仍用 beta 事件名（`response.audio.delta` 等）。插件用
`_AZURE_EVENT_MAPPING` 先归一成 GA 名字，后面只维护一套 handler。
这是适配器模式，不是两套业务逻辑。

另暴露两个调试事件：`openai_server_event_received` /
`openai_client_event_queued`，方便对照 04 章的原始协议。

### 4.4 生成的两种来源：模型自己开口 vs 应用叫它开口

| 来源 | OpenAI 侧 | LiveKit 侧 |
| --- | --- | --- |
| 服务端 VAD 认为用户说完 | 自动 `response.create`（`create_response=True`） | `generation_created` 且 `user_initiated=False` → `_realtime_generation_task` |
| `session.generate_reply()` / `on_enter` 问候 | 插件发 `response.create`，metadata 带 `client_event_id` | `user_initiated=True`；10 s 内等不到 `response.created` 就超时，迟到的响应会被 `response.cancel` 丢掉 |

超时/打断与"响应稍后才 created"之间的竞态，用 `_DiscardedGeneration` 吞掉
后续 delta，避免幽灵音频灌进扬声器。这是 Realtime 协议里最脏的一段，插件
写得很完整。

### 4.5 打断与截断：cancel 停生成，truncate 改历史

- `interrupt()` → `response.cancel`。只停当前生成，不改历史。
- `truncate(message_id, audio_end_ms)` → `conversation.item.truncate`。
  把已经说出口的音频在**用户真正听到的位置**切开，避免模型以为整句都说完了。
- `audio_end_ms == 0` 则直接 `conversation.item.delete`。
- 半级联（只有 text）则改本地 chat ctx 再同步回去。

文档原话：打断后"自动把对话历史截断为用户实际听到的那一段"。这是第二代
S2S 能做假全双工的关键——**模型仍是轮次制，系统层把没说完的尾巴从上下文里
剪掉**。

### 4.6 半开的 turn taking 会警告

若 `create_response=False`（轮次交给客户端）但 `interrupt_response` 仍为真，
插件打 warning：服务端还会在用户开口时取消响应。正确姿势是两个开关一起关，
否则 LiveKit 以为自己在管打断，OpenAI 也在管，两边抢。

## 五、轮次检测：必须只有一个主人

这是 LiveKit × OpenAI 实现里最值得抄的一条：**turn taking 允许两种实现，
但同一时刻只许一个做主。**

### 5.1 默认：OpenAI 服务端检测（推荐给 Realtime）

`RealtimeModel()` 默认 `semantic_vad`（也可用 `server_vad`）。此时：

- Agent **原样转发**用户音频，不在本地做 EOT；
- 模型用 `input_audio_buffer.speech_started / speech_stopped` 通知框架；
- `AgentActivity._on_input_speech_started` 立刻 `interrupt()`；
- `InterruptionOptions` 几乎全部失效：`enabled` 必须保持 `True`，只有
  `discard_audio_if_uninterruptible` 仍生效；
- **`interruption.enabled=False` 是硬错误**（`ValueError`）。想禁止用户打断，
  必须 `RealtimeModel(turn_detection=None)`，改用 Session 上的 VAD。

`server_vad` 可调 `threshold` / `prefix_padding_ms` / `silence_duration_ms`
（电话噪声场景官方示例：threshold 0.7、silence 400 ms）。
`semantic_vad` 可调 `eagerness`：`low` / `medium` / `high`。

映射到 04 章：这就是把 VAD 三姿态（检测 / 提交 / 自动回复）留在 OpenAI；
LiveKit 只做媒体和播放。

### 5.2 备选：LiveKit TurnDetector + 关掉模型 VAD

文本端点模型跑在**转写空间**。Realtime 的用户转写往往**晚于**模型开口，
所以官方示例强制并行一条 STT：

```python
session = AgentSession(
    turn_detection=MultilingualModel(),
    vad=silero.VAD.load(),
    stt=deepgram.STT(),
    llm=openai.realtime.RealtimeModel(
        turn_detection=None,              # 必须关，否则双检测器互抢
        input_audio_transcription=None,   # 改用 Deepgram
    ),
)
```

音频被**复制**到两条路径：一条进 Realtime（理解+说话），一条进 STT
（给 TurnDetector 和字幕）。这就是文档说的 "Realtime + separate STT"。

`AgentActivity._interrupt_by_audio_activity` 开头有守卫：若 Realtime
`capabilities.turn_detection` 为真，**直接 return**。本地 VAD 打断逻辑
不会和模型抢。

### 5.3 级联管道上 LiveKit 自己的一套（Realtime 默认用不上）

`TurnHandlingOptions` 是给 STT‑LLM‑TTS（以及 `turn_detection=None` 的
Realtime）准备的完整客户端策略：

| 子系统 | 做什么 | 和 06 章 10 态的关系 |
| --- | --- | --- |
| Turn detector / VAD / STT / manual | 用户何时说完 | 用户侧 EOT，不是模型输出态 |
| Endpointing `fixed` / `dynamic` | 说完后再等多久才提交 | HOLDING 的等待窗口；dynamic 用会话停顿 EMA |
| Interruption `adaptive` / `vad` | 用户插话是真打断还是附和 | adaptive ≈ 区分 INTERJECTING vs BACKCHANNEL |
| `resume_false_interruption` | 空转写则接着说 | RESUMING vs YIELDING |
| Preemptive generation | EOT 确认前先跑 LLM（可选 TTS） | 投机 SPEAKING；Flux 同类 |
| `user_turn_limit` | 用户说太久则钩子打断 | 产品策略，不是轮次理论 |

Realtime + 服务端 VAD 时，上面这张表大部分被跳过。**不要以为配了
`TurnHandlingOptions` 就作用于 GPT Realtime。** 文档写得很硬。

### 5.4 节点：Realtime 几乎没有管道节点可改

级联可 override `stt_node` / `llm_node` / `tts_node`。Realtime 只留：

- `realtime_audio_output_node`：出口音频（音量、滤波）
- `transcription_node`：字幕
- 生命周期：`on_enter` / `on_exit` / `on_user_turn_completed`

想改"何时开口"，Realtime 默认路径上**改不了节点**，只能改模型侧
`turn_detection`，或关掉它把控制权拿回 TurnDetector。

## 六、对照我们的 10 态：LiveKit 实现的是哪一层

06 章把状态分成现象 / 模型表示 / 系统事件三层。LiveKit × OpenAI 几乎全部
发生在**系统事件层**，而且公开状态机比 10 态粗得多。

| 10 态 | LiveKit 有没有一等公民 | 实际怎么做 |
| --- | --- | --- |
| **LISTENING** | 有 | `agent_state=listening` |
| **HOLDING** | 无（级联有 endpointing delay） | Realtime 默认交给 `semantic_vad` eagerness |
| **THINKING / DELEGATING** | 半有 | `thinking` 含"还没出声"；工具走 `function_ch`，无独立 DELEGATING 态 |
| **BACKCHANNEL** | 级联 adaptive 有意图；Realtime 默认无 | 服务端 VAD 路径不区分附和 |
| **SPEAKING** | 有 | 首帧回调才进入 |
| **YIELDING** | 有，但是事件不是状态 | `speech_started` → `interrupt()` → `response.cancel` + truncate → `listening` |
| **RESUMING** | 级联有；Realtime 服务端 VAD 下 InterruptionOptions 被忽略 | `resume_false_interruption` 只在本地打断路径 |
| **INTERJECTING** | 无 | 没有"模型主动插话"API；只有用户打断模型 |
| **MUTED** | 弱 | `away`、`audio_input` 关闭、不可打断时丢帧 |
| **REPAIR** | 无 | 靠 prompt / 工具，没有修复态 |

系统阴影态：

| 阴影 | LiveKit 对应 |
| --- | --- |
| 委托中 | 工具执行；`max_tool_steps`（默认 3）用尽会再要一轮口头总结 |
| 切换中 | 多 Agent handoff；`_scheduling_paused` 时丢掉新的 realtime generation |
| 分轮暂定 | 无 GPT‑Live 式双视图；chat_ctx 直接按 item 追加 |

**结论：** LiveKit 把第二代 S2S 包装成可用的语音产品，输出侧只有
listening / thinking / speaking 三态，打断是**边沿事件**。06 章的 10 态
如果要落在这种框架上，不能指望 `agent_state` 变十个枚举；要在
`TurnHandlingOptions` + 模型 `turn_detection` + 自管 SpeechHandle 上长出来。

## 七、他们做对了什么，和 GPT‑Live / Instruct‑FD 差在哪

### 做对了（可直接借鉴）

1. **单一 `AgentSession`，三种管道是插件而不是产品分叉。** 半级联、并行 STT、
   换 TTS，都是填不同字段。
2. **Turn taking 所有权显式互斥。** 服务端 VAD 开着时，本地打断逻辑短路；
   关打断是硬错误而不是静默失效。这比"两边都配一点"干净。
3. **打断 = cancel + 按已播放毫秒 truncate。** 上下文与用户耳朵对齐，避免
   模型在下一轮引用没说完的句子。
4. **重连当一等操作。** 重放 session / tools / chat_ctx，丢弃 in-flight
   generation，item_id 状态随连接丢弃。
5. **capabilities 比特。** 新 Realtime 提供商只要实现同一接口，编排不用改。
6. **假打断恢复、抢跑生成、动态 endpointing** 做在级联侧——说明他们清楚
   这些是**客户端策略**，不是模型能力。Realtime 路径刻意不假装拥有它们。

### 没做、也不该误会他们做了

1. **不是全双工。** 输入在流，输出仍是"一轮 response"。重叠只来自 barge-in
   （用户打断模型），没有模型在用户说话时持续发声的 INTERJECTING / 持续
   BACKCHANNEL。
2. **没有说/想分离。** `thinking` 只是"音频还没到"。工具调用会卡住或另起
   response，不是 GPT‑Live 的异步委托时钟。
3. **没有 Instruct‑FD 那种输出策略指令。** 可控的是 VAD 参数和 Session 选项，
   不是"现在允许附和 / 禁止插话"的生成期指令。
4. **字幕天然滞后。** 官方建议需要实时转写就加独立 STT。
5. **纯 Realtime 不能 `say(精确稿件)`。** 要念稿走半级联。
6. **一次 response 一条 message** 是插件假设。多段输出或复杂 tool+speech
   交织会打 warning。

## 八、若我们要接同样的栈：建议怎么用、怎么长

这些建议叠在 05、06 章之上，专门针对"用 LiveKit 这类编排层接 OpenAI
Realtime"的路径。

1. **先选管道，再谈状态。** 只要还在 OpenAI Realtime / Qwen Realtime 这一代
   API 上，产品状态机就按 listening / thinking / speaking + 打断边沿 来做；
   10 态里 BACKCHANNEL / INTERJECTING / RESUMING 能做多少，取决于你有没有
   把 turn taking 从模型手里拿回来。
2. **默认把 VAD 留给模型。** 与 LiveKit 官方一致。只有需要自适应打断、假打断
   恢复、或语义 EOT 比 `semantic_vad` 更好时，才 `turn_detection=None` +
   并行 STT + TurnDetector。
3. **禁止双检测器。** 配置校验应做成启动失败，不要运行期互抢。
4. **truncate 按播放头，不按生成头。** 用户听到哪，历史就剪到哪。
5. **半级联作为品牌音色和念稿的逃逸舱。** 不要和"全双工"混谈；它解决的是
   输出可控，代价是延迟回到级联量级。
6. **工具不要走活跃音频路径的同步等待。** LiveKit 的 `max_tool_steps` +
   口头收束只是止血。要对齐 GPT‑Live，需要在 LiveKit 之外加委托会话
   （05 章的第二时钟），前台 Realtime 只说"我去查"。
7. **对外事件与模型事件分层。** 前端只订 `agent_state_changed` /
   `user_input_transcribed`；协议细节留在 `openai_server_event_received`
   这种调试通道。不要把 `response.output_audio.delta` 泄漏成产品状态。

## 九、关键链接

| 主题 | URL |
| --- | --- |
| 集成总览（本文入口） | https://docs.livekit.io/agents/integrations/openai/ |
| OpenAI Realtime 插件 | https://docs.livekit.io/agents/models/realtime/plugins/openai/ |
| Realtime 模型总览（限制与半级联） | https://docs.livekit.io/agents/models/realtime/ |
| 三种管道对比 | https://docs.livekit.io/agents/models/pipelines/ |
| AgentSession | https://docs.livekit.io/agents/logic/sessions/ |
| Turns / 打断 / Realtime 模式 | https://docs.livekit.io/agents/logic/turns/ |
| Turn detector | https://docs.livekit.io/agents/logic/turns/turn-detector/ |
| TurnHandlingOptions | https://docs.livekit.io/reference/agents/turn-handling-options/ |
| Pipeline nodes | https://docs.livekit.io/agents/logic/nodes/ |
| Python Realtime API 参考 | https://docs.livekit.io/reference/python/livekit/plugins/openai/realtime/index.html |
| 插件源码 `realtime_model.py` | https://github.com/livekit/agents/blob/main/livekit-plugins/livekit-plugins-openai/livekit/plugins/openai/realtime/realtime_model.py |
| 编排源码 `agent_activity.py` | https://github.com/livekit/agents/blob/main/livekit-agents/livekit/agents/voice/agent_activity.py |
| Realtime + TurnDetector 示例 | https://github.com/livekit/agents/blob/main/examples/voice_agents/realtime_turn_detector.py |
| 级联 vs Realtime 博客 | https://livekit.com/blog/realtime-vs-cascade |

## 十、一句话

LiveKit 对 OpenAI 的实现，本质是 **WebRTC 房间 ↔ Realtime WebSocket 的适配器
+ 一条可切换主人的轮次状态机**。模型仍是第二代 S2S；所谓"自动处理打断"
是 `speech_started → response.cancel → item.truncate`，不是全双工输出状态。
我们若抄，抄的是**所有权互斥、按播放头截断、重连重放、capabilities 分流**，
而不是把它当成 GPT‑Live 的开源版。
