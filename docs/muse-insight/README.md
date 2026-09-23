# Meta Muse 洞察：个人 agent 为什么成立

2026-09-08 Meta 发布 Muse，定位是「给所有人的个人 agent」：每人一台云端电脑，在 App 或 WhatsApp 里像给人发消息一样把事交给它。两周内它冲上美国 App Store 免费榜前列。2026-09-22，Meta Superintelligence Labs 产品负责人 Nat Friedman 公开承认：产品形态「确实严重借鉴了 OpenClaw」，harness 从零写，但 `SOUL.md` 这类文件「Peter 做对了，所以我们照用」。

本目录回答三件事：它的势头来自哪里、和 OpenClaw 到底同在哪一层、以及它和现有 work agent / code agent 不是同一物种。对照对象包括本仓库的 [openclaw-automation/](../openclaw-automation/) 与 [phone-assistant-automation/](../phone-assistant-automation/)。

一手材料（核对日期 2026-09-23）：

- Meta News《Introducing Muse》（2026-09-08）
- Mona Sarantakos / Christine Awad《How We Designed Muse》（introducing.muse.ai，2026-09）
- Tarek Sheasha《How We Built Safety Into Muse》（research.meta.ai，2026-09-08）
- 《Introducing Muse Spark 1.3》（2026-09-02）与开发者模型页
- Nat Friedman 对 OpenClaw 相似性的回应，TechCrunch 2026-09-22 引述
- OpenClaw 官方概念文档：architecture、agent loop、workspace、system prompt（docs.openclaw.ai）
- RuntimeWire 五产品同题 bake-off（2026-09-16，Muse 在 muse.ai）
- Sensor Tower 下载口径，经 Mashable 2026-09 转述

## 目录

| 文档 | 内容 |
| --- | --- |
| [Muse深度洞察.slides.v1.html](./Muse深度洞察.slides.v1.html) | **汇报版式 8 页**（浅色 16:9，← → 翻页，`#p=N`）。P1 两张成绩单 → P2 两安全域 → P3 秘密 / 出网 / 浏览 / 付款 → P4 Spark 是居民不是冠军 → P5 对照 OpenClaw → P6 仓库 / 工单 / 生活 → P7 商业：卖零配置信任 → P8 抄围墙不抄下载。三视口校验通过。底稿是同目录四篇 |
| [01-它做成了什么.md](./01-它做成了什么.md) | 先拆开「成功」：装机与任务完成是两个数。产品是什么、五件真正做成的事、安全计算机为什么是主体工程、模型处在哪一层、还没做成的 |
| [02-和OpenClaw.md](./02-和OpenClaw.md) | 同一套产品直觉、被原样拿走的文件契约、被重写的盒子。对照表：谁运维、模型、通道、记忆、权限、扩展、自动化、计算机在谁那里 |
| [03-和工作agent与code-agent.md](./03-和工作agent与code-agent.md) | 三种物种（仓库 / 工单 / 生活）。目标函数、计算机、记忆、主动性、同意、扩展、失败模式。Muse Code 是 code agent，不是 Muse |
| [04-对我们系统的启示.md](./04-对我们系统的启示.md) | 已被双脑、打扰管理器、openClaw v4 印证的判断；权限计算机、凭证替身、两条车道、冷启动；不要抄的部分；两套分开的度量 |

## 一句话共识

Muse 的势头不是模型榜第一名换来的。OpenClaw 已经证明「一个人一台会持续做事的电脑、用文件当记忆、在聊天里说话」这个形态有人爱用；Meta 把**运维和权限从用户手里拿走**，做成零配置、可解释的安全计算机，再放进 WhatsApp 和已有的生活图谱里。任务可靠性在发布两周时仍然落后于更窄的 work agent。装机成功和把事做对，是两张成绩单。
