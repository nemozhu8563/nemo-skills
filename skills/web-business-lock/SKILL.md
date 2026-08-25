---
name: web-business-lock
description: "Lock one human-approved, upstream-qualified Web business opportunity into immutable identity, qualification, business-hypothesis, and pipeline state records. Use for 候选锁定、需求人工确认、candidate lock、上游机会进入 Web 出海业务流水线、稳定 provider identity、生成 candidate-lock.json；not for discovering opportunities, silently selecting a winner, inventing or relaxing qualification checks, or rewriting an existing candidate lock."
---

# Web Business Lock

把任一上游方法产出的“可进入复核”候选，变成一个由人精确批准、身份不含糊、资格证据可追溯且不可原地改写的 Web 业务项目起点。

## Dependency And Scope

- 机器契约来自同级必需依赖 `web-business-pipeline`；优先使用 `WEB_BUSINESS_PIPELINE_SKILL_DIR`，其次解析 `../web-business-pipeline` 或项目 `.agents/skills/web-business-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：带完整资格检查的合格上游候选，且当前项目尚无 `candidate-lock.json`。
- 终点：创建 `candidate_locked`。
- 本 Skill 所有产物：`candidate-lock.json`、`pipeline-state.json`、`decision-log.md`。不得直接编辑 `pipeline-state.json`；状态只能由中央 CLI 写入。

## Router Rules

- candidate still passes every recorded upstream qualification check
- provider identity is explicit and non-ambiguous
- exact current human confirmation exists
- `business_hypothesis` keeps the customer, problem, value, business model, acquisition channel, primary value event, riskiest assumption and unknowns explicit
- existing candidate lock is never overwritten
- 完整全链路或当前阶段不明时，回到 `$web-business-pipeline`；机会发现与资格规则由匹配的上游方法负责，只有 Steam/Roblox 游戏找词才使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 读取上游候选与原始证据，逐项核对 `qualification.status`、`method`、`checked_at` 和全部 `checks`。每项检查必须有 criterion、真实状态、证据引用与原始 observations；中央阶段不自行发明 KD、趋势、搜索量或其他垂直阈值。
2. 保留稳定的 `<namespace>:<slug>` key，并记录足以消歧的 `identities[{provider,id}]`。没有外部平台 ID 时使用项目已有的稳定内部 ID；同名但 provider/id 不同的对象不能合并。
3. 若当前用户指令没有精确确认候选 key、批准人和具体理由，展示 key、名称、provider identities、资格证据和 `business_hypothesis` 后提出一个阻塞式确认问题；用户回答前不得运行 `init`。批准理由同时写明商业模式假设、目标客户、用户问题、价值主张、主要获客渠道、目标价值事件、最高风险假设和关键未知项；这些内容不能写成已验证收入或已跑通商业闭环。
4. 从中央模板 `templates/candidate-input.example.json` 准备输入，替换全部示例值并删除 `example_only`。保留真实 `source_report`；缺失字段不估算。
5. 确认目标目录中不存在候选锁、状态文件或决策日志，再运行中央 CLI 的 `init`，把精确确认值分别传给 `--approved-by`、`--confirm-key` 和 `--rationale`。
6. 运行 `validate` 和 `status`。只有输出确认 `current_stage: candidate_locked` 且候选哈希有效，才交给 `$web-business-planner`。

中央命令形态：

```bash
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 不可变、可哈希的候选身份
- 由用户原话支持的批准记录
- 商业模式假设、目标事件与关键未知项，且不冒充商业验证
- 中央 CLI 的 validate/status 结果
- 下一步 planner handoff 与所有 missing evidence
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 只在用户指定的新项目目录创建三类中央产物。
- 不得改写上游历史、候选报告或已有锁；更换候选时创建新项目。
- 不执行搜索、购买、Git、部署、DNS、统计配置或广告动作。
- 网络：none; read existing local upstream evidence only。
- 交互：required for exact candidate key approval, approver and rationale。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 替用户从多个候选中静默选赢家
- 把单一指标、模型判断或缺失证据当作合格结论
- 为修正候选而覆盖 candidate-lock.json
