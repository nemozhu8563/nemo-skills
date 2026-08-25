---
name: web-business-builder
description: "Implement planned Web business pages and functions from an approved page contract and claim evidence, then map every page, source, claim, path, review status, and content hash in content-manifest.json. Use for SaaS/工具/内容/线索/游戏站实现、功能页与落地页开发、content-manifest.json、证据驱动内容、把 researched 项目推进到 build_ready；not for changing the locked opportunity, inventing claims or UI, bulk thin-page generation, local release approval, deployment, or analytics setup."
---

# Web Business Builder

把页面矩阵和证据包变成真实可运行页面，同时保留逐页来源、claim、路径、状态和哈希的机器映射。

## Dependency And Scope

- 机器契约来自同级必需依赖 `web-business-pipeline`；优先使用 `WEB_BUSINESS_PIPELINE_SKILL_DIR`，其次解析 `../web-business-pipeline` 或项目 `.agents/skills/web-business-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：初次建站为 `researched`；优化/扩展模式仅由 `$web-business-expander` 在 `grow` 中调用。
- 终点：初次建站进入 `build_ready`；优化/扩展模式保持 `grow`。
- 本 Skill 所有产物：`用户项目中的页面/组件/内容文件`、`content-manifest.json`。不得直接编辑 `pipeline-state.json`；状态只能由中央 CLI 写入。

## Router Rules

- implementation matches the page function contract
- every planned page has exactly one manifest entry
- all public claims map to evidence
- generated files exist and placeholders are absent before handoff
- 完整全链路或当前阶段不明时，回到 `$web-business-pipeline`；机会发现仍由匹配的上游方法负责，只有 Steam/Roblox 游戏找词才使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 运行中央 `status` 和 `validate`，读取 candidate lock、page matrix、evidence pack、项目规则、Git 状态和现有实现。初次模式只接受 `researched`；优化/扩展模式必须带 grow 变更批次、模式及逐项验收条件。
2. 沿用项目已有框架、组件、样式和命令；不添加依赖或新抽象，除非当前页面确实需要且用户授权。保留用户已有修改。
3. 逐页按照功能契约实现：只出现允许字段、动作、状态和页面目标；营销解释、运营边界卡片或示例卡不得擅自进入工作流页。
4. 内容只使用 evidence pack 中能够追溯的事实，写原创表达。无法支撑的 claim 不进入页面；不得复制竞品品牌、文案、截图、CSS 或专有资产。
5. 写 `content-manifest.json`，使每个矩阵 `page_id` 唯一映射到项目相对路径、title、locale、primary keyword、source IDs、claim IDs、状态和实际 SHA-256。当前新增或修改页在 QA 人审前标为 `draft`；未改动且已存在于部署基线的页面才保留 `published`。禁止 `..` 路径和占位哈希。
6. 运行项目最小可行构建/类型检查以发现实现错误，但完整发布验收由 `$web-business-qa` 负责。
7. 初次模式运行 `gate --target build_ready`，通过后转移。优化/扩展模式运行 `validate --stage build_ready`，不改状态并交回 expander；现有页优化必须同步更新受影响的 manifest/source/claim/hash 映射。

中央命令形态：

```bash
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 契约内的真实页面和必要组件
- 逐页来源与 claim 映射完整的 content-manifest.json
- 最小实现检查结果
- build_ready gate 或 optimization/expansion validation 结果
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 只修改用户指定站点项目中与本批页面直接相关的文件。
- 不修改候选锁、页面矩阵、证据包或中央状态；发现上游错误时退回总编排器。
- 不提交、不推送、不部署、不改 DNS、不创建统计属性。
- 网络：none by default; package installation or external asset downloads require separate explicit scope。
- 交互：required for stack-changing choices or any page behavior outside the approved contract。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 为了未来复用重构整个站点
- 生成矩阵之外的薄页或语言版本
- 把模型自检称为人工内容审核或发布验收
