# Artifact Schemas

Machine-readable JSON Schema files live in `schemas/`; editable starting points live in `templates/`.

## Cross-file keys

- `schema_version` is currently `2`.
- `candidate_key` must equal the immutable `candidate-lock.json.key`.
- `page_id`, `source_id` and `claim_id` are stable local identifiers and must be unique in their file.
- Page, source and claim references are validated across files.
- Content paths are project-relative, cannot contain `..`, and receive a SHA-256 after build.

## Completion is semantic

The CLI intentionally does not use file existence as a success signal. It checks required fields, exact candidate identity, page ownership, source coverage, claim trust/currentness, real files and hashes, human review, old-domain residue, local check evidence, active action authorization, HTTP/provider readback and valid data.

## Candidate handoff

Every upstream method emits the same v2 candidate shape:

- a stable `<namespace>:<slug>` key;
- one or more `identities[{provider,id}]` entries for entity disambiguation;
- `qualification.status: qualified`, the method and check time;
- one or more passed `qualification.checks`, each with a criterion, evidence references and object-valued raw observations;
- a structured `business_hypothesis` covering customer, problem, value, models, acquisition, primary value event, riskiest assumption and unknowns.

The upstream method owns its thresholds. The central contract does not require a particular KD, trend, interview count or acquisition channel. Qualification only admits a candidate to human confirmation; `init` still requires an exact `--confirm-key`, approver and rationale.

## Template handling

Files under `templates/` contain illustrative placeholders and are not evidence. `candidate-input.example.json` includes `example_only: true`; `init` refuses it until that flag is removed and the example values are replaced.
