# 02 · 事件目录（event catalog）规范与内建条目

> 配套 `openClaw自动化任务方案.slides.v2.2.html` P7 / P12 / P13 / P18。本文是目录的**完整文本版**：条目 schema、filter 语法、命名规则、10 组 63 条内建事件（含模型不可见的 internal 字段）。幻灯片只放分组总览，细节以本文为准。

## 1. 设计约束

1. **模型只看目录的可见部分**：`type / group / desc / fields / must_filter / pair / state_query`。`rate / debounce / stale_after / sensitivity` 是 internal，cron service 在订阅时从目录取用，模型不写、不感知。
2. **目录静态进 system prompt**：63 条一行一条约 3–4K token，作为编译期 system prompt 的静态段（KV cache 前缀命中）。`event_catalog` 工具只保留 `get(type)`（返回完整可见条目）与派生事件查询（路 B publish 出来的、不在内建表里的类型）。
3. **filter 只做单事件布尔**：字段只能来自该条目的 `fields`；没有函数、时间、跨事件引用、state。时间窗归 `limits.activeWindow`；跨事件组合归 trigger + state（幻灯片 P12）。
4. **事件中心不做 CEP、没有 guards**：目录 + 单事件 filter + at-least-once 推送，其余都在 cron service。
5. **`occurred_at` 不在 payload 里**：它是推送信封字段（`event_id / job_id / event_type / occurred_at / payload`），进 tick 时放在 `tick.event.occurred_at`。

## 2. 条目 schema

```yaml
type:        <group>.<noun>_<verb|state>     # 唯一键，小写下划线；成对事件用 _on/_off、_connected/_disconnected、enter/exit
group:       device | setting | connectivity | geofence | activity | phone | alarm | app | calendar | notification
desc:        一句话中文描述（≤ 20 字）
fields:                                       # payload 字段；"!" 标 key 字段（可被填槽解析工具解析成稳定 id）
  - name: zone        type: string   key: true   desc: 围栏名（places.list）
  - name: confidence  type: number   range: 0–1
must_filter: [zone]                           # 订阅时必须约束的字段；缺失 → cron add 校验失败
pair:        geofence.exit                    # 成对事件（编译期做时序 / 缺席组合时用）
state_query: phone_state.get(zones)           # 对应的"当前状态"查询；供 T1 状态门用
internal:                                     # 模型不可见
  rate:        low | mid | high | burst       # 典型频率，决定是否要求 must_filter
  debounce:    5m                             # 同 job 同 filter 的合并窗口，事件中心评估
  stale_after: 10m                            # 过期阈值；事件中心丢弃 + openClaw 兜底
  sensitivity: none | location | contacts | content
```

**校验规则（cron service 在 `cron add / update` 时执行，失败即报错回主 loop）**

- `eventType` 必须在目录中（内建或已发布的派生事件）。
- filter 中出现的字段必须 ∈ 该条目 `fields`；枚举字段的比较值必须 ∈ 枚举。
- `must_filter` 列出的字段必须在 filter 中被约束（`==`、`in`、`startsWith` 任一）。
- `rate: high | burst` 的条目若无 `must_filter`，编译规则要求回读时提醒用户"会很频繁"。

**派生事件条目（路 B，v2.3 补）**

派生事件是某条 job 的 payload 调 `event_publish(type, payload)` 发出的事件，与内建事件同构，登进同一张目录：

- **谁登记**：生产者 job 首次 `cron add` 时，cron service 用 `payload` 里声明的 `publishes: {type, desc, fields}` 向事件中心 `catalog.register`；事件中心校验 `type` 不与内建冲突、`fields` 合法后写入。生产者 job `remove` 时条目保留（可能已有消费者），标 `orphaned` 供对账。
- **group**：固定为生产者声明的业务组名（如 `weather`、`ticket`、`press`），不得复用 10 个内建组名；`type` 同样 `group.noun_verb`，如 `weather.rain_tomorrow`、`ticket.on_sale`、`press.conference_ended`。
- **fields**：由生产者定，规则同内建（key 字段可标 `!`，枚举写全）。消费者 job 的 filter 只能引用这些字段，`cron add` 校验一致。
- **internal**：`rate` 由生产者的 schedule 推出（`cron 0 20 * * *` → low），`debounce / stale_after` 取组默认（1m / 24h，天气类事件"过期"的含义与围栏不同，生产者可覆盖），`sensitivity` 继承生产者 payload 的最高级别。
- **模型怎么看到**：不进静态 prompt（数量不定），主 loop 用 `event_catalog.get(type)` 或 `event_catalog.search(q)` 查派生事件；回读时把字段列给用户。

## 3. filter 语法（一页）

```
expr     := or
or       := and ( '||' and )*
and      := not ( '&&' not )*
not      := '!' not | primary
primary  := '(' expr ')' | field op literal | field 'in' '[' literal (',' literal)* ']'
            | field ('contains' | 'startsWith') string
op       := '==' | '!=' | '<' | '<=' | '>' | '>='
field    := 条目 fields 里的名字（不带 payload. 前缀）
literal  := 'string' | number | true | false | null
```

- 字符串用单引号；大小写敏感。
- 布尔字段可直接写 `field` / `!field`。
- **不支持**：函数调用、`now / ts / hour()` 等时间量、其他事件的字段、`state`。

示例：

| 用户话 | filter |
|---|---|
| 到家 | `zone == 'home'` |
| 张三来电（张三 → contacts.search → `c_12`） | `contact_id == 'c_12'` |
| 微信或钉钉的通知 | `package_name in ['com.tencent.mm', 'com.alibaba.android.rimet']` |
| 电量低于 15%（battery_low 自带 level） | `level <= 15` |
| 连上家里 WiFi | `bssid == 'a4:…'` 或 `ssid == 'Home-5G'` |
| 非视频来电 | `!is_video` |

## 4. 命名与字段规范

- **两套大小写，各归各位**：事件目录 yaml 与事件 payload 字段一律 snake_case（`stale_after`、`must_filter`、`contact_id`、`occurred_at`）；openClaw job JSON（`cron add` 的所有字段）一律 camelCase（`staleAfter`、`nextCheckAt`、`maxRunsPerDay`、`activeWindow`、`eventType`）。cron service 订阅时把目录的 `stale_after` 带成 subscribe 参数 `staleAfter`，是同一个量的两种拼写，不是两个参数。
- 事件类型：`group.noun_verb`，小写点号分组、下划线连词，如 `geofence.enter`、`phone.call_incoming`、`device.battery_low`。
- 成对事件：`_on / _off`（开关类）、`_connected / _disconnected`（连接类）、`enter / exit`（围栏）、`locked / unlocked`、`plugged_in / plugged_out`。
- 一次性变更：`_changed`，payload 带新值（必要时带 `previous`）。
- 电话状态用 `call_incoming / call_outgoing / call_answered / call_ended / call_missed`（原稿 `call_received` 改为 `call_incoming`）。
- key 字段命名：`contact_id`、`package_name`、`device_addr`、`bssid`、`zone`、`event_id`（日历）。显示名字段（`contact_name`、`app_name`、`device_name`、`ssid`）保留在 payload 供 message 使用，但**编译期优先用 key 字段写 filter**。
- 位置类事件不暴露经纬度给模型：`latitude / longitude` 归 internal（只在推送信封 payload 里出现，模型看到的目录不列出、filter 不能用）。

## 5. 填槽解析工具（编译期，主 loop 可见，只读）

| 工具 | 输入 | 输出 | 用途 |
|---|---|---|---|
| `contacts.search(q)` | 姓名 / 昵称 / 号码片段 | `[{contact_id, name, numbers[]}]` | `phone.* / sms.received` 的 `contact_id` |
| `apps.list(q?)` | 名称片段 | `[{package_name, app_name}]` | `app.* / notification.*` 的 `package_name` |
| `bluetooth.paired()` | — | `[{device_addr, device_name, type}]` | `bluetooth.device_*` 的 `device_addr` |
| `places.list()` | — | `[{zone, label}]` | `geofence.*` 的 `zone` |

运行期（trigger 脚本 / 判定 agentTurn / 动作 agentTurn）只读工具：

| 工具 | 返回 | 用途 |
|---|---|---|
| `phone_state.get(fields[])` | `{screen, locked, battery, charging, dnd, ringer, airplane, wifi{connected, ssid, bssid}, bluetooth{on, devices[]}, headset, zones[], activity, foreground_app}` | 组合条件的"状态门"（T1），判定 prompt 里的现况查询 |

## 6. 内建条目（10 组 63 条）

列说明：**字段**中 `!` 前缀 = key 字段；**必约束** = must_filter；**internal** 列为 `rate / debounce / stale_after / sensitivity`，模型不可见。

### 6.1 device（10）

| type | desc | 字段 | 必约束 | pair / state_query | internal |
|---|---|---|---|---|---|
| `device.screen_on` | 屏幕亮起 | — | — | pair `device.screen_off`；state `screen` | high / 30s / 2m / none |
| `device.screen_off` | 屏幕熄灭 | — | — | pair `device.screen_on` | high / 30s / 2m / none |
| `device.locked` | 设备锁定 | — | — | pair `device.unlocked`；state `locked` | high / 30s / 2m / none |
| `device.unlocked` | 设备解锁 | `method: enum[pin, biometric, none]` | — | pair `device.locked` | high / 30s / 2m / none |
| `device.battery_low` | 电量低于阈值 | `level: number 0–100` | — | pair `device.battery_okay`；state `battery` | low / 10m / 30m / none |
| `device.battery_okay` | 电量恢复 | `level: number 0–100` | — | pair `device.battery_low` | low / 10m / 30m / none |
| `device.charging` | 开始充电 | `source: enum[ac, usb, wireless]` | — | pair `device.discharging`；state `charging` | mid / 1m / 10m / none |
| `device.discharging` | 停止充电 | `level: number 0–100` | — | pair `device.charging` | mid / 1m / 10m / none |
| `device.shutdown` | 设备即将关机 | `reason: enum[user, low_battery, system]` | — | pair `device.boot` | low / — / 5m / none |
| `device.boot` | 设备开机完成 | — | — | pair `device.shutdown` | low / — / 5m / none |

### 6.2 setting（17）

| type | desc | 字段 | 必约束 | pair / state_query | internal |
|---|---|---|---|---|---|
| `setting.airplane_mode_on` | 飞行模式开 | — | — | pair `_off`；state `airplane` | low / 1m / 10m / none |
| `setting.airplane_mode_off` | 飞行模式关 | — | — | pair `_on` | low / 1m / 10m / none |
| `setting.dnd_on` | 免打扰开 | `mode: enum[priority, alarms, total]`，`until: datetime\|null` | — | pair `_off`；state `dnd` | low / 1m / 10m / none |
| `setting.dnd_off` | 免打扰关 | — | — | pair `_on` | low / 1m / 10m / none |
| `setting.ringer_changed` | 铃声模式变化 | `mode: enum[normal, vibrate, silent]`，`previous: enum` | — | state `ringer` | mid / 1m / 10m / none |
| `setting.brightness_changed` | 亮度变化 | `level: number 0–100`，`auto: boolean` | — | — | high / 5m / 10m / none |
| `setting.volume_changed` | 音量变化 | `stream: enum[ring, media, alarm, call]`，`level: number 0–100` | `stream` | — | high / 1m / 10m / none |
| `setting.dark_mode_on` | 深色模式开 | — | — | pair `_off` | low / 1m / 10m / none |
| `setting.dark_mode_off` | 深色模式关 | — | — | pair `_on` | low / 1m / 10m / none |
| `setting.location_on` | 定位服务开 | — | — | pair `_off` | low / 1m / 10m / none |
| `setting.location_off` | 定位服务关 | — | — | pair `_on` | low / 1m / 10m / none |
| `setting.hotspot_on` | 热点开 | — | — | pair `_off` | low / 1m / 10m / none |
| `setting.hotspot_off` | 热点关 | — | — | pair `_on` | low / 1m / 10m / none |
| `setting.nfc_on` | NFC 开 | — | — | pair `_off` | low / 1m / 10m / none |
| `setting.nfc_off` | NFC 关 | — | — | pair `_on` | low / 1m / 10m / none |
| `setting.power_saving_on` | 省电模式开 | — | — | pair `_off` | low / 1m / 10m / none |
| `setting.power_saving_off` | 省电模式关 | — | — | pair `_on` | low / 1m / 10m / none |

### 6.3 connectivity（13）

| type | desc | 字段 | 必约束 | pair / state_query | internal |
|---|---|---|---|---|---|
| `bluetooth.on` | 蓝牙开 | — | — | pair `bluetooth.off`；state `bluetooth.on` | low / 1m / 10m / none |
| `bluetooth.off` | 蓝牙关 | — | — | pair `bluetooth.on` | low / 1m / 10m / none |
| `bluetooth.device_connected` | 蓝牙设备已连接 | `!device_addr: string`，`device_name: string`，`type: enum[audio, wearable, car, input, other]` | — | pair `bluetooth.device_disconnected`；state `bluetooth.devices` | mid / 30s / 5m / none |
| `bluetooth.device_disconnected` | 蓝牙设备已断开 | `!device_addr`，`device_name`，`type` | — | pair `bluetooth.device_connected` | mid / 30s / 5m / none |
| `wifi.on` | WiFi 开 | — | — | pair `wifi.off`；state `wifi` | low / 1m / 10m / none |
| `wifi.off` | WiFi 关 | — | — | pair `wifi.on` | low / 1m / 10m / none |
| `wifi.connected` | 连上 WiFi | `ssid: string`，`!bssid: string` | — | pair `wifi.disconnected`；state `wifi.ssid` | mid / 1m / 10m / location |
| `wifi.disconnected` | WiFi 断开 | `ssid`，`!bssid` | — | pair `wifi.connected` | mid / 1m / 10m / location |
| `headset.plugged_in` | 耳机接入 | `headset_type: enum[wired, usb_c, bluetooth]` | — | pair `headset.plugged_out`；state `headset` | mid / 10s / 2m / none |
| `headset.plugged_out` | 耳机拔出 | `headset_type` | — | pair `headset.plugged_in` | mid / 10s / 2m / none |
| `usb.connected` | USB 已连接 | `mode: enum[charge, mtp, ptp, tether]` | — | pair `usb.disconnected` | mid / 10s / 2m / none |
| `usb.disconnected` | USB 已断开 | — | — | pair `usb.connected` | mid / 10s / 2m / none |
| `network.type_changed` | 网络类型变化 | `type: enum[wifi, 5g, 4g, 3g, none]`，`previous: enum` | — | — | high / 1m / 5m / none |

### 6.4 geofence（2）

| type | desc | 字段 | 必约束 | pair / state_query | internal |
|---|---|---|---|---|---|
| `geofence.enter` | 进入地理围栏 | `!zone: string`，`confidence: number 0–1` | `zone` | pair `geofence.exit`；state `zones` | low / 5m / 10m / location |
| `geofence.exit` | 离开地理围栏 | `!zone`，`confidence` | `zone` | pair `geofence.enter` | low / 5m / 10m / location |

internal 额外字段：`latitude / longitude` 出现在推送 payload 中，但不在可见 `fields` 里，filter 不能引用。

### 6.5 activity（1）

| type | desc | 字段 | 必约束 | pair / state_query | internal |
|---|---|---|---|---|---|
| `activity.changed` | 运动状态变化 | `activity: enum[still, walking, running, cycling, in_vehicle]`，`previous: enum`，`confidence: number 0–1` | `activity` | state `activity` | high / 2m / 5m / none |

### 6.6 phone（6）

| type | desc | 字段 | 必约束 | pair / state_query | internal |
|---|---|---|---|---|---|
| `phone.call_incoming` | 来电响铃 | `!contact_id: string\|null`，`contact_name: string\|null`，`phone_number: string`，`is_video: boolean` | — | — | mid / — / 1m / contacts |
| `phone.call_outgoing` | 去电拨出 | `!contact_id`，`contact_name`，`phone_number` | — | — | mid / — / 1m / contacts |
| `phone.call_answered` | 来电已接听 | `!contact_id`，`contact_name`，`phone_number` | — | — | mid / — / 1m / contacts |
| `phone.call_ended` | 通话结束 | `!contact_id`，`contact_name`，`phone_number`，`duration: number 秒`，`direction: enum[in, out]` | — | — | mid / — / 5m / contacts |
| `phone.call_missed` | 未接来电 | `!contact_id`，`contact_name`，`phone_number` | — | — | mid / — / 30m / contacts |
| `sms.received` | 收到短信 | `!contact_id: string\|null`，`phone_number: string`，`text: string` | — | — | mid / — / 10m / content |

### 6.7 alarm（3）

| type | desc | 字段 | 必约束 | pair / state_query | internal |
|---|---|---|---|---|---|
| `alarm.fired` | 闹钟响起 | `alarm_id: string`，`label: string\|null`，`scheduled_at: datetime` | — | — | low / — / 2m / none |
| `alarm.dismissed` | 闹钟被关闭 | `alarm_id`，`label` | — | — | low / — / 5m / none |
| `alarm.snoozed` | 闹钟被推迟 | `alarm_id`，`label`，`snooze_until: datetime` | — | — | low / — / 5m / none |

### 6.8 app（5）

| type | desc | 字段 | 必约束 | pair / state_query | internal |
|---|---|---|---|---|---|
| `app.opened` | 应用进入前台 | `!package_name: string`，`app_name: string` | `package_name` | pair `app.closed`；state `foreground_app` | burst / 30s / 2m / none |
| `app.closed` | 应用离开前台 | `!package_name`，`app_name`，`duration: number 秒` | `package_name` | pair `app.opened` | burst / 30s / 2m / none |
| `app.installed` | 应用已安装 | `!package_name`，`app_name`，`version: string` | — | — | low / — / 30m / none |
| `app.uninstalled` | 应用已卸载 | `!package_name`，`app_name` | — | — | low / — / 30m / none |
| `app.updated` | 应用已更新 | `!package_name`，`app_name`，`version`，`previous_version: string` | — | — | low / — / 30m / none |

### 6.9 calendar（3）

| type | desc | 字段 | 必约束 | pair / state_query | internal |
|---|---|---|---|---|---|
| `calendar.event_starting` | 日程即将开始 | `!event_id: string`，`title: string`，`start_time: datetime`，`end_time: datetime`，`location: string\|null`，`lead_minutes: number` | — | pair `calendar.event_ended` | mid / — / 5m / content |
| `calendar.event_ended` | 日程结束 | `!event_id`，`title`，`end_time` | — | pair `calendar.event_starting` | mid / — / 10m / content |
| `calendar.reminder` | 日程提醒触发 | `!event_id`，`title`，`start_time`，`location` | — | — | mid / — / 5m / content |

### 6.10 notification（3）

| type | desc | 字段 | 必约束 | pair / state_query | internal |
|---|---|---|---|---|---|
| `notification.posted` | 收到通知 | `!package_name: string`，`app_name: string`，`title: string\|null`，`text: string\|null`，`category: enum[message, email, social, promo, system, other]` | `package_name` 或 `category` | pair `notification.removed` | burst / 10s / 5m / content |
| `notification.removed` | 通知被移除 | `!package_name`，`app_name`，`notification_id: string` | `package_name` | pair `notification.posted` | burst / 10s / 5m / none |
| `notification.clicked` | 通知被点击 | `!package_name`，`app_name`，`title` | `package_name` | — | mid / — / 5m / content |

## 7. 相对原稿的改动清单

| 原稿 | 定稿 | 原因 |
|---|---|---|
| `phone.call_received` | `phone.call_incoming` | 与 `call_outgoing / call_answered` 同一动词族 |
| `bluetooth.state_on/off`、`wifi.state_on/off` | `bluetooth.on/off`、`wifi.on/off` | 去掉冗余 `state_` |
| `setting.ringtone_changed{mode}` | `setting.ringer_changed{mode, previous}` | ringtone 是铃声文件，ringer 才是模式 |
| `setting.dnd_mode_on/off` | `setting.dnd_on/off` | 与其他开关同形 |
| `geofence.*{zone, latitude, longitude, confidence}` + `subscribe_params{zone}` | `fields: zone!, confidence`；`must_filter: [zone]`；经纬度 internal | 用 filter 统一表达"参数"，位置不暴露给模型 |
| `phone.call_ended{duration}` 只有时长 | 加 `direction` | 区分来电 / 去电结束 |
| 无 | `sms.received`、`activity.changed`、`network.type_changed`、`device.boot`、`device.unlocked.method` | 补常见触发源与成对事件 |
| payload 含 `occurred_at` | 移到推送信封 | 每条事件都有，不是 payload 语义 |
| `notification.posted` 无约束 | `must_filter: package_name 或 category` | burst 级频率，裸订阅会淹没 job |
| 无 internal | `rate / debounce / stale_after / sensitivity` | 订阅卫生参数从模型手里收回，由 cron service 按目录带上 |
