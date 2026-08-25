---
name: web-business-expander
description: "Optimize existing pages or add new pages for a proven grow Web business from an approved data retrospective, real query/page evidence, explicit hypotheses, and testable acceptance criteria. Select a finite change batch from evidence strength, risk, dependencies, and human review capacity; update the existing planner-evidence-builder artifacts, human-review every changed page, and reuse the QA-launch-telemetry re-entry chain. Use for 按复盘优化 Web 业务、现有页转化/CTR/内容/内链改进、grow 后扩页、真实新意图、有限变更批次、重新上线后 observing；not for data review without an execution decision, thin-page spam, fixed-count bulk generation, bypassing evidence or deployment, changing hold/retire sites, or automating before the manual workflow is proven."
---

# Web Business Expander

把已批准的数据复盘转成一个可验证的站点变更批次：既能优化现有页面，也能新增页面；边界由证据、风险、依赖和可完整审核的能力决定，不由“1–3 页”或“至少 10 页”决定。

## Dependency And Scope

- 机器契约来自同级必需依赖 `web-business-pipeline >=1.0.0`；优先使用 `WEB_BUSINESS_PIPELINE_SKILL_DIR`，其次解析 `../web-business-pipeline` 或项目 `.agents/skills/web-business-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：`grow`，且已批准的 growth decision 包含有效 GSC/query/page 机会；目标页面类型的手工实现与审核方式已经可执行。
- 终点：本地优化或扩展期间保持 `grow`；重走 QA、launch、telemetry 后回到 `observing`。
- 本 Skill 所有产物：`decision-log.md 中的变更批次说明`、`由 planner/evidence/builder/qa/launch/telemetry 各自更新的既有产物`。不得直接编辑 `pipeline-state.json`；授权和状态只能由中央 CLI 写入。

## Router Rules

- exactly one mode is selected: `optimize-existing` or `expand-new`
- every change item records evidence, target, problem, expected impact and acceptance criteria
- every change item names one funnel stage and one primary success metric
- batch size follows evidence, risk, dependencies and full-review capacity, never a fixed page count
- existing pages keep stable page IDs; only new pages receive new IDs
- every changed page receives human review before relaunch
- 完整全链路或当前阶段不明时，回到 `$web-business-pipeline`；只做数据复盘和 grow/hold/retire 决策时使用 `$web-business-growth`；机会发现仍由匹配的上游方法负责，只有 Steam/Roblox 游戏找词才使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 运行中央 `status`/`validate`，确认当前为 `grow`，并读取已批准 growth decision、当前部署 revision、页面矩阵、证据包、内容清单和 analytics snapshot。hold、retire、无 valid data 或没有具体机会时停止。
2. 选择且只选择一种模式：
   - `optimize-existing`：改进已有页面的意图承接、标题/摘要、首屏、内容结构、claim、内链、导航或可用性；保持稳定 `page_id`。
   - `expand-new`：为尚未被现有页面承接的真实搜索意图新增页面；创建新 `page_id` 并先消除关键词蚕食。
3. 建立变更项清单。每项记录 `change_id`、目标 page ID/route、证据引用、可观察问题、改动假设、`funnel_stage`（`search_growth`、`conversion_learning` 或 `commercial_scale`）、`primary_success_metric`、基线/时间窗、预期影响、验收条件、风险、依赖和回滚影响。每项只允许一个主要成功指标，其余作为 guardrail；新增页还要记录 primary keyword、用户问题、页面类型、独特信息和内部链接位置。
4. 选择能够验证假设、覆盖必要依赖且可以逐页完成人工审核的最小连贯批次。批次可以是一页或多页；不设最小或固定目标页数。若主要指标没有可靠基线，先把测量或页面契约修复作为本轮工作；证据弱、共享组件影响面过大或审核能力不足时，缩小批次或停止。
5. 只有存在可重复的同类工作时才写生产契约/提示，明确固定结构、必备字段、来源要求、禁止编造、待确认标记和项目内容格式。提示是生产约束，不是事实来源。
6. 调用 `$web-business-planner` 的 optimization/expansion mode 更新矩阵，再用 `$web-business-evidence` 更新来源与 claim，最后用 `$web-business-builder` 更新页面和 manifest。现有页优化必须同步其受影响的 matrix/evidence/manifest 记录；新增页必须完成全部新记录。任何一步失败即停。
7. 调用 `$web-business-qa` 的 optimization/expansion mode 运行 build、标题/正文、内链、导航、SEO、资产和视觉检查。manifest 中 `status: reviewed` 标识当前变更批次，`status: published` 只保留给未改动的部署基线页；每个变更页都完成人工审核并记录 reviewer/time，模型自审不算。
8. 本地通过后仍保持 `grow`。只有用户逐项授权时才交给 `$web-business-launch` 部署并记录新 revision/HTTP 回读，再由 `$web-business-telemetry` 更新 snapshot 和观察窗口。
9. 所有更新产物通过中央 `gate --target observing` 后才执行 `grow -> observing`。下一轮依据新数据重新决策；不得在同一轮继续扩大范围来掩盖未通过的假设。

中央命令形态：

```bash
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 明确的 `optimize-existing` 或 `expand-new` 模式
- 带证据、目标、问题、funnel stage、主要成功指标、预期影响和验收条件的有限变更批次
- 更新后的矩阵、证据、内容、QA 和全批次人审结果
- 重发/telemetry handoff，或最终 observing gate
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 本 Skill 负责编排优化/扩展批次；每类产物仍由对应阶段 Skill 写入。
- 没有精确授权时只做到本地 QA，不推送、不部署、不改 DNS。
- 不修改候选锁，不改变 hold/retire 项目，不自动抓取受限来源。
- 网络：read-only research in planning/evidence; external relaunch is delegated to web-business-launch with exact authorization。
- 交互：required when mode or scope materially branches the outcome, for every changed-page human review, relaunch actions and observation handoff。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 用固定页数把不同风险和证据强度的工作伪装成同一种批次
- 关键词一换就复制同一篇内容，或没有真实来源也批量填充数值、功能或结论
- 一开始就写自动抓取/生成脚本替代尚未跑通的手工流程
