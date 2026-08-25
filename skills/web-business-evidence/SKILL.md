---
name: web-business-evidence
description: "Build the claim-level evidence pack for a planned Web business, giving every page independent source lineages and binding claims that require current trust to current official or trusted evidence. Use for Web 出海素材研究、逐页双来源、evidence-pack.json、claim 核验、价格/功能/数值/日期/官方链接验证；not for SERP page planning, copying competitor articles, writing unsupported content, page implementation, or treating AI summaries as sources."
---

# Web Business Evidence

把“有素材”升级为逐页可引用、逐条 claim 可核验的证据包，让后续内容无法用相似产品、竞品转述或模型记忆补空。

## Dependency And Scope

- 机器契约来自同级必需依赖 `web-business-pipeline`；优先使用 `WEB_BUSINESS_PIPELINE_SKILL_DIR`，其次解析 `../web-business-pipeline` 或项目 `.agents/skills/web-business-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：初次建站为 `planned`；优化/扩展模式仅由 `$web-business-expander` 在 `grow` 中调用。
- 终点：初次建站进入 `researched`；优化/扩展模式保持 `grow`。
- 本 Skill 所有产物：`evidence-pack.json`。不得直接编辑 `pipeline-state.json`；状态只能由中央 CLI 写入。

## Router Rules

- every page references at least two distinct source lineages
- claims marked `current_trusted` have current official or trusted evidence
- missing evidence stays missing
- competitor prose and proprietary assets are not copied
- 完整全链路或当前阶段不明时，回到 `$web-business-pipeline`；机会发现仍由匹配的上游方法负责，只有 Steam/Roblox 游戏找词才使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 运行中央 `status` 和 `validate`，读取不可变候选锁及完整页面矩阵。初次模式只接受 `planned`；优化/扩展模式必须带 grow 变更批次、模式及逐项验收条件。
2. 建立 source registry：稳定 `source_id`、URL、标题、来源类型、可靠性、`retrieved_at`，对时效性来源填写 `current_as_of`。同一原文的镜像、AI 摘要或竞品转述只算一条 lineage。
3. 为每个 `page_id` 绑定至少两个不同来源。至少有一条能够支撑该页核心事实；社区内容可发现线索，但不能单独支撑敏感 claim。
4. 逐条登记将公开出现的 claim，并明确 `evidence_requirement`。标记为 `current_trusted` 的价格、数值、日期、版本/可用状态、官方链接或其他时效敏感事实，必须由当前 `official|trusted` 来源支撑，并记录验证状态与时间；`standard` 也必须有适合该事实的真实来源。
5. 冲突、过期或无法确认的事实保持 `unverified` 或从页面范围移除；不得估算、补零、借用相似产品数据或把模型判断当来源。
6. 初次模式运行 `gate --target researched`，通过后才转移。优化/扩展模式运行 `validate --stage researched`，不改状态并交回 expander；现有页改动同步更新其来源与 claim 映射。

中央命令形态：

```bash
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 来源注册表及可靠性/时效信息
- 逐页至少两条独立来源覆盖
- claim 到 source 的可审计映射
- researched gate 或 optimization/expansion validation 结果
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 只写 evidence-pack.json 和用户明确需要的本地研究说明。
- 不保存 Cookie、token、密码、浏览器存储或私有账号配置。
- 不修改页面矩阵、内容文件、候选锁、状态文件或远端来源。
- 网络：read-only public source research; authenticated or private sources require explicit scope and no credential capture。
- 交互：required when source trust, freshness or conflicting claims cannot be resolved from evidence。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 复制竞品全文或专有数据
- 用 AI 摘要制造第二来源
- 在证据不足时补出价格、功能、数字、日期、可用状态或官方 URL
