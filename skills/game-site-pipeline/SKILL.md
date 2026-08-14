---
name: game-site-pipeline
description: "Orchestrate and resume the full lifecycle of a search-driven overseas game utility or guide site after keyword discovery, routing each current state to the matching stage Skill while keeping one evidence state machine. Use for 热词游戏站全链路、游戏站建站流水线、从选词到上线复盘、继续上次游戏站项目、检查当前关卡、批量扩页后重新观察、grow hold retire 或模板化总流程；route exact single-stage work to game-candidate-lock, game-site-planner, game-site-evidence, game-site-builder, game-site-qa, game-site-launch, game-site-telemetry, game-site-growth, game-site-templater, or game-page-expander. Not for keyword discovery alone, generic SEO advice, unrelated websites, or silently buying domains, publishing, deploying, changing DNS, configuring analytics, or applying for ads."
---

# Game Site Pipeline

把一个已经通过雷达硬门槛、并由人确认的游戏主词，推进为可审计、可恢复的站点项目。现有 `game-keyword-radar` 继续负责找词；本 Skill 是总编排器，阶段执行由十个专用 Skill 承担，但全部共享本包的状态机、Schema、模板和 CLI。本 Skill 不把“可进入主词复核”偷换成“已选定主词”。

## Local CLI

本 Skill 的确定性入口是：

```bash
python3 scripts/pipeline.py <command> --project-dir <project-dir>
```

支持 `init`、`status`、`validate`、`gate`、`transition`、`authorize`、`revoke`。CLI 只写本地项目记录，不调用注册商、Git、部署平台、DNS、GSC、GA 或广告平台。

## Stage Router

1. 完整全链路、恢复未知项目或询问“下一步”时，先由本 Skill 运行 `status` 和 `validate`。
2. 根据当前状态只路由一个阶段入口；阶段完成并通过中央 gate 后，再回到本 Skill 重新判断。
3. 精确的单阶段请求直接使用对应阶段 Skill，不要让多个 Skill 同时改同一产物。
4. `grow` 后扩页沿用原有 evidence、QA、launch、telemetry 门禁；在新部署和统计回读前保持 `grow`，不得把本地新增页面直接记成 `observing`。
5. 路由、产物所有权、初次建站和扩页复用路径见 [references/skill-suite.md](references/skill-suite.md)。

## Mandatory Workflow

1. 检查范围和现状。
   - 读取目标项目规则、Git 状态和已有产物；保留用户修改。
   - 若用户只要找词、Steam/Roblox 候选或 Semrush 核验，使用 `$game-keyword-radar`，不要触发本 Skill。
   - 若全链路任务尚无合格候选，先通过 `$game-keyword-radar` 产出候选，再停在人工主词确认门；不要自行替用户选词。
   - 若当前请求只覆盖一个阶段，按 Stage Router 切换到对应专用 Skill；中央 CLI 仍是唯一状态写入者。

2. 锁定候选。
   - 从雷达报告整理 `templates/candidate-input.example.json` 所示输入，保留稳定 `game:<slug>` key 和 Steam/Roblox `platform_ids`。
   - `init` 必须同时收到 `--approved-by`、精确匹配的 `--confirm-key` 和具体 `--rationale`。
   - 初始化生成不可变 `candidate-lock.json`、带候选哈希的 `pipeline-state.json` 和 `decision-log.md`。锁文件变化后所有门禁失败；修正方式是新建项目，不是覆盖锁。

3. 按状态推进，不跳关。
   - 状态顺序：`candidate_locked → planned → researched → build_ready → local_verified → deploy_ready → deployed → telemetry_verified → observing → grow|hold|retire → templated`。
   - 每次先运行 `gate --target <stage>`；只有结果为 `ok: true` 才运行 `transition --to <stage>`。
   - 文件存在不代表完成。`gate` 必须验证字段、引用、内容哈希、来源覆盖、人工审核、授权和线上回读。

4. 规划页面矩阵。
   - 使用 `page-matrix.json` 为每页指定唯一 `primary_keyword` 和 `intent_key`。
   - 每页先写页面级功能契约：用户目标、允许字段、允许动作、允许状态和明确非目标。
   - 同义词或 intent key 被两个页面占用时停止，先消除关键词蚕食。
   - 非基础语言只有在需求证据存在、该语言内容完整时才可加入。

5. 建立证据包和内容清单。
   - 每页至少两个不同来源；`redeem_code`、`numeric_value`、`official_link` 必须绑定当前的 official/trusted 来源并标为已验证。
   - 不复制竞品全文、品牌文案或资产；只可借鉴信息架构和通用交互模式，不做像素级复刻。
   - `content-manifest.json` 必须逐页映射矩阵、来源和 claim。构建后记录项目相对路径及真实 SHA-256。
   - 批量扩页前至少人工审核首批 5 页；若全站少于 5 页，则全部人工审核。

6. 做本地发布检查。
   - `launch-report.json` 必须记录 build、lint、tests、links、assets、visual、content_review；无适用检查可写 `not_applicable`，但必须给出证据或理由。
   - 检查 canonical origin 和旧域名残留，写明回滚步骤。
   - 本地通过、Git 推送、部署、域名、DNS 是不同事实，不得合并表述。

7. 对外动作逐项授权。
   - 域名购买、DNS 修改、Git 推送、部署、创建 GSC、创建 GA、广告申请都需要用户对该具体动作的新明确授权。
   - 只有在当前请求已经明确授权该动作时，才可运行 `authorize` 记录原始指令、范围、授权人和有效期；`authorize` 本身不执行外部动作。
   - 外部动作完成后，将对应 `authorization_id` 和实际回读证据写入报告。没有匹配授权或真实回读，不得进入 `deployed` 或 `telemetry_verified`。
   - 可用 `revoke` 立即撤销尚未消费或不再有效的授权。

8. 观察和决策。
   - 分开证明部署 URL、域名、GSC property、GA property、索引状态和实际指标。
   - 没有有效 GSC 数据时，只做技术排查并安排第 7 天、第 14 天复盘；不得进入 `grow` 或 `retire`。
   - 不使用 Google Indexing API 提交普通攻略页。
   - `grow`、`hold`、`retire` 必须写入人类批准的证据性理由；只有在明确区分可复用基础设施与产品专属内容后才能进入 `templated`。

9. 验证并交付。
   - 运行 `validate`，报告当前状态、下一关 blocker、warning 和 missing evidence。
   - 最终回复分开列出：已验证本地产物、已授权但未执行的动作、真实线上回读、有效数据、推断和未完成事项。
   - 不提交、不推送、不部署、不购买、不建统计属性、不申请广告，除非用户另行明确要求对应动作。

Skill 路由见 [references/skill-suite.md](references/skill-suite.md)，字段契约见 [references/schemas.md](references/schemas.md)，状态与恢复规则见 [references/state-machine.md](references/state-machine.md)，证据规则见 [references/evidence-policy.md](references/evidence-policy.md)，上线和增长门禁见 [references/launch-gates.md](references/launch-gates.md) 与 [references/growth-rules.md](references/growth-rules.md)。

## Write And Runtime Boundary

- 允许写：用户指定项目中的八类耐久产物，以及项目自己的页面文件。
- 默认不写：Skill 目录运行状态、vault 内日志/临时文件、浏览器凭证、账号配置、远端服务和 Git 历史。
- 临时文件、缓存和日志如确有需要，使用系统缓存目录；不得留在 Obsidian vault。
- 回滚只处理本轮写入的阶段记录或报告字段，不覆盖用户内容。`candidate-lock.json` 不可原地重写。

## Non-goals

- 不替代找词雷达、通用 SEO 顾问、建站框架或部署供应商。
- 不因生成速度、竞品页面数量、stars、installs 或单日流量预测而批量建页。
- 不绕过登录、验证码、付费墙、审批或平台权限。
- 不把模型判断当作搜索需求、来源真实性、索引成功或商业验证。
