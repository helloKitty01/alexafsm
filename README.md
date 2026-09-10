# AI 文档库

本仓库用于沉淀 AI / Agent 系统相关的设计文档与讨论。

## 协作约定

详见 [AGENTS.md](./AGENTS.md)，要点：

- **所有修改直接在 master 分支上提交并推送**，禁止新建任何分支、不开 PR；
- 所有文档统一放在 `docs/<主题>/` 下；
- 每个目录只保留同一系列的最新版本，历史版本归档到同目录的 `history/` 子文件夹。

## 目录

| 目录 | 内容 |
| --- | --- |
| [docs/latency-discussion/](./docs/latency-discussion/) | Agent loop 端到端时延优化讨论（单 loop 成本、loop 次数、快慢双系统、工具接入要求与共建倡议） |
| [docs/kv-cache-discussion/](./docs/kv-cache-discussion/) | KV cache 命中率与 agent 上下文工程（分层排布、渐进式加载、压缩策略）的设计讨论；含**最终汇报版承载 `kv cache方案（汇报版）.v1.4`（9 页 + 附录 3 页；P1 数据基线 M1–M11 / K / R 为全稿单一事实来源并数据绑定，P2 组成对比 + 三尺子，P3 尺子与四步改造，P4–P6 任务 / 问答 / 闲聊逐 Q 账目按 v7.2 版式当前实测 vs 目标推演对照，已上线第一步实测与预热下沉附录）**、v2 汇报大纲（13）、实测数据需求（14）、上下文模块与长度基线（15）、逐调用实测 `token_breakdown.csv`、prompt 各段内容变化对照，以及 v2 单页幻灯片 P1 组成对比 v1.2 / P2 尺子与三方案 / P7 自动化统计；上一版整合材料 kvcache整体方案.v1 暂留对照 |
| [docs/reminder-discussion/](./docs/reminder-discussion/) | reminder 机制（内部代号 notion 方案）的业界洞察：Claude Code system-reminder、Manus recitation、Anthropic 官方模式 |
| [docs/agent-variable-scheme/](./docs/agent-variable-scheme/) | Agent 变量句柄方案（当前版本 v4 文档 + v6 幻灯片，v1–v5 留档于 history/） |
| [docs/variable-resolution/](./docs/variable-resolution/) | 工具参数变量解析机制方案（含单页幻灯片：深色原版、浅色版及同款 PPTX） |
| [docs/skill-env-variables/](./docs/skill-env-variables/) | Skill 分支环境变量传入方案（前台应用为例，通道选择与决策矩阵，含业界实现调研） |
| [docs/thinking-tool-calls/](./docs/thinking-tool-calls/) | 思考模式（Thought）与 Function Call 的时序机制（先想后调、三层"出不出 thought"原因） |
| [docs/skill-tool-rom-versioning/](./docs/skill-tool-rom-versioning/) | Skill 与工具的 ROM 配套管理（双速发布、版本感知、工具治理、单 skill 可行性、重组情形、工具集对象与 A/B 管理路线，含单页 / 8 页详解 / v2 ~ v2.7 系列幻灯片，v2.7 为最新汇报版，含上架场景决策树与 A~F 穷举） |
| [docs/phone-assistant-automation/](./docs/phone-assistant-automation/) | 手机智慧助手需求与方案（统一任务模型：定时/事件/自定义监视/长时异步任务，双脑架构 + 打扰管理器；含多任务管理 Agent v1.3 幻灯片：双入口 × 三层模型 × UAT 接口 × 异构执行体，v1.0–v1.2 留档 history/） |
| [docs/openclaw-automation/](./docs/openclaw-automation/) | openClaw 自动化任务统一方案（定时 + 事件订阅 + 模型判定触发，v2.0 幻灯片 20 页四章结构，v0.1–v1.0 留档 history/）：以 openClaw cron service 为唯一中枢按需新增——四种触发（时间 / 脚本轮询 / 模型判定轮询 / 外部事件）一条执行路径；原生 `cron` 工具全貌与层级图（一个工具，`schedule.kind ∈ at / every / cron / stream / event`，`trigger.kind ∈ script / agent`）、session 四选一、事件中心（EventHub）/ 原生 / 新增三方归属与 γ 方案、谁来订阅（Gateway 内部完成）、新增 `schedule.kind="event"` 规格与投递语义、事件入口（传输四选一 + `fireJob → runJob` 点火路径）、工具可见范围 × 订阅生命周期（`event_catalog` 只读 / `event_publish` 主 loop 不可见 / 判定阶段只读 + `trigger_result` 收口）、两页端到端时序、上下文组织（五块信封）、七步编译成本阶梯与 `payload.message` 三段模板、`trigger.kind="agent"` 规格（"当 xxxx 时"写不成脚本交给受限判定 Agent：`{fire,message,state}` 契约沿用、六条约束、三层级联门、S9 完整实例 + state 逐 tick 演进）、九个场景全表（S6–S9 分支 / 嵌套 / 动作反馈 / 时序各一条 job，嵌套 = state.phase）、派生事件路 A / B 两维正交、可靠性清单与预授权等开放问题；**v2.0 为版面重做：一个工具 · 四种触发 · 一条执行路径四章重组，首页目录与阅读路线，20 页逐页校验无溢出** |
| [docs/omni-realtime-voice/](./docs/omni-realtime-voice/) | omni 实时语音架构洞察（三代架构演进与业界谱系、GPT‑Live 全双工 + 说/想分离、OpenAI 六个月实时系统工程：流式推理/实例切换/压缩即切换/WARP/relay+transceiver、Realtime API 会话与事件模型、对双脑架构的启示、全双工输出状态盘点与统一状态模型 v3.7：44 场景全集（A→X 主序，P0/P1/P2 为色标）× 状态交互图 × 四层分层 ×（状态·floor）× 事件完备性矩阵 × 九缺口与五决策 × 词表校订 × 外挂 ASR 标识（v3.7 汇报版幻灯片 23 页：全貌图 / 分叉树 / 44 场景按时间线展开 / 全集矩阵 / 打断判定窗含回声前置 / 四页 12 条共用时间轴的泳道链路走查 / 四层协议与谁产谁消 / 与外部词表逐项对比 / 五项决策；v1–v3.6 留档 history/）、LiveKit Agents × OpenAI 集成实现） |
