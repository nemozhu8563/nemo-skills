# Commercial Validation Layer

## 目的与边界

这是一层跨阶段的商业证据与诊断方法，不是新的生命周期状态机。现有
`candidate_locked → planned → researched → build_ready → local_verified → deploy_ready → deployed → telemetry_verified → observing → grow|hold|retire`
保持不变，中央 CLI 和 Schema version 也不因此改变。

方法来自用户提供的龙猫《SEO出海赚钱逻辑》中关于项目选择、商业闭环、意图演进、增长杠杆和止损的框架。这里做了四类处理：

- 保留：需求、商业价值、竞争、产品解决力、SEO 可行性；流量、转化和单位价值分开验证。
- 适配：把“从 $0 到 $1K/$10K/$100K”改写为证据层级，不绑定某一种 Web 业务模式。
- 拒绝：把 `$1K / $10K / $100K` 当生命周期硬门槛，或把收入、客单价、复购设为所有站点必填。
- 补充：把项目假设、原始观察和结论映射进 v2 产物，并把 `unknown`、`zero`、`not_applicable` 分开。

## 商业结果模型

把商业结果理解为：

`可发现需求/流量 × 商业意图 × 承接转化 × 单位价值 × 复购或留存`

这不是要求五项都非零的公式。不同商业模式使用不同价值事件：

| 商业模式 | 可观察的承接事件 | 可观察的价值事件 | 常见不适用项 |
|---|---|---|---|
| 广告 | 有效页面浏览、广告曝光 | 已回读广告收入、RPM | 客单价、购买复购 |
| Affiliate | 合法外链点击 | 可归因成交、佣金 | 站内收款、套餐 |
| 付费工具/订阅 | 注册、试用、核心功能完成 | 购买、续费、ARPU/留存 | 广告 RPM |
| 线索/赞助 | 合格咨询、表单完成 | 已确认线索价值、赞助收入 | 电商客单或复购可能不适用 |

未选择商业模式时，所有价值结论都是假设。没有适用指标时写 `not_applicable`；有可靠埋点但计数为零时写 `zero`；没有可靠读数时写 `unknown`。三者不得互换。

## 三层证据，不新增状态

- `search_growth`：已经证明需求、曝光、点击或明确 query/page 机会；只能说明搜索侧值得继续实验。
- `conversion_learning`：已有授权埋点中的目标动作被可靠观测，或可靠埋点证明目标动作计数为零；用于学习页面承接和产品路径。
- `commercial_scale`：已有可归因价值事件，并在明确时间窗内显示可重复性；才可以讨论放大商业闭环。

`grow` 是生命周期决定，不等于 `commercial_scale`。只有搜索机会、没有转化证据时仍可基于现有规则进入 `grow`，但理由必须写成搜索增长或转化实验，不能宣称赚钱闭环已经成立。

## 项目选择问题

候选通过其上游方法的资格检查后，再把以下内容写进结构化 `business_hypothesis` 和人工批准理由；它们是商业假设，不新增自动分数或全局硬门槛：

1. 用户持续在解决什么问题？
2. 可能的商业模式是什么？
3. 哪些查询或竞品行为支持商业意图？
4. 站点能提供什么真实产品、工具、信息或路径来解决问题？
5. 第一项可观察的承接事件和价值事件分别是什么？
6. 哪些关键项仍是 `unknown`？

## 意图与页面承接

搜索意图可从信息发现逐步靠近解决方案、产品/对比和交易，但不是所有项目都必须建立交易页。规划阶段只使用现有字段表达角色：

- `page_type` 与 `search_intent`：页面处在 discovery、utility 或 commercial-support 哪一类意图中；
- `user_goal`：用户这次访问要完成什么；
- `allowed_actions`：页面允许的下一步；
- `non_goals`：明确禁止凭空加入购买、下载、外链或其他商业动作。

商业化不能绕过页面功能契约。没有真实产品、合法去向和需求证据时，不得为了“靠近交易”自动发明 CTA、价格、支付、下载或 Affiliate 链接。

## 当前 v2 产物映射

| 阶段 | 现有产物 | 记录方式 |
|---|---|---|
| candidate lock | `candidate-lock.json.business_hypothesis` 与 `decision.rationale` | 客户、问题、价值、商业模式、获客渠道、主要价值事件、最高风险假设、未知项和人工批准理由 |
| planner | `page-matrix.json.pages[*]` | 复用 `page_type/search_intent/user_goal/allowed_actions/non_goals`，不新增未校验字段 |
| telemetry | `analytics-snapshot.json.ga.metrics` | 只放真实 GA property 已返回的聚合事件及值；使用 `ga.period`，保留事件定义和原始计数 |
| growth | `analytics-snapshot.json.decision.rationale` 与 `decision-log.md` | 标明证据层级、症状、反证、下一实验和 missing evidence |
| optimizer/expander | `decision-log.md` 的变更项 | 记录 `funnel_stage`、`primary_success_metric`、基线、时间窗和验收条件 |

外部支付、广告或 Affiliate 后台的金额不能伪装成 GA 数据。没有独立 provider 回读时，把它列为 missing evidence；若有独立回读，只在决策理由中引用来源、时间窗和原始值，等待未来明确授权的 Schema 升级再结构化。

## 原始证据规则

- 记录事件定义、原始计数、时间窗、来源/property 和适用范围；派生转化率时同时保留分子、分母和公式。
- 不把估算、截图缺口、模型判断或配置成功写成真实事件或收入。
- 不混用不同时间窗、地区、locale、部署 revision 或 property 的数据。
- 只读取已有或明确授权的聚合埋点；不因为本方法存在就新增跟踪、创建 property 或修改站点代码。
- 不保存原始 IP、用户标识、Cookie、token 或逐用户行为；地区判断只使用获准平台返回的聚合数据。

## 症状到下一步

| 症状 | 先排除 | 证据层级 | 下一步 |
|---|---|---|---|
| 无曝光 | 索引、技术、关键词与内容方向 | `search_growth` 尚未成立 | 技术排查、调整方向或 `hold`；无 valid GSC 时不得 `retire` |
| 有曝光无点击 | 标题、SERP 展示、意图匹配 | `search_growth` | 优化现有页，主要指标用 CTR/点击，不冒充转化 |
| 有流量无转化 | 事件是否可靠、页面角色、动作路径、产品匹配 | `conversion_learning` | 先修测量或承接，再做最小实验；不能直接判市场无需求 |
| 有转化无价值 | 归因、商业模式、价格/套餐、支付或 Affiliate 路径 | `conversion_learning` | 验证价值事件；未回读金额时保持 unknown |
| 有价值但增长慢 | 流量、转化、单位价值、留存中哪一项受限 | `commercial_scale` | 一次只选择主要杠杆和主要成功指标 |
| 持续验证无商业价值 | 有效 GSC、充分观察窗、可靠事件、技术阻塞是否排除 | 可能 `retire` | 仅在证据充分且人工批准时止损；retire 仍不授权删除资源 |

## 放大与止损边界

- 放大前先说明放大的是搜索覆盖、转化学习还是已验证商业结果。
- 每个优化/扩展变更项只指定一个主要 `funnel_stage` 和 `primary_success_metric`，其余指标作为 guardrail。
- 竞品分析的输出是机会地图：关键词缺口、页面/工具缺口、信任差距和承接差距；不是页面抄写清单。
- 以“无商业价值”为 `retire` 理由时，必须已有 valid GSC、足够观察期、可信的 zero/observed 事件、已排除主要技术阻塞，并取得人工批准。
- 无 valid GSC 时仍只能 `hold`。本方法不削弱 `growth-rules.md` 和中央 CLI 的既有门禁。
