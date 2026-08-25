---
name: web-business-growth
description: "Make an evidence-based grow, hold, or retire decision for an observing Web business from a valid analytics snapshot, query/page opportunities, available conversion or value evidence, and explicit human approval, while distinguishing search growth, conversion learning, and commercial scale. Use for Web 出海数据复盘、有流量无转化、商业验证、转化闭环、grow hold retire、第 7 天或第 14 天增长决策、GSC 查询与页面机会、继续投入还是暂停或退出；not for analytics setup, fabricated forecasts, claiming a commercial closed loop without conversion evidence, retiring without valid GSC data, automatic page generation, ad approval, or universal traffic and revenue promises."
---

# Web Business Growth

把“感觉这个站行不行”变成一个有时间区间、原始指标、机会解释和人类批准的生命周期决定。

## Dependency And Scope

- 机器契约来自同级必需依赖 `web-business-pipeline`；优先使用 `WEB_BUSINESS_PIPELINE_SKILL_DIR`，其次解析 `../web-business-pipeline` 或项目 `.agents/skills/web-business-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：`observing` 且 analytics snapshot 已通过中央校验；`hold` 必须先由 telemetry 更新后回到 observing。
- 终点：进入 `grow`、`hold` 或 `retire`。
- 本 Skill 所有产物：`analytics-snapshot.json 中的 decision`、`由中央 transition 追加的 decision-log.md 记录`。不得直接编辑 `pipeline-state.json`；授权和状态只能由中央 CLI 写入。

## Router Rules

- grow and retire require valid GSC performance data
- hold is the only decision allowed without valid GSC data
- recommendation is separated from human approval
- search growth, conversion learning and commercial scale are separate conclusions
- raw period, counts, opportunity and uncertainty remain visible
- 完整全链路或当前阶段不明时，回到 `$web-business-pipeline`；机会发现仍由匹配的上游方法负责，只有 Steam/Roblox 游戏找词才使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 运行中央 `status`/`validate`，确认当前为 `observing`，snapshot 的 site URL、property、period 和部署对象一致。过期或错 property 数据先退回 `$web-business-telemetry`。
2. 读取原始 GSC/GA 指标、queries、pages、indexed pages、观察天数、技术检查，以及 telemetry 已可靠回读的聚合转化/价值事件。分开事实与解释；同比/环比必须有可比时间窗，不能用单日尖峰下结论，也不能把 unknown 当作 zero。
3. 先标记当前结论层级：`search_growth` 只证明搜索机会，`conversion_learning` 证明或可靠否证一个承接动作，`commercial_scale` 才表示可归因价值具有可重复性。`grow` 不自动等于商业闭环；没有转化证据时不得宣称商业闭环或商业放大成立。
4. 按症状定位下一步：无曝光先查技术/关键词；有曝光无点击看 SERP 与意图；有流量无转化先查事件可靠性、页面承接和产品路径；有转化无价值再查归因、商业模式或价格；有价值但慢只选择一个主要增长杠杆。
5. 形成三个生命周期候选：`grow` 需要有效 GSC 数据和明确 query/page 机会；`hold` 用于数据不足、测量未知或主动等待；`retire` 需要有效数据证明继续投入不划算。没有 valid GSC data 时只允许 hold。若以“持续无商业价值”为 retire 理由，还必须有充分观察窗、可信 zero/observed 事件并排除主要技术阻塞。
6. 给出推荐、证据、反证、机会成本和下一步，但不要代替用户批准。当前指令未明确选择时，提出一个阻塞式 grow/hold/retire 决策问题。
7. 把用户批准的 recommendation、具体 rationale、approved_by 和 approved_at 写入 analytics decision。理由必须引用 snapshot 的实际数据、结论层级和 missing evidence，不得只写“AI 建议”。
8. 运行 `gate --target grow|hold|retire`；通过后才使用同一 actor/reason 转移。失败时保持 observing 并列出缺失证据。
9. grow 只记录决策并路由执行：需要优化现有页面或新增页面时交给 `$web-business-expander` 选择 `optimize-existing`/`expand-new`，需要抽取已验证基础设施时交给 templater。hold 保留复查日期并在到期时回 telemetry；retire 只停止投入，不自动删除站点、域名、数据或远端资源。

中央命令形态：

```bash
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 事实/推断/不确定性分开的数据复盘
- `search_growth`、`conversion_learning`、`commercial_scale` 的证据分层，且不越级宣称商业闭环
- grow/hold/retire 推荐与备选
- 用户批准的 analytics decision
- 中央决策 gate、状态和下一步路由
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 只更新本地决策记录，不直接改页面、部署、域名、统计 property 或广告。
- 未经精确批准只给建议，不把模型推荐写成 approved_by。
- retire 不授权删除、取消域名、关闭服务或移除数据。
- 网络：none by default; use the already recorded snapshot, with refresh routed to web-business-telemetry。
- 交互：required for the final grow, hold, or retire approval and rationale。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 根据模型预测或单日波动自动执行页面优化/扩展
- 把有流量、进入 grow 或存在 CTA 当成已跑通商业闭环
- 没有有效 GSC 数据就 retire
- 承诺固定收录、排名、流量、RPM 或收入
