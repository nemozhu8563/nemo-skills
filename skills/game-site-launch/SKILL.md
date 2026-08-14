---
name: game-site-launch
description: "Launch a locally verified overseas game site through separately authorized Git push, deployment, domain purchase, DNS change, or related external actions, then record provider, revision, DNS, and public HTTP readback without merging those facts. Use for 游戏站上线、部署授权、Git push 门禁、域名购买确认、DNS 修改、Vercel 或 Cloudflare 部署、launch-report.json 线上回读；not for local QA, blanket authorization, silent purchases, credential extraction, analytics setup, or claiming deployment from a dashboard status alone."
---

# Game Site Launch

在本地验收之后，把每一个外部动作拆成独立授权、实际执行和真实回读三件事；只把证据完整的部署记为上线。

## Dependency And Scope

- 机器契约来自同级必需依赖 `game-site-pipeline`；优先使用 `GAME_SITE_PIPELINE_SKILL_DIR`，其次解析 `../game-site-pipeline` 或项目 `.agents/skills/game-site-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：初次建站为 `deploy_ready`；扩页重发模式由 `$game-page-expander` 在 `grow` 且 QA 通过后调用。
- 终点：初次建站进入 `deployed`；扩页模式保持 `grow` 并交给 telemetry。
- 本 Skill 所有产物：`pipeline-state.json 中由中央 CLI 写入的逐项授权`、`launch-report.json 中的 external_actions、deployment、http_readback`。不得直接编辑 `pipeline-state.json`；授权和状态只能由中央 CLI 写入。

## Router Rules

- domain, DNS, Git push, deployment and ads are separate permissions
- authorization is not execution and execution is not readback
- deployment revision and public HTTP response are recorded
- unused or failed authorization can be revoked and rollback is actionable
- 完整全链路或当前阶段不明时，回到 `$game-site-pipeline`；找词和 Semrush 核验使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 运行中央 `status`/`validate`，读取 launch report、目标 revision、canonical origin、回滚步骤和现有授权。初次模式只接受 `deploy_ready`；扩页模式必须带 grow + 已通过 expansion QA 的上下文。
2. 把待办拆成中央允许的独立 action：`domain_purchase`、`dns_change`、`git_push`、`deployment`、`gsc_setup`、`ga_setup`、`advertising_application`。本 Skill 只执行本次上线实际需要且用户明确授权的项。
3. 对每项检查当前用户原话、scope、granted_by 和有效期。当前指令已精确授权则可直接用 `authorize` 记录；只有笼统“上线”但涉及购买、DNS 或其他 materially branching 动作时，先提出一个阻塞式问题。不得复用不同 action 的授权。
4. 执行前再次解析精确 target：Git remote/branch/revision、部署项目/环境、域名和 DNS record。不得输出凭证；登录、验证码、付费确认、权限不足或目标不一致时停止。
5. 每项执行后立即做独立回读：Git 远端 revision、provider deployment ID/status、公开 URL HTTP 状态/内容、域名所有权、DNS 解析。把 authorization ID、时间、目标和证据写入对应 external action；一个事实不能替代另一个。
6. 初次模式只有 deployment 为 verified、source revision 明确、匹配授权有效且公共 HTTP readback passed 时，才 `gate --target deployed` 并转移。扩页模式运行 `validate --stage deployed`，保持 `grow` 并交给 `$game-site-telemetry`。
7. 失败或中断时保持原状态，记录实际结果，撤销不再安全的授权，并按已有 rollback 恢复；恢复后重新回读，不把回滚计划称为已回滚。

中央命令形态：

```bash
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 每项外部动作的精确授权记录
- Git/provider/domain/DNS/HTTP 相互独立的真实回读
- 与实际部署 revision 一致的 launch-report.json
- deployed gate 或 expansion deployment validation 结果
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 只有用户当前明确授权的精确外部动作可以执行；未授权项只列计划。
- 不读取、复制、打印或保存 token、Cookie、密码、private key 和浏览器存储。
- 不创建 GSC/GA、不读取性能数据、不申请广告，除非另有对应阶段和精确授权。
- 网络：only the exact provider, registrar, Git remote, DNS, and public URL covered by the current authorization。
- 交互：required for each external action unless the current user instruction already explicitly authorizes that exact action and scope。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 用一个“上线”授权包办购买、DNS、推送和部署
- 把 provider READY 或 Git push 当作公共域名可用
- 绕过登录、验证码、付费确认、保护分支或平台权限
