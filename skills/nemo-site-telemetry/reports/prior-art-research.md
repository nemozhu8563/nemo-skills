# Prior-Art Research

- Researched at: 2026-08-19
- Queries:
  - `google analytics clarity search console setup`
  - `website telemetry onboarding`
  - `search console sitemap verification`
  - `GA4 analytics tracking setup`
- Catalog status: skills.sh and SkillsMP both returned results for all query families; no catalog-side missing evidence.
- Metric semantics: skills.sh installs are ecosystem adoption telemetry; GitHub stars are repository-level popularity. Neither proves correctness, fit, or skill-specific quality.
- Rating/review evidence: unavailable.

## Shortlist

| Candidate | Why relevant | skills.sh installs | Repository stars | Trust/license | Adopt | Reject |
|---|---|---:|---:|---|---|---|
| [`kostja94/marketing-skills:analytics-tracking`](https://skills.sh/kostja94/marketing-skills/analytics-tracking) | GA4 setup, event naming, Realtime/DebugView validation | 2.1K | 905 | MIT repository; source read 2026-08-19 | Keep setup vs validation separation and provider-side readback | No Clarity, GSC onboarding, production-origin isolation, DNS ownership, or recovery contract |
| [`kostja94/marketing-skills:google-search-console`](https://skills.sh/kostja94/marketing-skills/google-search-console) | Clear performance/indexing/sitemap report semantics | 1.5K | 905 | MIT repository; source read 2026-08-19 | Keep performance, indexing, and sitemap as separate states | Primarily ongoing analysis, not property/DNS onboarding |
| [`mvanhorn/printing-press-library:pp-google-search-console`](https://skills.sh/mvanhorn/printing-press-library/pp-google-search-console) | Agent mode, dry-run, site/sitemap list/get/submit and idempotent readback | 447 | 1,937 | Skill frontmatter Apache-2.0; source read 2026-08-19 | Keep read-before-write, explicit exit/readback semantics | Reject mandatory CLI, OAuth/token persistence, SQLite corpus, and broad analysis dependency |
| [`OpenClaudia/openclaudia-skills:search-console`](https://github.com/OpenClaudia/openclaudia-skills) | Alternative GSC automation packaging | unavailable | 649 | MIT repository; source read 2026-08-19 | None beyond confirming adjacent demand | Reject direct OAuth secret/token environment workflow and weaker provider/DNS evidence boundary |
| Local `nemo-gsc-submit` | Governed Domain property, DNS, ownership, sitemap, recovery and claim guard | n/a | n/a | Local MIT package | Migrate the full GSC onboarding contract into this package | Reject runtime adapter/dependency and separate trigger surface after migration |

Repository metrics were observed on 2026-08-19. No user-rating dataset was available, so the design does not rank candidates by popularity alone.

## Contribution ledger

### Keep

- From `analytics-tracking`: distinguish code installation, network transport, Realtime, and DebugView.
- From `google-search-console`: keep sitemap, indexing, performance, and configuration as distinct states.
- From `pp-google-search-console`: exact resource discovery, read-before-write, idempotency, and read-after-submit.
- From local `nemo-gsc-submit`: Domain property default, manual TXT, provider + two-resolver evidence, Owner readback, sitemap claim guard, token preservation, browser recovery, permission and rollback boundaries.

### Adapt

- Generalize telemetry from game sites to game, SaaS, content, documentation, and other websites.
- Replace provider-specific assumptions with GA4/Clarity/GSC-native UI/API readback and project-native build tools.
- Apply a production exact-origin gate and preview-negative test to both GA4 and Clarity.
- Treat public frontend IDs as configuration while keeping credentials and GSC verification material secret.
- Convert “analytics installed” into separate setup, request, provider, recording, crawl, and indexing statuses.

### Reject

- A two-Skill design where the new package merely calls `nemo-gsc-submit`.
- A `game-*` package name or game-pipeline state as the universal API.
- Third-party CLI installation, persistent OAuth/token storage, or a new analytics dependency.
- Popularity-only selection, dashboard-only claims, duplicate-resource retries, and any claim that sitemap submission proves indexing.
- Hard-coding analytics consent as granted for every site; consent values must follow the site's actual policy/CMP.

### Invent

- One self-contained cross-site package with no runtime dependency on the old GSC Skill.
- Build-time exact production-origin gate plus runtime origin/hostname guard.
- Required positive production verification and negative preview/local verification.
- Unified but independent output fields for GA4, Clarity, and GSC.
- Declare provider/human evidence per capability; keep `missing evidence` until an authorized packaged-skill run reads back that exact capability.

## Google API adapter addendum (2026-08-20)

The adapter redesign, current in `0.3.0`, additionally inspected these execution surfaces:

- [`ncosentino/google-search-console-mcp`](https://github.com/ncosentino/google-search-console-mcp): keep its small read-only surface; reject it as the package runtime because `webmasters.readonly` cannot submit a sitemap.
- [`AminForou/mcp-gsc`](https://github.com/AminForou/mcp-gsc): keep the evidence that sitemap mutation is API-accessible; reject a broad submit/delete tool surface for this governed onboarding package.
- [`pijusz/mcp-gsc`](https://github.com/pijusz/mcp-gsc): keep write-disabled-by-default as a safety signal; replace its coarse write toggle with per-operation intent, scope, plan, apply, and readback gates.
- [`googleanalytics/google-analytics-mcp`](https://github.com/googleanalytics/google-analytics-mcp): keep official read-only Admin/Data patterns; add package-owned create-only flows because the official MCP does not create properties or streams.

The chosen adapter-first design avoids a mutable third-party MCP runtime dependency. A future MCP shim may wrap the same tested core, but it must not duplicate authentication, authorization, redaction, or recovery logic.

## Why this design is stronger

The shortlisted public Skills are useful specialists, but none combines all three providers with production isolation, consent boundaries, DNS ownership, recovery, and downstream claim separation. The local GSC package supplies the most mature governed control plane; the new package preserves that work while removing the adapter boundary and adding GA4/Clarity transport and provider evidence.

## Assumptions and missing evidence

- Provider UIs, consent behavior, and report timing are mutable and must be rechecked before future changes.
- The catalog had no reliable rating/review data.
- A 2026-08-20 authorized packaged-skill run verified only the bounded GSC Search Analytics read primitive for one exact property/window. GA4, Clarity, sitemap mutation, bootstrap writes, complete cross-provider onboarding, and blind human output review remain `missing evidence`.
