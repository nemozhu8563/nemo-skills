# Evidence Policy

## Source coverage

Each planned page requires at least two distinct sources. Count URLs, not paraphrases. A copied competitor article and an AI summary of that article are one lineage, not two sources.

Reliability levels are:

- `official`: game developer, publisher, platform, or primary document;
- `trusted`: independently accountable specialist source with current evidence;
- `community`: useful discovery or corroboration, but not authoritative;
- `unverified`: lead only and never enough for sensitive claims.

## Claim-level guard

Every public claim in the evidence pack records its page, exact claim text, type and source IDs. Codes, numeric values and official links are sensitive claim types. They require:

- at least one `official` or `trusted` source;
- a non-empty `current_as_of` timestamp on that source;
- `status: verified` and `verified_at` on the claim.

Missing evidence remains missing. Do not infer a code, number, URL, date, feature or platform status from similar games or competitor copy.

## Competitor boundary

Competitor sites can inform intent coverage, information architecture and common interaction patterns. Do not copy their prose, page set wholesale, brand, illustrations, screenshots, CSS, proprietary data or pixel layout. Store sources and write original content from primary facts.

## Secret and private-data boundary

Project artifacts and content receive a conservative secret-pattern scan. Never record passwords, API keys, access tokens, private keys, Cookie/localStorage data or provider credentials. Private GSC/GA metrics may be recorded only for the user-authorized property, without authentication material.
