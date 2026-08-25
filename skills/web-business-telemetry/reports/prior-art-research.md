# Prior Art Research — web-business-telemetry

Date: 2026-08-07

This package is a modular stage of the already researched `web-business-pipeline` workflow. It does not pretend that ten independent catalog searches were run. The governed parent research deduplicated 99 candidate families and inspected the implementations below at source level; this stage reuses only the mechanisms relevant to its narrower job.

### AgriciDaniel/claude-seo — seo-google

- Source: https://github.com/AgriciDaniel/claude-seo/tree/main/skills/seo-google
- Discovery/trust context: 2026-08-07: SkillsMP recorded 13,269 repository stars; actual Google readback mechanisms were inspected.
- Stage lesson: 保留 capability-aware GSC/GA 和真实属性回读；落到 setup/readback/data 分层.

### dqhieu/gsc-seo-autopilot — gsc-seo-autopilot

- Source: https://github.com/dqhieu/gsc-seo-autopilot
- Discovery/trust context: 2026-08-07: 22 skills.sh installs; recurring SEO command routing was inspected.
- Stage lesson: 保留周期 SEO 操作；改为 day-7/day-14 可审计观察.

## Keep / Adapt / Reject / Invent

- Keep: 真实 Google property 回读、周期检查和能力感知操作.
- Adapt: 把配置、索引、性能和观察窗口拆为四层事实.
- Reject: 普通攻略页 Indexing API、无数据补零、跨 property 扩权.
- Invent: no-data 分支只允许技术诊断与定时复查.

## Evidence boundary

Catalog installs and repository stars are adoption/popularity signals, not user ratings, correctness proof or business outcomes. The shared parent report is `../web-business-pipeline/reports/prior-art-research.md`. Real provider, ranking, traffic, revenue and end-user evidence remain missing until an authorized project records them.
