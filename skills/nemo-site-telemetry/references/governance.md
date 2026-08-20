# Governance

## Authorization boundary

用户明确要求“接入/配置/上线/搞好”某个 telemetry 组件时，授权包含完成该组件所需且可预期的精确常规动作：

- 创建或复用目标 GA4 property/web stream；
- 创建或复用目标 Clarity project；
- 添加或恢复目标 GSC property；
- 在已确认的权威 DNS zone 新增一条必要验证记录；
- 执行 GSC Verify 并提交精确 sitemap；
- 修改当前站点代码/config 并运行本地验证。

“查看/检查 sitemap 是否已提交”“只查状态”或“我刚刚手动提交，帮我看结果”只授权公网检查与精确 GSC Sitemaps list/get 回读，不授权 submit 或 re-submit。只有明确提交请求，或当前上下文已明确要求完成 GSC 接入/配置/上线/搞好，才包含一次幂等提交授权。

部署/发布只有在用户请求包含上线、部署或明确允许部署时才执行。代码接入授权不自动授权 push、merge、生产部署或隐私政策发布。

`bootstrap enable-apis`、首次 Google OAuth consent、选择 Cloud/quota project、授予 `serviceusage.services.use`、把身份加入 GSC/GA4 资源是独立 Google API bootstrap 动作。普通 readback、sitemap 状态查询或 telemetry onboarding 检查不隐式授权这些动作。

以下动作必须单独确认：

- 删除 provider 资源、DNS 记录、sitemap、owner、用户或历史数据；
- 切换到不完全匹配的账号、organization 或 DNS zone；
- 邀请用户、提升权限或向第三方授予长期访问；
- 修改 nameserver/DNSSEC、计费套餐或产生费用；
- 发布或更改隐私/法律文本；
- Git commit、push、PR、merge 或生产部署（除非请求已明确包含该精确动作）。

## Trust boundary

- 站点源码/构建证明预期实现，不证明 provider 收到数据。
- 浏览器 Network 证明客户端请求，不证明 provider 完成处理。
- GA4 Realtime/DebugView、Clarity Dashboard/Recordings 和 GSC UI/API 是各自 provider 证据，不能跨 provider 推断。
- DNS provider 回读证明控制面保存，两个独立公共解析器才证明公共传播。
- GSC ownership 不证明 sitemap；sitemap 不证明 crawl/index。
- 成功 API write response 不证明 provider 业务状态；写后 exact list/get 才是 verified readback。
- GA4 Realtime API 不证明 DebugView，GSC URL Inspection 不等于请求收录。
- API 与浏览器返回不同账号或 resource identity 时阻断；browser fallback 不扩大动作权限。
- production-only/preview isolation 是本 Skill 的治理选择，不是 provider 官方强制条件。

## Secret handling

允许进入前端与非秘密 config：

- GA4 Measurement ID；
- Clarity Project ID；
- public production origin。

不得持久化或回显：

- cookie、session、OAuth access/refresh token；
- Google/Microsoft/provider 密码与恢复信息；
- DNS/API token、service-account private key；
- 完整 GSC verification value；
- gcloud ADC access token、JWT、OAuth code、credential path 与 service-account JSON 内容；
- 含上述内容的未打码截图、HAR、日志或命令输出。

发现长期凭据进入仓库时停止使用并建议轮换；不得复制进 Skill 包。

## Idempotency

- GA4：精确 account/property/stream URL 查找；相同复用，不按名称模糊匹配。
- Clarity：精确 organization/project/site URL 查找；相同复用。
- GSC：精确 property type/value、TXT type/name/content、sitemap absolute URL 查找。
- Code：查找 GTM/plugin/已有脚本，避免重复初始化。
- Browser：重连后先读现有 tab 与 provider 状态。

任何写操作超时都先 read-after-write。

Google API adapter 的 plan 只保存 target/authorization fingerprint、时间和 credential-free inputs；临时 task directory 为 `0700`、plan 为 `0600`，并绑定 owner、非 symlink、10 分钟 TTL、canonical digest 和单次 apply。长期 checkpoint 不保存 plan、token 或 credential path。

## Rollback boundary

- 代码层：可移除本次注入并重新构建/部署，但要确认未删除站点原有 telemetry。
- provider 层：不自动删除 GA4 property/stream、Clarity project 或 GSC property/sitemap。
- DNS：验证成功后不自动删除 TXT；Google 周期性复查，删除可能使 ownership 过期。
- 错误外部资源：精确回读目标与创建证据，说明影响，获得单独授权后删除，再从 provider/public endpoint 回读。

## Claim guard

| 声明 | 最低证据 |
|---|---|
| GA4 已配置 | 精确 stream + production code readback |
| GA4 生产请求已发送 | production Network request matched |
| GA4 已接收近期数据 | 目标 property Realtime 或 DebugView readback |
| Clarity tag 已加载 | production tag load readback |
| Clarity 已发送数据 | production `/collect` POST |
| Clarity 录屏可见 | 目标 project Recordings/Dashboard readback |
| DNS 已传播 | provider + 两个公共 resolver matched |
| GSC ownership 已验证 | property verified + Owner readback |
| sitemap 已提交 | GSC 列表/API 中存在精确 URL |
| 页面已抓取/收录 | 独立 GSC crawl/index evidence |

缺少最低证据时使用 `pending`、`unknown` 或 `missing evidence`。
