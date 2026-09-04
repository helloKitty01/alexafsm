# omni 实时语音架构洞察（GPT‑Live / Realtime API）

这是一个洞察用目录，用于沉淀对 **omni 模型 + 全双工实时语音系统**整体架构的深度
分析。主要素材为 OpenAI 2026 年的三份一手材料，并交叉业界公开架构
（Moshi、Qwen3‑Omni、Gemini Live、Grok Voice、Alexa+）与第三方实测。

一手来源：

- 《Introducing GPT‑Live》（2026‑07‑08）——产品与模型形态；
- 《How we built a realtime system for responsive voice AI in six months》
  （2026‑08‑03）——GPT‑Live 的系统工程；
- 《Realtime conversations》及 Realtime API 相关指南——开发者可触达的会话模型；
- 前置工作《How OpenAI delivers low-latency voice AI at scale》（2026‑05‑04）
  与 IETF WARP / SNAP / SPED 草案。

与 [phone-assistant-automation/](../phone-assistant-automation/) 的双脑架构强相关：
GPT‑Live 正是"omni 全双工前台 + 异步深度后台"这条路线在业界的首个大规模验证。

## 目录

| 文档 | 内容 |
| --- | --- |
| [01-演进脉络与omni架构总览.md](./01-演进脉络与omni架构总览.md) | omni 的定义；级联 → S2S 轮次制 → 全双工三代架构；Moshi / Qwen3‑Omni / Gemini Live / Grok / Alexa+ 谱系对照；omni 系统的五个设计轴 |
| [02-GPT-Live产品与模型架构.md](./02-GPT-Live产品与模型架构.md) | 全双工决策环与说/想分离两大决策；四档推理等级；人评与 GPQA / BrowseComp 数据；安全与水印；上线限制；Agora 三方实测与"三时钟"模型 |
| [03-GPT-Live实时系统工程.md](./03-GPT-Live实时系统工程.md) | "the voice must flow"：有状态流式推理、Go 媒体快路径、实例切换与压缩即切换、委托预算、双视图分轮、WARP + Instant Connect、relay + transceiver 地基、静默灰度的教训 |
| [04-Realtime-API会话模型.md](./04-Realtime-API会话模型.md) | Session / Conversation / Response 对象模型；client/server 事件；VAD 三姿态；打断与截断；out‑of‑band 响应；function calling / MCP / SIP；模型阵容与定价；API 概念到系统架构的映射；面向 GPT‑Live API 的迁移准备 |
| [05-对我们系统的启示.md](./05-对我们系统的启示.md) | 被验证的判断、需补进双脑架构的设计（两时钟三度量、后台预热、分轮器、打断三形态、压缩即切换、会话建立预算）、要避的坑、待讨论 |
| [06-全双工输出状态盘点.md](./06-全双工输出状态盘点.md) | 全双工输出状态的三层视角（会话现象 / 模型表示 / 系统事件）：Sacks–Skantze–VAP 基础；Moshi / Freeze‑Omni / SALMONN‑omni / BayLing‑Duplex / FLM‑Audio / Fun‑Audio‑Chat‑Duplex 等状态编码对照；Easy Turn / TEN / Flux / Qwen `smart_turn` 用户侧状态；Full‑Duplex‑Bench 行为标签；Instruct‑FD 五策略指令遵循；Qwen 系三条线定位；统一 10 态输出状态模型（讨论稿）、待决问题与来源 Top 10 附录 |
| [07-LiveKit-OpenAI实现洞察.md](./07-LiveKit-OpenAI实现洞察.md) | LiveKit Agents × OpenAI 集成实现：WebRTC↔Realtime WS 适配器；三种管道共用 AgentSession；插件协议翻译（24 kHz / 100 ms / 打断 truncate / 重连重放）；轮次所有权互斥；对照 10 态的系统事件层映射 |
| [LiveKit-OpenAI实现.slides.html](./LiveKit-OpenAI实现.slides.html) | 9 页幻灯片 v1：定性 → 三管道 → 运行时 → 插件 → cancel+truncate → 单主人轮次 → 10 态对照 → 做对了/没做 → 七条建议 |
| [08-场景全集与状态交互分层.md](./08-场景全集与状态交互分层.md) | 统一状态模型 **v2**（场景驱动）：34 场景全集（每条带具体例子 + **P0/P1/P2 优先级**：P0 最小可用 9 / P1 体验分水岭 15 / P2 增强暂缓 10）；三分类原则；`THINKING/DELEGATING` 拆分为 `PREPARING` + `HOLDING`；工具 / 委托不建态、时延 T0/T1/T2 分段；四层分层；外部 7 项事件词表校订；外挂 ASR 外部标识；对模型输出五条需求与验收 |
| [全双工输出状态.slides.v3.html](./全双工输出状态.slides.v3.html) | **当前版本 v3（讨论底稿，11 页）**：34 场景**逐条细化到状态轨迹**（A/B/C/D/X 五组）+ 双向覆盖检查（状态↔场景）→ **完整状态交互图**（含入口链与议题标注）→ 两条泳道走查（B3 停顿不抢答、D3 真打断全链路）→ 转换表（16+6，议题挂行）→ **三个待讨论议题**（HOLDING 续说时延归属 / REPAIR·BACKCHANNEL 的存在理由 / T1 filler 出声归属）；结论收敛后回写 08 章 |
| [history/](./history/) | 历史版本留档：全双工输出状态幻灯片 v1（11 页，10 态讨论稿版）、v2（12 页，场景全集 × 四层协议汇报版），已被 v3 取代 |

## 一句话共识

GPT‑Live 的新意不在"更聪明的语音"，而在**把"说"和"想"拆成两个时钟**：
全双工模型守住"永远有人在听、在回应"的第一时钟，前沿模型负责"答案有多深"的
第二时钟；系统层面用异步 RPC 边界把两者隔开，一切重活（委托、压缩、迁移、
持久化、分轮）都不上活跃路径——**the voice must flow**。
