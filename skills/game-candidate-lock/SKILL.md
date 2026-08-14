---
name: game-candidate-lock
description: "Lock one human-approved and radar-qualified Steam or Roblox game keyword candidate into the immutable game-site-pipeline identity and state records. Use for 游戏候选锁词、主词人工确认、candidate lock、从 game-keyword-radar 候选进入建站、核对 Steam app ID 或 Roblox universe ID、生成 candidate-lock.json；not for finding keywords, silently selecting the winner, relaxing qualification thresholds, or rewriting an existing candidate lock."
---

# Game Candidate Lock

把雷达中的“可进入主词复核”候选变成一个明确由人批准、平台身份不含糊、不可原地改写的站点项目起点。

## Dependency And Scope

- 机器契约来自同级必需依赖 `game-site-pipeline`；优先使用 `GAME_SITE_PIPELINE_SKILL_DIR`，其次解析 `../game-site-pipeline` 或项目 `.agents/skills/game-site-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：合格雷达候选，且当前项目尚无 `candidate-lock.json`。
- 终点：创建 `candidate_locked`。
- 本 Skill 所有产物：`candidate-lock.json`、`pipeline-state.json`、`decision-log.md`。不得直接编辑 `pipeline-state.json`；状态只能由中央 CLI 写入。

## Router Rules

- candidate still passes every radar hard threshold
- platform identity is explicit and non-ambiguous
- exact current human confirmation exists
- existing candidate lock is never overwritten
- 完整全链路或当前阶段不明时，回到 `$game-site-pipeline`；找词和 Semrush 核验使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 读取雷达报告和候选行，逐项核对：Trends 为 `rising`、Semrush Volume 为真实正数且数据库明确、KD `<30`、真实长尾词 `>=10`、SERP 为 `open|mixed`、可靠来源 `>=2`。
2. 保留稳定的 `game:<slug>` key，并至少记录一个平台身份。Steam 使用 app ID；Roblox 使用 universe/place 等能够消歧的稳定 ID。相同标题不能合并成同一平台实体。
3. 若当前用户指令没有精确确认候选 key、批准人和具体理由，展示 key、名称、平台 ID 与资格证据后提出一个阻塞式确认问题；用户回答前不得运行 `init`。
4. 从中央模板 `templates/candidate-input.example.json` 准备输入，替换全部示例值并删除 `example_only`。保留真实 `source_report`；缺失字段不估算。
5. 确认目标目录中不存在候选锁、状态文件或决策日志，再运行中央 CLI 的 `init`，把精确确认值分别传给 `--approved-by`、`--confirm-key` 和 `--rationale`。
6. 运行 `validate` 和 `status`。只有输出确认 `current_stage: candidate_locked` 且候选哈希有效，才交给 `$game-site-planner`。

中央命令形态：

```bash
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 不可变、可哈希的候选身份
- 由用户原话支持的批准记录
- 中央 CLI 的 validate/status 结果
- 下一步 planner handoff 与所有 missing evidence
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 只在用户指定的新项目目录创建三类中央产物。
- 不得改写雷达历史、候选报告或已有锁；换词时创建新项目。
- 不执行搜索、购买、Git、部署、DNS、统计配置或广告动作。
- 网络：none; read existing local radar evidence only。
- 交互：required for exact candidate key approval, approver and rationale。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 替用户从多个候选中静默选赢家
- 把一次热度尖峰或模型判断当作合格证据
- 为修正候选而覆盖 candidate-lock.json
