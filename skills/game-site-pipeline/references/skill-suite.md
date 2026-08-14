# Game Site Skill Suite

## 单一真相源

十个阶段 Skill 是可发现的工作入口，不是十套流水线。`game-site-pipeline` 中的 `scripts/pipeline.py`、Schema、模板和状态机是唯一机器契约。阶段 Skill 不复制 CLI、不直接改 `pipeline-state.json`，也不能自行发明状态名。

解析中央 CLI 时按以下顺序：

1. 用户显式设置的 `GAME_SITE_PIPELINE_SKILL_DIR`；
2. 当前阶段 Skill 的同级目录 `../game-site-pipeline`；
3. 当前项目 `.agents/skills/game-site-pipeline`；
4. 均不可读时停止，报告缺失依赖，不复制或重写中央 CLI。

## 初次建站路由

| 顺序 | Skill | 允许起点 | 所有产物 | 正常终点 |
|---:|---|---|---|---|
| 0 | `game-keyword-radar` | 尚无项目 | 候选报告与核验表 | 人工主词复核门 |
| 1 | `game-candidate-lock` | 合格候选 + 精确人工确认 | `candidate-lock.json`、`pipeline-state.json`、`decision-log.md` | `candidate_locked` |
| 2 | `game-site-planner` | `candidate_locked` | `page-matrix.json` | `planned` |
| 3 | `game-site-evidence` | `planned` | `evidence-pack.json` | `researched` |
| 4 | `game-site-builder` | `researched` | 页面文件、`content-manifest.json` | `build_ready` |
| 5 | `game-site-qa` | `build_ready` | 内容哈希、人工审核、本地检查、`launch-report.json` | `local_verified`，随后 `deploy_ready` |
| 6 | `game-site-launch` | `deploy_ready` | 独立授权记录、部署与 HTTP 回读 | `deployed` |
| 7 | `game-site-telemetry` | `deployed` | `analytics-snapshot.json` 中的 GSC/GA、索引和观察证据 | `telemetry_verified`，随后 `observing` |
| 8 | `game-site-growth` | `observing` | 数据决策与审批记录 | `grow`、`hold` 或 `retire` |
| 9a | `game-site-templater` | `grow` | 模板边界和可选本地模板产物 | `templated` |
| 9b | `game-page-expander` | `grow` | 有限扩页批次和更新后的矩阵/证据/内容 | 保持 `grow`，进入复用链 |

## 扩页复用链

扩页不是跳过前置门禁的“批量生成”。在 `grow` 状态下：

1. `game-page-expander` 用真实 GSC 机会先规划至少 10 个候选内页，再按同类 2–3 页的有限批次调用 planner/evidence/builder 的 expansion mode 更新三类产物；这些步骤不改状态。
2. `game-site-qa` 的 expansion mode 对新增页和受影响旧页重新做哈希、首批人工审核、本地检查和旧域名扫描；状态仍保持 `grow`。
3. `game-site-launch` 取得新的精确授权，部署新增内容并记录新 revision 与 HTTP 回读；状态仍保持 `grow`。
4. `game-site-telemetry` 记录新部署后的 GSC/GA 和观察窗口，只有中央 `gate --target observing` 通过后才执行 `grow -> observing`。

任何一步缺证据，都保持 `grow` 并报告 blocker。不得因为页面文件已经生成就声称扩页上线或重新进入观察。

## Hold 复查

`hold` 不直接再次做增长决策。到复查日期后先用 `game-site-telemetry` 更新数据并执行 `hold -> observing`，再由 `game-site-growth` 重新决定。没有有效 GSC 数据时仍只能 `hold`。

## 并发与所有权

- 同一时间只允许一个阶段 Skill 写项目产物。
- 只读研究可以并行，但写回前必须合并为一个阶段所有者的结果。
- 阶段 Skill 不覆盖其他阶段产物；需要跨阶段修正时回到总编排器重新路由。
- `candidate-lock.json` 永不可原地重写。换主词必须创建新项目。
