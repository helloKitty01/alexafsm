# openClaw 自动化任务：首版收敛——模型选模式填参数 · 程序生成 · 官方能力为准

从"每天早上 9 点帮我干 xxx"出发，把 openClaw 的定时任务扩到事件驱动的自动化。**v4 是一次收敛而不是修正**：v3.x 把十二个场景（定时 / 事件 / 条件 / 组合）都纳入一套通用执行模型（`sources[]`、`onTick`、`trigger.agent`、`nextCheckAt`、`done`、`quota`…），v4 按三条原则把首版边界收到**定时、单事件、简单即时条件、本人提醒与少量固定动作**，并把运行时语义全部落回 openClaw 官方能力上：

1. **模型负担轻**：模型只在创建期出场一次——从 5 个固定模式里选一个、填参数、回读一句；脚本、state、权限、job 形态由程序生成。
2. **整体机制少**：工程新增只有两件——5 个模板 + 创建处理函数、EventHub → 官方 `stream` 的桥接命令。不新增调度体系、任务表、事件适配器、判定模型工具、结束 / 限额协议。
3. **与官方一致**：`at / every / cron / stream`、`trigger.script` 契约、`once`、script payload 的 `notify / state / nextCheck`、approval card / standing grant、runs / delivery / failureAlert 全部照用；实施前锁定版本，三栏区分官方已有 / 我们的适配 / 暂不支持。

首版五个场景：S1 晨报、S2 定时查天气满足条件提醒、S3 到家开灯、S4 指定联系人来电提醒、S10 到家查电量低则提醒。其余七个（S5 抢票、S6 分档卖出、S7 狗上沙发、S8 盯卧铺、S9 持续领先、S11 到家后来电、S12 离开没到家）进入**路线图**，用户提出时明确说明并给替代话术。

> 命名约定：中文统一叫"事件中心"，代码 / 端点用 `EventHub`；桥接命令叫 `eventhub-sub`。job JSON 字段沿用官方 camelCase；事件目录 yaml 与事件 payload snake_case。
> 官方文档核对日期 2026-09-20（`docs.openclaw.ai/automation/cron-jobs/{schedules,payloads}`）；尚未核实实际部署的 release / commit。

## 目录

| 文件 | 内容 |
| --- | --- |
| [openClaw自动化任务方案.slides.v4.html](./openClaw自动化任务方案.slides.v4.html) | **幻灯片（当前版本 v4，24 页 = 主稿 18 页 + 附录 6 页，单文件 HTML 16:9，滚动式）**。① 边界与职责：三条原则与首版五场景 / 暂缓七场景（P2）、**模型只选模式填参数回读、程序生成其余一切**的职责边界表与提案 JSON（P3）、职责边界图（P4）、**模式库 5 个**（定时生成内容 · 定时查询→条件→提醒 · 单事件→固定动作 · 单事件→通知本人 · 单事件→查现况→提醒，每个给模型填的参数、程序生成的官方 job 形态、模板里固定的逻辑，P5）；② 运行时以官方为准：一条路 `到点 → 条件门（可省略）→ payload → run → 交付` 与**官方名词表**（schedule 五 kind、trigger.script 契约与 30 s / 5 次预算、once、payload 四 kind、notify / state / nextCheck、streamBatch、approval / standing grant、tool policy，P6）、一条路图（P7）、**两种 job 形态**——条件门 + agentTurn 与单个 script payload，官方不允许同 job 混用（共用 trigger.state 槽）——及字段三栏（P8）、形态对照图（P9）、**限制四分**（source 整形 / 运行时动作冷却与窗口 / 用户业务限制 / 平台配额，三类对模型隐藏，到顶行为各异，P10）；③ 事件 · 审批 · 结束：**stream 桥接**链路、官方批处理行为、模板固定三步（解析 / 去重 / 过期）、首版不承诺项（P11）、S3 事件时序图（P12）、S2 形态 B 脚本状态机图（P13）、**审批与结束语义**——once 以首次成功执行为准、state 仅成功 run 后持久化、approval card / standing grant（P14）、run 生命周期图（P15）；④ 验证与拍板：五场景全表（P16）、**四条轨迹推演**（同批两事件 / 旧事件迟到 / 最后一次动作失败 / 等待确认时条件改变，P17）、八项拍板 D1–D8 + 版本锁定三栏 + 待核实 V1–V6（P18）。附录：路线图七场景逐条（缺的能力 / 评估什么 / 替代话术，A1）、S9 / S7 设想状态机图（A2 / A3）、三段固定模板代码（A4）、事件目录与 filter 语法（A5 / A6）。**八张图每张独占一页**，archify 渲染并保留钩子：进入视口跑一遍 trace，`→` / `←` 逐章高亮，`P` 自动播放，**悬停节点看上下游流光**（非相邻压暗、相邻亮起、相邻边跑光点，出边蓝 / 入边紫），点击钉住并在章节栏显示上游 N · 下游 M，Esc 取消；配色沿用蓝 / 紫 / 绿 / 橙 / 红五色。24 页经无头浏览器 1100 / 1334 / 1700 三宽度逐页校验无溢出 |
| [archify/](./archify/) | v4 八张图的 Typed JSON 源与 deliver 出的独立 HTML（`v4-P4-职责边界.dataflow`、`v4-P7-一条路.workflow`、`v4-P9-两种形态.architecture`、`v4-P12-S3事件桥接.sequence`、`v4-P13-S2形态B脚本.lifecycle`、`v4-P15-run生命周期.lifecycle`、`v4-A3-设想S9.lifecycle`、`v4-A4-设想S7.lifecycle`）。改图先改 JSON，`validate <type> <json> --quality showcase --json` 9/9 后 `deliver`，再 `python3 ../../slide-style/inline_archify.py <json> <html> --suffix xx` 抽 SVG + 章节内联 |
| [02-event-catalog.md](./02-event-catalog.md) | 事件目录规范与内建条目全文（10 组 63 条）。v4 里它是**候选接入清单**：首版只用 `geofence.enter` / `phone.call_incoming` 两条；条目决定桥接命令能订什么、模板能生成什么 filter；不整体注入 prompt，只列已接入模板对应的条目 |
| [history/](./history/) | 历史版本留档（v0.1 → v3.2 主稿、v3.0 / v3.1 附录、`archify-v3.2/` 为 v3.2 九张图的源）。v3.2 → v4 的差别见下文"v4 相对 v3.2" |

## 核心结论

1. **模型只做三件事**：选模式（5 选 1 或"不支持"）、填参数（时间 / 对象 ID / 阈值 / 文案，对象 ID 来自 `phone.lookup` 解析）、回读一句。模型产物是应用内部的提案 JSON `{template, args, readback}`，不是 `cron add` 参数；创建处理函数校验（模式命中 · 参数合法 · 对象唯一 · 工具已接入 · 有权限）后把参数注入固定模板生成真正的 job。模型只有三种创建结果：可以创建 / 需要澄清 / 暂不支持（说明原因 + 替代，用户接受才建）。
2. **模式库 5 个，模板 = 固定 JS / prompt 骨架 + 参数注入**，工程维护、有版本；不建模板语言与通用编译器。实际是 2 个前缀（stream 三步 / cron）+ 3 个后缀（查判提醒 / 幂等动作 / 生成内容）的组合。对应工具或本人交付渠道未接入时该模式不出现在列表里。
3. **两种官方 job 形态**：形态 A 条件门 + agentTurn / systemEvent（要生成内容或需审批；`trigger.script` 只读判定并持有 state 槽），形态 B 单个 script payload（查 + 判 + 动在同一段固定脚本，state 槽归它，条件不满足 `return {}`，**每次检查都记一次 run**——接受）。**官方不允许 condition trigger 与 script payload 同 job**，这是 v4 把判断并进 payload 的直接原因。首版 S1 用 A（无门），S2 / S3 / S4 / S10 用 B，全程零 token。
4. **一条路是官方的**：到点 / 批到达 → 条件门（可省略的一步，不是旁路）→ payload → run → notify / announce；`fire` 是 `trigger.script` 返回值里的布尔，不是节点；限制、审批、预算收在 run 内部。没有自定义的 onTick / sources / done / quota / lastRunAt。
5. **限制分四类，三类对模型隐藏**：① source 整形（事件中心 debounce、桥接按实例订阅、重连只收新事件）；② 动作冷却与执行窗口——job 级，在模板脚本内判断（`state.lastActionAt` 动作成功后写；**事件仍收，只是不动作**，不在 source 层过滤）；③ 用户业务限制（"每天一次"= state 记日期，次日恢复；一次性用官方 `once`，完成安静结束）；④ 平台配额（官方 timeout / tool budget / 30 s 最小间隔，到顶退避告警）。debounce ≠ cooldown；source 级冷却挡不住多源；三类阈值到顶行为不同，不能合并。
6. **事件接入 = 官方 `stream` + 工程维护的 `eventhub-sub`**：模型只填事件类型与 filter 参数；桥接命令订阅、逐行 JSON 到 stdout、按实例管理租约、先落盘再 ack（D7）、重连只收新事件不补历史。照抄 stream 行为：250 ms 静默关批、payload 运行期间后到的行并入下一批、内建 30 s 间隔、**失败不重试**、五次短命退出进 error。模板固定三步：逐行解析（截断丢弃）→ `event_id` 去重（state.seen 24 h，成功后写）→ `occurred_at` 过期丢弃。**首版不承诺**逐条处理、毫秒级、恰好一次、离线补执行；因此抢票、比分等高频时效场景进路线图。
7. **审批与结束全是官方语义**：agentTurn 的高危 exec → approval card → run waiting；"Always allow" 铸 standing grant（= 旧稿 D3 的二期免确认，不自建参数级约束）；script payload unattended、不能 ask_user，因此只做创建期已授权的固定动作（开灯、本人提醒）。`once: true` 在**首次成功执行**后停用（失败 / 拒绝不停用、state 不持久化、下次可再 fire）——"判定到了"与"做成了"由 run 结果分开，替代旧稿的 done。state 仅成功 run 后持久化是官方既有行为：去重键、日期、lastActionAt 都在动作成功后写，失败自然回滚。
8. **四条轨迹推演（P17）**：同批两事件（幂等 set + seen 一次写回）、旧事件迟到（过期丢弃；source 不丢事实所以以后能做"旧事件取消新计时"）、最后一次动作失败（state 不持久化 → 不会"记了 seen 却没开灯"；run 与 delivery 分开可查）、等待确认时条件改变（allow 后由动作 agentTurn 重读现况）——都在"官方状态模型 + 模板三步 + 幂等目标状态"下有确定行为，不需要自定义事务 / 补偿 / 恢复协议。
9. **八项拍板 D1–D8**：D1 fire = 返回值；D2 脚本边界按官方数字、模板显式最小 toolsAllow；D3 固定动作 = 创建期授权、需确认走 agentTurn + approval、Always allow = 二期；D4 官方 waiting；D5 stream 桥接；D6 source 不丢事实、窗口与冷却在脚本内；D7 落盘后再 ack；D8 幂等键 event_id + job_id 入 state、动作用目标状态非 toggle。
10. **版本锁定三栏**：官方已有（schedule 五 kind · trigger.script / once · payload 四 kind · notify / state / nextCheck · pacing · approval / standing grant · runs / delivery · tool policy）/ 我们的适配（5 模板 + 创建处理函数 · eventhub-sub · phone.lookup · 模板三步 · 目录进 prompt）/ 暂不支持（sources[] · onTick · trigger.agent / postScript · nextCheckAt · done · quota · 派生事件 · 跨事件 state · 对外发送 / 支付 / 交易）。
11. **待核实 V1–V6**：锁定版本的字段名与 notify 投递；stream `mode: match` 只接 JSON 行、子进程收尾、重启后源身份；script payload 能否调插件工具、toolsAllow 是否生效；事件中心租约与 filter 在哪侧评估（S4 contact_id 过滤取决于此）；地点 / 联系人 / 设备 / 天气 / 电量工具可用且创建轮次可见；agent 建 job 的 `--tools` 默认值。
12. **顺序**：锁版本 + V1–V6 → 模式①②（S1 / S2，纯 cron）→ 桥接 + 模式③（S3）→ ④⑤（S4 / S10）→ 路线图逐项评估，不预先承诺。
13. **路线图进入条件**：有明确重要需求 · 对应官方能力在锁定版本存在或适配可控 · 能补一条轨迹推演 · 有验收用例。缺一不进。旧稿对 S5–S12 的分析（判定契约、state 状态机、nextCheck、派生事件）保留为评估材料，A2 / A3 的设想状态机图即来自 v3.2。
14. **文档组织**：一份 24 页幻灯片，八张 archify 图每张独占一页（悬停 Intent Trace、钉住、分章、trace、播放）；`02-event-catalog.md` 是候选接入清单。版面规则：单页 16:9、正文 clamp(11px, 1.12vw, 15px)，配色沿用五色，archify 语义类映射到这五色；三宽度逐页校验。

## v4 相对 v3.2

- **是收敛不是修正**：v3.2 的分析仍然成立，但首版只做其中五个场景；七个复杂场景转路线图，每条写清缺的能力、评估什么、替代话术。
- **模型职责从"写 job"改为"选模式填参数"**：脚本、filter、state、toolsAllow、once、冷却全部由模板与创建处理函数生成；这是对 Codex 评审"没有真正减少模型创建期职责"的回应。
- **运行时语义落回官方**：`trigger.script` 与 `payload.script` 不能同 job（v3.2 大量使用该组合，改为形态 A / B 二选一）；`once` 替代 `done`；`nextCheck` + `pacing` 替代 `nextCheckAt`；state 仅成功后持久化替代自造的"状态与结果分离"；approval card / standing grant 替代自建的 D3 / D4。
- **撤回 v3.2 的 limits 三拆**：debounce ≠ cooldown、source 级冷却挡不住多源、source 层过滤窗口会破坏状态正确性——改为四分（整形 / 运行时冷却窗口 / 业务限制 / 平台配额），三类对模型隐藏；删掉 `sources[].window / cooldown`、`lastRunAt / runsToday`、`quota` 字段。
- **事件接入改为 stream 桥接**：不做 webhook 入口、onTick、事件适配器、`sources[]` 多源；接受批处理与合并，新增 D7 落盘后再 ack、D8 动作幂等。
- **图**：从九张半栏图改为八张整页图；补 Intent Trace 悬停层与钉住；`fire` 降为返回值、固定动作优先 script 两点保留。

## 开放问题

- **S4 的"指定联系人"过滤放哪**：事件中心侧按 `contact_id` 评估（首选，需其支持），还是桥接侧过滤（所有来电都推到 Gateway）——待事件中心确认，决定桥接命令的最小功能面。
- **锁定哪个 release / commit**：文档核对日期 2026-09-20；实施前必须核实实际部署版本的 `cron add` 字段名、script payload 的 `notify` 投递与插件工具可调性（V1–V3）。
- **stream 只接 stdout JSON 行**：`mode: match` + `^\{` 是否足够，还是桥接命令要把日志完全静默（V2）。
- **`nextCheck` 的精度**：路线图 S9 / S12 依赖它做"到点"，官方语义是从成功完成起算并受 pacing 夹，能否接受 ±pacing 的误差。
- **模板版本升级时已建 job 怎么办**：官方保护"运行中修改脚本不被旧返回覆盖"，但批量升级模板脚本的流程需要定义。
- **本人提醒的重复**：重连 / 合批可能让 S4 重复提醒，首版接受；若用户不接受，需要在模板里加 `lastActionAt` 冷却（机制已有，是否默认开）。
