# Nemo Supabase Auth Prior-Art Research

- Researched at: 2026-08-21
- Discovery: Qiaomu Meta unified runner across skills.sh and SkillsMP, direct shortlist source inspection, official installed Supabase Skill inspection, and local Nemo Governed package comparison
- Queries: `supabase google auth oauth`, `google oauth client configuration`, `oauth redirect uri security`
- Catalog result: all three queries completed in both catalogs; 69 candidate families were collected before relevance screening.
- Metric semantics: skills.sh numbers are installs. SkillsMP stars, when present, are repository stars, not per-Skill ratings or correctness.
- Rating evidence: `missing_evidence`; no trustworthy user-review score was used.

## Source-inspected shortlist

| Candidate | Dated signal | Trust/license | Learned mechanism | Deliberate constraint |
|---|---:|---|---|---|
| `openai-curated-supabase:supabase` | Installed official plugin inspected 2026-08-21 | provider-distributed local plugin | current-doc/changelog gate, provider verification, session safety | not treated as a complete Google Cloud + application + browser workflow |
| `sickn33/agentic-awesome-skills:nextjs-supabase-auth` | 6.2K skills.sh installs observed 2026-08-21 | MIT | PKCE callback, `exchangeCodeForSession`, trusted `getUser`, callback errors | no boilerplate copying and no code-only success claim |
| `mcollina/skills:oauth` | 1.1K skills.sh installs observed 2026-08-21 | MIT | exact redirects, state/PKCE, token safety | Fastify-specific implementation rejected |
| `yoanbernabeu/supabase-pentest-skills:supabase-audit-auth-config` | 402 skills.sh installs observed 2026-08-21 | MIT | auth configuration/readback and security audit mindset | no intrusive signup/pentest loop or mutation logging |
| `nemo-skills:nemo-domain-launch` | local Governed package | MIT | activation gate, exact action ledger, snapshots, rollback, claim guard, scoped symlink | DNS/domain behavior not carried over |

## Reuse decision

No existing Nemo-owned Skill provided the requested end-to-end job. Modifying the official cached Supabase plugin would be unsafe because it is upstream-managed and intentionally broad. Modifying `nextjs-supabase-auth` would preserve code scaffolding but still omit the Google/Supabase provider mutation and evidence boundaries. Therefore a new `nemo-supabase-auth` package is justified, while depending on the official Supabase Skill for current platform behavior.

## Synthesis ledger

### Keep

- Recheck current Supabase docs/changelog before live work.
- Use PKCE callback exchange and a server-trusted user check.
- Match redirect URIs exactly and keep OAuth/token material out of output.
- Read provider configuration back after mutation.

### Adapt

- Turn generic OAuth redirect advice into a five-row URL matrix separating Google origins, Google’s Supabase provider callback, Supabase Site URL, Supabase app callbacks, and application `redirectTo`.
- Turn an auth audit into an audit-first reuse decision before creating Google resources.
- Turn code-only callback guidance into a four-channel evidence ladder across source, Google, Supabase, and a real protected browser session.
- Apply Nemo’s Governed action/before/readback/rollback structure to account and session side effects.

### Reject

- Creating duplicate clients without inventory or repurposing unrelated production clients.
- Framework boilerplate that ignores existing project helpers.
- Fastify-specific code and intrusive pentest/signup loops.
- Any flow that copies a credential, OAuth code, token, Cookie, personal email, user ID, or browser storage into reports or tool output.
- `Enabled`, HTTP 200, account chooser, or user-row existence as standalone end-to-end proof.

### Invent

- Separate `configuration_ready` and `end_to_end_verified` claims.
- A human-in-the-loop direct provider-field handoff for the Google credential value.
- A real-login mutation gate that announces consent, user create/reuse, and session effects.
- A validator that rejects callback-layer conflation, unsafe URL shapes, sensitive keys/value patterns, unsupported claims, and missing action evidence.

## Official-source boundary

Current Supabase Google login, Redirect URLs, and changelog pages were inspected and are recorded in `references/official-sources.md`. Direct Google Developers/Auth Platform pages timed out through all attempted retrieval paths. No stable Google button names or screen order are claimed; direct Google documentation remains `missing_evidence`, and live provider readback is mandatory.

## Missing evidence

- No provider-backed head-to-head run compares this Skill with the baseline or an inspected candidate.
- No human blind review has been completed.
- Catalog adoption metrics do not prove safety, correctness, or user satisfaction.
- Google and Supabase product/UI behavior can change after the research date and must be refreshed before mutation.
