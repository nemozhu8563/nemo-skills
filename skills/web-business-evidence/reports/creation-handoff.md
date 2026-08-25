# Creation Handoff — web-business-evidence 1.0.0

## Result

- Generalized `web-business-evidence` to 1.0.0: 为任意 Web 业务建立逐页来源与 claim 证据包，并支持 grow 中现有页优化与新页扩展。
- Canonical location: `skills/web-business-evidence`; publication status: local only.
- Central dependency: `web-business-pipeline >=1.0.0`; no state machine or CLI is duplicated.

## Reference skills studied

- [coreyhaines31/marketingskills — programmatic-seo](https://github.com/coreyhaines31/marketingskills/tree/main/skills/programmatic-seo): 保留每页 unique value 与来源驱动内容；落到逐页覆盖。
- [AgriciDaniel/claude-seo — seo-google](https://github.com/AgriciDaniel/claude-seo/tree/main/skills/seo-google): 保留真实 provider/readback 思想；改为敏感 claim 的当前来源回读。

## Absorbed and rejected

- Keep: 证据驱动页面和真实读回原则。
- Adapt: 从页面级参考升级为 claim-to-source 映射与来源 lineage 去重。
- Reject: 竞品改写、AI 摘要充当独立来源、缺失事实自动补全。
- Invent: 对价格、功能状态、数字、官方状态与链接使用 `standard|current_trusted` 时效/可信级别联合门禁。

## Advantages and highlights

- [design advantage] 单阶段入口拥有明确起点、产物和终点，同时中央状态机保持唯一真相源。
- [design advantage] 优化/扩展模式复用同一 evidence/QA/launch/telemetry 契约，不另造旁路。
- [hypothesis] 更窄的触发边界预计能减少全链路上下文污染，但真实项目对比仍是 missing evidence。

## Verification and limits

- [validated advantage] Package validation 为 0 failure / 0 warning，trigger eval 为 10/10，Skill IR 已导出；中央 suite contract 与状态机测试合计 27/27 通过。
- Provider-backed output、真实站点运行、人类最终内容审核、排名、流量、收入和公开安装仍是 missing evidence。
- No commit, push, deployment, domain/DNS change, analytics setup, advertising application or public release was requested or performed by creating this package.
