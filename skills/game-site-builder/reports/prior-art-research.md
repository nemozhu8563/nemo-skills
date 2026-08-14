# Prior Art Research — game-site-builder

Date: 2026-08-07

This package is a modular stage of the already researched `game-site-pipeline` workflow. It does not pretend that ten independent catalog searches were run. The governed parent research deduplicated 99 candidate families and inspected the implementations below at source level; this stage reuses only the mechanisms relevant to its narrower job.

### coreyhaines31/marketingskills — programmatic-seo

- Source: https://github.com/coreyhaines31/marketingskills/tree/main/skills/programmatic-seo
- Discovery/trust context: 2026-08-07: 114.8K skills.sh installs; repository stars are popularity signals, not quality ratings.
- Stage lesson: 保留 unique value 和反薄页原则；落到矩阵内有限实现.

### thatrebeccarae/claude-marketing — content-pipeline

- Source: https://github.com/thatrebeccarae/claude-marketing
- Discovery/trust context: 2026-08-07: 72 skills.sh installs; staged artifacts were inspected at source level.
- Stage lesson: 保留 staged artifact；用跨文件 manifest 替代生成文件即完成.

## Keep / Adapt / Reject / Invent

- Keep: 独特页面价值、分阶段内容产物和可恢复构建.
- Adapt: 将生成结果绑定页面契约、source IDs、claim IDs 与真实文件哈希.
- Reject: 矩阵外批量生成、复制竞品、为复用而提前重构.
- Invent: 内容文件、页面意图和 claim 证据的三向 manifest.

## Evidence boundary

Catalog installs and repository stars are adoption/popularity signals, not user ratings, correctness proof or business outcomes. The shared parent report is `../game-site-pipeline/reports/prior-art-research.md`. Real provider, ranking, traffic, revenue and end-user evidence remain missing until an authorized project records them.
