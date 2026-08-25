# Prior Art Research — web-business-launch

Date: 2026-08-07

This package is a modular stage of the already researched `web-business-pipeline` workflow. It does not pretend that ten independent catalog searches were run. The governed parent research deduplicated 99 candidate families and inspected the implementations below at source level; this stage reuses only the mechanisms relevant to its narrower job.

### AgriciDaniel/claude-seo — seo-google

- Source: https://github.com/AgriciDaniel/claude-seo/tree/main/skills/seo-google
- Discovery/trust context: 2026-08-07: SkillsMP recorded 13,269 repository stars; actual Google readback mechanisms were inspected.
- Stage lesson: 保留真实 Google/provider readback；落到配置、部署和公网事实分离.

### dqhieu/gsc-seo-autopilot — gsc-seo-autopilot

- Source: https://github.com/dqhieu/gsc-seo-autopilot
- Discovery/trust context: 2026-08-07: 22 skills.sh installs; recurring SEO command routing was inspected.
- Stage lesson: 保留命令路由；改为逐 action 授权、执行和回读.

## Keep / Adapt / Reject / Invent

- Keep: 能力感知的 provider 操作、命令路由和真实回读.
- Adapt: 把上线拆成 Git、部署、域名、DNS、HTTP 五类互不替代证据.
- Reject: 默认全自治、共享授权、dashboard 状态代替公网结果.
- Invent: 中央 permission ledger 与 launch report 的 authorization ID 交叉验证.

## Evidence boundary

Catalog installs and repository stars are adoption/popularity signals, not user ratings, correctness proof or business outcomes. The shared parent report is `../web-business-pipeline/reports/prior-art-research.md`. Real provider, ranking, traffic, revenue and end-user evidence remain missing until an authorized project records them.
