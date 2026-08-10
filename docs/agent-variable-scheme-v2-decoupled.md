# Agent 工具结果变量化方案 v2：分层解耦版

> 系列文档：[v1 框架侧提取](./agent-variable-scheme.md) · **v2 分层解耦（本文）** ·
> [v3 透明信封](./agent-variable-scheme-v3-envelope.md)（附 [HTML 幻灯片](./agent-variable-scheme-v3-slides.html)）
>
> 与 [v1 方案](./agent-variable-scheme.md) 的核心区别：**Agent 与工具彻底解耦**。
> Agent 不再内置"哪些字段该提取"的规则，而是默认**整体存储每个 toolResult**，
> 只认识两个协议标识：结果里的 `$export`（工具自述导出）与参数里的 `{{...}}`（引用）。
> 工具可以完全不知道本机制存在（基线层兜底），也可以精细控制导出行为（协议层 opt-in）。

---

## 1. 分层架构

```mermaid
flowchart TB
    subgraph L0["基线层（零耦合，默认开启）"]
        B1["整体存储：每个 toolResult 存为 {tool缩写}{全局序号}<br/>如 find1 / ticket2 / read3"]
        B2["通用省略：超阈值叶子值 → stub<br/>stub 内嵌可复制引用串 $ref"]
        B3["引用解析：{{name.path}} → 执行前替换<br/>工具永远只见真实值"]
    end
    subgraph L1["协议层（工具 opt-in）"]
        P1["工具在结果中放保留键 $export：<br/>value / preview / name_hint / lifetime_hint"]
        P2["覆盖基线：定制 preview、<br/>导出'短但须精确复述'的值、声明物理有效期"]
    end
    subgraph L2["句柄层（工具生态内共享寻址）"]
        H1["工具直接返回 resource URI<br/>artifact://…，内容不经过 Agent"]
        H2["下游工具直接消费 URI<br/>（URI 本身很短，无需变量化）"]
    end
    L1 -->|"未标记的字段回落到"| L0
    L2 -->|"跨生态时回落到"| L1
```

**职责边界**（解耦的关键在这张表）：

| 角色 | 职责 | 不负责 |
|---|---|---|
| 工具（可选参与） | 用 `$export` 标记想导出的字段、给 preview / `lifetime_hint`；或返回 resource URI | 不感知变量命名、作用域、存储、引用语法 |
| Agent Runtime | 整体存储、扫 `$export`、通用省略、`{{}}` 解析替换、错误回喂 | 不理解任何工具的业务语义 |
| VariableStore | 作用域（loop/conversation）、TTL、LRU、spill/rehydrate、checkpoint | 不决定"什么值该导出" |
| LLM | **原样复制** stub 里的 `$ref` 引用串 | 不需要自己构造引用路径 |

---

## 2. 运行时流程

### 出方向：toolResult → 对话上下文

```mermaid
flowchart LR
    A["工具返回原始结果"] --> B["① 整体存入 VariableStore<br/>命名：{tool缩写}{全局调用序号}"]
    B --> C{"② 扫描保留键 $export"}
    C -->|命中| D["拆出 value 存回原路径<br/>stub 采用工具给的<br/>preview / lifetime_hint"]
    C -->|未命中| E["③ 通用省略：<br/>叶子值 > 阈值 → 截断 stub"]
    D --> F["④ stub 内嵌可复制引用串<br/>{&quot;$ref&quot;: &quot;{{find1.log_path}}&quot;, …}"]
    E --> F
    F --> G["⑤ stub 版写入对话上下文<br/>（原始长值绝不进上下文）"]
```

### 入方向：LLM tool call → 工具执行

```mermaid
flowchart LR
    A["LLM 输出 tool call"] --> B["① JSON 解析 + schema 校验<br/>（{{}} 占位按字符串通过）"]
    B --> C{"② 扫描参数值中的 {{name.path}}"}
    C -->|"变量不存在 / 路径错 / 已过期"| D["不执行工具<br/>构造 tool error 回喂<br/>附可用引用清单 → LLM 自纠"]
    C -->|全部命中| E["③ 展开替换<br/>整值保留原类型 / 字符串内插拼接<br/>同时 touch 续期"]
    E --> F["④ 执行工具（真实值）"]
    F --> G["⑤ 展开后的真实值<br/>不回写对话历史"]
```

两个协议标识就是 Agent 与外界的全部契约：

| 标识 | 出现位置 | 含义 |
|---|---|---|
| `$export` | 工具结果 JSON 中的保留键 | 工具自述："这个值请变量化，preview / 有效期我来给" |
| `{{name.path}}` | LLM 输出的参数值中 | 引用：执行前由 Runtime 替换为真实值 |

---

## 3. 端到端详细示例

### 场景

多轮对话，Turn 1 用户说：

> "帮我找出昨天 CI 构建失败的日志，分析原因，然后把完整日志传到团队网盘。"

参与工具（三个层次各有代表）：

| 工具 | 层次 | 说明 |
|---|---|---|
| `find_artifacts` | 基线层 | 存量老工具，**完全不知道变量机制存在** |
| `get_upload_ticket` | 协议层 | 自有工具，结果里用 `$export` 自述导出 |
| `read_file` / `upload_file` | 句柄层 | 同一存储生态，通过 `artifact://` URI 直传内容 |

---

### 调用 ①：`find_artifacts`（基线层——工具零改动）

LLM 输出：

```json
{"tool": "find_artifacts", "args": {"query": "ci build failure", "date": "2026-08-06"}}
```

**工具真实返回**（普通 JSON，没有任何协议标记）：

```json
{
  "status": "ok",
  "log_path": "/mnt/ci-cache/workspaces/team-platform/pipelines/nightly-build/runs/2026-08-06T031500Z-8f4d2c1a-7b3e-4e9d-a2c4-91f0e8d7b6a5/attempts/2/steps/17-integration-test/artifacts/logs/build_failure_full.log",
  "size_bytes": 18734208
}
```

Runtime 出方向管线：

1. 整体存为 **`find1`**（find_artifacts 的第 1 次全局调用）；
2. 扫 `$export`：无命中；
3. 通用省略：`log_path` 218 字符 > 阈值 200 → stub 化；`size_bytes` 短且需推理，内联保留；
4. 写入上下文的 stub 版：

```json
{
  "status": "ok",
  "log_path": {
    "$ref": "{{find1.log_path}}",
    "size": 218,
    "preview": "/mnt/ci-cache/workspaces/team-platform/…/17-integration-test/artifacts/logs/build_failure_full.log"
  },
  "size_bytes": 18734208
}
```

> LLM 后续引用时**原样复制 `$ref` 的值**即可，不需要理解命名规则或自己拼路径。

**此刻存储状态**：

| 变量 | 内容 | scope | 元数据 |
|---|---|---|---|
| `find1` | 完整 toolResult（含 218 字符路径） | loop | source=find_artifacts#1 |

---

### 调用 ②：`get_upload_ticket`（协议层——工具自述导出）

LLM 请求上传票据：

```json
{"tool": "get_upload_ticket", "args": {"dest_folder": "reports"}}
```

**工具真实返回**（自有工具，主动使用 `$export` 保留键）：

```json
{
  "status": "ok",
  "url": {
    "$export": {
      "value": "https://storage.example.com/teamdrive/upload?sig=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWFtLXBsYXRmb3JtIiwiZXhwIjoxNzU0NTUwMjAwLCJwYXRoIjoiL3RlYW1kcml2ZS9yZXBvcnRzLyIsInBlcm0iOiJ3cml0ZSJ9.k7Jf3nQ9pXw2vYs8rTz5mHc1bLd4eGa6uIo0NkSjWqE&expires=1754550200",
      "preview": "teamdrive/reports 上传端点（签名 URL）",
      "name_hint": "upload_url",
      "lifetime_hint": "expires:2026-08-07T09:30:00Z"
    }
  },
  "token": {
    "$export": {
      "value": "tkn_9f2Kx7Qw",
      "preview": "上传令牌（10 字符，必须精确使用）",
      "name_hint": "upload_token"
    }
  }
}
```

注意 `token` 只有 10 字符，**低于阈值，基线层抓不到**——但它抄错一个字符就 401。
这正是协议层存在的理由：只有工具自己知道"这个值短但必须精确复述"。

Runtime：整体存为 **`ticket2`**，`$export` 命中两处 → 拆出 `value` 存回原路径，
`lifetime_hint` 记入变量元数据。写入上下文的 stub 版：

```json
{
  "status": "ok",
  "url": {
    "$ref": "{{ticket2.url}}",
    "size": 287,
    "preview": "teamdrive/reports 上传端点（签名 URL）",
    "expires": "2026-08-07T09:30:00Z"
  },
  "token": {
    "$ref": "{{ticket2.token}}",
    "preview": "上传令牌（10 字符，必须精确使用）"
  }
}
```

**此刻存储状态**：

| 变量 | 内容 | scope | 元数据 |
|---|---|---|---|
| `find1` | 完整 toolResult | loop | — |
| `ticket2` | 完整 toolResult（url 已拆出 $export.value） | loop | url 的 expires=09:30Z |

---

### 调用 ③：`read_file`（入方向替换 + 句柄层返回）

LLM 只需 ~8 个 token 就写完路径参数：

```json
{"tool": "read_file", "args": {"path": "{{find1.log_path}}", "tail_lines": 500}}
```

Runtime 入方向管线：

1. JSON 解析、schema 校验通过（占位符按字符串）；
2. 解析 `{{find1.log_path}}`：`find1` 存在、路径 `log_path` 存在 → 替换为完整 218 字符路径，同时 `find1` touch 续期；
3. 执行工具，`read_file` 收到的是**真实路径**（它对变量机制一无所知）。

**工具真实返回**（该工具属于共享存储生态，大内容走句柄层）：

```json
{
  "status": "ok",
  "content_resource": "artifact://ci-cache/run-8f4d2c1a/build_failure_full.log",
  "tail": "……500 行日志原文，共 43012 字符……"
}
```

Runtime：整体存为 **`read3`**；`$export` 无命中；通用省略抓到 `tail`（42KB）；
`content_resource` 是 54 字符的 URI，**短，直接内联**——句柄层的意义就在于此：
18MB 的日志内容从头到尾没进过 Agent，进上下文的只是一个短 URI。stub 版：

```json
{
  "status": "ok",
  "content_resource": "artifact://ci-cache/run-8f4d2c1a/build_failure_full.log",
  "tail": {
    "$ref": "{{read3.tail}}",
    "size": 43012,
    "preview": "…[03:21:44] ERROR IntegrationTest.test_payment_flow FAILED\n[03:21:44] AssertionError: expected status 200, got 503\n[03:21:45] ERROR upstream 'payment-gateway' health check timeout after 30s…"
  }
}
```

LLM 直接从 preview 中读出失败原因（payment-gateway 健康检查超时），无需展开 42KB 全文。

---

### 调用 ④：引用出错 → 自动纠正

LLM 上传时手滑，用了 `$export` 里的 `name_hint` 当路径（一个真实会发生的混淆）：

```json
{
  "tool": "upload_file",
  "args": {
    "source": "artifact://ci-cache/run-8f4d2c1a/build_failure_full.log",
    "dest": "{{ticket2.upload_url}}",
    "auth_token": "{{ticket2.token}}"
  }
}
```

Resolver 在 `ticket2` 中查无路径 `upload_url` → **不执行工具**，构造 tool error 回喂：

```json
{
  "error": "unknown_reference",
  "message": "ticket2 中不存在路径 'upload_url'。ticket2 可用引用：{{ticket2.url}} (string, 287B, teamdrive/reports 上传端点), {{ticket2.token}} (string, 10B, 上传令牌)"
}
```

LLM 立即改用正确引用（字符串内插拼接文件名）：

```json
{
  "tool": "upload_file",
  "args": {
    "source": "artifact://ci-cache/run-8f4d2c1a/build_failure_full.log",
    "dest": "{{ticket2.url}}&filename=build_failure_full.log",
    "auth_token": "{{ticket2.token}}"
  }
}
```

Resolver 展开两处引用；`upload_file` 收到完整 287 字符 URL 与真实 token，
从 artifact 存储**直传**网盘（内容依然不经过 Agent）。上传成功，LLM 给出最终回复。

### Turn 1 结束：生命周期结算

- `find1`、`ticket2`、`read3` 本轮均被引用 → **touch-to-promote，提升为 `conversation`**；
- 稍后 `read3`（42KB）因体积被 LRU **spill** 到冷层，热层留 tombstone。

---

### Turn 2（一小时后）：跨轮引用 + lifetime_hint 生效

用户："刚才那份日志的尾部 500 行也单独存一份传上去。"

Runtime 在本轮 user message 末尾（append-only，不破坏 prompt 前缀缓存）附加清单：

```xml
<available_variables>
  {{find1.log_path}}   string 218B  conversation           CI 失败日志绝对路径
  {{ticket2.url}}      string 287B  conversation(已过期)    teamdrive 上传端点，09:30Z 过期
  {{ticket2.token}}    string 10B   conversation           上传令牌
  {{read3.tail}}       string 42KB  conversation(spilled)  CI 失败日志尾部 500 行
</available_variables>
```

LLM 先写文件再上传：

```json
{"tool": "write_file", "args": {"path": "/tmp/log_tail.txt", "content": "{{read3.tail}}"}}
```

- `read3` 已 spill → Resolver 触发 **rehydrate**（冷层读回）后替换，42KB 原文交给工具；

接着 LLM 引用 `{{ticket2.url}}` 上传——Resolver 检查元数据发现**已过 09:30Z 有效期**
（工具当初通过 `lifetime_hint` 声明的物理失效时间，Agent 只负责执行判定）：

```json
{
  "error": "reference_expired",
  "message": "{{ticket2.url}} 已于 2026-08-07T09:30:00Z 过期（get_upload_ticket 声明的有效期）。请重新调用 get_upload_ticket 获取新的上传地址。"
}
```

LLM 自纠：重新调用 `get_upload_ticket` → 新结果存为 **`ticket6`** → 用 `{{ticket6.url}}` 完成上传。

---

## 4. 全程 token 与正确性对比

| 步骤 | 无变量方案 | 分层方案 |
|---|---|---|
| 调用③ path 参数 | 逐字复述 218 字符 ≈ 60+ tokens，UUID 段易抄错 | `{{find1.log_path}}` ≈ 8 tokens，复制 stub 即可 |
| 调用④ dest + token | 297 字符 ≈ 100+ tokens，token 抄错即 401 | 两个引用 ≈ 14 tokens |
| 18MB 日志内容 | 无法进上下文，只能工具内截断 | `artifact://` URI 54 字符直传，内容不经 Agent |
| Turn 2 跨轮引用 | 从多轮前历史逐字抄写 | 清单里复制引用串；过期有明确报错兜底 |

---

## 5. 协议规范摘要

**`$export`（工具 → Agent，结果 JSON 中的保留键）**

| 字段 | 必填 | 说明 |
|---|---|---|
| `value` | 是 | 真实值（任意 JSON 类型） |
| `preview` | 否 | 给 LLM 看的摘要；缺省则 Runtime 机械截断 |
| `name_hint` | 否 | 语义命名提示（仅用于清单展示，不改变引用路径） |
| `lifetime_hint` | 否 | 物理有效期等事实声明；Agent 作为淘汰/报错依据 |

**`$ref` stub（Agent → LLM，写入上下文的替身）**：`$ref`（可复制引用串）、`size`、`preview`、可选 `expires`。

**引用语法（LLM → Agent）**：`{{变量名.JSONPath}}`；整值引用保留原类型，出现在字符串内部则内插拼接。
变量名 = `{tool 名缩写}{全局调用序号}`，由 Runtime 自动分配。

**安全约定**：只在参数值位置替换；工具结果原文中的 `{{` 与 `$export` 字面量入库时转义，防止伪造导出或二次展开。
