# web-business-qa

完成本地构建、内容人工审核和部署就绪门禁。它是 `web-business-pipeline` 套件的阶段入口，不复制中央状态机。

## 适用边界

- 起点：初次建站为 `build_ready`；优化/扩展模式由 `$web-business-expander` 在 `grow` 中调用。
- 终点：初次建站依次进入 `local_verified` 和 `deploy_ready`；优化/扩展模式保持 `grow`。
- 不适用：用一次 build 通过替代链接、资产、视觉和内容检查；把 not_applicable 当作无理由跳过；把本地 localhost 或 provider preview 当作公共线上成功。

## 你可以直接这样说

- “给这个 Web 业务做本地验收，写 launch-report.json”
- “跑 build、链接、资产和视觉检查，并完成人工审核覆盖整个当前变更批次”
- “扫描旧域名、记录 rollback，再判断是否 deploy_ready”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/web-business-qa /absolute/path/to/project/.agents/skills/web-business-qa
ln -s /absolute/path/to/nemo-skills/skills/web-business-pipeline /absolute/path/to/project/.agents/skills/web-business-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill web-business-qa
```

## 工作方式

1. 运行中央 `status` 和 `validate`，读取全部上游产物、项目命令和现有工作树。初次模式只接受 `build_ready`；优化/扩展模式必须带 grow 变更批次、模式及逐项验收条件。
2. 逐页确认文件存在并刷新真实 SHA-256；manifest 与矩阵、证据的 page/source/claim 引用必须完全一致。
3. 运行项目实际配置的 build、lint、tests、links、assets 检查，并用浏览器检查代表性桌面/移动视图、加载/空/错误状态和主要交互。没有对应命令时可记 `not_applicable`，但必须写具体理由。
4. 生成当前变更批次审核清单，每个新增或修改页面都由人审核并记录 `reviewed_by`、`reviewed_at`；无法完整审核时缩小批次或暂停，不能固定抽样几页代替。

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

- 找不到中央 CLI：确认 `WEB_BUSINESS_PIPELINE_SKILL_DIR` 或同级 `web-business-pipeline` symlink 可读；不要复制 CLI。
- 当前状态不匹配：运行中央 `status`，回到 `$web-business-pipeline` 重新路由。
- gate 失败：保留当前状态，修正报告中的具体 evidence 缺口后重试。
- 用户要求越过边界：只执行当前已明确授权且属于本 Skill 的动作，其他动作交给对应阶段。

## 风险边界

- 只修改与验收证据直接相关的 manifest 和 launch report；修复代码仅在用户请求实现修复时进行。
- 人类审核是阻塞门，不能由模型代签或默认通过。
- 不推送、不部署、不买域名、不改 DNS、不创建 GSC/GA、不申请广告。
