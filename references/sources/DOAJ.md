# DOAJ — Protocol Card

> Status: behavior observed 2026-10. Re-probe on repeated failures.

## Access

- Articles: `GET https://doaj.org/api/search/articles/<query>?page=<N>&pageSize=<S>`
- `<query>` is a Lucene/Elasticsearch query string (URL-encoded).
- Fielded: `doi:<doi>` (encode the colon). Journals endpoint:
  `/api/search/journals/<query>` (journal metadata, not articles).

## Identity & auth

- No API key for search endpoints. Still courteous: browser
  `User-Agent` + `Accept: application/json`.

## Rate limits & courtesy

- Loose limits, but stay sequential with 1-3s delay; stop on
  consecutive 429/403 and resume manually later.

## Anti-bot & standard response

- None on the API itself (no captcha, no 403 under sequential use).
- Publisher landings (outside DOAJ) are frequently anti-bot:
  full-page 403 (CDN), bare-302 without `Location` (curl stops,
  `num_redirects=1`), transient 503. Test exactly 3 angles once each
  (default UA, browser UA, HTTP/1.1); persistent failure = reject,
  recorded precisely. Proven anti-bot patterns are not retried again.

## Parser notes

- Query behavior: unquoted terms = loose OR (heavy noise, e.g.
  mining engineering, medicine for management topics). ALWAYS use
  quoted phrases for precision, then screen manually via abstract.
- `pageSize` max 100, default 10; always send explicit `page`.
- bibjson fields: `title`, `year`, `author[].name`,
  `journal.title`, `journal.publisher`, `identifier[]` (type doi),
  `link[]` (type fulltext), `abstract`, `keywords`, `subject`.
- Detail per DOI via the `doi:` query before verifying.

## Traps

- Over-gather ~5-6x the per-source target: Layer-1 attrition is high.
- Dedup by lowercase DOI BEFORE verifying. Missing DOI or malformed
  `http://dx.doi.org/...` values = immediate reject.
- No-record-at-authority (landing 200 but no authority metadata) =
  reject; a 200 landing alone is not a pass.

## Fallback chain

- DOAJ search is already full-text; `site:` dorking is a complement
  only when the API misses a web-visible candidate.

## Retry budget

- 1x retry via explicit `https` / HTTP/1.1 for failed landings;
  then verdict. Resolver checks stay one light GET per DOI.

## Example

> Topic-specific values below are illustration only.

- EN: `"<TOPIC PHRASE>"`, `"<TOPIC PHRASE>" AND performance`,
  `"<RELATED CONCEPT>"`.
- Local language: `"<TOPIC IN LOCAL LANGUAGE>"` (recall varies;
  record hit counts as evidence either way).

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
