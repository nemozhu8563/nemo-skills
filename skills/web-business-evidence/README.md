# web-business-evidence

为每页建立双来源和 claim 级证据包。它是 `web-business-pipeline` 套件的阶段入口，不复制中央状态机。

## 适用边界

- 起点：初次建站为 `planned`；优化/扩展模式仅由 `$web-business-expander` 在 `grow` 中调用。
- 终点：初次建站进入 `researched`；优化/扩展模式保持 `grow`。
- 不适用：复制竞品全文或专有数据；用 AI 摘要制造第二来源；在证据不足时补出价格、功能、数字、日期、可用状态或官方 URL。

## 你可以直接这样说

- “为页面矩阵建立 evidence-pack.json，每页至少双来源”
- “核验价格、功能状态、数值和官方链接的 claim-level 证据”
- “把素材整理成 source lineage 和 current_as_of 可审计记录”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/web-business-evidence /absolute/path/to/project/.agents/skills/web-business-evidence
ln -s /absolute/path/to/nemo-skills/skills/web-business-pipeline /absolute/path/to/project/.agents/skills/web-business-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill web-business-evidence
```

## 工作方式

1. 运行中央 `status` 和 `validate`，读取不可变候选锁及完整页面矩阵。初次模式只接受 `planned`；优化/扩展模式必须带 grow 变更批次、模式及逐项验收条件。
2. 建立 source registry：稳定 `source_id`、URL、标题、来源类型、可靠性、`retrieved_at`，对时效性来源填写 `current_as_of`。同一原文的镜像、AI 摘要或竞品转述只算一条 lineage。
3. 为每个 `page_id` 绑定至少两个不同来源。至少有一条能够支撑该页核心事实；社区内容可发现线索，但不能单独支撑敏感 claim。
4. 逐条登记将公开出现的 claim。标记为 `current_trusted` 的价格、数值、日期、版本/可用状态、官方链接或其他时效敏感事实，必须由当前 `official|trusted` 来源支撑，并记录验证状态与时间。

## 输出

- 来源注册表及可靠性/时效信息
- 逐页至少两条独立来源覆盖
- claim 到 source 的可审计映射
- researched gate 或 expansion validation 结果

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

- 只写 evidence-pack.json 和用户明确需要的本地研究说明。
- 不保存 Cookie、token、密码、浏览器存储或私有账号配置。
- 不修改页面矩阵、内容文件、候选锁、状态文件或远端来源。
