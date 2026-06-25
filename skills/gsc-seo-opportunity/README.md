# GSC SEO Opportunity

It fetches your own site's Search Console performance data and produces an action-first optimization report:

- high-impression low-CTR pages
- striking-distance queries
- query/page decay versus the previous period
- long-tail new page candidates
- cannibalization checks
- a compact 7-day execution plan

## Setup

```bash
export GSC_SEO_RUNTIME_ROOT="$HOME/Library/Caches/gsc-seo-opportunity"
mkdir -p "$GSC_SEO_RUNTIME_ROOT/config"
cp config/sites.example.json "$GSC_SEO_RUNTIME_ROOT/config/sites.json"
```

Put your OAuth client file at:

```text
$GSC_SEO_RUNTIME_ROOT/config/credentials.json
```

Authorize:

```bash
node scripts/gsc-seo-audit.mjs auth
```

List Search Console properties:

```bash
node scripts/gsc-seo-audit.mjs sites
```

Run an audit:

```bash
node scripts/gsc-seo-audit.mjs audit --config "$GSC_SEO_RUNTIME_ROOT/config/sites.json"
```

## Notes

- OAuth token and reports stay under `$GSC_SEO_RUNTIME_ROOT`.
- The script uses the official Search Console Search Analytics and Sites APIs.
- Reports should be reviewed by an agent or site owner before changes are applied.
