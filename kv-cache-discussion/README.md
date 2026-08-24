# KV Cache 与 Agent 上下文工程讨论

这是一个讨论用目录，用于沉淀关于大模型 KV cache 命中率与 agent 上下文组织的设计讨论。
内容随讨论持续迭代。

## 目录

| 文档 | 内容 |
| --- | --- |
| [01-问题定义.md](./01-问题定义.md) | 当前系统面临的上下文组织问题（UAT 消息流、动态 skill 等） |
| [02-上下文分层与排布.md](./02-上下文分层与排布.md) | 按变化频率分层的排布方案与"渐进式加载"设计 |
| [03-压缩策略.md](./03-压缩策略.md) | 超长上下文"从远到近"压缩的缓存代价分析与改进 |
| [04-开放问题.md](./04-开放问题.md) | 待讨论、待确认的问题清单 |
| [05-渐进式加载详细设计.md](./05-渐进式加载详细设计.md) | L2 内容随 user message 结构化注入的详细方案（消息规范、去重、压缩交互） |
| [06-模型侧拼接细节.md](./06-模型侧拼接细节.md) | DeepSeek V4 / GLM 5.2 的 tools 拼接位置、defer_loading、reasoning 剔除与验证脚本 |
| [07-分代冻结详解.md](./07-分代冻结详解.md) | 分代冻结机制展开：合并式 vs 堆叠式、时间线算账、字节级冻结的工程陷阱 |
| [08-量化收益评估.md](./08-量化收益评估.md) | 基于现网基线（输入 37K / 命中 25K / 66%）的收益估算与敏感性分析 |
| [上下文工程与KV-Cache优化.slides.html](./上下文工程与KV-Cache优化.slides.html) | 汇报用 HTML 幻灯片 v1（6 页，已被 v2 取代，留档） |
| [上下文工程与KV-Cache优化.v2.slides.html](./上下文工程与KV-Cache优化.v2.slides.html) | 汇报用 HTML 幻灯片 v2（7 页，已被 v3 取代，留档） |
| [上下文工程与KV-Cache优化.v3.slides.html](./上下文工程与KV-Cache优化.v3.slides.html) | 汇报用 HTML 幻灯片 v3（7 页，已被 v4 取代，留档） |
| [上下文工程与KV-Cache优化.v4.slides.html](./上下文工程与KV-Cache优化.v4.slides.html) | 汇报用 HTML 幻灯片 v4（7 页，已被 v5 取代，留档） |
| [上下文工程与KV-Cache优化.v5.slides.html](./上下文工程与KV-Cache优化.v5.slides.html) | 汇报用 HTML 幻灯片 v5（已被 v6 取代，留档） |
| [上下文工程与KV-Cache优化.v6.slides.html](./上下文工程与KV-Cache优化.v6.slides.html) | 汇报用 HTML 幻灯片 v6（存在版面溢出问题，已被 v7 取代，留档） |
| [上下文工程与KV-Cache优化.v7.slides.html](./上下文工程与KV-Cache优化.v7.slides.html) | 汇报用 HTML 幻灯片 v7（已被 v8 取代，留档） |
| [上下文工程与KV-Cache优化.v8.slides.html](./上下文工程与KV-Cache优化.v8.slides.html) | 汇报用 HTML 幻灯片 v8（基于 v7：术语规范 query级/Tools块、目标页标题"挑战 90%+ 命中率"、删输入输出比卡、附录 D 增补"为何非 100%"口径说明） |
| [上下文工程与KV-Cache优化.pptx](./上下文工程与KV-Cache优化.pptx) | 真实 PPT（浅色系，2 页：现状与问题 / 目标方案），由 [make_pptx.py](./make_pptx.py) 生成 |

## 背景共识

- KV cache 命中条件：**前缀逐 token 完全一致**，改动一个 token，其后全部失效。
- Agent loop 输入输出比悬殊（常见 100:1），缓存命中与否直接决定成本（约 10 倍差价）和 TTFT。
- 一切上下文组织决策，都要回答同一个问题：**这次改动会让缓存从哪个位置断掉。**
