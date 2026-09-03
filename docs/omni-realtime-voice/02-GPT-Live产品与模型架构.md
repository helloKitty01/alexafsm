# 02 GPT‑Live 产品与模型架构

来源：OpenAI《Introducing GPT‑Live》（2026‑07‑08，2026‑07‑31 更新 SynthID 水印），
辅以第三方实测（Agora Media Lab）与多家二手报道交叉核对。
GPT‑Live 没有公开技术报告，本章严格区分"官方说了什么"与"外界推断了什么"。

## 一句话定位

> GPT‑Live 是 OpenAI 第三代语音系统：**全双工**语音模型负责持续对话，
> 遇到需要搜索、深度推理或 agent 任务时**在后台委托前沿模型（GPT‑5.5）**，
> 结果回来后自然接入对话，全程不停顿。

两个模型：**GPT‑Live‑1**（Go / Plus / Pro 默认）和 **GPT‑Live‑1 mini**（Free 默认），
2026‑07‑08 起在 iOS / Android / ChatGPT.com 全球上线，取代 Advanced Voice Mode
成为 ChatGPT Voice 默认。API 版"即将推出"（有通知表单，截至本文无模型 ID、
无定价）。

## 两个设计决策

### 决策一：全双工，把轮次检测器从音频路径上拆掉

官方描述：**"Instead of processing a sequence of separate messages, GPT‑Live
continuously processes input while generating output. The model can therefore
make interaction decisions many times per second: whether to speak, continue
listening, pause, interrupt, or invoke a tool."**

对用户可感知的表现：

| 行为 | 第二代（AVM）做不到的原因 | GPT‑Live 的表现 |
| --- | --- | --- |
| 附和（backchannel） | 只能整轮响应，"嗯嗯"会变成一轮完整回答 | 用户说话中间插"mhmm""got it"，不抢话 |
| 停下来想 | 静音超过阈值即被判为说完 | 保持沉默等用户继续 |
| 用户打断 | 取消当前响应、重开新轮 | 模型自己判断"是不是真的要打断我"，再决定让不让 |
| 要求放慢 / 闭嘴听 | 需要重新一轮 | 直接调整节奏或进入纯聆听 |
| 实时翻译 | 需要等一整句 | 边听边译（结构上要求并发处理输入输出） |

**动作空间视角**（外界推断，非官方内部实现）：每个时间步的决策先是"出不出声"，
再是"说什么"。这一层必须又小又快，才能每秒跑多次而不成为瓶颈——
这也解释了为什么承担深度推理的不能是同一个模型。

### 决策二：说/想分离——对话模型与前沿模型解耦

官方描述：把"持续交互"（GPT‑Live）与"深度推理"（后台前沿模型）解耦。
需要网页搜索、更难的推理或 agent 式任务时，GPT‑Live 把任务交给另一个模型，
自己**继续和用户说话**，结果就绪后带回对话。上线时后台模型是 GPT‑5.5，
OpenAI 表示会持续替换为更新的前沿模型。

四档推理等级（按套餐开放）：

| 等级 | 后台模型与推理力度 | 可用套餐 | 适用 |
| --- | --- | --- | --- |
| Instant | GPT‑5.5 Instant | 全部（含 Free 的 mini） | 日常对话、快答 |
| Medium | GPT‑5.5 Thinking，medium effort | Go / Plus / Pro | 中等深度问题、轻量调研 |
| High | GPT‑5.5 Thinking，high effort | Go / Plus / Pro | 多步推理、深度分析（搜索时明显更慢） |
| X‑High | GPT‑5.5 Thinking，extended | Pro | 重度 agent / 研究任务 |

**关键性质：选更深的推理等级不会让对话本身变慢。** 这只在说/想分离的架构下
才成立——变慢的是"实质答案到达"的时钟，不是"有人在回应我"的时钟。

## 评测：分离架构的收益在哪里

### 对话体验（OpenAI 自建人评，5–10 分钟匹配对话）

| 模型 | 相对 AVM 偏好率 | 流畅度（均值/7） | 愉悦度（均值/7） |
| --- | --- | --- | --- |
| GPT‑Live‑1 | 75.7% | 4.96 | 5.19 |
| GPT‑Live‑1 mini | 69.2% | 4.33 | 4.47 |
| Advanced Voice Mode | （50% = 持平） | 3.80 | 3.82 |

评测维度：整体偏好、轮次交接、打断处理、对话流、自然度。

### 任务能力（委托带来的跃升）

| 模型 | GPQA（专家级科学推理） | BrowseComp（agent 式网页搜索） |
| --- | --- | --- |
| Advanced Voice Mode | 45.3% | 0.7% |
| GPT‑Live‑1 mini | 74.9% | 31.6% |
| GPT‑Live‑1 (Instant) | 76.5% | 35.1% |
| GPT‑Live‑1 (Medium) | 81.7% | 60.6% |
| GPT‑Live‑1 (High) | 84.2% | 75.2% |

另有内部 τ³‑Voice Telecom 变体（多轮电信客服任务），GPT‑Live‑1 High/Medium
领先 AVM。

**解读**：BrowseComp 从 0.7% 到 75.2% 不是语音模型变聪明了，而是**语音层学会了
什么时候该放手**。语音模型本身没变大，推理上限由后台模型决定，且随前沿模型
迭代自动抬升，不必动语音层。这是分离架构最重要的战略收益。

## 声音、安全与水印

- 九个声音（Arbor, Breeze, Cove, Ember, Juniper, Maple, Sol, Spruce, Vale）为
  GPT‑Live 重制。定位"为对话设计，不做声音模仿"：声音预定义，有防止模仿
  真人的安全措施。
- 语音专属安全训练 + **说话中即可生效的实时安全措施**：可以在模型正在说话时
  转向更安全的回答、提供危机资源、或在高风险情形下结束对话。青少年保护与
  Parental Controls 联动，上线后监控情感依赖。
- 2026‑07‑31 起 ChatGPT Voice 与 API 生成的受支持音频带 SynthID 水印，公开
  验证工具可检测 OpenAI 来源信号，并开放验证 API。

## 上线时的限制（官方承认）

- 不支持语音 + 视频 / 屏幕共享（Advanced / Standard Voice 保留以提供该能力）。
- 语言覆盖：非头部语言可能带非母语口音或流利度缺口。
- 不在 Business / Enterprise / Edu 工作区、Temporary Chat、桌面端、Codex、
  custom GPT 中提供。
- 无 API。开发者当下的对应物是 Realtime API 的 `gpt-realtime-2.1`（见 04 章），
  这是**另一个模型**，不是 GPT‑Live。
- 用量按滚动 24 小时计：Pro $200 不限；Pro $100 约 12 h Instant + 12 h Medium/High；
  Go/Plus 约 1 h Instant + 1 h Medium/High + 2 h mini；Free 仅 mini；单次会话
  上限 2 小时。

## 第三方实测：时延到底怎样

OpenAI 没有公布 GPT‑Live 的端到端时延数字。Agora Media Lab 于上线周用
人工嘴 + iPhone 13 + 双轨波形录音 + 受控网络损伤做了测量（30 次/条件，
单设备单账号单地点，Agora 自身有商业利益，结论需按此折价）：

| 指标 | GPT‑Live‑1 | Advanced Voice Mode | 解读 |
| --- | --- | --- | --- |
| 首音时延中位（用户末帧 → AI 首帧） | ~1.1 s | ~1.3 s | 仅快 205 ms，**不是"5 倍快"** |
| 首音时延 P90 | 中位 + 104 ms | 2318 ms | **抖动降 5 倍**（标准差 489 → 104 ms），这才是真实收益 |
| 被打断后让出时间 | 慢 ~500 ms | — | 不是退化：模型在判断"你是不是真的要打断"；30/30 拒绝背景人声探针（AVM 被骚扰停 20 次） |
| 10% 上行丢包下中位退化 | +314 ms | +2448 ms | 丢包对增量式架构只是丢一点上下文，对流水线是整段卡住；**受损的新模型仍胜过健康的旧模型**（P90 1836 vs 2318 ms） |

Agora 提出的**三时钟模型**值得直接采用：

1. **应答起点**（acknowledgment onset）：第一次出声，往往是"让我看一下"；
2. **实质答案起点**（substantive‑answer onset）：真正有信息量的内容开始；
3. **答案完成**（answer completion）。

GPT‑Live 的"快"主要来自把硬时延**重新分配进对话**：第一时钟很早触发，第二
时钟等后台模型。用户感知的响应性来自第一时钟。任何对标 GPT‑Live 的语音产品
都应该分别对这三个时钟设预算。

## 外界流传但未证实的说法

- "sub‑300 ms 时延"：不见于 OpenAI 任何官方材料，也与独立测量不符，不应引用。
- 具体的模型规模、码本设计、训练方式：OpenAI 未公开，与 Moshi/Qwen‑Omni 的
  类比只是谱系定位，不是实现断言。

## 对本章的一句话总结

GPT‑Live 的新颖之处不在"更聪明的语音"，而在**把"说"和"想"拆成两个时钟**：
全双工模型守住第一时钟（永远有人在听、在回应），前沿模型负责第二时钟
（答案有多深）。第 03 章讲 OpenAI 如何在系统层面让这两个时钟互不阻塞。
