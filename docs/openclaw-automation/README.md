# openClaw 自动化任务：定时 + 事件订阅 + 模型判定触发统一方案

从"每天早上 9 点帮我干 xxx"出发，把 openClaw 的定时任务能力扩展到事件驱动的自动化
（明天下雨 / 到家 / 收到某人电话 / 火车放票抢票），再扩展到**"当 xxxx 时"写不成脚本、要 Agent loop 才能判断**的条件触发
（股票分档抛售 / 狗上沙发驱赶 / 开售后买卧铺没买到继续盯 / 曼联持续领先 30 分钟通知张三）。
架构以 openClaw 为基础、按需新增。前提假设：存在一个统一的**事件中心（EventHub）**，
订阅即推送，filter / guards 在事件中心侧评估，有 publish 接口。订阅由 openClaw Gateway 内部完成，模型不调订阅工具。

> 命名约定：中文统一叫"事件中心"，代码 / 字段 / 端点用 `EventHub`（如 `EventHub.subscribe`、`/hooks/eventhub`），
> 模型可见的两个工具叫 `event_catalog`（只读查目录）和 `event_publish`（发派生事件）；判定 agentTurn 的收口工具叫 `trigger_result`。v0.3 及以前写作 EMS。

## 目录

| 文件 | 内容 |
| --- | --- |
| [openClaw自动化任务方案.slides.v1.0.html](./openClaw自动化任务方案.slides.v1.0.html) | **整体方案幻灯片（当前版本 v1.0，18 页）**：目标与场景归类（S1–S5 基础 + S6–S9 复杂，**四种触发**：时间 / 脚本轮询 / 模型判定轮询 / 外部事件；G2 改为"触发尽量不过模型，过模型的触发受约束"）→ openClaw 原生 `cron` 工具全貌（层级图：一个工具，`schedule.kind ∈ at / every / cron / stream / event`，**`trigger.kind ∈ script / agent(新增)`**）→ session 四选一与默认 isolated、跨次记忆三层级 → 三方归属表（含 `trigger.kind="agent"` 新增行）与 α β γ 三方案对比、选 γ、谁来订阅 → 整体架构（cron service 唯一中枢，四种触发汇入同一条执行路径；触发层新增"模型判定 checker"）→ 新增 `schedule.kind="event"` 规格与事件中心契约、投递语义 → 事件入口：传输 × 点火 → 工具可见范围 × 订阅生命周期（表 1 新增"判定 agentTurn"列与 `trigger_result` 行：判定阶段只读）→ 端到端时序 ①（S3 到家）→ 端到端时序 ②（S2 路 B；生产者 ② 改为 `trigger.kind=agent`）→ 上下文组织（信封 ② 在 trigger fire 时换成 `<trigger_result>`）→ 七步编译（第 2 步改为成本阶梯 event → script → agent，可级联做门；时序条件必落 state）与 `payload.message` 三段模板 → 工具调用实例（S1 / S2 / S3）→ 派生事件路 A / 路 B（A / B 与 script / agent 两维正交）→ **新增 P15 `trigger.kind="agent"` 规格：三种落法（A 一体 / B 发事件 / C 新 kind，选 C）、六条约束（`trigger_result` 结构化收口、state 是核心、判定只读、预算、滞回、失败不算 fire）、S9 完整 `cron add` 实例、三层级联门（事件·时间 → 脚本 → 模型）** → 五个基础场景全表 → **新增 P17 四个复杂场景验证（S6 分支 / S7 嵌套 / S8 动作反馈监视 / S9 嵌套 + 时序）：门 / 判定 / state / 动作 / 高危 / 缺口逐列；三个结论：嵌套与时序不需要新原语、预授权 vs G6 待拍板、run→state 回流 / `endAt` / waiting 期间 fire 合并留实现期** → 可靠性清单（新增判定抖动 / 失控成本 / 越权 / 失败误触发四行）、已定结论、开放问题与下一步 |
| [history/](./history/) | 历史版本留档：v0.1（11 页，假设 openClaw 无 checker / 需自建 Task 表与 `/hooks/events` 入口层 / 九件工具 / 抢票走 command 特例；核实原生 `cron` 工具能力后被 v0.2 取代）、v0.2（12 页，γ 方案首版；工具边界与订阅归属未定稿、S5 独占半页且路 B 流程图有遮挡，被 v0.3 取代）、v0.3（13 页，定稿工具边界与订阅归属、新增工具可见范围页；缺运行时视图且外部服务简写 EMS 不直观，被 v0.4 取代）、v0.4（15 页，新增两页时序图、EMS 改名事件中心；事件入口只有一句 POST 未展开，被 v0.5 取代）、v0.5（16 页，新增事件入口传输 × 点火页；条件触发只有脚本一种判定者，模型判定仅作为路 B 生产者 ② 的特例出现，"写不成脚本的条件"被判为不支持，被 v1.0 取代） |

## 核心结论（v1.0）

1. **一个任务工具 + 一个只读工具**：模型只面对 openClaw 原生 `cron` 工具（`at / every / cron / stream` 是它 `schedule.kind` 的取值，
   不是多个工具）和只读的 `event_catalog`；job 表就是任务表。γ 方案：新增 `schedule.kind="event"` + `trigger.kind="agent"` +
   Gateway 内部事件中心适配器 + 信封拼装 + `payload.message` 编译模板；v0.1 的 Task 表、`/hooks/events` 入口层、九件工具整体取消。
2. **四种触发，一条执行路径**：时间（原生）、脚本轮询（原生 `trigger.script`）、**模型判定轮询（新增 `trigger.kind="agent"`）**、
   外部事件（新增 event kind）；执行统一为 isolated agentTurn，全部经同一段 `runJob`。
3. **模型判定型触发（v1.0 新增）**："当 xxxx 时"写不成脚本（看图 / 读页面 / 语义判断 / 多步查证）时，判定者从脚本换成受限 agentTurn，
   `{fire, message, state}` 契约、fire:false 静默、state 跨 tick 三件事全部沿用。六条约束：只能通过 `trigger_result` 结构化收口；
   state（≤16KB）由模型维护——**嵌套 = state.phase，时序条件 = state 里的时间戳**；判定阶段只读（无 cron / event_publish / 写工具）；
   预算（小模型 + lightContext + 60s + maxToolCalls + maxChecksPerDay）；滞回（consecutive N + cooldown）由 checker 实现；
   **模型 checker 失败不算 fire**（与脚本 checker 相反）。三层级联门：事件·时间门 → 脚本门 → 模型判定，模型放最后一层。
   三种落法中选 C（新 trigger kind），A（every + agentTurn 一体）作零代码过渡，B（发事件）留给结果要复用的场合。
4. **订阅由 cron service 内部完成**：用户说"到家时帮我 xxx"，模型只调一次 `cron add(schedule.kind=event)`；cron service 处理 add 时
   内部调 `EventHub.subscribe`，订阅方是 openClaw Gateway 单一主体，每条订阅带 `job_id`。subscribe / unsubscribe / pause 不是工具，
   job 拥有订阅生命周期（add / update / enabled / remove / 启动对账 / 未知 job_id 退订）。
5. **门控归事件中心**：`filter / guards` 由模型写在订阅里、openClaw 原样转发、事件中心评估；openClaw 侧对事件只做四件事：
   订阅转发、`event_id` 去重、`occurred_at` 过期、拼信封起 agentTurn。事件中心 filter 逐事件无状态，"持续 / 连续 / N 分钟后"类时序条件不能寄望 filter。
6. **`event_publish` 主 loop 与判定阶段不可见**：trigger / script 脚本可用；动作 agentTurn 按 job `toolsAllow` 放开、默认关。
7. **运行上下文 = 冻结的任务定义**：系统身份（可 lightContext）+ 事件事实（显式标外部数据；trigger fire 时为 `<trigger_result>` 证据摘要 + state 快照）
   + `payload.message` 三段（原话 / 编译补充 / 策略）+ contextMessages（创建时冻结）+ `last_run_summary` 一行；不读主对话历史。
8. **路 B 为目标形态，两维正交**：A / B 决定 payload 是动作还是 publish；script / agent 决定谁来判定。生产者 ② 模型判定型 = 模型判定触发的"结果要复用"用法，
   不是独立机制；私有一次性判定（含 S6–S9）走路 A。
9. **事件入口分传输与点火两段**：传输是可替换的入口适配器（默认 webhook 复用原生 hooks 基建）；点火走 `/hooks/eventhub` → `fireJob` → 与定时到点同一段 `runJob`；
   受理即回 200、执行异步；幂等键 event_id + job_id 存 SQLite 24h；同 job 串行、跨 job 并行。
10. **四个复杂场景全部一条 job 落地（v1.0 新增页）**：S6 分支 = checker 算档 + 动作 message 里的分支表；S7 嵌套 = state.phase（不再依赖运行中建子 job）；
    S8 动作反馈 = 成功 `cron remove` 自己、失败 run 结束监视自然继续；S9 时序 = state.lead_since。子 job / run 级 wait 从必需降为可选。
11. **S5 抢票无特殊机制**：两条 `at` job（current 确认 → 运行中自建 isolated 执行）+ 支付前 `ask_user`；时效问题搁置。

## 开放问题

- **预授权 vs G6**：S6 / S7 / S9 的卖出 / 对外发送是 G6 的"必确认"，用户意图恰是免确认。倾向：创建期对具体参数与范围显式确认并写进策略段，越界才 `ask_user`；支付暂不放开（S8 仍 `ask_user`）。
- **判定 checker 的模型选型与预算默认值**（哪个小模型、每日上限、S7 类多模态判定成本）。倾向 fast 小模型 + lightContext，默认 maxChecksPerDay 200。
- run → trigger.state 回流（`stateUpdate`）、job `endAt`、同 job 有 run 在 waiting 时新 fire 合并而非排队——实现期在 cron service 内一起做。
- 事件中心与 Gateway 的部署关系（同进程 / 同机 / 跨设备）与事件中心的推送能力、重试策略——决定入口默认选 webhook 还是本机直调。
- cron service 内部 `fireJob` / `runJob` / checker 的函数边界待到源码核实（目前依据工具描述与文档，stream kind 与 trigger.script 是先例）。
- current 运行中能否 `cron add`（影响 S5 两阶段；S7 已不依赖）。
- `filter` 表达式语言与事件中心对齐（openClaw 不解释，跟事件中心现有的走）。
- `event_publish` 在动作 agentTurn 里的 toolsAllow 默认策略（倾向默认关、仅生产者 ② 类 job 放开）。
- S5 抢票统一走模型后的时效（搁置，整体方案定后单独评估）。
