---
name: game-site-telemetry
description: "Verify Google Search Console and Google Analytics for a deployed overseas game site, record existing or explicitly authorized property setup, separate indexing from performance data, schedule day-7 and day-14 observation when data is missing, and return the pipeline to observing. Use for 游戏站 GSC/GA、统计回读、索引检查、sitemap、telemetry_verified、observing、第 7 天或第 14 天复盘；not for generic GSC SEO analysis, Google Indexing API submission, fabricated traffic, credential capture, growth decisions, or creating properties without authorization."
---

# Game Site Telemetry

把“装了统计”拆成属性真实存在、数据是否有效、页面是否收录和下一次观察时间四层证据，避免把配置成功当成流量验证。

## Dependency And Scope

- 机器契约来自同级必需依赖 `game-site-pipeline`；优先使用 `GAME_SITE_PIPELINE_SKILL_DIR`，其次解析 `../game-site-pipeline` 或项目 `.agents/skills/game-site-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：初次建站为 `deployed`；复查可从 `hold`；扩页重发可从 `grow` 且 launch readback 已更新。
- 终点：初次依次进入 `telemetry_verified` 与 `observing`；复查/扩页返回 `observing`。
- 本 Skill 所有产物：`analytics-snapshot.json`、`必要时由中央 CLI 写入的 gsc_setup/ga_setup 授权`。不得直接编辑 `pipeline-state.json`；授权和状态只能由中央 CLI 写入。

## Router Rules

- GSC and GA properties are read back separately
- existing and newly created properties are distinguished
- indexing, configuration and performance are separate evidence
- missing GSC data creates technical checks plus day-7/day-14 reviews
- 完整全链路或当前阶段不明时，回到 `$game-site-pipeline`；找词和 Semrush 核验使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 运行中央 `status`/`validate`，核对部署 URL、canonical origin、source revision 与 HTTP readback。初次、hold 复查和 grow 扩页三种模式必须明确，不能混用旧 snapshot。
2. 优先查找并读取用户已有的准确 GSC/GA property。`setup_mode: existing` 只记录 readback；若必须创建，则 `gsc_setup` 和 `ga_setup` 分别取得精确授权，不能用 deployment 授权代替。
3. 分别记录 GSC 与 GA 的 property ID、setup status、setup mode、readback time、data status、时间区间和真实指标。只读取页面/API 明确返回的值；无数据、权限错误和请求失败是不同状态。
4. 单独检查 sitemap 可达性、robots、canonical、内部链接、页面状态码和 GSC 索引证据。普通攻略页不得使用 Google Indexing API；URL Inspection 或 sitemap 提交也不能冒充已收录。
5. 写 `analytics-snapshot.json`。GSC 没有 valid data 时，记录技术检查和两个未来 review date，分别代表第 7 天和第 14 天；不得填造 clicks、impressions、queries 或 indexed pages。
6. 初次模式先 `gate --target telemetry_verified` 并转移，再补齐 observation 后 `gate --target observing` 并转移。`hold` 复查或 grow 扩页模式在新 snapshot 和全部前置证据更新后直接 gate/transition 到 `observing`。
7. 最终分开报告 property 配置、索引、性能数据、观察周期和 missing evidence；增长结论交给 `$game-site-growth`。

中央命令形态：

```bash
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- GSC 与 GA 独立的 property readback
- 索引、sitemap 和技术检查证据
- 带真实时间区间的 analytics-snapshot.json
- telemetry_verified/observing gate 和下一复查日期
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 只访问用户授权站点的 property 和公共 URL，不扩大到其他账号/站点。
- 不保存 OAuth token、Cookie、密码、service-account key 或浏览器存储。
- 不做 grow/hold/retire 决定，不提交普通页面到 Google Indexing API，不申请广告。
- 网络：read-only access to the exact authorized GSC/GA properties and public sitemap/pages; creation only with separate authorization。
- 交互：required for login, property selection ambiguity, CAPTCHA, or creating a new GSC/GA property。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 把 property 创建成功说成已有流量
- 用零填补尚未返回的数据
- 在没有授权时创建 GSC/GA 或读取其他站点
