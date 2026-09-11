# openClaw 自动化任务：定时 + 事件订阅 + 脚本 / 模型判定触发统一方案

从"每天早上 9 点帮我干 xxx"出发，把 openClaw 的定时任务能力扩展到事件驱动的自动化
（明天下雨 / 到家 / 收到某人电话 / 火车放票抢票），再扩展到条件触发（股票分档抛售 / 狗上沙发驱赶 / 开售后买卧铺没买到继续盯 / 曼联持续领先 30 分钟通知张三）
与**跨事件 / 跨状态的组合条件**（到家且电量低 / 到家后 10 分钟内来电 / 离开公司 1 小时还没到家）。
架构以 openClaw 原生 `cron` 为基础、按需新增。前提假设：存在一个统一的**事件中心（EventHub）**，订阅即推送，单事件 filter 在事件中心侧评估，有 publish 接口；
**事件中心不做 CEP**，判定（trigger state）、限额（`limits`）、自设闹钟（`nextCheckAt`）全在 cron service。订阅由 openClaw Gateway 内部完成，模型不调订阅工具、不感知 debounce / staleAfter。

> 命名约定：中文统一叫"事件中心"，代码 / 字段 / 端点用 `EventHub`（如 `EventHub.subscribe`、`/hooks/eventhub`）。
> 模型可见的新工具只有三个：`phone.lookup(kind, q)`（只读；kind ∈ contacts / apps / bluetooth / places / state）、`event_publish`（仅 payload script）、`trigger_result`（仅判定 agent）。
> 大小写：job JSON 字段 camelCase（`staleAfter / nextCheckAt / maxRunsTotal`），事件目录 yaml 与事件 payload snake_case（`stale_after / must_filter / contact_id`）；点火入口叫 `onTick`。
> 九个核心名词（tick / trigger / fire / limits / run / filter / nextCheckAt / state / 派生事件）的定义见主稿 P5。

## 目录

| 文件 | 内容 |
| --- | --- |
| [openClaw自动化任务方案.slides.v3.1.html](./openClaw自动化任务方案.slides.v3.1.html) | **主稿幻灯片（当前版本 v3.1，17 页，HTML 16:9）**。五项新增（`sources[]` 多源调度 + 事件适配器 / tick + nextCheckAt / limits / trigger.agent / 编译期支撑）、三个新工具、字段集一页写完（P6）；**判定者 `script` 与 `agent` 是同一契约下的两个正式选项**：有结构化数据源默认脚本（零 token），看图 / 读页面 / 语义判断选模型，十二个场景里只有 S7 必须选模型，S6 / S8 / S9 两者皆可；**P9 专页讲 agent 判定的完整形态**（前置 script 门 → 只读判定模型 → 可选 postScript 收口计时 / 计数；为什么判定和动作分在两个 agentTurn；何时选 agent）；**六项拍板**（D1 fire = "需要执行一次 payload"、D2 脚本运行时边界与"失败 = fire:false"、D3 预授权分期、D4 跨 session ask_user 强制 announce、D5 事件入口默认 webhook + `stream` 零改动验证、D6 activeWindow 窗外仍维护 state）。四章：① 总体（十二场景 / 架构 / 原生复用 vs 五项新增）→ ② 核心模型（一条路与名词 / 最小字段集 / 事件源 / trigger / agent 判定 / limits 与 nextCheckAt / 组合条件一种写法 / 派生事件只差 payload）→ ③ 编译与执行 → ④ 验证与拍板（十二场景全表 / S3 时序 / 拍板 · 可靠性 · 分期 · 待核实 V1–V7）。17 页经无头浏览器 1100 / 1334 / 1700 三宽度逐页校验无溢出、无面板内溢出 |
| [openClaw自动化任务方案.附录.slides.v3.1.html](./openClaw自动化任务方案.附录.slides.v3.1.html) | **附录幻灯片（v3.1，10 页）**：实现者才需要的细节——A2 事件目录 schema 与 10 组 63 条总览、A3 filter 语法 EBNF / 校验四条 / 写不了的归哪、A4 三套编译模板（message 三段含跃迁 → 动作表 / 判定 prompt 三段 / 组合脚本三例，事件间隔用 `occurred_at`）、A5 时序 ②（S2 派生事件两条 job 接力）、A6 三个模型出场位置与三条管线、A7 判定期单 tick 信封（S9 选 agent 判定时）、A8 动作期信封（S9 与 S3 对照）、A9 事件入口传输四选一与 `stream` 零改动验证路径、A10 S7 完整 job（agent 判定 + postScript + 跃迁映射 + 一次上沙发的 tick 时间线）。10 页同样三宽度校验无溢出 |
| [02-event-catalog.md](./02-event-catalog.md) | **事件目录规范与内建条目全文**（配套主稿 P7 / P11 与附录 A2 / A3 / A4）：设计约束（模型只看可见字段、目录含派生条目静态进 prompt、filter 单事件布尔、事件中心不做 CEP、`occurred_at` 在信封不在 payload）→ 条目 schema（`type / group / desc / fields(!key) / must_filter / pair / state_query` + internal `rate / debounce / stale_after / sensitivity`）与 cron add 校验规则 → 派生事件条目登记 → filter 语法 BNF 与示例 → 命名与字段规范 → **唯一只读查询工具 `phone.lookup`** → **10 组 63 条内建条目逐条表**（device 10 / setting 17 / connectivity 13 / geofence 2 / activity 1 / phone 6 / alarm 3 / app 5 / calendar 3 / notification 3，含 internal 默认值）→ 相对原稿的改动清单 |
| [history/](./history/) | 历史版本留档（v0.1 → v3.0 主稿及 v3.0 附录）。每一版被下一版取代的原因写在各自文件的封面；v3.0 → v3.1 的差别见下文"v3.1 相对 v3.0" |

## 核心结论

1. **一个任务工具 + 三个只读小工具**：模型只面对 openClaw 原生 `cron` 工具；`schedule` 有单一时间源的简写（`kind: at / every / cron`）和通用形式 `sources[]`（每项 `kind ∈ at / every / cron / event`，1..n，时间与事件可混排）；事件目录（内建 63 条 + 已登记派生条目）静态在编译期 system prompt 里，没有目录查询工具；新工具只有 `phone.lookup`、`event_publish`、`trigger_result`。job 表就是任务表。
2. **一条路，三道门**：`tick → trigger → fire → limits → run`。tick 三种来源（时间到点 / 订阅事件到达 / `nextCheckAt` self 闹钟）全部进 `onTick`；filter（事件中心）答"这件事值不值得叫醒我"，trigger（checker）答"现在需要动作吗"，limits（cron service）答"此刻该不该跑"。**fire（D1）= trigger 认为需要执行一次 payload**，trigger 检测跃迁并在 `message` 里写**跃迁名**（`stage_1 / stage_2`、`entered_sofa / still_on_sofa_5m / left_sofa`），跃迁 → 动作的映射写在 `payload.message` 策略段——判定侧不出现动作工具名。
3. **最小字段集（P6）**：`schedule`（简写或 `sources[]`）；`trigger {kind: script|agent, script, prompt, postScript, state, stateSchema, toolsAllow}`（agent 时 `script` 是零 token 前置门、其 message 进判定信封，`postScript` 收 `trigger_result` 算计时 / 计数并给出最终 fire / state）；`limits {activeWindow, cooldown, maxRunsPerDay, maxRunsTotal, maxChecksPerDay}`（全部可选，用户明说才写）；`payload {kind, message, toolsAllow, publishes}`；`sessionTarget`（默认 isolated）；`delivery`。契约 `trigger(tick, state) → {fire, message, state, nextCheckAt?}`，script 与 agent 相同。
4. **判定默认是脚本，模型是可选项（G2 / P9）**：有结构化数据源（行情 / 比分 / 余票 / 预报 API、`phone.lookup(state)`）默认 `trigger.script`，零 token；只有图像 / 非结构化页面必须 `trigger.agent`（S7）；有 API 但条件含语义判断时 agent 是可选项（S6 / S8 / S9），默认仍是 script，用户要更强的语义判断时切换。选 agent 必配三道护栏：前置 script 门、`maxChecksPerDay`（超出暂停并告警，回读时告知"每天最多看 N 次"）、stateSchema + postScript（计时、计数、去重不交给模型）。判定和动作分在两个 agentTurn 的理由：fire:false 的代价、判定期权限、跨 tick 记忆、limits 只数真正的动作；"判定动作一体"只用于离线验证判定 prompt。
5. **三种"时间"的分工**：绝对时间点 → `sources[]` 里的时间源（"8 点前一直没收到快递通知" = event + cron 两源）；相对某次事件的时间点 → `nextCheckAt`（离开后 1 小时、领先后 30 分钟）；只在某时段允许跑 → `limits.activeWindow`。
6. **时间戳规则**：事件与事件之间的间隔用 `tick.event.occurred_at`（投递可能延迟、重试、乱序）；deadline / nextCheckAt 的到点用 `tick.now`（cron service 自己的钟）。不假设投递顺序；同一 job 的 onTick 串行处理（V7）。
7. **脚本运行时边界（D2）**：cron service 进程内沙箱；能读 `tick` / `trigger.state`；只能 `tools.call` toolsAllow 内的只读工具；不能 cron / event_publish / 写工具；30s / 5 次调用 / state ≤16KB；**失败 = fire:false + check error，state 保留旧值**（不采用"失败算 fire"，避免误动作）。
8. **limits 与 nextCheckAt**：limits 在 fire 与 run 之间，job 级、四种叫醒源共用；一次性用 `maxRunsTotal: 1`；activeWindow 窗外事件 / self tick 仍进 trigger 维护 state（D6）。`nextCheckAt` **只加一个 self tick、不减任何 tick**，新值覆盖、`null` 作废。S9 用 script 时 155 个 tick 零 token，22:40 self tick fire 一次；用 agent 时前置 script 只在比分变化或 self tick 放行，一场球 5–6 次判定。
9. **组合条件一种写法（P11）**：与 / 或 / 之后 / 没有 / 到点还没全是 `sources[]` + 一段 `trigger.script`——"或"= sources 两个无 trigger；"事件且状态"= 脚本查 `phone.lookup(state)`；"A 之后 W 内 B"= state 记 `a_at`（occurred_at）；"A 之后 W 内没有 B"= state 记 `deadline` + `nextCheckAt`。不给模板编号，不加原语，事件中心不做 CEP。
10. **事件源（P7）**：模型只写 `eventType + filter`；cron service 处理 add 时按 sources 里的 event 项逐条 `EventHub.subscribe(filter + 目录默认 debounce / staleAfter, tag=job_id)`，订阅是 job 的副作用（add / update 差集 / enabled / remove / 启动对账）；时间项由原生调度器按 index 产生 tick，不经事件中心。入口四步：鉴权找 job → event_id 去重 24h → occurred_at 过期 → 先回 200 再 `onTick`。三句承诺：事件不丢、动作不重复、过期不执行。
11. **派生事件只差 payload 一个字段（P12）**：默认是普通 job；结果要复用时 payload 改 `script → event_publish(type, payload)` 并带 `publishes {type, desc, fields}` 登记目录，消费者是普通 event job。编译规则：单用途只关我 → 普通 job；公共事实或两个以上用途 → 派生事件；拿不准 → 普通 job。
12. **编译（P13）**：主 loop 六步——路由 → 选叫醒源与判定者（成本阶梯）→ `phone.lookup` 填槽 → 写判定与限额 → message 三段 + 显式 sessionTarget / toolsAllow / delivery → 回读一句 → `cron add`。S5 的车次 / 席别 / 代付在这一步问清，S5 是一条 `at` job。
13. **执行（P14）**：isolated 默认；四种上下文的工具面（主 loop / trigger script / 判定 agent / 动作 agentTurn）；五块信封 = 触发头 + 触发事实（标 external-data）+ 冻结的 message 三段 + contextMessages + `last_run_summary`，不读主对话。**跨 session ask_user（D4）**：run 进 waiting → 问题经 delivery 渠道送达 → 答复回 run；可能 ask_user 的 job 强制 announce；超时 → error + failureAlert。
14. **预授权分期（D3 / G6）**：一期支付 / 卖出 / 对外发送一律 ask_user；二期在 toolsAllow 加参数级约束后，创建期确认过的范围免确认；支付永远 ask_user。
15. **十二场景全表（P15）**：S1 cron；S2 cron + script 查预报；S3 event geofence.enter + limits；S4 event phone.call_incoming；S5 一条 at；S6 every + script 跃迁 fire（可选 agent），stage=2 后 `cron remove` 自己；S7 every 30s + agent（前置 script 有运动 || self，postScript 算三个跃迁，附录 A10 有完整 job）；S8 every 30s + script 或 agent，cooldown 2m，成功自删；S9 every 1m + script 或 agent + nextCheckAt，maxRunsTotal 1；S10 event + script 查电量；S11 event ×2 + state a_at；S12 event ×2 + state deadline + nextCheckAt。
16. **分期**：一期把两种判定者都做出来——`sources[]` + 事件适配器、tick + nextCheckAt、limits、目录进 prompt + `phone.lookup`、`event_publish`、D2 脚本边界、`trigger.agent` 基础（prompt + trigger_result + 前置 script），覆盖 S1–S12；二期加护栏与放权——postScript + stateSchema 强校验、多模态直接进判定信封、参数级 toolsAllow 约束、预授权放开。
17. **动手前到源码核实（V1–V7）**：`trigger.script` 沙箱能力与失败默认语义；`stream` kind 的 tick 语义；自动化 run 里 `cron remove` 自己对 isolated 是否放开；run waiting 的 ask_user 送达与恢复；toolsAllow 是否支持参数级约束；`at` 自删能否配到 every / event；`onTick` 对同一 job 是否已串行。
18. **文档组织**：主稿 17 页讲逻辑与每个场景，附录 10 页放规格细节、模板、模型视角与一份完整 job 示例；`02-event-catalog.md` 是目录全文。版面规则：单页 16:9、正文 clamp(11px, 1.12vw, 15px)，无头浏览器三宽度逐页校验，既查页面溢出也查面板内溢出。

## v3.1 相对 v3.0

- `sources[]` 通用化：每项 `kind ∈ at / every / cron / event`，时间源可与事件源混排（v3.0 写的"时间源不再与事件源混排"撤回）；顶层 `schedule.kind` 保留为单一时间源简写。
- 修正 bug：S11 / S12 与 A4 组合脚本模板里事件间隔改用 `tick.event.occurred_at`，不再用 `tick.now`；新增时间戳规则与 V7（同 job onTick 串行）。
- `trigger.agent` 从"二期例外"改为**一期可选项**：新增 P9 专页（三段流水、A vs C 四行对比、何时选 agent、三道护栏）、可选 `postScript`、前置 script 的 message 进判定信封；S6 / S8 / S9 标为"可选 agent"。
- trigger `message` 统一写跃迁名，跃迁 → 动作表进 payload.message 策略段；判定 prompt 不含动作工具名。
- 编译回读增加"每天最多看 N 次"提示。
- 材料中不再保留版本变更叙述：附录 A10 由变更记录换成 S7 完整 job 示例，各页去掉与旧版的对照。

## 开放问题

- **openClaw 源码事实 V1–V7**（见主稿 P17）：都是"核实后照写"的事实，不是设计分歧；V1 若原生脚本失败语义不可配，D2 需要在 checker 外包一层。
- **判定模型选型与默认预算**（哪个小模型、`maxChecksPerDay` 默认 200 是否合适、S7 多模态成本）。
- **模型 I/O 细节三项**（附录 A6–A8）：`last_run_summary` 由谁产出（倾向动作模型最终文本首行，NO_REPLY 时 cron service 用工具调用列表拼一行）；多模态输入如何进判定信封（一期由前置 script 预取塞进 tick 块，二期直接进信封）；`NO_REPLY` 与 `announce` 并存（倾向抑制渠道发送、主 session 摘要仍发）。
- 事件中心与 Gateway 的部署关系与推送能力——决定 D5 默认 webhook 还是本机直调。
- 派生事件条目的生命周期：生产者 job remove 后条目标 `orphaned` 保留还是级联通知消费者（倾向保留 + 对账时提示）。
- 同 job 有 run 在 waiting 时新 fire 合并而非排队——实现期在 cron service 内做。
- 混排 job 的 activeWindow 语义（时间源 tick 窗外是否也进 trigger 维护 state）——按 D6 同样处理，待实现期确认没有反例。
- S5 抢票统一走模型后的时效（搁置）。
