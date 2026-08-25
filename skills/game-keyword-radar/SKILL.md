---
name: game-keyword-radar
description: "Run and govern a game keyword radar workflow that collects middle-tail Steam and Roblox candidates, compares historical momentum, validates search demand through 3ue/Semrush Volume, KD, intent and long-tail evidence, and writes combined local Markdown/CSV reports. Use for 生财航海热词游戏站、游戏热词雷达、中腰部游戏关键词、Steam/Roblox 找词、3ue 或 Semrush 核验、候选增量对比和报告回填；not for generic SEO advice, unrelated competitor research, credential extraction, or automatic publishing."
---

# Game Keyword Radar

把 Steam / Roblox 的中腰部候选、历史变化和 Google/SERP、Google Trends、3ue / Semrush 搜索证据合并成可回读的本地候选池。候选池不是选词结论：默认保留最多 30 个候选，每天只对自动排出的最多 10 个词实际尝试三层查询；缺失字段必须留空并写明状态和原因。

## Default Project

默认项目：

```text
/Users/nemo/Documents/Obsidian/04_Projects/AI出海/游戏热词雷达
```

如项目迁移，使用 `GAME_KEYWORD_RADAR_PROJECT_DIR` 指向包含 `package.json` 的目录。运行时历史与快照必须留在系统缓存目录，不写进 Skill。

## Mandatory Workflow

1. 先检查边界。
   - 读取项目 `README.md`、`config/radar.json`、`evidence/keyword-validation.csv`。
   - 检查目标文件和工作树状态；保留用户已有修改。
   - 不安装依赖，不创建定时任务，不提交、不推送、不发布，除非用户另行明确要求。

2. 运行采集与基线。
   - 在本 Skill 目录执行 `bash scripts/run-radar.sh`；需要参数时直接追加。
   - 先运行 `npm test`。测试失败时停止写回并报告。
   - 检查 Steam、Roblox、YouTube 的状态，不能把某一来源失败解释为“市场没有机会”。
   - Steam 与 Roblox 核心源全部失败时，确认退出码为 `2`、失败诊断进入运行快照，并保留上一份可用 Markdown/CSV；不要把保留报告称为本轮新数据。
   - 第一次运行只建立基线；第二次及以后才可声称存在玩家数、评论数或排名变化。

3. 建立每日查询队列并逐词执行。
   - 自动候选池默认保留最多 30 个中腰部候选；每天按排序自动排出最多 10 个仍有查询缺口的词。当天首次排出的 10 个会写入 `query_batch_date` 和 `query_batch_position`；同日重跑必须保留原批次和顺序，不能自动切到下一批。
   - 当天 10 个候选都必须实际尝试 Google/SERP、Google Trends、Semrush 三层。SERP 拥挤、搜索意图错位或找不到游戏本体仍要继续尝试 Semrush，以便提供可审计的真实数据；这些负向证据只影响淘汰，不得从当天查询队列移除。候选池其余词标记为待轮到，不算当日执行失败。
   - Google/SERP 使用精确游戏查询，记录 `verified|partial|blocked|not_found|unqueried`、`open|mixed|crowded`、`intent_match=match|mismatch`、可靠来源数、核验时间、入口和说明。
   - Google Trends 对当天 10 个候选固定使用全球、Web 搜索、过去 30 天；可把候选主词与 `GPTs` 放在同一张图表中比较相对热度，该对比仅作参考。每个词都记录状态、核验时间和失败原因。
   - 优先中腰部且有持续信号的词，不因一次暴涨直接入选。
   - 固定 Semrush 全球库 `global`；不同地区库不得直接比较。已有 US 记录要迁移到 `semrush_us_*` 历史字段保留，但不能进入 GLOBAL 的分数、判断或对比。
   - Google Trends 被浏览器或安全策略明确拒绝时，`google_trends`、主词平均值和 `GPTs` 平均值留空并在备注中记录阻断；不得绕过安全策略，也不得把 Semrush Trend 当成 Google Trends。

4. 通过 3ue / Semrush 做浏览器辅助核验。
   - 使用用户已有浏览器登录态打开 `https://dash.3ue.co/zh-Hans/#/page/m/home`，从可见工具卡进入 Semrush。
   - 只读取页面明确展示的 Keyword、Database、Volume、KD、CPC、Intent、Trend、Related Keywords 和 Questions。
   - 不读取、导出、复制或保存 Cookie、localStorage、Token、密码、共享账号信息或节点配置。
   - CAPTCHA 出现时必须停下并询问用户。
   - 用户明确授权 3ue 换节点时，额度不足只终止当前节点：复用同一个 3ue / Semrush 业务标签返回控制台，按页面可用标记串行切换节点后重试。不得并行打开多个业务标签，不得输出或保存节点标签、启动链接或节点配置。
   - 用户未授权换节点时，额度不足、共享节点异常或页面结构不可控均停止自动操作。
   - 更新指标后页面可能先显示“不可用”再补齐数据；等待页面稳定并至少复读一次，再决定 `partial` 或 `not_found`，不能把处理中状态当成最终缺失。
   - 浏览器页面读取连续失败时不要重复轰炸：把当前词标为 `blocked` 或 `partial` 并记录原因，然后在安全可行时继续下一个词；不得降级为要求用户填写的人工查询清单。
   - CAPTCHA 是强制停点；停止时保持所有尚未执行的候选为 `unqueried`，整轮必须报告 `incomplete`。只有 CAPTCHA 或登录失效确实阻断自动化时才保留 handoff 页。
   - 全程严格复用一个 3ue / Semrush 业务标签串行查询，不得为了提速并行打开业务标签。

5. 逐词原子写回精确证据。
   - 以报告中的 `key` 为主键更新机器管理的 `evidence/keyword-validation.csv`；每完成一个词就写回，避免中途阻断丢失前序结果。正常流程不要求用户手工编辑该文件。
   - Google/SERP 使用：`serp_status`、`serp_checked_at`、`serp_competition`、`intent_match`、`reliable_sources`、`serp_source`、`serp_notes`。
   - Google Trends 使用：`google_trends_status`、`google_trends`、`google_trends_candidate_avg_30d`、`google_trends_gpts_avg_30d`、`google_trends_checked_at`、`google_trends_source`、`google_trends_notes`。
   - Semrush 使用当前 GLOBAL 字段：`semrush_database`、`semrush_volume`、`semrush_kd`、`semrush_cpc`、`semrush_intent`、`semrush_trend`、`semrush_related_keywords`、`semrush_question_keywords`、`semrush_checked_at`、`semrush_source`、`semrush_status`、`semrush_notes`。迁移前 US 数据由 `semrush_us_*` 历史字段保留，只读展示且不参与评分。
   - 三层状态只允许 `verified|partial|blocked|not_found|unqueried`：`unqueried` 表示没有执行到，不能用 `pending`、空白或 `—` 隐藏；`partial`、`blocked`、`not_found` 必须在对应 `*_notes` 中解释。
   - 如完成 `GPTs` 对比，Google Trends 写入 `google_trends_candidate_avg_30d`、`google_trends_gpts_avg_30d`、`google_trends_checked_at`；两个平均值必须来自同一张“全球 / Web / 过去 30 天”图表。未完成时留空，不阻断主词复核。
   - 相关词和问题词以 `|` 分隔；没有展示的字段留空，不估算、不补零。
   - 不在 `semrush_source` 或 `notes` 中写入账号、会话、Cookie、Token、代理节点或个人身份信息。

6. 重新运行并比较。
   - 再次运行雷达，确认 Semrush 字段进入 Markdown/CSV，KD 与长尾词参与搜索验证分。
   - 只有三层状态全为 `verified`、Google Trends 上涨、KD `<30`、真实长尾词 `>=10`、SERP 为 `open|mixed`、`intent_match=match`、可靠来源 `>=2` 时，才标记“可进入主词复核”。主词与 `GPTs` 的近 30 天平均热度对比保留为参考信号；高于、相等、低于或缺失都不参与评分、缺失判断或淘汰。
   - `intent_match=mismatch` 是硬淘汰条件；即使 Volume 与 KD 好看，也不能把现实服务、同名泛词、其他游戏或地点词当作当前游戏需求。
   - KD `>40`、趋势下跌或尖峰、长尾词少于 5、SERP 拥挤等是负向信号。

7. 验证并交付。
   - 运行 `npm test`。
   - 检查最新 Markdown、CSV、快照和历史文件中没有凭证形态字符串。
   - 报告数据源成功/失败、候选总数、今日批次及候选池累计的三层实际尝试数、`verified|partial|blocked|not_found|unqueried` 分布、三层均已尝试数、三层均 verified 数、报告路径和历史是否更新。
   - 对每个候选清楚列出 Volume、KD、CPC、Intent、趋势、长尾数量、意图匹配、缺失字段状态和原因。只有当日批次存在 `unqueried` 才让当日批次标为 `incomplete`；候选池外的未查询词显示为待轮到，不得称为当日失败，也不得把用户手工复核列为正常下一步。
   - 只有候选满足本 Skill 自己的全部资格规则且用户要求交接时，才附带 `web-business-pipeline` v2 candidate handoff；不得调用中央 `init`，不得填写批准人，也不得把“可进入主词复核”写成已批准。

## Web Business Candidate V2 Handoff

游戏雷达是可选的垂直上游，不是 Web 出海业务总入口。向 `$web-business-lock` 交接时使用下面的通用结构：

```json
{
  "key": "game:<slug>",
  "name": "<verified game name>",
  "source_report": "<local report path or stable evidence reference>",
  "identities": [
    {"provider": "steam", "id": "<app-id>"}
  ],
  "qualification": {
    "status": "qualified",
    "method": "game-keyword-radar@0.2.0",
    "checked_at": "<ISO-8601 UTC>",
    "checks": [
      {
        "check_id": "search-opportunity",
        "criterion": "All current game-keyword-radar qualification rules passed",
        "status": "passed",
        "evidence_refs": ["<report-or-row-reference>"],
        "observations": {}
      }
    ]
  },
  "business_hypothesis": {
    "target_customer": "<evidence-backed player segment hypothesis>",
    "customer_problem": "<search-intent problem hypothesis>",
    "value_proposition": "<site value hypothesis>",
    "business_models": ["<hypothesis only>"],
    "primary_acquisition_channel": "search",
    "primary_value_event": "<observable value event hypothesis>",
    "riskiest_assumption": "<single highest-risk assumption>",
    "unknowns": ["<unverified commercial or user unknown>"]
  }
}
```

- `identities` 使用真实稳定 ID；Steam 用 app ID，Roblox 用 universe/place 等能够消歧的稳定 ID。同名游戏的不同 provider identity 不得合并。
- `qualification.checks` 必须逐项保留趋势、Volume、KD、长尾、SERP、intent 和来源检查的真实 observations 与 evidence refs；示例中的空对象不能原样交付。
- `business_hypothesis` 只写有证据或用户陈述支持的假设。商业模式、价值事件和收入未知时写进 `unknowns`，不得冒充已验证商业闭环。
- 不满足全部资格规则时，保持原始失败/缺失状态，不生成 `status: qualified` 的 handoff。

详细字段和降级流程见 [references/workflow.md](references/workflow.md)。

## Output Contract

最终回复必须分清：

- 已验证事实：本轮实际来源状态、候选数量、真实 Semrush 字段和测试结果。
- 推断：为什么某词值得继续核验。
- 未完成：验证码、额度、登录、SERP 或 Trends 等缺口。
- 本地文件：最新 Markdown、CSV、机器证据表和运行时快照路径。
- 可选交接：仅在满足规则且用户要求时给出 candidate v2；明确它仍待 `$web-business-lock` 人工批准。

不得把 installs、stars、榜单排名、单日热度或模型判断称为市场验证；不得把“优先验证”称为已选定主词。

## Write And Rollback Boundary

- 允许写：项目 `evidence/keyword-validation.csv`、`reports/`，以及项目配置允许的系统缓存运行时目录。
- 默认不写：浏览器凭证、Skill 目录运行数据、账号配置、定时任务、Git 历史和远端系统。
- 浏览器查询是只读操作；任何下载、上传、购买、套餐变更、消息发送或发布都需要新的明确授权。
- 写回错误时只回滚本轮触碰的核验行或报告，不覆盖其他用户修改。

## Non-goals

- 不替代通用 SEO、竞品 Top Pages 或整站 Semrush 审计。
- 不绕过验证码、付费墙、设备限制或共享账号规则。
- 不自动发布网站，不自动创建产品，也不以搜索量替代 SERP 和素材可持续性判断。
