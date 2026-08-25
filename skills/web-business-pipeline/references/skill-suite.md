# Web Business Skill Suite

## 单一真相源

十个阶段 Skill 是可发现的工作入口，不是十套流水线。`web-business-pipeline` 中的 `scripts/pipeline.py`、Schema、模板和状态机是唯一机器契约。阶段 Skill 不复制 CLI、不直接改 `pipeline-state.json`，也不能自行发明状态名。

解析中央 CLI 时按以下顺序：

1. 用户显式设置的 `WEB_BUSINESS_PIPELINE_SKILL_DIR`；
2. 当前阶段 Skill 的同级目录 `../web-business-pipeline`；
3. 当前项目 `.agents/skills/web-business-pipeline`；
4. 均不可读时停止，报告缺失依赖，不复制或重写中央 CLI。

## 初次业务验证路由

| 顺序 | Skill | 允许起点 | 所有产物 | 正常终点 |
|---:|---|---|---|---|
| 0 | 匹配垂直的上游发现方法 | 尚无合格候选 | 带方法、检查项和证据引用的候选 | 人工候选复核门 |
| 1 | `web-business-lock` | 合格候选 + 精确人工确认 | `candidate-lock.json`、`pipeline-state.json`、`decision-log.md` | `candidate_locked` |
| 2 | `web-business-planner` | `candidate_locked` | `page-matrix.json` | `planned` |
| 3 | `web-business-evidence` | `planned` | `evidence-pack.json` | `researched` |
| 4 | `web-business-builder` | `researched` | 页面文件、`content-manifest.json` | `build_ready` |
| 5 | `web-business-qa` | `build_ready` | 内容哈希、人工审核、本地检查、`launch-report.json` | `local_verified`，随后 `deploy_ready` |
| 6 | `web-business-launch` | `deploy_ready` | 独立授权记录、部署与 HTTP 回读 | `deployed` |
| 7 | `web-business-telemetry` | `deployed` | `analytics-snapshot.json` 中的 GSC/GA、索引、观察证据及已有授权埋点的聚合事件 | `telemetry_verified`，随后 `observing` |
| 8 | `web-business-growth` | `observing` | 搜索增长、转化学习、商业放大分层及审批记录 | `grow`、`hold` 或 `retire` |
| 9a | `web-business-templater` | `grow` | 模板边界和可选本地模板产物 | `templated` |
| 9b | `web-business-expander` | `grow` | 有限优化/扩展批次和更新后的矩阵/证据/内容 | 保持 `grow`，进入复用链 |

## 优化/扩展复用链

优化现有页面和新增页面都不是跳过前置门禁的“直接改站”。在 `grow` 状态下：

1. `web-business-expander` 从已批准的 growth decision 选择 `optimize-existing` 或 `expand-new`。每个变更项必须写明证据、目标页面、问题、`funnel_stage`、`primary_success_metric`、预期影响、验收条件、风险和依赖。
2. 批次大小不使用固定页数阈值；选择能够验证假设、处理依赖且可以完整人工审核的最小连贯批次。证据不足、风险过高或审核能力不足时缩小批次。
3. `web-business-planner`、`web-business-evidence`、`web-business-builder` 的 optimization/expansion mode 更新 matrix、evidence 和 manifest；现有页优化沿用稳定 `page_id`，新增页才创建新 `page_id`。这些步骤不改状态。
4. `web-business-qa` 对当前变更批次的每个新增或修改页面，以及共享组件影响到的代表性状态，重新做哈希、人工审核、本地检查和旧域名扫描；状态仍保持 `grow`。
5. `web-business-launch` 取得新的精确授权，部署本批改动并记录新 revision 与 HTTP 回读；状态仍保持 `grow`。
6. `web-business-telemetry` 记录新部署后的 GSC/GA 和观察窗口，只有中央 `gate --target observing` 通过后才执行 `grow -> observing`。

任何一步缺证据，都保持 `grow` 并报告 blocker。不得因为页面文件已经修改或生成就声称优化上线或重新进入观察。

## 游戏垂直适配

`game-keyword-radar` 保留为游戏垂直的可选上游，不是总入口。它完成 Steam/Roblox 候选发现与自身资格规则后，将结果映射为 v2 candidate：

- `key`: 稳定的 `game:<slug>`；
- `identities`: Steam app ID、Roblox universe/place ID 等稳定平台身份；
- `qualification.method`: `game-keyword-radar` 及其版本；
- `qualification.checks`: 雷达实际执行的趋势、搜索量、KD、长尾、SERP、来源等检查和原始观察；
- `business_hypothesis`: 仍由人工复核目标用户、问题、价值、商业模式、主要价值事件、最高风险假设和未知项。

中央 pipeline 只校验 handoff 的结构、通过状态和证据引用，不复刻或放宽雷达自己的阈值。其他垂直使用自己的发现方法和检查项，但输出同一个 candidate v2 合同。

## Hold 复查

`hold` 不直接再次做增长决策。到复查日期后先用 `web-business-telemetry` 更新数据并执行 `hold -> observing`，再由 `web-business-growth` 重新决定。没有有效 GSC 数据时仍只能 `hold`。

## 并发与所有权

- 同一时间只允许一个阶段 Skill 写项目产物。
- 只读研究可以并行，但写回前必须合并为一个阶段所有者的结果。
- 阶段 Skill 不覆盖其他阶段产物；需要跨阶段修正时回到总编排器重新路由。
- `candidate-lock.json` 永不可原地重写。更换候选必须创建新项目。
