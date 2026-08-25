# Prior Art Research — web-business-qa

Date: 2026-08-07

This package is a modular stage of the already researched `web-business-pipeline` workflow. It does not pretend that ten independent catalog searches were run. The governed parent research deduplicated 99 candidate families and inspected the implementations below at source level; this stage reuses only the mechanisms relevant to its narrower job.

### thatrebeccarae/claude-marketing — content-pipeline

- Source: https://github.com/thatrebeccarae/claude-marketing
- Discovery/trust context: 2026-08-07: 72 skills.sh installs; staged artifacts were inspected at source level.
- Stage lesson: 保留阶段清单；改为真实命令、哈希和语义检查.

### AgriciDaniel/claude-seo — seo-google

- Source: https://github.com/AgriciDaniel/claude-seo/tree/main/skills/seo-google
- Discovery/trust context: 2026-08-07: SkillsMP recorded 13,269 repository stars; no rating or outcome evidence was available.
- Stage lesson: 保留 readback 分层；本 Skill 只证明 local，不越界证明 online.

## Keep / Adapt / Reject / Invent

- Keep: 阶段检查表、可恢复交付和真实读回分层.
- Adapt: 增加当前变更批次逐页人审、旧域名扫描、逐项 not_applicable 理由与 rollback；审核范围随真实变更批次而不是固定页数变化.
- Reject: 模型自批、单一 build 即发布就绪、preview 代替公网证明.
- Invent: 本地七类检查与人审/哈希/域名残留的联合 gate.

## Evidence boundary

Catalog installs and repository stars are adoption/popularity signals, not user ratings, correctness proof or business outcomes. The shared parent report is `../web-business-pipeline/reports/prior-art-research.md`. Real provider, ranking, traffic, revenue and end-user evidence remain missing until an authorized project records them.
