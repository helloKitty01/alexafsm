# openClaw 自动化任务：定时 + 事件订阅统一方案

从"每天早上 9 点帮我干 xxx"出发，把 openClaw 的定时任务能力扩展到事件驱动的自动化
（明天下雨 / 到家 / 收到某人电话 / 火车放票抢票）。
架构以 openClaw 为基础、按需新增。前提假设：存在一个统一的**事件中心（EventHub）**，
订阅即推送，filter / guards 在事件中心侧评估，有 publish 接口。订阅由 openClaw Gateway 内部完成，模型不调订阅工具。

> 命名约定：中文统一叫"事件中心"，代码 / 字段 / 端点用 `EventHub`（如 `EventHub.subscribe`、`/hooks/eventhub`），
> 模型可见的两个工具叫 `event_catalog`（只读查目录）和 `event_publish`（发派生事件）。v0.3 及以前写作 EMS。

## 目录

| 文件 | 内容 |
| --- | --- |
| [openClaw自动化任务方案.slides.v0.5.html](./openClaw自动化任务方案.slides.v0.5.html) | **整体方案幻灯片（当前版本 v0.5，16 页）**：目标与五场景归类 → openClaw 原生 `cron` 工具全貌（层级图：一个工具，`at / every / cron / stream / event` 是 schedule.kind 取值；payload 三种、`trigger` 条件监视器、pacing、contextMessages、delivery）→ session 四选一与默认 isolated、跨次记忆三层级 → 三方归属表（事件中心 / 原生 / 新增，含 `event_catalog` / `event_publish`）与 α β γ 三方案对比、选 γ、谁来订阅 → 整体架构（cron service 唯一中枢，三种触发汇入同一条执行路径）→ 新增 `schedule.kind="event"` 规格与事件中心契约、投递语义 → **事件入口：传输 × 点火（新增页：四种传输方式对比与 `EventIngress.onEvent` 入口抽象、默认 webhook；为什么不走原生 `/hooks/agent` 而走 cron service 的 `fireJob → runJob` 路径；返回码语义、幂等键、背压、同 job 串行）** → 工具可见范围 × 订阅生命周期 → **端到端时序 ①（S3 到家开灯 12 步，标出哪几步有模型参与、异常分支、run 状态机）** → **端到端时序 ②（S2 明天下雨路 B，生产者 S2a trigger + script → 事件中心 → 消费者 S2b，与路 A / 模型判定型生产者的差异）** → 事件启动 Agent 时的上下文组织（isolated 默认栈 + 五块信封）→ 七步编译与 `payload.message` 三段模板 → 大模型工具调用实例（S1 cron / S2 trigger 路 B / S3 event）→ 派生事件路 A / 路 B 与两类生产者 → 五场景全表 → 可靠性清单、已定结论、开放问题与下一步 |
| [history/](./history/) | 历史版本留档：v0.1（11 页，假设 openClaw 无 checker / 需自建 Task 表与 `/hooks/events` 入口层 / 九件工具 / 抢票走 command 特例；核实原生 `cron` 工具能力后被 v0.2 取代）、v0.2（12 页，γ 方案首版；工具边界与订阅归属未定稿、S5 独占半页且路 B 流程图有遮挡，被 v0.3 取代）、v0.3（13 页，定稿工具边界与订阅归属、新增工具可见范围页；缺运行时视图且外部服务简写 EMS 不直观，被 v0.4 取代）、v0.4（15 页，新增两页时序图、EMS 改名事件中心；事件入口只有一句 POST 未展开，被 v0.5 取代） |

## 核心结论（v0.5）

1. **一个任务工具 + 一个只读工具**：模型只面对 openClaw 原生 `cron` 工具（`at / every / cron / stream` 是它 `schedule.kind` 的取值，
   不是多个工具）和只读的 `event_catalog`；job 表就是任务表。γ 方案：新增 `schedule.kind="event"` + Gateway 内部事件中心适配器 +
   信封拼装 + `payload.message` 编译模板；v0.1 的 Task 表、`/hooks/events` 入口层、九件工具整体取消。
2. **订阅由 cron service 内部完成**：用户说"到家时帮我 xxx"，模型只调一次 `cron add(schedule.kind=event)`；cron service 处理 add 时
   内部调 `EventHub.subscribe`，订阅方是 openClaw Gateway 单一主体，每条订阅带 `job_id`。subscribe / unsubscribe / pause 不是工具，
   job 拥有订阅生命周期（add / update / enabled / remove / 启动对账 / 未知 job_id 退订）。
3. **门控归事件中心**：`filter / guards` 由模型写在订阅里、openClaw 原样转发、事件中心评估；openClaw 侧对事件只做四件事：
   订阅转发、`event_id` 去重、`occurred_at` 过期、拼信封起 agentTurn。
4. **`event_publish` 主 loop 不可见**：trigger / script 脚本可用；agentTurn 按 job `toolsAllow` 放开、默认关。
5. **三种触发，一条执行路径**：时间（原生）、条件轮询（原生 `trigger`）、外部事件（新增 event kind）；执行统一为 isolated agentTurn。
6. **运行上下文 = 冻结的任务定义**：系统身份（可 lightContext）+ 事件事实（显式标外部数据）+ `payload.message` 三段
   （原话 / 编译补充 / 策略）+ contextMessages（创建时冻结）+ `last_run_summary` 一行；不读主对话历史。
7. **路 B 为目标形态，生产者分两类**：规则判定型（trigger + script → `event_publish`）、模型判定型（agentTurn + `event_publish`，
   用于"发布会结束了吗"这类需要语义判断的派生事件）；私有一次性判定走路 A。
8. **事件入口分传输与点火两段（v0.5 新增页）**：传输是可替换的入口适配器（默认 webhook 复用原生 hooks 基建，同机可切本机直调，
   长连接留扩展，轮询只做兜底）；点火不走原生 `/hooks/agent`（它不认识 job），而是薄入口 `/hooks/eventhub` → cron service 内部
   `fireJob(jobId, event)` → 与定时到点完全同一段 `runJob`；受理即回 200、执行异步；2xx 表示"别再重试"，仅 Gateway 内部错误回 5xx；
   幂等键 event_id + job_id 存 SQLite 24h；同 job 串行、跨 job 并行。
9. **运行时视图（v0.4 新增两页时序）**：S3 全链路 12 步只有 5 步有模型参与（创建期 4 步 + 执行期 1 步），其余零 token；
   run 状态机 queued → running → (waiting) → ok / error / skipped，job（订阅，长期）与 run（一次触发，短期）分离。
   路 B 的两条 job 各自独立留 run 记录，第 7 步之后与单事件路径完全相同。
10. **S5 抢票无特殊机制**：两条 `at` job（current 确认 → 运行中自建 isolated 执行）+ 支付前 `ask_user`；时效问题搁置。

## 开放问题

- 事件中心与 Gateway 的部署关系（同进程 / 同机 / 跨设备）与事件中心的推送能力（仅 HTTP POST 还是有长连接）、重试策略——决定入口默认选 webhook 还是本机直调。
- cron service 内部 `fireJob` / `runJob` 的函数边界待到源码核实（目前依据工具描述与文档，stream kind 是先例）。

- current 运行中能否 `cron add`（工具描述对 automation-run 的限制是否只针对 isolated；影响 S5 两阶段落地方式）。
- `filter` 表达式语言与事件中心对齐（openClaw 不解释，跟事件中心现有的走）。
- `event_publish` 在 agentTurn 里的 toolsAllow 默认策略（倾向默认关、仅模型判定型生产者 job 放开）。
- S5 抢票统一走模型后的时效（搁置，整体方案定后单独评估）。
