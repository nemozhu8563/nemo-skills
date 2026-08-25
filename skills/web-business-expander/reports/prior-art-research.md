# Prior Art Research — web-business-expander

Date: 2026-08-24

The update research ran three intent-shaped queries — `analytics driven website optimization`, `SEO content optimization`, and `search console content improvement` — against both configured catalogs. All six catalog calls completed and produced 74 deduplicated candidate families. No third-party Skill code was executed.

## Current catalog signals

- `kostja94/marketing-skills:google-search-console` appeared for Search Console improvement with 1.5K skills.sh installs.
- `kostja94/marketing-skills:content-optimization` appeared for SEO content optimization with 1K skills.sh installs.
- `inhouseseo/superseo-skills:improve-content` appeared for Search Console content improvement with 76 skills.sh installs.
- These are discovery/popularity signals only. The catalog marked them as requiring source review, so this update does not import their instructions or claim their outcomes.

## Previously source-reviewed mechanisms retained

### coreyhaines31/marketingskills — programmatic-seo

- Source: https://github.com/coreyhaines31/marketingskills/tree/main/skills/programmatic-seo
- Keep: intent alignment, reusable page structure and explicit rejection of thin mass generation.
- Adapt: the same evidence discipline now applies to improving an existing page as well as adding a new one.

### thatrebeccarae/claude-marketing — content-pipeline

- Source: https://github.com/thatrebeccarae/claude-marketing
- Keep: staged artifacts and resumable handoffs.
- Adapt: every optimization or expansion batch reuses planner → evidence → builder → QA → launch → telemetry.

## Keep / Adapt / Reject / Invent

- Keep: intent-level evidence, staged artifacts, differentiated value and explicit human review.
- Adapt: support `optimize-existing` and `expand-new`; require evidence, target, problem, expected impact and acceptance criteria for every change item.
- Reject: fixed `1–3`, `5`, or `10` page thresholds as a Skill boundary; reject thin-page generation, unsupported claims and review sampling that ignores the actual change batch.
- Invent: size the smallest coherent batch from evidence strength, risk, dependencies and full-review capacity; keep stable page IDs for existing-page optimization and reuse the central grow re-entry chain.

## Evidence boundary

Catalog installs are adoption/popularity signals, not user ratings, correctness proof or business outcomes. The shared parent report is `../web-business-pipeline/reports/prior-art-research.md`. Provider-backed ranking, traffic, revenue, end-user outcomes and a real project E2E remain missing evidence until an authorized project records them.
