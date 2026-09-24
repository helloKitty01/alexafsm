# Jev 洞察：一个不写字的模型为什么这一周这么火

2026-09-15，TypeSafe AI 结束隐身，发布第一款 System One 模型 Jev。它不生成句子。程序把一段状态和一组事先写好的问题送进去，它并行返回选择、分数或是非概率。发布后几天，Vercel AI Gateway、AI SDK 的 `evaluate`，以及 LangChain / LangSmith 都接上了。多家报道引 Vercel 的说法：上线 24 小时内，近 13% 的付费团队用过它，快过该网关以往任何模型。

本目录回答三件事：这股热度量的是什么、模型实际交出的是哪种函数、以及它和本仓库的手机助手 / OpenClaw 自动化该怎么接。对照对象是 [phone-assistant-automation/](../../../phone-assistant-automation/)、[openclaw-automation/](../../../openclaw-automation/) 和 [llm-choice/](../../../llm-choice/) 里已经写过的「输出比输入贵」这件事。

一手材料（核对日期 2026-09-24）：

- Diogo Almeida《Introducing System One Models & Jev》（typesafe.ai，2026-09-15）
- TypeSafe 文档：Models、Jev 1.13 jaggedness（页面写明最后审阅 2026-09-17）、Confidence、System One
- Business Wire，种子轮公告（2026-09-15）
- Vercel Changelog《TypeSafe AI's Jev now available on AI Gateway》（2026-09-16，Rohan Taneja、Zachary Chen、Jerilyn Zheng）
- LangChain《Jev-as-a-Judge for Agent Evals》（2026-09-20，Daniel Shea、Seán Roche）
- The New Stack 对 Vercel 采用率原文的引述（Vercel 博客猜测地址返回 404，13% 按引述使用）

## 目录

| 文档 | 内容 |
| --- | --- |
| [01-它为什么在这一周火.md](./01-它为什么在这一周火.md) | 热度的三层：分发入口、单价和延迟、一句能转述的故事。13% 量的是免费窗口里的付费团队有没有打过一次 |
| [02-决策函数不是聊天模型.md](./02-决策函数不是聊天模型.md) | 三种问题、并行采样、输出免费的成本结构、「不能幻觉」在官方文本里实际保证的是类型 |
| [03-哪些数字不能加在一起.md](./03-哪些数字不能加在一起.md) | 193 倍和 444 倍的口径、LangChain 的 5 条天气轨迹、官方自己列出的九类翻车、定价可能被补贴 |
| [04-对我们系统的启示.md](./04-对我们系统的启示.md) | 打扰分级、模板选择、轨迹验收可以交给它；钱 / 发送 / 删除、中文口语、计数和日期仍留在代码和 `waiting_user` |

## 一句话共识

Jev 火，是因为 2026 年的 agent 账单已经证明：大量步骤只是封闭判断，却在用自回归模型一个词一个词地写出来。它把输出侧的生成拿掉，换成类型和概率，再从 Vercel 的免费窗口灌进现成的工作流。这是接口和成本结构的成功。判断仍会错，对抗文本仍能推动答案，中文还要单独测。它适合当中枢旁边的快裁判，不适合当会写字的执行者，也不适合凭高置信度放行不可逆动作。
