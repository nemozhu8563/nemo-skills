# Site Telemetry Workflow

## Completion definition

本 Skill 的“接入完成”不是单一布尔值。对用户请求的每个组件，必须报告当前最高证据层：

- GA4：资源/stream 与代码已配置 → 生产请求已观察 → Realtime 或 DebugView 已读回。
- Clarity：project/tag 已配置 → tag 与 `/collect` 已观察 → Recordings/Dashboard 已读回。
- GSC：property 与验证材料已配置 → DNS/ownership 已验证 → sitemap 已读回；索引证据另算。

如果用户只要求其中一个组件，只完成并报告该组件。未请求组件使用 `not_requested`，不得把“一站式”理解为自动扩大外部写入范围。

## 0. First-use readiness gate

首次使用本 Skill 或切换到一个新目标站点时，第一项可观察动作必须是只读 readiness 检查。它先于登录、代码修改、provider 配置、API bootstrap 和任何外部写入，并把结果写入最终输出的 `readiness_check`。

至少检查并区分：

1. 本地能力：Python 3.11+、项目原生命令；选择 Google API 模式时再检查 `gcloud`、CLI active identity、ADC、精确 Cloud project/quota project 与三项 API service 状态；
2. 站点身份：production origin/canonical、preview/local、技术栈、部署目标、现有 IDs/脚本、robots/sitemap 与 CMP/consent；
3. provider 身份：目标 GA4 account/property、Clarity organization/project、GSC property，以及当前浏览器/API 身份是否一致；
4. 会话需求：Google 浏览器、Microsoft Clarity 浏览器、DNS provider 与部署平台分别写 `available`、`reauth_required`、`not_required` 或 `not_checked`；
5. 权限与证据：能否读取目标资源、缺失的是 scope 还是 resource role、哪些检查尚无证据。

readiness 不自动发起 OAuth、登录、切换账号、授权、启用 API 或创建资源。无法安全检查的项目保留 `not_checked`/`missing_evidence`；任何 target identity、consent、project 或权限 blocker 都先进入输出。

## 1. Restore before acting

从任务上下文、仓库、部署平台、浏览器和 provider 恢复：

- canonical production origin、www/http 跳转与所有 preview/local origin；
- 构建框架、HTML 注入点、环境变量和 analytics 配置来源；
- 已存在的 GA4 account/property/web stream/Measurement ID；
- 已存在的 Clarity organization/project/Project ID；
- 已存在或待验证的 GSC property、DNS TXT、Owner 与 sitemap；
- CMP、cookie banner、Consent Mode 与隐私政策的既有决定；
- 当前部署 revision、打开的 provider tab 和中断前写操作。

连接中断不表示业务状态丢失。任何不确定写入先做 read-after-write。

## 2. Read-only site preflight

至少检查：

1. production origin 为精确 HTTPS origin，不含路径、查询或尾部歧义；
2. canonical、重定向和站内绝对 URL 一致；
3. preview/local/branch 域名清单已识别；
4. 页面现有 GA4/Clarity/GTM 脚本、公开 IDs 与重复注入；
5. robots.txt 与 sitemap 的公网状态（仅 GSC 请求时强制）；
6. 站点是否已有 CMP/consent callback；
7. 构建产物是否可能在多个 hostname 复用；
8. 当前 provider 账号/组织是否与目标站点精确匹配。

账号、organization、zone 或 production origin 不匹配时停止外部写入，不选择“最像的”资源。

若任务需要 GSC/GA4 provider readback，先选择证据面：已满足 Google API bootstrap 时优先受控 adapter；需要 DebugView、Clarity、ownership/DNS 或 association 时使用 browser；两者组合使用 `mixed`。API unavailable 只改变执行面，不改变用户授权或 target identity。

## 3. Write the exact configuration plan into the report

在任何外部写入前，为 `ga4`、`clarity`、`gsc` 每个组件把配置方案写入用户可见的 `configuration_plan`；未请求组件也明确写 `not_requested`。每个组件固定记录：

- `desired_resource`：精确名称、站点 URL/域名与目标账号；
- `existing_matches`：精确匹配的 property/stream/project/property；
- `action`：`existing`、`created`、`resumed` 或 `blocked`；
- `external_write`：需要创建/更新的最小集合；
- `readback`：写后必须从哪里读取；
- `rollback`：能否仅回滚代码、是否影响 ownership/历史数据。

同一站点已有精确资源时复用。相似名称、不同域名或不同组织不能自动复用。

配置方案描述“准备做什么”，不是完成证据。执行后必须按 provider readback 更新 `existing_matches`、`action` 和剩余写入；未知目标或权限写为 blocker，不能用内部推理或按钮点击填成已完成。

选择 `google_api` 或 `mixed` 时，同一份 `configuration_plan` 还必须包含 `google_api_bootstrap`：`auth_mode`、精确 `cloud_project`/`quota_project`、最小 capabilities/scopes、required services、resource permissions、是否需要 interactive login、外部写入、回读和回滚。缺少任一精确值时保持 blocked，不生成猜测命令。

## 4. Implement production isolation

优先实现两道门：

1. 构建时：只有规范化后的 build origin 与 production origin 完全相等，才把 GA4/Clarity block 写入 HTML。
2. 运行时：在创建远程 script 或发送请求之前，再比较 `window.location.origin` 或精确 hostname。

正向和负向都要可自动校验：

- production build 恰好包含一个预期 marker、一个目标 ID 配置和批准的远程脚本；
- local/preview build 不含 marker、IDs、`googletagmanager.com`、`clarity.ms/tag` 或其他未批准远程统计脚本；
- 如果框架不支持静态移除，报告 bundle 残留，并证明 runtime gate 在网络动作之前执行。

## 5. Apply consent decisions

Consent Mode 的值必须来自已确认的用户选择/CMP/站点政策，而不是 Skill 示例。

- GA4：先设置 consent default，再发送 config/event；选择变化时 update。
- Clarity：使用 `consentv2` 传递 `ad_Storage` 与 `analytics_Storage`。
- 广告用途未请求时，GA4 的 `ad_storage`、`ad_user_data`、`ad_personalization` 与 Clarity 的 `ad_Storage` 默认 `denied`。
- `analytics_storage`/`analytics_Storage` 没有明确决策时，不假定 `granted`。

本 Skill 只执行已确定的技术策略，不判断某地区法律是否允许。

## 6. Build and local verification

使用项目已有命令，不引入新的构建依赖。至少执行：

- production-like build + 项目检查；
- local/default build + 项目检查；
- 对生成 HTML 做目标 marker/ID/remote-script 正负断言；
- 现有 lint/typecheck/test 中与改动相关的检查。

公开 ID 可以出现在 production HTML；任何 token、cookie 或 verification value 出现在构建产物都视为失败。

## 7. Deploy and browser verification

只有用户已授权当前部署/上线动作时才部署；代码接入授权不自动等于部署授权。

部署后分别验证：

- production：脚本数量、目标 ID、runtime gate、实际请求；
- preview：没有 GA4/Clarity 远程请求；
- 控制台：无重复初始化与明显 runtime error；
- network：记录 endpoint、status、initiator、页面 origin 与时间，不保存 cookie/header 凭据。

## 8. Provider readback

### GA4

- Admin/Data API 可读取 exact property/stream 与有限 Realtime；API Realtime 只更新 `ga4.realtime`，不能写 `ga4.debugview=verified`。
- Realtime：近期活动/事件已在目标 property/stream 中出现；官方说明为 best-effort，无正式 SLO。
- DebugView：开启 debug mode 后目标设备事件被接收；它不证明普通生产流量完整性。
- 两者都缺失时，保留 network 证据并标记 `pending` 或 `missing_evidence`。

### Clarity

- tag 代码存在和脚本 loaded 分开记录；
- Network 中 `POST https://www.clarity.ms/collect` 是 transport 证据；
- Recordings/Dashboard 或 live users 是 provider 端证据；
- collect 出现但后台无数据时，不把 recording 写成 verified。

### GSC

- provider + 两个公共解析器匹配后再 Verify；
- GSC 显示 verified 且 Owner 后再处理 sitemap；
- 先解析 sitemap `operation_mode`：状态查询与用户手动提交后的检查只做 list/get；明确提交或 GSC 接入授权才允许在确认缺失后 submit 一次；
- sitemap 在列表/API 中读回后才写 submitted/existing；提交后超时或浏览器中断必须先 list/get，不能盲目重提；
- 抓取和索引必须有单独 GSC/URL Inspection 证据。
- URL Inspection API 只读取 exact URL 当前状态，不调用 Indexing API；sitemap apply 只能来自安全 plan，status/manual 模式无法生成计划。

## 9. Recovery paths

### Provider UI or browser disconnected

1. 检查宿主浏览器控制面；沙箱 localhost 失败不能单独证明 CDP 未开启。
2. 恢复已有 tab、property、project 和 challenge。
3. 从 provider 读取写入结果。
4. 仅在确认资源不存在后重试创建。

### Google API unavailable or ambiguous

1. 普通 readback 不隐式 enable API、安装 gcloud、启动 OAuth 或扩大 scope。
2. 一般 403 同时保留 scope/resource role 为 unknown，先分别核验，不猜账号。
3. GSC submit timeout/5xx 后第一步 exact get/list；仍 absent 才评估一次全新 recovery plan。
4. GA4 create timeout/5xx 只回读候选，永不自动 replay；property 已创建而 stream 未确认时保留 partial external state。
5. API/browser identity 冲突时 blocked，不选择“更方便”的证据覆盖另一边。

### Production request exists, provider data absent

- 确认目标公开 ID、页面 origin、consent 状态、过滤规则与 provider property；
- 保留请求时间；
- 按 provider 的实时报告重新读回；
- 传播窗口内写 `pending`，不创建第二个资源或第二套脚本。

### Preview sends telemetry

- 视为发布阻断；
- 定位 build-time gate、runtime gate 或共享 bundle；
- 修复并重新验证 production-positive + preview-negative；
- 不通过 provider filter 掩盖错误注入。

## 10. Final report

最终报告必须包含 `SKILL.md` 的全部 output contract 字段，包括用户可见的 `readiness_check` 与逐组件 `configuration_plan`，以及 `checked_at`、证据来源、未执行原因和下一步。provider UI/API 未读回时，明确写 `missing evidence`，不能把本地测试通过表述为端到端完成。
