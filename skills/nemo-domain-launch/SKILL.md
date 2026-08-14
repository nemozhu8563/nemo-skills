---
name: nemo-domain-launch
description: "Governed first-domain launch for a project with no formal production domain, or only a provider URL such as pages.dev or vercel.app. Use when Nemo asks to deploy or bind a Spaceship domain through Cloudflare DNS using exactly one route: static_pages for Cloudflare Pages, or saas_vercel for Vercel-hosted SaaS/SSR. Deploys the selected provider target, verifies Cloudflare authoritative DNS, TLS and public routes, then idempotently writes the verified formal domain to project-root AGENTS.md. Do not trigger when the project already has a formal production domain, for domain purchase only, Vercel-only hosting without Cloudflare DNS, GitHub Pages, Git push, GSC/GA/ads, wildcard Vercel domains, arbitrary DNS deletion, credential extraction, or generic deployment advice."
---

# Nemo Domain Launch

给“尚无正式域名”的项目选择并执行一条发布路线，直到自定义域名在公网真实可用，再把结果写回项目根 `AGENTS.md`。Provider 状态、公共 DNS、HTTPS 内容、本机缓存和文件写回分别取证，不互相冒充。

## Activation Gate

1. 从项目根 `AGENTS.md`、README、环境变量示例、站点配置、hosting provider 和公共 DNS 做只读发现，把 `formal_domain_before.status` 记为 `absent`、`provider_default_only`、`present` 或 `unresolved`。
2. 只有 `absent` 或 `provider_default_only` 可以进入 mutation。`pages.dev`、`vercel.app` 等 provider 默认地址不算正式域名。
3. `present` 时不触发本 Skill；已有正式域名的故障维修、证书修复或迁移交给对应 provider/domain 运维流程。
4. `unresolved` 时继续只读发现，不用猜测替代门禁，也不部署、不改 DNS、不写 `AGENTS.md`。

## Deployment Router

| `deployment_mode` | 适用项目 | 固定路线 | Hosting action |
|---|---|---|---|
| `static_pages` | 已有可验证静态输出，可由 Cloudflare Pages 承载 | Spaceship → Cloudflare DNS → Cloudflare Pages | `pages_deploy` |
| `saas_vercel` | Vercel 承载的 SaaS、Next.js、SSR、Functions 或其他动态应用 | Spaceship → Cloudflare DNS → Vercel | `vercel_deploy` |

- 每次只能选一个 mode；另一条 hosting action 的 authorization、execution、readback 必须形成一致的 `not_required` 三元状态。
- 两条路线都要求 Spaceship 是 registrar、Cloudflare 是 authoritative DNS。单纯 Vercel 部署、其他 registrar 或其他 DNS provider 不触发。
- Vercel wildcard domain 要求 Vercel nameservers，与本 Skill 的 Cloudflare authoritative DNS 契约冲突；停止并另行决策，不能静默换路线。
- 游戏站全链路状态仍由 `$game-site-pipeline` / `$game-site-launch` 管理。本 Skill 返回独立证据，不直接篡改其中央状态。

## Required Inputs

- `project_dir`：当前项目的绝对根目录；最终只允许写 `project_dir/AGENTS.md`。
- `deployment_mode` 与 `formal_domain_before` 的状态、证据。
- 项目原生 `build_command` 和 check/test 命令；不得发明或静默替换。
- `static_pages`：项目原生 `output_dir`、Pages project、production branch。
- `saas_vercel`：精确 Vercel account/team、project、production deployment 或待发布 revision；输出目录可为 `null`。
- `production_origin`、`domain`、Spaceship registrar、Cloudflare zone，以及 apex/subdomain 模式。
- 本次精确动作集合：`pages_deploy`、`vercel_deploy`、`custom_domain_binding`、`dns_record_change`、`nameserver_change`、`dnssec_change`、`agents_md_writeback`。
- 至少一个代表性业务路径。`static_pages` 还要求 canonical、`robots.txt`、`sitemap.xml`；`saas_vercel` 无这些文件时可明确记 `not_required`，但已存在却指错域名时必须失败。

缺少输入时先从项目文件和 provider 当前状态只读发现。只有无法安全推导且会实质改变结果时才询问一个必要问题。

## Compact Workflow

1. **建立事实基线。** 记录 Git revision/dirty state、现有 provider 默认 URL、正式域名缺失证据、Cloudflare zone/DNS、公共 NS/DS 和 Spaceship 当前设置。创建脱敏 launch report，保存每个动作的授权、执行、回读和 rollback snapshot。
2. **运行项目原生验证。** 两种 mode 都先跑现有 build/check/test。`static_pages` 必须以最终 `production_origin` 重建输出，再运行 `scripts/preflight.py` 检查首页、代表性内页、canonical、robots 和 sitemap；不得部署旧产物。`saas_vercel` 按项目现有 Vercel 配置验证 build、env 名称和代表性流程，不读取或记录 secret value。
3. **验证身份和精确目标。** 复用已验证的 Cloudflare Wrangler OAuth/API 环境和 Vercel CLI/dashboard 会话，只读确认 account、project、zone 和 domain target。OAuth callback、token、Cookie、验证码、环境变量值和浏览器存储不得进入聊天、命令回显、报告或 fixture。
4. **执行唯一 hosting route。** `static_pages` 部署已验证的静态目录，记录 deployment ID、environment、source revision、终态和 `pages.dev` HTTPS 回读。`saas_vercel` 发布或复用精确 production deployment，记录 deployment ID/URL、READY 终态、source revision 和 `vercel.app` HTTPS 回读；优先复用同一已验证 artifact，不用重建掩盖问题。
5. **准备 Cloudflare authoritative DNS。** 创建或读取精确 zone，取得该 zone 实际分配的两台 nameserver；快照 Cloudflare 导入记录、Spaceship DNS、当前 NS 和父区 DS。Pages/Vercel binding、DNS record、NS 和 DNSSEC 是独立动作。
6. **绑定正式域名。** `static_pages` 必须先在 Pages 项目添加 custom domain，再依 provider 结果处理 DNS；只手工建 CNAME 可能产生 522。`saas_vercel` 必须先在目标 Vercel 项目添加 domain，再逐项复制该项目当前 Domain Settings 返回的 A/CNAME/TXT/verification 值到 Cloudflare；不得硬编码通用 target。Vercel 承载记录与第三方验证记录在验收阶段保持 DNS-only；启用 Cloudflare proxy 是上线后的独立 mutation。
7. **最小化切换。** 只删除“按 ID、类型、名称、内容精确匹配，已确认是停放记录，且确实阻塞目标”的记录，并保留可恢复快照。MX、TXT、CAA、邮件和验证记录默认保留。先正确处理旧 DNSSEC，再在 Spaceship 切到 Cloudflare 实际 nameservers，等待 zone Active。
8. **完成 DNSSEC（如在范围内）。** 普通迁移先移除旧 DS，等待父区 DS TTL 到期且公开查询为空，再切 NS。Cloudflare zone Active 后启用 signing，读取新 DS，再写入 Spaceship。至少两个验证递归解析器返回 `ad` 才能声明完成。未请求时整组动作写一致的 `not_required`。
9. **证明 `domain_ready`。** 回读 hosting provider 的 deployment/domain/certificate，运行 `scripts/verify_public.py` 检查 Cloudflare NS、目标 DNS、正式 HTTPS、TLS、根路径与代表性路径；按 mode 检查 SEO 文件。最后用 `scripts/validate_launch_report.py --require-domain-ready` 校验证据。
10. **写回并证明 `launch_complete`。** 仅在 `domain_ready=true` 后运行 `scripts/update_agents_domain.py`。它保留已有内容，缺文件时创建，只维护一个 `nemo-domain-launch` block，重复运行不追加；写后立即回读并更新 report。再用 `--require-launch-complete` 验证。

详细执行顺序见 [runbook](references/runbook.md)。Spaceship 能力见 [registrar adapters](references/registrar-adapters.md)。证据与回滚规则见 [evidence and rollback](references/evidence-and-rollback.md)。

## Mutation Protocol

每次写入都执行同一协议：

1. 解析精确 provider、account、project/zone、record/domain/file 和期望值。
2. 保存前值与 rollback action；DNS 删除保存完整 record snapshot，`AGENTS.md` 只记录文件是否存在和受管块是否存在，不复制私人内容到报告。
3. 检查当前用户指令是否覆盖这一动作。用户已明确要求本项目完整上线时，mode 对应部署、域名/DNS 切换和成功后的 `AGENTS.md` 写回属于该范围，不重复询问；购买域名、付费升级、Git push 和无关 DNS 永远不自动包含。
4. 只执行一个最小 mutation。
5. 立即做 provider/file readback，再做公共回读；传播中的状态写 `pending`，不盲目重试或扩大修改。
6. 记录时间、target、前值摘要、后值、证据 pointer 和 rollback 状态。

禁止 blind overwrite、批量清空 zone、按名称模糊删除、写死 Vercel DNS 值、多次无差别重试，以及用 Dashboard 绿色状态或本机缓存替代公网验证。

## Gate Ladder

- `scope_locked`：项目、mode、origin、domain、provider targets、registrar 和授权动作明确。
- `first_domain_eligible`：`formal_domain_before` 为 `absent` 或 `provider_default_only`，且有证据。
- `local_verified`：项目原生 build/check 通过；静态 mode 的正式 origin 产物预检通过。
- `hosting_deployed`：唯一 hosting action 终态和 provider 默认 URL 回读通过；另一 action 为一致 `not_required`。
- `zone_staged`：Cloudflare zone、目标 NS、DNS/DS 快照和 rollback 已记录。
- `nameservers_cut_over`：父区公开 NS 与 Cloudflare 分配值一致，旧 DS 已按路径处理。
- `custom_domain_active`：Pages 或 Vercel binding、hosting DNS、certificate 和正式域 HTTPS 均通过。
- `dnssec_active`：请求时要求 Cloudflare signing、父区 DS 和两个 resolver 的 `ad`；否则为 `not_required`。
- `domain_ready`：mode 对应 provider、公共 DNS、TLS、根路径和代表性路径满足契约，`missing_evidence` 为空。
- `agents_md_recorded`：项目根 `AGENTS.md` 的受管块精确回读成功。
- `launch_complete`：必须同时满足 `domain_ready` 与 `agents_md_recorded`。

任一 gate 失败就停在当前安全状态，执行对应回滚或给出下一条最小恢复动作，不跳级。

## AGENTS.md Managed Block

唯一允许写入的形态：

```md
<!-- nemo-domain-launch:begin -->
## Production deployment

- Formal domain: https://example.com
- Deployment mode: `static_pages`
- Route: Spaceship → Cloudflare DNS → Cloudflare Pages
<!-- nemo-domain-launch:end -->
```

- 现有 `AGENTS.md` 内容原样保留；不存在时可在项目根创建。
- 相同 block 再执行为 no-op；已有不同 block、重复/残缺 marker 或符号链接时失败关闭，不覆盖。
- 不写 account ID、zone ID、token、Cookie、deployment secret 或其他凭证。

## Output Contract

- `scope`：项目、mode、正式域名缺失证据、build/output、origin、Pages/Vercel project、domain、registrar、source revision。
- `actions`：七个动作分别记录 authorization、execution、readback、before 和 rollback；非当前 hosting route 为一致 `not_required`。
- `observations.provider`：Pages/Vercel deployment、Cloudflare zone、custom domain、certificate、hosting DNS、DNSSEC 分开记录。
- `observations.public_dns`：至少两个 resolver 的 NS、DS、A/AAAA/CNAME、hosting target 一致性与 DNSSEC `ad`。
- `observations.public_http`：provider 默认 URL、正式根路径、代表性路径、TLS，以及 mode 适用的 canonical/robots/sitemap。
- `observations.agents_md`：只记录状态、项目根路径和 managed block 名。
- `claims`：`domain_ready`、`launch_complete`、`dnssec_complete` 都必须由 validator 证明。
- `rollback`：DNS snapshot、旧 NS/DS、Pages/Vercel 上一个可用 deployment、最后安全检查点。

默认从 [launch report template](templates/launch-report.template.json) 开始。报告中不得出现 token、OAuth code、Cookie、密码、private key、浏览器 profile、完整 callback URL 或 secret 环境变量值。

## Trust, Rollback, And Degradation

- 使用最新 Cloudflare、Vercel 和 Spaceship 官方/实时状态校准命令、记录值和 UI；远端脚本只读审查，不直接执行。
- Pages 部署失败不改 DNS；Vercel 部署失败不绑定域名。Hosting 健康而 DNS 异常时优先修最小 DNS 问题，不盲目重部署。
- 回退已发布的 Cloudflare DS 时先移除新 DS、等待父区过期，再切旧 NS；不要先关闭 signing。
- 无 provider 写权限时只产出 preflight、inventory、mutation plan、rollback snapshot 和 `missing evidence`，不写 `AGENTS.md`。
- 无 registrar 会话时保留 hosting deployment 事实，停在 NS/DS handoff。
- 无 `dig` 时至少用两个命名公共 DNS API；本机缓存不能单独通过。
- 回滚计划不等于回滚完成；回滚后重新做 provider、公共 DNS、HTTPS 和文件回读。

## Non-goals

- 购买/转移域名、续费、套餐升级或其他成本动作
- 已有正式域名项目的日常部署、故障维修或迁移
- Vercel-only、GitHub Pages、容器平台或非 Cloudflare authoritative DNS 路线
- Vercel wildcard domain 的 nameserver 迁移
- 保存或索取 Cloudflare、Vercel、Spaceship 凭证
- 清空 DNS zone、删除邮件/验证记录或绕过 2FA
- Git push、GSC、GA、广告、数据库 migration 或游戏站中央状态

## Maintenance

- 每季度或 Cloudflare Pages/DNS/Wrangler、Vercel domains/deployments、Spaceship NS/DS 行为变化时复核 [official sources](references/official-sources.md)。
- 更新版本前运行 package validation、trigger eval、offline tests、secret scan、Skill IR 和 local release gate。
- Provider-backed 与人工 blind review 仍是 `missing evidence`，除非有独立、可复核的新证据写入 `reports/output-evidence.json`。
