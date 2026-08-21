# nemo-supabase-auth

> 为明确的 Web 项目配置、审计或修复 Supabase Google Auth，并用真实登录和受保护会话完成证据闭环。

当前状态：`0.1.0`，Nemo 本地 Governed Skill，尚未发布到 GitHub。

## 它解决什么

这个 Skill 把容易混在一起的四层拆开：

1. Google Cloud project、Auth audience/branding/scopes 与 OAuth Web client。
2. Google 的 Supabase provider callback。
3. Supabase Site URL、Redirect URLs 与应用 `redirectTo`。
4. 应用 PKCE callback、可信用户校验与受保护页面。

它会先复用兼容的已有资源。只有明确要求新建，或确认没有兼容 project/client，才创建新的 Google 资源。

## 安装

Canonical source：

```text
/Users/nemo/Documents/AI/awesome-skills/nemo-skills/skills/nemo-supabase-auth
```

当前只安装到 `payforplus`，使用项目级软链接，不复制目录：

```bash
ln -s /Users/nemo/Documents/AI/awesome-skills/nemo-skills/skills/nemo-supabase-auth \
  /Users/nemo/Documents/AI/project/payforplus/.agents/skills/nemo-supabase-auth
```

不要对这个本地限定范围的 Skill 运行 `npx skills add`，也不要创建全局入口。

验证：

```bash
test -r /Users/nemo/Documents/AI/project/payforplus/.agents/skills/nemo-supabase-auth/SKILL.md
```

## 你可以直接这样说

- “给当前项目配置 Supabase Google 登录，先复用已有 Google OAuth client，没有再新建。”
- “在我的 Google 账号里为这个项目新建 Cloud project 和 Web client，再接到 Supabase。”
- “修复 Supabase Google 登录的 `redirect_uri_mismatch`，验证真实登录和 session。”
- “审计 Site URL、Redirect URLs、PKCE callback 和 Google provider，不要改配置。”
- “只把 Google/Supabase 配置做到 ready；先不要创建真实用户。”

它不会触发于通用 Supabase 数据库任务、GitHub 登录等非 Google provider、Google Drive/Gmail API、纯原理解释、Auth pentest 或要求导出凭证的请求。

## 最重要的 URL 区分

```text
Google redirect URI
  https://<project-ref>.supabase.co/auth/v1/callback

Supabase Redirect URL and app redirectTo
  https://app.example.com/auth/callback
```

前者把 Google 带回 Supabase；后者再把 Supabase 带回应用。两者互换会造成 mismatch、登录循环或回到错误页面。

## 成功定义

```text
configuration_ready:
  current docs checked
  application callback contract passed
  exact URL matrix passed
  Google project/client/audience/scopes read back
  Supabase provider/Site URL/Redirect URLs read back

end_to_end_verified:
  configuration_ready
  real Google login authorized and completed
  callback chain completed
  trusted server-side user signal passed
  protected route passed
  logout negative check passed
```

Dashboard 显示 `Enabled`、OAuth endpoint 返回 HTTP 200、或能打开 Google account chooser，都不能单独证明端到端成功。

## 凭证边界

Client secret 由用户直接填入已确认的 Supabase UI 或批准的 secret store。Skill 不要求把它复制进聊天、shell、报告、fixture、截图或源码，也不读取 Cookie、token、邮箱、user ID 或 browser storage。

真实登录可能创建 Google consent grant、Supabase user 和 session，必须在执行前确认该动作已经授权。删除用户、删除 OAuth client、撤销 grant、发布 OAuth app 都是新的独立动作。

## 本地验证

验证一个脱敏运行报告：

```bash
python3 scripts/validate_report.py /absolute/path/to/oauth-report.json
python3 scripts/validate_report.py /absolute/path/to/oauth-report.json --require-end-to-end
```

验证 Skill package：

```bash
python3 ../../../qiaomu-meta-skill/scripts/validate_skill.py .
python3 ../../../qiaomu-meta-skill/scripts/export_skill_ir.py . --output reports/skill-ir.json
python3 ../../../qiaomu-meta-skill/scripts/trigger_eval.py . --cases evals/trigger_cases.json --output reports/trigger-eval.json
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Troubleshooting

| 症状 | 先检查 | 不要误判 |
|---|---|---|
| `redirect_uri_mismatch` | 请求实际 redirect URI 与 Google Web client 的精确回读值 | 不要把 app callback 填入 Google redirect URI |
| Google 登录后回首页 | Supabase Site URL、Redirect URLs、应用 `redirectTo` | Provider Enabled 不证明回跳正确 |
| callback 有 code 但没有 session | PKCE `exchangeCodeForSession`、SSR cookie adapter、错误分支 | 不要记录完整 callback URL |
| 本地能用、生产失败 | 生产 callback 是否精确 allowlist、scheme/host/path/尾斜杠 | 不要用宽泛 production wildcard |
| Supabase 有用户但页面仍未登录 | 服务端可信用户检查、callback cookie 写入、protected route | 用户行存在不等于当前请求有 session |

## Prior art

设计复用了 Supabase 官方 Skill 的 current-doc/readback 边界、`nextjs-supabase-auth` 的 PKCE callback、通用 OAuth Skill 的 exact redirect/PKCE 原则、Supabase auth audit Skill 的配置核查，以及 `nemo-domain-launch` 的 Governed mutation ledger。没有复制 provider-specific boilerplate 或 pentest mutation。

Declared upstream_inspiration: `['openai-curated-supabase:supabase', 'sickn33/agentic-awesome-skills:nextjs-supabase-auth', 'mcollina/skills:oauth', 'yoanbernabeu/supabase-pentest-skills:supabase-audit-auth-config', 'nemo-skills:nemo-domain-launch']`

## License

MIT
