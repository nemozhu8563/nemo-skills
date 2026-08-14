# First Production Domain Runbook

This runbook contains decision rules and command shapes, not immutable provider truth. Before a real mutation, compare commands and returned values with current official documentation and locally installed CLI help.

## 0. Prove eligibility and select one route

Start at the exact project root. Read project-root `AGENTS.md`, README, hosting configuration, origin/site configuration, environment-variable names, provider project metadata, and public DNS.

Classify `formal_domain_before.status`:

- `absent`: no formal production domain is configured.
- `provider_default_only`: only a provider URL such as `pages.dev` or `vercel.app` exists.
- `present`: a formal production domain already exists; stop and route maintenance/deployment elsewhere.
- `unresolved`: evidence conflicts or is incomplete; stay read-only.

For an eligible project, select exactly one mode from runtime facts:

| Mode | Selection rule | Active hosting action |
|---|---|---|
| `static_pages` | A project-native build creates a static directory that Cloudflare Pages can serve | `pages_deploy` |
| `saas_vercel` | The application relies on Vercel runtime behavior such as Next.js SSR, Functions, or SaaS server features | `vercel_deploy` |

Do not run both. Mark authorization, execution, and readback of the inactive hosting action `not_required` with the selected mode as evidence.

## 1. Lock scope and local evidence

Resolve without guessing:

- absolute project directory, existing build/check/test commands, source revision, and dirty state
- final production HTTPS origin and at least one representative path
- selected hosting account/team and project
- static output directory and Pages production branch for `static_pages`
- exact Vercel production target/revision for `saas_vercel`
- Spaceship domain, apex/subdomain, Cloudflare zone, current NS/DS, and exact authorized mutations
- absolute final writeback target `project_dir/AGENTS.md`

Run the project's own checks before provider mutation. Never replace project-native commands with a guessed build.

For `static_pages`, build with the final production origin and run:

```bash
python3 "$SKILL_DIR/scripts/preflight.py" "$PROJECT_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --origin "$PRODUCTION_ORIGIN" \
  --representative-path /representative/ \
  --output "$ARTIFACT_DIR/preflight.json"
```

The preflight is read-only except for its requested JSON output. It checks files against the formal origin without requiring that origin to resolve before first binding. A failed preflight blocks Pages deployment; do not edit generated output by hand just to pass it.

For `saas_vercel`, use the project's existing Vercel configuration and build path. Confirm required environment-variable **names** exist in the target environment without reading or recording secret values. Exercise a representative application path locally when the project provides a safe test.

## 2. Read provider identity and existing resources

Cloudflare interactive OAuth examples:

```bash
npx wrangler whoami
npx wrangler pages project list --json
```

Headless Cloudflare access may reference `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` by name only. Never print, echo, paste, serialize, or persist their values.

For Vercel, inspect current CLI help and read identity/project linkage before `saas_vercel` mutation:

```bash
npx vercel --help
npx vercel whoami
```

Confirm the selected account/team/project from returned resource data or the authenticated dashboard. Successful login to the wrong account is not authority for the target.

## 3. Execute only the selected hosting route

### `static_pages`

Inspect the installed Wrangler command first:

```bash
npx wrangler pages project create --help
npx wrangler pages deploy --help
```

Create the exact project only when readback proves it is absent, then deploy the already verified directory:

```bash
npx wrangler pages project create "$PAGES_PROJECT" --production-branch "$PRODUCTION_BRANCH"
npx wrangler pages deploy "$OUTPUT_DIR" \
  --project-name "$PAGES_PROJECT" \
  --branch "$PRODUCTION_BRANCH"
```

Record the deployment ID, environment, URL, source revision, dirty state, and terminal status. Fetch the resulting `pages.dev` URL over HTTPS; upload success alone does not prove content.

### `saas_vercel`

Use the project's established Vercel deployment workflow and current CLI syntax. Do not introduce a second build path or silently relink the directory to a different team/project. Record the exact project/team, deployment ID/URL, source revision, terminal `READY` state, and HTTPS readback of the `vercel.app` URL.

If a healthy production deployment already corresponds to the intended revision, it may be reused as an evidenced no-op. A stale, preview-only, protected, or wrong-project deployment cannot be promoted by assumption.

## 4. Stage Cloudflare authoritative DNS

For either mode:

1. Create or locate the exact Cloudflare zone in the authorized account.
2. Record the two nameservers assigned to that zone. Never use example or previously seen values.
3. Snapshot imported Cloudflare records, Spaceship-hosted records, public NS, and parent DS.
4. Preserve MX, TXT, CAA, DKIM, DMARC, SPF, ownership-verification, and unrelated subdomain records by default.
5. Keep Pages/Vercel binding, DNS record mutation, nameserver cutover, and DNSSEC as separate actions and evidence.

## 5. Bind the custom domain by mode

### `static_pages`

1. Add the exact domain to the Pages project through the current provider-native API, CLI, or dashboard.
2. Read Pages custom-domain status and resulting Cloudflare DNS.
3. If Pages created the required record, do not add a duplicate.
4. If the record is absent, derive it from current Pages instructions and live provider output.

Creating only a CNAME without the Pages binding can return 522 and does not satisfy this route.

### `saas_vercel`

1. Add the domain to the exact Vercel project.
2. Read the Domain Settings response for this domain and project.
3. Copy the returned apex A, subdomain CNAME, and any ownership TXT/verification values exactly into Cloudflare.
4. Keep Vercel hosting and validation records DNS-only during acceptance.
5. Read both Vercel domain/certificate state and Cloudflare records back.

Do not hardcode `76.76.21.21`, `cname.vercel-dns.com`, or any other remembered target. Vercel may return project-specific values. Wildcard domains require Vercel nameservers and therefore conflict with this Skill's Cloudflare-authoritative contract; stop and route them elsewhere.

## 6. Resolve DNS conflicts safely

For each blocking record, record:

- provider record ID
- type, exact FQDN, content, proxy state, and TTL
- evidence that it is parking/default infrastructure rather than user content
- why it blocks the selected Pages/Vercel target
- timestamp and complete rollback payload

Automatic cleanup is allowed only when all of these are true:

1. The current instruction authorizes DNS cleanup for this exact domain.
2. The record matches by ID, type, name, and content.
3. Read-only evidence classifies it as parking/default infrastructure.
4. It directly blocks the selected hosting record.
5. The record can be recreated from the saved snapshot.

Otherwise stop at the permission gate. Never clear a zone or delete unrelated mail/verification records to make the hosting record fit.

## 7. Ordinary nameserver and DNSSEC migration

When an old DS exists and no separately validated multi-signer path is in use:

1. Remove or disable the old DNSSEC/DS state at Spaceship.
2. Query the parent DS until it is absent after its TTL window.
3. Replace Spaceship nameservers with the exact two nameservers assigned to this Cloudflare zone.
4. Verify public NS through at least two resolvers and wait for Cloudflare zone `Active`.
5. Verify selected hosting DNS, custom-domain state, and certificate/HTTPS.
6. If DNSSEC is authorized, enable signing in Cloudflare and read the generated DS fields.
7. Publish those exact DS fields at Spaceship.
8. Verify parent DS and successful DNSSEC `ad` through at least two validating resolvers.

If DNSSEC is out of scope, its action must be a coherent `not_required` triad and `dnssec_complete` stays false. Never compress DS absence, NS cutover, zone activation, signing, and new DS publication into one “DNS done” status.

## 8. Prove the public domain

For `static_pages`:

```bash
python3 "$SKILL_DIR/scripts/verify_public.py" "$DOMAIN" \
  --expected-origin "$PRODUCTION_ORIGIN" \
  --representative-path /representative/ \
  --require-cloudflare-ns \
  --require-dnssec \
  --output "$ARTIFACT_DIR/public-verification.json"
```

For `saas_vercel`, omit `--require-dnssec` when it was not authorized. If the application genuinely has no canonical, `robots.txt`, or sitemap, add the narrow optional flags:

```bash
--allow-missing-canonical --allow-missing-seo-files
```

Those flags allow absence, not wrong values. Existing canonical/SEO content that points at a provider default or unrelated origin still fails.

Manual spot checks remain useful:

```bash
dig @1.1.1.1 NS "$DOMAIN" +noall +answer
dig @8.8.8.8 DS "$DOMAIN" +dnssec
curl --fail --silent --show-error --location --head "$PRODUCTION_ORIGIN/"
```

Also read an actual representative response body. TLS must validate normally; `curl -k` is diagnostic evidence of failure, never proof of success.

Populate the launch report and prove the first claim:

```bash
python3 "$SKILL_DIR/scripts/validate_launch_report.py" \
  "$ARTIFACT_DIR/launch-report.json" --require-domain-ready
```

## 9. Write the verified domain to `AGENTS.md`

Only after `domain_ready` passes:

```bash
python3 "$SKILL_DIR/scripts/update_agents_domain.py" \
  "$ARTIFACT_DIR/launch-report.json"
python3 "$SKILL_DIR/scripts/validate_launch_report.py" \
  "$ARTIFACT_DIR/launch-report.json" --require-launch-complete
```

The writer targets only the resolved project-root `AGENTS.md`, preserves existing content, creates the file when absent, and manages one marker block. The same domain/mode is a no-op. A different block, malformed/duplicate marker, relative target, or symlink fails closed.

## 10. Final report

Start from `templates/launch-report.template.json` and keep sensitive runtime artifacts out of version control. Report selected and inactive routes separately, distinguish `domain_ready` from `launch_complete`, and leave provider-backed or human-review claims as `missing evidence` unless the actual evidence exists.

The validators enforce claim consistency and obvious secret leakage. They do not call Cloudflare, Vercel, Spaceship, public DNS, or the site, so they cannot replace provider/public readback.
