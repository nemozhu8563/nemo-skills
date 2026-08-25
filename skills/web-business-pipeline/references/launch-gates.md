# Launch Gates

## Separate facts

Report these independently:

1. local build/test/content checks;
2. Git revision and push, if used;
3. deployment provider state;
4. public HTTP readback;
5. domain purchase/ownership;
6. DNS resolution;
7. GSC property readback;
8. GA property readback;
9. indexing evidence;
10. actual traffic/query data.

One item never proves another. A provider dashboard saying “ready” does not prove the public domain, and a reachable URL does not prove GSC or GA data.

## Authorization boundary

`domain_purchase`, `dns_change`, `git_push`, `deployment`, `gsc_setup`, `ga_setup`, and `advertising_application` are separate actions. Record authorization only from a current explicit user instruction for that exact action. Put its `authorization_id` beside the resulting evidence. Authorization does not count as execution, and execution without readback does not count as verification.

## Local checks and rollback

The launch report covers build, lint, tests, links, assets, visual acceptance and content review. `not_applicable` requires a reason. It also records canonical origin, forbidden old origins and a concrete rollback procedure.

The bundled CLI never performs external actions. Use another scoped tool only after authorization. If an external action partly fails, leave the current stage unchanged, record the evidence and revoke or narrow the permission before retrying.

Do not use Google Indexing API for ordinary content or utility pages. Use sitemap, internal linking, crawlability and normal GSC inspection.
