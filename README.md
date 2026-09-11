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
| [docs/openclaw-automation/](./docs/openclaw-automation/) | openClaw 自动化任务统一方案（定时 + 事件订阅 + 脚本 / 模型判定触发；**当前 v3.1**：单文件 28 页幻灯片（主稿 18 页 + 附录 10 页，P2 为汇报用"一页看懂"：能力扩展四级台阶 + 编译期 / 运行期整体逻辑）+ `02-event-catalog.md` 事件目录全文，旧版留档 history/）：以 openClaw 原生 `cron` 为唯一中枢按需新增——一条路 **tick → trigger → fire → limits → run**、三道门各答一个问题（filter 事件中心 / trigger checker / limits cron service）；**新增只有五项**（`schedule.sources[]` 多源调度——每项 `kind ∈ at / every / cron / event`，时间与事件可混排——与事件中心适配器、tick + `nextCheckAt` self 闹钟、job 级 `limits {activeWindow, cooldown, maxRunsPerDay, maxRunsTotal, maxChecksPerDay}`、`trigger.kind="agent"` 只读判定 + `trigger_result` + 可选 `postScript`、编译期支撑：目录静态进 prompt + 唯一查询工具 `phone.lookup` + `event_publish` / `publishes` 登记），新工具三个，字段集一页写完；**判定者 script 与 agent 是同一契约下的两个正式选项**：有结构化数据源默认脚本（零 token），看图 / 读页面 / 语义判断选模型，十二场景里只有 S7 必须选模型（S6 / S8 / S9 可选），P10 专页讲 agent 判定完整形态（前置 script 门 → 只读判定 → postScript 收口计时计数；为什么判定与动作分两个 agentTurn；三道护栏）；trigger message 写跃迁名、跃迁 → 动作表在 payload.message 策略段；组合条件一种写法（sources + state 时间戳 + nextCheckAt，事件间隔用 `occurred_at`、到点用 `tick.now`）；三种"时间"分工（绝对时间点 → 时间源 / 相对事件 → nextCheckAt / 时段 → activeWindow）；派生事件只差 payload 一个字段；**六项拍板** D1–D6（fire = "需要执行一次 payload"、脚本边界与"失败 = fire:false"、预授权分期、跨 session ask_user 强制 announce、入口默认 webhook + `stream` 零改动验证、activeWindow 窗外仍维护 state）；分期一期含两种判定者、二期护栏与放权；动手前待核实 V1–V7；附录 A10 为 S7 完整 job 示例；28 页经无头浏览器三宽度逐页校验无溢出 |
| [docs/omni-realtime-voice/](./docs/omni-realtime-voice/) | omni 实时语音架构洞察（三代架构演进与业界谱系、GPT‑Live 全双工 + 说/想分离、OpenAI 六个月实时系统工程：流式推理/实例切换/压缩即切换/WARP/relay+transceiver、Realtime API 会话与事件模型、对双脑架构的启示、全双工输出状态盘点与统一状态模型 v3.7：44 场景全集（A→X 主序，P0/P1/P2 为色标）× 状态交互图 × 四层分层 ×（状态·floor）× 事件完备性矩阵 × 九缺口与五决策 × 词表校订 × 外挂 ASR 标识（v3.7 汇报版幻灯片 23 页：全貌图 / 分叉树 / 44 场景按时间线展开 / 全集矩阵 / 打断判定窗含回声前置 / 四页 12 条共用时间轴的泳道链路走查 / 四层协议与谁产谁消 / 与外部词表逐项对比 / 五项决策；v1–v3.6 留档 history/）、LiveKit Agents × OpenAI 集成实现） |
