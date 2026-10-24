# EUROPEPMC — Protocol Card (life-science literature API)

> Status: behavior observed 2026-10-24. Re-probe on repeated failures.

## Access

- REST API (public, no auth):
  `https://www.ebi.ac.uk/europepmc/webservices/rest/search`
- Request:
  `GET /search?query=<Q>&format=json&pageSize=<N>&resultType=core`
  - `<Q>` must be URL-encoded. Syntax: `DOI:"<doi>"`,
    `TITLE_ABS:"<phrase>"`, `AND`/`OR`, quotes for phrases.
  - `pageSize` max 1000; paginate via `page=N` + `cursorMark`
    beyond 25 results.
  - `resultType=core` returns `doi`, `title`, `abstractText`,
    `pubYear`, `journalTitle`, `authorString`, `pmid`, `pmcid`,
    `fullTextUrlList`, `source`.
- Search UI: `https://europepmc.org`.
- OA articles: `https://europepmc.org/articles/PMC<pmcid>` (a
  legitimate OA mirror, usable as evidence URL).

## Identity & auth

- No auth, no key, no email required. Browser-like UA.

## Rate limits & courtesy

- Sequential, ~1s delay, small `pageSize` (25 is plenty for
  narrow topics). No burst. Max 1 retry on an identically
  failing path, then switch angles or mark unresolved.

## Anti-bot & standard response

- None on the REST API — no captcha, no challenge.
- Publisher landing pages are the trap: observed blockers
  return HTTP 403 to datacenter curl for VALID DOIs while the
  `doi.org/<DOI>` 302 redirect itself is correct. Record as
  `resolver_status: 403-anti-bot (redirect correct)`, reject
  strictly, and flag `needs_richer_check` for browser
  promotion. Do not evade with header retries (full Accept +
  Accept-Language headers were tried — still 403).

## Parser notes

- `abstractText` sometimes carries HTML tags — strip before use.
- `doi` can be null (pre-DOI records) — DOI-less rows are
  rejected, never counted.
- `DOI:"<doi>"` returns exactly 1 record — ideal for detail
  pulls on shortlisted candidates.
- `fullTextUrlList`: split `availabilityCode: OA` (Europe_PMC /
  Unpaywall mirrors) from `S` (ticketed DOI links).

## Traps

- Corpus is life-science/biomedical: non-biomed topic terms are
  thin or absent. Over-gather via domain-adjacent variants
  (e.g. hospital/healthcare contexts), take top-N by relevance,
  then screen titles + abstracts manually to the inclusion
  criteria. Never chase full recall on a 700+ broad query.
- One intermittent empty Crossref response observed (transient —
  a single retry succeeded). Retry 1x before calling a DOI dead.
- Europe PMC records link into PubMed/MEDLINE and PMC — the
  same DOI may surface from several ecosystem queries.
  Lowercase-DOI dedup still applies.

## Fallback chain

- Browser is NOT a primary path — the REST API already returns
  structured metadata + abstracts. Browser only promotes
  `needs_richer_check` rows (anti-bot landings).
- Metadata authority stays Crossref; the resolver stays doi.org.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Narrow: `query="<PHRASE>" AND "<PHRASE>"&format=json
  &pageSize=25&resultType=core` (URL-encoded).
- Bare terms also AND: `query=<T1> AND <T2> AND <T3>` needs
  no field prefix (Lucene-style).
- Over-gather: `TITLE_ABS:"<PHRASE>" AND <CONTEXT>`; screen
  top-N, then 2-layer curl per DOI shortlist.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
