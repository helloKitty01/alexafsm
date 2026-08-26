# Reminder 机制（内部代号：notion 方案）讨论

这是一个讨论用目录，用于沉淀关于 agent 系统 **reminder 机制**（运行期动态注入
提醒/状态块）的业界洞察与设计讨论。内容随讨论持续迭代。

与 [kv-cache-discussion/](../kv-cache-discussion/) 强相关：reminder 机制正是
那边"通道一：被动注入"的业界成熟形态，且天然满足缓存友好排布原则。

## 目录

| 文档 | 内容 |
| --- | --- |
| [01-业界方案盘点.md](./01-业界方案盘点.md) | Claude Code system-reminder、Manus recitation、Anthropic 官方模式的方案与使用方式 |
| [02-作用机理与解决的问题.md](./02-作用机理与解决的问题.md) | reminder 为什么有效：注意力几何、context rot、状态同步、缓存经济 |
| [03-对我们系统的启示.md](./03-对我们系统的启示.md) | 落地设计建议、与渐进式加载的配合、待讨论取舍 |
| [reminder机制.slides.html](./reminder机制.slides.html) | 2 页幻灯片（浅色系）：P1 业界洞察 + 注入位置；P2 两个内部实践（tool result 隐私字段屏蔽、随 User 注入时间/前台应用） |
| [reminder机制.pptx](./reminder机制.pptx) | 同内容的真实 PPT 文件（浅色系，16:9，2 页），由 [make_pptx.py](./make_pptx.py) 生成 |

## 一句话共识

reminder 是 agent 的**二级指令通道**：system prompt 负责"我是谁、规则是什么"
（占据 primacy 位置，产品级静态），reminder 负责"此刻你需要知道什么"
（占据 recency 位置，事件触发、短小、append-only）。
