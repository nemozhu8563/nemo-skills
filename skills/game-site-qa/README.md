# game-site-qa

完成本地构建、内容人工审核和部署就绪门禁。它是 `game-site-pipeline` 套件的阶段入口，不复制中央状态机。

## 适用边界

- 起点：初次建站为 `build_ready`；扩页模式由 `$game-page-expander` 在 `grow` 中调用。
- 终点：初次建站依次进入 `local_verified` 和 `deploy_ready`；扩页模式保持 `grow`。
- 不适用：用一次 build 通过替代链接、资产、视觉和内容检查；把 not_applicable 当作无理由跳过；把本地 localhost 或 provider preview 当作公共线上成功。

## 你可以直接这样说

- “给这个游戏站做本地验收，写 launch-report.json”
- “跑 build、链接、资产和视觉检查，并完成首批五页人工审核门”
- “扫描旧域名、记录 rollback，再判断是否 deploy_ready”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/game-site-qa /absolute/path/to/project/.agents/skills/game-site-qa
ln -s /absolute/path/to/nemo-skills/skills/game-site-pipeline /absolute/path/to/project/.agents/skills/game-site-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill game-site-qa
```

## 工作方式

1. 运行中央 `status` 和 `validate`，读取全部上游产物、项目命令和现有工作树。初次模式只接受 `build_ready`；扩页模式必须带 grow 批次上下文。
2. 逐页确认文件存在并刷新真实 SHA-256；manifest 与矩阵、证据的 page/source/claim 引用必须完全一致。
3. 运行项目实际配置的 build、lint、tests、links、assets 检查，并用浏览器检查代表性桌面/移动视图、加载/空/错误状态和主要交互。没有对应命令时可记 `not_applicable`，但必须写具体理由。
4. 生成首批页面审核清单。全站或本批少于 5 页时全部审核，否则至少 5 个不同页面由人审核并记录 `reviewed_by`、`reviewed_at`。模型自评不算人工审核；缺少人类结果时必须暂停。

## 输出

- 真实内容哈希和审核记录
- 七类本地检查及证据
- canonical/旧域名/回滚记录完整的 launch-report.json
- local_verified/deploy_ready gate 或 expansion validation 结果

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

- 只修改与验收证据直接相关的 manifest 和 launch report；修复代码仅在用户请求实现修复时进行。
- 人类审核是阻塞门，不能由模型代签或默认通过。
- 不推送、不部署、不买域名、不改 DNS、不创建 GSC/GA、不申请广告。
