# Claude Code、Cursor、直接 API：Fable 怎么收费

核对日 2026-09-23。订阅规则来自当天的 [Claude 价目](https://claude.com/pricing)、[Claude Fable models on your plan](https://support.claude.com/en/articles/15424964-claude-fable-5-on-your-plan)、[What is the Max plan?](https://support.claude.com/en/articles/11049741-what-is-the-max-plan)、[usage credits](https://support.claude.com/en/articles/12429409-manage-usage-credits-for-paid-claude-plans)、[Use Claude Code with your Pro or Max plan](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan)。Cursor 侧沿用 [02-输入输出为什么分开.md](./02-输入输出为什么分开.md)。

Fable 5.1 的 token 标价在三条路上是同一组数：输入 $10、5 分钟缓存写 $12.50、缓存读 $0.25、输出 $50，每百万 token。差别在「订阅费买到的那一段算不算 Fable」，以及超出之后是否回到这组标价。

## Claude Code 先看你怎么登录

Claude Code 本身不另卖一份 Fable 价目。登录方式决定账单：

| 登录 | Fable 5.1 怎么扣 |
| --- | --- |
| Pro / Max，用 `/login`，环境里没有 `ANTHROPIC_API_KEY` | 走订阅。网页、桌面、手机、Claude Code 抽同一个额度 |
| 设置了 `ANTHROPIC_API_KEY`，或改用 Console 额度 | 从第一个 token 起按 API 标价计。订阅里的额度不用。`/cost` 显示这一会话的美元 |

第二条很容易误触：本机留着 API key 时，Claude Code 不会去用你已经付过的 Pro / Max。

## 订阅里的 Fable

| 方案 | 月费 | Fable 5.1 |
| --- | --- | --- |
| Pro | $20；年付折合 $17（一次付 $200） | 不在套餐额度里。从第一条 Fable 消息起走 usage credits，按 API 标价另计 |
| Max 5x | $100 | 含在套餐里，最多用到每周额度的 50%。这 50% 不是加出来的容量，和 Opus、Sonnet、网页聊天共用同一条每周额度。Fable 比其他模型烧得快 |
| Max 20x | $200 | 与 Max 5x 同一套 Fable 规则。五小时窗口的用量是 Pro 的 20 倍，每周额度更高，具体 token 数不公布 |

额度有两层，都没有固定条数或固定 token：滚动的五小时窗口，加上每周上限。用完可以等重置，也可以打开 usage credits，按 API 标价继续。credits 与订阅分开出账。

Max 上的 Fable 用到每周额度的 50% 之后，两条路：继续用 Fable，改走 credits；或换 Opus / Sonnet，留在套餐额度里。Pro 没有「先用套餐里的 Fable」这一段。2026 年 7 月给 Pro 的一次性 Fable 5 额度不适用于 Fable 5.1。

Claude Code 里 Fable 5.1 需要 2.1.255 或更高版本。

## 和直接 API、和 Cursor 的差

| | Claude Code，Pro | Claude Code，Max 20x | Claude Code，API key / 直接 API | Cursor Ultra，模型选 Fable |
| --- | --- | --- | --- | --- |
| 先付 | $20 | $200 | 不先付。API 预存额度，一年有效，不退 | $200 |
| Fable 单价 | 套餐内没有。credits 即标价 | 套餐内那一段不按 token 计价；超出后 credits 即标价 | 从第一个 token 起就是标价 | 从第一个 token 起按标价扣额度 |
| 能白用的 Fable | 没有 | 每周额度的至多一半，且和聊天、Opus、Sonnet 抢同一条额度 | 没有 | 最后公开的 Other Models 额度是 $400 标价，可以全部花在 Fable 上。2026-09-23 的价目页已改成 Included，以 Spending 为准 |
| 超出之后 | 标价 | 标价 | 一直是标价 | 标价。个人方案不加价 |
| 批处理半价 | 交互式会话用不上 | 同左 | Batch API 可以 | 用不上 |
| 提示词谁决定长度 | Claude Code 的会话、`CLAUDE.md`、读过的文件 | 同左 | 调用方自己组 | Cursor 的规则、索引和工具定义 |

三笔账不要加在一起。在 Cursor 终端里跑 Claude Code、并用 Claude 账号登录，扣的是 Anthropic 的订阅或 credits，不扣 Cursor 的 Other Models。在 Cursor 里把模型选成 Fable，扣的是 Cursor。两套同时开，两套都扣。

## 哪一条更省

按 Fable 的标价用量看整月现金：

- **用量低于订阅费。** 直接 API 最低。Pro 的 $20 买不到 Fable 额度，Fable 仍按标价另付，等于 API 价再加 $20。Max 的 $100 / $200 只有在套餐内那一段 Fable 的标价高于月费时才划算；这段的 token 数 Anthropic 不公布，打满之前无法事先折成美元。
- **Max 的套餐内那一段。** 这是 Claude Code 相对 API 唯一的 Fable 补贴：月费封顶，直到五小时窗口、每周额度，或 Fable 的 50% 周帽先到。帽到了之后，边际 token 与直接 API 同价，月费照付。
- **Cursor Ultra，且第三方标价用量超过 $200。** 少付的是一笔固定的 $200（按 $400 含额度计算），见上一篇。这 $400 可以全部给 Fable。Max 不能把整个月的额度都给 Fable，最多一半，而且网页聊天也在扣同一条。
- **用量远超含额度。** 三条路的边际价格都回到 $10 / $50。直接 API 还能走 Batch 半价；Claude Code 和 Cursor 的交互会话走不到 Batch。

Pro 适合日常用 Sonnet / Opus 写代码，偶尔的 Fable 按 API 价另付。整天把 Fable 开在 Claude Code 里，Pro 不提供这段额度，要看 Max 的周帽够不够用；帽不够时，Cursor 的美元额度可以全部花在 Fable 上，直接 API 则没有月费地板。
