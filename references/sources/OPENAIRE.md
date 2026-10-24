# OPENAIRE — Protocol Card (research aggregator API)

> Status: behavior observed 2026-10-24. Re-probe on repeated failures.

## Access

- API (public, no auth):
  `https://api.openaire.eu/search/publications?format=json&...`
- Discovery: `...&size=<n>&keywords=<query>` (broad: query is
  split into a boolean AND across common words) or
  `...&size=<n>&title=<2-3 words>` (strict: EVERY word must
  appear in the title).
- Record pull: `...&doi=<DOI>` (exactly 1 record, with
  `description`/abstract when available).
- Supported params (from the API's own error message): `funder,
  country, keywords, title, doi, author, fromDateAccepted,
  toDateAccepted`, plus `size, format, sortBy, page`. `keyword=`
  (singular) is NOT supported (HTTP 400) — use `keywords=`.
- Response: `response.header.total.$` (hit count),
  `response.results.result[]`, each item under
  `metadata.oaf:entity.oaf:result` with `pid.$` (DOI), `title`,
  `dateofacceptance`, `description`, `creator`, `collectedfrom`
  (provenance: Crossref, repositories, ...).
- UI `https://explore.openaire.eu` is heavy JS — never scrape
  it; the JSON API suffices. Docs:
  `https://develop.openaire.eu/search-api/`.

## Identity & auth

- No auth, no login, no token (open data). Identified
  browser-like UA + mission identity on every call.

## Rate limits & courtesy

- Sequential + 1-2s sleep between calls; no parallel burst.
  A full run stays under ~30 requests — far below any
  reasonable threshold.

## Anti-bot & standard response

- None on the API — no captcha, no challenge.
- HTTP failures happen PUBLISHER-side at Layer 1 (persistent
  OJS 403s to HEAD and GET even with browser UA + Referer,
  Cloudflare challenges, down hosts, timeouts): record the
  observed non-200 `resolver_status` + `needs_richer_check`
  and move on. That is publisher infrastructure, NOT an
  OpenAIRE problem — never re-retry it into a burst.

## Parser notes

- `results` is `None` (not an empty list) when total=0 —
  handle explicitly or the parser crashes on empty queries.
- Preview titles are truncated (~110 chars): canonical
  metadata (full title, journal, publisher, authors) ALWAYS
  comes from the Crossref L2 call, never from the preview.
- The `doi=` record's `description` is a useful BACKUP
  abstract for inclusion screening when the publisher page
  is anti-bot — it never replaces Layer 1.
- `dateofacceptance` tracks the Crossref year for active DOIs.

## Traps

- Long `title=` phrases recall ~0 (strict per-word AND) — a
  zero-hit long phrase proves nothing; always back off to
  2-3 words or `keywords=` before concluding.
- `keywords=` precision is LOW: theses, course packs, OSF
  preprints, course notes, datasets. Manual title curation
  (unit-level vs individual vs non-journal) BEFORE
  verification is mandatory, not optional.
- Non-journal DOI prefixes (`10.31219/osf.io/...`, `10.13140/...`,
  `10.5281/zenodo...`, SSRN), handle-only records, and `None`
  DOIs are rejected BEFORE verification — journal DOI required.
- High overlap with sibling lanes (same OJS articles appear
  in OpenAlex/Unpaywall): dedup lowercase-DOI against
  neighbor staging BEFORE burning verification requests.

## Fallback chain

- Crossref for canonical metadata; OpenAIRE `description`
  as backup abstract; `needs_richer_check` queue for
  403/down publisher landings (optional coordinator
  rehabilitation, not failure).

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Discovery: `keywords=<NARROW TERMS>` + `keywords=<SECOND
  LANGUAGE TERMS>`; `title=<2-3 WORDS>` for title search.
- Pipeline: curate titles -> dedup vs siblings -> L2
  (Crossref) -> L1 (`curl -sIL` + browser UA) -> GET
  recheck for non-200s before final verdict.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
