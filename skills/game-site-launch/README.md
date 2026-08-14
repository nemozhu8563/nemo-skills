# game-site-launch

逐项授权执行上线动作并记录真实线上回读。它是 `game-site-pipeline` 套件的阶段入口，不复制中央状态机。

## 适用边界

- 起点：初次建站为 `deploy_ready`；扩页重发模式由 `$game-page-expander` 在 `grow` 且 QA 通过后调用。
- 终点：初次建站进入 `deployed`；扩页模式保持 `grow` 并交给 telemetry。
- 不适用：用一个“上线”授权包办购买、DNS、推送和部署；把 provider READY 或 Git push 当作公共域名可用；绕过登录、验证码、付费确认、保护分支或平台权限。

## 你可以直接这样说

- “这个站已 deploy_ready，授权部署当前 revision 并做 HTTP 回读”
- “分别记录 Git push、Vercel 部署和 DNS 修改的授权与结果”
- “按 launch-report.json 上线，确认公共 URL 而不是只看 provider READY”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/game-site-launch /absolute/path/to/project/.agents/skills/game-site-launch
ln -s /absolute/path/to/nemo-skills/skills/game-site-pipeline /absolute/path/to/project/.agents/skills/game-site-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill game-site-launch
```

## 工作方式

1. 运行中央 `status`/`validate`，读取 launch report、目标 revision、canonical origin、回滚步骤和现有授权。初次模式只接受 `deploy_ready`；扩页模式必须带 grow + 已通过 expansion QA 的上下文。
2. 把待办拆成中央允许的独立 action：`domain_purchase`、`dns_change`、`git_push`、`deployment`、`gsc_setup`、`ga_setup`、`advertising_application`。本 Skill 只执行本次上线实际需要且用户明确授权的项。
3. 对每项检查当前用户原话、scope、granted_by 和有效期。当前指令已精确授权则可直接用 `authorize` 记录；只有笼统“上线”但涉及购买、DNS 或其他 materially branching 动作时，先提出一个阻塞式问题。不得复用不同 action 的授权。
4. 执行前再次解析精确 target：Git remote/branch/revision、部署项目/环境、域名和 DNS record。不得输出凭证；登录、验证码、付费确认、权限不足或目标不一致时停止。

## 输出

- 每项外部动作的精确授权记录
- Git/provider/domain/DNS/HTTP 相互独立的真实回读
- 与实际部署 revision 一致的 launch-report.json
- deployed gate 或 expansion deployment validation 结果

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

- 只有用户当前明确授权的精确外部动作可以执行；未授权项只列计划。
- 不读取、复制、打印或保存 token、Cookie、密码、private key 和浏览器存储。
- 不创建 GSC/GA、不读取性能数据、不申请广告，除非另有对应阶段和精确授权。
