# 和 Codex 里的 GPT-6 Astra 比

核对日 2026-09-23。API 价来自 [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra)。Codex / Work 的额度来自 [Managing usage with GPT-6 Astra in Work and Codex](https://help.openai.com/en/articles/20001516-managing-usage-with-gpt-6-astra-in-work-and-codex)。聊天里的 GPT-6 Pro 来自 [GPT-5.6 and GPT-6 Pro in ChatGPT](https://help.openai.com/en/articles/20001354-gpt-56-and-gpt-6-pro-in-chatgpt)。同一次调用的形状沿用 [02-输入输出为什么分开.md](./02-输入输出为什么分开.md)。

Astra 的输出价和未缓存输入价与 Fable 5.1 相同。更贵的是缓存读，以及输入超过 272K 时整次请求改价。

## API 单价

短上下文，每百万 token：

| | 未缓存输入 | 缓存读 | 缓存写 | 输出 |
| --- | --- | --- | --- | --- |
| GPT-6 Astra | $10 | $1.00 | $12.50 | $50 |
| Fable 5.1 | $10 | $0.25 | $12.50 | $50 |
| V4.1-Flash，非高峰 | $0.15 | $0.003 | 无单独写入费 | $0.60 |

缓存写是未缓存输入的 1.25 倍，和 Fable 的 5 分钟档同价。Batch 和 Flex 是标准价的一半。Fast 是适用价格的 2 倍。`reasoning.effort` 可以设 low、medium、high、xhigh、max。把 effort 调低会少花额度；Fable 的思考关不掉，只能调深浅。

输入 token 超过 272K 时，整次请求按长上下文计：输入和缓存 ×2，输出 ×1.5。不是只给超出的那一段加价。Fable 在 1M 窗口内不加这笔。仓库上下文堆过 272K 之后，Astra 的这一次会比短上下文的同形调用贵一截，Fable 的单价不变。

## 同一次调用

缓存里已有 10 万前缀，新输入 5 千，输出 1 万。这一次的输入远低于 272K，用短上下文价。

| | 这一次 |
| --- | --- |
| GPT-6 Astra | $0.65 |
| Fable 5.1 | $0.575 |
| V4.1-Flash，非高峰 | $0.007 |

差在缓存读：10 万 token，Astra 是 $0.10，Fable 是 $0.025。输出都是 $0.50，仍占金额的大部分。

15 次调用、第 1 次把 10 万前缀写入缓存、每次输出 1 万：Astra 是 $10.90，Fable 是 $9.85，Flash 非高峰是 $0.12。每次输出 3 万时，Astra 是 $25.90，Fable 是 $24.85。短上下文上，Astra 和 Fable 是同一档账单，Astra 略高。和 Flash 的差距大约 90 倍，原因和上一篇一样：输出单价差了大约两个数量级。

$200 现金、按这 15 次调用的短上下文形状：直接 API 的 Astra 大约 18 个任务，Fable 大约 20 个。Cursor Ultra 按 $400 含额度大约 40 个 Fable 任务。Flash 非高峰大约 1,660 个。

若一次请求的输入超过 272K，上面这张表不再适用。整段缓存、新输入和输出都进长上下文价，输出从 $50 变成 $75。Fable 没有对应的一档。

## Codex 订阅里的 Astra

Work 和 Codex 共用一份额度。本地消息数是估计，不是定额。实际消耗看任务长度、推理档和 Fast。五小时窗口和每周窗口可能同时存在，两边都有剩余才能继续。下表是每五小时的本地消息估计。

| 方案 | 月费 | Codex / Work 里的 Astra | 普通聊天里的 GPT-6 Pro（底层是 Astra） |
| --- | --- | --- | --- |
| Plus | $20 | 约 5–45 条 / 五小时 | 没有 |
| Pro 5x | $100 | 约 25–225 条 | 50 条 / 周，和 GPT-5.6 Sol Pro 共用 |
| Pro 20x | $200 | 约 100–900 条 | 200 条 / 周。另有 Sol Pro 每天 170 条，两个模型合计每天不超过 200 条 |

Codex CLI 要用 0.153.0 或更新。用 API key 跑 Codex 时按 API 标价另计，不扣这份订阅额度。云端任务和本地消息共用额度，云端任务用的是 GPT-5.6 Sol，往往比一条本地消息更费。

这和 Claude Code 的结构不一样。Claude Pro 的 $20 不含 Fable，Fable 从第一条起按 API 标价另付。Plus 的 $20 含一段 Codex / Work 里的 Astra。Max 的 Fable 最多占每周额度的 50%，token 数不公布。Codex 的估计是消息条数，同样折不成美元，不能和 Cursor 的 $400 标价额度比谁的 token 更多。

聊天里的 GPT-6 Pro 是另一本账。Plus 能在 Codex 里用 Astra，不能在普通聊天里用。Pro 的每周几十到两百条，和 Codex 的五小时窗口互不占用。

Cursor 这次打开的价目表没有 GPT-6 Astra 一行。Codex 的额度不能在 Cursor 里花，Cursor 的 Other Models 额度也不能折成 Astra token。

## 效果

编码 agent 指数（09-09，各自官方壳）：Astra + Codex 与 Fable 5.1 + Claude Code 都是 62。Astra max 大约每个编码任务 $7.09，大约比 Fable 便宜 40%。那是 Artificial Analysis 的任务成本，不是上面这张 $10.90 的示意调用。综合智力指数 v4.3 里，Astra 和 Fable 5.1 并列 53。Opus 5.5 后来的指数是 58，Terminal-Bench 4.0 与 Astra（xhigh）同为 59.6%。这些不是同一次评测。

短上下文、同形 token 时，Astra 的 API 账单略高于 Fable，不是更便宜的 Fable。Codex 订阅省钱的那一段，是 Plus / Pro 套餐里的消息额度；额度用完之后，边际价格回到和 Fable 同一档的标价，并且在 272K 以上整次加价。高量可重试的步骤仍然是 Flash 或 Luna，不是把 Astra 的 effort 拉到 max。
