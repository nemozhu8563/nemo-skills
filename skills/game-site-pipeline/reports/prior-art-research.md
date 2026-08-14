# Prior Art Research

Date: 2026-08-07

The governed dual-catalog search completed all configured queries and returned 99 candidate families. Four implementations were then reviewed at source level before this package was designed. Catalog counts below are discovery metadata observed on the research date; live GitHub checks were used only to confirm repository activity and approximate current stars.

## Reviewed implementations

### coreyhaines31/marketingskills — programmatic-seo

- Discovery evidence: 114.8K skills.sh installs; SkillsMP catalog recorded 42,958 repository stars; the live repository was approximately 43.4K stars.
- Repository evidence: MIT license, active recent maintenance.
- Keep: intent-aligned pages, hub-and-spoke information architecture, unique value per page, and explicit rejection of thin mass generation.
- Adapt: replace generic pSEO scale advice with a page matrix, normalized intent ownership, first-five-page human review, and a content hash gate.
- Reject: page count or template availability as proof that expansion is justified.
- Source: https://github.com/coreyhaines31/marketingskills/tree/main/skills/programmatic-seo

### AgriciDaniel/claude-seo — seo-google

- Discovery evidence: SkillsMP catalog recorded 13,269 repository stars; the live repository was approximately 13.6K stars.
- Repository evidence: MIT license, active recent maintenance.
- Keep: capability-aware Google integrations and actual Search Console / GA readback.
- Adapt: split setup, property readback, indexing and performance data into separate proofs; allow existing properties without pretending a new setup occurred.
- Reject: use of Google Indexing API for ordinary game guide pages.
- Source: https://github.com/AgriciDaniel/claude-seo/tree/main/skills/seo-google

### thatrebeccarae/claude-marketing — content-pipeline

- Discovery evidence: 72 skills.sh installs; live repository approximately 95 stars.
- Repository evidence: MIT license.
- Keep: named stage artifacts and resumable work.
- Adapt: every stage is checked through cross-file semantics, hashes and evidence, not through output-file existence.
- Reject: treating a generated artifact as automatic stage completion.
- Source: https://github.com/thatrebeccarae/claude-marketing

### dqhieu/gsc-seo-autopilot — gsc-seo-autopilot

- Discovery evidence: 22 skills.sh installs; live repository approximately 9 stars.
- Repository evidence: MIT license.
- Keep: explicit command routing for recurring SEO operations.
- Adapt: a deterministic local CLI exposes `status`, `validate`, `gate` and `transition` while provider operations remain outside the bundled runtime.
- Reject: default full autonomy, configuration or state inside the Skill directory, and weak-evidence bulk content changes.
- Source: https://github.com/dqhieu/gsc-seo-autopilot

## Invented for this workflow

- An immutable radar-to-site `candidate-lock.json` with exact human confirmation and a hash over stable key plus platform IDs.
- Claim-level evidence rules for redemption codes, numeric values and official links.
- A permission ledger where domain purchase, DNS, Git push, deployment, GSC, GA and ads are independent actions.
- Layered readback that never treats deployment, domain, telemetry, indexing or traffic as interchangeable.
- A no-data branch that permits diagnostics and scheduled hold, but blocks grow and retire.
- Old-domain residue scanning and a first-five-page human-review gate before batch expansion.

## Evidence boundary

No trustworthy rating evidence was available from either catalog. Install counts and repository stars are popularity signals, not ratings, correctness proof or outcome evidence. The package does not claim that prior-art popularity validates this workflow. Its own claims are limited to mechanisms directly implemented and local evaluations actually run; provider, ranking, traffic, revenue and user-outcome evidence remain missing until a real authorized project records them.
