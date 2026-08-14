# Workflow And Data Contract

## Stable layers

1. Discovery: Steam 热门新品与 Roblox Top Trending / Up-and-Coming。
2. Middle-tail filter: Roblox 在线玩家区间并排除头部；Steam 发布时间与评论数区间。
3. Persistence: 系统缓存中的历史与快照。
4. Daily search batch: 候选池最多 30 个；每天自动固定最多 10 个词，逐词完整尝试 Google/SERP、Google Trends 与 Semrush。Google Trends 固定全球、Web 搜索、过去 30 天，并可用 `GPTs` 同图基线作为相对热度参考，判断意图错位、SERP 竞争与可靠素材源。
5. Semrush validation: 对当天同一批最多 10 个候选读取 3ue / Semrush 全球库证据；SERP 拥挤或意图错位仍要留下实际查询状态，不能作为跳过 Semrush 的理由。
6. Decision: 候选状态、硬门槛与参考信号，不自动发布产品。

## Batch policy

- 候选池默认最多 30 个；这是发现层规模。每个自然日首次运行时，从仍有查询缺口的候选中按排序固定最多 10 个，写入 `query_batch_date` 和 `query_batch_position`。
- 同一天重跑必须继续原 10 个，不能自动切换下一批；候选池中未被选中的词显示为待轮到。
- 当日 10 个中的每一个都要实际尝试 Google/SERP、Google Trends 与 Semrush。`crowded`、意图错位、拼写纠正吞没或找不到游戏本体都应形成负向证据，但不得跳过 Semrush。
- 当日批次只要三层都已实际尝试即为 `complete`，即使状态是 `partial`、`blocked` 或 `not_found`；只有当日批次中的 `unqueried` 才为 `incomplete`。候选池外的未查询词不影响当天完成状态。
- Google Trends 被浏览器或安全策略明确拒绝时保持为空，在备注中记录阻断；不得通过其他浏览器、raw CDP 或间接方式绕过明确安全拒绝，也不得用 Semrush Trend 替代。

## Google Trends baseline contract

- 配置默认是 `baselineTerm=GPTs`、`timeRange=today 1-m`、`geo=""`（全球）、`searchType=web`。
- `google_trends_candidate_avg_30d` 和 `google_trends_gpts_avg_30d` 必须来自同一张图表；两者都存在且主词平均值严格大于 `GPTs` 时，`google_trends_vs_gpts=higher`。
- `higher|not_higher` 只描述相对热度；平均值相等、主词更低或两个平均值缺失，都不参与评分、缺失判断或候选状态。

## Semrush writeback fields

| Field | Meaning | Rule |
|---|---|---|
| `semrush_database` | 当前地区数据库 | 默认 `global`；只与同库数据比较 |
| `semrush_volume` | 月搜索量 | 只写页面显示数字 |
| `semrush_kd` | Keyword Difficulty | `<30` 为通过信号，`>40` 为负向信号 |
| `semrush_cpc` | CPC | 商业意图参考，不参与当前分数 |
| `semrush_intent` | Intent | 原样记录 Semrush 意图标签 |
| `semrush_trend` | Trend | 原样记录页面文本或序列 |
| `semrush_related_keywords` | 相关词 | `|` 分隔，去重后参与长尾词计数 |
| `semrush_question_keywords` | 问题词 | `|` 分隔，去重后参与长尾词计数 |
| `semrush_checked_at` | 核验时间 | ISO 日期或时间 |
| `semrush_source` | 可回溯入口 | 写页面名称或公开 URL，不写会话信息 |
| `semrush_status` | 完整度 | `verified|partial|blocked|not_found|unqueried` |

`longtail_count` 可显式填写；留空时，雷达按相关词与问题词的并集计数。兼容旧 `kd` 字段，但新数据使用 `semrush_kd`。原有 US 字段会归档到 `semrush_us_*`，供报告显示历史事实；它们不会参与 GLOBAL 的分数、资格判断或数值比较。

## Browser boundary

- 允许：打开用户给定的 3ue 页面、点击可见 Semrush 工具卡、在同一个业务标签串行执行当天最多 10 个只读关键词查询、读取可见结果。
- 禁止：检查 Cookies、localStorage、session store、密码管理器、共享账号详情或节点配置。
- 停止点：CAPTCHA、登录、套餐/额度变更、下载确认、任何外部写操作。
- 降级：同一读取方向失败两次后，不继续重复；将当前词原子写为 `blocked` 或 `partial` 并继续下一个词。正常流程不得把查询清单交给用户手工填写。

## Qualification gate

只有全部满足才是“可进入主词复核”：

- Google Trends `rising` 且非单日尖峰；
- KD `<30`；
- 真实长尾词 `>=10`；
- SERP `open` 或 `mixed`；
- `intent_match=match`；
- 可靠来源 `>=2`。

主词与 `GPTs` 的全球近 30 天同图平均值对比是参考信号，不属于上述资格门槛。

Volume 不单独决定是否入选。高搜索量可能对应头部竞争、新闻尖峰或错误意图。

## Failure matrix

| Failure | Action | Claim boundary |
|---|---|---|
| Steam/Roblox 单源失败 | 保留另一来源并报告状态 | 不声称全网无机会 |
| Steam/Roblox 核心源全部失败 | 退出码 `2`，诊断写入快照，保留上一份可用日报/CSV | 不把旧报告称为本轮结果 |
| 首次运行 | 写入基线 | 不声称增长 |
| Semrush 页面不可读 | 当前词写为 `blocked`，继续同日下一词 | 不猜字段，也不降级为手工清单 |
| 只取到部分字段 | `partial`，已见字段照录 | 不把 partial 称为完整验证 |
| CAPTCHA | 停止并询问用户，剩余当日词保持 `unqueried` | 不绕过，报告当日批次 incomplete |
| 地区库变化 | 分开记录；US 归档为 `semrush_us_*`，当前 GLOBAL 重新查询 | 不直接比较 Volume/KD |
| 无相关词 | 留空或 `not_found` | 不写 0 除非页面明确显示 0 |
