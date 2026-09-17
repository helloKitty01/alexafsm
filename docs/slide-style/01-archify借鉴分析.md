# Archify skill 借鉴分析:我们的浅色幻灯片能学什么

> 对象:[tt-a1i/archify](https://github.com/tt-a1i/archify)(v2.17,MIT)——`archify/SKILL.md`、`assets/template.html`(主题 / 预设 CSS)、`references/authoring-contract.md`。
> 对照:`docs/kv-cache-discussion/kv cache方案(汇报版).v1.4.slides.html`(浅色,与 `KV-Cache收益闭环.v7.2` 同一套模板)。
> 落地:同目录 `kv cache方案(汇报版·升级版).v1.slides.html`,本文第五节逐条对应。

## 一、archify 是什么,和我们的幻灯片是什么关系

它不是 PPT 工具,是"架构图渲染器 + 校验器":Agent 写一份 Typed JSON(architecture / workflow / sequence / dataflow / lifecycle 五种),Node 脚本确定性编译成单文件 HTML + 内联 SVG,自带深浅主题、四套视觉预设(classic / signal-flow / blueprint / editorial)、聚焦 / 路径 / 章节播放等交互;并强制做布局校验——连线穿节点、标签重叠、留白不足直接报错,`validate --json` 返回稳定规则码和"只改这个对象"的修复指引。

所以可借鉴的分三层:**视觉 token**、**图的组织纪律**、**交付 / 校验流程**。另外它本身能作为我们幻灯片里"图页"的生成器(Node ≥ 18 即可,本机 v18.20 已验证 `doctor` 全绿)。

## 二、视觉 token 对比:两套色板几乎同源

两边都是 Tailwind slate 系,颜色上不用改,archify 生成的 SVG 嵌进我们的页里不违和。真正值得借的是**怎么用色**。

| 角色 | 我们 v1.4(浅色) | archify classic-light | 升级版 v1 取值 |
| --- | --- | --- | --- |
| 页面底 | `#e9edf4` | `#f8fafc` | `#eef2f7`(比页面白略深,让页面浮起) |
| 页面 / 面板 | 白 → `#eef3fb` 135° 渐变 | `#ffffff` 平面 | `#ffffff` 平面(去渐变) |
| 卡片 | `#f7f9fc` | `#ffffff` panel | `#f8fafc` |
| 边线 | `#dfe5ee` | `#e2e8f0` | `#e2e8f0` |
| 正文 / 次要 / 弱化 | `#1f2a3d` / `#5c6b84` / — | `#0f172a` / `#64748b` / `#94a3b8` | `#0f172a` / `#64748b` / `#94a3b8`(补第三档) |
| accent / good / warn / bad | `#2563eb` / `#059669` / `#d97706` / `#dc2626` | 主路径 `#059669`,security `#e11d48` | 不变 |
| 层级色 prod / sess / q / loop | `#3b5bdb` / `#7c3aed` / `#d97706` / `#0891b2` | 七类各一组"低透明填充 + 饱和描边" | 色相不变,表达方式改成填充 + 描边 |

archify 的七类语义色(供图页直接用):frontend 青 `#0891b2`、backend 绿 `#059669`、database 紫 `#7c3aed`、cloud 琥珀 `#d97706`、security 玫红 `#e11d48`、messagebus 橙 `#ea580c`、external 灰 `#64748b`;连线 `#94a3b8`,主路径强调 `#059669`;填充统一为同色 8–20% 透明。

## 三、值得借鉴的九点(按收益排序)

1. **填充 + 描边替代实心色块**。我们 `.bars .seg .top` 是饱和实心底 + 白字 + text-shadow,浅色页上很重、投影发灰。archify 一律 8–20% 透明填充 + 1.5px 同色描边 + 用描边色写字。做法:每个层级只定义一个 `--c`,块用 `background: color-mix(in srgb, var(--c) 14%, #fff); border: 1.5px solid var(--c); color: var(--c)`。虚框(待定 / 未定)自然变成 `border-style: dashed`,对应它的 `dashed` variant。
2. **语义色与状态色分开**。我们 q 级 = warn 都是 `#d97706`,prod `#3b5bdb` 和 accent `#2563eb` 几乎一样,读者要靠文字判断"这是层级还是状态"。archify 的原则:**颜色 = 类型,强调靠 variant(default / emphasis / security / dashed),状态不靠换色靠描边 / 虚线**。层级四色保留;状态只留 good / bad + 蓝色"新增";"被连带"这类中间态改用斜纹(我们 `first` 已经用了 repeating-linear-gradient,推广即可)。
3. **一页一条主线、≤ 12 个主节点、辅助信息进说明卡而不是加连线**。这是它 SKILL.md 的硬约束。我们 P3 一页塞 4 张 KPI 卡 + 三格 + 四列表 + 四步卡,字号压到 `.56–.72em`。定一个"密度预算":正文字号下限 `.66em`,每页 ≤ 3 个内容块,超出的拆进附录(我们已有附录 A / B 的做法,把它变成规则)。
4. **标题层级**:"一个短标题,让图说话;subtitle 默认省略,不允许复述标题 / 节点"。我们 h2 是整句结论 + `<small>` 口径说明,P2 标题 60+ 字。改成三段:**eyebrow(页码 · 章节)+ 短标题(≤ 20 字)+ lede(一句结论)**,口径和数据来源统一下沉到页脚。
5. **不允许用 `overflow: hidden` 假装通过**。我们 `.card { overflow: hidden; /* 防御 */ }` 正是它明令禁止的做法。它要求在 1440×900 / 1600×1000 / 1920×1080 下 `scrollWidth ≤ innerWidth && scrollHeight ≤ innerHeight`,溢出只能删冗余或压间距,不能缩字号、不能裁切。配一个 `check_slides.py`(本目录)跑三个视口,逐页逐卡检查 `scrollHeight > clientHeight`,把裁切改成报错。
6. **editorial 浅色预设当"汇报版"的第二套皮**。暖纸底 `#f2eee5`、面板 `#fbf8f1`、边 `#c4b9a6`、墨色 `#242018`、次要 `#6f6658`、强调锈红 `#bb4c23`,标题衬线(Georgia / Songti SC),背景一条细竖线 + 32px 横格。"讨论稿"和"给领导的汇报版"用两套皮一眼可辨,几何完全不变。blueprint 浅色(`#edf7fa` 底 + 32px 网格 + 青蓝 `#087f9c`)适合架构页。
7. **图例只列出现的类型**(`meta.legend` 默认 `auto`)。我们的图例是手写六项挂在 h3 里。规则化:段块标 `data-kind`,脚本扫描后只生成出现过的项。
8. **深链与演示态**。`#view=` / `#focus=` / `#route=` 可恢复状态,`F` 进演示,`T` 切主题,`S` 循环预设。我们只有翻页;加 `#p=N`、`F`(隐藏页脚 / lede / 导航)、`T` / `S` 是小成本。
9. **直接拿它画图**。我们 P4–P6 "一轮 = 1–2 次调用"和附录 B "两次 prefill"都是 CSS chip + "→" 拼的;正好对应 archify 的 `sequence`,`meta.locale: zh-CN` 支持中文 viewer UI。渲染出的 SVG 只依赖一组语义类(`.c-* / .a-* / .m-* / .t-* / .s-*`)和 CSS 变量,把这组样式和变量并进幻灯片即可内联。注意它按 CJK = 2 单位算标签宽度,中文标签要短。

## 四、我们比它强、要保留的

- `data-b` / `data-calc` 数据绑定:改 `BASELINE` 全稿同步。archify 的 JSON 是静态事实,没有这层。
- em 预算 + `clamp()` 等比缩放的 16:9 deck,多页节奏;archify 是单图自适应。
- 中文正文用 PingFang,数字 / 标识用 mono。archify 全局 JetBrains Mono,中文场景不该照搬;但 M1–M11、K1–K4、R1–R6 这类标识全 mono 是对的。

## 五、升级版 v1 逐条落地

| 借鉴点 | 升级版 v1 的做法 |
| --- | --- |
| 1 填充 + 描边 | `.seg .top`、`.hseg`、`.mat .c`、`table.bl .lv`、`.aseg` 全部改为 `color-mix()` 填充 + 同色描边 + 描边色文字;去掉所有 `text-shadow` |
| 2 语义 / 状态分离 | 层级四色只出现在"这段属于哪一级";命中 / 白算 / 新增三态用 good / bad / accent;"被连带"与"首次载入""异常"用斜纹区分 |
| 3 密度预算 | 正文最小 `.66em`;P3 四张尺子卡压成两行两列 + 表格,四步卡不变 |
| 4 标题三段 | 每页 `<header class="hd">`:eyebrow(`P4 · 场景账目 · 任务型 25%`)+ `h2`(短标题)+ `.lede`(一句结论)+ 右侧状态 badge(实测 / 推演 / 已上线) |
| 5 禁裁切 | 删除 `.card { overflow: hidden }`;`check_slides.py` 三视口逐页逐卡校验通过 |
| 6 第二套皮 | `S` 键在 classic / editorial 间切换(变量替换,几何不变);`T` 键深浅色 |
| 7 自动图例 | `.legend[data-for]` 由脚本扫描目标容器的 `data-kind` 生成 |
| 8 深链 / 演示 | `#p=N` 同步地址栏;`F` 演示态;`Home` / `End`;`[` / `]` 跨章节(正文 ↔ 附录) |
| 9 archify 画图 | 附录 B 的"两次 prefill"时间线换成 archify `sequence`(4 参与者 · 3 段 · 10 条消息);新增附录 C "一个 Q 的两次模型调用"`sequence`(5 参与者 · 2 段 · 12 条消息);两张图均 `validate --quality showcase` 9/9 通过、0 error 0 warning 后 `deliver`,再抽 SVG 内联 |

## 六、用 archify 给幻灯片画图的操作

```bash
# 安装(任选)
npx skills add tt-a1i/archify -g            # 作为 skill
git clone --depth 1 https://github.com/tt-a1i/archify.git && cd archify/archify && npm i   # 作为 CLI

node bin/archify.mjs doctor
node bin/archify.mjs guide "会话创建后台预热两次 prefill" --json      # 不确定用哪种图时问它
# 写 JSON(只读一个 schema + 一个 example),然后:
node bin/archify.mjs validate sequence x.sequence.json --quality showcase --json   # 要 9/9 checks、0 error、0 warning
node bin/archify.mjs deliver  sequence x.sequence.json x.html --quality showcase --json
```

内联到幻灯片:

1. 从 `x.html` 取 `<svg …>…</svg>`;把 `id` 全部加页内唯一后缀(marker、title、desc、节点),同步替换 `url(#…)` 与 `aria-labelledby`;去掉 `data-*`、背景 `grid` 矩形与 pattern。
2. 幻灯片 `<style>` 里并入两块:archify light 的变量(`--frontend-fill/stroke` 等七组 + `--arrow` / `--arrow-emphasis` / `--lane-fill` / `--lane-stroke` / `--mask` / `--text*`)和语义类样式(`.c-*` / `.a-*` / `.m-*` / `.t-*` / `.s-*` / `.semantic-sigil`)。升级版 v1 的 `<style>` 里已带这两块,可直接复用。
3. 给 `svg.archify` 设 `width:100%; height:auto; display:block`,放进 `.card` 即可;深浅主题与预设切换会一起生效。

常见校验失败与修法(都来自本次实践):`viewBox` 高度 ≥ 480;消息 y 在 `[160, height − 83]`;共享横向区间的两条消息 y 差 ≥ 28;segment y 在 `[72, height − 45]`;CJK 标签按 2 单位算,长标签换短词而不是删语义。

## 七、不采纳的

- 全局 JetBrains Mono:中文正文可读性差。
- 单图满屏(first-screen artifact):幻灯片一页多块,图只能占一列;所以图页用"左图右卡"而不是 archify 自己的"上图下卡"。
- Typed JSON 替代手写 HTML:我们的账目页(P4–P6)是数据驱动渐变条,archify 五种图型都不覆盖;继续用自家 `renderAccount()`。
