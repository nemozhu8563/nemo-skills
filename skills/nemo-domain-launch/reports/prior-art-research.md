# Nemo Domain Launch Prior-Art Research

- Researched at: 2026-08-14
- Discovery: Qiaomu Meta unified runner across skills.sh and SkillsMP, plus direct source inspection and local Nemo skill comparison
- Queries: `Cloudflare Pages custom domain deployment`, `Vercel custom domain Cloudflare DNS deployment`, `deployment skill formal domain AGENTS.md`
- Catalog result: all three queries succeeded in both catalogs; 67 candidate families were collected before relevance screening.
- Metric semantics: skills.sh numbers are installs. SkillsMP stars, when present, are repository stars—not per-skill ratings, satisfaction, or correctness.
- Rating evidence: `missing evidence`; no trustworthy per-skill user-review score was used.

## Source-inspected shortlist

| Candidate | Dated signal | Trust/license signal | Learned mechanism | Deliberate constraint |
|---|---:|---|---|---|
| [`genericService/claude-skills:cloudflare-pages`](https://github.com/genericService/claude-skills) | 90 skills.sh installs observed 2026-08-14 | source revision `5ce3abf53bd811379d4e82ee86a1d8ff90543c82`; repository license not used as authority | CLI-first Pages workflow and early static/SSR routing | no token copying or persistent shell-secret setup |
| [`bm629/agent-skills:cloudflare-pages-ops`](https://github.com/bm629/agent-skills) | 56 skills.sh installs observed 2026-08-14 | MIT; source revision `489dd7b5a266b766787eea60fdf03725f7372c4d` | read-before-write provider operations and independent readback | provider state alone cannot prove a public launch |
| [`makerjackie/jackie-skills-starter:cloudflare-dns`](https://github.com/makerjackie/jackie-skills-starter) | 45 skills.sh installs observed 2026-08-14 | no clear license found; source revision `145241e853949d33fd4f9c59a62685688e535b13` | explicit DNS inventory and record-level operations | no fuzzy deletion; no unlicensed prose or code copied |
| [`lovstudio/skills:deploy-to-vercel`](https://github.com/lovstudio/skills) | 28 skills.sh installs observed 2026-08-14 | community source, inspected read-only | compact Vercel deployment sequencing | reject universal DNS values, token persistence, and fixed-sleep success claims |
| [`render-oss/skills:render-static-sites`](https://github.com/render-oss/skills) | 216 skills.sh installs and 76 repository stars observed 2026-08-14 | official provider repository, MIT; source revision `4e4a00a51a99aa772793b1a2ab3abe0e214c88ef` | build/output discovery and post-deploy provider verification | Render-specific commands and assumptions were not carried over |

Supporting local comparison: `nemo-skills:game-site-launch` was inspected for its independent authorization, execution, and readback contract. It remains the broader game-site state-machine owner; this package handles the first-domain deployment slice and does not claim to update that central report.

## Synthesis ledger

### Keep

- Prefer CLI/API execution when it is more reliable than a dashboard.
- Read identity, account/team, project, zone, domain, and record state before every write.
- Separate static artifacts from dynamic/SSR hosting requirements.
- Read provider state back after each mutation.

### Adapt

- Convert the old static-only Pages workflow into an explicit two-mode router: `static_pages` and `saas_vercel`.
- Keep Spaceship as registrar and Cloudflare as authoritative DNS in both routes while leaving mutable registrar UI in a runtime adapter.
- Turn generic “check DNS” guidance into distinct hosting-provider, Cloudflare/public-DNS, public-HTTPS, local-cache, and project-file evidence channels.
- Treat Vercel Domain Settings as live project data rather than a constant DNS recipe.

### Reject

- Triggering on ordinary deploy/maintenance work after a project already has a formal domain.
- Deleting DNS by name alone, clearing a zone, or treating imported records as disposable.
- Asking users to paste tokens, OAuth callbacks, Cookies, verification codes, or browser storage into chat or shell profiles.
- Hardcoded Vercel A/CNAME/TXT values, automatic proxy enablement during acceptance, and fixed sleeps followed by success claims.
- Declaring completion from a green provider status, browser cache, or successful file write without the other evidence channels.

### Invent

- A first-domain eligibility gate that treats `pages.dev` and `vercel.app` as provider defaults, not formal production domains.
- A dual-route launch report requiring the inactive hosting action to be a coherent `not_required` triad.
- Separate `domain_ready` and `launch_complete` claims so `AGENTS.md` bookkeeping cannot impersonate public launch evidence.
- An idempotent, project-root-only `AGENTS.md` writer that preserves existing content and fails closed on conflict, malformed markers, or symlinks.
- An ordinary DNSSEC chain separating old DS expiry, NS cutover, Cloudflare signing, new DS publication, and two-resolver AD verification.

## Official-source boundary

Cloudflare and Vercel behavior is grounded separately in dated links under `references/official-sources.md`; prior-art skills are workflow references, not platform authority. Spaceship's official support page was challenge-protected during the review, so no fixed UI path or button label is claimed.

## Missing evidence

- No provider-backed head-to-head run compares this Skill against a baseline or inspected candidate.
- No human blind review has been completed.
- Catalog adoption metrics do not prove safety, correctness, or user satisfaction.
- Provider, CLI, registrar UI, and DNS behavior can change after the research date and must be refreshed before mutation.
