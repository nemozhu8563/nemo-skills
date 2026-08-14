# Nemo Domain Launch 0.2.0 Creation Handoff

## Result

- Skill: `nemo-domain-launch` 0.2.0
- Job: give a project with no formal production domain exactly one governed route—Spaceship → Cloudflare DNS → Cloudflare Pages for static output, or Spaceship → Cloudflare DNS → Vercel for SaaS/SSR—then write the verified domain to project-root `AGENTS.md`
- Canonical path: `/Users/nemo/Documents/AI/awesome-skills/nemo-skills/skills/nemo-domain-launch`
- Status: local Governed use; installed by canonical symlink; not committed, pushed, or published to GitHub

## Reference skills studied

### `genericService/claude-skills:cloudflare-pages`

- Signal: 90 skills.sh installs observed 2026-08-14; source revision `5ce3abf53bd811379d4e82ee86a1d8ff90543c82`.
- Learned: CLI-first Pages deployment and early static/SSR routing.
- Applied in: `static_pages` routing and `references/runbook.md`.
- Rejected: credential-copy and persistent shell-secret patterns.

### `bm629/agent-skills:cloudflare-pages-ops`

- Signal: 56 skills.sh installs observed 2026-08-14; MIT; source revision `489dd7b5a266b766787eea60fdf03725f7372c4d`.
- Learned: read-before-write resource operations and provider readback.
- Applied in: Mutation Protocol and per-action authorization/execution/readback evidence.
- Rejected: treating provider state as sufficient public proof.

### `makerjackie/jackie-skills-starter:cloudflare-dns`

- Signal: 45 skills.sh installs observed 2026-08-14; source revision `145241e853949d33fd4f9c59a62685688e535b13`; clear license missing.
- Learned: explicit DNS inventory and record-level operations.
- Applied in: exact parking-record cleanup and rollback snapshots.
- Rejected: fuzzy deletion and copying unlicensed prose or code.

### `lovstudio/skills:deploy-to-vercel`

- Signal: 28 skills.sh installs observed 2026-08-14; community source inspected read-only.
- Learned: compact Vercel deployment sequencing.
- Applied in: the `saas_vercel` route and provider-default URL readback.
- Rejected: hardcoded universal DNS targets, token persistence in shell profiles, and fixed sleeps followed by success claims.

## Absorbed, rejected, and invented

- `keep`: CLI/API-first execution, read-before-write, runtime-based static/dynamic routing, and provider readback.
- `adapt`: both routes keep Spaceship as registrar and Cloudflare as authoritative DNS; Vercel DNS values come from the live target project.
- `reject`: existing-domain maintenance triggers, blanket DNS deletion, copied credentials, stale artifacts, provider-only success, and wildcard Vercel under Cloudflare nameservers.
- `invent`: first-domain eligibility, dual-route inactive-action triads, separate `domain_ready`/`launch_complete` claims, and an idempotent conflict-safe project-root `AGENTS.md` writer.

## Advantages and highlights

- `design advantage`: one package covers the user's two actual launch routes without conflating static output with SaaS/SSR hosting. Evidence: `SKILL.md`, `manifest.json`, and `agents/interface.yaml`.
- `design advantage`: a `pages.dev` or `vercel.app` address counts as provider-default-only, while those suffixes are forbidden as the final formal-domain claim. Evidence: `scripts/validate_launch_report.py` and tests.
- `design advantage`: hosting provider, public DNS, public HTTPS, local cache, and `AGENTS.md` writeback are independent evidence channels. Evidence: `references/evidence-and-rollback.md`.
- `validated advantage`: 30/30 trigger cases passed with no false positives or negatives; 43/43 deterministic unit tests passed across routing, report claims, public verification, secret rejection, and writeback behavior.
- `hypothesis`: the first-domain gate and staged evidence ledger should reduce false launch claims and risky DNS cutovers, but provider-backed comparison remains `missing evidence`.

## Verification and limits

- Python syntax: all bundled scripts and tests compiled successfully.
- Unit tests: 43/43 passed.
- Trigger evaluation: 30/30 passed; 0 false positives and 0 false negatives.
- Skill IR: regenerated for `nemo-domain-launch` 0.2.0 with owner `Nemo`.
- Package validation: passed with zero failures and zero warnings after handoff alignment.
- Local installation: the project-local `game-site/.agents/skills/nemo-domain-launch` and `payforplus/.agents/skills/nemo-domain-launch` entries resolve to the canonical directory and their root `SKILL.md` files are readable.
- Output evidence: 10 behavior cases and deterministic fixtures; provider-backed comparison and human blind review remain `missing evidence`.
- Publication: not requested and not performed. No commit, remote, PR, GitHub Release, or remote clean-install claim is made.
- Excluded mutations: domain purchase/transfer, paid upgrades, Git push, GSC, GA, ads, unrelated DNS, and game-site central state.
