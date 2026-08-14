---
name: game-page-expander
description: "Expand a proven grow game site with a finite batch of at least ten planned long-tail pages derived from real query or keyword opportunities, using reusable page prompts, independent evidence, differentiated content, first-five human review, and the existing QA-launch-telemetry re-entry chain. Use for 游戏站批量内页、grow 后扩页、至少十个内页规划、长尾页面生产线、首批五页审核、重新上线后 observing；not for thin-page spam, unverified mass generation, bypassing evidence or deployment, expanding hold/retire sites, or automating before the manual page workflow is proven."
---

# Game Page Expander

把已经能做好单篇内容的能力放大成有限批次：先规划至少十个真实搜索意图，再按同类几个一批生成、核验、人工审核并重走上线观察链。

## Dependency And Scope

- 机器契约来自同级必需依赖 `game-site-pipeline`；优先使用 `GAME_SITE_PIPELINE_SKILL_DIR`，其次解析 `../game-site-pipeline` 或项目 `.agents/skills/game-site-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：`grow`，且增长决定包含有效 GSC/关键词机会；单篇手动流程已被证明。
- 终点：本地扩页期间保持 `grow`；重走 QA、launch、telemetry 后回到 `observing`。
- 本 Skill 所有产物：`decision-log.md 中的扩页批次说明`、`由 planner/evidence/builder/qa/launch/telemetry 各自更新的既有产物`。不得直接编辑 `pipeline-state.json`；授权和状态只能由中央 CLI 写入。

## Router Rules

- at least ten candidate pages map to explicit search intents
- generation runs in small same-type batches after a manual page pattern works
- every page has independent evidence and differentiated useful content
- five new pages receive human review before relaunch
- 完整全链路或当前阶段不明时，回到 `$game-site-pipeline`；找词和 Semrush 核验使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 运行中央 `status`/`validate`，确认当前为 `grow`，并从已批准 growth decision 中提取真实 query/page/长尾机会。hold、retire、无 valid data 或单篇尚做不好时停止。
2. 先列至少 10 个候选内页：稳定 page ID、对应搜索词、用户问题、页面类型、预期独特信息和内部链接位置。去重 intent；不能仅换名字复制。
3. 写一份可复用的同类内页生产契约/提示：固定结构、必备字段、来源要求、格式、禁止编造、待确认标记和项目内容格式。它是生产约束，不是事实来源。
4. 以同类 2–3 个页面为一批调用 `$game-site-planner` expansion mode 更新矩阵，再用 `$game-site-evidence` 建双来源和 claim 证据，最后用 `$game-site-builder` 生成差异化内容与 manifest；每批失败即停。
5. 调用 `$game-site-qa` expansion mode 运行 build、标题/正文、内链、导航、SEO、资产和视觉检查，并由人审核至少 5 个新增页；本批少于 5 页则全部审核。模型自审不算。
6. 本地通过后仍保持 `grow`。只有用户逐项授权时才交给 `$game-site-launch` 重发并记录新 revision/HTTP 回读，再由 `$game-site-telemetry` 更新 snapshot 和观察窗口。
7. 所有更新产物通过中央 `gate --target observing` 后才执行 `grow -> observing`。根据审核结果决定下一批；不得一次铺几十上百页来掩盖单页质量问题。

中央命令形态：

```bash
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 至少十个内页的意图清单和有限批次计划
- 可复用但证据受限的页面生产契约
- 更新后的矩阵、证据、内容、QA 和人审结果
- 重发/telemetry handoff，或最终 observing gate
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 本 Skill 负责编排扩页批次；每类产物仍由对应阶段 Skill 写入。
- 没有精确授权时只做到本地 QA，不推送、不部署、不改 DNS。
- 不修改候选锁，不扩展 hold/retire 项目，不自动抓取受限来源。
- 网络：read-only research in planning/evidence; external relaunch is delegated to game-site-launch with exact authorization。
- 交互：required for batch scope, reusable prompt, first-five human review, relaunch actions and observation handoff。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 关键词一换就复制同一篇内容
- 没有真实来源也批量填充数值、技能或打法
- 一开始就写自动抓取/生成脚本替代尚未跑通的手工流程
