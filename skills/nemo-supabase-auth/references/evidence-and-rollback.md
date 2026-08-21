# Evidence And Rollback Contract

## Evidence channels

Keep these channels independent:

| Channel | Proves | Does not prove |
|---|---|---|
| Application source | Login initiation, callback exchange, safe redirect, and protected-route logic exist in the inspected revision | Deployed revision, provider configuration, or a real session |
| Google provider | Exact project/client/audience/scopes and registered callback configuration | Supabase settings, app callback behavior, or a logged-in user |
| Supabase provider | Google provider, Site URL, and Redirect URLs are saved in the exact project | Google client correctness or real browser success |
| Browser callback | One authorized interactive flow returned through the expected route chain | Server-trusted identity unless checked separately |
| Trusted application signal | The deployed server recognized an authenticated request and protected access worked | Provider configuration for every environment or every user |

An observation records time, target alias, method, redacted result, and evidence pointer. A planned command, fixture, HTTP 200, masked provider field, screenshot, or `Enabled` label is not equivalent to the stronger channel.

## Action ledger

Every action has five fields:

```json
{
  "authorization": {"status": "authorized", "evidence": "current user instruction"},
  "before": {"state": "redacted summary", "observed_at": "RFC3339 timestamp"},
  "execution": {"status": "succeeded", "evidence": "local evidence pointer"},
  "readback": {"status": "verified", "evidence": "provider or file readback pointer"},
  "rollback": "One exact recovery action without credential values."
}
```

Allowed terminal combinations:

- required successful action: `authorized` / `succeeded` / `verified`;
- not applicable action: `not_required` / `not_required` / `not_required` with a reason;
- incomplete action: keep the exact stage as `pending`, `failed`, or `missing_evidence`; do not promote a claim.

Authentication to a provider proves identity/access, not authorization for every action.

## Minimum before snapshots

### Application code

- source revision and dirty-state summary;
- exact files expected to change;
- existing test command and callback behavior;
- rollback as the exact reviewed diff, without overwriting unrelated dirty files.

### Google Cloud and Auth

- owning account/organization alias;
- project existence and selected project alias;
- current audience and publication-state enum;
- requested scope names;
- existing Web clients and their non-secret origin/redirect configuration;
- no credential value and no personal test-user identity.

### Supabase

- organization/project alias;
- Google provider enabled enum and secret-present boolean only;
- current Site URL and Redirect URLs;
- no service-role key, JWT, user identity, or session data.

### Real login

- whether the selected test identity already has an account/grant, recorded only as `known_existing`, `known_absent`, or `unknown`;
- expected side effects: consent grant, user creation/reuse, and session creation;
- logout action; user deletion and grant revocation remain separately authorized.

## Claim rules

`configuration_ready: true` requires:

- source gate complete and relevant code preflight passed;
- URL matrix structurally valid and both callback layers separated;
- `application_code` either verified or coherently `not_required` because existing code passed;
- Google project/Auth/client actions verified or coherently reused with live readback;
- Supabase provider and URL configuration verified;
- no unresolved required configuration evidence.

`end_to_end_verified: true` additionally requires:

- `real_login_test` authorized, executed, and read back;
- browser callback chain completed;
- trusted server-side user signal passed without recording identity;
- protected route/API accepted the authenticated request;
- logout completed and the protected route then rejected or redirected;
- `missing_evidence` is empty.

Provider-backed output evidence must come from the actual scoped run. Recorded fixtures prove only the package contract.

## Rollback matrix

| Last completed stage | Safe rollback boundary |
|---|---|
| Read-only audit | No state changed |
| Application code only | Revert only the reviewed auth diff; preserve unrelated dirty files |
| New Google project only | Leave isolated or request explicit destructive deletion; do not auto-delete |
| Google Auth configuration | Restore the captured audience/publication/scope state when the provider permits; publication reversal may require a new decision |
| OAuth client edited | Restore exact origins/redirects from snapshot; do not rely on a credential backup |
| New OAuth client created | Disable/delete only with separate authorization after confirming no consumers |
| Supabase provider edited | Restore enabled/client-ID state; user must re-enter any previous credential value because reports never store it |
| Supabase URLs edited | Restore exact previous Site URL and Redirect URLs |
| Real login completed | Sign out; keep user/grant unless separately authorized to delete or revoke |

Rollback completion requires fresh readback from the affected source plus the relevant code or browser check. A rollback plan alone is not proof of recovery.

## Redaction rules

Allowed report data:

- project/environment aliases, source revision, URL configuration, action status, booleans, scope names, timestamps, and local evidence pointers;
- counts such as `existing_clients: 1` or `test_users_configured: true` when they do not reveal identities.

Forbidden report data:

- credential values, authorization codes, tokens, JWTs, authorization headers, Cookies, session identifiers;
- runtime callback URLs with query/fragment;
- email addresses, user IDs, Google subject identifiers, account chooser content;
- browser storage/profile dumps, raw network archives, or screenshots with identity data.

The bundled validator rejects common forbidden keys and value patterns, but it is a backstop rather than permission to collect sensitive data.
