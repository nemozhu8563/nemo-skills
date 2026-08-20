# Nemo Site Telemetry

面向游戏站、SaaS、内容站、文档站等网站的一体化 telemetry 上线 Skill。它在一个可恢复流程中处理 GA4、Microsoft Clarity 与 Google Search Console，但对三者分别验证、分别报告。

`0.3.0` 在不依赖第三方 MCP 的 Google API adapter 中增加了受控 GSC Search Analytics 只读查询。adapter 用 `gcloud` 提供 ADC 短期 token，以官方 REST API 回读 GSC 与 GA4，并把唯一允许的写入限制在安全的 `plan → apply → readback` 流程中。Clarity、GA4 DebugView、GSC ownership/DNS 和 GA4↔GSC 关联仍保留浏览器证据路径。

## 你可以直接这样说

- “给这个 SaaS 站接入 GA4 和 Clarity，只在正式域名采集。”
- “把统计和 GSC 一起上线，验证 DNS 并提交 sitemap。”
- “继续上次中断的 Clarity/GSC 配置，不要重复创建。”
- “检查现有 GA4 是否真的收到生产流量，preview 不要污染。”
- “看下 sitemap 在 GSC 里有没有提交，只查状态，不要提交。”
- “我刚手动提交了 sitemap，帮我把 GSC 状态读回来。”
- “验证这个 GSC property 的 Search Analytics 只读查询，读取最近 28 天 query 行。”

只做日常报表、录屏分析、排名诊断、关键词研究、广告转化或法律判断时不使用本 Skill。

## 核心原则

1. 资源先查后写，断线后恢复，不重复 property、stream、project、TXT 或 sitemap。
2. production origin 精确门禁 + runtime guard；local/preview 零生产 telemetry。
3. consent 状态来自站点既有政策/CMP，不把示例值当成通用许可。
4. GA4 的请求与 Realtime/DebugView、Clarity 的 tag/request/recording、GSC 的 property/DNS/ownership/Search Analytics/sitemap/indexing 分层回读。
5. 没有 provider 或人工证据时明确写 `missing evidence`。
6. sitemap 查询或手动提交后的检查只读；明确提交/接入授权时才查重后提交一次，并始终回读。
7. Google API bootstrap 与首次 OAuth/资源授权不是“零点击”；完成一次性准备后，受支持的日常 readback 与已授权写入才可零 dashboard 点击。

## 第一次运行先做 readiness

对新站点，Skill 的第一项动作是只读检查，并在任何登录、代码修改、provider 配置或外部写入前输出：

- `readiness_check`：本地运行时、production/canonical、preview/local、现有 IDs/资源、CMP/consent、sitemap，以及各登录/权限面的实际状态与 blocker；
- `configuration_plan`：Google API bootstrap 的认证模式、Cloud/quota project、capabilities/scopes、services 与资源权限；以及 GA4、Clarity、GSC 各自的 `desired_resource`、`existing_matches`、`action`、`external_write`、`readback`、`rollback`。

Google 侧有三套互相不能替代的登录面：

| 登录面 | 用途 | 何时需要 |
|---|---|---|
| `gcloud` CLI identity | 查询/启用 Cloud API services | 选择 `google_api` 且需要 bootstrap status/enable 时 |
| ADC (`gcloud auth application-default login`、service account 或 impersonation) | adapter 获取 GSC/GA4 短期 token | API probe/readback/apply 时 |
| Google 浏览器会话 | GA4 DebugView、GSC ownership/DNS、GA4↔GSC association | 对应 UI 证据或操作被请求时 |

Clarity 需要目标 Microsoft organization/project 的浏览器会话。DNS provider 和部署平台仅在需要验证/修改 DNS 或部署代码时登录；只读状态查询不会自动扩大到这些登录。Skill 不自动运行 OAuth/login、切换账号或覆盖现有 ADC，而是先把精确缺口和建议配置写入方案。

本地只读检查顺序：

```bash
python3 --version
gcloud --version
gcloud auth list --filter=status:ACTIVE --format='value(status)'
gcloud config get-value project
python3 scripts/google_api_adapter.py bootstrap status --project-id PROJECT_ID --quota-project-id QUOTA_PROJECT_ID
python3 scripts/google_api_adapter.py auth probe --capability gsc-read
python3 scripts/google_api_adapter.py auth probe --capability ga4-read
```

不要把邮箱、token 或 credential path 放入报告。缺少精确 project/quota project 时不运行 `bootstrap status`；ADC 缺失时先把 `reauth_required` 与所需 capability/scopes 写入配置方案，再由操作者决定是否进行交互登录。

如果方案选择自建 Desktop OAuth client 的用户 ADC，首次授权 scope 必须包含 `openid`、`https://www.googleapis.com/auth/userinfo.email` 和 `https://www.googleapis.com/auth/cloud-platform`，再追加当前 GSC/GA4 capability 的最小 scope。否则浏览器登录即使完成，adapter 在后续 probe 刷新 token 时仍可能报 `reauth_required`。只读场景不得预先加入 `webmasters` 或 `analytics.edit`；完整命令和 quota project 说明见 [Google API Adapter](references/google-api.md#自建-desktop-oauth-client-的-adc-scope-基线)。

## Google API adapter

运行前置：Python 3.11+；若选择 API 模式，还需要已安装的 `gcloud`、已明确选择的 Cloud/quota project、已启用的 `searchconsole.googleapis.com`、`analyticsadmin.googleapis.com`、`analyticsdata.googleapis.com`，以及当前 ADC 身份对精确 GSC/GA4 资源的权限。adapter 不自动安装 CLI、不自动登录、不创建 service account，也不把 credential 文件复制进仓库。

常用只读入口：

```bash
python3 scripts/google_api_adapter.py bootstrap status --project-id PROJECT_ID --quota-project-id QUOTA_PROJECT_ID
python3 scripts/google_api_adapter.py gsc list-sitemaps --site-url 'sc-domain:example.com'
python3 scripts/google_api_adapter.py gsc search-analytics --site-url 'sc-domain:example.com' --start-date 2026-08-01 --end-date 2026-08-19 --dimension query --row-limit 1000
python3 scripts/google_api_adapter.py ga4 list-web-streams --property-id PROPERTY_ID
python3 scripts/google_api_adapter.py ga4 realtime --property-id PROPERTY_ID --metric activeUsers
```

`gsc search-analytics` 只接受起止日期、可重复的固定 dimension、search/data/aggregation 枚举、`row-limit` 与 `start-row`。默认使用 `WEB`、`FINAL`、`AUTO`、1000 行和 offset 0；不接受任意 JSON、filters 或 hourly 查询。输出的 clicks、impressions、CTR 与 position 是 GSC top aggregated rows；命中 row limit 只表示可能还有下一页，不代表完整导出或稳定快照，也不能证明页面已抓取或收录。

GSC sitemap 与 GA4 resource create 使用临时 `0700` task directory 内的单次 `0600` plan，apply 必须传回 plan digest 和 authorization fingerprint。`status_only`、`manual_readback` 无法到达写 endpoint；GSC ambiguous submit 的 recovery plan 还必须绑定原 authorization fingerprint，并受跨进程 15 分钟单次 claim 限制；GA4 create 响应不明确时只回读，不自动重放。公网 sitemap 预检只连接已解析并固定的公网地址，拒绝内网/metadata 目标和 DNS rebinding。

本地测试和 schema 只证明实现契约。2026-08-20 已用现有 ADC 对 `sc-domain:quasimorphwiki.site` 完成一次真实、受控的 Search Analytics 只读查询：限定日期窗口、`query` dimension、`FINAL` 数据、limit 100，共返回 11 行，`row_limit_reached=false`，聚合类型为 `BY_PROPERTY`；原始 query 行未写入包内报告。这只证明该精确 property/window 的只读 primitive 可用，不证明完整导出、稳定快照、sitemap/crawl/indexing，也不证明 GA4、Clarity、sitemap mutation、bootstrap 写入或完整 onboarding 已端到端验证；这些能力仍是 `missing evidence`。

## 安装状态

当前版本是本机 Governed Skill，canonical source 位于 `nemo-skills/skills/nemo-site-telemetry`，仅按需通过项目级 `.agents/skills/` 软链接安装，不建立全局 Codex skill 链接。尚未发布到 GitHub，不提供公共安装命令。

未来发布后才可把占位形式替换成真实仓库；当前不要执行：

```bash
npx skills add <published-repo> --skill nemo-site-telemetry
```

项目安装命令只创建软链接，不复制 Skill：

```bash
mkdir -p <project>/.agents/skills
ln -s /Users/nemo/Documents/AI/awesome-skills/nemo-skills/skills/nemo-site-telemetry <project>/.agents/skills/nemo-site-telemetry
```

当前只安装到 `game-site`、`image-generator`、`payforplus` 与 `new-api` 四个项目。

## 输出摘要

```text
readiness_check: partial / google_cli_login=available / google_adc=reauth_required / blockers=exact_cloud_project,adc
configuration_plan: ga4=blocked / clarity=not_requested / gsc=blocked / external_write=[]
site_preflight: verified / production=https://example.com / preview_isolation=verified
ga4: setup=existing / production_request=verified / realtime=verified
clarity: setup=created / tag_loaded=verified / production_request=verified / recording=pending
gsc: property=resumed / public_dns=verified / ownership=verified / sitemap=submitted / search_analytics=verified / indexing=unknown
recovery_checkpoint: saved / wait for Clarity recording readback
```

这些状态不可互相替代。尤其是：请求发出不等于 provider 已接收；sitemap 提交不等于页面已抓取或收录。

## 包验证

在 canonical skill 目录运行：

```bash
python3 /Users/nemo/Documents/AI/awesome-skills/qiaomu-meta-skill/scripts/validate_skill.py .
python3 /Users/nemo/Documents/AI/awesome-skills/qiaomu-meta-skill/scripts/trigger_eval.py . --cases evals/trigger_cases.json --output reports/trigger-eval.json
python3 /Users/nemo/Documents/AI/awesome-skills/qiaomu-meta-skill/scripts/export_skill_ir.py . --output reports/skill-ir.json
python3 /Users/nemo/Documents/AI/awesome-skills/qiaomu-meta-skill/scripts/release_check.py . --phase local --run-tests --output reports/release-check.json
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/google_api_adapter.py --help
```

## 风险边界

“接入/配置/上线”授权当前目标组件的常规精确创建与验证流程；删除资源、移除 owner、邀请用户、切换账号或 DNS zone、修改 nameserver、产生费用、长期授权第三方、发布隐私政策都必须另行明确授权。

启用 Google API、首次 OAuth consent、授予 service account/用户资源权限也属于独立 bootstrap 边界；普通状态查询不会隐式执行这些动作。

GA4 Measurement ID 和 Clarity Project ID 是前端公开标识，不是 API secret。cookie、OAuth token、DNS provider token、密码、GSC verification value 和未打码凭据截图不得进入 Skill、仓库或最终报告。

## Troubleshooting

- 生产请求可见但 GA4 Realtime 无数据：核对 Measurement ID、consent、filter、目标 property 和读取窗口；不要创建第二个 stream。
- Clarity `/collect` 可见但没有录屏：核对 Project ID、consent、bot exclusion 和 organization；把 recording 标为 pending。
- DNS provider 已保存但 GSC 验证失败：等待两个公共 resolver 匹配，不重复 TXT。
- 用户手动提交 sitemap 后暂时未在 GSC 读到：保持 `manual_readback` 与 `pending`，记录 checkpoint，不代替用户重复提交。
- preview 发出统计请求：视为隔离失败，修复 origin gate 后重新验证 production-positive 与 preview-negative。
