# Growth Rules

## Observation without data

`telemetry_verified` proves configuration, not performance. When GSC reports `no_valid_data` or `error`, record technical checks and at least two future review dates representing day 7 and day 14. The only allowed lifecycle decision without valid GSC data is `hold`; do not claim growth failure or retire the site.

Technical checks may include sitemap reachability, robots rules, canonical tags, internal links, page status codes, GSC property scope and manual URL inspection. They are diagnostics, not traffic evidence.

## Evidence-based decisions

- `grow`: valid query/page data, a concrete opportunity and human approval justify more pages or improvement.
- `hold`: insufficient evidence or a deliberate wait; keep the next review explicit.
- `retire`: valid data plus a human-approved rationale show continued effort is not justified.
- `templated`: the project has a reviewed reusable scope and explicit product-specific exclusions. A working codebase alone is not a reusable template.

Store raw counts and observation period in `analytics-snapshot.json`. Store the decision rationale in both the snapshot and `decision-log.md`. Avoid universal traffic, ranking, revenue or time-to-index promises.
