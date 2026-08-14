# Evidence And Rollback Contract

## Five evidence channels

Never flatten these into one status:

| Channel | Proves | Does not prove |
|---|---|---|
| Hosting provider | The selected Pages or Vercel deployment and domain binding reached the recorded state | Public DNS propagation, TLS, or the intended page content |
| Cloudflare and public DNS | The zone, parent NS/DS, and recursive answers match the selected hosting route | Hosting health, TLS, or application behavior |
| Public HTTPS | Certificate validation, final URL, response, and representative content work on the formal domain | Registrar state or DNSSEC by itself |
| Local cache | What this machine or browser currently observes | Global propagation |
| Project file | The exact `nemo-domain-launch` block exists in project-root `AGENTS.md` | That deployment, DNS, or HTTPS works |

Every observation records `observed_at`, target, method, result, and an evidence pointer. Planned commands and expected values are not observations.

## Claim rules

`domain_ready: true` requires all of the following:

- `formal_domain_before.status` was proved `absent` or `provider_default_only` before mutation.
- Exactly one of `pages_deploy` or `vercel_deploy` completed with provider readback; the inactive route has a coherent `not_required` authorization/execution/readback triad.
- The selected provider default URL passed HTTPS readback.
- Cloudflare is the authoritative DNS provider and public NS answers match the exact nameservers assigned to this zone when cutover is in scope.
- The custom domain, hosting DNS, certificate, formal HTTPS root, and at least one representative route passed.
- `static_pages` checks canonical, `robots.txt`, and `sitemap.xml` against the formal origin.
- `saas_vercel` may mark absent canonical/SEO files `not_required`; an existing value that points at the wrong origin still fails.
- No evidence required by the selected route remains `pending`, `failed`, or `missing_evidence`.

`launch_complete: true` additionally requires:

- `domain_ready: true` already passed validator checks.
- `agents_md_writeback` was authorized, executed, and read back at exactly `project_dir/AGENTS.md`.
- The file contains one exact `nemo-domain-launch` managed block for the verified origin and selected mode.

`dnssec_complete: true` additionally requires:

- Cloudflare signing is active.
- The new parent DS is observed publicly.
- At least two named validating recursive resolvers return a successful DNSSEC answer with the `ad` flag.

Provider-backed launch evidence must come from the actual target run. A recorded fixture, old deployment, another domain, or the existence of an `AGENTS.md` block cannot satisfy it.

## Before-state snapshots

Before any provider or file mutation, retain the minimum state needed for a precise rollback:

```json
{
  "hosting": {
    "mode": "static_pages",
    "project": "example-project",
    "last_known_good_deployment": "provider-deployment-id"
  },
  "dns_record": {
    "provider": "registrar-or-cloudflare",
    "record_id": "provider-record-id",
    "type": "A",
    "name": "example.com",
    "content": "192.0.2.10",
    "ttl": 300,
    "proxied": false
  },
  "nameservers": ["old-ns-1.example", "old-ns-2.example"],
  "parent_ds": [],
  "agents_md": {
    "file_existed": true,
    "managed_block_present": false
  },
  "observed_at": "RFC3339 timestamp"
}
```

Do not copy private `AGENTS.md` content into the report. Do not include token-bearing headers or raw browser/network captures that contain credentials.

## Rollback matrix

| Last completed stage | Safe rollback boundary |
|---|---|
| Local preflight | No provider or project-file state changed |
| Pages deployed only | Redeploy the last known-good Pages artifact or leave the isolated `pages.dev` deployment |
| Vercel deployed only | Promote/redeploy the recorded last known-good production deployment; do not change DNS to hide a failed build |
| Zone staged, NS unchanged | Restore exact changed Cloudflare records from snapshot; old public DNS remains authoritative |
| Old DS removed, NS unchanged | Restore old DS only if the old authoritative provider is still signing correctly |
| NS changed, no new DS | Restore old NS only if its zone is still correct; verify public DNS before reintroducing old DS |
| New Cloudflare DS published | Remove the new DS first and keep Cloudflare signing enabled until the parent DS TTL expires; then change NS |
| Domain and certificate active | Prefer hosting deployment rollback over DNS rollback when DNS is healthy |
| `AGENTS.md` block written | Remove only the exact managed block if the launch itself is rolled back; preserve every other byte of the file |

Rollback completion always requires fresh hosting-provider, Cloudflare/public-DNS, HTTPS, and—when changed—project-file readback.

## Secret and privacy boundary

Never store:

- API token, OAuth code, or callback URL
- Cookie, session identifier, password, verification/recovery code, or private key
- Browser profile or storage dump
- Authorization header or raw request containing credentials
- Secret environment-variable values

Account ID, zone ID, project name, deployment ID, and DNS record ID are not authentication secrets, but they are operational metadata. Keep them in local artifacts, minimize disclosure, and do not use them as public examples.
