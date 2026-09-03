# 04 Realtime API 会话模型

来源：OpenAI 平台文档《Realtime conversations》及相关指南（WebRTC / WebSocket /
VAD / SIP），Realtime API GA 公告（2025‑08‑28，`gpt-realtime`），
`gpt-realtime-2.1` / `-2.1-mini` 发布（2026‑07‑06）。

定位提醒：**Realtime API 今天暴露的是第二代（S2S 轮次制）模型的表面**，
GPT‑Live 尚无 API。但 OpenAI 明确说 GPT‑Live 系统"将承载即将推出的 GPT‑Live API"，
而外界普遍预期它会**扩展而非替代**现有的会话/事件模型。所以理解这套模型
既是今天能用的东西，也是明天迁移的地基。本章末尾会把 API 概念映射回 03 章的
系统架构。

## 一、会话对象模型

一个 Realtime Session 是模型与已连接 client 之间的**有状态交互**，由三类对象构成：

| 对象 | 作用 | 关键约束 |
| --- | --- | --- |
| **Session** | 交互参数：模型、输出声音、模态、音频格式、VAD、工具、指令、存储 prompt | 大多数属性随时可 `session.update`；`voice` 在模型首次输出音频后不可改；单会话最长 60 分钟 |
| **Conversation** | 会话期间的用户输入 Item 与模型输出 Item 序列（默认对话） | Item 类型：message / function_call / function_call_output |
| **Response** | 一次模型生成，产出音频/文本 Item 追加进 Conversation | 可覆盖 session 配置（仅本次生效）；可选择不进入默认对话（out‑of‑band） |

另有 **input audio buffer**：WebSocket 模式下 client 手工向其追加 base64 音频；
WebRTC 模式下由媒体轨道自动填充。

## 二、事件驱动的交互协议

一切通过 **client events**（你发）与 **server events**（服务端发）完成。
WebSocket 上两者共用一条有序通道；WebRTC 上音频走媒体轨道，事件走
`oai-events` data channel。

### 会话生命周期

```text
连接建立 ──▶ server: session.created
client: session.update ──▶ server: session.updated（返回完整有效配置）
```

`session.update` 示例（当前 GA schema）：

```json
{
  "type": "session.update",
  "session": {
    "type": "realtime",
    "model": "gpt-realtime-2.1",
    "output_modalities": ["audio"],
    "audio": {
      "input":  { "format": { "type": "audio/pcm", "rate": 24000 },
                  "turn_detection": { "type": "semantic_vad" } },
      "output": { "format": { "type": "audio/pcm" }, "voice": "marin" }
    },
    "prompt": { "id": "pmpt_123", "version": "89", "variables": { "city": "Paris" } },
    "instructions": "Speak clearly and briefly. Confirm understanding before taking actions."
  }
}
```

要点：可引用**服务端存储的 prompt**（含开发者消息、工具、变量、示例对话，
可 pin 版本），直接字段覆盖 prompt 中的同名字段。

### 文本 / 音频输入输出

| 意图 | client event | 关键 server events |
| --- | --- | --- |
| 加一条用户文本 | `conversation.item.create`（`input_text`） | `conversation.item.created` |
| 流式送音频（WS） | `input_audio_buffer.append`（base64，单块 ≤ 15 MB） | `input_audio_buffer.speech_started / speech_stopped`（VAD 开时） |
| 一次性送整段音频 | `conversation.item.create`（`input_audio`） | 同上 |
| 送图片 | `conversation.item.create`（`input_image`，data URL） | 同上 |
| 触发生成 | `response.create`（可带 `output_modalities`、`instructions`、`tools` 覆盖） | `response.created` → `response.output_text.delta` / `response.output_audio.delta` / `response.output_audio_transcript.delta` → `response.done` |

注意 `response.done` / `response.output_audio.done` **不含音频字节**，只含转写；
音频只在 `response.output_audio.delta` 里。WebRTC 下则直接从远端媒体轨道播放，
不必处理这些 delta。

声音选项：`alloy, ash, ballad, coral, echo, sage, shimmer, verse, marin, cedar`，
推荐 `marin` / `cedar`。

### 语音活动检测（VAD）的三种姿态

| 模式 | 配置 | 行为 | 适用 |
| --- | --- | --- | --- |
| 自动（默认） | `turn_detection: { type: server_vad \| semantic_vad }` | 服务端判定说话起止，自动 commit 并自动 `response.create`；用户开口自动打断当前响应 | 大多数对话场景 |
| VAD 开、响应手动 | `turn_detection.create_response = false`, `interrupt_response = false` | 仍检测起止，但不自动生成响应，client 自行 `response.create` | 审核、输入校验、RAG 前置——用一点时延换控制权 |
| 手动 / push‑to‑talk | `turn_detection: null` | client 自己 `input_audio_buffer.commit` + `response.create`，新输入前 `input_audio_buffer.clear` | 按键说话；避开 VAD 误判，且没有 VAD 超时等待，反而更"跟手" |

`semantic_vad` 带 `eagerness`（low / medium / high / auto）：这是第二代框架内
对"抢话 vs 迟钝"两难的**可调旋钮**，也是 GPT‑Live 中被模型内生决策取代的那个东西。
不同业务应视为产品决策而非默认值：客服想快，辅导类产品要容忍用户思考停顿。

### 打断与截断（Interruption & Truncation）

用户打断时 API 会检测语音、取消进行中的响应（`response.cancelled`）并开新响应。
但模型需要知道**自己说到哪被打断了**（用户可能问"你刚说的最后那个是什么"），
所以要把**未播放的部分从对话中删掉**——这叫 truncate。

| 连接 | 谁管播放缓冲 | 截断方式 |
| --- | --- | --- |
| WebRTC / SIP | 服务端持有输出音频缓冲，知道播了多少 | **自动截断** |
| WebSocket | client 自己播放 | 监听 `input_audio_buffer.speech_started` → 立即停播 → 记录已播时长 → 发 `conversation.item.truncate { item_id, content_index, audio_end_ms }` |

限制：模型无法精确对齐转写与音频，truncate 会切掉未播音频并**删除对应转写**，
但不会给出截断后的转写文本。

这正是 Alexa+ 所谓"上下文化打断"的 API 化：让模型的历史与用户实际听到的一致。

### Push‑to‑talk 流程差异

- **WebSocket**：按下 → 开始录音；若有进行中响应则 `response.cancel`，若在播放则
  停播并 `conversation.item.truncate`；松开 → `input_audio_buffer.append` →
  `input_audio_buffer.commit` → `response.create`。
- **WebRTC / SIP**：按下 → `input_audio_buffer.clear`；有响应则 `response.cancel`，
  在播放则 `output_audio_buffer.clear`（同时截断对话）；松开 → `commit` → `response.create`。

## 三、默认对话之外的响应（out‑of‑band）

这是 Realtime API 里最接近"说/想分离"思想的机制。

| 用法 | 配置 | 场景 |
| --- | --- | --- |
| 旁路响应不进对话 | `response.conversation = "none"` + `metadata` 标识 | 对当前对话做分类（support/sales）、审核、摘要，结果不污染主对话 |
| 自定义上下文 | `response.input = [ {type:"item_reference", id}, {新 message} ]` | 只看最近 N 轮、或拼接额外上下文生成 |
| 无上下文插入 | `response.input = []` + `instructions` | 忽略一切历史，强制说一段固定话（如法定告知） |

多条响应可**并发**生成，用 `metadata` 在 `response.done` 中区分归属。
同一条连接上因此可以同时跑"面向用户的语音响应"和"后台分类/决策"两条线。

## 四、Function calling 与异步工具

流程与 Chat Completions 同构，但以事件表达：

1. `session.update` / `response.create` 中声明 `tools`（`type: function`）与 `tool_choice`；
2. 模型决定调用 → 响应输出 Item 为 `function_call`（`name`, `call_id`, `arguments`），
   可用 `response.function_call_arguments.delta` 流式监听，`response.done` 含完整数据；
3. client 执行代码；
4. `conversation.item.create { type: "function_call_output", call_id, output }` →
   再发 `response.create` 让模型基于结果回话。

GA 版起 `gpt-realtime` 原生支持**异步函数调用**：长耗时工具不再冻结会话，
模型在等结果期间可以继续流畅对话——这就是"应答时钟"与"实质答案时钟"分离
在第二代 API 上的雏形。配合**远程 MCP server**（在 session 配置里传 URL 即可挂上
整套工具），以及 SIP（接 PSTN / PBX / 桌面话机）。

## 五、连接方式的选择

| 方式 | 适用 | 音频处理 | 认证 |
| --- | --- | --- | --- |
| **WebRTC** | 浏览器、移动端 | 媒体轨道自动收发，抖动/丢包/回声由 WebRTC 处理；事件走 data channel | 临时密钥（ephemeral key）或**统一接口**（后端调 `/v1/realtime/calls`，简单但把应用服务器放进会话初始化关键路径） |
| **WebSocket** | 服务器到服务器 | 自己搬 base64 音频块，自己管播放与截断 | 标准 API key（只在安全后端） |
| **SIP** | 电话网络、呼叫中心 | 信令（发起、DTMF、转接）留在 SIP 层，音频与推理走 Realtime | 后端配置 |

OpenAI 的建议很明确：面向终端设备用 WebRTC，服务端集成用 WebSocket。
这与 03 章"用户设备到模型的媒体路径必须是 WebRTC 级别的"一致。

## 六、当前模型阵容与定价（2026‑07）

| 模型 | 定位 | 文本 in/cached/out（$/1M） | 音频 in/cached/out（$/1M） | 图像 in/cached |
| --- | --- | --- | --- | --- |
| `gpt-realtime-2.1` | 最强实时推理、工具、指令跟随、语音 agent；可配推理力度 | 4.00 / 0.40 / 24.00 | 32.00 / 0.40 / 64.00 | 5.00 / 0.50 |
| `gpt-realtime-2.1-mini` | 更快更省的 mini **推理**模型（推理与工具从旗舰独占下放到 mini） | 0.60 / 0.06 / 2.40 | 10.00 / 0.30 / 20.00 | 0.80 / 0.08 |

2.1 相对 2 的改进：字母数字识别、静音与噪声处理、打断行为；且通过缓存改进把
全系 Realtime 模型 **p95 时延至少降 25%**。知识截止 2024‑09‑30。粗算双向对话成本
约 $0.05–0.15/min（旗舰）、$0.02–0.05/min（mini）。

## 七、把 API 概念映射回 GPT‑Live 系统架构

| Realtime API 概念 | 03 章对应物 | 说明 |
| --- | --- | --- |
| Session（有状态、60 min 上限） | 有状态流式推理会话 + 实例切换/压缩 | GPT‑Live 侧用切换机制支撑"随时压缩、长时通话"，API 侧则给了 token 上限与多轮截断的粗粒度控制 |
| `turn_detection` / `semantic_vad` / `eagerness` | 被拆掉的轮次检测器 | 第二代把它做成可调旋钮，第三代让模型内生决策 |
| `input_audio_buffer.append` 搬 base64 | 媒体快路径（WebRTC 直达模型） | WebSocket 搬字节只适合服务端集成 |
| `conversation.item.truncate` | 推测视图 vs 权威记录 | 都是让"模型记忆"与"用户实际听到"保持一致 |
| out‑of‑band response + `metadata` | 异步委托边界 | 同一连接上跑旁路推理，不进主对话 |
| 异步 function calling | "委托不阻塞对话" | 模型等工具时继续说话 |
| 远程 MCP、存储 prompt、预建工具 | "在委托被请求之前就把前沿模型和工具准备好" | 都是把准备工作挪出响应关键路径 |
| WebRTC 统一接口 `/v1/realtime/calls` | Instant Connect 想消掉的信令关键路径 | 文档明说统一接口"把应用服务器放进会话初始化关键路径"——正是 Instant Connect 要解决的那类延迟 |

## 八、面向 GPT‑Live API 的迁移准备（建议）

基于以上映射，今天按下列方式构建，届时切 GPT‑Live 更可能是**换模型**而非重写：

1. **围绕持久会话 + 事件流建模**，不要在应用层再造"等用户说完再发"的轮次门控——
   那会把全双工模型退化成更慢的流水线。
2. **打断作为一等状态**：真正停止生成（`response.cancel`），不只是客户端静音；
   处理三种打断：用户打断模型、模型打断用户、引用已说内容的上下文化打断。
3. **委托路径单独设预算与兜底**：工具/后台模型超时怎么说、失败是否重试、
   绝不让沉默成为默认失败态。
4. **用三时钟度量**（应答起点 / 实质答案起点 / 完成），并在真实网络损伤下测。
5. **`eagerness` 是产品决策**，按业务场景调，不用默认值。
6. **引用可核实的数字**：不要把 sub‑300 ms 这类未证实数字当官方口径。

业界把这套事件接到 WebRTC 房间的开源实现，见
[07-LiveKit-OpenAI实现洞察.md](./07-LiveKit-OpenAI实现洞察.md)：LiveKit 用
`speech_started → response.cancel → item.truncate` 做打断，并用 capabilities
比特在"模型做主 / 客户端做主"之间显式互斥。
