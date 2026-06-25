---
name: gsc-seo-opportunity
description: "Connect to Google Search Console, analyze owned-site query/page performance data, and produce SEO optimization opportunities. Use when the user wants Search Console analysis, CTR/title fixes, keyword expansion, content refresh priorities, decay diagnosis, cannibalization checks, or new page ideas from their own GSC data. Not for generic SEO advice without GSC access or scheduler setup."
---

# GSC SEO Opportunity

Turn Google Search Console performance data into a short, actionable SEO opportunity report for a site owner.

## Scope

Use this skill when the user wants to:

- analyze their own site's GSC performance data through the Search Console API
- analyze Search Console queries, pages, impressions, clicks, CTR, and average position
- find pages with high impressions but weak CTR
- find near-ranking queries that deserve page/title/content optimization
- compare recent GSC windows and diagnose growth or decay
- identify long-tail query clusters that may deserve new pages

Do not use this skill for:

- generic SEO strategy without GSC data
- competitor research that depends on Semrush, Ahrefs, Similarweb, or SERP scraping
- Google Analytics conversion analysis unless the user provides GA data separately
- submitting URLs for indexing or using the Google Indexing API
- setting up cron, launchd, GitHub Actions, or other scheduler infrastructure

## Runtime Boundary

GSC credentials, OAuth tokens, raw exports, and generated reports are runtime artifacts. Keep them outside the skill directory by default.

Default runtime root:

```text
~/Library/Caches/gsc-seo-opportunity/
```

Override with:

```bash
GSC_SEO_RUNTIME_ROOT=/path/to/runtime
```

Expected runtime layout:

```text
config/credentials.json
config/sites.json
data/token.json
reports/
logs/
```

## Workflow

1. Resolve runtime config.
   - If no config path is named, use `$GSC_SEO_RUNTIME_ROOT/config/sites.json`.
   - If OAuth is missing, run `scripts/gsc-seo-audit.mjs auth` and have the user complete browser consent.
   - Never paste OAuth client secrets or token values into chat.

2. Fetch GSC data.
   - Run `scripts/gsc-seo-audit.mjs audit --config <config>`.
   - Prefer a 28-day current window and 28-day comparison window with a 2-day end offset.
   - Use `query,page` dimensions as the default evidence surface.

3. Analyze opportunities with the model in [references/opportunity-model.md](references/opportunity-model.md).
   - CTR/title opportunities
   - striking-distance keyword/page opportunities
   - content refresh or decay opportunities
   - new page or long-tail expansion candidates
   - cannibalization checks

4. Write the report.
   - Keep the report action-first.
   - Include concrete query/page evidence, not generic SEO advice.
   - Give a 7-day execution plan with the smallest high-confidence changes first.
   - Mark guesses clearly when GSC cannot explain cause by itself.

## Command Reference

From this skill directory:

```bash
node scripts/gsc-seo-audit.mjs auth
node scripts/gsc-seo-audit.mjs sites
node scripts/gsc-seo-audit.mjs audit --config "$GSC_SEO_RUNTIME_ROOT/config/sites.json"
```

## Output Contract

A completed audit should report:

- report path
- site URL and date window
- number of GSC rows analyzed
- top 5 opportunities with query/page evidence
- generated JSON path for follow-up analysis
- any missing permissions, API limits, or data gaps

## Quality Gates

Before saying the audit is done:

- Confirm the report is based on GSC rows, not general SEO assumptions.
- Confirm no credential, token, or client secret was written into the skill directory.
- Confirm each recommendation cites at least one query or page.
- Confirm date windows are explicit.
- Confirm the report distinguishes data-backed findings from hypotheses.
