# 照片搜索 × 相册整理（含 500 条分页与增量更新）

两个 skill 的组合场景：**相册整理 skill** 依赖**照片搜索 skill**（单向）；照片搜索的 **searchTool**（query、是否出卡、游标 | offset、pageSize、filter——表达式，支持 `in` / `not in` 数组）每次最多返回 500 张；相册整理有 **createAlbum** / **appendAlbum**。
「帮我把小猫的照片建一个相册」一周后再说一次时只追加新增的照片。本目录沉淀需求与场景、整体方案、工具定义、关键细节与待核实项。

**当前（5 页汇报版）**：
P1 背景与场景（现有能力盘点、三个子问题、两条边界、场景矩阵 S1–S10）；
P2 整体方案（一张分层架构图标清**已有 / 新增 / 待决策**：新增只有两项——searchTool 的 filter 支持 `album` 字段即 `album not in [A]` 表达排除、appendAlbum 增加 `source=search` 形态在工具内吞掉循环；相册整理 skill 改写不再教翻页；主流程首次与增量同一条 2 个 loop：找册 → appendAlbum → 用 added 汇报。**不做事前报数**——searchTool 只有 hasMore 没有总数）；
P3 工具定义（searchTool 输入 query / showCard / cursor | offset / pageSize / filter 与输出 items / hasMore / nextCursor 逐项标已有・新增，调用示例，filter 必须在取 pageSize 之前下推、`album` 字段 = 成员 ∪ 移出记录；appendAlbum 两种形态，并解释**排除搜索**（引擎截断前先扔掉已在册的）与**幂等追加**（已在册跳过、同一批加两次结果一样）；createAlbum；找册）；
P4 关键细节（offset 必错 / 只靠排除的前提 / 排除播种 + 游标定位；推荐写法；索引更新不及时的时序与静默少加；引擎能力 → 写法决策表）；
P5 决策 D1–D4（D4 = 不事前确认、事后用 added 汇报、首轮 hasMore 走异步）、核实 V1–V5、验收加两条延迟注入用例、风险排序、下一步。
「同名默认追加」「移出记录」归入已有能力；幻灯片正文不带版本信息。

## 目录（当前版本）

| 文件 | 内容 |
| --- | --- |
| [01-需求与场景.md](./01-需求与场景.md) | 全文（顶部有术语对照）：一句话问题、能力边界与依赖方向、场景矩阵、三项拍板（4.1 排除与游标的分工 / 4.2 工具吞掉翻页 / 4.3 索引时效性专题 A–D）、工具契约、主流程、依赖与挑战、待核实 |
| [图搜建册方案.slides.v5.html](./图搜建册方案.slides.v5.html) | 5 页汇报版（浅色 16:9）：背景与场景 / 整体方案（单图标已有・新增・待决策）/ 工具定义（searchTool 输入输出、appendAlbum 两种形态、排除搜索与幂等追加释义）/ 关键细节 / 决策・核实・验收 |

## 历史版本（[history/](./history/)）

| 文件 | 说明 |
| --- | --- |
| 图搜建册方案.slides.v4.html | 5 页版首稿：含事前「报数」步骤与 searchTool 新增 total 输出（searchTool 实际没有总数，已撤回） |
| 图搜建册方案.slides.v3.html | 3 页汇报版（统一术语后的首版；无独立工具定义页） |
| 图搜建册方案.slides.v2.1.html | 14 页详版：当前 / 目标两张架构图对照、五个优化点、索引时效性四页专题（A 问题 → B 根因 → C 三策略决策表 → D 影响与验收）；旧术语（search / add_to_album / add_from_search / exclude_album） |
| 图搜建册方案.slides.v2.html | 8 页；三项拍板 + 「排除即翻页」为首选（未处理索引时效性） |
| 图搜建册方案.slides.v1.html | 初版 6 页（深色版式；翻页由模型驱动、三项待拍板） |
