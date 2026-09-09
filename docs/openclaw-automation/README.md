# openClaw 自动化任务：定时 + 事件订阅统一方案

从"每天早上 9 点帮我干 xxx"出发，把 openClaw 的定时任务能力扩展到事件驱动的自动化
（明天下雨 / 到家 / 收到某人电话 / 火车放票抢票）。
架构以 openClaw 为基础、按需新增。前提假设：存在一个统一事件管理服务（EMS），
订阅即推送，filter / guards 在 EMS 侧评估，有 publish 接口。

## 目录

| 文件 | 内容 |
| --- | --- |
| [openClaw自动化任务方案.slides.v0.2.html](./openClaw自动化任务方案.slides.v0.2.html) | **整体方案幻灯片（当前版本 v0.2，12 页）**：目标与五场景归类 → openClaw 原生 `cron` 工具全貌（schedule 四种含 `stream`、payload 三种、`trigger` 条件监视器、pacing、contextMessages、delivery）→ session 四选一与默认 isolated、跨次记忆三层级 → 三方归属表（EMS / 原生 / 新增）与 α β γ 三方案对比、选 γ → 整体架构（cron service 唯一中枢，job 表 = 任务表，三种触发汇入同一条执行路径）→ 新增 `schedule.kind="event"` 规格与 EMS 契约、投递语义、openClaw 侧四步处理 → **事件启动 Agent 时的上下文组织**（isolated 默认栈 + 五块信封 + 取舍 + 体量）→ 七步编译与 `payload.message` 三段模板 → **大模型工具调用实例**（S1 cron / S2 trigger 路 B / S3 event 三个完整 `cron add` JSON）→ 派生事件路 A / 路 B 对比与 S5 抢票两阶段统一形态 → 五场景全表 → 可靠性清单、已定结论、开放问题与下一步 |
| [history/](./history/) | 历史版本留档：v0.1（11 页，假设 openClaw 无 checker / 需自建 Task 表与 `/hooks/events` 入口层 / 九件工具 / 抢票走 command 特例；核实原生 `cron` 工具能力后被 v0.2 取代） |

## 核心结论（v0.2）

1. **γ 方案**：openClaw cron service 是唯一任务中枢，job 表就是任务表，原生 `cron` 工具是模型唯一入口；
   新增只有 `schedule.kind="event"` + EMS 适配器 + 信封拼装 + `payload.message` 编译模板。
   v0.1 的 Task 表、`/hooks/events` 入口层、九件工具整体取消。
2. **三种触发，一条执行路径**：时间（原生 at / every / cron）、条件轮询（原生 `trigger` 静默脚本，state 去重）、
   外部事件（新增 event kind 订阅 EMS）；执行统一为 isolated agentTurn，不再有 command 特例。
3. **门控归 EMS**：`filter / guards` 由模型写在订阅里、openClaw 原样转发、EMS 评估；
   openClaw 侧对事件只做四件事：订阅转发、`event_id` 去重、`occurred_at` 过期、拼信封起 agentTurn。
4. **运行上下文 = 冻结的任务定义**：系统身份（可 lightContext）+ 事件事实（显式标外部数据）+ `payload.message` 三段
   （原话 / 编译补充 / 策略）+ contextMessages（创建时冻结）+ `last_run_summary` 一行；不读主对话历史。
5. **路 B 为目标形态**：公共可复用的派生事件（天气、放票）由 trigger + script publish 进 EMS 目录，多任务可订阅；
   私有一次性判定走路 A（trigger 直接跑 agentTurn）。
6. **高危动作永不走默认路径**：支付 / 对外发送 / 删除在运行中用 `ask_user` 停下；S5 抢票拆为 current 前置确认 →
   运行中自建 isolated 执行任务的两阶段。

## 开放问题

- `filter` 表达式语言与 EMS 对齐（openClaw 不解释，跟 EMS 现有的走）。
- `ems_publish` 作为 script / trigger 内可调工具的接入方式（倾向 plugin 注册）。
- 抢票统一走模型后的时效损失是否可接受（先实测阶段 2 耗时）。
