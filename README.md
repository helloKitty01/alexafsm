# AI 文档库

本仓库用于沉淀 AI / Agent 系统相关的设计文档与讨论。

## 目录

| 目录 | 内容 |
| --- | --- |
| [latency-discussion/](./latency-discussion/) | Agent loop 端到端时延优化讨论（单 loop 成本、loop 次数、快慢双系统） |
| [kv-cache-discussion/](./kv-cache-discussion/) | KV cache 命中率与 agent 上下文工程（分层排布、渐进式加载、压缩策略）的设计讨论 |
| [reminder-discussion/](./reminder-discussion/) | reminder 机制（内部代号 notion 方案）的业界洞察：Claude Code system-reminder、Manus recitation、Anthropic 官方模式 |
| [docs/variable-resolution/](./docs/variable-resolution/) | 工具参数变量解析机制方案（含单页幻灯片：深色原版、浅色版及同款 PPTX） |
| [docs/skill-env-variables/](./docs/skill-env-variables/) | Skill 分支环境变量传入方案（前台应用为例，通道选择与决策矩阵，含业界实现调研） |
| [docs/thinking-tool-calls/](./docs/thinking-tool-calls/) | 思考模式（Thought）与 Function Call 的时序机制（先想后调、三层"出不出 thought"原因） |
| [docs/skill-tool-rom-versioning/](./docs/skill-tool-rom-versioning/) | Skill 与工具的 ROM 配套管理方案（双速发布、能力分支、版本门控与运营纪律，含单页 HTML 幻灯片） |
