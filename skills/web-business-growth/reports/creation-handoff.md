# Creation Handoff — web-business-growth 1.0.0

## Result

- Generalized `web-business-growth` to 1.0.0: 用有效搜索、转化与商业证据和人工批准决定 grow、hold 或 retire。
- Canonical location: `skills/web-business-growth`; publication status: local only.
- Central dependency: `web-business-pipeline >=1.0.0`; no state machine or CLI is duplicated.

## Reference skills studied

- [AgriciDaniel/claude-seo — seo-google](https://github.com/AgriciDaniel/claude-seo/tree/main/skills/seo-google): 保留真实 GSC/GA 数据和 query/page 读取；落到原始 period 与指标。
- [coreyhaines31/marketingskills — programmatic-seo](https://github.com/coreyhaines31/marketingskills/tree/main/skills/programmatic-seo): 保留 opportunity-driven expansion；拒绝以模板能力自动放量。

## Absorbed and rejected

- Keep: 真实搜索数据、页面机会和 intent-driven expansion。
- Adapt: 增加 no-data hold、反证、机会成本和最终人工批准。
- Reject: 自动扩页、单日波动决策、流量收入保证。
- Invent: 生命周期决策与中央状态 gate 的双重批准记录。

## Advantages and highlights

- [design advantage] 单阶段入口拥有明确起点、产物和终点，同时中央状态机保持唯一真相源。
- [design advantage] growth 只负责决策；优化/扩展执行复用同一 evidence/QA/launch/telemetry 契约，不另造旁路。
- [hypothesis] 更窄的触发边界预计能减少全链路上下文污染，但真实项目对比仍是 missing evidence。

## Verification and limits

- [validated advantage] Package validation 为 0 failure / 0 warning，trigger eval 为 11/11，Skill IR 已导出；中央 suite contract 与状态机测试合计 27/27 通过。
- Provider-backed output、真实站点运行、人类最终内容审核、排名、流量、收入和公开安装仍是 missing evidence。
- No commit, push, deployment, domain/DNS change, analytics setup, advertising application or public release was requested or performed by creating this package.
