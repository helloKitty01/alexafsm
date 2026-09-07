# Prompt 各段内容变化对照 — 数据与思路

> 本文件为 `prompt段内容变化对照.slides.html` 的配套数据文档。
> 别人可以基于此文件中的原始数据和思路，按自己的风格重新生成 slides / report / 表格。

---

## 1. 背景与目标

### 1.1 项目背景
小艺助手的 KVCache 优化：将 system_prompt (SP) 中的动态内容（技能列表、记忆、设备信息）移到 user message 的 `<system-reminder>` 中，使 SP 成为稳定前缀，提高缓存命中率。

### 1.2 本页目标
对比优化前后 prompt 中**每个段的内容变化**：原来是什么、现在是什么、变了什么、为什么变。

### 1.3 数据口径
- **Trace 文件**：`优化前后对比/before-q8-1.txt` 和 `after-q8-1.txt`
- **会话**：Q8 闲聊首调（"我有个好朋友闹别扭"）
- **模型**：两边均为 DS-V4-Flash-0731（同模型对比，排除 tokenizer 差异）
- **字符数**：原始 chars（非 token）；token 数见 `token_breakdown.md`
- **Slides 概念**：沿用 `上下文组成对比.v1.2.slides.html` 的段名（SP·固定、SP·动态⚡、user.md、Tools、UAT 等）

---

## 2. 段定义与 slides 概念映射

| Slides 段 | 含义 | 变化频率 |
|---|---|---|
| SP·固定 | 角色设定/原则/规范/安全/工具说明（14 个 `##` 段） | 版本发布才变 |
| SP·动态⚡ | skills + memory + device（每 Q 重写的病灶） | 每 Q 原位重写 |
| user.md | 会话级用户画像 | 会话创建时定 |
| Tools | 工具定义 JSON（API 独立字段） | 版本发布才变 |
| UAT·历史 10 轮 | 预载的上一会话历史 | 会话创建时定 |
| UAT·本会话 U | 当前会话的 user message | 每 Q 追加 |

---

## 3. 逐段变化明细

### 3.1 SP·固定（14 个 `##` 段）

**位置**：SP 中 → SP 中（不变）

**14 个段列表**（两边完全相同的段用 ✅ 标注）：

| # | `##` 段名 | before chars | after chars | 状态 |
|---|---|---:|---:|---|
| 1 | 识别用户意图 | 624 | 624 | ✅ 相同 |
| 2 | 说话方式 | 1,315 | 1,315 | ✅ 相同 |
| 3 | 承接判定 | 812 | 812 | ✅ 相同 |
| 4 | 模糊指令 | 339 | 339 | ✅ 相同 |
| 5 | 工具调用风格 | 332 | 332 | ✅ 相同 |
| 6 | 系统自身信息查询 | 437 | 437 | ✅ 相同 |
| 7 | 技能 | 674 | 674 | ✅ 相同 |
| 8 | AGENTS.md | 9,407 | 9,407 | ✅ 相同 |
| 9 | SOUL.md | 1,518 | 1,518 | ✅ 相同 |
| 10 | TOOLS.md | 20,474 | 20,843 | ⚠️ 微调 |
| 11 | 状态隔离与规则生效边界 | 337 | 337 | ✅ 相同 |
| 12 | 😊 像人类一样回应！ | 260 | 260 | ✅ 相同 |
| 13 | Response_Synthesis_Strategy.md | 7,099 | 7,099 | ✅ 相同 |
| 14 | Conversation_Style.md | 4,436 | 4,436 | ✅ 相同 |
| | **合计** | **43,478** | **44,019** | +541 chars |

**TOOLS.md 的具体变化**（+369 chars）：
- `#### PersonalContextSearch工具使用原则` 第 1 条扩充：
  - 新增"场景记忆"概念（用户近期高频活跃场景）
  - 新增"原子记忆"概念（个人基础信息、关联人员、日程规划、个人经历、行为偏好）
- 新增第 8 条"参数提取原则"：
  - 本机数据/原子记忆检索：仅提取 query
  - "我"/"我的家庭成员"问题：禁止将 query 中的"我"改写成"用户"
  - 场景记忆检索：需从 MEMORY.md 提取相关场景填充 scenes 字段
- 原第 8/9/10 条顺延为 9/10/11

### 3.2 SP·动态⚡ — Available Skills

**位置**：SP 中部 → user message `<system-reminder>`（**迁移**）

**Before**（在 SP 中，5,640 chars，12 个技能）：
```
mental-health, universal-writing-assistant, naps, phone-settings,
celia-collect, time-manager, medical-health-afu, deep-research,
access-system-metadata-safe-gateway, cross-device-transfer,
wakeup-device, product-guide
```

**After**（在 user message 中，6,925 chars，14 个技能）：
```
universal-writing-assistant, doc-reader, podcast-generate, aigir2,
phone-settings, gimbal-car-control, mindmap-generate, doc-generate,
search-activities, deep-research, access-system-metadata-safe-gateway,
cross-device-transfer, wakeup-device, product-guide
```

**技能变化**：
- 仅 before 有（5 个）：mental-health, naps, celia-collect, time-manager, medical-health-afu
- 仅 after 有（7 个）：doc-reader, podcast-generate, aigir2, gimbal-car-control, mindmap-generate, doc-generate, search-activities
- 两边都有（7 个）：universal-writing-assistant, phone-settings, deep-research, access-system-metadata-safe-gateway, cross-device-transfer, wakeup-device, product-guide

**变化原因**：技能列表每 Q 可能变化（用户可安装/卸载技能），放在 SP 中会导致 SP 每 Q 重写，破坏缓存前缀稳定性。移到 user message 后，SP 不再因技能变化而重写。

### 3.3 SP·动态⚡ — MEMORY.md

**位置**：SP 尾部 → user message `<system-reminder>`（**迁移**）

**Before**（在 SP 中，18 chars）：
```
## MEMORY.md
隐私去除
```

**After**（在 user message 中，34 chars）：
```
## MEMORY.md


```
（内容为空，本次 trace 无记忆数据）

**变化原因**：记忆内容每 Q 可能更新，放在 SP 中会破坏缓存前缀。移到 user message 后随 U 追加。

### 3.4 user.md（会话级）

**位置**：SP 尾部 → SP 尾部（位置不变，**内容填充**）

**Before**（26 chars，占位符）：
```
## USER.md - 和你打交道的人
隐私去除
```

**After**（1,151 chars，真实数据 + 新增私域原则）：
```
## USER.md - 和你打交道的人
了解你正在帮助的人
以下是用户授权的个人数据，用于理解用户特征并支持个性化服务。
<USER_PROFILE_DATA>
- 用户称呼：张俊
- 用户其他个人信息：["用户家庭地址在江苏省南京市秦淮区"]
- 用户重要日：["用户结婚纪念日的日期是每年2月1日","用户恋爱纪念日的日期是每年4月13日"]
- 用户关系人信息：["用户和我老婆（我和我老婆）结婚纪念日的日期是每年2月1日"]
- 用户的家在江苏省南京市秦淮区(新街口)
</USER_PROFILE_DATA>
<USER_BASIC_DATA>
- 一、用户基础静态信息台账
  用户自称名为张俊二，曾口述名杨存在"张俊"与"张军"的口径差异表述
  二、长期稳定行为存档（日常饮食/文娱休闲/物质消费/工作技术/生活人际/交互沟通偏好 — 均"无记录"）
  三、休眠周期行为存档 — 无记录
</USER_BASIC_DATA>
<USER_CURRENT_LOCATION>
- 江苏省南京市雨花台区雨花街道华为南京研究所B区
</USER_CURRENT_LOCATION>
### 私域信息使用与兜底原则（新增 469 chars）
1. 事实锚定与防脑补：必须基于 USER.md/MEMORY.md/PersonalContextSearch 检索结果，禁止脑补
2. 对象锁定与防张冠李戴：锁定具体主体匹配，严禁错配
3. 公私域隔离：私域事实不能用公域搜索结果替代
```

**变化原因**：
- before trace 中 user.md 是占位符（"隐私去除"），说明 before 版本未启用用户画像注入
- after 版本启用了真实用户画像，会话创建时确定、会话内不变，适合放在 SP 中
- 私域原则是新增的规范，约束模型处理私域信息的行为

### 3.5 DEVICE_INFO（会话级）

**位置**：SP 尾部 → SP 尾部（位置不变，**数据更新**）

**Before**（369 chars）：
```
设备：HUAWEI Mate 70 Pro+
系统：HarmonyOS 7.0
已安装应用：56 个（样机管理,设置,查找设备,优酷视频,淘宝,...）
```

**After**（395 chars）：
```
设备：HUAWEI Pura X
系统：HarmonyOS 6.0
已安装应用：63 个（抖音,样机管理,设置,查找设备,淘宝,夸克,...）
```

**变化原因**：两次 trace 使用了不同的测试设备，非优化导致的变化。DEVICE_INFO 本身是会话级数据（会话创建时确定），放在 SP 尾部合理。

### 3.6 Tools（API 字段）

**位置**：API 独立字段 → API 独立字段（位置不变，**顺序变 + 内容微调**）

**Before**（12,498 chars，5,806 tokens）：
```
顺序：invoke → SystemAutoAction → PersonalContextSearch → run_subagent →
      WebSearch → SkillLoad → think → CodeInterpreter → OpenApp → exec →
      CloseApp → discover_remote_agents
```

**After**（12,727 chars，5,944 tokens）：
```
顺序：discover_remote_agents → run_subagent → WebSearch → PersonalContextSearch →
      SystemAutoAction → OpenApp → CloseApp → SkillLoad → CodeInterpreter →
      exec → invoke → think
```

**内容变化**：
| 工具 | before tok | after tok | 差异 |
|---|---:|---:|---|
| PersonalContextSearch | 644 | 766 | +122（desc 改写，新增"场景记忆""原子记忆"概念） |
| run_subagent | 773 | 789 | +16（desc 微调） |
| 其余 10 个 | — | — | 完全相同 |

**变化原因**：工具顺序调整可能与 chat template 或模型对工具的注意力分布有关。PersonalContextSearch 的 description 改写与 TOOLS.md 中的原则扩充对应（新增记忆类型概念）。

### 3.7 UAT·本会话 U（query 级）

**位置**：user message → user message（位置不变，**结构变化**）

**Before**（41 chars，纯 query）：
```
[用户输入时间：Sat 2026-09-05 15:40] 你好呀，给我讲个笑话吧
```

**After**（7,020 chars，system-reminder + query）：
```
<system-reminder>
## Available Skills
（14 个技能描述，6,925 chars）
## MEMORY.md
（空，34 chars）
</system-reminder>
[用户输入时间：Sat 2026-09-05 15:39] 你好呀，给我讲个笑话吧
```

**变化原因**：这是本次优化的核心——动态内容（skills + memory）从 SP 移到 user message 的 `<system-reminder>` 中。U 从纯 query 变为"动态上下文 + query"，每 Q 追加而非原位重写。

### 3.8 UAT·历史 10 轮（会话级）

**位置**：UAT → UAT（不变）

两边都是预载上一会话的完整 U/A/T。本次 trace 中 before 的历史 = 102 chars，after 的历史 = 5,597 chars（差异是因为两次 trace 捕获的会话历史不同，非优化导致）。

---

## 4. 变化类型总结

| 类型 | 段 | 说明 | 对 KVCache 的影响 |
|---|---|---|---|
| 🟢 不变 | SP·固定（14段中13段）、UAT·历史 | 内容完全未动 | 前缀稳定，可命中 |
| 🟡 内容更新 | TOOLS.md、Tools、DEVICE_INFO | 文案微调或数据更新 | 不影响结构，但内容变了需重算 |
| 🔴 位置迁移 | Available Skills、MEMORY.md | 从 SP 移到 user message | **核心优化**：SP 不再因动态内容重写 |
| 🔵 新增/填充 | user.md（占位→真实）、私域原则 | 从占位符变为真实数据 | 会话级数据填充到 SP，会话内不变 |

---

## 5. 量化影响

| 指标 | Before | After | 变化 |
|---|---:|---:|---|
| SP 总量 | 54,148 chars | 50,010 chars | -7.6% |
| SP·动态⚡（在 SP 中） | 5,658 chars | 0 chars | 完全移出 |
| user message | 41 chars | 7,020 chars | +170× |
| 首调 cache hit | 55.7% | 0% | 首调全算（无缓存可命中） |
| Q2 cache hit | 56.9% | 84.5% | 大幅提升 |
| Q3 cache hit | 63.7% | 85.1% | 大幅提升 |
| Q4 cache hit | 95.3% | 85.1% | before 偶发高命中 |
| Q2 miss | 18,630 tok | 7,514 tok | -59.7% |
| Q3 miss | 13,977 tok | 7,916 tok | -43.3% |
| Q4 miss | 1,813 tok | 8,604 tok | after 更稳定 |

**关键结论**：after 牺牲了首调（0% hit，全算），换取 Q2 起 miss 钉死在 ~8K（不随轮数增长）；before 的 miss 随轮数波动剧烈（19.5K→18.6K→14.0K→1.8K）。

---

## 6. 原始数据提取方法

### 6.1 Trace 文件结构
```json
{
  "system_prompt": "完整 SP 文本",
  "tools": [12 个工具定义 JSON],
  "messages": [
    {"role": "user", "content": "user message 文本"},
    {"role": "assistant", "content": [...], "usage": {"input": N, "cache_read": N, "output": N}},
    {"role": "toolResult", "content": [...]}
  ]
}
```

### 6.2 段提取方法
- SP 中的段：用 `## ` 开头的行作为段分隔符
- user message 中的段：`<system-reminder>` 标签内的 `## ` 段
- Tools：`json.dumps(tools, ensure_ascii=False)` 序列化后计数

### 6.3 Token 计算方法
- DeepSeek-V4-Flash-0731：纯 Python BPE 分词器，解析 `tokenizer.json`（byte-level BPE, vocab 100K）
- GLM-5：纯 Python BPE 分词器，解析 `tokenizer.model`（raw-unicode BPE, vocab 151K）
- 每个段的 token 数 = 用对应模型 tokenizer 对该段文本直接分词计数
- 详见 `优化前后对比/_gen_breakdown_v2.py`

### 6.4 数据文件
- `优化前后对比/token_breakdown.csv` — 逐条 query 逐次调用的分段 token 明细
- `优化前后对比/token_breakdown.json` — 结构化数据（Q1–Q11）
- `优化前后对比/token_breakdown.md` — 人类可读表格
- `优化前后对比/before-q8-1.txt` / `after-q8-1.txt` — 原始 trace 文件

---

## 7. 生成 slides 的思路

### 7.1 页面定位
这一页是 `上下文组成对比.v1.2.slides.html`（P1）的补充页（P2）。P1 讲的是"结构怎么变"（段的位置和缓存命运），P2 讲的是"内容怎么变"（每段原来是什么、现在是什么）。

### 7.2 表格设计
- 左列：Slides 段名（与 P1 一致）
- 中左列：位置变化（SP→UM 等）
- 中列：原来内容（具体到技能名、设备型号等）
- 中右列：现在内容
- 右列：变化类型标签（不变/更新/迁移/填充）+ chars 对比

### 7.3 颜色编码
- 🟢 绿色 = 不变：内容未动
- 🟠 橙色 = 更新：内容微调（文案改写、数据更新）
- 🔴 红色 = 迁移：从 SP 移到 user message（KVCache 优化的核心动作）
- 🔵 蓝色 = 填充：从占位符变为真实数据

### 7.4 底部小结
4 个指标卡片：SP 总量、user message、SP·动态⚡、缓存效果，让人一眼看到优化的量化结果。

### 7.5 可扩展方向
- 如果要加更多 Q 的对比，可以从 `token_breakdown.md` 提取 Q1–Q6（task/qa 类型）的数据
- 如果要展示 SP 内部 14 个段的详细内容，可以展开为子表
- 如果要展示 Tools 的逐工具 diff，可以加一个折叠区域
