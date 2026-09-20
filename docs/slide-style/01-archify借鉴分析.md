# Archify 借鉴分析:把它的画图与动态能力接进我们的幻灯片

> 对象:[tt-a1i/archify](https://github.com/tt-a1i/archify)(v2.17,MIT)——`archify/SKILL.md`、`assets/template.html`(viewer 运行时)、`renderers/*`(五种渲染器)、`references/viewer-runtime.md`。
> 落地:`docs/kv-cache-discussion/kv cache方案(汇报版·升级版).v2.slides.html`(16 页,5 张 archify 图,全部可分章、可 trace),源文件在同目录 `archify/`。
> 结论先说:**值得学的是"作者给拓扑、渲染器管几何纪律"的画图方式和"顺序即动画、分章即讲述"的动态机制;配色与版式我们原有的浅色系已经够好,不动。**

## 一、archify 是什么

不是 PPT 工具,也不是自动布局器,是"架构图渲染器 + 校验器 + 探索式 viewer":Agent 写一份 Typed JSON(`architecture` / `workflow` / `sequence` / `dataflow` / `lifecycle` 五种),Node 脚本确定性编译成单文件 HTML + 内联 SVG;布局校验强制通过(连线穿节点、标签互压、走线节律、桌面可读性,`validate --quality showcase` 必须 9/9、0 error 0 warning),`--json` 回执给稳定规则码和"只改这个对象"的修复指引。生成的 HTML 自带深浅主题、聚焦 / 上下游可达 / 路径探查 / 语义透镜 / 分章故事 / 演示态 / 导出。

对我们的价值分两层:**画图**(第二节)、**动态**(第三节);怎么接进 deck 见第四节;它的一些风格 token 顺手借了,放第七节。

## 二、画图能力:作者给什么、渲染器管什么

| 图型 | 作者给 | 渲染器管 | 我们用在 |
| --- | --- | --- | --- |
| `architecture` | 组件(`type` 七类 · label · sublabel · tag)、`boundaries`(`region` / `security-group`,`wraps` 一组节点)、连线(`variant` default / emphasis / security / dashed);坐标 `pos` 自由放或 `layout.mode: grid` + `row/col` | 正交走线、端口自动展开(多条线不堆一个点)、标签避让、连线穿节点 / 标签互压直接报错 | P2 全景架构:四路来源 → 应用 → 引擎 ↔ 缓存 → 工具,两个边界 |
| `workflow` v2 | `lanes` × 逻辑列 `col` 0–5、`phases`(阶段头)、`groups`、`mainPath`、`lane.variant: exception` | **几何全部由编译器解**,作者不写坐标;`validate --layout-json` 给可读的布局回执 | P5 四步路线:三级泳道 + 例外道,主线 = 四步 |
| `sequence` | 参与者、`segments`(y 区间 + 标签)、消息(y · variant)、`activations` | 列宽(`column_fit: spread`)、消息间距 ≥ 28、标签净空 | 附录 B 预热、附录 C 一个 Q 两次调用 |
| `dataflow` | `stages` + 节点(`stage` · `row`)+ 流(`classification` 标数据类别) | 阶段列几何固定(5 阶段需 viewBox ≥ 1068 宽)、节点 112 宽 | P11 统计管线 |
| `lifecycle` | `lanes` + 状态(`type` active / waiting / failure / terminal)+ 转移 | 主轨 / 事件列对齐 | 暂未用(适合"缓存块的生命周期:写入 / 命中 / 逐出 / TTL") |

另外两个没用上但值得记住的:`compare architecture base.json head.json` 生成 **Before / Delta / After**,区分新增 / 删除 / 语义变化 / 移动 / 重路由(正好对应 P3 "当前 vs 目标"的拓扑变化);`meta.repository` 让 architecture 节点带 `SRC n` 指向真实源码行。

### 写图时的硬约束(全部踩过)

- 每图 ≤ 12 主节点、一条主线、`views` ≤ 5 章;辅助信息进 `cards`,不加连线。
- **CJK 标签按 2 单位算宽**,中文要短词;dataflow 节点 112 宽固定,超长副标题直接 `desktop-readability` 失败。
- 标签默认落在段中点,两条线共用走廊时必撞;修法顺序:`labelSegment`(换段)→ `labelDx/labelDy`(挪)→ 换端口 `fromSide/toSide` → 短词;不要先删语义。
- architecture 里"一堆源 → 一个汇"最好让源横排在上、汇居中在下(标签各占自己一列的竖段),不要竖排在左(四条线挤一条竖走廊)。
- workflow v2 中分叉边会和主线共用列间走廊(`ambiguous-corridor` / `proper-crossing`),调泳道顺序比调 `route` 管用;`drop` 等预设在紧约束下可能无解。
- dataflow 双出边端口会展开 ±7px,同排直连就出 7px 微段;让分叉节点单独占一列,或把分叉挂到下游。
- 一次 `validate` 只改诊断指到的对象;两轮不降错就停下重排,别硬调坐标。

## 三、动态能力:四层机制,都不复杂

读 `assets/template.html` 的实现,动态分四层:

**1. `meta.animation: "trace"` —— 顺序即动画。** 渲染器给每条边 / 每个节点打 `data-animate="edge|node"` + `style="--step:N"`,N 来自 authored 顺序(消息顺序 / mainPath / 边的序号)。CSS 只有两组 keyframes:

```css
[data-animate="edge"] { animation: archify-edge-flow 2.4s linear 1; animation-delay: calc(var(--step) * 160ms); }
@keyframes archify-edge-flow { 0% { stroke-dasharray: 10 8; stroke-dashoffset: 54; opacity: .42 } 88% { stroke-dashoffset: 0; opacity: 1 } 100% { stroke-dashoffset: 0 } }
@keyframes archify-node-pulse { 18%, 36% { filter: drop-shadow(0 0 8px var(--arrow-emphasis)); stroke-width: 2.4 } }
```

本质是 PPT 的"按顺序出现 + 沿线流动",但**顺序不是手工 K 帧,是从图的语义里来的**;只跑一遍(ambient pass),`100%` 关键帧不写 `stroke-dasharray` 让虚线回到 authored 线型(实线 / 安全虚线 / 异步虚线),这个小技巧我们照搬了。

**2. `meta.views` —— 一张图分章讲(≤ 5 章)。** 每章 `{id, label, focus: [节点 id], note}`。播放时非焦点节点压暗、相邻站点之间沿 authored 关系画流动轨迹、每章 3.2 s、镜头跟随。**几何不动,动的是讲述焦点**——正是汇报最需要的"图不变、重点在走",不用画五张图。它只按作者写的相邻关系分类(forward / reverse / multiple / 无直连),不推断。

**3. 探索层(答问用)。** `#focus=id`、`#focus=id&reach=upstream|downstream`、`#route=a~b`(最短有向路径逐站)、`#lens=kind~kind`(角色对比),键盘 `/` 搜节点、`R` 探路、`L` 透镜、`M` 雷达。汇报不用,被问"这条线断在哪"时打开原 HTML 直接演示。

**4. 外部驱动。** URL 参数 `?theme=light|dark&present=1&play=1&embed=1`,hash `#view=` / `#focus=` / `#route=`,且监听 `hashchange`——父页面改 iframe 的 hash 即可翻章,不需要 postMessage。坑:`embed=1` 会强制关掉 ambient trace(只留 story),要 trace 用 `present=1`。

## 四、接进 deck 的做法(路 C:内联保钩子 + 原文件随附)

三条路比较过:A 用 iframe 嵌原成品(动态一个不丢,但 deck 不再单文件、`file://` 下 iframe 抢焦点);B 内联 SVG 但保留钩子、移植两段 CSS + 一段小 JS(单文件、节奏可控,失去 route / reach / lens);**C = B + 同目录保留原 HTML 供答问**。选 C。

### 4.1 `inline_archify.py`(本目录)

```bash
python3 inline_archify.py <spec>.json <delivered>.html --suffix xx --out /tmp/xx.json
# 输出 { svg, chapters:[{l 章名, t 说明, n [节点 id], e [边 id]}], type, title }
```

做的事:只取 `<svg>`;去背景 grid 与 `data-preset` / `data-quality-profile`(由 deck 的 `html[data-theme]` / `html[data-preset]` 接管);**所有 id 加页内后缀**并同步 `url(#…)` / `aria-labelledby`(一页可放多张);去 `tabindex` / `role="button"` / `aria-*`(幻灯片不需要可聚焦节点);**保留** `data-node-id` / `data-edge-id` / `data-edge-from|to` / `data-animate` / `--step` / `data-composition-points` / `data-segment-id`;sequence 的消息只有 `data-composition-edge-*`,统一补成 `data-edge-*`,五种图型在 deck 侧用同一套选择器。

章节从哪来:非 sequence 图取 `meta.views`,`e` = 两端都在 `focus` 里的边;sequence 图**按 `segments` 切章**(`e` = y 落在段内的消息,`n` = 涉及的参与者),`views` 数量一致时借用其 `note`——因为时序图的 focus 几乎总是全部参与者,按段分才有信息量。

### 4.2 deck 侧(CSS ~40 行 + JS ~120 行,已在 v2 里)

- `.diagram[data-chapters]` 挂章节 JSON,内含 `svg.archify` 与一条 `.chap` 章节栏(圆点 = 全图 + 各章,文字 = 章名 · 说明,右侧键位提示)。
- **进页**:`svg[data-animation="trace"]` 加 `data-tracing`,按 archify 的 `--step` 跑一遍边流动 + 节点脉冲,`maxStep × 150ms + 2.6s` 后移除。
- **分章**:`svg[data-chapter]` 下,不在 `n` 的 `[data-node-id]`、不在 `e` 的 `[data-edge-id]`(边与标签组同时命中)、不是当前段的 `[data-segment-id]` 打 `data-dim`;`e` 内的边按序写 `--cs`,`path[data-flow]` 以 `--cs × 260ms` 依次流动。
- **键位**:`→` / `Space` 先走章节再翻页,`←` 先回退章节再翻页,`↑` `↓` 直接翻页,`P` 自动播放(3.2 s / 章,到末章停),深链 `#p=N&c=K`,监听 `hashchange` 可被外部驱动。
- 边界 / 例外泳道需要 deck 补两条类:`.c-region`(琥珀虚线)、`.c-security-group`(玫红虚线),否则渲染成黑块。
- `prefers-reduced-motion` 下全部动画关闭、线型回到静态。

### 4.3 版式上怎么放图

- architecture / workflow 适合"左图右卡"(图 flex 1.7–2,四张 `dcard`);dataflow 天生又宽又稀(阶段列固定 ~215px 间距、8–10px 字号),**必须整页横贯**(P11),塞进半栏字号会掉到 6px 以下不可读。
- sequence 放半栏没问题(附录 B / C)。
- 图页说明尽量进 `.chap` 章节说明和 h3 副标题,`cards` 里的话搬到右侧卡;archify 自带的图例保留(它只列出现过的类型)。

### 4.4 第二个样板:openclaw-automation v3.2(滚动式 deck,九张图,配色不变)

同一套 `inline_archify.py` + 分章引擎接进另一个 deck 时验证了几件事:

- **配色可以完全不动**:archify 只输出语义类(`.c-frontend` 等七类 + `.a-*` / `.m-*` / `.t-*`),把七组 `--*-fill / --*-stroke` 变量映射到目标 deck 自己的色板即可(那份稿是 蓝 = 模型 · 紫 = openClaw 非 LLM · 绿 = 事件中心 · 橙 = 新增 · 红 = 配额),连线主路径 `--arrow-emphasis` 也跟着换。"只借动态、不借风格"成立。
- **滚动式 deck 的引擎变体**:没有 `.slide.active`,`→` / `←` / `P` 作用于视口内最居中的 `.panel.diagram`(取 `getBoundingClientRect` 中心到视口中心的距离),`IntersectionObserver` 在图进入 ≥ 60% 时跑一遍 trace、离开时回全图;给当前图加 `.focus` 外框提示。
- **图的高度是硬约束**:archify 标签 8–10px 在 980–1100 宽的 viewBox 里,放进半栏(≈550px)就掉到 5px。可读的摆法只有两种——图独占一列(≥ 60% 宽,P4 / P6 / P10 / P17 / A5)或右栏图 + 下方一张小表(P11 / A10);一列里"图 + 大段代码"必定把图压成缩略图,宁可把代码挪到附录引用。
- **`lifecycle` 图型**:`main` 泳道是主轨(隐式前进箭头,无 `data-edge-id`,分章时不压暗),`terminal` 是底部终态带,其余泳道共用中间事件带,事件 / 终态列 N 对齐主轨列 N + 2;回退边用 `fromSide/toSide: top` + `via` 走上方通道,标签用 `labelDy` 挪出节点。适合画 trigger.state 这类"跃迁名 = 转移标签"的状态机。
- **`dataflow` 的分叉**:同一节点两条出边到同一排会出 7px 微段,把分叉合成一个节点或把目标分到不同 `row`;三阶段 viewBox 至少 1068 宽。
- **`sequence` 按段分章**比按 `views.focus` 有信息量得多;`inline_archify.py` 已默认按 `segments` 切。

## 五、v2 逐图落地

| 页 | 图型 | 拓扑 | 章 | 主要修复 |
| --- | --- | --- | --- | --- |
| P2 全景架构 | architecture | 版本发布 / 用户资料 / 会话历史 / 检索 → Agent 应用 → 推理引擎 ↔ KV 缓存,应用 ↔ 工具;region "缓存实例 · 会话粘性",security-group "用户私域" | 三级来源 / 一次调用 / 工具往返 | 源从竖排改横排;应用 ↔ 引擎往返用 `labelDy` 上下分;引擎 → 缓存标签 `labelDy +60` 落到区域内 |
| P5 四步路线 | workflow v2 | 泳道 产品级 / 轮次 / 会话级 / 不进账本(exception),阶段 当前 · ①–④ · 目标,mainPath = 四步,分叉 会话级冻结 → 预热 | ① / ② / ③ / ④ | 泳道顺序改为 产品级 / 轮次 / 会话级,预热直接放在会话级下方,消掉走廊冲突 |
| P11 统计管线 | dataflow | 来源(引擎 · 应用)→ 明细 → 归因 → 聚合 → 输出(报警 · 日报) | 采集 / 归因 / 报表与报警 | 三张报表合成一个"日报"节点(三出边标签无处放),报警改挂在聚合之后;副标题缩短过 desktop-readability |
| 附录 B | sequence(+trace +views) | 4 参与者 · 3 段 · 10 消息 | 会话创建 / ASR 期间 / 真正推理 | — |
| 附录 C | sequence(+trace +views) | 5 参与者 · 2 段 · 12 消息 | 调① / 调② | — |

## 六、命令清单

```bash
git clone --depth 1 https://github.com/tt-a1i/archify.git /tmp/archify && cd /tmp/archify/archify   # Node ≥ 18,无需 npm i
node bin/archify.mjs doctor
node bin/archify.mjs guide "会话创建后台预热两次 prefill" --json                      # 不确定图型时问它
node bin/archify.mjs validate <type> x.json --quality showcase --json                 # 要 9/9 · 0 error · 0 warning
node bin/archify.mjs deliver  <type> x.json x.html --quality showcase --json          # 通过后 JSON 不再改
python3 docs/slide-style/inline_archify.py x.json x.html --suffix xx --out /tmp/xx.json   # 抽 SVG + 章节
python3 docs/slide-style/check_slides.py deck.html --shots /tmp/shots                 # 三视口溢出校验
```

常见校验失败与修法:`label-route-clearance`(标签压到别的线)→ `labelSegment` / `labelDx|Dy`;`endpoint-side-direction`(显式 side 与走线方向不一致)→ 改 side 或删掉让它自动;`ambiguous-corridor` / `proper-crossing`(两条边共用列间走廊)→ 调泳道顺序或列;`micro-segment` / `short-interior-segment`(端口展开造成 7–13px 小段)→ 让分叉节点独占一列;`desktop-readability` → 缩短 label / sublabel / tag;sequence:`viewBox` 高 ≥ 480、消息 y ∈ [160, height − 83]、同一横向区间两条消息 y 差 ≥ 28。

## 七、顺手借的风格 token(v1 已落地,不再投入)

两套色板同源(Tailwind slate),archify SVG 嵌进浅色页不违和。v1 借了:填充 + 描边替代实心色块、颜色 = 类型 / 状态靠描边虚线斜纹、页头三段(eyebrow · 短标题 · lede)、禁 `overflow: hidden` 裁切并用 `check_slides.py` 三视口校验、自动图例、`#p=N` 深链 / `F` 演示 / `T` 深浅色 / `S` editorial 第二套皮。这些留着,但后续精力放在图与动态上,不再往配色方向做。

## 八、不采纳的

- 全局 JetBrains Mono:中文正文可读性差。
- Typed JSON 替代手写 HTML:账目页(P6–P8)是数据驱动渐变条,archify 五种图型都不覆盖;继续用自家 `renderAccount()`。
- iframe 嵌原成品作为主路径:deck 要保持单文件;原 HTML 只作答问附件。
- `visual_preset: signal-flow`:深色霓虹风,与汇报浅色版不搭;editorial 只作 `S` 键备选。
