# openClaw 自动化任务：定时 + 事件订阅 + 模型判定触发统一方案

从"每天早上 9 点帮我干 xxx"出发，把 openClaw 的定时任务能力扩展到事件驱动的自动化
（明天下雨 / 到家 / 收到某人电话 / 火车放票抢票），再扩展到**"当 xxxx 时"写不成脚本、要 Agent loop 才能判断**的条件触发
（股票分档抛售 / 狗上沙发驱赶 / 开售后买卧铺没买到继续盯 / 曼联持续领先 30 分钟通知张三）。
架构以 openClaw 为基础、按需新增。前提假设：存在一个统一的**事件中心（EventHub）**，
订阅即推送，单事件 filter 在事件中心侧评估，有 publish 接口；**事件中心不做 CEP、没有 guards**，job 级限额（`limits`）与跨事件组合（多 tick 源 + trigger state）全在 cron service。
订阅由 openClaw Gateway 内部完成，模型不调订阅工具、不感知 debounce / staleAfter 等卫生参数。

> 命名约定：中文统一叫"事件中心"，代码 / 字段 / 端点用 `EventHub`（如 `EventHub.subscribe`、`/hooks/eventhub`），
> 模型可见的两个工具叫 `event_catalog`（只读查目录）和 `event_publish`（发派生事件）；判定 agentTurn 的收口工具叫 `trigger_result`；
> 编译期填槽解析工具四个（`contacts.search / apps.list / bluetooth.paired / places.list`），运行期现况查询一个（`phone_state.get`）。v0.3 及以前写作 EMS。

## 目录

| 文件 | 内容 |
| --- | --- |
| [openClaw自动化任务方案.slides.v2.2.html](./openClaw自动化任务方案.slides.v2.2.html) | **整体方案幻灯片（当前版本 v2.2，29 页，HTML 16:9）**。v2.2 = v2.1 五章结构保留，做三处收敛并新增三页：**⑴ guards 废除 → job 级 `limits`**（`activeWindow / cooldown / maxRunsPerDay / once`，cron service 在 fire → run 之间评估，四种触发共用；debounce / staleAfter 退为目录 internal 默认，模型不写；原则 G4 改为"filter 归事件中心，限额与组合归 cron service"）；**⑵ 事件成为 tick 源**（`schedule.kind="multi"` + `sources[]` 可混排事件与时间，每个 tick 都交给同一个 trigger；tick 契约 `{source, event?, now}`，trigger 返回 `{fire, message, state, nextCheckAt?}`——`nextCheckAt` 自设闹钟与 `trigger.stateSchema` 由 v2.1 建议升级为方案项）；**⑶ 事件目录定稿**（条目 schema 六项可见 + 四项 internal、filter 语法只做单事件布尔、10 组 63 条内建事件静态进编译期 system prompt、五个只读小工具）。新增 **P12 组合条件与限额**（五类组合：单事件布尔 / 跨事件或 / 事件且状态 / 时序且 / 缺席非，各自落法；类型 ④ 完整 `cron add`；sources 与 tick 契约；limits 规格；事件中心不做 CEP 的理由）、**P13 事件目录**（schema · filter 语法一页 · 分组总览）、**P18 三套编译模板**（message 三段 / 判定 prompt 三段 / 组合脚本 T1 事件且状态 · T2 时序且 · T3 缺席非，填槽而非自由写）。存量页同步：架构图与归属表去 guards 加限额器；P4 字段表加 `multi / limits / stateSchema / nextCheckAt`；P7 event 规格改为"模型只写 eventType + filter"；S3 filter 改 `zone == 'home'` + `limits.activeWindow`；S9 改为 `limits.activeWindow + once`、脚本门 `比分变化 || self`、判定用 `nextCheckAt=lead_since+30m`，六 tick 演进表（消除 v2.1 指出的脚本门不一致）；工具可见范围加填槽解析与 `phone_state.get`；九场景全表加 limits 列；第五章 P25–P29 改为新目录样例 / tick 信封 / self tick / "已定 vs 倾向"。首页目录与阅读路线更新，29 页经无头浏览器 1400 / 1100 两种宽度逐页校验无溢出 |
| [02-event-catalog.md](./02-event-catalog.md) | **事件目录规范与内建条目全文**（配套 v2.2 P7 / P12 / P13 / P18）：设计约束（模型只看可见字段、目录静态进 prompt、filter 单事件布尔、事件中心不做 CEP、`occurred_at` 在信封不在 payload）→ 条目 schema（`type / group / desc / fields(!key) / must_filter / pair / state_query` + internal `rate / debounce / stale_after / sensitivity`）与 cron add 校验规则 → filter 语法 BNF 与示例 → 命名与字段规范 → 填槽解析工具与 `phone_state.get` → **10 组 63 条内建条目逐条表**（device 10 / setting 17 / connectivity 13 / geofence 2 / activity 1 / phone 6 / alarm 3 / app 5 / calendar 3 / notification 3，含 internal 默认值）→ 相对原稿的改动清单（`call_received → call_incoming`、`state_on → on`、`ringtone → ringer`、geofence 参数改 must_filter、经纬度 internal、新增 `sms.received / activity.changed / network.type_changed / device.boot` 等） |
| [history/](./history/) | 历史版本留档：v0.1（11 页，假设 openClaw 无 checker / 需自建 Task 表与 `/hooks/events` 入口层 / 九件工具 / 抢票走 command 特例；核实原生 `cron` 工具能力后被 v0.2 取代）、v0.2（12 页，γ 方案首版；工具边界与订阅归属未定稿、S5 独占半页且路 B 流程图有遮挡，被 v0.3 取代）、v0.3（13 页，定稿工具边界与订阅归属、新增工具可见范围页；缺运行时视图且外部服务简写 EMS 不直观，被 v0.4 取代）、v0.4（15 页，新增两页时序图、EMS 改名事件中心；事件入口只有一句 POST 未展开，被 v0.5 取代）、v0.5（16 页，新增事件入口传输 × 点火页；条件触发只有脚本一种判定者，模型判定仅作为路 B 生产者 ② 的特例出现，"写不成脚本的条件"被判为不支持，被 v1.0 取代）、v1.0（18 页，新增 `trigger.kind="agent"` 模型判定触发与 S6–S9 复杂场景验证；页序按迭代追加、无章节结构，多页字号偏小且面板拥挤、S6–S9 在场景页合并成一行，被 v2.0 取代）、v2.0（20 页四章重排 + 版面重做；大模型参与位置散落在各章、判定阶段的输入信封与 `event_catalog` 返回格式未给结构，被 v2.1 取代）、v2.1（26 页，新增第五章模型视角；guards 仍由模型写在订阅里、事件中心承担门控，多事件组合条件与事件目录格式未定义，`next_check_at` / `stateSchema` 只是建议，被 v2.2 取代） |

## 核心结论（v2.2；方案主干与 v1.0–v2.1 一致，第 5 / 6 条按 v2.2 改写，第 14 / 15 条为 v2.2 新增）

1. **一个任务工具 + 几个只读小工具**：模型只面对 openClaw 原生 `cron` 工具（`at / every / cron / stream` 是它 `schedule.kind` 的取值，
   不是多个工具），事件目录静态在编译期 system prompt 里，`event_catalog` 退为 `get(type)` + 派生事件查询；job 表就是任务表。γ 方案：新增 `schedule.kind="event" / "multi"` + `trigger.kind="agent"` +
   job 级 `limits` + tick / `nextCheckAt` / `stateSchema` 契约 + Gateway 内部事件中心适配器 + 信封拼装 + 三套编译模板；v0.1 的 Task 表、`/hooks/events` 入口层、九件工具整体取消。
2. **四种触发，一条执行路径**：时间（原生）、脚本轮询（原生 `trigger.script`）、**模型判定轮询（新增 `trigger.kind="agent"`）**、
   外部事件（新增 event kind）。v2.2 起统一为 **tick → trigger → fire → limits → runJob**：时间、事件、`nextCheckAt` 自触发都只是 tick 源；执行统一为 isolated agentTurn。
3. **模型判定型触发（v1.0 起）**："当 xxxx 时"写不成脚本（看图 / 读页面 / 语义判断 / 多步查证）时，判定者从脚本换成受限 agentTurn，
   `{fire, message, state, nextCheckAt?}` 契约、fire:false 静默、state 跨 tick 三件事全部沿用。六条约束：只能通过 `trigger_result` 结构化收口；
   state（≤16KB）由模型维护并可由 `stateSchema` 校验——**嵌套 = state.phase，时序条件 = state 里的时间戳 + `nextCheckAt` 自设闹钟**；判定阶段只读（无 cron / event_publish / 写工具，可用 `phone_state.get`）；
   预算（小模型 + lightContext + 60s + maxToolCalls + maxChecksPerDay）；滞回 consecutive N 留在 trigger，cooldown / once 归 `limits`；
   **模型 checker 失败不算 fire**（与脚本 checker 相反）。三层级联门：事件·时间门 → 脚本门 → 模型判定，模型放最后一层。
   三种落法中选 C（新 trigger kind），A（every + agentTurn 一体）作零代码过渡，B（发事件）留给结果要复用的场合。
4. **订阅由 cron service 内部完成**：用户说"到家时帮我 xxx"，模型只调一次 `cron add(schedule.kind=event)`；cron service 处理 add 时
   内部调 `EventHub.subscribe`，订阅方是 openClaw Gateway 单一主体，每条订阅带 `job_id`。subscribe / unsubscribe / pause 不是工具，
   job 拥有订阅生命周期（add / update / enabled / remove / 启动对账 / 未知 job_id 退订）。
5. **filter 归事件中心，限额与组合归 cron service（v2.2 改写）**：模型在 `schedule` 里只写 `eventType + filter`，filter 只做单事件布尔（字段 ∈ 目录 `fields`、无函数无时间、`must_filter` 字段必须约束）；
   cron service 订阅时从目录 internal 带上 debounce / staleAfter。**guards 废除**，换成 job 级 `limits {activeWindow, cooldown, maxRunsPerDay, once}`，四种触发共用，在 fire → run 之间评估，
   只在用户明说或提议被确认时写，运行期模型零感知。跨事件的与 / 或 / 非 / 时序 / 缺席全部落 `multi.sources` + trigger state，事件中心不做 CEP。
6. **工具面（v2.2 改写）**：`event_publish` 主 loop 与判定阶段不可见，trigger / script 脚本可用，动作 agentTurn 按 `toolsAllow` 放开、默认关；
   编译期新增四个只读填槽解析工具（显示名 → key 字段写进 filter），运行期新增只读 `phone_state.get`（组合条件的状态门、判定 prompt 的现况查询）。
7. **运行上下文 = 冻结的任务定义**：系统身份（可 lightContext）+ 事件事实（显式标外部数据；trigger fire 时为 `<trigger_result>` 证据摘要 + state 快照）
   + `payload.message` 三段（原话 / 编译补充 / 策略）+ contextMessages（创建时冻结）+ `last_run_summary` 一行；不读主对话历史。
8. **路 B 为目标形态，两维正交**：A / B 决定 payload 是动作还是 publish；script / agent 决定谁来判定。生产者 ② 模型判定型 = 模型判定触发的"结果要复用"用法，
   不是独立机制；私有一次性判定（含 S6–S9）走路 A。
9. **事件入口分传输与点火两段**：传输是可替换的入口适配器（默认 webhook 复用原生 hooks 基建）；点火走 `/hooks/eventhub` → `onTick`（去重 → 过期 → 回 200 → trigger → limits）→ 与定时到点同一段 `runJob`；
   受理即回 200、执行异步；幂等键 event_id + job_id 存 SQLite 24h；同 job 串行、跨 job 并行。
10. **四个复杂场景全部一条 job 落地**：S6 分支 = checker 算档 + 动作 message 里的分支表；S7 嵌套 = state.phase（不再依赖运行中建子 job）；
    S8 动作反馈 = 成功 `cron remove` 自己、失败 run 结束监视自然继续；S9 时序 = state.lead_since + `nextCheckAt`（判定在开始领先时自设 30 分钟闹钟，脚本门放行 self tick；once 由 limits 收尾）。子 job / run 级 wait 从必需降为可选。
11. **S5 抢票无特殊机制**：两条 `at` job（current 确认 → 运行中自建 isolated 执行）+ 支付前 `ask_user`；时效问题搁置。
12. **文档组织（v2.0）**：四章二十页——① 总体 → ② 四种触发（按时间 / 脚本轮询 / 外部事件 / 模型判定顺序，每种触发都给完整 `cron add` 实例）→ ③ 执行与编译 → ④ 运行时与验证；
    首页给四条阅读路线（只看结论 / 评审方案 / 做实现 / 核对场景）。版面规则：单页 16:9，正文 clamp(11px, 1.12vw, 15px)，面板与表格拉伸填满、表格纵向居中，
    时序图用 SVG 生成脚本产出（标签不压线、左缘不裁切），全部 20 页经无头浏览器逐页校验无溢出。
13. **模型视角（v2.1 新增第五章）**：大模型只在 **4 + 1 个位置**出场——① 编译期（主 session，唯一读主对话历史的位置；输出 `cron add` + 回读，S9 还要产出给另一个模型的 `trigger.prompt`）、
    ② 判定期（isolated 小模型，输入 = 静态前缀 system + 只读工具 + 判定 prompt 与动态尾部 state 快照 + 新数据，唯一出口 `trigger_result({fire,message,state})`，失败不算 fire）、
    ③ 动作期（isolated，输入五块信封，输出工具调用 + 最终文本 / NO_REPLY，去向由 delivery 决定，写回 `last_run_summary` 一行）、④ current 仅 S5a、⑤ 落法 A 仅作过渡验证。
    三条管线：① → ②③ 靠冻结字段，② → ③ 靠结构化契约，③ → ③ 靠一行摘要；**模型之间没有共享对话**。事件中心 / cron service / 脚本 checker / script payload 全程零 token。
    v2.1 的建议在 v2.2 中已定四项（判定信封结构、判定 prompt / 组合脚本模板、事件目录格式与进入方式、`nextCheckAt`），余 `last_run_summary` 产出方、多模态进判定信封、`NO_REPLY` 与 `announce` 并存三项给倾向。
14. **组合条件（v2.2 新增）**：五类——① 单事件布尔靠 filter；② 跨事件"或"靠 `multi.sources` 无 trigger；③ 事件"且"状态靠 event 源 + `trigger.script` 查 `phone_state.get` / 业务 API（模板 T1）；
    ④ 时序"且"（A 之后 W 内 B）靠两个 event 源 + `state{a_at}`（模板 T2）；⑤ 缺席"非"（A 之后 W 内没有 B）靠 `state{deadline}` + `nextCheckAt` self tick（模板 T3）。
    tick 契约 `{source:{kind:'event'|'cron'|'every'|'at'|'self', eventType?, index}, event?:{event_id, occurred_at, payload}, now}`；`nextCheckAt` 之前周期 tick 跳过 trigger、事件 tick 仍送达。
    编译期模型对三套模板填槽而不是自由写；更复杂的组合直接写脚本或改 `trigger.agent`；要复用的组合走路 B 发派生事件。
15. **事件目录（v2.2 新增，详见 `02-event-catalog.md`）**：条目 = `type / group / desc / fields(!key) / must_filter / pair / state_query` 六项可见 + `rate / debounce / stale_after / sensitivity` 四项 internal；
    10 组 63 条内建事件一行一条（≈3–4K token）作为编译期 system prompt 静态段；`occurred_at` 在推送信封不在 payload；geofence 经纬度 internal；
    命名规范 `_on/_off`、`_connected/_disconnected`、`enter/exit`，`phone.call_received` 改 `call_incoming`；cron add 时校验 eventType 在目录、filter 字段 ∈ fields、枚举值合法、must_filter 已约束。

## 开放问题

- **（模型 I/O 层面，v2.2 后余三项）** `last_run_summary` 由谁产出（倾向：动作模型最终文本首行即摘要，NO_REPLY 时 cron service 用工具调用列表拼一行）、多模态输入（S7 快照）如何进判定信封（倾向：gate 预取塞进 tick 块）、`NO_REPLY` 与 `announce` 并存语义（倾向：抑制渠道发送、主 session 摘要仍发）——见 P29。
- **toolsAllow 参数级约束**（收件人 ∈ 白名单、maxCalls）是否纳入本期：作为预授权的机械校验落法，倾向纳入（P28）。
- **`limits.activeWindow` 窗外**是否仍执行带 state 的 script trigger 以维护 state：倾向执行（零 token），实现期确认成本。

- **预授权 vs G6**：S6 / S7 / S9 的卖出 / 对外发送是 G6 的"必确认"，用户意图恰是免确认。倾向：创建期对具体参数与范围显式确认并写进策略段，越界才 `ask_user`；支付暂不放开（S8 仍 `ask_user`）。
- **判定 checker 的模型选型与预算默认值**（哪个小模型、每日上限、S7 类多模态判定成本）。倾向 fast 小模型 + lightContext，默认 maxChecksPerDay 200。
- run → trigger.state 回流（`stateUpdate`）、同 job 有 run 在 waiting 时新 fire 合并而非排队——实现期在 cron service 内一起做（job `endAt` 已由 `limits.activeWindow` 绝对区间覆盖）。
- 事件中心与 Gateway 的部署关系（同进程 / 同机 / 跨设备）与事件中心的推送能力、重试策略——决定入口默认选 webhook 还是本机直调。
- cron service 内部 `onTick` / `runJob` / checker 的函数边界待到源码核实（目前依据工具描述与文档，stream kind 与 trigger.script 是先例）。
- current 运行中能否 `cron add`（影响 S5 两阶段；S7 已不依赖）。
- `filter` 语法已在 P13 / `02-event-catalog.md` 固定为单事件布尔子集；事件中心若已有表达式引擎，需确认是该子集的超集。
- `event_publish` 在动作 agentTurn 里的 toolsAllow 默认策略（倾向默认关、仅生产者 ② 类 job 放开）。
- S5 抢票统一走模型后的时效（搁置，整体方案定后单独评估）。
