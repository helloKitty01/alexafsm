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
| [08-场景全集与状态交互分层.md](./08-场景全集与状态交互分层.md) | 统一状态模型 **v2 → v3.3 修订**（场景驱动）：**42 场景全集**（每条带具体例子 + **P0/P1/P2 优先级**：P0 最小可用 10 / P1 体验分水岭 22 / P2 增强暂缓 10；v3.3 由状态 × 事件矩阵补入 B10 端点撤回、D11 暂停继续、D12 打断后回来、D13 策略中止、D14 自回声、X5 播放卡顿、X6 插话撞等答、X7 禁言中告警）；三分类原则；`THINKING/DELEGATING` 拆分为 `PREPARING` + `HOLDING`；工具 / 委托不建态、时延 T0/T1 状态级 + T2 轮级；四层分层（新增 `playout_position` 上行、`committed_revoked` / `policy_stop` / `safety_event` / `playout_stalled`）；外部 7 项事件词表校订；外挂 ASR 外部标识（+ `segment_merge`）；对模型输出五条需求与六场景验收；**第 10 节状态 × 事件完备性矩阵**；**第 11 节七个已识别缺口 + 决策 1–5 + C4 × D3 链路走查** |
| [全双工输出状态.slides.v3.3.html](./全双工输出状态.slides.v3.3.html) | **汇报版 v3.3（19 页，中文；状态名统一为「英文（中文）」，事件名保留协议字段；绿色 NEW 标记本版新增）**：封面（含议程）→ 人机六差异逼出机制 → 一张图看全貌（边①–⑯，⑨ 三触发源）→ 完整状态清单（系统 11 / 用户 4 / floor 五值）→ 三条设计原则（补决策 4/5 前提）→ 一轮对话五段（34 → 42）→ **42 场景全部带状态轨迹**（P0 十个含 D14 自回声 / P1 二十二个分两页 / P2 十个含理由 + 双向覆盖）→ **状态 × 事件完备性矩阵**（绿格 = 矩阵找出的遗漏）→ 打断判定窗（回声前置 + 真打断 / 暂停请求 / 附和 / 噪声四出口 + 策略取向）→ PREPARING/HOLDING 阈值 + 轮级时钟 + 工具委托 → **三条泳道链路走查**（B3+B4 停顿不抢答 / D3 真打断全链路 / C4 × D3 大模型接管中被打断，红框标缺口）→ 四层协议 + 产地决策 + 外挂 ASR 信号 → 与外部 7 项词表逐项对比 → **七个已识别缺口及处置** → **五项决策**（含影响范围）+ 五条模型需求 + 六场景验收 + 下一步 → 附录完整转换表（16 + 6，变更标注）。已合并 v3 底稿的全部独有内容（状态轨迹、泳道、覆盖矩阵） |
| [history/](./history/) | 历史版本留档：全双工输出状态幻灯片 v1（11 页，10 态讨论稿版）、v2（12 页，场景全集 × 四层协议汇报版）、v3（11 页，技术讨论底稿：轨迹 + 两条泳道 + 三议题）、v3.1（16 页，英文为主的汇报版初稿）、v3.2（15 页，中文汇报版，34 场景 / 三项决策），均已被 v3.3 取代 |

## 一句话共识

GPT‑Live 的新意不在"更聪明的语音"，而在**把"说"和"想"拆成两个时钟**：
全双工模型守住"永远有人在听、在回应"的第一时钟，前沿模型负责"答案有多深"的
第二时钟；系统层面用异步 RPC 边界把两者隔开，一切重活（委托、压缩、迁移、
持久化、分轮）都不上活跃路径——**the voice must flow**。
