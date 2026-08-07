# Agent 工具结果变量化方案（Variable Handle）

> 解决问题：Agent loop / 多轮对话中，toolA 的结果包含超长内容（如绝对路径、签名 URL、文件内容），
> 后续 tool 调用依赖该内容时，LLM 逐 token 复述会导致**增量推理时延高**且**容易抄错**。
> 方案：长内容只在框架层流转，LLM 只输出短变量引用 `{{vN}}`，框架在工具执行前替换为真实值。

---

## 1. 整体架构图

```mermaid
flowchart TB
    subgraph LLM["LLM（只见句柄，不见长内容）"]
        direction TB
        L1["输入上下文：<br/>历史消息 + tool result 替身<br/>+ available_variables 清单"]
        L2["输出：tool call<br/>参数含 {{v3}} 短引用"]
    end

    subgraph Runtime["Agent Runtime（管线）"]
        direction TB
        P1["① JSON 解析"]
        P2["② Schema 校验<br/>（占位符按字符串校验）"]
        P3["③ Variable Resolver<br/>引用替换：{{v3}} → 真实值<br/>支持整值 / 字符串内插 / JSONPath"]
        P4["④ 工具执行"]
        P5["⑤ Externalizer<br/>长字段提取 → 变量化<br/>阈值 / 声明式 / 精确复述型"]
        P6["⑥ 写回上下文<br/>（只写替身 + preview）"]
        P1 --> P2 --> P3 --> P4 --> P5 --> P6
    end

    subgraph Store["VariableStore"]
        direction TB
        S1["热层（内存）<br/>name → {value, scope, source,<br/>created_turn, last_used_turn}"]
        S2["冷层（磁盘 / 对象存储）<br/>spill 降级 + tombstone 指针"]
        S3["生命周期管理<br/>step / loop / conversation / persistent<br/>TTL + LRU + touch-to-promote"]
        S1 <-->|"spill / rehydrate"| S2
        S3 --- S1
    end

    subgraph Tools["工具层（见到真实值）"]
        T1["toolA / toolB / ..."]
    end

    subgraph Ctx["上下文管理"]
        C1["Compaction 反向替换：<br/>历史长内容 → 新变量引用"]
        C2["Checkpoint：<br/>对话历史 + 变量表 一起快照"]
    end

    L2 -->|"tool call"| P1
    P3 -->|"resolve(name)"| S1
    P3 -->|"未知/过期引用"| ERR["构造 tool error 回喂<br/>附可用变量清单 → LLM 自纠"]
    ERR --> L1
    P4 --> T1
    T1 -->|"原始结果（可能超长）"| P5
    P5 -->|"put(name, value)"| S1
    P6 --> L1
    Ctx -.-> Store
    Ctx -.-> L1
```

**要点回顾**

| 方向 | 时机 | 动作 |
|---|---|---|
| 出方向（结果 → 变量） | 工具执行后、写入上下文**前** | 长/精确复述型字段落库，上下文里只留 `$var` 替身 + preview |
| 入方向（变量 → 参数） | schema 校验后、工具执行**前** | `{{vN}}` 替换为真实值；替换结果**不回写**对话历史 |

---

## 2. 变量生命周期状态图

```mermaid
stateDiagram-v2
    [*] --> loop : 工具结果变量化<br/>（默认 scope=loop）
    loop --> conversation : touch-to-promote<br/>（跨轮被引用 / 最终回复引用）
    loop --> [*] : loop 结束未被提升<br/>→ 回收
    conversation --> spilled : LRU / 容量超限<br/>→ 降级到冷层
    spilled --> conversation : 再次被引用<br/>→ rehydrate
    conversation --> [*] : TTL 到期（N 轮未引用）<br/>→ 淘汰
    conversation --> persistent : 显式声明<br/>（跨会话资产）
    persistent --> [*] : 显式删除
```

| 作用域 | 存活范围 | 典型内容 | 回收时机 |
|---|---|---|---|
| `step` | 当前一次 loop 迭代 | 中间管道值 | 迭代结束 |
| `loop` | 当前一轮 agent loop | toolA→toolB 传递的路径、句柄 | loop 结束（agent 给出最终回复） |
| `conversation` | 整个多轮会话 | 跨轮复用的路径、URL、文件内容 | TTL / LRU / 会话结束 |
| `persistent` | 跨会话 | 用户长期资产 | 显式删除 |

---

## 3. 核心时序图

```mermaid
sequenceDiagram
    participant U as 用户
    participant LLM
    participant RT as Agent Runtime
    participant VS as VariableStore
    participant T as 工具

    U->>LLM: 请求（Turn 1）
    LLM->>RT: toolA(...)
    RT->>T: 执行 toolA
    T-->>RT: 结果含 600 字符签名 URL
    RT->>VS: put(v1, url, scope=loop)
    RT-->>LLM: result{url: {$var:"v1", preview:"…"}}
    LLM->>RT: toolB({"dest": "{{v1}}"})
    RT->>RT: 解析 + 校验
    RT->>VS: resolve("{{v1}}")
    VS-->>RT: 完整 URL（600 字符）
    RT->>T: 执行 toolB(完整 URL)
    T-->>RT: 结果
    RT-->>LLM: result（短，内联）
    LLM-->>U: 最终回复
    Note over RT,VS: loop 结束：v1 被引用过 → 提升为 conversation
    U->>LLM: 后续请求（Turn 5）
    LLM->>RT: toolC({"dest": "{{v1}}"})
    Note over VS: v1 仍存活（conversation 作用域）<br/>touch → 续期
```

---

## 4. 端到端详细示例

### 场景

多轮对话。用户第 1 轮说：

> "帮我找出昨天 CI 构建失败的日志，分析失败原因，把摘要报告上传到团队网盘。"

可用工具：`find_artifacts`、`read_file`、`write_file`、`upload_file`。

---

### Turn 1 / Loop 迭代 ①：查找产物 —— 出方向变量化

LLM 输出 tool call（正常短参数，无需变量）：

```json
{"tool": "find_artifacts", "args": {"query": "ci build failure", "date": "2026-08-06"}}
```

**工具真实返回**（Runtime 内部可见，LLM 永远看不到这一版）：

```json
{
  "status": "ok",
  "log_path": "/mnt/ci-cache/workspaces/team-platform/pipelines/nightly-build/runs/2026-08-06T031500Z-8f4d2c1a-7b3e-4e9d-a2c4-91f0e8d7b6a5/attempts/2/steps/17-integration-test/artifacts/logs/build_failure_full.log",
  "upload_url": "https://storage.example.com/teamdrive/upload?sig=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWFtLXBsYXRmb3JtIiwiZXhwIjoxNzU0NTUwMDAwLCJwYXRoIjoiL3RlYW1kcml2ZS9yZXBvcnRzLyIsInBlcm0iOiJ3cml0ZSJ9.k7Jf3nQ9pXw2vYs8rTz5mHc1bLd4eGa6uIo0NkSjWqE&expires=1754550000&uploader=ci-bot",
  "size_bytes": 18734208
}
```

`log_path` 218 字符、`upload_url` 344 字符，均超过阈值（200），且都是"精确复述型"字段
（工具 schema 中标注了 `exportable: true`）。Externalizer 落库：

| 变量 | 值 | scope | source |
|---|---|---|---|
| `v1_log_path` | 完整路径（218 字符） | loop | `find_artifacts#call_01` |
| `v2_upload_url` | 完整签名 URL（344 字符） | loop | `find_artifacts#call_01` |

**LLM 实际看到的 tool result**（写入对话历史的版本）：

```json
{
  "status": "ok",
  "log_path": {
    "$var": "v1_log_path", "type": "string", "size": 218,
    "preview": "/mnt/ci-cache/workspaces/team-platform/…/17-integration-test/artifacts/logs/build_failure_full.log",
    "scope": "loop", "source": "find_artifacts#call_01"
  },
  "upload_url": {
    "$var": "v2_upload_url", "type": "string", "size": 344,
    "preview": "https://storage.example.com/teamdrive/upload?sig=eyJhbGci…&uploader=ci-bot",
    "scope": "loop", "source": "find_artifacts#call_01"
  },
  "size_bytes": 18734208
}
```

> `size_bytes` 是 LLM 需要**推理其内容**的短值（判断文件大不大），内联保留，不变量化。

---

### Turn 1 / Loop 迭代 ②：读日志 —— 入方向替换 + 结果再变量化

LLM 输出（只需 ~10 个 token 就写完了路径参数）：

```json
{"tool": "read_file", "args": {"path": "{{v1_log_path}}", "tail_lines": 500}}
```

Runtime 管线：

1. JSON 解析 ✓
2. Schema 校验：`path` 声明了支持 `$ref`，占位符按字符串通过 ✓
3. **Resolver 替换**：`{{v1_log_path}}` → 完整 218 字符路径（同时 `last_used_turn` 续期）
4. 执行 `read_file`，工具拿到真实路径

工具返回 500 行日志（约 42KB）→ Externalizer 落库为 `v3_log_tail`（scope=loop），LLM 看到：

```json
{
  "status": "ok",
  "content": {
    "$var": "v3_log_tail", "type": "string", "size": 43012,
    "preview": "...\n[03:21:44] ERROR IntegrationTest.test_payment_flow FAILED\n[03:21:44] AssertionError: expected status 200, got 503\n[03:21:45] ERROR upstream service 'payment-gateway' health check timeout after 30s\n…(共 500 行)",
    "scope": "loop", "source": "read_file#call_02"
  }
}
```

> 这里 preview 特意截取了**含 ERROR 的区分性片段**（Externalizer 对日志类内容可用启发式选摘要），
> LLM 已能直接从 preview 判断失败原因，无需再把 42KB 全文塞进上下文。

---

### Turn 1 / Loop 迭代 ③：写报告 —— 短内容照常内联

LLM 基于 preview 分析出原因，生成摘要报告（报告本身是 LLM 新创作的内容，必须由它输出）：

```json
{
  "tool": "write_file",
  "args": {
    "path": "/tmp/report-20260806.md",
    "content": "# CI 构建失败分析（2026-08-06 nightly）\n\n- 失败用例：IntegrationTest.test_payment_flow\n- 直接原因：payment-gateway 健康检查超时（30s），接口返回 503\n- 建议：检查 payment-gateway 部署状态与依赖数据库连接池配置\n"
  }
}
```

工具返回 `{"status": "ok", "path": "/tmp/report-20260806.md"}` —— 路径短，**内联，不变量化**。

---

### Turn 1 / Loop 迭代 ④：上传 —— 字符串内插引用

```json
{
  "tool": "upload_file",
  "args": {
    "local_path": "/tmp/report-20260806.md",
    "dest": "{{v2_upload_url}}&filename=report-20260806.md"
  }
}
```

Resolver 做**字符串内插**：完整 344 字符 URL + 拼接后缀 → 工具执行上传成功。

LLM 给出最终回复，**Turn 1 的 loop 结束**。生命周期结算：

- `v1_log_path`、`v2_upload_url`、`v3_log_tail` 本轮都被引用过 → **touch-to-promote，提升为 `conversation`**
- `v3_log_tail`（42KB）体积大，随后被 LRU **spill 到冷层**，热层留 tombstone

---

### Turn 2（若干轮之后）：跨轮引用 + 错误自纠 + rehydrate

用户："把**完整日志文件**也传到网盘吧。"

Runtime 在本轮 user message 末尾附加变量清单（append-only，不破坏 prompt 前缀缓存）：

```xml
<available_variables>
  v1_log_path      string  218B   conversation  /mnt/ci-cache/…/build_failure_full.log
  v2_upload_url    string  344B   conversation  https://storage.example.com/…（签名 URL，2026-08-07 过期）
  v3_log_tail      string  42KB   conversation(spilled)  CI 失败日志尾部 500 行
</available_variables>
```

**② 错误自纠示例**：LLM 手滑引用了不存在的变量：

```json
{"tool": "upload_file", "args": {"local_path": "{{v1_logpath}}", "dest": "{{v2_upload_url}}"}}
```

Resolver 查无 `v1_logpath`，**不执行工具**，构造 tool error 回喂：

```json
{
  "error": "unknown_variable",
  "message": "变量 v1_logpath 不存在。可用变量：v1_log_path (string, 218B, /mnt/ci-cache/…), v2_upload_url (string, 344B), v3_log_tail (string, 42KB, spilled)"
}
```

LLM 立即重试正确引用：

```json
{"tool": "upload_file", "args": {"local_path": "{{v1_log_path}}", "dest": "{{v2_upload_url}}&filename=build_failure_full.log"}}
```

- `v1_log_path` 命中热层 → 直接替换；
- 若这次引用的是 `v3_log_tail`（已 spill）→ Resolver 触发 **rehydrate**（冷层读回热层）后替换。

两个变量因本次 touch 再次续期。上传完成，任务结束。

---

### 全程 LLM 输出 token 对比

| 步骤 | 无变量方案（LLM 逐字复述） | 变量方案（LLM 输出引用） |
|---|---|---|
| 迭代② path 参数 | 218 字符 ≈ 60+ tokens，且可能抄错 UUID | `{{v1_log_path}}` ≈ 6 tokens |
| 迭代④ dest 参数 | 344 字符签名 URL ≈ 110+ tokens，抄错即 403 | `{{v2_upload_url}}…` ≈ 10 tokens |
| Turn 2 两个参数 | 从多轮前的历史里逐字抄 562 字符 | 16 tokens |
| 上下文占用 | 长内容在历史中反复出现多份 | 每个长值只存一份替身 + preview |

---

## 5. 实现清单（落地时的模块划分）

| 模块 | 职责 | 关键接口 |
|---|---|---|
| `VariableStore` | 存取、作用域、TTL/LRU、spill/rehydrate、checkpoint | `put / get / resolve / end_of_loop / snapshot` |
| `Externalizer` | 出方向：阈值 + 声明式 + 启发式 preview 生成 | `externalize(result, source, turn)` |
| `Resolver` | 入方向：整值 / 内插 / JSONPath；未知引用报错 | `resolve_args(args, turn)` |
| `ContextManager` | 变量清单注入（消息尾部 append）、历史 compaction 反向替换 | `inject_listing / compact` |
| 工具 Schema 扩展 | `exportable: true`（输出侧）、`accepts_ref: true`（输入侧） | — |

**防注入与安全**：只在参数**值**位置替换；工具结果原文中出现的 `{{` 字面量入库时转义；
子 agent 不共享变量表，跨 agent 传递需显式解析或带 ACL 的引用。
