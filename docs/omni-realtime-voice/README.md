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

## 一句话共识

GPT‑Live 的新意不在"更聪明的语音"，而在**把"说"和"想"拆成两个时钟**：
全双工模型守住"永远有人在听、在回应"的第一时钟，前沿模型负责"答案有多深"的
第二时钟；系统层面用异步 RPC 边界把两者隔开，一切重活（委托、压缩、迁移、
持久化、分轮）都不上活跃路径——**the voice must flow**。
