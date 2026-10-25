# SEMANTICSCHOLAR — Protocol Card (paper graph API, throttled search)

> Status: behavior observed 2026-10-25. Re-probe on repeated failures.

## Access

- Web: `https://www.semanticscholar.org` (paper page
  `/paper/<paperId>` — the evidence URL for S2-sourced records).
- Graph API v1 (JSON): `https://api.semanticscholar.org/graph/v1`.
  Docs: `https://api.semanticscholar.org/api-docs/`.
- Discovery: `GET /paper/search?query=<q>&limit=<n>&fields=<f>`
  (see Rate limits — persistently throttled keyless).
- Lookup: `GET /paper/DOI:<doi>?fields=<f>` (stable 200;
  returns `paperId`, canonical page URL, metadata).
- Fields used: `title,authors,year,venue,publicationVenue,
  externalIds,url,openAccessPdf`. Lookup response carries
  `paperId`, `title`, `authors[{authorId,name}]`, `year`,
  `venue`, `externalIds{DOI,...}`, `url`, `openAccessPdf`.

## Identity & auth

- Keyless: shared IP quota (~100 req/5min). With a key
  (request form on the product page): header `x-api-key`
  and a far looser quota. Key via env, never hardcoded.
- Research UA on every call; no S2 HTML scraping.

## Rate limits & courtesy (critical)

- Observed: `/paper/search` stayed `429 Too Many Requests`
  from a shared egress IP across attempts 70s apart, while
  `/paper/DOI:` answered 200 normally.
- NEVER burst `/paper/search`. Pattern: per-DOI lookups with
  >=4s gaps; discovery via OpenAlex/Crossref (open, friendly
  limits, polite `mailto:` pool). If search recovers:
  `limit<=20`, >=3s gaps, stop on 429 + 60s backoff.
- Request a key when the lane needs bulk `/paper/search`;
  without one, stay on lookup + external discovery.

## Anti-bot & standard response

- The throttle IS the anti-bot: persistent 429 on search,
  clean 200 on lookup. Lookup may also 429 on a shared egress
  IP (observed 2026-10-25) — wait >=60s between calls, then a
  single retry. Standard response is the split pattern above —
  not retries, not evasion.
- Publisher-side blocks (big-publisher 403s to datacenter
  curl, small-OJS 302s without Location) fail strict L1
  even for valid DOIs: record and reject, never force.

## Parser notes

- `venue` is often empty for proceedings/chapters — fall
  back to the Crossref `container-title` for the venue name.
- A dead DOI shows consistently: S2 404 + doi.org 404 +
  empty Crossref. That triple is why 2-layer verification
  is mandatory, not optional.

## Traps

- Index is English-biased: pure non-English discovery is
  weak — pair every non-English query with an English one
  via the external discovery source.
- S2-vs-Crossref year can differ 1-2 years (online-first vs
  volume year): always compare the two API years against
  each other, never against memory.
- L1 MUST use GET, not HEAD — HEAD returns phantom 302/403
  on some OJS publishers.
- A correct redirect target + matching L2 with a 403
  landing is an INTENTIONAL contractual loss (reject),
  not a dead DOI — label it as such for browser rehab.

## Fallback chain

- OpenAlex/Crossref discovery -> S2 per-DOI lookup (S2
  membership proof: `paperId` + S2 page URL required on
  every pass record) -> 2-layer verification.
- Dorking is not primary; optional manual check:
  `site:semanticscholar.org/paper "<title>"`.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Discovery: OpenAlex `works?search=<BILINGUAL TERMS>` ->
  DOI list -> S2 `/paper/DOI:<doi>?fields=...` (>=4s gaps).
- Evidence URL = the S2 paper page, never the discovery URL.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
