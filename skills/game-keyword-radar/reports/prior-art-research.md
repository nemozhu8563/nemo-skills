# Prior Art Research

Date: 2026-08-07

The built-in dual-catalog research completed three queries successfully and returned 78 candidate families. Four source implementations were reviewed directly before designing this skill.

## Reviewed skills

### Eronred/aso-skills — keyword-research

- Public metadata observed: MIT, not archived, 1,724 GitHub stars, last push 2026-07-27; skills.sh showed 2.7K installs.
- Adopted: explicit Volume / Difficulty / Relevance / Intent dimensions and primary, secondary, long-tail grouping.
- Rejected: app-store-specific ranking assumptions that do not map directly to game guide sites.

### Eronred/aso-skills — market-pulse

- Same repository metadata; skills.sh showed 2.3K installs.
- Adopted: multiple source signals plus historical persistence; one observation is not a trend.
- Rejected: treating a single marketplace pulse as enough evidence for product selection.

### OpenClaudia/openclaudia-skills — semrush-research

- Public metadata observed: MIT, not archived, 621 GitHub stars, last push 2026-08-07; skills.sh showed 373 installs.
- Adopted: Semrush-native fields, explicit error states and quota boundaries.
- Rejected: API-key-first design, because this workflow uses the user's existing browser-based 3ue channel and must not extract credentials.

### nexscope-ai/Amazon-Skills — amazon-keyword-research

- Public metadata observed: MIT, not archived, 505 GitHub stars, last push 2026-07-23; skills.sh showed 1K installs.
- Adopted: deterministic long-tail expansion and deduplicated keyword groups.
- Rejected: the original shell/Python implementation interpolated user keywords into executable strings and was Amazon-specific.

## Evidence boundary

Install counts and GitHub stars are popularity signals, not ratings or proof of quality. No trustworthy user-rating evidence was available. This package claims only that the mechanisms above were inspected and selectively adapted; its own validated advantages are limited to local tests, trigger evaluation, and actual provider-backed results when those are recorded separately.
