# Google API Adapter

## Role and boundary

这个 adapter 是 `nemo-site-telemetry` 的可选执行面，不是第二个 Skill，也不是通用 Google API/MCP passthrough。它负责：

- GSC sites、sitemaps、URL Inspection 与受控 Search Analytics 读取；
- 明确授权后的精确 sitemap submit；
- GA4 account/property/Web stream 与有限 Realtime 读取；
- 明确授权后的 GA4 property/Web stream create-only；
- 统一 credential-free JSON、错误分类和恢复证据。

它不实现通用 GSC 报表 passthrough、Google Indexing API、delete/patch、权限管理、账号切换、GSC ownership/DNS、GA4 DebugView、GA4↔GSC association 或 Clarity。API 不可用时，browser fallback 继承同一 intent、target 与权限边界，不能成为删除、提权或切换账号的旁路。

## Prerequisites and bootstrap

- Python 3.11+，仅使用标准库。
- 可选外部工具 `gcloud`；不自动安装或升级。
- Cloud project 与 quota project 必须由操作者明确选择并回读。
- API service：`searchconsole.googleapis.com`、`analyticsadmin.googleapis.com`、`analyticsdata.googleapis.com`。
- 首次 OAuth login/consent、API enable、`serviceusage.services.use`、把身份加入 GSC/GA4 资源都是一次性人工/授权边界。

首次使用按下面顺序执行并把结果写入 `readiness_check`，不要跳过检查直接登录或启用 API：

1. 只读检查 Python 与 `gcloud` 是否存在、版本是否满足；
2. 区分并检查 `gcloud` CLI active identity 与 ADC。CLI identity 支撑 `gcloud services list/enable`，adapter 的 GSC/GA4 token 来自 ADC、service account ADC 或 impersonation；
3. 确认精确 Cloud project 与 quota project 后运行 `bootstrap status`；project 未选择时保持 blocked，不能从相似项目名猜测；
4. 对用户实际请求的最小 capability 运行 `auth probe`，验证 token、scope 与资源可见性；
5. 将缺失 API、scope、resource role、browser session 和 provider 资源分别写入 `configuration_plan`；
6. 只有用户已明确授权 Google API bootstrap，才运行 `bootstrap enable-apis`，然后重新 status/probe/readback。

`gcloud auth login` 与 `gcloud auth application-default login` 是两套身份，不能互相代替。前者缺失时，service status/enable 不可用；后者缺失时，默认 `adc_user` adapter token 不可用。首次 ADC consent 可能还需要操作者提供仓库外的 OAuth Desktop Client 配置和按 capability 选择的 scopes；Skill 只能先给出精确配置方案，不能静默使用默认 scopes、覆盖已有 ADC 或输出 credential 路径。

### 自建 Desktop OAuth client 的 ADC scope 基线

这一节只适用于 `adc_user` 使用操作者提供的 Desktop OAuth client；不把它套用到 service account 或 impersonation。

先在用户可见的 `configuration_plan` 中列出当前 capability，再请求交互登录。首次 `gcloud auth application-default login --scopes` 必须始终包含以下基础 scope：

- `openid`
- `https://www.googleapis.com/auth/userinfo.email`
- `https://www.googleapis.com/auth/cloud-platform`

然后只追加当前请求所需的 capability scope：`gsc-read` 用 `https://www.googleapis.com/auth/webmasters.readonly`，`gsc-sitemap-submit` 用 `https://www.googleapis.com/auth/webmasters`，`ga4-read` 用 `https://www.googleapis.com/auth/analytics.readonly`，`ga4-admin-write` 用 `https://www.googleapis.com/auth/analytics.edit`。没有明确写入授权时，不能预先加入两个 write scope。

`gcloud auth application-default login --scopes` 会替换默认 scope 集；而 adapter 后续的 `gcloud auth application-default print-access-token --scopes=...` 刷新会要求 `openid` 与 `userinfo.email`。因此，漏掉基础 scope 时，浏览器 OAuth 成功不等于 adapter 可用，`auth probe` 仍可能返回 `reauth_required`。此时先把完整的最小 scope 集写回配置方案，获得操作者授权后再重新登录；不能把一般 `reauth_required` 自动解释为可以扩展 write scope。

例如，GSC 与 GA4 都只读时，授权方案使用：

```bash
gcloud auth application-default login \
  --client-id-file=/secure/path/to/oauth-desktop-client.json \
  --scopes=openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/webmasters.readonly,https://www.googleapis.com/auth/analytics.readonly
```

带 `--client-id-file` 的登录不会把 quota project 写入 ADC；因此仍须在 adapter 的每次命令中显式提供并回读精确 `--project-id` 与 `--quota-project-id`，不要为此隐式改动全局 gcloud project。

Google 浏览器登录另用于 GA4 DebugView、GSC ownership/DNS 和 GA4↔GSC association；Microsoft 浏览器登录用于 Clarity。它们与 CLI/ADC 是独立证据面，任何账号或资源身份冲突都必须 blocked。

普通 status/readback 命令永不调用 `bootstrap enable-apis`。只有用户明确要求配置 Google API 时才可运行：

```bash
python3 scripts/google_api_adapter.py bootstrap status \
  --project-id PROJECT_ID --quota-project-id QUOTA_PROJECT_ID
python3 scripts/google_api_adapter.py bootstrap enable-apis \
  --project-id PROJECT_ID --quota-project-id QUOTA_PROJECT_ID
```

`gcloud` 只做 service bootstrap、ADC 与短期 token broker；GSC/GA4 业务调用走固定官方 REST allowlist。每条顶层命令重新按最小 capability 取 token，不跨 operation 缓存：

| capability | scope | provider role |
|---|---|---|
| `gsc-read` | `webmasters.readonly` | 精确 property 可读 |
| `gsc-sitemap-submit` | `webmasters` | 精确 property 可提交 sitemap |
| `ga4-read` | `analytics.readonly` | 精确 account/property 可读 |
| `ga4-admin-write` | `analytics.edit` | 目标 account 可创建 property/stream |

一般 403 无法证明是 scope 还是 resource role 时，两者都保持 `unknown` 并阻断写入；不能猜测并扩大 scope。用户 ADC 的 API 写入缺少已确认 quota project 时同样阻断。

## Authentication modes

- `adc_user`：本机交互默认；首次 `gcloud auth application-default login` 不是零点击。
- `adc_service_account`：只使用操作者已提供的仓库外 `GOOGLE_APPLICATION_CREDENTIALS`；文件必须是当前用户拥有、非 symlink、`0600` 或更严格，父目录不可 group/world writable。
- `impersonation`：已有 IAM 条件时可用；adapter 不授予 Token Creator。

token、subject email、credential path、Authorization/cookie header、JWT/PEM/OAuth code 和 GSC verification value 不进入 stdout、stderr、plan、checkpoint、fixture 或报告。

## Command surface

读取：

```text
auth probe --capability gsc-read|gsc-sitemap-submit|ga4-read|ga4-admin-write
gsc list-sites|get-site|list-sitemaps|get-sitemap|inspect-url|search-analytics
ga4 list-account-summaries|get-property|list-web-streams|realtime
```

写入：

```text
gsc sitemap-plan → gsc sitemap-apply → exact get readback
ga4 resource-plan → ga4 resource-apply → exact property/stream readback
```

`recovery_readback` 只能绑定第一次 ambiguous submit 返回前已保存的 authorization fingerprint：

```text
gsc sitemap-plan --operation-mode recovery_readback \
  --recovery-authorization-fingerprint <original-authorization-fingerprint> ...
```

Realtime 只允许 `activeUsers`、`eventCount`、`screenPageViews`，不能演变成日常报表查询。URL Inspection 只读取 exact URL 当前结果，不请求收录。

Search Analytics 使用同一个 `gsc-read` / `webmasters.readonly` capability：

```bash
python3 scripts/google_api_adapter.py gsc search-analytics \
  --site-url 'sc-domain:example.com' \
  --start-date 2026-08-01 \
  --end-date 2026-08-19 \
  --dimension query \
  --row-limit 1000
```

只允许 `start/end date`、可重复的 `country|date|device|page|query|searchAppearance` dimension、`WEB|IMAGE|VIDEO|NEWS|DISCOVER|GOOGLE_NEWS` search type、`FINAL|ALL` data state、受支持的 aggregation type、`rowLimit=1..25000` 与 `startRow>=0`。默认是 `WEB`、`FINAL`、`AUTO`、1000 行和 offset 0；不开放任意 JSON、filters 或 hourly 查询。

该 endpoint 虽为 `POST webmasters.searchanalytics.query`，实现固定传入 `read_only=True`，因此只走有界读重试，永不创建 write plan 或 recovery checkpoint。响应只保留 dimensions、clicks、impressions、CTR、position 与实际 aggregation；未知字段被丢弃，不合法 keys/metrics fail closed。Discovery 声明大写 aggregation enum，但 2026-08-20 的真实 API 回读使用 lowerCamel `byProperty`；adapter 仅把四个已知 lowerCamel 别名规范化为契约中的大写值，其他值继续 fail closed。Google 只返回 top aggregated rows，API 没有总行数或 cursor；`row_limit_reached=true` 仅表示可能需要用相同参数递增 `start-row`，不能把分页视为完整、稳定快照，也不能推导 indexing。

## Plan security and recovery

- plan 只能写入系统临时目录下以 `nemo-site-telemetry-` 开头的独立 task directory；目录 `0700`、文件 `0600`。
- 创建与 apply 都拒绝 symlink、错误 owner、过宽 mode、非 canonical bytes、错误 digest、过期 TTL、authorization/target/operation 漂移和不在 allowlist 的 action。
- plan 绑定 10 分钟 TTL、canonical target fingerprint、credential-free authorization basis 与 SHA-256；apply 前重新读取 provider 当前状态。
- plan 是单次使用；apply 完成、失败或 pending 后不复用旧 plan。
- 公网 sitemap 预检拒绝 userinfo、fragment、私网、loopback、link-local、reserved 与混合公私 DNS 结果；连接固定到已校验的公网 IP，HTTPS 仍按原 hostname 验证证书，每次同 host redirect 都重新解析并校验，阻断 DNS rebinding 与 metadata SSRF。
- GSC PUT timeout/5xx 后的第一项网络动作是 exact get/list。仍 absent 时，adapter 在私有系统临时目录保存不含凭据的 ambiguous checkpoint；只有原授权仍有效、target 不变且显式传回原 authorization fingerprint 的全新 `recovery_readback` plan 才可继续。
- recovery apply 在 PUT 前以 authorization + target 原子 claim；同一组合 15 分钟内跨进程、跨 task 临时目录最多一个 recovery submit。claim 后无论结果如何都只能继续 readback，不能再生成 recovery submit。
- GA4 POST timeout/5xx 永不自动 replay。只按 immutable account/property 与 canonical origin 回读；零个或多个候选都保持 pending。property 已创建而 stream 不明确时报告 `partial_external_state`。

## Output and exit codes

stdout 始终是一份符合 `contracts/google-api-output.schema.json` 的 JSON，末尾一个换行；stderr 仅输出固定、脱敏错误码。稳定退出码：

| code | meaning |
|---|---|
| `0` | completed / verified / noop |
| `2` | CLI/input contract invalid；未访问 provider |
| `10` | Python/gcloud/API/ADC prerequisite missing |
| `11` | capability/account/scope/quota/resource access blocked or unknown |
| `12` | target/authorization/plan/TTL/digest invalid |
| `13` | provider transient or ambiguous；保持 pending |
| `14` | provider permanent rejection/not found |
| `15` | safe internal error；无 traceback/provider payload |

API evidence 与浏览器 evidence 冲突时必须 `blocked`。成功 HTTP write 只证明请求返回；只有写后 exact list/get 才能标记 `verified`。没有真实授权 provider run 时，包级结论继续为 `missing evidence`。
