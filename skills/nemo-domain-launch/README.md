# nemo-domain-launch

> 给尚无正式生产域名的项目完成一条可验证、可回滚的首域名发布路线，并在成功后把正式地址幂等写入项目根 `AGENTS.md`。

当前状态：`0.2.0`，Nemo 本地 Governed Skill，尚未发布到 GitHub。

## 两条支持路线

| Mode | 项目类型 | 路线 |
|---|---|---|
| `static_pages` | 可生成静态输出的站点 | Spaceship → Cloudflare DNS → Cloudflare Pages |
| `saas_vercel` | Vercel 承载的 SaaS、Next.js、SSR 或 Functions 应用 | Spaceship → Cloudflare DNS → Vercel |

只有项目没有正式域名，或只有 `pages.dev` / `vercel.app` 默认地址时才使用。项目已有正式域名时，本 Skill 不负责普通部署、证书维修或迁移。

## 安装

本地 canonical source 是：

```text
/Users/nemo/Documents/AI/awesome-skills/nemo-skills/skills/nemo-domain-launch
```

它只安装到 `game-site` 和 `payforplus`，不建立全局入口，也不复制目录：

```bash
ln -s /Users/nemo/Documents/AI/awesome-skills/nemo-skills/skills/nemo-domain-launch \
  /Users/nemo/Documents/AI/project/game-site/.agents/skills/nemo-domain-launch

ln -s /Users/nemo/Documents/AI/awesome-skills/nemo-skills/skills/nemo-domain-launch \
  /Users/nemo/Documents/AI/project/payforplus/.agents/skills/nemo-domain-launch
```

即使未来公开发布，也不改变这个作用域：只在 `game-site` 和 `payforplus` 建立项目级链接，不创建全局安装入口。不要对本 Skill 运行 `npx skills add`；该命令不能表达这两个项目的限定范围，应只使用上面的项目级 `ln -s` 命令。

验证：

```bash
test -r /Users/nemo/Documents/AI/project/game-site/.agents/skills/nemo-domain-launch/SKILL.md
test -r /Users/nemo/Documents/AI/project/payforplus/.agents/skills/nemo-domain-launch/SKILL.md
```

## 你可以直接这样说

- “这个静态站还没有正式域名，把 Spaceship 域名经 Cloudflare Pages 上线。”
- “这个 SaaS 现在只有 vercel.app 地址，接到 Cloudflare DNS 和 Vercel。”
- “先判断当前项目有没有 production domain；没有的话选择正确路线完成部署。”
- “部署、DNS、TLS 和页面都验证成功后，把正式域名写进项目根 AGENTS.md。”

这些请求不会触发：只买域名、已有正式域名的普通维护、只部署到 Vercel 而不使用 Cloudflare DNS、GitHub Pages、GSC/GA/广告、Git push、Vercel wildcard domain。

## 工作方式

1. 读取项目根文档、配置、provider 默认 URL 和公共 DNS，证明正式域名为 `absent` 或 `provider_default_only`；`unresolved` 不允许进入 mutation。
2. 根据运行时选择唯一 mode；另一 hosting action 必须完整标为 `not_required`。
3. 运行项目已有 build/check/test。静态路线还会以最终 origin 重建并检查输出中的 canonical、robots、sitemap 和代表性内页。
4. 部署到 Pages 或 Vercel，回读 deployment ID、终态和 provider 默认 URL。
5. 在 Cloudflare 建立 authoritative DNS，快照 Spaceship 当前 DNS、NS 和 DS，再按安全顺序切换。
6. Pages 路线先绑定 Pages custom domain；Vercel 路线先添加 Vercel domain，再复制该项目当时返回的精确 A/CNAME/TXT 值。不会写死通用 Vercel DNS target。
7. 从 provider、两个公共 resolver、TLS/HTTPS 和页面内容四条证据链证明 `domain_ready`。
8. 运行受管写回脚本，保留原 `AGENTS.md` 内容；相同域名重复执行为 no-op。只有写回回读成功后才声明 `launch_complete`。

## 成功定义

```text
first_domain_eligible: passed
deployment_mode: static_pages | saas_vercel
hosting_deployed: passed (selected provider deployment ID recorded)
inactive_hosting_route: not_required / not_required / not_required
cloudflare_authoritative_dns: passed on at least two public resolvers
custom_domain_and_tls: passed
domain_ready: passed
agents_md_recorded: passed (single nemo-domain-launch managed block)
launch_complete: passed
```

Provider 显示 `READY` / `Active`、本机浏览器能打开、文件成功写入，任何一个都不能单独代表完整上线。

## 主要输入

| 输入 | 必需 | 说明 |
|---|---:|---|
| `project_dir` | 是 | 当前项目绝对根目录；最终只写这里的 `AGENTS.md` |
| `deployment_mode` | 是 | `static_pages` 或 `saas_vercel` |
| `formal_domain_before` | 是 | `absent` / `provider_default_only` 及证据 |
| `build_command` | 是 | 项目已有命令 |
| `output_dir` / `pages_project` | 静态路线 | 已验证静态输出和 Pages project |
| `vercel_project` | SaaS 路线 | 精确 Vercel account/team/project |
| `production_origin` | 是 | `https://example.com`；首次绑定前可尚未公网可达 |
| `domain` / `registrar` | 是 | Spaceship 域名及 apex/subdomain |
| 授权动作 | 是 | mode 对应部署、binding、DNS、NS、DNSSEC、最终 AGENTS 写回 |

交互式操作复用现有 Wrangler/Vercel/browser 会话。Headless 模式只引用环境变量名。不要在聊天、报告或 shell 配置中粘贴 token、OAuth callback、Cookie、验证码、私钥或 secret 环境变量值。

## 本地验证命令

静态产物预检：

```bash
python3 scripts/preflight.py /path/to/project \
  --output-dir dist \
  --origin https://example.com \
  --representative-path /guide/
```

公网验证：

```bash
python3 scripts/verify_public.py example.com \
  --expected-origin https://example.com \
  --representative-path /guide/ \
  --require-cloudflare-ns \
  --require-dnssec
```

SaaS 应用没有 canonical/robots/sitemap 时，可在确认它们确实不适用后增加：

```bash
--allow-missing-canonical --allow-missing-seo-files
```

域名证据通过后写回：

```bash
python3 scripts/validate_launch_report.py launch-report.json --require-domain-ready
python3 scripts/update_agents_domain.py launch-report.json
python3 scripts/validate_launch_report.py launch-report.json --require-launch-complete
```

Package 自检：

这里的 `qiaomu-meta-skill` 只是当前使用的 authoring/validation 工具名；成品 Skill 的名称、owner 和安装入口均为 Nemo。

```bash
python3 ../../../qiaomu-meta-skill/scripts/validate_skill.py .
python3 ../../../qiaomu-meta-skill/scripts/export_skill_ir.py . --output reports/skill-ir.json
python3 ../../../qiaomu-meta-skill/scripts/trigger_eval.py . --cases evals/trigger_cases.json --output reports/trigger-eval.json
python3 -m unittest discover -s tests -p 'test_*.py'
```

## 关键风险边界

- `pages_deploy`、`vercel_deploy`、`custom_domain_binding`、DNS、NS、DNSSEC、`agents_md_writeback` 分别记账。
- Pages 必须先建立 custom-domain binding；只有 DNS record 可能返回 522。
- Vercel DNS 值必须从当前项目 Domain Settings 实时读取；验收阶段保持 DNS-only。Cloudflare proxy 是后续独立 mutation。
- Vercel wildcard domain 要求 Vercel nameservers，不属于本 Skill。
- 普通 DNSSEC 迁移不能在旧 DS 仍生效时直接更换 nameserver。
- 任何 DNS 删除都要按 ID、类型、名称、内容精确匹配，并保存完整快照。
- 写回只管理一段 marker block；遇到不同 block、重复 marker 或 symlink 会失败关闭。

## Troubleshooting

| 症状 | 判断 | 最小处理 |
|---|---|---|
| `pages.dev` 正常、正式域失败 | Pages binding、NS/DNS 或证书未完成 | 分别回读 Pages domain、Cloudflare zone、公共 DNS 和 TLS |
| `vercel.app` 正常、正式域失败 | 域未加到正确 Vercel project，或 Cloudflare 记录值/代理状态错误 | 重新读取该项目 Domain Settings，逐项比对记录和值 |
| NS 已改但 `SERVFAIL` | 旧 DS 与新权威区不兼容 | 检查父区 DS，按 rollback report 恢复或完成正确迁移 |
| HTTPS 正常但 canonical 是默认域 | 构建未使用正式 origin，或部署了旧 artifact | 以正式 origin 重建并重新执行 mode 对应验证 |
| `domain_ready=true` 但写回失败 | AGENTS target/marker 冲突或 symlink | 保留现有文件，修正精确冲突后重跑；不覆盖私人规则 |

## Prior art

设计参考 Cloudflare/Vercel 官方文档、`genericService/claude-skills`、`bm629/agent-skills`、`makerjackie/jackie-skills-starter`、Render 官方 Skill、`lovstudio/skills` 和本地 `game-site-launch`。从 Vercel prior art 中明确拒绝了硬编码通用 CNAME、把 token 写入 shell profile、固定 sleep 后即宣布成功等做法。详细证据见 `reports/prior-art-research.md`。

Declared upstream_inspiration: `['genericService/claude-skills:cloudflare-pages', 'bm629/agent-skills:cloudflare-pages-ops', 'makerjackie/jackie-skills-starter:cloudflare-dns', 'render-oss/skills:render-static-sites', 'lovstudio/skills:deploy-to-vercel', 'nemo-skills:game-site-launch']`

## License

MIT
