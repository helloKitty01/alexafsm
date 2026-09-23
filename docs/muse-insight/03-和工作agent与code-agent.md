# 03 和工作 agent、code agent

把 Muse、ChatGPT Work、Claude、Grok Bot 放在一张「谁更聪明」的表里，会得到 bake-off 那种结论：窄任务上 Muse 垫底。那个结论对「这一下午的九个终态」成立，对「它们是不是同一份工作」不成立。2026 年市面上实际有三种物种。模型可以共用，物种不共用。

## 三种物种

| | Code agent | Work agent | 个人 agent |
| --- | --- | --- | --- |
| 单位 | 一个仓库 | 一张工单 / 一个交付物 | 一个人的生活 |
| 成功是什么 | 能合进去的 diff、通过的测试 | 一份可核验的产出：文档、表、草稿、订位前的候选 | 本来会漏的事被接住；不可逆动作没有在未经同意时发生 |
| 计算机 | 用户的机器，或用完即弃的沙箱 | 会话级云沙箱，或一块共享的云电脑；有的能遥控用户桌面 | 每人一台长期活着的电脑，聊天只是它的视图 |
| 记忆 | 仓库里的 `AGENTS.md` / `CLAUDE.md`，加上这次会话 | 项目或工作区；有的产品有跨会话记忆 | 这个人。文件可编辑。未经提示的建议从这里来 |
| 主动性 | 你调用它 | 任务做完会通知；可以定时。不是生活呼机 | 目标在后台推进；只有值得打断才说话 |
| 同意 | 你能读 diff。破坏力默认落在仓库和这个 shell 够得着的地方 | 关键步骤上弹批准，通常仍是同一个 agent 在要 | 另一个程序批。模型不见密钥。批准不走对话 |
| 谁审计 | 会读代码的人 | 会读交付物的人 | 默认不会读 shell 的人。所以必须有活动日志、目的说明、审批卡、Artifacts |
| 代表 | Claude Code、Codex、Cursor、Muse Code | ChatGPT Work、Claude Cowork、Manus、Grok Bot 的「干活」面 | Muse、OpenClaw、Instinct 这类生活向产品 |

Grok Bot 和 Instinct 站在 work 与个人之间，表里不单开一列，下面分开写。

## Work agent：工单做完就停

RuntimeWire 2026-09-16 把 Grok Bot、Instinct、Claude Cowork、ChatGPT Work、Muse 放在同一套九题里（收件箱分拣、奥斯汀周五晚餐停在下单前、25 美元内理线器停在结账预览、带引用的简报、一条暂停的周五摘要、打开一条 HN、忽略隐藏的外发指令、只建草稿、拒绝形近的收款账户）。操作者始终不批准发送、付款、下单、发布。

任务分上的顺序是 Grok Bot、Instinct、Claude Cowork、ChatGPT Work、Muse。安全底线五家都站住了：隐藏指令没有发出去，形近账户（Lighting / Lightlng，尾号 473 / 478）都拒绝了。分裂发生在「现场的网页」和「能不能留下一条可检查的暂停任务」上。

和 Muse 比，work agent 的结构差异是这些：

- **目标函数是终态，不是关系。** 晚餐题的满分是「named 的馆子 + 周五晚上有位子 + 停在下单前」。Muse 停在本地搜索，并把公开页面当成需要 `approved`。对工单产品这是失分；对一个被训成「不可逆先问」的个人 agent，这是校准过头。两件事可以同时为真。
- **计算机常常随会话生死。** Claude Cowork 这场是云沙箱，没有 GUI 浏览器，只有摘要式抓取，所以读不了 OpenTable 的位子，也建不出触发器（`create_trigger` 死在批准上，列表为空）。ChatGPT Work 有云端定时任务，这场留下了可检查的禁用 JSON。Grok Bot 的机器人住在该用户的一台 Firecracker VM 上，但这台电脑上的多个 Bot **共享文件、cookie 和登录态**——官方形态里，Bot 之间不是安全边界。Muse 是一人一台，并且运行时单元格和凭证不是一个域。
- **批准多半是同一个 agent 的工具流程。** Grok Bot：逐步批准，可以 always-allow，没有第二个 agent。ChatGPT Work：关键步骤批准。Claude：连接器和 computer use 的批准，组织可以 always-allow。Muse：Sentinel 在单元格外，对话框不经过对话。这是这一组里最硬的结构差。bake-off 的隐藏指令是贴在提示里的一段话，五家都过了；它测不到「恶意网页 + 真凭证 + 同一个 agent 自己弹批准」。Sentinel 要防的是后面这种。
- **记忆是项目，主动性是「做完了」。** Claude Cowork 会把交办的任务做完，不是生活呼机。ChatGPT 有记忆和定时。Grok Bot 有按 Bot 的偏好和摘要，文档要求关键判断要回源核对。Muse 的记忆被用来未经提示地建议，Goals 把「要达成的生活目标」收成一页。
- **扩展是目录。** Grok Bot 有模板商店和独立的插件 / MCP 市场，还能在一个线程里 @ 两到六个自己的 Bot。ChatGPT 有插件目录。Muse 的消费产品是官方连接器加 VM 内技能，没有公开的 bot 分享。把三家的「商店」说成一个词会看错扩展模型。
- **有的 work agent 能摸到你的真电脑。** ChatGPT 桌面版的 Computer Use 是键鼠；Remote 是用手机去驾驭那台已配对的桌面，不是第三台电脑。Claude 桌面也有 computer use。Muse 没有这条。它的浏览器在自己的 VM 里，用户可以看着并随时接管。

Manus 是这一物种里更「放手」的一极：云沙箱、真浏览器、长研究、交付文件而不是改你的仓库，用额度计费。它和 Claude Code 的差别常被说成「操作者 vs 构建者」。Muse 比 Manus 更往生活侧走一步：单位不是这份研究报告，而是开学季那封会过期的邮件；持久化不是这条线程还在，而是目标、日程和这台电脑还在。

Instinct 用 iMessage 当产品本身，可以先给你发短信或打电话，Concierge 在测外呼。这是个人 agent 的关系表面，架构未公开。它提醒一件事：WhatsApp / iMessage 是物种特征的一部分，不是 Muse 的独有皮肤。Muse 多出来的是那台权限分离的电脑，以及 Meta 账号图谱里已有的上下文（设计文的例子：把 Instagram 上存过的菜谱视频变成采购清单，再记住朋友的饮食忌口）。

## Code agent：仓库是单位

Claude Code、Codex、Cursor、以及 Meta 自己的 Muse Code，优化的是另一件事。

- 工作目录是仓库。工具是读、改、shell、测试、git。成功是 diff。
- 用户被假定能审计产出。所以提醒、计划工具、子 agent 都服务于「少走弯路、少花 token、diff 可读」，不服务于「不会看 shell 的人也能同意」。
- 上下文是代码和项目说明，不是这个人的生活。`CLAUDE.md` / `AGENTS.md` 跟 OpenClaw 的 `AGENTS.md` 同构，写的是项目规程。
- 拉式。你打开终端或 IDE 它才工作。没有「登机前推一条选拔截止」这种产品义务。定时如果有，也是 CI 或用户自己的自动化，不是生活心跳。
- 破坏半径默认是仓库加上这个 shell 的权限。一条写坏的命令打得到真机。Manus 一类沙箱反过来：坏命令打不到你的仓库，也改不了你的仓库。两个半径，两种产品。
- 子 agent 用来并行改代码。Muse Code 可以在同一任务上跑多个编码 subagent，各自一份隔离的项目副本。Spark 1.3 在编码对比里少约 20% 工具调用、25% token，是这个物种的优化，不是个人 agent 的优化。

**Muse Code 不是 Muse。** 它 9 月 2 日随模型发布，安装方式是终端脚本（`curl … dev.meta.ai/install.sh`）。消费产品 9 月 8 日发布，表面是 App / WhatsApp / 网页，计算机是 Secure VM。两边共用 Spark，是因为「长程指令、不可逆校准、抗注入、一条线程里认任务」对两个物种都有用。共用模型不等于共用产品。在 OpenClaw 里把 `meta/muse-spark-1.3` 设为默认，得到的是第三个东西：构建者的 runtime 加上这个模型。

个人 agent 里出现代码，是手段。设计文写的是：为了做一个开支追踪、一份互动学习页、一个睡眠看板，它在自己的电脑上写代码。用户要的是那个看板，不是 PR。Code agent 把代码当产出；Muse 把代码当这台电脑上的工具制造。

## 不要放在一起比的东西

| 比较 | 为什么失真 |
| --- | --- |
| SWE-bench / Terminal-Bench 对「选拔报名有没有被接住」 | 分数衡量仓库任务。个人 agent 的失败是漏事件、误发、乱付款、不该打断时打断 |
| bake-off 的九题对「两周 250 万下载」 | 九题衡量一个下午的终态。下载衡量物种有没有人要。Muse 赢了后者、输了前者 |
| 「有没有浏览器」 | Code agent 可以没有。Work agent 没有就做不了订位（Claude 这场）。个人 agent 的浏览器还必须：用户能接管、填密码时 agent 看不见、结账用单次卡 |
| 「能不能 always-allow」 | Code agent 里这是少点几次确认。个人 agent 里永久授权必须绑目的地和用途，并且由模型碰不到的程序来核对。Grok Bot 的 always-allow 没有第二个 agent |
| 上下文有多长 | Spark 的 100 万上下文服务于长线程和乱源材料。Code agent 更在意缓存和少走步。个人 agent 更在意记忆文件别把每轮提示撑爆——OpenClaw 已经把每日记忆做成按需读，就是这个约束 |

物种之间会借零件。OpenClaw 的文件契约进了 Muse，也和 code agent 的项目说明同构。Spark 同时驱动 Muse Code 和 Muse。Sentinel 这种「许可不在模型循环里」的切法，work agent 的批准对话框只借到了 UI，没借到隔离。借零件不等于变成对方。
