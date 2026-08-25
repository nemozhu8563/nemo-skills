# Build Contract

The page matrix is also the page-level product contract. Before HTML, UI or code, every page defines:

- one user goal;
- one primary keyword and one normalized intent key;
- fields the page may display;
- actions the user may take;
- states the page may expose;
- explicit non-goals.

Anything not in that contract stays out of the first implementation. Marketing panels, operational notes, sample cards or extra navigation are not added merely to make a page look complete.

The content manifest maps every page contract to a project-relative file, sources and claims. At `build_ready`, entries may be `planned` or `draft`. At `local_verified`, every file must exist, its SHA-256 must match, and its status must be `reviewed` or `published`.

`status: reviewed` marks a page in the current change batch; `status: published` is reserved for an unchanged page already represented by the deployed baseline. Every page in the current change batch requires human review before release, regardless of batch size. Human review records reviewer and timestamp; model self-review does not count. If the whole batch cannot be reviewed, reduce the batch instead of sampling a fixed number of pages.
