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
| [openClaw自动化任务方案.slides.v2.1.html](./openClaw自动化任务方案.slides.v2.1.html) | **整体方案幻灯片（当前版本 v2.1，26 页，HTML 16:9）**。v2.1 = v2.0 四章 20 页原样保留 + 尾部新增**第五章「模型视角」P21–P26**：把大模型当主角，按 4 + 1 个出场位置逐页给出输入信封与输出契约，每页左输入 · 右输出 · 底部契约，贯穿 S3（事件型，最简闭环）与 S9（模型判定型，① ② ③ 全出场）两个例子；"方案已定"与"本章建议"用蓝 / 红两色区分。**⑤ 模型视角（P21–P26）**：出场地图（五位置总表 + 三条冻结管线：① → ②③ 靠冻结字段、② → ③ 靠 `trigger_result` 契约、③ → ③ 靠一行摘要，模型之间没有共享对话）→ 位置 ① 编译期（S3 输入：主对话 / 工具 schema / `event_catalog` 返回样例 / 编译规则；输出：`cron add` + 回读；字段溯源表；S9 差别：还要产出 `trigger.prompt`，建议补「条件 / 步骤 / 输出」判定 prompt 模板）→ 位置 ② 判定期单 tick（S9 22:41 完整输入信封：静态前缀 system + 只读工具 + 判定 prompt，动态尾部 state 快照 + 新数据；输出唯一为 `trigger_result({fire,message,state})`；checker 三种结束方式对照；指出 P11 脚本门与 30 分钟时序条件的不一致）→ 位置 ② 续（四 tick 输入 / 输出 state 对照；信封布局与 KV cache：state 必须放判定 prompt 之后；三个加固建议：`stateSchema` 校验 / state 演进告警 / `state.next_check_at` 自设闹钟）→ 位置 ③ 动作期（S9 五块动作信封与工具调用 / 最终文本 / delivery / `last_run_summary` 输出；S3 对照只有信封块 ② 不同；预授权应在 toolsAllow 层做参数级机械校验）→ 位置 ④ current 与 ⑤ 落法 A 的 I/O、谁不过模型、六项 I/O 层面未定义与倾向。首页目录加第五章与"看模型输入输出"阅读路线，26 页经无头浏览器 1400 / 1100 两种宽度逐页校验无溢出。v2.0 内容：方案结论不变，按"一个工具 · 四种触发 · 一条执行路径"重组为四章，每页左上角带章节标记，首页是目录与四条阅读路线。**① 总体（P2–P5）**：九个场景归类（S6–S9 各自独立成行）与六条原则 G1–G6 → 一页整体架构（对话层 / 中枢 / 触发层 / 执行层，原生 · 新增 · 外部三色标注）→ 原生 `cron` 工具全貌（层级图 + job 字段表）→ 三方归属与 α β γ 选 γ、谁来订阅。**② 四种触发（P6–P11）**：时间 + 脚本轮询（S1 / S2 完整 `cron add`）→ 外部事件 ⑴ `schedule.kind="event"` 规格与字段表、推送 envelope、openClaw 四步 → ⑵ 事件入口：传输四选一 × 点火 `fireJob → runJob` → ⑶ 订阅生命周期 + S3 完整实例与字段来源 → 模型判定 ⑴ 为什么需要 / 三种落法选 C / 六条约束 → ⑵ 三层级联门、与脚本 checker 差别、S9 完整实例 + state 逐 tick 演进表。**③ 执行与编译（P12–P16）**：session 四选一（S5 是唯一用 current 的场景）→ 工具可见范围六列表 → 运行上下文五块信封（isolated 默认栈图）→ 七步编译与 `payload.message` 三段模板 → 派生事件路 A / 路 B 两维正交。**④ 运行时与验证（P17–P20）**：端到端时序 ① S3（12 步，右侧 run 状态机与异常分支）→ 时序 ② S2 路 B 两条 job 接力 → 九个场景全表（schedule / trigger / state / payload / toolsAllow / 高危逐列）→ 可靠性清单、已定结论、开放问题、下一步 |
| [history/](./history/) | 历史版本留档：v0.1（11 页，假设 openClaw 无 checker / 需自建 Task 表与 `/hooks/events` 入口层 / 九件工具 / 抢票走 command 特例；核实原生 `cron` 工具能力后被 v0.2 取代）、v0.2（12 页，γ 方案首版；工具边界与订阅归属未定稿、S5 独占半页且路 B 流程图有遮挡，被 v0.3 取代）、v0.3（13 页，定稿工具边界与订阅归属、新增工具可见范围页；缺运行时视图且外部服务简写 EMS 不直观，被 v0.4 取代）、v0.4（15 页，新增两页时序图、EMS 改名事件中心；事件入口只有一句 POST 未展开，被 v0.5 取代）、v0.5（16 页，新增事件入口传输 × 点火页；条件触发只有脚本一种判定者，模型判定仅作为路 B 生产者 ② 的特例出现，"写不成脚本的条件"被判为不支持，被 v1.0 取代）、v1.0（18 页，新增 `trigger.kind="agent"` 模型判定触发与 S6–S9 复杂场景验证；页序按迭代追加、无章节结构，多页字号偏小且面板拥挤、S6–S9 在场景页合并成一行，被 v2.0 取代）、v2.0（20 页四章重排 + 版面重做；大模型参与位置散落在各章、判定阶段的输入信封与 `event_catalog` 返回格式未给结构，被 v2.1 取代） |

## 核心结论（v2.1；方案主干与 v1.0 / v2.0 一致，第 13 条为 v2.1 新增的模型视角）

1. **一个任务工具 + 一个只读工具**：模型只面对 openClaw 原生 `cron` 工具（`at / every / cron / stream` 是它 `schedule.kind` 的取值，
   不是多个工具）和只读的 `event_catalog`；job 表就是任务表。γ 方案：新增 `schedule.kind="event"` + `trigger.kind="agent"` +
   Gateway 内部事件中心适配器 + 信封拼装 + `payload.message` 编译模板；v0.1 的 Task 表、`/hooks/events` 入口层、九件工具整体取消。
2. **四种触发，一条执行路径**：时间（原生）、脚本轮询（原生 `trigger.script`）、**模型判定轮询（新增 `trigger.kind="agent"`）**、
   外部事件（新增 event kind）；执行统一为 isolated agentTurn，全部经同一段 `runJob`。
3. **模型判定型触发（v1.0 起）**："当 xxxx 时"写不成脚本（看图 / 读页面 / 语义判断 / 多步查证）时，判定者从脚本换成受限 agentTurn，
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
10. **四个复杂场景全部一条 job 落地**：S6 分支 = checker 算档 + 动作 message 里的分支表；S7 嵌套 = state.phase（不再依赖运行中建子 job）；
    S8 动作反馈 = 成功 `cron remove` 自己、失败 run 结束监视自然继续；S9 时序 = state.lead_since。子 job / run 级 wait 从必需降为可选。
11. **S5 抢票无特殊机制**：两条 `at` job（current 确认 → 运行中自建 isolated 执行）+ 支付前 `ask_user`；时效问题搁置。
12. **文档组织（v2.0）**：四章二十页——① 总体 → ② 四种触发（按时间 / 脚本轮询 / 外部事件 / 模型判定顺序，每种触发都给完整 `cron add` 实例）→ ③ 执行与编译 → ④ 运行时与验证；
    首页给四条阅读路线（只看结论 / 评审方案 / 做实现 / 核对场景）。版面规则：单页 16:9，正文 clamp(11px, 1.12vw, 15px)，面板与表格拉伸填满、表格纵向居中，
    时序图用 SVG 生成脚本产出（标签不压线、左缘不裁切），全部 20 页经无头浏览器逐页校验无溢出。
13. **模型视角（v2.1 新增第五章）**：大模型只在 **4 + 1 个位置**出场——① 编译期（主 session，唯一读主对话历史的位置；输出 `cron add` + 回读，S9 还要产出给另一个模型的 `trigger.prompt`）、
    ② 判定期（isolated 小模型，输入 = 静态前缀 system + 只读工具 + 判定 prompt 与动态尾部 state 快照 + 新数据，唯一出口 `trigger_result({fire,message,state})`，失败不算 fire）、
    ③ 动作期（isolated，输入五块信封，输出工具调用 + 最终文本 / NO_REPLY，去向由 delivery 决定，写回 `last_run_summary` 一行）、④ current 仅 S5a、⑤ 落法 A 仅作过渡验证。
    三条管线：① → ②③ 靠冻结字段，② → ③ 靠结构化契约，③ → ③ 靠一行摘要；**模型之间没有共享对话**。事件中心 / cron service / 脚本 checker / script payload 全程零 token。
    本章附带的建议（红色标注、待拍板）：补判定 prompt「条件 / 步骤 / 输出」三段模板；判定信封 state 放判定 prompt 之后以命中 KV cache 前缀；`stateSchema` 校验 + state 演进告警 + `state.next_check_at` 自设闹钟；
    预授权在 toolsAllow 层做参数级机械校验；并指出 P11 脚本门"比分有变化"与 30 分钟时序条件的不一致（门必须能读 state 与 now）。

## 开放问题

- **（v2.1 新增，模型 I/O 层面）** 判定信封结构与判定 prompt 模板、`last_run_summary` 由谁产出、`event_catalog` 返回格式、多模态输入（S7 快照）如何进判定信封、`NO_REPLY` 与 `announce` 并存语义、`state.next_check_at` 是否升级为方案项（P10 六条约束）、toolsAllow 参数级约束是否纳入本期——倾向见 P24 / P26。

- **预授权 vs G6**：S6 / S7 / S9 的卖出 / 对外发送是 G6 的"必确认"，用户意图恰是免确认。倾向：创建期对具体参数与范围显式确认并写进策略段，越界才 `ask_user`；支付暂不放开（S8 仍 `ask_user`）。
- **判定 checker 的模型选型与预算默认值**（哪个小模型、每日上限、S7 类多模态判定成本）。倾向 fast 小模型 + lightContext，默认 maxChecksPerDay 200。
- run → trigger.state 回流（`stateUpdate`）、job `endAt`、同 job 有 run 在 waiting 时新 fire 合并而非排队——实现期在 cron service 内一起做。
- 事件中心与 Gateway 的部署关系（同进程 / 同机 / 跨设备）与事件中心的推送能力、重试策略——决定入口默认选 webhook 还是本机直调。
- cron service 内部 `fireJob` / `runJob` / checker 的函数边界待到源码核实（目前依据工具描述与文档，stream kind 与 trigger.script 是先例）。
- current 运行中能否 `cron add`（影响 S5 两阶段；S7 已不依赖）。
- `filter` 表达式语言与事件中心对齐（openClaw 不解释，跟事件中心现有的走）。
- `event_publish` 在动作 agentTurn 里的 toolsAllow 默认策略（倾向默认关、仅生产者 ② 类 job 放开）。
- S5 抢票统一走模型后的时效（搁置，整体方案定后单独评估）。
