# Official Source Registry

Mutable Cloudflare, Vercel, Wrangler, CLI, API, product-state, DNS, and registrar behavior must be refreshed before a real launch. The date below records the design review, not a permanent guarantee.

## Reviewed on 2026-08-14

| Source | Stable mechanism used | Runtime rule |
|---|---|---|
| [Cloudflare agent setup prompt](https://developers.cloudflare.com/agent-setup/prompt.md) | Official entrypoint for configuring agent access to Cloudflare | Fetch the current prompt when setup is requested or Cloudflare tooling is unavailable; never preserve OAuth callback material |
| [Pages Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/) | Build first, deploy the output directory, then read the deployment back | Recheck current Wrangler `--help`; do not assume Wrangler performs the project build |
| [Pages custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/) | Add the domain to Pages before relying on DNS; a DNS-only CNAME can produce 522 | Re-read before binding and distinguish apex full setup from an external-DNS subdomain |
| [Cloudflare full setup](https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/) | Cloudflare assigns two zone-specific nameservers; records must be reviewed; ordinary migration removes old DNSSEC before cutover | Never invent nameservers or reuse values from another zone |
| [Cloudflare DNSSEC](https://developers.cloudflare.com/dns/dnssec/) | Ordinary migration is old DS removal and expiry, NS cutover, Cloudflare signing, then new DS publication | Verify parent DS and validating-resolver `ad`; a dashboard toggle is not completion proof |
| [Cloudflare proxy status](https://developers.cloudflare.com/dns/proxy-status/) | A/AAAA/CNAME records may be proxied; third-party validation records must remain DNS-only | Keep Vercel hosting/verification records DNS-only during acceptance; proxying is a later, separately verified change |
| [Cloudflare DNS records](https://developers.cloudflare.com/dns/manage-dns-records/) | Exact record semantics and same-name conflicts matter | Read the exact record before create/update/delete; preserve unrelated mail and verification records |
| [Cloudflare zone status](https://developers.cloudflare.com/dns/zone-setups/reference/domain-status/) | Pending and Active have different operational meaning | Gate domain and DNSSEC completion on current provider state plus public readback |
| [Vercel add a domain](https://vercel.com/docs/domains/working-with-domains/add-a-domain) | Add the domain to the exact project; apex, subdomain, and ownership verification may require different A/CNAME/TXT values; wildcard domains require Vercel nameservers | Copy the values shown for that project at runtime; never hardcode a universal Vercel target |

The source pages showed these principles during the 2026-08-14 review. Numeric limits, pricing, UI paths, CLI flags, DNS targets, verification values, API shapes, and waiting times are intentionally not frozen into this Skill.

## Spaceship source boundary

Spaceship's official custom-nameserver support URL was discoverable during review:

- [How to change nameservers](https://www.spaceship.com/support/domain-management/how-to-change-nameservers/)

The article body was challenge-protected in that review, so this package does **not** claim a permanent click path. A real run must inspect the current authenticated UI or a newly accessible official article and record the observed controls. See [registrar adapters](registrar-adapters.md).

## Refresh triggers

Refresh the relevant source before acting when:

- Wrangler or Vercel CLI version, command output, or project linkage changed.
- A Pages project is Git-connected instead of Direct Upload.
- Vercel returns DNS or ownership-verification values that differ from an earlier run.
- The domain uses partial/CNAME setup, delegated subdomain, secondary DNS, wildcard routing, or multi-signer DNSSEC.
- Cloudflare, Vercel, or Spaceship renamed statuses, controls, or required DS fields.
- A provider response contradicts this runbook.

When sources conflict, prefer the current official page plus live read-only provider state. Record the conflict and do not silently choose the more convenient rule.
