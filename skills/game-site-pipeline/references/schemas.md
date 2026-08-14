# Artifact Schemas

Machine-readable JSON Schema files live in `schemas/`; editable starting points live in `templates/`.

## Cross-file keys

- `schema_version` is currently `1`.
- `candidate_key` must equal the immutable `candidate-lock.json.key`.
- `page_id`, `source_id` and `claim_id` are stable local identifiers and must be unique in their file.
- Page, source and claim references are validated across files.
- Content paths are project-relative, cannot contain `..`, and receive a SHA-256 after build.

## Completion is semantic

The CLI intentionally does not use file existence as a success signal. It checks required fields, exact candidate identity, page ownership, source coverage, claim trust/currentness, real files and hashes, human review, old-domain residue, local check evidence, active action authorization, HTTP/provider readback and valid data.

## Candidate handoff

The radar handoff keeps the upstream `game:<slug>` key and must carry at least one platform ID. Required qualification evidence is:

- Google Trends status `rising`;
- measured Semrush Volume greater than zero and its database;
- Semrush KD below 30;
- at least 10 real long-tail terms;
- SERP status `open` or `mixed`;
- at least two reliable sources.

This only admits a candidate to human confirmation. `init` still requires an exact `--confirm-key`, approver and rationale.

## Template handling

Files under `templates/` contain illustrative placeholders and are not evidence. `candidate-input.example.json` includes `example_only: true`; `init` refuses it until that flag is removed and the example values are replaced.
