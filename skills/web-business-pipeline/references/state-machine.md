# State Machine

## States

| State | Proof added |
|---|---|
| `candidate_locked` | Human-approved, qualified, provider-disambiguated candidate is immutable |
| `planned` | Page matrix and page-level function contracts have no keyword overlap |
| `researched` | Every page has two sources and sensitive claims have current trusted evidence |
| `build_ready` | Every planned page maps to a content manifest entry |
| `local_verified` | Files and hashes match, required checks pass, every page in the current change batch is human-reviewed |
| `deploy_ready` | Local checks and rollback plan are complete; no external action is implied |
| `deployed` | Authorized deployment and actual HTTP readback are recorded |
| `telemetry_verified` | GSC and GA properties are separately read back |
| `observing` | Observation window is recorded; missing data has day-7/day-14 follow-up |
| `grow` | Valid GSC data and a human-approved growth decision exist |
| `hold` | A human-approved pause exists; missing data may remain under scheduled review |
| `retire` | Valid GSC data and a human-approved retirement decision exist |
| `templated` | Reusable infrastructure and product-specific exclusions are approved |

## Allowed transitions

```text
candidate_locked -> planned -> researched -> build_ready -> local_verified
                 -> deploy_ready -> deployed -> telemetry_verified -> observing
observing -> grow | hold | retire
hold -> observing | retire
grow -> observing | templated
```

There is no skip flag. To correct an earlier stage, edit the non-lock artifact, rerun `validate`, and record the reason in `decision-log.md`. Do not rewrite `candidate-lock.json`; create a new project if the primary candidate changes.

The state file stores a canonical SHA-256 of the lock and a second identity hash over `key + identities`. Two products with the same normalized name can therefore retain their business key while different provider identities remain distinguishable.

## Recovery

Run `status` after interruption. It reads the recorded stage and evaluates every legal next gate without changing files. An interrupted external action is not “deployed” until both its authorization ID and provider/HTTP readback are present. Revoke stale authorization before retrying with a narrower scope.
