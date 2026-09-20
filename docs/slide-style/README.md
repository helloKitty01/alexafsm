# 幻灯片风格:archify 画图 / 动态接入与浅色 token

沉淀仓库内 HTML 幻灯片的**画图、动态、交付**规范。起点是对 [tt-a1i/archify](https://github.com/tt-a1i/archify) skill 的分析,落地样板:`docs/kv-cache-discussion/kv cache方案(汇报版·升级版).v2.slides.html`(翻页式,5 张图)与 `docs/openclaw-automation/openClaw自动化任务方案.slides.v4.html`(滚动式,8 张**整页图**,含悬停 Intent Trace 与钉住,配色沿用原稿——只借动态不借风格的样板)。

## 目录

| 文件 | 内容 |
| --- | --- |
| [01-archify借鉴分析.md](./01-archify借鉴分析.md) | archify 是什么;**画图能力**(五种图型作者给什么 / 渲染器管什么 / 我们用在哪 + 写图硬约束);**动态能力四层**(`animation: trace` 顺序即动画、`views` 分章讲述、探索层、URL / hash 外部驱动);接进 deck 的做法(路 C:内联保钩子 + 原文件随附,`inline_archify.py` 与 deck 侧 CSS / JS 说明,版式上怎么放图);v2 逐图落地表;命令清单与常见校验失败修法;顺手借的风格 token;不采纳的 |
| [inline_archify.py](./inline_archify.py) | 把 archify `deliver` 出的 HTML 抽成可内联的 SVG 片段 + 章节 JSON:去 grid / preset、id 加后缀、去可聚焦属性,**保留 data-node-id / data-edge-id / data-animate / --step / data-segment-id 钩子**;sequence 消息补 `data-edge-*`;章节取 `meta.views`(sequence 按 `segments` 切)。用法:`python3 inline_archify.py spec.json delivered.html --suffix xx --out /tmp/xx.json` |
| [check_slides.py](./check_slides.py) | 三视口(1440×900 / 1600×1000 / 1920×1080)逐页逐卡溢出校验 + 可选截图。检查文档滚动、元素内容溢出(含 overflow:hidden 的裁切)、元素出页。用法:`python3 check_slides.py deck.html --shots /tmp/shots`,依赖 playwright |

## 约定(自升级版 v2 起对新幻灯片生效)

### 图

1. 架构 / 流程 / 时序 / 数据流 / 状态类的图**一律用 archify 生成**,不用 CSS chip + "→" 拼;图型按 01 第二节的表选,不确定就 `archify guide`。
2. 每图 ≤ 12 主节点、一条主线、`views` ≤ 5 章;辅助信息进右侧卡,不加连线;中文标签用短词(CJK 按 2 单位算宽)。
3. `validate --quality showcase` 必须 9/9 · 0 error · 0 warning 后再 `deliver`;通过后 JSON 不再改。修复只改诊断指到的对象,两轮不降错就重排。
4. Typed JSON 与 deliver 出的 HTML 一起放在主题目录的 `archify/` 下,改图先改 JSON;原 HTML 供答问时探路 / 上下游 / 播放。
5. 内联用 `inline_archify.py`,**保留钩子**;deck 的 `<style>` 里要有 archify 的语义类(`.c-* / .a-* / .m-* / .t-* / .s-*`)、七组颜色变量、以及 `.c-region` / `.c-security-group`。

### 动态

6. 图页的 `meta` 写 `animation: "trace"` + `views`;进页跑一遍 trace,`→` / `←` 先走章节再翻页,`P` 自动播放,`↑` `↓` 直接翻页;深链 `#p=N&c=K`。
7. 分章只动讲述焦点(压暗 / 流动),不动几何;`prefers-reduced-motion` 下全部关闭。
8. 版式:**图默认独占一页**(`.slide.figure`:页头 lede + 图占满 + 章节栏),说明文字放相邻页;退而求其次才是独占一列(≥ 60% 宽);一列里不放"图 + 大段代码"。
8a. 配色:archify 的七组颜色变量映射到 deck 自己的色板,不引入它的配色;滚动式 deck 用视口居中判定当前图(见 01 第 4.4 节)。
8b. 悬停:图页必须带 Intent Trace 层——悬停节点压暗非相邻、相邻边跑光点(出边 / 入边 / 自环三色),悬停边亮两端,点击钉住并显示上游 / 下游数(见 01 第 4.5 节)。

### 风格与交付(v1 起)

9. 色块"低透明填充 + 同色描边 + 描边色文字";颜色 = 类型,状态只用 good / bad / accent + 斜纹 / 虚线。
10. 页头三段:eyebrow(页码 · 章节)+ 短标题(≤ 20 字)+ 一句 lede;口径放页脚;右上角状态 badge。
11. 禁止 `overflow: hidden` 裁切;交付前 `check_slides.py` 三视口全通过,溢出靠删冗余、压间距、调密度档解决。
12. 图例由脚本按出现过的类型生成;支持 `#p=N` 深链、`F` 演示态、`T` 深浅色、`S` classic / editorial。
