# openClaw 自动化任务：定时 + 事件订阅 + 脚本 / 模型判定触发统一方案

从"每天早上 9 点帮我干 xxx"出发，把 openClaw 的定时任务能力扩展到事件驱动的自动化
（明天下雨 / 到家 / 收到某人电话 / 火车放票抢票），再扩展到条件触发（股票分档抛售 / 狗上沙发驱赶 / 开售后买卧铺没买到继续盯 / 曼联持续领先 30 分钟通知张三）
与**跨事件 / 跨状态的组合条件**（到家且电量低 / 到家后 10 分钟内来电 / 离开公司 1 小时还没到家）。
架构以 openClaw 原生 `cron` 为基础、按需新增。前提假设：存在一个统一的**事件中心（EventHub）**，订阅即推送，单事件 filter 在事件中心侧评估，有 publish 接口；
**事件中心不做 CEP**，判定（trigger state）、配额计数器、自设闹钟（`nextCheckAt`）全在 cron service；叫醒窗口与 cooldown 是 `sources[]` 的属性。订阅由 openClaw Gateway 内部完成，模型不调订阅工具、不感知 debounce / staleAfter。

> 命名约定：中文统一叫"事件中心"，代码 / 字段 / 端点用 `EventHub`（如 `EventHub.subscribe`、`/hooks/eventhub`）。
> 模型可见的新工具只有三个：`phone.lookup(kind, q)`（只读；kind ∈ contacts / apps / bluetooth / places / state）、`event_publish`（仅 payload script）、`trigger_result`（仅判定 agent）。
> 大小写：job JSON 字段 camelCase（`staleAfter / nextCheckAt / maxRunsTotal / lastRunAt`），事件目录 yaml 与事件 payload snake_case（`stale_after / must_filter / contact_id`）；点火入口叫 `onTick`。
> 九个核心名词（tick / filter / window · cooldown / trigger / fire / state · nextCheckAt / run / 配额 / 派生事件）的定义见主稿 P6。

## 目录

| 文件 | 内容 |
| --- | --- |
| [openClaw自动化任务方案.slides.v3.2.html](./openClaw自动化任务方案.slides.v3.2.html) | **幻灯片（当前版本 v3.2，28 页 = 主稿 18 页 + 附录 10 页，单文件 HTML 16:9，滚动式）**。相对 v3.1 做了**模型收拢**与**九张 archify 分章图**两件事。收拢：一条路只剩 `tick → [trigger] → run`，trigger 是 L2 起才有的可选旁路，**fire 降为 trigger 返回值里的一条定义**（不再是节点）；v3.1 的 `limits` 拆成三处——"什么时候叫我"归 `sources[].window / cooldown`（时间源直接写 cron 表达式或 `startAt–endAt`），依赖 run 事实的节流归 trigger（tick 带 `lastRunAt / runsToday`），`maxRunsTotal / maxRunsPerDay / maxChecksPerDay` 是 cron service 的**系统配额**（默认 runs/day 50 · checks/day 200，用户明说才覆盖，到顶暂停告警，不经判定者）；trigger 契约加 `done`（S6 stage_2 / S9 用它收尾，payload 自删只留 S8）；**payload 成本阶梯**：动作在编译期能写成固定工具调用 → `payload.script`（默认，零 token，S3 / S7 / S10 / S11 全程零 token），要生成 / 交互 / 必确认 → agentTurn；D2 脚本边界分两档（trigger 只读 / payload 可写但不能 cron / ask_user，必确认动作 fail-closed）；D6 改为"窗口是叫醒源属性，self 闹钟不受窗口约束"。图：P4 整体架构（architecture）、P6 一条路（workflow）、P10 agent 判定三段（workflow）、P11 S9 领先计时状态机（lifecycle）、P13 派生事件（dataflow）、P17 S3 时序、A5 S2 时序（sequence，替换手写 SVG）、A9 事件入口（dataflow）、A10 S7 跃迁状态机（lifecycle）；全部 `validate --quality showcase` 9/9 后 `deliver`，由 `slide-style/inline_archify.py` 保钩子内联，archify 七类语义色映射到本稿原色板（蓝 = 模型 · 紫 = openClaw · 绿 = 事件中心 · 橙 = 新增 · 红 = 配额 / 回执，**配色不变**）；滚动式 deck 的分章引擎：图进入视口跑一遍 trace，`→` / `←` 对视口内最居中的图逐章高亮（非焦点节点压暗、章内边按序流动、时序图按段压暗），`P` 自动播放 3.2 s / 章，离开视口回全图。28 页经无头浏览器 1100 / 1334 / 1700 三宽度逐页校验无溢出 |
| [archify/](./archify/) | 九张图的 Typed JSON 源与 deliver 出的独立 HTML（答问时打开：`R` 探路、聚焦节点看 Upstream / Downstream、`P` 播放章节；`?theme=light&present=1`）。改图先改 JSON，`validate <type> <json> --quality showcase --json` 9/9 后 `deliver`，再 `python3 ../../slide-style/inline_archify.py <json> <html> --suffix xx` 抽 SVG + 章节内联（见 slide-style/01 第四、六节）|
| [02-event-catalog.md](./02-event-catalog.md) | **事件目录规范与内建条目全文**（配套主稿 P8 / P12 与附录 A2 / A3 / A4）：设计约束（模型只看可见字段、目录含派生条目静态进 prompt、filter 单事件布尔、事件中心不做 CEP、`occurred_at` 在信封不在 payload）→ 条目 schema（`type / group / desc / fields(!key) / must_filter / pair / state_query` + internal `rate / debounce / stale_after / sensitivity`）与 cron add 校验规则 → 派生事件条目登记 → filter 语法 BNF 与示例 → 命名与字段规范 → **唯一只读查询工具 `phone.lookup`** → **10 组 63 条内建条目逐条表**（device 10 / setting 17 / connectivity 13 / geofence 2 / activity 1 / phone 6 / alarm 3 / app 5 / calendar 3 / notification 3，含 internal 默认值）→ 相对原稿的改动清单 |
| [history/](./history/) | 历史版本留档（v0.1 → v3.1 主稿、v3.0 附录，以及合并前单独成册的 v3.1 附录）。v3.1 → v3.2 的差别见下文"v3.2 相对 v3.1" |

## 核心结论

1. **一个任务工具 + 三个只读小工具**：模型只面对 openClaw 原生 `cron` 工具；`schedule` 有单一时间源的简写（`kind: at / every / cron`）和通用形式 `sources[]`（每项 `kind ∈ at / every / cron / event`，1..n，时间与事件可混排）；事件目录（内建 63 条 + 已登记派生条目）静态在编译期 system prompt 里，没有目录查询工具；新工具只有 `phone.lookup`、`event_publish`、`trigger_result`。job 表就是任务表。
2. **一条路，两道可选门**：`tick → [trigger] → run`。tick 三种来源（时间到点 / 订阅事件到达 / `nextCheckAt` self 闹钟）全部进 `onTick`，tick 带 `lastRunAt / runsToday`；filter（事件中心）答"值不值得叫醒我"，trigger（checker，L2 起才有）答"现在需要动作吗"，**无 trigger 的 job tick 即 run**。**fire（D1）是 trigger 返回值里的一条定义**：= 需要执行一次 payload 而不是条件为真；trigger 检测跃迁并在 `message` 里写**跃迁名**（`stage_1 / stage_2`、`entered_sofa / still_on_sofa_5m / left_sofa`），跃迁 → 动作表写在 payload（script 里是一段 `switch`）——判定侧不出现动作工具名。配额不在路上。
3. **最小字段集（P7）**：`schedule`（简写或 `sources[]`，事件源可带 `window / cooldown`，时间源用 cron 表达式或 `startAt–endAt` 表达窗口）；`trigger {kind: script|agent, script, prompt, postScript, state, stateSchema, toolsAllow}`（agent 时 `script` 是零 token 前置门、其 message 进判定信封，`postScript` 收 `trigger_result` 算计时 / 计数并给出最终 fire / state）；`quota {maxRunsTotal, maxRunsPerDay, maxChecksPerDay}`（系统默认，明说才覆盖）；`payload {kind: script(默认)|agentTurn|systemEvent, script | message, toolsAllow, publishes}`；`sessionTarget`；`delivery`。契约 `trigger(tick, state) → {fire, message, state, nextCheckAt?, done?}`，script 与 agent 相同；`done` → 本次 run 后 disable + 退订。
4. **判定默认是脚本，模型是可选项（G2 / P10）**：有结构化数据源（行情 / 比分 / 余票 / 预报 API、`phone.lookup(state)`）默认 `trigger.script`，零 token；只有图像 / 非结构化页面必须 `trigger.agent`（S7）；有 API 但条件含语义判断时 agent 是可选项（S6 / S8 / S9），默认仍是 script，用户要更强的语义判断时切换。选 agent 必配三道护栏：前置 script 门、配额 `maxChecksPerDay`（系统默认 200，S7 覆盖 400；超出暂停并告警，回读时告知"每天最多看 N 次"）、stateSchema + postScript（计时、计数、去重不交给模型）。判定和动作分开的理由：fire:false 的代价、判定期权限、跨 tick 记忆、checks 与 runs 分开计数；"判定动作一体"只用于离线验证判定 prompt。
5. **三种"时间"的分工**：绝对时间点 → `sources[]` 里的时间源（"8 点前一直没收到快递通知" = event + cron 两源）；相对某次事件的时间点 → `nextCheckAt`（离开后 1 小时、领先后 30 分钟）；只在某时段叫我 → `sources[].window` 或 cron 表达式本身（D6：窗外该源不产生 tick，self 闹钟不受窗口约束）。
6. **时间戳规则**：事件与事件之间的间隔用 `tick.event.occurred_at`（投递可能延迟、重试、乱序）；deadline / nextCheckAt 的到点用 `tick.now`（cron service 自己的钟）。不假设投递顺序；同一 job 的 onTick 串行处理（V7）。
7. **脚本运行时边界（D2）两档**：同一 cron service 进程内沙箱，30s / 5 次调用 / state ≤16KB。**trigger script** 能读 `tick` / `trigger.state`，只能 `tools.call` toolsAllow 内的只读工具，**失败 = fire:false + check error，state 保留旧值**；**payload script** 可调 `payload.toolsAllow` 内的写工具与 `event_publish`，不能 cron / ask_user，遇必确认动作 fail-closed（run error + failureAlert）——这类动作编译期就该选 agentTurn。
8. **限额不是一层，拆三处**：叫醒源的有效范围（"只在晚上 / 别一直提醒"）归 `sources[].window / cooldown`；依赖 run 事实的节流（"刚做过别再做"，S8 2m、S11 30m）归 trigger，脚本查 `tick.lastRunAt`，由判定者自己决定，跃迁不会被"跳过"丢失；**配额**（`maxRunsTotal / maxRunsPerDay / maxChecksPerDay`）是 cron service 挂在 job 上的计数器，系统默认 runs/day 50 · checks/day 200，用户明说才覆盖，到顶暂停 + 告警，不经判定者——是脚本 bug / 模型幻觉时的安全网。`nextCheckAt` **只加一个 self tick、不减任何 tick**，新值覆盖、`null` 作废。S9 用 script 时 155 个 tick 零 token，22:40 self tick fire 一次并 `done`。
9. **组合条件一种写法（P12）**：与 / 或 / 之后 / 没有 / 到点还没全是 `sources[]` + 一段 `trigger.script`——"或"= sources 两个无 trigger；"事件且状态"= 脚本查 `phone.lookup(state)`；"A 之后 W 内 B"= state 记 `a_at`（occurred_at）；"A 之后 W 内没有 B"= state 记 `deadline` + `nextCheckAt`。不给模板编号，不加原语，事件中心不做 CEP。
10. **事件源（P8）**：模型只写 `eventType + filter`；cron service 处理 add 时按 sources 里的 event 项逐条 `EventHub.subscribe(filter + 目录默认 debounce / staleAfter, tag=job_id)`，订阅是 job 的副作用（add / update 差集 / enabled / remove / 启动对账）；时间项由原生调度器按 index 产生 tick，不经事件中心。入口四步：鉴权找 job → event_id 去重 24h → occurred_at 过期 → 先回 200 再 `onTick`。三句承诺：事件不丢、动作不重复、过期不执行。
11. **派生事件只差 payload 一个字段（P13）**：默认是普通 job；结果要复用时 payload 改 `script → event_publish(type, payload)` 并带 `publishes {type, desc, fields}` 登记目录，消费者是普通 event job。编译规则：单用途只关我 → 普通 job；公共事实或两个以上用途 → 派生事件；拿不准 → 普通 job。
12. **编译（P14）**：主 loop 六步——路由 → 选叫醒源与判定者（成本阶梯）→ `phone.lookup` 填槽 → 写判定与限额 → message 三段 + 显式 sessionTarget / toolsAllow / delivery → 回读一句 → `cron add`。S5 的车次 / 席别 / 代付在这一步问清，S5 是一条 `at` job。
13. **执行（P15）**：**payload script 默认**（不起 session，在沙箱直接拿 tick / trigger.message / state 调工具，零 token）；agentTurn 走 isolated；五种上下文的工具面（主 loop / trigger script / 判定 agent / payload script / 动作 agentTurn）；agentTurn 的五块信封 = 触发头 + 触发事实（标 external-data）+ 冻结的 message 三段 + contextMessages + `last_run_summary`，不读主对话。**跨 session ask_user（D4）**：run 进 waiting → 问题经 delivery 渠道送达 → 答复回 run；可能 ask_user 的 job 强制 announce；超时 → error + failureAlert。
14. **预授权分期（D3 / G6）**：一期支付 / 卖出 / 对外发送一律 ask_user；二期在 toolsAllow 加参数级约束后，创建期确认过的范围免确认；支付永远 ask_user。
15. **十二场景全表（P16）**：S1 cron + agentTurn；S2 cron + script 查预报；S3 event geofence.enter（window 18–23 · cooldown 2h）+ **payload script**；S4 event phone.call_incoming；S5 一条 at；S6 cron 交易时段 + script 跃迁 fire（可选 agent），stage_2 → `done`；S7 every 30s + agent（前置 script 有运动 || self，postScript 算三个跃迁）+ **payload script switch**，配额 checks/day 400，动作零 token（附录 A10 完整 job）；S8 every 30s startAt + script 或 agent，trigger 查 lastRunAt ≥ 2m，支付成功后自删；S9 every 1m startAt–endAt + script 或 agent + nextCheckAt，fire + `done`；S10 event + script 查电量 + systemEvent；S11 event ×2 + state a_at + lastRunAt 节流 + systemEvent；S12 event ×2 + state deadline + nextCheckAt。收尾两种：trigger 知道结束 → `done`；结果决定去留 → payload 自删（只剩 S8）。
16. **分期**：一期把两种判定者、两种动作者都做出来——`sources[]`（含 window / cooldown）+ 事件适配器、tick（带 lastRunAt）+ nextCheckAt + done、配额计数器与默认值、payload script 档、目录进 prompt + `phone.lookup`、`event_publish`、`trigger.agent` 基础（prompt + trigger_result + 前置 script），覆盖 S1–S12；二期加护栏与放权——postScript + stateSchema 强校验、多模态直接进判定信封、参数级 toolsAllow 约束、预授权放开。
17. **动手前到源码核实（V1–V7）**：`trigger.script` 沙箱能力与失败默认语义；`stream` kind 的 tick 语义；自动化 run 里 `cron remove` 自己对 isolated 是否放开（只剩 S8 依赖）；run waiting 的 ask_user 送达与恢复；toolsAllow 是否支持参数级约束；`at` 自删能否复用为 `done` 的实现、payload script 沙箱能否拿到写工具；`onTick` 对同一 job 是否已串行。
18. **文档组织**：一份 28 页幻灯片——P2 一页看懂给汇报用，前 18 页主稿讲逻辑与每个场景，后 10 页附录放规格细节、模板、模型视角与一份完整 job 示例；九张 archify 图（架构 / 流程 / 状态机 / 数据流 / 时序）可逐章高亮与自动播放，源在 `archify/`；`02-event-catalog.md` 是目录全文。版面规则：单页 16:9、正文 clamp(11px, 1.12vw, 15px)，配色沿用蓝 / 紫 / 绿 / 橙 / 红五色，archify 语义类映射到这五色；无头浏览器三宽度逐页校验，既查页面溢出也查面板内溢出。

## v3.2 相对 v3.1

- **一条路收成 `tick → [trigger] → run`**：trigger 是 L2 起才有的可选旁路，L0 / L1 的 job 到点 / 事件到了直接跑；**fire 从节点降为 trigger 返回值里的一条定义**；"三道门"说法去掉。
- **limits 拆三处**：`activeWindow / cooldown` → `sources[]` 属性（时间源直接写进 cron 表达式或 `startAt–endAt`；事件源 `window` / `cooldown` 覆盖目录 debounce）；依赖 run 事实的节流 → trigger，tick 新增 `lastRunAt / runsToday`；`maxRunsTotal / maxRunsPerDay / maxChecksPerDay` → cron service 的**系统配额**（默认值 + 可覆盖，到顶暂停告警）。D6 改为"窗口是叫醒源属性，self 闹钟不受窗口约束"。
- **trigger 契约加 `done`**：S6 stage_2、S9 用它收尾；payload 自删只留 S8（结果决定去留）；V3 的依赖面缩小。
- **payload 成本阶梯**：`payload.kind: script` 成为默认（动作编译期已确定的固定工具调用，零 token），agentTurn 只用于要生成 / 多步交互 / 必确认；S3 / S7 / S10 / S11 全程零 token，S7 的跃迁 → 动作表从 message 策略段改为 script `switch`。D2 分两档（trigger script 只读；payload script 可写但不能 cron / ask_user，必确认动作 fail-closed）。
- **九张 archify 图**（P4 / P6 / P10 / P11 / P13 / P17 / A5 / A9 / A10）替换 CSS 箭头与两张手写时序 SVG；分章高亮、trace、自动播放；配色映射到本稿原色板。
- 材料中不保留版本变更叙述（本节除外）。

## 开放问题

- **openClaw 源码事实 V1–V7**（见主稿 P18）：都是"核实后照写"的事实，不是设计分歧；V1 若原生脚本失败语义不可配，D2 需要在 checker 外包一层。
- **判定模型选型与配额默认值**（哪个小模型、checks/day 默认 200 与 runs/day 默认 50 是否合适、S7 多模态成本）。
- **模型 I/O 细节三项**（附录 A6–A8）：`last_run_summary` 由谁产出（倾向动作模型最终文本首行，NO_REPLY 时 cron service 用工具调用列表拼一行）；多模态输入如何进判定信封（一期由前置 script 预取塞进 tick 块，二期直接进信封）；`NO_REPLY` 与 `announce` 并存（倾向抑制渠道发送、主 session 摘要仍发）。
- 事件中心与 Gateway 的部署关系与推送能力——决定 D5 默认 webhook 还是本机直调。
- 派生事件条目的生命周期：生产者 job remove 后条目标 `orphaned` 保留还是级联通知消费者（倾向保留 + 对账时提示）。
- 同 job 有 run 在 waiting 时新 fire 合并而非排队——实现期在 cron service 内做。
- payload script 的 `announce(text)` 是否作为沙箱内建（S7 still_on_sofa_5m、S10 / S11 提醒）还是一律走 systemEvent——实现期定。
- S5 抢票统一走模型后的时效（搁置）。
