# CROSSREF — Protocol Card

> Status: behavior observed 2026-10. Re-probe on repeated failures.

## Access

- Search: `GET https://api.crossref.org/works?query=<keywords>&rows=<N>&select=DOI,title,author,container-title,publisher,published,URL,type`
- Detail: `GET https://api.crossref.org/works/<DOI>`
- Docs: `https://api.crossref.org/documentation`
- Role: metadata aggregator (not fulltext) and Layer-2 authority for
  DOI verification. Also the discovery backbone when other sources fail.

## Identity & auth

- Header: `User-Agent: <project>/1.0 (mailto:<YOUR_EMAIL>)`
- `mailto` query param with a valid contact routes to the polite pool
  (faster, prioritized). Anonymous pool is slow.
- Never fake an institutional mailto; use the operator's own identity.

## Rate limits & courtesy

- Observed: `X-Rate-Limit-Limit: 3`, interval 1s (anonymous).
- Sequential only, no burst/parallel. Sleep 4-6s between requests.
- HTTP 429 = throttled: back off 60s+, then continue one at a time.
  A 2-query burst triggered an empty 429 that cleared after 65s.

## Anti-bot & standard response

- None on the API itself. Layer-1 failures happen at publisher
  landings (403/444 anti-bot despite a correct doi.org redirect):
  record status as-is, verdict reject, queue `needs_richer_check`.

## Parser notes

- JSON. Keep `select` minimal and `rows` small (10) for speed.
- Year: `published`, fallback `published-print` /
  `published-online` / `created`.
- Screen result `type`: `posted-content` (preprints), dissertations,
  and books appear — filter against inclusion criteria.
- Retroactive re-deposits shift the year (deposit date vs issue
  date): tolerate with annotation, do not auto-reject.

## Fallback chain

- Crossref IS the fallback for dead/maintenance/throttled sources.
  It needs no fallback itself; on persistent 429, stop and resume later.

## Retry budget

- 1x retry for empty responses / network hiccups, then backoff.
- Persistent 429 after backoff: stop the source, record, move on.

## Example

> Topic-specific values below are illustration only.

- `query=<TOPIC TERMS>&rows=10&select=DOI,title,author,container-title,publisher,published,URL,type&mailto=<YOUR_EMAIL>`
- L1: `curl -s -o /dev/null -w "%{http_code} %{url_effective}" -m 40 -L -A "<UA>" "https://doi.org/<DOI>"`
- L2: `curl -s "https://api.crossref.org/works/<DOI>"`, match title + year.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
