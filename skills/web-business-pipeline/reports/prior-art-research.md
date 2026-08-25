# Prior-Art Research

Original research: 2026-08-07

Web-business generalization amendment: 2026-08-24

The original governed dual-catalog search returned 99 candidate families. A 2026-08-24 refresh for `web business validation pipeline`, `website launch analytics growth`, and `SEO business monetization workflow` returned 78 candidate families. Four implementations were reviewed at source level; the refresh remains discovery metadata and did not justify adopting uninspected code. Catalog counts below are historical observations, not current ratings or outcome proof.

## Reviewed implementations

### coreyhaines31/marketingskills — programmatic-seo

- Discovery evidence: 114.8K skills.sh installs; SkillsMP catalog recorded 42,958 repository stars; the live repository was approximately 43.4K stars.
- Repository evidence: MIT license, active recent maintenance.
- Keep: intent-aligned pages, hub-and-spoke information architecture, unique value per page, and explicit rejection of thin mass generation.
- Adapt: replace generic pSEO scale advice with a page matrix, normalized intent ownership, full current-change-batch human review, and a content hash gate.
- Reject: page count or template availability as proof that expansion is justified.
- Source: https://github.com/coreyhaines31/marketingskills/tree/main/skills/programmatic-seo

### AgriciDaniel/claude-seo — seo-google

- Discovery evidence: SkillsMP catalog recorded 13,269 repository stars; the live repository was approximately 13.6K stars.
- Repository evidence: MIT license, active recent maintenance.
- Keep: capability-aware Google integrations and actual Search Console / GA readback.
- Adapt: split setup, property readback, indexing and performance data into separate proofs; allow existing properties without pretending a new setup occurred.
- Reject: use of Google Indexing API for ordinary content pages.
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

## User-supplied domain method

龙猫《SEO出海赚钱逻辑》提供了项目选择、商业闭环、意图演进、增长杠杆和止损框架。它不是 Agent Skill，但直接影响了本次通用化：

- Keep: 客户、问题、价值、商业模式、最高风险假设、主要指标和事件层级。
- Adapt: 把收入里程碑改写为 `search_growth`、`conversion_learning`、`commercial_scale` 三层证据，不把金额当生命周期状态。
- Reject: 重型 SWOT/PESTLE、缺证据的自动评分、澳洲本地 SEO 模板和任何垂直阈值成为中央硬门槛。
- Location: `references/commercial-validation.md`、candidate v2 `business_hypothesis`、telemetry 原始事件和 growth 决策理由。

## Invented for this workflow

- An immutable upstream-to-project `candidate-lock.json` with exact human confirmation and a hash over stable key plus provider-neutral identities.
- Qualification checks owned by each upstream method while the central contract verifies traceability and pass status without inventing global KD, trend or interview thresholds.
- Claim-level `standard|current_trusted` evidence rules for time-sensitive prices, features, numeric values, official status and links.
- A permission ledger where domain purchase, DNS, Git push, deployment, GSC, GA and ads are independent actions.
- Layered readback that never treats deployment, domain, telemetry, indexing or traffic as interchangeable.
- A no-data branch that permits diagnostics and scheduled hold, but blocks grow and retire.
- Old-domain residue scanning and a human-review gate covering every page in the current change batch before optimization or expansion relaunch.
- Two grow execution modes, `optimize-existing` and `expand-new`, with batch size determined by evidence strength, risk, dependencies and full-review capacity instead of fixed page counts.

## Evidence boundary

No trustworthy rating evidence was available from either catalog. Install counts and repository stars are popularity signals, not ratings, correctness proof or outcome evidence. The package does not claim that prior-art popularity validates this workflow. Its own claims are limited to mechanisms directly implemented and local evaluations actually run; provider, ranking, traffic, revenue and user-outcome evidence remain missing until a real authorized project records them.
