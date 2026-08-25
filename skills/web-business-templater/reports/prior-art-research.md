# Prior Art Research — web-business-templater

Date: 2026-08-07

This package is a modular stage of the already researched `web-business-pipeline` workflow. It does not pretend that ten independent catalog searches were run. The governed parent research deduplicated 99 candidate families and inspected the implementations below at source level; this stage reuses only the mechanisms relevant to its narrower job.

### coreyhaines31/marketingskills — programmatic-seo

- Source: https://github.com/coreyhaines31/marketingskills/tree/main/skills/programmatic-seo
- Discovery/trust context: 2026-08-07: 114.8K skills.sh installs; repository stars and installs are popularity signals, not outcome proof.
- Stage lesson: 保留模板化页面与自动生成基础设施；增加 unique value 与反薄页边界.

### thatrebeccarae/claude-marketing — content-pipeline

- Source: https://github.com/thatrebeccarae/claude-marketing
- Discovery/trust context: 2026-08-07: 72 skills.sh installs; staged artifact and resumability mechanisms were inspected.
- Stage lesson: 保留可复用 staged infrastructure；将产品内容作为显式 exclusion.

## Keep / Adapt / Reject / Invent

- Keep: 模板驱动路由/SEO、内容与框架分离、可恢复验证.
- Adapt: 按框架/配置/内容三层拆分并增加第二产品替换测试.
- Reject: 万能框架、连产品内容复制、模板化等于公开发布.
- Invent: template_readiness 同时记录 reusable scope 与 product-specific exclusions.

## Evidence boundary

Catalog installs and repository stars are adoption/popularity signals, not user ratings, correctness proof or business outcomes. The shared parent report is `../web-business-pipeline/reports/prior-art-research.md`. Real provider, ranking, traffic, revenue and end-user evidence remain missing until an authorized project records them.
