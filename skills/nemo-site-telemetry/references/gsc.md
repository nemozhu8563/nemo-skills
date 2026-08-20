# Google Search Console Onboarding And Verification

## Completion definition

GSC 接入完成要求当前回读证明：

1. 目标 property 类型和值正确；
2. property 已 verified，当前上下文具备 Owner 权限；
3. 精确 sitemap 已出现在 Sitemaps 列表/API；
4. sitemap 的实际状态被原样记录。

页面已抓取或收录不是以上事实的推论。

## Property and DNS

- 默认 Domain property，因为它覆盖所有协议与子域；输入只用域名，不含协议或路径。
- 只有用户需要受限范围、没有 DNS 控制权或业务边界要求时使用 URL-prefix。
- property selector 与待验证资源先查重；existing/resumed 优先于 created。
- Domain property 通过 DNS 验证。优先手动 TXT，避免为一次验证授予长期 DNS 访问。
- 确认权威 nameserver、provider、精确 zone、apex name 语义与现有 TXT。
- 完全相同的 type/name/content 复用；不同 owner 的 Google verification TXT 保留，不覆盖、不删除。
- verification value 只在执行所需的短生命周期内使用，不进入仓库、笔记、报告、聊天、未打码截图或命令历史。

## DNS evidence

1. 写后从 DNS provider UI/API 回读 type、name、TTL、content matched。
2. 再从两个独立公共解析器（默认 `1.1.1.1` 与 `8.8.8.8`）查询。
3. 在进程内比较实际值，仅输出 `matched/pending`，不回显 TXT。
4. 两个公共解析器都匹配后再点击 Verify；未传播时有上限地等待，不重复创建记录。

## Ownership

- 回到同一 property 与 challenge，点击 Verify 一次。
- 从 GSC Settings/Ownership verification 或等价界面读回 verified 与 Owner。
- Google 会周期性检查 verification token。成功后默认保留 TXT；自动删除可能使权限过期。
- browser/CDP 中断后恢复原 tab/property 并 read-after-write，不重新创建。

## Sitemap

提交前从公网读取精确 URL，并检查成功响应、可解析非空 XML、完整 canonical URL、property 范围和 robots。

先根据用户当前意图确定操作模式；不得因为 Skill 支持提交就把只读请求升级为写操作：

| 用户意图 | `operation_mode` | 允许动作 | 完成证据 |
|---|---|---|---|
| “看下/检查/是否已提交/只查状态” | `status_only` | 公网预检 + 精确 Sitemaps list/get；禁止 submit | 原样报告存在、缺失或 provider 状态 |
| “我刚手动提交了，帮我看状态” | `manual_readback` | 精确 list/get；禁止 submit/re-submit | 读到原始状态；尚未出现则标记 `pending` 并保存 checkpoint |
| “提交 sitemap”或已明确要求 GSC 接入/配置/上线/搞好 | `submit_once` | 公网预检 + 精确 list/get；确认缺失后 submit 一次，再 list/get | 精确 URL 出现在 GSC 且原始状态已记录 |
| submit 点击/API 超时、浏览器或 CDP 中断 | `recovery_readback` | 先精确 list/get；仅在仍有原始写授权且确认缺失后重试 | 回读结果或精确的恢复 checkpoint |

- 精确 URL 已存在：记录 `existing` 与原始状态，不重复提交。
- 精确 URL 不存在且 `submit_once` 已获授权：提交一次，再从 Sitemaps list/get 回读。
- 精确 URL 不存在但当前是 `status_only` 或 `manual_readback`：报告未发现或仍待传播，不提交。
- 用户口述“已提交”、按钮点击成功或请求已发出都不是 provider 证据；仍需 list/get 回读。
- `Success`、`Processing`、`Couldn't fetch` 等原始状态照实保留。
- sitemap 是发现 URL 的提示。Google 官方明确说明它不保证抓取 sitemap 中的所有内容或编入索引。

### Google API adapter mapping

| `operation_mode` | adapter 命令 | 写 endpoint |
|---|---|---|
| `status_only` | `gsc get-sitemap` 或 `gsc list-sitemaps` | 禁止 |
| `manual_readback` | `gsc get-sitemap` 或 `gsc list-sitemaps` | 禁止 |
| `submit_once` | `gsc sitemap-plan` → `gsc sitemap-apply` → exact get | plan 校验通过后最多一次 |
| `recovery_readback` | exact get/list；仍 absent 且原授权有效才生成全新 recovery plan | 最多一次 recovery submit |

`sitemap-plan` 对 `status_only`/`manual_readback` 在取得 token 或访问 provider 前 fail closed。apply 不信任旧 plan 的 absence：先按 write capability 重新读取 exact property 与 sitemap，再决定 noop 或发送一个 PUT。timeout/5xx 后第一项网络动作必须是 exact get/list，旧 token 与旧 plan 都不能重用。

`recovery_readback` 生成新 plan 时必须传回第一次 ambiguous submit 对应的 `--recovery-authorization-fingerprint`。adapter 用 credential-free checkpoint 验证原授权 expiry 与 exact target，并在 recovery PUT 前做跨进程原子 claim；同一 authorization/target 在 15 分钟窗口内最多一个 recovery submit，之后只能继续 exact get/list。

URL Inspection 使用 `searchconsole.urlInspection.index.inspect` 的只读结果，只能更新 `gsc.indexing` 的观察证据；它不是 Google Indexing API，也不发起抓取或收录请求。

## Search Analytics readback

Search Analytics 是 `gsc-read` 的受控只读 primitive，用于 onboarding/verification 中验证精确 property 的查询能力，或交给专门 SEO 流程读取限定窗口。它不会提交 sitemap、请求抓取、改变 property，也不会证明 indexing。

- 必须明确 `site-url`、`start-date` 与 `end-date`；日期包含首尾两天。
- 只允许固定 dimensions、search type、`FINAL|ALL`、aggregation type、`rowLimit=1..25000` 和 `startRow>=0`；禁止任意 request JSON、filters 与 hourly passthrough。
- `FINAL` 用于较稳定的最终数据；`ALL` 可能包含 fresh、尚未最终确定且后续会变化的数据。
- 每行 `keys` 顺序与 dimensions 一致；`ctr` 是 0–1 比例，`position` 是平均排名。
- API 返回 top aggregated rows，不保证完整底层数据，也不提供总行数或 cursor。分页保持相同查询参数并递增 `startRow`，但跨请求结果可能变化。
- adapter 输出 `row_count`、`row_limit_reached` 与 `response_aggregation_type`，并丢弃 provider 未知字段；Search Analytics 数据与 sitemap、crawl、URL Inspection/indexing 证据保持分离。

## Evidence and output

- `gsc.property`：existing/created/resumed + type/value matched。
- `gsc.public_dns`：provider、resolver 1、resolver 2 分开记录。
- `gsc.ownership`：verified/pending/failed + Owner/unknown。
- `gsc.sitemap`：existing/submitted/not_found/pending/failed；另附 `sitemap_operation_mode`、`sitemap_action_taken`、raw provider status 与 `checked_at`。
- `gsc.search_analytics`：verified/empty/pending/failed/not_requested/not_checked；另附日期、dimensions、search/data/aggregation、offset/limit、row count 与 `checked_at`。
- `gsc.indexing`：没有独立 Page indexing/URL Inspection 证据时必须为 `unknown` 或 `pending`。

## Destructive boundary

删除 TXT、property、sitemap 或 owner，切换 Google/DNS 账号或 zone，授予他人权限、修改 nameserver/DNSSEC 都不在正常接入授权内，必须单独确认并做精确回读。
