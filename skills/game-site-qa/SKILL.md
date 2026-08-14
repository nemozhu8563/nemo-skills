---
name: game-site-qa
description: "Verify a built overseas game site locally by checking real file hashes, build, lint, tests, links, assets, visual states, content review, canonical origin, old-domain residue, and rollback, then write launch-report.json and gate local_verified or deploy_ready. Use for 游戏站 QA、本地验收、首批五页人工审核、链接资产检查、视觉验收、旧域名扫描、launch-report.json、部署前门禁；not for model self-approval, silently waiving failed checks, executing deployment, changing DNS, or claiming a public URL works."
---

# Game Site QA

把“页面写完了”变成有命令、证据、人工审核和回滚方案的本地可发布事实，并严格停在外部动作之前。

## Dependency And Scope

- 机器契约来自同级必需依赖 `game-site-pipeline`；优先使用 `GAME_SITE_PIPELINE_SKILL_DIR`，其次解析 `../game-site-pipeline` 或项目 `.agents/skills/game-site-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：初次建站为 `build_ready`；扩页模式由 `$game-page-expander` 在 `grow` 中调用。
- 终点：初次建站依次进入 `local_verified` 和 `deploy_ready`；扩页模式保持 `grow`。
- 本 Skill 所有产物：`content-manifest.json 中的真实哈希和审核字段`、`launch-report.json`。不得直接编辑 `pipeline-state.json`；状态只能由中央 CLI 写入。

## Router Rules

- all real files and hashes match
- build/lint/tests/links/assets/visual/content checks pass or have justified not_applicable
- at least first five pages are reviewed by a human
- canonical origin, forbidden old origins and rollback are explicit
- 完整全链路或当前阶段不明时，回到 `$game-site-pipeline`；找词和 Semrush 核验使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 运行中央 `status` 和 `validate`，读取全部上游产物、项目命令和现有工作树。初次模式只接受 `build_ready`；扩页模式必须带 grow 批次上下文。
2. 逐页确认文件存在并刷新真实 SHA-256；manifest 与矩阵、证据的 page/source/claim 引用必须完全一致。
3. 运行项目实际配置的 build、lint、tests、links、assets 检查，并用浏览器检查代表性桌面/移动视图、加载/空/错误状态和主要交互。没有对应命令时可记 `not_applicable`，但必须写具体理由。
4. 生成首批页面审核清单。全站或本批少于 5 页时全部审核，否则至少 5 个不同页面由人审核并记录 `reviewed_by`、`reviewed_at`。模型自评不算人工审核；缺少人类结果时必须暂停。
5. 扫描 canonical origin、代码/内容中的旧域名残留，确认部署目标 revision 和可执行回滚步骤。把所有结果写入 `launch-report.json`，失败项保持 failed/not_run。
6. 初次模式先 `gate --target local_verified` 并转移；随后加入唯一 planned deployment action，`gate --target deploy_ready` 并转移。扩页模式运行 `validate --stage local_verified`，保持 `grow` 并交给 launch。
7. 最终分开报告自动检查、人类审核、本地视觉证据、未运行项和外部动作 blocker；不得把本地预览称为线上回读。

中央命令形态：

```bash
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 真实内容哈希和审核记录
- 七类本地检查及证据
- canonical/旧域名/回滚记录完整的 launch-report.json
- local_verified/deploy_ready gate 或 expansion validation 结果
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 只修改与验收证据直接相关的 manifest 和 launch report；修复代码仅在用户请求实现修复时进行。
- 人类审核是阻塞门，不能由模型代签或默认通过。
- 不推送、不部署、不买域名、不改 DNS、不创建 GSC/GA、不申请广告。
- 网络：none for local QA; browser access may inspect a local preview only。
- 交互：mandatory for first-batch human content review and unresolved visual acceptance。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 用一次 build 通过替代链接、资产、视觉和内容检查
- 把 not_applicable 当作无理由跳过
- 把本地 localhost 或 provider preview 当作公共线上成功
