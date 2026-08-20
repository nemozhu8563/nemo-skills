# Creation Handoff

## Package identity

- Name: `nemo-site-telemetry`
- Version: `0.3.0`
- Mode: Governed
- Lifecycle: local
- Audience: one operator onboarding telemetry for game, SaaS, content, documentation, or other websites
- Canonical target: `/Users/nemo/Documents/AI/awesome-skills/nemo-skills/skills/nemo-site-telemetry`
- Project install targets: `game-site`, `image-generator`, `payforplus`, and `new-api` under each project's `.agents/skills/nemo-site-telemetry`
- Global install: intentionally absent

## Decision summary

One self-contained Skill now owns first-time/resumed GA4, Microsoft Clarity, and GSC onboarding. Its first observable action for a new site is a read-only readiness check, followed by a user-visible Google API bootstrap and per-component configuration plan before any login, code change, or external write. GSC logic is migrated rather than delegated to `nemo-gsc-submit`; the package has no runtime dependency on that old Skill. Version `0.3.0` adds bounded GSC Search Analytics readback to the standard-library adapter while preserving controlled bootstrap, GSC sitemap plan-apply-readback, GA4 Admin/Data flows, and the separate game-pipeline telemetry stage.

## Reference skills studied

- [`kostja94/marketing-skills:analytics-tracking`](https://skills.sh/kostja94/marketing-skills/analytics-tracking): retained the separation among installation, transport, Realtime, and DebugView; this appears in `SKILL.md`, `references/ga4.md`, and the output contract.
- [`mvanhorn/printing-press-library:pp-google-search-console`](https://skills.sh/mvanhorn/printing-press-library/pp-google-search-console): retained exact-resource discovery and read-before-write; this appears in `references/gsc.md` and the sitemap state machine.
- [`ncosentino/google-search-console-mcp`](https://github.com/ncosentino/google-search-console-mcp): retained the value of a small read-only Search Console surface, but adapted it behind the package-owned adapter because its `webmasters.readonly` scope cannot submit a sitemap.
- [`googleanalytics/google-analytics-mcp`](https://github.com/googleanalytics/google-analytics-mcp): retained official read-only Admin/Data API patterns, while rejecting the assumption that a read-only MCP can perform GA4 property or stream creation.

## Absorbed, rejected, and invented

- Keep: exact resource identity, least-capability reads, read-before-write, and provider-side readback.
- Adapt: one cross-site package exposes browser, Google API, or mixed evidence without allowing either surface to widen the other surface's authorization.
- Reject: a separate GSC Skill dependency, a `game-*` universal name, third-party MCP runtime installation, persistent token storage, delete/permission APIs, and automatic GA4 create replay.
- Invent: authorization-bound `plan → apply → readback`, a credential-free cross-process single-recovery-submit checkpoint, public sitemap SSRF protection with DNS/IP pinning, semantic read handling for POST-based APIs, and a fixed Search Analytics primitive that keeps ranking analysis outside the onboarding router.

## Stable contract

- Any one or more of GA4, Clarity, and GSC may be requested.
- First use/new-site work starts with a user-visible read-only `readiness_check`; unknown identity, session, project, permission, consent, or resource facts remain blockers.
- Before external writes, `configuration_plan` records Google auth/project/scope/service prerequisites and each component's exact target, existing matches, action, write, readback, and rollback.
- Exact resources are discovered before writes and resumed after interruption.
- production-only/preview isolation is an explicit local governance choice.
- Consent values come from an existing CMP/policy decision; this Skill gives no legal opinion.
- GA4 setup/request/Realtime/DebugView are separate.
- Clarity setup/tag/request/recording are separate.
- GSC property/DNS/ownership/sitemap/indexing are separate.
- GSC Search Analytics is an exact-property, bounded, read-only primitive; top aggregated rows are not a complete export, stable snapshot, or indexing evidence.
- GSC sitemap status checks and manual-submission follow-ups are read-only; explicit submit/onboarding authorization permits one idempotent submit only after exact list/get confirms absence.
- Provider/human evidence absent from a run is labeled `missing evidence`.
- Google API bootstrap is separate from normal reads; no ordinary status/readback command enables services.
- POST-based URL Inspection and GA4 Realtime remain bounded read operations, while sitemap submit and GA4 create keep no-auto-retry write semantics.
- GSC ambiguous submit permits at most one authorization-bound recovery submit within the recovery window; GA4 ambiguous create is readback-only.

## File map

- `SKILL.md`: router, gates, compact workflow, output and recovery contract.
- `references/workflow.md`: end-to-end evidence order and recovery paths.
- `references/ga4.md`: gtag, consent, requests, Realtime and DebugView.
- `references/clarity.md`: project/tag, consentv2, collect and recordings.
- `references/gsc.md`: migrated property/DNS/ownership/sitemap contract plus bounded Search Analytics readback.
- `references/governance.md`: authorization, trust, secrets, idempotency and rollback.
- `references/official-sources.md`: current first-party documentation.
- `references/google-api.md`: fixed API surface, ADC/bootstrap, scopes, CLI, safe errors, recovery, and browser fallback.
- `scripts/google_api_adapter.py` and `scripts/google_api/`: deterministic adapter, provider allowlists, redaction, plans, and recovery limiter.
- `contracts/google-api-output.schema.json`: stable credential-free adapter envelope.
- `evals/trigger_cases.json`: cross-site activation and neighbor exclusions.
- `evals/output_cases.json`: provider, consent, recovery and claim failure scenarios.
- `tests/test_contract.py`, `tests/test_google_api_contract.py`, and `tests/test_google_api_adapter.py`: deterministic package and adapter contracts using only fakes/fixtures.

## Release and installation sequence

1. Validated package structure and frontmatter.
2. Ran contract tests and trigger eval.
3. Exported Skill IR and inspected resource boundaries.
4. Ran secret scan and local release check.
5. Installed the canonical directory through four project-level symlinks and read back `readlink`, `realpath`, and root `SKILL.md` for each project.
6. Removed the global `nemo-site-telemetry` link and the stale `payforplus` link to `nemo-gsc-submit`; the superseded `nemo-gsc-submit` canonical directory remains absent.

## Rollback

The old package was untracked and was intentionally deleted only after the new canonical package passed validation and install readback. Git cannot directly recover that old directory. Recovery now means fixing one or more project-level `nemo-site-telemetry` links or reconstructing from current task evidence; do not recreate the old runtime dependency or a global link.

## Validation evidence

- package validation: passed with no warnings.
- contract and adapter tests: 41/41 passed.
- trigger eval: 28/28 passed; zero false positives and zero false negatives at threshold 0.38.
- output behavior specification: 29 cases parsed and covered, including readiness, sitemap intent, Google API bootstrap, secret redaction, ambiguous writes, Search Analytics and analysis exclusions.
- live read-only readiness: Python 3.14.5, gcloud 568.0.0 and an active CLI identity are available; Cloud project is unset, while the host-side `gsc-read` ADC probe verified scope and Search Console resource access with zero-click steady state.
- provider-backed Search Analytics: `sc-domain:quasimorphwiki.site`, 2026-07-23 through 2026-08-19, query dimension, FINAL data, offset 0 and limit 100 returned 11 rows with `row_limit_reached=false`; raw query rows were not stored in package evidence.
- live compatibility regression: the first query safely rejected lowerCamel `byProperty`; after allowlisted normalization to `BY_PROPERTY`, the same query passed, while unknown aliases remain fail closed.
- quasimorphwiki production check: passed for 23 pages, 6 business categories, 21 local materials, and 517 build artifacts with the exact production origin.
- sitemap intent regression: status-only absence, manual-submit readback, explicit submit-once, interrupted-submit recovery, and the cross-process single recovery claim are covered.
- adapter safety regression: public sitemap SSRF/DNS rebinding, URL-prefix path boundaries, plan integrity, provider-status normalization, GA4 invalid stream URIs, and semantic read-only POST retries are covered.
- Skill IR export: passed for schema `2.0.0-qiaomu-lite`.
- output contract evidence: deterministic checks passed and the bounded GSC Search Analytics primitive has provider-backed evidence; human review and unrelated provider flows remain missing.
- secret scan: passed with zero findings.
- local release check: an exact-copy temporary `codex/nemo-site-telemetry-local-gate` branch passed 8 gates with 1 expected clean-install warning and 0 blocks; the canonical checkout remains on the default branch and is not publication-ready by design.
- project symlink readback: passed for `game-site`, `image-generator`, `payforplus`, and `new-api`; every `readlink` and `realpath` resolves to the canonical directory, and root `SKILL.md` is readable.
- scope cleanup: passed; the global `nemo-site-telemetry` link, old `nemo-gsc-submit` canonical directory, and stale `payforplus` old link are absent.

## Remaining evidence

- Blind human review of real output: missing evidence.
- GitHub publication/install path: not requested.
- Full GA4, Clarity, sitemap-mutation and cross-provider onboarding run: missing evidence. Cloud/quota project remains unset, so API bootstrap/write flows were not attempted; no interactive login, account switch or permission change occurred.
- Commit, push, PR, publication, and deployment: not requested.
