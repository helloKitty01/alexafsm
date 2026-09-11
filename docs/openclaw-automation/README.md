# openClaw 自动化任务：定时 + 事件订阅 + 脚本 / 模型判定触发统一方案

从"每天早上 9 点帮我干 xxx"出发，把 openClaw 的定时任务能力扩展到事件驱动的自动化
（明天下雨 / 到家 / 收到某人电话 / 火车放票抢票），再扩展到条件触发（股票分档抛售 / 狗上沙发驱赶 / 开售后买卧铺没买到继续盯 / 曼联持续领先 30 分钟通知张三）
与**跨事件 / 跨状态的组合条件**（到家且电量低 / 到家后 10 分钟内来电 / 离开公司 1 小时还没到家）。
架构以 openClaw 原生 `cron` 为基础、按需新增。前提假设：存在一个统一的**事件中心（EventHub）**，订阅即推送，单事件 filter 在事件中心侧评估，有 publish 接口；
**事件中心不做 CEP**，判定（trigger state）、限额（`limits`）、自设闹钟（`nextCheckAt`）全在 cron service。订阅由 openClaw Gateway 内部完成，模型不调订阅工具、不感知 debounce / staleAfter。

> 命名约定：中文统一叫"事件中心"，代码 / 字段 / 端点用 `EventHub`（如 `EventHub.subscribe`、`/hooks/eventhub`）。
> v3.0 模型可见的新工具只有三个：`phone.lookup(kind, q)`（只读；kind ∈ contacts / apps / bluetooth / places / state）、`event_publish`（仅 payload script）、`trigger_result`（仅判定 agent）。
> 大小写：job JSON 字段 camelCase（`staleAfter / nextCheckAt / maxRunsTotal`），事件目录 yaml 与事件 payload snake_case（`stale_after / must_filter / contact_id`）；点火入口叫 `onTick`。
> 九个核心名词（tick / trigger / fire / limits / run / filter / nextCheckAt / state / 派生事件）的定义见主稿 P5。v0.3 及以前写作 EMS。

## 目录

| 文件 | 内容 |
| --- | --- |
| [openClaw自动化任务方案.slides.v3.0.html](./openClaw自动化任务方案.slides.v3.0.html) | **主稿幻灯片（当前版本 v3.0，16 页，HTML 16:9）**。v3.0 是**收敛版**：新增从 9 项收到 5 项（event 源 + 适配器 / tick + nextCheckAt / limits / trigger.agent / 编译期支撑）、新工具从 7 个收到 3 个、字段集收到一页写完（P6）；**判定默认用原生 `trigger.script`，十二个场景里只有 S7 必须过模型**（S8 / S9 视有无结构化 API）；**六项拍板**（D1 fire = "需要执行一次 payload"而非"条件为真"、D2 脚本运行时边界与"失败 = fire:false"、D3 预授权分期、D4 跨 session ask_user 路径与强制 announce、D5 事件入口默认 webhook + `stream` 零改动验证、D6 activeWindow 窗外仍维护 state）。四章：① 总体（十二场景谁叫醒谁判定 / 架构 / 原生复用 vs 五项新增）→ ② 核心模型（一条路与名词 / 最小字段集 / 事件源 / trigger / limits 与 nextCheckAt / 组合条件一种写法 / 派生事件只差 payload）→ ③ 编译与执行 → ④ 验证与拍板（十二场景全表 / S3 时序 / 拍板 · 可靠性 · 分期 · 待核实 V1–V6）。16 页经无头浏览器 1100 / 1334 / 1700 三宽度逐页校验无溢出、无面板内溢出 |
| [openClaw自动化任务方案.附录.slides.v3.0.html](./openClaw自动化任务方案.附录.slides.v3.0.html) | **附录幻灯片（v3.0，10 页）**：实现者才需要的细节——A2 事件目录 schema 与 10 组 63 条总览、A3 filter 语法 EBNF / 校验四条 / 写不了的归哪、A4 三套编译模板（message 三段 / 判定 prompt 三段 / 组合脚本三例）、A5 时序 ②（S2 派生事件两条 job 接力）、A6 三个模型出场位置与三条管线、A7 判定期单 tick 信封（S9 agent 变体）、A8 动作期信封（S9 与 S3 对照）、A9 事件入口传输四选一与 `stream` 零改动验证路径、A10 v2.3 → v3.0 砍了什么 / 改了什么 / 为什么。10 页同样三宽度校验无溢出 |
| [02-event-catalog.md](./02-event-catalog.md) | **事件目录规范与内建条目全文**（配套主稿 P7 / P10 与附录 A2 / A3 / A4）：设计约束（模型只看可见字段、目录含派生条目静态进 prompt、filter 单事件布尔、事件中心不做 CEP、`occurred_at` 在信封不在 payload）→ 条目 schema（`type / group / desc / fields(!key) / must_filter / pair / state_query` + internal `rate / debounce / stale_after / sensitivity`）与 cron add 校验规则 → 派生事件条目登记（生产者 `payload.publishes` 声明、`catalog.register`、group 不复用内建组、internal 推导）→ filter 语法 BNF 与示例 → 命名与字段规范（camelCase / snake_case 两套各归各位）→ **唯一只读查询工具 `phone.lookup`（v3.0 合并原四个解析工具与 `phone_state.get`）** → **10 组 63 条内建条目逐条表**（device 10 / setting 17 / connectivity 13 / geofence 2 / activity 1 / phone 6 / alarm 3 / app 5 / calendar 3 / notification 3，含 internal 默认值）→ 相对原稿的改动清单 |
| [history/](./history/) | 历史版本留档：v0.1（11 页，假设 openClaw 无 checker / 需自建 Task 表与 `/hooks/events` 入口层 / 九件工具 / 抢票走 command 特例；核实原生 `cron` 工具能力后被 v0.2 取代）、v0.2（12 页，γ 方案首版；工具边界与订阅归属未定稿，被 v0.3 取代）、v0.3（13 页，定稿工具边界与订阅归属、新增工具可见范围页；缺运行时视图，被 v0.4 取代）、v0.4（15 页，新增两页时序图、EMS 改名事件中心；事件入口未展开，被 v0.5 取代）、v0.5（16 页，新增事件入口传输 × 点火页；"写不成脚本的条件"被判为不支持，被 v1.0 取代）、v1.0（18 页，新增 `trigger.kind="agent"` 与 S6–S9；无章节结构、版面拥挤，被 v2.0 取代）、v2.0（20 页四章重排 + 版面重做；模型参与位置散落，被 v2.1 取代）、v2.1（26 页，新增第五章模型视角；guards 仍由模型写在订阅里，被 v2.2 取代）、v2.2（29 页，guards 废除改 job 级 limits、事件成为 tick 源、目录与三套模板定稿；核心名词无正式定义，被 v2.3 取代）、v2.3（30 页，新增一条路与九个名词定义、场景扩到十二个、派生事件页重写为 2×2；**机制堆叠过多**——`multi` / `gate` / `hysteresis` / `budget` / `once` / T1–T3 / 路 A / 7 个工具 / `current`，S6 / S9 不必要地用模型判定，脚本运行时边界、跨 session ask_user、预授权、S7 "下沙发停音"与一条路冲突等关键点未定，被 v3.0 取代） |

## 核心结论（v3.0）

1. **一个任务工具 + 三个只读小工具**：模型只面对 openClaw 原生 `cron` 工具（`at / every / cron / stream / event` 是 `schedule.kind` 的取值，不是多个工具）；事件目录（内建 63 条 + 已登记派生条目）静态在编译期 system prompt 里，没有目录查询工具；新工具只有 `phone.lookup`（只读查询）、`event_publish`（payload script 发派生事件）、`trigger_result`（判定 agent 唯一出口）。job 表就是任务表。
2. **一条路，三道门**：`tick → trigger → fire → limits → run`。tick 三种来源（时间到点 / 订阅事件到达 / `nextCheckAt` self 闹钟）全部进 `onTick`；filter（事件中心）答"这件事值不值得叫醒我"，trigger（checker）答"现在需要动作吗"，limits（cron service）答"此刻该不该跑"。凡 filter 写不了的不扩 filter，分别归 limits 与 trigger。**fire 的定义（D1）= trigger 认为需要执行一次 payload**，trigger 负责检测跃迁（进入阈值 / 上下沙发 / 到点仍领先），`message` 告诉动作模型是哪个跃迁——S6 分档、S7 上 / 下沙发因此一条 job 成立。
3. **最小字段集（P6）**：`schedule {kind, sources[{eventType, filter}]}`（event 时 1..n 个源，没有 `multi`）；`trigger {kind: script|agent, script, prompt, state, stateSchema, toolsAllow}`（agent 时 `script` 是零 token 前置门，同一契约）；`limits {activeWindow, cooldown, maxRunsPerDay, maxRunsTotal, maxChecksPerDay}`（全部可选，用户明说才写）；`payload {kind, message, toolsAllow, publishes}`；`sessionTarget`（默认 isolated，不用 current）；`delivery`。契约 `trigger(tick, state) → {fire, message, state, nextCheckAt?}`，与原生 `trigger.script` 相同，只多一个可选 `nextCheckAt`。
4. **判定默认是脚本，模型是例外（G2）**：有结构化数据源（行情 / 比分 / 余票 / 预报 API、`phone.lookup(state)`）一律 `trigger.script`，零 token；只有看图（S7）、读非结构化页面（S8 / S9 无 API 时）才 `trigger.agent`，且必须配前置 script 门与 `maxChecksPerDay`。S6 / S9 在 v2.x 用 agent 只因没假设 API，v3.0 一律先脚本。十二个场景里只有 S7 必须过模型。
5. **脚本运行时边界（D2）**：cron service 进程内沙箱；能读 `tick` / `trigger.state`；只能 `tools.call` toolsAllow 内的只读工具；不能 cron / event_publish / 写工具；30s / 5 次调用 / state ≤16KB；**失败 = fire:false + check error，state 保留旧值**（不沿用原生"失败算 fire"，避免误动作）。这是全部数值规则场景成立的前提。
6. **limits 与 nextCheckAt**：limits 在 fire 与 run 之间，job 级、四种叫醒源共用；`once` 改为 `maxRunsTotal: 1`；activeWindow 窗外事件 / self tick 仍进 trigger 维护 state（D6）。`nextCheckAt` **只加一个 self tick、不减任何 tick**（v2.2 "此前周期 tick 跳过"的语义取消，成本靠前置 script 与 activeWindow）；新值覆盖、`null` 作废。S9 有 API 时 155 个 tick 全是脚本、零 token，22:40 self tick fire 一次。
7. **组合条件一种写法（P10）**：与 / 或 / 之后 / 没有全是 `sources[]` + 一段 `trigger.script`——"或"= sources 两个无 trigger；"事件且状态"= 脚本查 `phone.lookup(state)`；"A 之后 W 内 B"= state 记 `a_at`；"A 之后 W 内没有 B"= state 记 `deadline` + `nextCheckAt`。不给模板编号，不加原语，事件中心不做 CEP。
8. **事件源（P7）**：模型只写 `eventType + filter`；cron service 处理 add 时按 sources 逐条 `EventHub.subscribe(filter + 目录默认 debounce / staleAfter, tag=job_id)`，订阅是 job 的副作用（add / update 差集 / enabled / remove / 启动对账）。入口四步：鉴权找 job → event_id 去重 24h → occurred_at 过期 → 先回 200 再 `onTick`。三句承诺：事件不丢、动作不重复、过期不执行。
9. **派生事件只差 payload 一个字段（P11）**：默认是普通 job；结果要复用时 payload 改 `script → event_publish(type, payload)` 并带 `publishes {type, desc, fields}` 登记目录，消费者是普通 event job。两层 limits（生产侧管事件发几次、消费侧各管自己）。编译规则：单用途只关我 → 普通 job；公共事实或两个以上用途 → 派生事件；拿不准 → 普通 job。"路 A"这个名字取消。
10. **编译（P12）**：主 loop 六步——路由 → 选叫醒源与判定者（成本阶梯）→ `phone.lookup` 填槽 → 写判定与限额 → message 三段 + 显式 sessionTarget / toolsAllow / delivery → 回读一句 → `cron add`。**S5 的车次 / 席别 / 代付在这一步问清**，S5 变成一条 `at` job，不再需要 current 与运行中 cron add。
11. **执行（P13）**：isolated 默认；四种上下文的工具面（主 loop / trigger script / 判定 agent / 动作 agentTurn）；五块信封 = 触发头 + 触发事实（标 external-data）+ 冻结的 message 三段 + contextMessages + `last_run_summary`，不读主对话。**跨 session ask_user（D4）**：run 进 waiting → 问题经 delivery 渠道送达 → 答复回 run；可能 ask_user 的 job 强制 announce；超时 → error + failureAlert。
12. **预授权分期（D3 / G6）**：一期支付 / 卖出 / 对外发送一律 ask_user；二期在 toolsAllow 加参数级约束（`messaging.send.to ∈ {…}`、`maxCalls`）后，创建期确认过的范围免确认；支付永远 ask_user。
13. **十二场景全表（P14）**：S1 cron；S2 cron + script 查预报（单用途 agentTurn / 多用途 publish）；S3 event geofence.enter + limits；S4 event phone.call_incoming；S5 一条 at；S6 every + script 跃迁 fire，stage=2 后 `cron remove` 自己；S7 every 30s + agent（前置 script 有运动 || self），三个跃迁 play / notify / stop；S8 every 30s + script（无 API 则 agent），cooldown 2m，成功自删；S9 every 1m + script + nextCheckAt，maxRunsTotal 1；S10 event + script 查电量；S11 event ×2 + state a_at；S12 event ×2 + state deadline + nextCheckAt。
14. **分期**：一期全是确定性逻辑（event 源 + 适配器、tick + nextCheckAt、limits、目录进 prompt + `phone.lookup`、`event_publish`、D2 脚本边界），覆盖 S1–S6、S8 / S9（有 API）、S10–S12；二期 `trigger.agent` + `trigger_result` + stateSchema、参数级 toolsAllow 约束、预授权放开，覆盖 S7 与无 API 变体。
15. **动手前到源码核实（V1–V6）**：`trigger.script` 沙箱能力与失败默认语义；`stream` kind 的 tick 语义；自动化 run 里 `cron remove` 自己对 isolated 是否放开；run waiting 的 ask_user 送达与恢复；toolsAllow 是否支持参数级约束；`at` 自删能否配到 every / event。
16. **文档组织（v3.0）**：主稿 16 页讲逻辑与每个场景，附录 10 页放规格细节、模板、模型视角与变更记录；`02-event-catalog.md` 是目录全文。版面规则沿用 v2.0：单页 16:9、正文 clamp(11px, 1.12vw, 15px)，无头浏览器三宽度逐页校验，既查页面溢出也查面板内溢出。

## 开放问题

- **openClaw 源码事实 V1–V6**（见主稿 P16）：都是"核实后照写"的事实，不是设计分歧；V1 若原生脚本失败语义不可配，D2 需要在 checker 外包一层。
- **判定模型选型与默认预算**（哪个小模型、`maxChecksPerDay` 默认 200 是否合适、S7 多模态成本）——二期。
- **模型 I/O 细节三项**（附录 A6–A8）：`last_run_summary` 由谁产出（倾向动作模型最终文本首行，NO_REPLY 时 cron service 用工具调用列表拼一行）；多模态输入如何进判定信封（倾向前置 script 预取塞进 tick 块）；`NO_REPLY` 与 `announce` 并存（倾向抑制渠道发送、主 session 摘要仍发）。
- 事件中心与 Gateway 的部署关系与推送能力——决定 D5 默认 webhook 还是本机直调。
- 派生事件条目的生命周期：生产者 job remove 后条目标 `orphaned` 保留还是级联通知消费者（倾向保留 + 对账时提示）。
- 同 job 有 run 在 waiting 时新 fire 合并而非排队——实现期在 cron service 内做。
- S5 抢票统一走模型后的时效（搁置）。
