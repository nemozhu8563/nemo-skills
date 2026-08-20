# Official Sources

Checked on 2026-08-20. Google tag/support pages were read through a host-visible Chrome CDP session because direct shell access timed out; Google API method contracts were additionally checked against the official `googleapis/google-api-go-client` Discovery documents. Microsoft pages were read from the official Microsoft Learn Markdown representation. Mutable provider behavior must be rechecked before future Skill changes.

## Google Analytics 4

- [Set up the Google tag with gtag.js](https://developers.google.com/tag-platform/gtagjs)
  - The official snippet loads `googletagmanager.com/gtag/js?id=TAG_ID`, initializes `gtag`, then calls `gtag('config', 'TAG_ID')`.
  - The page recommends Tag Assistant and browser Network requests for tag verification.
  - A Google tag ID is embedded in site code; it is an identifier, not an authentication secret.
- [Set up consent mode on websites](https://developers.google.com/tag-platform/security/guides/consent)
  - Consent Mode distinguishes `analytics_storage`, `ad_storage`, `ad_user_data`, and `ad_personalization`.
  - Default consent state should be set before measurement commands and updated when user choice changes.
  - The selected granted/denied policy is site/legal-context dependent; Google does not prescribe this Skill's production-only gate.
- [[GA4] Realtime report](https://support.google.com/analytics/answer/9271392?hl=en)
  - Realtime shows activity from the last 5 and 30 minutes.
  - Google calls it best-effort and notes possible delay/disruption without a formal SLO.
- [Monitor events in DebugView](https://support.google.com/analytics/answer/7201382?hl=en)
  - DebugView shows events collected from a debug-enabled device and requires debug mode.
  - It is suited to tag troubleshooting; it does not prove ordinary production traffic coverage.
- [Analytics Admin API v1beta REST](https://developers.google.com/analytics/devguides/config/admin/v1/rest)
  - The adapter uses account summaries, property get/list/create and Web data stream get/list/create only.
  - Official Discovery revision checked for the implementation contract: `20260802`.
- [Analytics Admin API v1beta Discovery](https://github.com/googleapis/google-api-go-client/blob/main/analyticsadmin/v1beta/analyticsadmin-api.json)
  - Locks the tested method paths, scopes, request fields, and revision for this adapter version.
- [Analytics Data API v1beta REST](https://developers.google.com/analytics/devguides/reporting/data/v1/rest)
  - The adapter uses `properties.runRealtimeReport` with a fixed telemetry-verification metric allowlist.
  - Realtime API success is not DebugView evidence. Official Discovery revision checked: `20241117`.
- [Analytics Data API v1beta Discovery](https://github.com/googleapis/google-api-go-client/blob/main/analyticsdata/v1beta/analyticsdata-api.json)
  - Locks the tested Realtime method path, scope, request fields, and revision for this adapter version.

## Microsoft Clarity

- [How to setup Clarity manually](https://learn.microsoft.com/en-us/clarity/setup-and-installation/clarity-setup)
  - Each site/project has a unique tracking code copied into the site's `<head>`.
  - Microsoft documents two verification paths: project Recordings/Dashboard and Network `POST https://www.clarity.ms/collect`.
  - The page says data can be viewed as soon as the code is added; current provider readback is still required before this Skill claims recording evidence.
- [Consent Mode](https://learn.microsoft.com/en-us/clarity/setup-and-installation/consent-mode)
  - Clarity can wait for a valid consent signal before setting cookies and documents how to inspect consent status.
  - The site owner remains responsible for communicating consent changes.
- [Clarity Cookie Consent API - ConsentV2](https://learn.microsoft.com/en-us/clarity/setup-and-installation/clarity-consent-api-v2)
  - `consentv2` is the current recommended API.
  - Required fields are `ad_Storage` and `analytics_Storage` with `granted` or `denied` values.
  - Denied consent uses no-consent mode without first-party or third-party Clarity cookies; it is not equivalent to no data collection.

## Google Search Console

- [Add a website or platform property](https://support.google.com/webmasters/answer/34592?hl=en)
  - Domain property covers subdomains and protocols and uses DNS verification.
  - URL-prefix property covers only the exact protocol/prefix.
  - An unfinished property can be saved and resumed.
- [Verify your site ownership](https://support.google.com/webmasters/answer/9008080?hl=en)
  - A verified owner has the highest permission level.
  - Multiple owners/methods can coexist; another owner's token must not be overwritten.
  - Search Console periodically checks verification tokens; removing one can cause permissions to expire.
- [What is a sitemap?](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)
  - A sitemap helps search engines discover and crawl URLs more efficiently.
  - Google explicitly states that a sitemap does not guarantee every item will be crawled or indexed.
- [Build and submit a sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
  - Use fully qualified canonical URLs and follow current file-size/URL-count limits.
- [Search Console API: Sitemaps submit](https://developers.google.com/webmaster-tools/v1/sitemaps/submit)
  - Submission needs the exact property identifier and absolute sitemap URL; meaningful completion still needs list/get readback.
- [Search Console API: Search Analytics query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)
  - Uses `POST /webmasters/v3/sites/{siteUrl}/searchAnalytics/query` with the `webmasters.readonly` scope for reads; `startDate` and `endDate` are required.
  - The controlled adapter allows official dimensions, `FINAL|ALL`, search and aggregation enums, `rowLimit=1..25000`, and `startRow>=0`; rows contain dimension keys, clicks, impressions, CTR, and average position.
  - Google returns top rows rather than a guaranteed complete export; offset pagination has no total count or stable snapshot guarantee.
- [Search Console API Discovery](https://github.com/googleapis/google-api-go-client/blob/main/searchconsole/v1/searchconsole-api.json)
  - The adapter fixes sites/sitemaps/Search Analytics to `webmasters/v3` and URL Inspection to `v1`; it does not expose Google Indexing API.
  - Official Discovery revision checked for the implementation contract: `20260819`.

## Google Cloud authentication

- [Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc)
- [`gcloud auth application-default login`](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login)
- [`gcloud auth application-default print-access-token`](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/print-access-token)
- [`gcloud services enable`](https://cloud.google.com/sdk/gcloud/reference/services/enable)
  - `gcloud` is used for explicit service bootstrap and short-lived ADC tokens, not as the GSC/GA4 business client.

## Provider-neutral DNS

- [Cloudflare: Manage DNS records](https://developers.cloudflare.com/dns/manage-dns-records/)
  - DNS fields and provider name semantics must be read back after writes.

Cloudflare is an example, not a dependency. For Route 53, Vercel DNS, a registrar, or another provider, use its current official record semantics plus provider and two-public-resolver readback.
