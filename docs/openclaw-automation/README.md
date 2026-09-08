# openClaw 自动化任务：定时 + 事件订阅整体方案

从"每天早上 9 点帮我干 xxx"出发，把 openClaw 的定时任务能力扩展到事件驱动的自动化
（明天下雨 / 到家 / 收到某人电话 / 火车放票抢票）。
前提假设：存在一个统一事件管理服务（EMS），订阅即推送，不区分手机平台。

## 目录

| 文件 | 内容 |
| --- | --- |
| [openClaw自动化任务方案.slides.v0.1.html](./openClaw自动化任务方案.slides.v0.1.html) | **整体方案幻灯片（当前版本 v0.1，11 页）**：目标与五场景归类 → openClaw 定时任务现状盘点（Gateway 内 cron、三种调度、三种 payload、交付、heartbeat 定位）→ session 四选一与默认 isolated → 事件驱动能力边界（openClaw 无订阅原语、EMS 承担 / 不承担、我们补什么）→ 整体架构（一张 Task 表、两个触发引擎、`/hooks/events` 入口、wake / agent / command 三分支）→ 与 EMS 的订阅 / 推送契约与投递语义（at-least-once + 去重 + 双侧过期）→ 七步编译流程 → 派生事件 checker 路 A / 路 B 与抢票特例 → 工具合一（`create_task` trigger 判别联合、九件工具、`subscribe_event` 并入、openClaw cron 工具对模型隐藏）→ 五场景全表 → 可靠性清单、开放问题与下一步 |

## 核心结论（v0.1）

1. **一张 Task 表统一时间型 / 事件型 / 轮询型任务**：时间型复用 openClaw cron，事件型走 EMS 订阅，
   轮询型 = command cron checker 产生派生事件；模型只面对 `create_task` 一个入口，底层路由由代码完成。
2. **触发不过模型，执行才过**：触发器全部非 LLM、零 token；LLM 只在创建时编译、触发后执行两个时刻介入。
3. **默认 isolated session**：省 token、防 context bleed、权限隔离；需要记忆用 `session:<task_id>`，纯提醒才进主 session。
4. **投递语义**：EMS at-least-once + 入口层 `event_id` 去重（24h）+ 双侧 `stale_after` 过期校验；入口先回 200 再执行。
5. **高危动作永不走默认路径**：支付 / 对外发送 / 删除必确认；抢票放票瞬间全程 command，脚本最多锁单，然后唤醒主 session 找用户付款。

## 开放问题

- EMS 是否有 publish 接口（决定派生事件走路 A 还是路 B）。
- Task 表 + 入口层放独立服务还是 openClaw plugin。
- 抢票边界（倾向候补优先 + 支付永不自动）。
