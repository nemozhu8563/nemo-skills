---
name: nemo-site-telemetry
description: >-
  Govern first-time or resumed website telemetry onboarding across Google Analytics 4 (GA4), Microsoft Clarity, and Google Search Console (GSC) for game, SaaS, content, documentation, and other sites. Use to add, configure, launch, verify, troubleshoot, or finish telemetry, DNS ownership, sitemap submission/status/manual readback, or bounded Search Analytics API verification, including “接入 GA4 和 Clarity”, “提交 GSC”, “看下 sitemap 是否已提交”, and “验证 Search Analytics 只读查询”. Enforce production-only instrumentation, consent-aware setup, exact-resource idempotency, intent-aware mutation, provider readback, and separate setup, transport, search-performance, crawling, and indexing evidence. Exclude routine analytics/SEO reporting, ranking or keyword research, legal advice, ad conversion setup, Google Indexing API, and game-pipeline day-7/day-14 orchestration.
license: MIT
metadata:
  author: Nemo
  version: "0.3.0"
---

# Nemo Site Telemetry

将 GA4、Microsoft Clarity 与 GSC 从准备接入推进到逐层回读，区分配置、请求、provider 数据、sitemap 与收录证据。

## Router Rules

- 用户要求为网站接入、配置、上线、恢复、验证或排查 GA4、Clarity、GSC 中任意一个或多个组件时触发；不要求三者每次全部执行。
- 游戏站、SaaS、内容站、文档站都属于本 Skill；实现与命名不得限定为游戏业务。
- “继续”“恢复”“搞好为止”若上下文指向 telemetry，应先恢复现有 property、stream、project、DNS 记录、sitemap、浏览器 tab 和部署状态，不重复创建。
- “统计 + 搜索控制台”在同一次执行中分别处理 GA4、Clarity、GSC，仍输出独立状态。
- 查询 sitemap 状态或回读用户刚手动提交的结果属于 GSC 验证；默认只读，不代表提交或重提授权。
- 明确验证 GSC Search Analytics API 可用性，或在 onboarding/verification 中读取一个精确 property 的受控日期窗口时触发；只允许固定只读参数，不开放任意报表 JSON、filters 或 hourly 查询。
- 只查看访问量、漏斗、录屏、点击、曝光、CTR、排名、关键词或内容机会时不触发；那是分析任务。
- 明确要求 `game-site-pipeline` 的 telemetry stage、day-7/day-14 snapshot、`grow/hold/retire` 决策时不触发；那是游戏站中央状态机的专用阶段。
- 不把 GA4 Measurement ID、Clarity Project ID 当作秘密；它们会进入前端。登录 cookie、OAuth token、DNS token 和 GSC verification value 仍不得保存或回显。

## Completion Model

每个组件采用三层证据：

1. `configured`：资源与代码配置已存在，并已从代码或 provider 回读。
2. `transport_observed`：生产 origin 上观察到目标请求；preview/local 必须无请求。
3. `provider_observed`：对应 provider UI/API 已读回数据或状态。

所需证据齐全才能写 `verified`；否则用 `pending`、`unknown` 或 `missing evidence`。文件、计划、按钮点击和客户端请求不能替代 provider readback。

## Compact Workflow

1. 从对话、仓库、部署、浏览器和 provider 恢复 production origin、站点类型、目标账号/组织、现有资源、sitemap 与已完成步骤。
2. 首次使用或新站点的第一项可观察动作必须是只读 `readiness_check`，先于任何登录、配置、代码修改或外部写入；按 [Workflow](references/workflow.md) 检查本地、站点、资源、consent、sitemap、CLI/ADC 与所需浏览器/provider 会话。
3. 把检查和 blocker 写入输出；未知项用 `not_checked`/`missing_evidence`，不猜测或自动发起 OAuth/login。
4. 将请求拆成 `ga4`、`clarity`、`gsc`；未请求项为 `not_requested`。外部写入前，必须把每个组件的精确目标、匹配、动作、写入、回读和回滚写入用户可见 `configuration_plan`。
5. 所有资源先查后写：精确匹配则复用或恢复；写操作超时后先 read-after-write，不能盲目重发。
6. 对 GSC sitemap 先解析操作模式：状态查询用 `status_only`，用户已手动提交用 `manual_readback`，明确提交或 GSC 接入授权用 `submit_once`，提交后中断用 `recovery_readback`；所有模式都必须先精确读回，再决定报告、提交或重试。
7. 按 [GA4](references/ga4.md)、[Clarity](references/clarity.md) 与 [GSC](references/gsc.md) 执行，并使用 [Workflow](references/workflow.md) 的证据顺序。
8. 对生产构建和非生产构建分别验证。生产端必须命中预期脚本/请求；local、preview、分支域名和错误 hostname 必须没有生产 telemetry 请求。
9. 从 provider 读回实际状态：GA4 Realtime 或 DebugView、Clarity collect + Recordings/Dashboard、GSC ownership + Sitemaps。传播期或新站无数据时原样报告。
10. 失败或中断时保存不含凭据的 `recovery_checkpoint`；下次从现状继续，不重建资源。

## Google API Adapter

- `Google API` 是可选执行面；按账号、资源与意图选择 `google_api`、`browser` 或 `mixed`；不可用时仅降级到已授权 browser/manual。
- 能力、browser-only 边界、bootstrap 与安全限制见 [Google API Adapter](references/google-api.md)。
- readiness 分别检查 CLI 身份、ADC 身份与 Google/Clarity 浏览器会话。
- 自建 Desktop OAuth 的 `adc_user` 登录须带 adapter 基础 scope 和当前最小 scope；遗漏时 OAuth 成功仍会 `reauth_required`。
- status/readback/onboarding 不隐式启用 API；`bootstrap enable-apis` 需明确配置授权。
- GSC Search Analytics 使用 `gsc-read` 与只读语义 `POST`；GSC sitemap 与 GA4 create 必走 `plan → apply → readback`。所有只读命令都不生成写计划，模糊 sitemap submit 先回读，GA4 模糊 create 永不自动 replay。
- adapter 仅用 Python 3.11+ 标准库和受控 `gcloud` ADC 短 token；没有 provider run 则 `missing evidence`。

## Production Isolation

production-only 是本 Skill 的治理选择，不冒充 GA4、Clarity 或 GSC 的官方硬性要求：

- 用规范化精确 production origin 做 build-time gate，并在任何远程脚本/请求前再做 runtime origin guard；禁止模糊匹配。
- local/preview 构建应完全不含 GA4/Clarity marker、ID 和远程脚本；框架被迫共享 bundle 时报告静态残留并证明 runtime gate 先执行。
- production origin 与公开 ID 可进非秘密配置；账号凭据走项目既有 secret 管理路径。

## Consent Boundary

- 先恢复现有 CMP/政策/选择；本 Skill 不提供法律结论，也不静默假定 analytics consent 为 granted。
- GA4 `analytics_storage` 与 Clarity Consent Mode `consentv2` 跟随已确认策略；未明确请求广告用途时广告相关字段保持 `denied`。
- consent default 必须先于 measurement；策略不明时只能设计，`ga4.setup`/`clarity.setup` 为 `blocked` 或 `missing evidence`。

## Gate Ladder

- `G0–G2 Scope/Authorization/Readiness`：目标不确定时仅只读；“接入”授权精确常规资源，“查看/手动提交后检查”只授权回读；删除、邀请、切换账号/zone、长期授权、计费与政策发布另行授权。站点、canonical、sitemap、consent 必须满足组件。
- `G3–G4 Idempotency/Code proof`：property、stream、project、TXT、sitemap 先查后写；生产构建只含预期 telemetry，非生产为零，部署 HTML 与配置一致。
- `G5–G6 Transport/Provider proof`：精确生产请求不等于 provider 已处理；GA4、Clarity、GSC 必须分别从自身 UI/API 回读。
- `G7 Claim guard`：请求、Realtime、recording、sitemap processing、crawl 与 index 严格分开。

## Output Contract

核心状态键固定为：`readiness_check`、`configuration_plan`、`site_preflight`、`ga4.setup`、`ga4.production_request`、`ga4.realtime`、`ga4.debugview`、`clarity.setup`、`clarity.tag_loaded`、`clarity.production_request`、`clarity.recording`、`gsc.property`、`gsc.public_dns`、`gsc.ownership`、`gsc.sitemap`、`gsc.search_analytics`、`gsc.indexing` 与 `recovery_checkpoint`。

```yaml
readiness_check:
  status: ready|partial|blocked
  local_runtime: verified|partial|blocked|not_checked
  target_identity: verified|partial|blocked|not_checked
  google_cli_login: available|reauth_required|not_required|not_checked
  google_adc: available|reauth_required|not_required|not_checked
  google_browser_login: available|reauth_required|not_required|not_checked
  clarity_browser_login: available|reauth_required|not_required|not_checked
  dns_or_deploy_login: available|reauth_required|not_required|not_checked
  blockers: []
configuration_plan:
  google_api_bootstrap:
    auth_mode: adc_user|adc_service_account|impersonation|none|unknown
    cloud_project: exact-project-or-blocked
    quota_project: exact-project-or-not_applicable
    capabilities_and_scopes: []
    required_services: []
    resource_permissions: []
    interactive_login: required|not_required|blocked|not_checked
    external_write: []
    readback: []
    rollback: []
  <ga4|clarity|gsc>:
    desired_resource: exact-target-or-not_requested
    existing_matches: []
    action: existing|create|resume|blocked|not_requested
    external_write: []
    readback: []
    rollback: []
site_preflight:
  status: verified|partial|failed|missing_evidence
  production_origin: https://example.com
  preview_isolation: verified|failed|not_checked
  consent_policy: verified|blocked|not_required|missing_evidence
ga4:
  setup: existing|created|resumed|blocked|not_requested
  production_request: verified|pending|failed|not_checked
  realtime: verified|pending|missing_evidence|not_checked
  debugview: verified|pending|missing_evidence|not_checked
clarity:
  setup: existing|created|resumed|blocked|not_requested
  tag_loaded: verified|pending|failed|not_checked
  production_request: verified|pending|failed|not_checked
  recording: verified|pending|missing_evidence|not_checked
gsc:
  property: existing|created|resumed|blocked|not_requested
  public_dns: verified|pending|failed|not_required|not_checked
  ownership: verified|pending|failed|not_checked
  sitemap: existing|submitted|not_found|pending|failed|not_requested
  sitemap_operation_mode: status_only|manual_readback|submit_once|recovery_readback|not_requested
  sitemap_action_taken: readback_only|submitted_once|none|not_checked
  sitemap_provider_status: raw-provider-status|not_visible|not_checked
  search_analytics: verified|empty|pending|failed|not_requested|not_checked
  indexing: observed|pending|unknown|not_checked
recovery_checkpoint:
  status: none|saved
  next_action: none-or-precise-step
google_api:
  provider_mode: browser|google_api|mixed|none
  auth_mode: adc_user|adc_service_account|impersonation|none|unknown
  capability_status: available|unavailable|unknown
  scope_status: matched|insufficient|unknown
  resource_access: matched|insufficient|unknown
  bootstrap_status: required|in_progress|completed|blocked|not_needed
  steady_state: zero_click|reauth_required|blocked|not_applicable
  api_readback: verified|pending|failed|not_attempted
```

额外规则：

- `readiness_check` 与 `configuration_plan` 必须进入用户可见输出，不能只作为内部推理；首次 readiness 未完成时不得开始配置或外部写入，配置方案中的未知值必须保留为 blocker。
- `configuration_plan` 在执行过程中按 provider readback 更新；它描述将做什么，不是已经做过的证据，不能替代下面的实际状态键。
- `ga4.production_request` 只证明浏览器发送/尝试发送请求；`ga4.realtime` 或 `debugview` 才是接收侧证据。
- `clarity.tag_loaded`、`clarity.production_request` 与 `clarity.recording` 是三个状态；`www.clarity.ms/collect` 请求不能代替 Dashboard/Recordings 回读。
- `gsc.sitemap=submitted` 不等于下载、抓取或索引；没有独立 GSC 证据时 `gsc.indexing=unknown`。
- `gsc.sitemap` 的证据记录必须附带 `sitemap_operation_mode`、`sitemap_action_taken`、GSC 原始状态和 `checked_at`；按钮点击、请求发出或用户口述提交都不能替代 Sitemaps list/get 回读。
- `gsc.search_analytics` 只表示精确 property 与日期窗口的受控只读查询；返回的是 top aggregated rows，不是完整导出、稳定快照、sitemap/crawl/indexing 证据，也不把本 Skill 变成排名或内容机会分析流程。
- `ga4.readback_surface` 与 `gsc.readback_surface` 使用 `api|browser|mixed|not_checked`；API 与浏览器资源身份冲突时必须 `blocked`，不能选择更方便的一边继续。
- GA4 Realtime API 只能更新 `ga4.realtime`，不能替代 `ga4.production_request` 或 `ga4.debugview`；GSC URL Inspection 是读取，不是 Google Indexing API 或请求收录。
- GSC DNS 必须由 provider 与两个独立公共解析器分别回读；只看到控制台保存成功不能写 `gsc.public_dns=verified`。
- 每项写明 `checked_at`、证据来源和实际 provider 原始状态；报告不包含公开 ID 以外的凭据或 verification value。

## Recovery And Rollback

- 中断后先回读真实外部状态，不以重建资源恢复连接。GA4/Clarity 可回滚本次代码并重部署；删除 provider 资源仍需单独授权。
- GSC 验证 TXT 默认保留，因为 Google 会周期性复查；删除也需精确回读与授权。回滚后复验生产/非生产、站点可用性及其他 telemetry。

## References

- 总流程与恢复：[Workflow](references/workflow.md)
- GA4：[GA4](references/ga4.md)
- Microsoft Clarity：[Clarity](references/clarity.md)
- Google Search Console：[GSC](references/gsc.md)
- Google API 执行面：[Google API Adapter](references/google-api.md)
- 权限、信任、秘密与回滚：[Governance](references/governance.md)
- 当前官方依据：[Official Sources](references/official-sources.md)
