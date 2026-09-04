# AI 文档库

本仓库用于沉淀 AI / Agent 系统相关的设计文档与讨论。

## 协作约定

详见 [AGENTS.md](./AGENTS.md)，要点：

- **所有修改更新都合入 master**，所有分支 PR 都必须合入，不留长期分支；
- 所有文档统一放在 `docs/<主题>/` 下；
- 每个目录只保留同一系列的最新版本，历史版本归档到同目录的 `history/` 子文件夹。

## 目录

| 目录 | 内容 |
| --- | --- |
| [docs/latency-discussion/](./docs/latency-discussion/) | Agent loop 端到端时延优化讨论（单 loop 成本、loop 次数、快慢双系统、工具接入要求与共建倡议） |
| [docs/kv-cache-discussion/](./docs/kv-cache-discussion/) | KV cache 命中率与 agent 上下文工程（分层排布、渐进式加载、压缩策略）的设计讨论 |
| [docs/reminder-discussion/](./docs/reminder-discussion/) | reminder 机制（内部代号 notion 方案）的业界洞察：Claude Code system-reminder、Manus recitation、Anthropic 官方模式 |
| [docs/agent-variable-scheme/](./docs/agent-variable-scheme/) | Agent 变量句柄方案（当前版本 v4 文档 + v6 幻灯片，v1–v5 留档于 history/） |
| [docs/variable-resolution/](./docs/variable-resolution/) | 工具参数变量解析机制方案（含单页幻灯片：深色原版、浅色版及同款 PPTX） |
| [docs/skill-env-variables/](./docs/skill-env-variables/) | Skill 分支环境变量传入方案（前台应用为例，通道选择与决策矩阵，含业界实现调研） |
| [docs/thinking-tool-calls/](./docs/thinking-tool-calls/) | 思考模式（Thought）与 Function Call 的时序机制（先想后调、三层"出不出 thought"原因） |
| [docs/skill-tool-rom-versioning/](./docs/skill-tool-rom-versioning/) | Skill 与工具的 ROM 配套管理（双速发布、版本感知、工具治理、单 skill 可行性、重组情形、工具集对象与 A/B 管理路线，含单页 / 8 页详解 / v2 ~ v2.7 系列幻灯片，v2.7 为最新汇报版，含上架场景决策树与 A~F 穷举） |
| [docs/phone-assistant-automation/](./docs/phone-assistant-automation/) | 手机智慧助手需求与方案（统一任务模型：定时/事件/自定义监视/长时异步任务，双脑架构 + 打扰管理器；含多任务管理 Agent v1.3 幻灯片：双入口 × 三层模型 × UAT 接口 × 异构执行体，v1.0–v1.2 留档 history/） |
| [docs/omni-realtime-voice/](./docs/omni-realtime-voice/) | omni 实时语音架构洞察（三代架构演进与业界谱系、GPT‑Live 全双工 + 说/想分离、OpenAI 六个月实时系统工程：流式推理/实例切换/压缩即切换/WARP/relay+transceiver、Realtime API 会话与事件模型、对双脑架构的启示、全双工输出状态盘点与统一状态模型 v2：34 场景全集 × 状态交互图 × 四层分层 × 词表校订 × 外挂 ASR 标识（v3.1 汇报版幻灯片 16 页，英文为主：全貌图 / 34 场景分级 / 打断三分 / 四层协议 / 与外部词表逐项对比 / 三项决策；v3 技术讨论底稿 11 页：场景细化到状态轨迹 + 泳道走查；v1/v2 留档 history/）、LiveKit Agents × OpenAI 集成实现） |
