# web-business-expander

在 `grow` 后把已批准的数据复盘转成有限站点变更：优化现有页面或新增页面，并重走上线观察门。它是 `web-business-pipeline` 套件的执行入口，不负责 grow/hold/retire 决策，也不复制中央状态机。

## 适用边界

- 起点：`grow`，且 growth decision 包含有效 GSC/query/page 机会。
- 两种模式：`optimize-existing` 或 `expand-new`，一次只选一种。
- 批次大小：由证据、风险、依赖和可完整人工审核的能力决定；不设“1–3 页”或“至少 10 页”阈值。
- 终点：本地改动期间保持 `grow`；重走 QA、launch、telemetry 后回到 `observing`。

## 你可以直接这样说

- “按照这次数据复盘优化现有页面，逐项写清证据、预期影响和验收条件。”
- “grow 后新增有真实搜索意图或客户旅程缺口的页面，批次大小按证据和审核能力决定。”
- “先修 CTR 低的标题和首屏，再重走 QA、launch、telemetry 回到 observing。”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/web-business-expander /absolute/path/to/project/.agents/skills/web-business-expander
ln -s /absolute/path/to/nemo-skills/skills/web-business-pipeline /absolute/path/to/project/.agents/skills/web-business-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill web-business-expander
```

## 工作方式

1. 运行中央 `status`/`validate`，确认 `grow`、已批准 growth decision 和当前部署基线一致。
2. 选择 `optimize-existing` 或 `expand-new`，为每个变更项记录证据、目标、问题、假设、预期影响、验收条件、风险和依赖。
3. 选择能够验证假设并可完整人工审核的最小连贯批次；证据或审核能力不足时缩小批次，不用固定页数凑规模。
4. 依次复用 planner → evidence → builder → QA → launch → telemetry；当前批次每个变更页都要人工审核，部署前始终保持 `grow`。

## 输出

- 明确的优化或扩展模式
- 有证据和验收条件的有限变更批次
- 更新后的矩阵、证据、内容、QA 和全批次人审结果
- 重发/telemetry handoff，或最终 observing gate

## 验证

```bash
python3 /absolute/path/to/qiaomu-meta-skill/scripts/validate_skill.py .
python3 /absolute/path/to/qiaomu-meta-skill/scripts/trigger_eval.py . --output reports/trigger-eval.json
python3 /absolute/path/to/qiaomu-meta-skill/scripts/export_skill_ir.py . --output reports/skill-ir.json
```

## Troubleshooting

- 找不到中央 CLI：确认 `WEB_BUSINESS_PIPELINE_SKILL_DIR` 或同级 `web-business-pipeline` symlink 可读；不要复制 CLI。
- 当前状态不匹配：运行中央 `status`，回到 `$web-business-pipeline` 重新路由。
- gate 失败：保留当前状态，修正报告中的具体 evidence 缺口后重试。
- 用户要求越过边界：只执行当前已明确授权且属于本 Skill 的动作，其他动作交给对应阶段。

## 风险边界

- 本 Skill 只编排优化/扩展批次；`web-business-growth` 继续只负责数据复盘和 grow/hold/retire 决策。
- 没有精确授权时只做到本地 QA，不推送、不部署、不改 DNS。
- 不修改候选锁，不改变 hold/retire 项目，不自动抓取受限来源。
