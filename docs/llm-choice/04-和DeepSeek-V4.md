# 和 DeepSeek V4 比

核对日 2026-09-23。单价来自当天的 [DeepSeek Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing)。效果和速度沿用 [2026-09-23-模型与agent怎么选.md](./2026-09-23-模型与agent怎么选.md) 里的 Artificial Analysis 数字，并对照 [Flash 与 Opus 5 的对照页](https://artificialanalysis.ai/models/comparisons/deepseek-v4-1-flash-vs-claude-opus-5)。Fable 的一次调用沿用 [02-输入输出为什么分开.md](./02-输入输出为什么分开.md)。

现在 API 上有两个 V4 型号。`deepseek-flash` 是 DeepSeek-V4.1-Flash。`deepseek-v4-pro` 在价目页上仍是 DeepSeek-V4-Pro-0813，按 Pro 的价计。9 月 10 日的发布说明写过 9 月 14 日起把 Pro 请求改路由到 Flash；今天的价目页没有改成那样。要 V4.1-Flash 的价，模型名用 `deepseek-flash`。

## 单价

每百万 token。没有单独的缓存写入费。命中缓存按 cache hit，未命中按 cache miss。高峰是非高峰的 2 倍。

| | 缓存命中 | 缓存未命中 | 输出 |
| --- | --- | --- | --- |
| V4.1-Flash，非高峰 | $0.003 | $0.15 | $0.60 |
| V4.1-Flash，高峰 | $0.006 | $0.30 | $1.20 |
| V4-Pro，非高峰 | $0.022 | $0.66 | $1.98 |
| V4-Pro，高峰 | $0.044 | $1.32 | $3.96 |
| Fable 5.1 | 缓存读 $0.25 | 输入 $10，缓存写 $12.50 | $50 |

高峰是周一到周五的两段，UTC 01:00–04:00 和 06:00–10:00，中国法定假日除外。对应北京时间工作日 09:00–12:00 和 14:00–18:00。午间、晚间、周末和法定假日全天都是非高峰。

Flash 的输出价相对 Fable：非高峰大约 1/83（$0.60 对 $50），高峰大约 1/42。缓存命中的比例几乎一样（$0.003 对 $0.25）。V4-Pro 非高峰的输出价大约是 Fable 的 1/25。

没有月费，没有每周 50% 的帽，也没有 Cursor 那种「订阅费低于额度面值」的补贴。用多少扣多少，从预存余额里扣。Flash 并发上限 2500，Pro 是 500。上下文 1M，最大输出 384K。思考模式默认开着，可以关掉；Fable 5.1 的思考关不掉。Flash 有视觉输入，V4-Pro 价目页写着不支持视觉。权重是 MIT。

## 同一次调用差多少钱

沿用上一篇的形状：缓存里已有 10 万前缀，新输入 5 千，输出 1 万。

| | 这一次调用 |
| --- | --- |
| Fable 5.1 | $0.575 |
| V4.1-Flash，非高峰 | $0.007 |
| V4.1-Flash，高峰 | $0.014 |
| V4-Pro，非高峰 | $0.025 |

15 次调用、第 1 次前缀未进缓存、每次输出 1 万：Fable 是 $9.85，Flash 非高峰是 $0.12，高峰是 $0.24。每次输出 3 万时，Fable 是 $24.85，Flash 非高峰是 $0.30。金额差大约 80 倍，因为两边都是输出占账单的绝大部分，而输出单价差就是这 80 倍。把 Flash 的思考关掉，输出更短，差距还会加大。Fable 没有这个开关。

$200 现金、按这个 15 次调用的形状：直接 API 的 Fable 大约 20 个任务；Cursor Ultra 按 $400 含额度大约 40 个任务；Flash 非高峰大约 1,660 个任务，高峰大约 830 个。Max 20x 的 $200 买的是不公开 token 数的周额度，而且 Fable 最多占其中一半，折不成同一行。

## 和三条 Fable 通路的差别

| | DeepSeek API | Claude Code 订阅 | Cursor Ultra | 直接调 Fable |
| --- | --- | --- | --- | --- |
| 模型 | V4.1-Flash 或 V4-Pro | 套餐里的是 Claude 模型。额度不能拿去调 DeepSeek | 价目表里的第三方模型，不含 DeepSeek | Fable 5.1 |
| 先付 | 无 | Pro $20 或 Max $100 / $200 | $200 | 无 |
| 超出或日常 | 一直按上表 | Fable 在 Pro 上从第一条按标价；Max 在周帽内不按 token 计 | 额度内按 Fable 标价扣，超出后仍是标价 | 一直是 Fable 标价 |
| 批处理半价 | 无这一档。非高峰已经是高峰的一半 | 交互会话用不上 | 用不上 | Batch 可以 |

DeepSeek 有 Anthropic 兼容地址 `https://api.deepseek.com/anthropic`。把 Claude Code 的请求指到这个地址、并用 DeepSeek 的 key，扣的是 DeepSeek 余额。Claude 的 Pro / Max 额度不会因此被消耗，也不会因此打折。Cursor 的 $400 额度同样不能折成 DeepSeek token。

## 效果不跟着价走

Artificial Analysis 上 V4.1-Flash（max）的综合智力指数是 40。同一站点把它和 Opus 5（max）放在一起时，是 40 对 51，Terminal-Bench 4.0 是 27% 对 49%。Opus 5.5 后来的指数是 58，Terminal-Bench 4.0 是 59.6%。这些数字不是同一次评测，不能排成一张总榜。能确定的是：Flash 在这套指数里不是 Fable / Opus 那一档。

速度相反。同一对照页上 Flash 约 220 token/s，首 token 约 1.1 秒；Opus 5 约 53 token/s，首 token 约 53 秒。Anthropic 给 Fable 5.1 的延迟档是「更慢」。

DeepSeek 自己的模型卡在 Terminal-Bench 2.1、DeepSWE 上给出更高的分数，并且写明换 harness 会掉一截：DeepSWE 在 mini-SWE 上 74.2，在 Claude Code 上 69.8。那是另一套题、另一套壳，不能拿来覆盖 Terminal-Bench 4.0 的 27%。

高量、可重试、能接受指数 40 这一档的步骤，用 Flash，尽量放在北京时间的非高峰。最难的一轮仍是 Fable 或 Opus 5.5 的价和效果。DeepSeek 没有把 Fable 的三条通路变成半价，它是另一个模型。
