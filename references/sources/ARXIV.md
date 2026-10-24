# ARXIV — Protocol Card (preprint API)

> Status: behavior observed 2026-10-25. Re-probe on repeated failures.

## Access

- API: `https://export.arxiv.org/api/query` (Atom XML, no auth).
  HTTPS is mandatory — plain HTTP returns 0 bytes.
- Landing page: `https://arxiv.org/abs/<id>` (preprint page, the
  evidence URL for arXiv-sourced candidates).
- `search_query`: prefixes `all:` (full text) / `ti:` (title) /
  `abs:` (abstract), exact phrases in double quotes, `AND`/`OR`
  operators (`+` encodes a space). Exact-phrase `all:` queries are
  far more precise than loose words; `ti:`/`abs:` narrow further.
- Paging: `start` / `max_results`; `sortBy=relevance|submitted`,
  `sortOrder=descending`.
- Atom fields: `id`, `title`, `published`, `author/name`,
  `summary`, `arxiv:doi`, `arxiv:journal_ref`, `category@term`.

## Identity & auth

- No auth, no key. Browser UA used consistently for all HTTP.

## Rate limits & courtesy

- arXiv rule: >=3s between requests. Stay sequential,
  `max_results<=30` per call.

## Anti-bot & standard response

- arXiv API itself: none observed — reachable via plain HTTP,
  no JS/login/challenge, no browser needed.
- Publisher landings are separate: verifying enriched journal
  DOIs may hit JS-redirect pages or 403s at the publisher.
  That is L1 publisher business, not arXiv business: score it
  per skill §8 (challenge bodies fail L1).

## Parser notes

- Two Atom namespaces: `http://www.w3.org/2005/Atom` plus
  `http://arxiv.org/schemas/atom` (carries `arxiv:doi`,
  `arxiv:journal_ref`).
- `arxiv:doi` is filled only when the author registered it — empty
  for most preprints. `arxiv:journal_ref` is free text.
- Zero-hit queries in languages outside the corpus are data, not
  fetch failures: record and move on, do not re-probe.

## Traps

- `arxiv:doi` empty does not mean unpublished — enrich via
  Crossref/OpenAlex before deciding.
- Preprint DOIs (`10.48550/arXiv.*`) pass Layer 1 (they resolve to
  arXiv) but ALWAYS fail Layer 2 (Crossref 404 — they are DataCite
  DOIs). Reject as "no journal DOI", never as verified.
- L1/L2 always run on the journal DOI; the arXiv ID lives only
  as provenance in `reason`.
- False friends: common words with engineering senses (e.g.
  "control" matching control theory) dominate loose queries.
  Prefer exact phrases.
- Spelling variants (British/American) return different hit sets —
  probe both when the topic vocabulary has them.
- Mainstream journal literature in many topics has no arXiv copy
  at all: cross-check via OpenAlex `locations[]` for negative
  evidence rather than assuming coverage.

## Fallback chain

- DOI enrichment: Crossref `/works` (`query.bibliographic` /
  `query.title`) + OpenAlex `/works?search=` with minimal `select=`.
- Verification: `doi.org/<DOI>` (L1) + `api.crossref.org/works/<DOI>`
  title/year match (L2), per the skill contract.
- arXiv is a discovery source for preprints, never a metadata
  authority — journal facts always come from the backbone.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Discovery: `all:"<EXACT PHRASE>"`, then `abs:"<PHRASE>" AND
  abs:<TERM>` narrowing; `ti:` title checks for backbone candidates.
- Per candidate: fetch `abs` page, enrich DOI, run 2-layer check.
- Provenance pattern: discovered as `arXiv:<ID>`; journal DOI
  enriched via backbone; `reason` notes both IDs; `source_url`
  is the journal landing page, never the `abs` page.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
