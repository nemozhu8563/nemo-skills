# GSC Opportunity Model

This model turns Search Console performance rows into practical SEO work. It follows the article's core idea: use GSC data to ask an agent where the site can improve, instead of guessing from generic SEO advice.

## Required Evidence

Default dimensions:

- `query`
- `page`

Default metrics:

- `clicks`
- `impressions`
- `ctr`
- `position`

Default comparison:

- current 28 days
- previous 28 days
- end offset of 2 days to avoid freshness noise

## Opportunity Types

### 1. CTR / Title Opportunity

Signal:

- high impressions
- average position usually 1-10
- CTR meaningfully below the expected range for that position

Likely action:

- rewrite title to match the query intent more directly
- make the meta description more specific
- add date, tool type, format, comparison, or benefit when it matches intent
- improve snippet-supporting headings on the page

Avoid:

- clickbait
- changing titles for pages with very low impressions
- assuming title is the only cause; SERP features and intent mismatch can also depress CTR

### 2. Striking-Distance Opportunity

Signal:

- position around 8-20
- enough impressions to matter
- query maps to an existing relevant page

Likely action:

- add a dedicated section answering the query
- strengthen internal links to the ranking page
- improve heading coverage and examples
- add FAQ or comparison blocks only when the query calls for them

### 3. Content Refresh / Decay Opportunity

Signal:

- clicks or impressions dropped versus the previous window
- position worsened, CTR dropped, or impressions shrank

Likely action:

- compare page content against current search intent
- update stale screenshots, pricing, dates, examples, or product names
- check whether a competitor or SERP feature displaced the page
- inspect the URL if indexing status is suspicious

Do not overclaim causality from GSC alone. Label cause hypotheses.

### 4. New Page / Long-Tail Opportunity

Signal:

- query has meaningful impressions
- existing page ranks weakly or only tangentially fits the query
- query is specific enough to support a separate page or tool surface

Likely action:

- create a focused page for the query cluster
- build a tool, template, calculator, comparison, or structured table if that matches intent
- link from the broader existing page

Avoid:

- creating one page per tiny query
- making blog posts when the query wants a tool, table, template, or product page

### 5. Cannibalization Check

Signal:

- one query maps to multiple pages with meaningful impressions
- no single page clearly wins

Likely action:

- choose the canonical target page
- consolidate overlapping content
- strengthen internal links toward the target page
- de-optimize or redirect only after manual review

## Report Shape

Reports should be action-first:

1. What to do this week.
2. Why the data says it matters.
3. Exact query/page evidence.
4. Expected effect.
5. Known uncertainty.

Keep tables compact. Prefer 5-12 high-confidence opportunities over a large noisy dump.
