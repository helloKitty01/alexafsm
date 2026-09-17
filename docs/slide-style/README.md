# 幻灯片风格:archify 借鉴与浅色 token

沉淀仓库内 HTML 幻灯片的视觉与交付规范。起点是对 [tt-a1i/archify](https://github.com/tt-a1i/archify) skill 的分析,落地样板是 `docs/kv-cache-discussion/kv cache方案(汇报版·升级版).v1.slides.html`。

## 目录

| 文件 | 内容 |
| --- | --- |
| [01-archify借鉴分析.md](./01-archify借鉴分析.md) | archify 是什么、与我们幻灯片的关系;两套浅色 token 对照表;九条可借鉴(填充 + 描边、语义 / 状态分离、密度预算、标题三段、禁裁切、editorial 第二套皮、自动图例、深链 / 演示、直接用它画图);我们要保留的(数据绑定、em 预算 deck、中文字体);升级版 v1 逐条落地表;用 archify 给幻灯片画图的操作与常见校验失败修法;不采纳的 |
| [check_slides.py](./check_slides.py) | 三视口(1440×900 / 1600×1000 / 1920×1080)逐页逐卡溢出校验 + 可选截图。检查文档滚动、元素内容溢出(含 overflow:hidden 的裁切)、元素出页。用法:`python3 check_slides.py deck.html --shots /tmp/shots`,依赖 playwright |

## 约定(自升级版 v1 起对新幻灯片生效)

1. 色块一律"低透明填充 + 同色描边 + 描边色文字",不用实心底 + 白字 + text-shadow;每个类型只定义一个 `--c`,用 `color-mix()` 派生。
2. 颜色 = 类型(层级四色),状态只用 good / bad / accent 三色 + 斜纹 / 虚线区分中间态。
3. 页头三段:eyebrow(页码 · 章节)+ 短标题(≤ 20 字)+ 一句 lede;口径与数据来源放页脚;右上角状态 badge(实测 / 推演 / 已上线)。
4. 禁止 `.card { overflow: hidden }` 式裁切;交付前用 `check_slides.py` 三视口全通过,溢出靠删冗余、压间距、调密度档(normal / dense / denser)解决,不缩字号到 `.56em` 以下。
5. 图例由脚本按出现过的类型生成,不手写。
6. 支持 `#p=N` 深链、`F` 演示态、`T` 深浅色、`S` classic / editorial 预设。
7. 流程 / 时序 / 数据流类的图优先用 archify 生成(`validate --quality showcase` 9/9 通过后内联 SVG),不用 CSS chip 拼。
