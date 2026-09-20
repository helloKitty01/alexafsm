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
| [docs/kv-cache-discussion/](./docs/kv-cache-discussion/) | KV cache 命中率与 agent 上下文工程（分层排布、渐进式加载、压缩策略）的设计讨论；含**最终汇报版承载 `kv cache方案（汇报版·升级版）.v2`（12 页 + 附录 4 页；内容与数据同 v1.4：P1 数据基线 M1–M11 / K / R 为全稿单一事实来源并数据绑定；v2 把 archify 的画图与动态能力接进 deck——新增 P2 全景架构（architecture：四路来源 → 应用 → 引擎 ↔ 缓存 → 工具，两个边界）、P5 四步改造路线（workflow v2：三级泳道 + 例外道，主线 = 四步）、P11 统计管线（dataflow 五阶段），附录 B / C 时序图加 trace + 分章；五张图 showcase 9/9 校验后由 `inline_archify.py` 保钩子内联，进页 trace、→ / ← 逐章高亮、P 自动播放、深链 `#p=N&c=K`；旧 P2–P9 顺延；三视口无溢出校验 16 页通过；升级版 v1 及更早留档 history/，Typed JSON 源与可探索原 HTML 在 archify/）**、v2 汇报大纲（13）、实测数据需求（14）、上下文模块与长度基线（15）、逐调用实测 `token_breakdown.csv`、prompt 各段内容变化对照，以及 v2 单页幻灯片 P1 组成对比 v1.2 / P2 尺子与三方案 / P7 自动化统计；上一版整合材料 kvcache整体方案.v1 暂留对照 |
| [docs/slide-style/](./docs/slide-style/) | 幻灯片风格规范：对 [archify](https://github.com/tt-a1i/archify) skill 的借鉴分析（重心是**画图能力**——五种图型作者给什么 / 渲染器管什么 / 写图硬约束，与**动态能力**——trace 顺序即动画、views 分章讲述、探索层、URL / hash 外部驱动；接进 deck 的路 C 做法与 v2 逐图落地表、命令清单与校验失败修法；风格 token 只作附带）、十二条新幻灯片约定（图 / 动态 / 风格与交付），`inline_archify.py`（抽 archify SVG 并保留分章 / trace 钩子）与三视口逐页逐卡溢出校验脚本 `check_slides.py` |
| [docs/reminder-discussion/](./docs/reminder-discussion/) | reminder 机制（内部代号 notion 方案）的业界洞察：Claude Code system-reminder、Manus recitation、Anthropic 官方模式 |
| [docs/agent-variable-scheme/](./docs/agent-variable-scheme/) | Agent 变量句柄方案（当前版本 v4 文档 + v6 幻灯片，v1–v5 留档于 history/） |
| [docs/variable-resolution/](./docs/variable-resolution/) | 工具参数变量解析机制方案（含单页幻灯片：深色原版、浅色版及同款 PPTX） |
| [docs/skill-env-variables/](./docs/skill-env-variables/) | Skill 分支环境变量传入方案（前台应用为例，通道选择与决策矩阵，含业界实现调研） |
| [docs/thinking-tool-calls/](./docs/thinking-tool-calls/) | 思考模式（Thought）与 Function Call 的时序机制（先想后调、三层"出不出 thought"原因） |
| [docs/skill-tool-rom-versioning/](./docs/skill-tool-rom-versioning/) | Skill 与工具的 ROM 配套管理（双速发布、版本感知、工具治理、单 skill 可行性、重组情形、工具集对象与 A/B 管理路线，含单页 / 8 页详解 / v2 ~ v2.7 系列幻灯片，v2.7 为最新汇报版，含上架场景决策树与 A~F 穷举） |
| [docs/phone-assistant-automation/](./docs/phone-assistant-automation/) | 手机智慧助手需求与方案（统一任务模型：定时/事件/自定义监视/长时异步任务，双脑架构 + 打扰管理器；含多任务管理 Agent v1.3 幻灯片：双入口 × 三层模型 × UAT 接口 × 异构执行体，v1.0–v1.2 留档 history/） |
| [docs/openclaw-automation/](./docs/openclaw-automation/) | openClaw 自动化任务统一方案（定时 + 事件订阅 + 简单即时条件；**当前 v4，首版收敛**：单文件 24 页幻灯片（主稿 18 页 + 附录 6 页）+ `02-event-catalog.md` 候选接入清单 + `archify/` 八张图的 Typed JSON 源，v0.1–v3.2 留档 history/）。三条原则：**模型负担轻**——模型只在创建期从 5 个固定模式里选一个、填参数（时间 / 对象 ID / 阈值 / 文案）、回读一句，产物是提案 JSON，脚本 / state / 权限 / job 形态由模板与创建处理函数生成；**机制少**——工程新增只有 5 个模板 + 创建处理函数、EventHub → 官方 `stream` 的桥接命令 `eventhub-sub`，不新增调度体系 / 事件适配器 / 判定模型工具 / 结束与限额协议；**与官方一致**——一条路 `到点 → 条件门（可省略）→ payload → run → 交付` 全是官方名词，`fire` 是 trigger.script 返回值，两种 job 形态（条件门 + agentTurn / 单个 script payload，官方不允许同 job 混用），`once` 以首次成功执行为准，state 仅成功 run 后持久化，approval card / standing grant，接受 stream 的批处理与失败不重试。首版五个场景 S1 晨报 / S2 定时查天气提醒 / S3 到家开灯 / S4 指定来电提醒 / S10 到家查电量（后四个全程零 token）；S5–S9、S11、S12 进路线图并给替代话术。限制分四类三类对模型隐藏；四条轨迹推演（同批两事件 / 旧事件迟到 / 动作失败 / 等待确认时条件改变）；八项拍板 D1–D8；版本锁定三栏（官方已有 / 我们的适配 / 暂不支持）；待核实 V1–V6。**八张 archify 图每张独占一页**：进入视口 trace、`→` / `←` 逐章、`P` 播放、悬停节点看上下游流光、点击钉住；配色沿用原五色；三宽度逐页校验无溢出；另有 **v3.3** 与之并列——v3.2 原内容不改、九张图各占一页、加悬停流光与钉住，供不接受 v4 收敛的读者对照 |
| [docs/photo-search-album/](./docs/photo-search-album/) | 照片搜索 skill × 相册整理 skill 的组合场景（相册整理单向依赖照片搜索；searchTool(query / 是否出卡 / 游标 \| offset / filter `in`・`not in`) 每次 ≤ 500 张；createAlbum / appendAlbum；「一周后同一句话」只追加不在册的）。**当前 v5 五页汇报版**：背景与场景（能力盘点、三个子问题、S1–S10）/ 整体方案（单张分层架构图标已有・新增・待决策：新增只有两项——filter 支持 `album not in [A]` 表达排除、appendAlbum 增加 `source=search` 在工具内吞掉循环；相册整理 skill 不再教翻页；首次与增量同链路 2 个 loop，不做事前报数、事后用 added 汇报）/ 工具定义（searchTool 输入 query・showCard・cursor \| offset・pageSize・filter 与输出 items・hasMore・nextCursor 逐项标已有・新增（只有 hasMore 没有总数），调用示例，filter 取 pageSize 前下推、album 字段 = 成员 ∪ 移出记录；appendAlbum 两种形态、排除搜索与幂等追加释义）/ 关键细节（offset 必错、只靠排除的前提、「排除播种 + 游标定位」——排除定义增量集合、游标保运行内正确、不依赖索引读己之写；索引不及时的时序与静默少加；引擎能力 → 写法决策表）/ 决策 D1–D4・核实 V1–V5・延迟注入验收・风险排序；v3 三页版、v2.1 十四页详版（含索引时效性四页专题）、v2、v1 留档 history/ |
| [docs/omni-realtime-voice/](./docs/omni-realtime-voice/) | omni 实时语音架构洞察（三代架构演进与业界谱系、GPT‑Live 全双工 + 说/想分离、OpenAI 六个月实时系统工程：流式推理/实例切换/压缩即切换/WARP/relay+transceiver、Realtime API 会话与事件模型、对双脑架构的启示、全双工输出状态盘点与统一状态模型 v3.7：44 场景全集（A→X 主序，P0/P1/P2 为色标）× 状态交互图 × 四层分层 ×（状态·floor）× 事件完备性矩阵 × 九缺口与五决策 × 词表校订 × 外挂 ASR 标识（v3.7 汇报版幻灯片 23 页：全貌图 / 分叉树 / 44 场景按时间线展开 / 全集矩阵 / 打断判定窗含回声前置 / 四页 12 条共用时间轴的泳道链路走查 / 四层协议与谁产谁消 / 与外部词表逐项对比 / 五项决策；v1–v3.6 留档 history/）、LiveKit Agents × OpenAI 集成实现） |
| [docs/auto-screenshot/](./docs/auto-screenshot/) | 会议共享 PPT / 网课自动截图（用户手动进入模式）：端上四段管线采屏 → 分块变化检测 → 稳定门（抗过渡与逐条动画）→ 本场 pHash 去重（含回翻）；ROI 忽略头像小窗；PC 指定窗口（WGC / ScreenCaptureKit）+ Android `MediaProjection` 为一期，iOS ReplayKit 为二期；热路径不上模型。含需求场景 S1–S10、「重复」四类定义 Dup-A–D、平台能力对照、拍板 D1–D6 与核实 V1–V6 |
