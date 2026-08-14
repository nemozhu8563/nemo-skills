---
name: game-site-growth
description: "Make an evidence-based grow, hold, or retire decision for an observing overseas game site from a valid analytics snapshot, query/page opportunities, indexed-page evidence, and explicit human approval. Use for 游戏站数据复盘、grow hold retire、第 7 天或第 14 天增长决策、GSC 查询与页面机会、继续投入还是暂停或退出；not for analytics setup, fabricated forecasts, retiring without valid GSC data, automatic page generation, ad approval, or universal traffic and revenue promises."
---

# Game Site Growth

把“感觉这个站行不行”变成一个有时间区间、原始指标、机会解释和人类批准的生命周期决定。

## Dependency And Scope

- 机器契约来自同级必需依赖 `game-site-pipeline`；优先使用 `GAME_SITE_PIPELINE_SKILL_DIR`，其次解析 `../game-site-pipeline` 或项目 `.agents/skills/game-site-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：`observing` 且 analytics snapshot 已通过中央校验；`hold` 必须先由 telemetry 更新后回到 observing。
- 终点：进入 `grow`、`hold` 或 `retire`。
- 本 Skill 所有产物：`analytics-snapshot.json 中的 decision`、`由中央 transition 追加的 decision-log.md 记录`。不得直接编辑 `pipeline-state.json`；授权和状态只能由中央 CLI 写入。

## Router Rules

- grow and retire require valid GSC performance data
- hold is the only decision allowed without valid GSC data
- recommendation is separated from human approval
- raw period, counts, opportunity and uncertainty remain visible
- 完整全链路或当前阶段不明时，回到 `$game-site-pipeline`；找词和 Semrush 核验使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 运行中央 `status`/`validate`，确认当前为 `observing`，snapshot 的 site URL、property、period 和部署对象一致。过期或错 property 数据先退回 `$game-site-telemetry`。
2. 读取原始 GSC/GA 指标、queries、pages、indexed pages、观察天数和技术检查。分开事实与解释；同比/环比必须有可比时间窗，不能用单日尖峰下结论。
3. 形成三个候选结论：`grow` 需要有效数据和明确 query/page 机会；`hold` 用于数据不足或主动等待；`retire` 需要有效数据证明继续投入不划算。没有 valid GSC data 时只允许 hold。
4. 给出推荐、证据、反证、机会成本和下一步，但不要代替用户批准。当前指令未明确选择时，提出一个阻塞式 grow/hold/retire 决策问题。
5. 把用户批准的 recommendation、具体 rationale、approved_by 和 approved_at 写入 analytics decision。理由必须引用 snapshot 的实际数据，不得只写“AI 建议”。
6. 运行 `gate --target grow|hold|retire`；通过后才使用同一 actor/reason 转移。失败时保持 observing 并列出缺失证据。
7. grow 路由到 templater 或 page-expander；hold 保留复查日期并在到期时回 telemetry；retire 只停止投入，不自动删除站点、域名、数据或远端资源。

中央命令形态：

```bash
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$GAME_SITE_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 事实/推断/不确定性分开的数据复盘
- grow/hold/retire 推荐与备选
- 用户批准的 analytics decision
- 中央决策 gate、状态和下一步路由
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 只更新本地决策记录，不直接改页面、部署、域名、统计 property 或广告。
- 未经精确批准只给建议，不把模型推荐写成 approved_by。
- retire 不授权删除、取消域名、关闭服务或移除数据。
- 网络：none by default; use the already recorded snapshot, with refresh routed to game-site-telemetry。
- 交互：required for the final grow, hold, or retire approval and rationale。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 根据模型预测或单日波动自动扩页
- 没有有效 GSC 数据就 retire
- 承诺固定收录、排名、流量、RPM 或收入
