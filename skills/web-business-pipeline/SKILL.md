---
name: web-business-pipeline
description: "Orchestrate and resume the full lifecycle of an evidence-driven Web business for overseas markets, from one human-approved qualified candidate through planning, evidence, implementation, QA, launch, telemetry, growth decisions, expansion, or templating. Use for Web 出海业务流水线、SaaS/工具站/内容站/线索业务/游戏站验证、商业闭环、有流量无转化、从候选到上线复盘、继续上次项目、检查当前关卡、grow hold retire；route exact single-stage work to web-business-lock, web-business-planner, web-business-evidence, web-business-builder, web-business-qa, web-business-launch, web-business-telemetry, web-business-growth, web-business-templater, or web-business-expander. Not for upstream opportunity discovery alone, generic SEO advice, an unrelated one-off website task, or silently buying domains, publishing, deploying, changing DNS, configuring analytics, or applying for ads."
---

# Web Business Pipeline

把一个已经通过其上游方法资格检查、并由人精确确认的 Web 出海机会，推进为可审计、可恢复的业务项目。机会可以是 SaaS、工具、内容、线索业务或游戏站；上游方法拥有自己的发现与资格规则，本 Skill 不在中央合同里硬编码某一垂直的指标。本 Skill 是总编排器，十个阶段 Skill 共享本包的状态机、Schema、模板和 CLI。本 Skill 不把“可进入复核”偷换成“已批准候选”。

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
4. `grow` 后优化现有页面或扩展新页面，都沿用 planner、evidence、builder、QA、launch、telemetry 门禁；在新部署和统计回读前保持 `grow`，不得把本地改动直接记成 `observing`。
5. 路由、产物所有权、初次建站和优化/扩展复用路径见 [references/skill-suite.md](references/skill-suite.md)。
6. 商业验证是共享证据层，不新增状态或跳关；项目假设、页面承接、原始事件和增长结论分别由 candidate-lock、planner、telemetry 和 growth 承担，见 [references/commercial-validation.md](references/commercial-validation.md)。

## Mandatory Workflow

1. 检查范围和现状。
   - 读取目标项目规则、Git 状态和已有产物；保留用户修改。
   - 若用户只要找需求、找词、竞品冷启动研究或其他上游机会发现，使用匹配该垂直的方法，不要触发本 Skill。Steam/Roblox 游戏词与 Semrush 核验使用 `$game-keyword-radar`。
   - 若全链路任务尚无合格候选，先由匹配的上游方法产出带资格证据的候选，再停在人工确认门；不要自行替用户选机会。
   - 若当前请求只覆盖一个阶段，按 Stage Router 切换到对应专用 Skill；中央 CLI 仍是唯一状态写入者。

2. 锁定候选。
   - 从上游证据整理 `templates/candidate-input.example.json` 所示输入，使用稳定 `<namespace>:<slug>` key，并用 `identities[{provider,id}]` 消歧同名实体。
   - `qualification.method` 标明上游方法，`qualification.checks` 逐项保存其通过标准、证据引用和原始观察。中央只校验这些检查已通过且可追溯，不把低 KD、趋势、访谈数或任何垂直阈值提升为全局规则。
   - `init` 必须同时收到 `--approved-by`、精确匹配的 `--confirm-key` 和具体 `--rationale`。
   - `business_hypothesis` 写明目标客户、用户问题、价值主张、商业模式、主要获客渠道、主要价值事件、最高风险假设和未知项；它不冒充已验证收入。
   - 初始化生成不可变 `candidate-lock.json`、带候选哈希的 `pipeline-state.json` 和 `decision-log.md`。锁文件变化后所有门禁失败；修正方式是新建项目，不是覆盖锁。

3. 按状态推进，不跳关。
   - 状态顺序：`candidate_locked → planned → researched → build_ready → local_verified → deploy_ready → deployed → telemetry_verified → observing → grow|hold|retire → templated`。
   - 每次先运行 `gate --target <stage>`；只有结果为 `ok: true` 才运行 `transition --to <stage>`。
   - 文件存在不代表完成。`gate` 必须验证字段、引用、内容哈希、来源覆盖、人工审核、授权和线上回读。

4. 规划页面矩阵。
   - 使用 `page-matrix.json` 为每页指定唯一 `primary_keyword` 和 `intent_key`。
   - 每页先写页面级功能契约：用户目标、允许字段、允许动作、允许状态和明确非目标。
   - 用现有页面字段表达 discovery、utility 或 commercial-support 角色；没有真实产品、合法去向和需求证据时，不得为了商业化发明 CTA、价格、支付、下载或 Affiliate 链接。
   - 同义词或 intent key 被两个页面占用时停止，先消除关键词蚕食。
   - 非基础语言只有在需求证据存在、该语言内容完整时才可加入。

5. 建立证据包和内容清单。
   - 每页至少两个不同来源。每条公开 claim 显式选择 `standard` 或 `current_trusted`；会随时间变化、影响交易/使用决定或声称官方状态的内容必须使用当前的 official/trusted 来源并标为已验证。
   - 不复制竞品全文、品牌文案或资产；只可借鉴信息架构和通用交互模式，不做像素级复刻。
   - `content-manifest.json` 必须逐页映射矩阵、来源和 claim。构建后记录项目相对路径及真实 SHA-256。
   - 当前变更批次中的每个页面都必须完成人工审核；`status: published` 只表示未改动且已存在于部署基线的页面。批次大小由证据强度、风险、依赖关系和可完整审核的能力决定，不使用固定页数阈值。

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
   - 区分 `search_growth`、`conversion_learning` 和 `commercial_scale`。进入 `grow` 不等于跑通商业闭环；没有可靠转化/价值事件时只能声明搜索机会或待验证假设。
   - 只使用已有授权统计返回的聚合原始事件；`unknown`、`zero`、`not_applicable` 分开，第三方收入不得伪装成 GA 数据。
   - 不使用 Google Indexing API 提交普通内容页。
   - `grow`、`hold`、`retire` 必须写入人类批准的证据性理由；只有在明确区分可复用基础设施与产品专属内容后才能进入 `templated`。

9. 验证并交付。
   - 运行 `validate`，报告当前状态、下一关 blocker、warning 和 missing evidence。
   - 最终回复分开列出：已验证本地产物、已授权但未执行的动作、真实线上回读、有效数据、推断和未完成事项。
   - 不提交、不推送、不部署、不购买、不建统计属性、不申请广告，除非用户另行明确要求对应动作。

Skill 路由见 [references/skill-suite.md](references/skill-suite.md)，字段契约见 [references/schemas.md](references/schemas.md)，状态与恢复规则见 [references/state-machine.md](references/state-machine.md)，证据规则见 [references/evidence-policy.md](references/evidence-policy.md)，商业验证见 [references/commercial-validation.md](references/commercial-validation.md)，上线和增长门禁见 [references/launch-gates.md](references/launch-gates.md) 与 [references/growth-rules.md](references/growth-rules.md)。

## Write And Runtime Boundary

- 允许写：用户指定项目中的八类耐久产物，以及项目自己的页面文件。
- 默认不写：Skill 目录运行状态、vault 内日志/临时文件、浏览器凭证、账号配置、远端服务和 Git 历史。
- 临时文件、缓存和日志如确有需要，使用系统缓存目录；不得留在 Obsidian vault。
- 回滚只处理本轮写入的阶段记录或报告字段，不覆盖用户内容。`candidate-lock.json` 不可原地重写。

## Non-goals

- 不替代上游机会发现方法、通用 SEO 顾问、建站框架或部署供应商。
- 不因生成速度、竞品页面数量、stars、installs 或单日流量预测而批量建页。
- 不绕过登录、验证码、付费墙、审批或平台权限。
- 不把模型判断当作搜索需求、来源真实性、索引成功或商业验证。
