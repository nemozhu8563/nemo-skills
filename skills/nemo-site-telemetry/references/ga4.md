# GA4 Onboarding And Verification

## Resource discovery

1. 确认目标 Google account/organization 与 production origin。
2. 查找精确匹配的 GA4 property 与 Web data stream；优先复用，不能按相似名称猜测。
3. 只有不存在精确资源且用户已要求接入时才创建。
4. 创建/恢复后从 provider 读取 Web stream URL 与 Measurement ID；最终报告可显示掩码后的 ID 或只记录 matched。

Measurement ID 会出现在前端 `gtag.js?id=...` 和请求中，不是认证密钥。它也不能证明操作者拥有 GA4 property。

## Code contract

官方 gtag.js 基本顺序包含：加载 Google tag、初始化 data layer、`gtag('js', new Date())`、`gtag('config', TAG_ID)`。本 Skill 在此基础上增加本地治理：

- build-time exact production-origin gate；
- runtime exact origin/hostname guard；
- consent default 在 config/event 前；
- 只注入一次，不与 GTM 或其他插件重复；
- local/preview 不输出 tag、ID 或远程脚本。

如果项目使用 GTM、框架官方插件或 CMP 集成，应沿用现有控制面，不额外手写第二套 gtag。

## Consent

- `analytics_storage` 控制 analytics storage。
- `ad_storage` 控制广告 storage。
- `ad_user_data` 与 `ad_personalization` 是额外广告同意参数。
- 广告未请求时后三项默认 `denied`。
- `analytics_storage` 必须来自实际 CMP/站点策略；没有决定时标记 blocked，而不是静默 granted。
- 用户选择改变后调用 consent update。

## Evidence ladder

1. `ga4.setup`：精确 property/stream 已 existing/created/resumed，代码与 production build 读回一致。
2. `ga4.production_request`：从 production origin 观察到目标 Google endpoint 请求；记录时间、origin、initiator 与公开 ID matched，不保存 cookie/header。
3. `ga4.realtime`：目标 property 的 Realtime 显示近期用户/事件。Realtime 是 best-effort，可能延迟或中断，不具正式 SLO。
4. `ga4.debugview`：开启 debug mode 后，目标设备事件出现在 DebugView。DebugView 只证明调试事件接收。

Network 请求不能代替 Realtime/DebugView；Realtime/DebugView 也不能单独证明当前部署 revision 或 preview 隔离。两类证据都要与 production origin 和部署版本关联。

## Google API adapter

- Analytics Admin API 读取 account summaries、exact property 与 Web data streams；resource identity 使用 `accounts/{id}`、`properties/{id}`、`properties/{id}/dataStreams/{id}`，display name 只展示、不单独决定匹配。
- Analytics Data API `runRealtimeReport` 只开放 `activeUsers`、`eventCount`、`screenPageViews` 三个 telemetry 验证 metric；成功结果只能写 `ga4.realtime` 和 `readback_surface=api|mixed`。
- DebugView 没有被本 adapter 的 Realtime 调用覆盖；`ga4.debugview` 仍需 GA4 DebugView UI 的独立 browser evidence。
- property/stream 创建只在 account ID、production origin、display name、IANA time zone 与 currency 都由当前任务明确提供时进入 plan。不能猜账号、时区、币种或 origin。
- create apply 前重新扫描 exact origin；已有一个匹配则 noop，多个匹配则 blocked。property/stream POST 结果 ambiguous 时只回读，永不自动 replay；部分成功必须记录 `partial_external_state`。
- adapter 不创建 Analytics account、不授予用户权限、不 patch/delete property 或 stream，也不自动建立 GA4↔GSC association。

## Failure modes

- 请求存在但 Realtime 无数据：检查 ID、consent、filter、stream、请求响应与读取的 property，不重复创建。
- 两个 page_view：检查重复 gtag/GTM/plugin 注入。
- preview 污染：修复 origin gate，不依赖报表过滤器掩盖。
- DebugView 无事件：确认 debug mode 与 consent；不要用普通 Realtime 事件冒充 DebugView。
- Admin/Data API 与浏览器显示不同账号/property：停止写入并分别回读身份，不按相似名称选一个继续。
