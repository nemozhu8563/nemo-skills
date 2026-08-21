---
name: nemo-supabase-auth
description: "Governed setup, audit, repair, and end-to-end verification of Supabase Google Auth for a web project. Use when Nemo asks to create or reuse the exact Google Cloud project and OAuth Web application, configure Google Auth Platform branding/audience/scopes, enable the Supabase Google provider, set Site URL and Redirect URLs, implement or validate a PKCE callback with exchangeCodeForSession, or prove a real Google sign-in and protected session. Also use for redirect_uri_mismatch, provider-disabled, callback, or login-loop diagnosis in a Supabase Google OAuth flow. Prefer a compatible existing project/client over duplicates. Do not trigger for generic Supabase database work, non-Google identity providers, unrelated Google APIs, explanation-only OAuth questions, pentesting, or any request to paste or export credentials."
---

# Nemo Supabase Auth

为一个明确的 Web 项目配置、审计或修复 Supabase Google Auth，并用真实浏览器登录和受保护会话证明结果。Google Cloud、Supabase Dashboard、应用代码和真实用户会话是四条独立证据链；任何一个绿色状态都不能代替端到端验收。

## Activation Gate

1. 锁定唯一 `project_dir`、环境、Supabase organization/project、Google account/organization、生产 origin 和本地/预览 origin。身份、项目或环境有歧义时只读发现，不创建资源、不改配置。
2. 先审计已有 Google Cloud project、OAuth Web client、Supabase provider、Site URL、Redirect URLs 和应用 callback。兼容配置优先复用；只有用户明确要求新建，或证明没有兼容资源，才创建新 project/client。
3. 分开记录七个动作：`application_code`、`google_cloud_project`、`google_auth_configuration`、`google_oauth_client`、`supabase_google_provider`、`supabase_url_configuration`、`real_login_test`。登录状态不等于 mutation 授权。
4. 用户明确要求“为当前项目完成 Google 登录配置”时，可把为该精确项目所必需的代码和 provider 配置视为在范围内；新建 Google Cloud project、发布 OAuth app、扩大 scopes、启用 billing、创建真实用户、删除资源仍须有对应的明确授权或现有指令证据。
5. 不读取、索取或保存 Client secret、OAuth code、token、Cookie、session identifier、测试账号邮箱、Supabase user ID 或浏览器存储。需要 secret 的字段由用户直接填入已确认的 provider UI 或批准的 secret store，agent 不经手其值。

## Required Inputs

- `project_dir` 和环境：`local`、`preview` 或 `production`。
- 当前应用的生产 origin、callback route、受保护的成功信号，以及需要支持的本地/预览 origin。
- 精确 Supabase organization、project name、project ref 和当前 Auth URL 配置；报告可以使用 project alias，不公开私人标识。
- 精确 Google account/organization 与计划复用或新建的 Google Cloud project、OAuth client。
- Google audience：Workspace internal 或 external；external 是否保持 Testing、需要哪些测试用户、是否真的要发布到 Production。
- 本次七个动作各自的 authorization；`not_required` 必须同时说明原因。

无法从代码、当前 Dashboard 状态或用户指令安全推导的分支只问一个必要问题，不静默选择 audience、发布状态、生产域名或用户身份。

## Current-Source Gate

在 provider mutation 前重新检查当前 Supabase Google login guide、Redirect URLs guide 和 Auth changelog。用 `supabase:supabase` 处理 Supabase 当前行为；Dashboard/UI 需要联网时按 `web-access:web-access` 的安全边界执行。官方链接和本次复核日期记录在 [official sources](references/official-sources.md)。

Google Console 页面名称和按钮会变化。以当前 provider UI 与官方资料为准，不把本 Skill 的示例标签当成实时事实。若 Google 官方资料无法读取，把它记为 `missing_evidence`，使用 Supabase 当前官方指南与 live provider readback 限定动作，不编造点击路径。

## URL Matrix: Never Conflate The Two Callbacks

先生成并人工复核下表，再改任何 provider：

| Surface | 允许的值 | 禁止混入 |
|---|---|---|
| Google Authorized JavaScript origins | 当前 Supabase 指南要求的纯 origin；Hosted 项目通常为 `https://<project-ref>.supabase.co`，本地栈按当前本地 Supabase origin | 路径、query、fragment、应用 callback route |
| Google Authorized redirect URIs | Supabase provider callback：`https://<project-ref>.supabase.co/auth/v1/callback` | 应用 `/auth/callback`、站点首页、通配符 |
| Supabase Site URL | 生产应用 origin，例如 `https://app.example.com` | Supabase provider callback |
| Supabase Redirect URLs | 应用 callback，例如 `https://app.example.com/auth/callback` 与明确需要的本地/预览 callback | Google 的 Supabase provider callback |
| App `redirectTo` | 上一行 allowlist 内的精确应用 callback | 未登记 URL、外部任意 `next`、带 OAuth code 的完整回调 |

- Google origins 只能是 origin；Hosted flow 不因为应用运行在某个 origin 就自动把它加入 Google 列表，必须遵循当前 Supabase/Google 契约。
- 生产 URL 使用精确 path。通配符只用于确有必要的本地或 preview 部署，并限制到最窄 host/path；生产不使用宽泛 wildcard。
- Supabase Site URL 是没有 `redirectTo` 时的默认目标，不是所有 callback 的替代品。
- `redirect_uri_mismatch` 必须比较浏览器请求实际发送的 redirect URI 与 Google client 当前回读值，逐字符检查 scheme、host、port、path 和尾斜杠。

## Compact Workflow

1. **建立脱敏基线。** 记录 Git revision/dirty state、auth SDK/SSR helpers、登录入口、callback route、protected route、环境、现有 provider/client 数量与每个动作的 before snapshot。只记录别名、状态和证据 pointer，不记录用户或凭证数据。
2. **审计与复用。** 在精确 Google account/organization 下查找与当前应用对应的 project 和 Web client；在 Supabase 查 Google provider、Site URL 与 redirect allowlist。名称相近但归属或 callback 不一致时标为冲突，不猜测、不重复创建。
3. **验证代码路径。** 确认 `signInWithOAuth({ provider: 'google', options: { redirectTo } })` 使用 URL matrix 中的应用 callback。PKCE/SSR callback 必须读取一次性 `code`、调用 `exchangeCodeForSession(code)`、处理失败，并在服务器端用可信的 `getUser()` 或等价当前官方方法验证用户。
4. **封闭 `next`。** `next` 只能是以单个 `/` 开头的站内相对路径；拒绝 `//host`、绝对 URL、反斜杠和编码后可逃逸的值。默认回到固定安全页面。
5. **配置 Google Auth。** 精确确认 project 后，只设置完成登录所需的 branding、audience 和 `openid`、email、profile scopes。External Testing 的测试用户由用户在 provider UI 直接选择；不记录邮箱。不要顺带启用无关 Google API、offline access、billing 或 Production publication。
6. **创建或更新 Web client。** client type 必须是 Web application。先保存现有 origins/redirects 快照，再做一个最小变更并回读。Client ID 可作为 provider 标识使用；Client secret 由用户直接从 Google UI 填到 Supabase UI，agent 不复制、不回显、不截图。
7. **配置 Supabase。** 在精确 project 启用 Google provider，写入 client ID 和用户直接输入的 secret；再单独配置 Site URL 与 Redirect URLs。Provider enable 与 URL allowlist 是两个 mutation，分别回读。
8. **运行真实登录。** 先告知该步骤可能产生 Google consent grant、Supabase user 和 session。只有授权后才在真实浏览器执行；不检查 Cookie/localStorage。登录完成后验证 callback chain、最终站内 URL、服务端用户信号与一个受保护页面。
9. **收尾。** 登出测试会话；如用户要求撤销 consent、删除测试用户或删除多余 OAuth client，把每项作为新的 destructive mutation 单独授权。默认保留成功配置，不自动清理真实用户或 provider 资源。

框架差异、Dashboard 顺序和失败诊断见 [runbook](references/runbook.md)。证据与回滚要求见 [evidence and rollback](references/evidence-and-rollback.md)。

## Mutation Protocol

每个外部或代码写入动作都执行相同协议：

1. 解析精确 account/organization/project/environment/route 与期望值。
2. 保存最小 before snapshot 和精确 rollback action；secret 字段只记录 `present` / `absent`，不读取值。
3. 把用户指令映射到该动作的 authorization，不能用“已登录”或“前一个动作已授权”替代。
4. 一次只做一个最小 mutation。
5. 立即从同一 provider 或文件做 readback；再进入下一动作。
6. 记录时间、target alias、前后状态、证据 pointer、rollback 状态和 `missing_evidence`。

禁止 blind overwrite、创建名称相似的重复 project/client、用截图猜配置、批量扩大 redirect wildcard、自动发布 OAuth app、自动启用 billing、无差别重试，以及用 HTTP 200 或 Dashboard `Enabled` 冒充真实登录。

## Application Contract

- 浏览器发起 OAuth；服务器 callback 完成 code exchange。不要把 service-role key 放入浏览器。
- SSR 场景沿用项目现有 Supabase server/client helpers 和 cookie adapter，不另造 auth abstraction。
- callback 失败要返回无敏感信息的稳定错误页或受控重定向；日志不得包含 request URL query、OAuth code、token、Cookie 或个人标识。
- `getSession()` 只说明本地 session 数据存在；服务端授权判定使用当前官方推荐的可信用户/claims 校验，不把可篡改的客户端数据当身份事实。
- 保留项目既有登录方式。除非用户明确要求，不自动链接账号、迁移用户、修改 RLS、增加角色或改变注册策略。

## Verification Ladder

按顺序取证，失败就停在该层：

1. `source_verified`：当前官方 Supabase docs/changelog 已复核，或缺失证据已明确。
2. `code_preflight`：登录入口、精确 `redirectTo`、PKCE exchange、相对 `next` 和 protected signal 通过静态/项目测试。
3. `url_matrix_verified`：Google origin、Google Supabase callback、Supabase Site URL、Supabase app callbacks 逐项不混淆。
4. `provider_readback`：Google project/client/audience/scopes 与 Supabase provider/URLs 从精确目标回读一致。
5. `browser_login_started`：Google account chooser/consent 来自预期 client；这一步仍不能证明成功。
6. `callback_completed`：Google → Supabase provider callback → app callback 链条完成，无 mismatch 或 loop。
7. `trusted_user_verified`：服务端可信方法返回当前已认证用户的布尔成功信号；报告不包含 email 或 user ID。
8. `protected_route_verified`：受保护页面或 API 成功，登出后再次访问被拒绝或重定向。

只有第 1–4 层通过才能声明 `configuration_ready=true`；只有第 1–8 层全部通过且 `missing_evidence` 为空，才能声明 `end_to_end_verified=true`。

## Secret And Privacy Boundary

永远不要把下列数据放进聊天、报告、fixture、源码、命令参数、shell history、截图、录屏、日志或 PR：

- Google Client secret、Supabase service-role key 或任何 password/private key
- OAuth authorization code、access/refresh/ID token、Bearer header
- Cookie、session identifier、浏览器 profile、localStorage/sessionStorage dump
- 真实邮箱、测试用户列表、Supabase user ID 或 Google subject identifier

如果任何值暴露，立即停止，标记证据受污染，并要求在对应 provider 轮换或撤销；轮换本身是单独 mutation。不要在报告中复述泄露值。

## Claims And Output Contract

从 [OAuth report template](templates/oauth-report.template.json) 创建本地脱敏报告，并运行 `scripts/validate_report.py`。输出包括：

- `scope`：项目/环境别名、代码 revision、生产与本地 origin 的非个人配置。
- `url_matrix`：静态配置 URL；绝不保存带 `code`、token、query 或 fragment 的运行时回调。
- `actions`：七个动作的 authorization、before、execution、readback 与 rollback。
- `observations`：官方资料、代码、Google、Supabase、浏览器 callback 和 protected route 的布尔/枚举证据。
- `claims`：`configuration_ready` 与 `end_to_end_verified`。
- `missing_evidence`：仍未取得的 provider、浏览器或人工证据。

运行：

```bash
python3 scripts/validate_report.py /absolute/path/to/oauth-report.json
python3 scripts/validate_report.py /absolute/path/to/oauth-report.json --require-configuration-ready
python3 scripts/validate_report.py /absolute/path/to/oauth-report.json --require-end-to-end
```

## Rollback And Degradation

- 代码失败：只回退本次精确 diff；不改 provider 来掩盖 callback bug。
- Google project 创建后尚无 client：可以保留隔离资源；删除 project 是 destructive action，不能自动执行。
- Web client 配错：从 before snapshot 恢复 exact origins/redirects；新 client 的删除需单独授权。
- Supabase provider 配错：恢复 provider enable 状态和原 client ID；secret 只能由用户重新输入，报告不能充当备份。
- URL allowlist 配错：恢复精确 Site URL 与 Redirect URLs，重新回读。
- 真实登录失败：登出当前测试会话，保留失败证据的脱敏摘要；不要自动删除用户或撤销 Google grant。
- 无 Dashboard 写权限：只产出 audit、URL matrix、代码检查和精确 handoff，不声称 configured。
- 无真实浏览器/测试账号授权：最多声明 `configuration_ready`，把 provider-backed login 标为 `missing_evidence`。
- Google 官方页面不可读取：记录缺失证据；不要从过时 UI 说明推导按钮或发布状态。

回滚计划不等于回滚完成。执行回滚后必须重新做 provider readback、代码测试和适用的登录验证。

## Non-goals

- 非 Google provider、Google Workspace API/Drive/Gmail 权限或任意 OAuth 服务端实现
- Supabase 数据库 schema、RLS、service-role、用户迁移、账号合并或 MFA
- Auth pentest、批量注册、绕过 consent/2FA 或抓取 browser storage
- 生产 OAuth publication、品牌验证、域名验证或 billing，除非用户逐项明确要求
- 删除 Google project/client、删除 Supabase user、撤销 grant 或 Git push

## Maintenance

每季度或 Supabase Auth、Google Auth Platform、SSR/PKCE helper、Redirect URLs 行为变化时复核 [official sources](references/official-sources.md)。更新前重新运行 prior-art、Skill IR、trigger eval、offline tests、secret scan、root-entrypoint isolation 和 local release gate。Provider-backed comparison 与 human blind review 在实际完成前始终是 `missing evidence`。
