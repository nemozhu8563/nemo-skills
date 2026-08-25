# web-business-growth

用有效数据和人工批准决定 grow、hold 或 retire。它是 `web-business-pipeline` 套件的阶段入口，不复制中央状态机。

## 适用边界

- 起点：`observing` 且 analytics snapshot 已通过中央校验；`hold` 必须先由 telemetry 更新后回到 observing。
- 终点：进入 `grow`、`hold` 或 `retire`。
- 不适用：根据模型预测或单日波动自动执行页面优化/扩展；没有有效 GSC 数据就 retire；承诺固定收录、排名、流量、RPM 或收入。

## 你可以直接这样说

- “根据第 14 天 GSC 和价值事件数据决定这个 Web 业务 grow、hold 还是 retire”
- “复盘 queries、pages 和 indexed pages，再让我确认是否继续投入”
- “没有 valid GSC data，只能给 hold 并保留复查日期”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/web-business-growth /absolute/path/to/project/.agents/skills/web-business-growth
ln -s /absolute/path/to/nemo-skills/skills/web-business-pipeline /absolute/path/to/project/.agents/skills/web-business-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill web-business-growth
```

## 工作方式

1. 运行中央 `status`/`validate`，确认当前为 `observing`，snapshot 的 site URL、property、period 和部署对象一致。过期或错 property 数据先退回 `$web-business-telemetry`。
2. 读取原始 GSC/GA 指标、queries、pages、indexed pages、观察天数和技术检查。分开事实与解释；同比/环比必须有可比时间窗，不能用单日尖峰下结论。
3. 形成三个候选结论：`grow` 需要有效数据和明确 query/page 机会；`hold` 用于数据不足或主动等待；`retire` 需要有效数据证明继续投入不划算。没有 valid GSC data 时只允许 hold。
4. 给出推荐、证据、反证、机会成本和下一步，但不要代替用户批准。当前指令未明确选择时，提出一个阻塞式 grow/hold/retire 决策问题。
5. grow 决策只说明机会和方向；实际优化现有页面或新增页面交给 `$web-business-expander`，由它按证据、风险、依赖和审核能力确定变更批次。

## 输出

- 事实/推断/不确定性分开的数据复盘
- grow/hold/retire 推荐与备选
- 用户批准的 analytics decision
- 中央决策 gate、状态和下一步路由

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

- 只更新本地决策记录，不直接改页面、部署、域名、统计 property 或广告。
- 未经精确批准只给建议，不把模型推荐写成 approved_by。
- retire 不授权删除、取消域名、关闭服务或移除数据。
