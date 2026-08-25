# 09 业界 Agent Harness 的 KV Cache 优化实践洞察

调研时间 2026-08。信息来源：Manus 官方博客、Anthropic 官方工程博客
（Claude Code / Advanced Tool Use）、Claude Code 逆向分析资料、
Mooncake（Kimi）论文与开源文档、vLLM/SGLang 集成文档。

## 0. 业界共识总览

所有做得好的 agent harness，缓存优化都落在**三个层面**，缺一不可：

| 层面 | 核心手段 | 代表 |
| --- | --- | --- |
| 上下文排布 | 稳定前缀、append-only、确定性序列化 | Manus、Claude Code |
| 压缩与工具管线 | 缓存安全的压缩、工具延迟加载、渐进式多级压缩 | Claude Code、Anthropic 平台 |
| 推理系统 | 分布式 KV 池、多级存储、跨实例前缀共享 | Mooncake（Kimi）、LMCache、SGLang HiCache |

我们方案（01–08）主要覆盖第一层和第二层的一部分；本篇重点提取
**业界已验证、我们尚未覆盖**的增量做法。

## 1. Manus：把 KV 命中率当北极星指标

- **"KV-cache 命中率是生产 agent 唯一最重要的指标"**——直接影响成本
  （10 倍价差）与 TTFT；输入输出比 ~100:1，成本几乎全在 prefill。
- 三条铁律与我们方案完全一致：前缀稳定（系统提示里不放秒级时间戳）、
  append-only（不改历史动作/观察）、确定性序列化（JSON 键序不稳定
  是"无声的缓存杀手"）。
- **Mask, don't remove**：工具定义全集常驻稳定前缀，用
  **logit masking**（decode 时屏蔽 token 分布）按状态约束可选动作，
  而非增删工具。配套设计：**工具名统一前缀分组**（`browser_*`、
  `shell_*`、`file_*`），一个前缀 mask 即可约束一族工具，
  无需有状态的 logits processor。
- 文件系统即外部记忆：大观察结果落盘、上下文留路径（可恢复压缩），
  与我们 03/05 的指针化一致。

**对我们的启示**：skill / 工具命名建立前缀分组规范（如 `deploy_*`、
`search_*`），为将来自建集群上做 logit masking 或分组约束留好接口。

## 2. Claude Code：工程化最深的参照系

### 2.1 提示装配顺序（与我们的 L0/L1/UAT 同构）

按稳定度严格排序：全局静态（system prompt + 核心工具）→ 项目级
（CLAUDE.md / 规则文件）→ 消息流（每轮变化，放最后）。
易变状态（system reminders）以**消息流内标签**注入，绝不改 system
prompt——与我们 turn_context 随 U 注入完全同构。

### 2.2 全局共享前缀段（SYSTEM_PROMPT_DYNAMIC_BOUNDARY）

system prompt 用一个哨兵串切成两半：边界前是**全球所有用户相同**的
核心指令/工具描述/安全规则，以 `scope: global` 全局缓存——数百万用户
共享同一份前缀 KV；边界后才是用户级配置。
代价是运营纪律：**边界前改一个字节，全网所有用户的缓存同时失效**。
为此 Claude Code 做了 "sticky beta headers"：会话内 header 一旦发出
就锁定不变，即使功能开关中途变化，宁可牺牲灵活性也要保住缓存。

**对我们的启示**：L0（产品级原则 + 工具全集）的变更要有**发布管控**
——版本化、择时发布、会话内锁定版本（会话中途不升级 L0），
避免一次文案微调打掉全网缓存。

### 2.3 Tool Search / defer_loading（我们方案 B 的官方版本）

- 工具全集随请求发给 API，但标 `defer_loading: true` 的**不进上下文前缀**；
  模型通过 tool search 按需发现，API 把命中的工具以 `tool_reference`
  块**内联追加进消息流**再展开——**前缀不动，缓存保留**。
- 效果：5 个 MCP server 场景从 ~77K token 降到 ~8.7K（-85%）；
  且工具超过 30–50 个后选择准确率退化，按需加载反而**提升准确率**
  （Opus 在 MCP 评测从 49% → 74%，官方数据）。
- 这正是我们方案 B（search 工具化）的平台级实现；**GLM 5.2 模板原生
  支持 defer_loading**（见 06），等于我们可以低成本对齐这套机制。
- 配套的 **Programmatic Tool Calling**：让模型在代码执行环境里调工具，
  中间结果留在执行环境、不进模型上下文——"工具输出不进上下文"的极致。

### 2.4 压缩：五级渐进管线 + 缓存安全分叉（最重要的增量借鉴）

- **渐进式压缩**：cheapest first——先做便宜的（清理/驱逐单个过期大
  tool result，"microcompact"），最后才做贵的全量摘要（"compact"）。
- **microcompact 双路径按缓存状态选择**：缓存还热时，不重写本地消息，
  而是发 `cache_edits` 让**服务端驱逐指定的旧 tool result**（应用层
  参与缓存管理）；缓存已冷时才走本地重写路径。两条路径互斥。
- **缓存安全分叉（cache-safe forking）**——最关键的一条：
  压缩需要把全量对话发给模型写摘要。**天真做法**是另起一个
  "请总结"的独立请求（不同 system prompt、无工具）→ 前缀从第一个
  token 就分叉，**整个长对话按全价重付一遍**，且对话越长（越需要压缩）
  这一刀越贵。**Claude Code 的做法**：压缩请求使用与主会话完全相同的
  system prompt、工具定义与历史消息，只在末尾追加一条"请总结"的
  user message——对 API 而言这就是主会话的又一轮请求，
  **前缀全部命中，摘要调用只为压缩指令本身付费**。
  配套要求：预留 "compaction buffer"（给压缩指令+摘要输出留窗口空间）。
- `cache_reference`：落在缓存前缀内的旧 tool result 标注引用 ID，
  服务端直接复用缓存表示、跳过重编码。

**对我们的启示（按优先级）**：

1. **摘要调用必须缓存安全分叉**——我们 03/07 只算了压缩后的重建成本，
   **漏算了摘要调用本身**：60K 上下文按全价发一次 ≈ 多付 54K 等效 token，
   把压缩的回本周期拉长一倍以上。裁剪改造（落地路径②）实现时，
   摘要请求必须复用主会话前缀（同 system+tools+历史+追加总结指令）。
2. 裁剪分级化：先指针化/驱逐个别大 T（对应我们的指针化表），
   到水位才全量摘要——与我们双水位设计兼容，作为水位间的轻量级手段。
3. 自建集群可实现 `cache_edits` 等价物：调度层通知引擎驱逐指定 block，
   或至少在应用层记录"哪些 T 已淘汰"，与引擎的 prefix cache 语义对齐。

### 2.5 断点与 TTL

4 个 cache_control 断点：工具区末尾、system 末尾、L1 类内容末尾、
对话尾部滚动（自动滑动）。TTL 5 分钟（可选 1 小时）：loop 内迭代
天然在窗口内；**危险区是用户两次 query 之间的长间隔**——与我们
P6/附录 C 的判断一致。

## 3. 推理系统侧：Mooncake（Kimi）与多级 KV 存储

自建集群最直接的参照是 **Mooncake**（Kimi 的服务平台，已开源）：

- **KVCache 中心化的分离架构**：prefill/decode 集群分离；把 GPU 集群里
  闲置的 CPU、DRAM、SSD、NIC 池化成**分布式 KVCache 池**，
  全局调度器围绕缓存复用做请求路由。
- 实测：真实 trace 下有效请求容量 +59%~498%；线上数千节点、
  日处理千亿级 token。
- 生态集成已成熟：vLLM `MooncakeStoreConnector`（跨实例前缀共享 +
  CPU/盘 offload）、SGLang **HiCache**（RadixAttention 扩展为
  device/host/remote 三级 KV 存储）、LMCache 联合方案。
- 工程细节（易踩坑）：跨进程共享缓存要求 block hash 一致，
  **必须固定 `PYTHONHASHSEED`**，否则相同 prompt 在不同进程算出
  不同 hash，跨实例命中悄悄归零。

**对我们的启示**：附录 C 的"参考方向"可以具体化为演进路线——
第一步会话亲和路由（最便宜）；第二步单实例 CPU offload
（HiCache L2 / vLLM offload）扩驻留容量；第三步跨实例分布式 KV 池
（Mooncake Store / LMCache），亲和路由退化为软约束。
我们对集群的"诉求一"（会话存续期不逐出）在 Mooncake 架构下
即"KV 池容量 + 缓存感知调度"，是被 Kimi 线上验证过的成熟形态。

## 4. 借鉴清单：对照我们的方案

| 业界实践 | 出处 | 我们的现状 | 动作 |
| --- | --- | --- | --- |
| 稳定前缀/append-only/确定性序列化 | Manus | 已覆盖（02/05） | 无 |
| 易变状态以消息流标签注入 | Claude Code | 已覆盖（turn_context） | 无 |
| 工具延迟加载 + search 按需发现 | Anthropic Tool Search | 方案 B 设计中 | GLM 5.2 defer_loading 对齐实现 |
| **摘要调用缓存安全分叉** | Claude Code | **未覆盖（漏算项）** | **纳入裁剪改造②的实现要求** |
| 渐进式多级压缩（cheapest first） | Claude Code | 部分（指针化表） | 双水位间加轻量级 microcompact |
| 应用层参与缓存驱逐（cache_edits） | Claude Code | 未覆盖 | 自建集群评估等价实现 |
| 工具名前缀分组 + logit masking | Manus | 未覆盖 | skill/工具命名规范先行 |
| 大结果不进上下文（Programmatic Tool Calling / 文件系统记忆） | Anthropic / Manus | 部分（落盘指针） | 评估代码执行环境形态 |
| L0 全局段发布管控 + 会话内版本锁定 | Claude Code | 未覆盖 | L0 变更流程制度化 |
| 分布式 KV 池 / 多级存储 / 缓存感知调度 | Mooncake / HiCache / LMCache | 诉求阶段 | 附录 C 演进路线具体化 |
| KV 命中率作为北极星指标上看板 | Manus | 落地路径① | 强化：拆分口径 + 长期看板 |
| PYTHONHASHSEED 等一致性细节 | vLLM/Mooncake 文档 | 未覆盖 | 集群配置 checklist |

## 5. 一句话总结

我们方案的主体（分层排布、注入式动态内容、低频裁剪、驻留诉求）
与业界最佳实践方向完全一致、且各自都有生产级验证；
**最大的增量收获是 Claude Code 的"缓存安全分叉"**——压缩请求本身
必须复用主会话前缀，否则每次压缩多付一次全价长上下文，
这是我们此前测算中漏掉的一项，需要在落地路径②中补上。
