# game-site-builder

按页面契约和证据实现页面及内容清单。它是 `game-site-pipeline` 套件的阶段入口，不复制中央状态机。

## 适用边界

- 起点：初次建站为 `researched`；扩页模式仅由 `$game-page-expander` 在 `grow` 中调用。
- 终点：初次建站进入 `build_ready`；扩页模式保持 `grow`。
- 不适用：为了未来复用重构整个站点；生成矩阵之外的薄页或语言版本；把模型自检称为人工内容审核或发布验收。

## 你可以直接这样说

- “按页面契约实现这些攻略页并生成 content-manifest.json”
- “把 researched 项目推进到 build_ready，内容必须证据驱动”
- “为每个页面记录 source IDs、claim IDs、路径和内容哈希”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/game-site-builder /absolute/path/to/project/.agents/skills/game-site-builder
ln -s /absolute/path/to/nemo-skills/skills/game-site-pipeline /absolute/path/to/project/.agents/skills/game-site-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill game-site-builder
```

## 工作方式

1. 运行中央 `status` 和 `validate`，读取 candidate lock、page matrix、evidence pack、项目规则、Git 状态和现有实现。初次模式只接受 `researched`；扩页模式必须带 grow 批次上下文。
2. 沿用项目已有框架、组件、样式和命令；不添加依赖或新抽象，除非当前页面确实需要且用户授权。保留用户已有修改。
3. 逐页按照功能契约实现：只出现允许字段、动作、状态和页面目标；营销解释、运营边界卡片或示例卡不得擅自进入工作流页。
4. 内容只使用 evidence pack 中能够追溯的事实，写原创表达。无法支撑的 claim 不进入页面；不得复制竞品品牌、文案、截图、CSS 或专有资产。

## 输出

- 契约内的真实页面和必要组件
- 逐页来源与 claim 映射完整的 content-manifest.json
- 最小实现检查结果
- build_ready gate 或 expansion validation 结果

## 验证

```bash
python3 /absolute/path/to/qiaomu-meta-skill/scripts/validate_skill.py .
python3 /absolute/path/to/qiaomu-meta-skill/scripts/trigger_eval.py . --output reports/trigger-eval.json
python3 /absolute/path/to/qiaomu-meta-skill/scripts/export_skill_ir.py . --output reports/skill-ir.json
```

## Troubleshooting

- 找不到中央 CLI：确认 `GAME_SITE_PIPELINE_SKILL_DIR` 或同级 `game-site-pipeline` symlink 可读；不要复制 CLI。
- 当前状态不匹配：运行中央 `status`，回到 `$game-site-pipeline` 重新路由。
- gate 失败：保留当前状态，修正报告中的具体 evidence 缺口后重试。
- 用户要求越过边界：只执行当前已明确授权且属于本 Skill 的动作，其他动作交给对应阶段。

## 风险边界

- 只修改用户指定站点项目中与本批页面直接相关的文件。
- 不修改候选锁、页面矩阵、证据包或中央状态；发现上游错误时退回总编排器。
- 不提交、不推送、不部署、不改 DNS、不创建统计属性。
