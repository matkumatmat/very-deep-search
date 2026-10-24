# BASE — Protocol Card (aggregator, registered API + guarded UI)

> Status: behavior observed 2026-10-24. Re-probe on repeated failures.

## Access

- Operator: Bielefeld University Library. Claimed scale: hundreds
  of millions of documents from 10k+ providers (OAI-PMH + Crossref
  harvest): journal articles, preprints, theses, books, datasets.
- Web UI: `https://www.base-search.net`
  (`/Search/Results?lookfor=<q>&language=<en|id|...>`, 20/page,
  facets: doctype, language, year, provider).
- Canonical record: `https://www.base-search.net/Record/<hash>`
  (the only proof of BASE indexing).
- HTTP Search Interface:
  `https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi`
  (`func=PerformSearch`, `query=`, `format=json|xml|dc|rss|...`).
  Query syntax is Lucene-like and fielded
  (`dctitle:<phrase> dcsubject:<phrase>`); paging via `hits` +
  `offset`; sort via `sort=dctitle|dcdate`.
- Advanced search: `/Search/Advanced` (per-field
  `dc:title/subject/creator`).

## Identity & auth

- API registration is REQUIRED (free, via the BASE helpdesk form):
  access is opened per registered **IP + User-Agent** combination.
- Unregistered calls return HTTP 200 with body
  `{"error": "Access denied for IP address ... and user agent ..."}`.
- Credentials via env vars (`BASE_USER`, registered UA) — never
  hardcoded. Community clients (e.g. R `rbace`) wrap the same
  interface and need the same registration.

## Rate limits & courtesy

- Registered mode: sequential, 2-3s delay, `format=json`.
- Never burst; one run stayed under ~60 total requests across all
  endpoints including fallbacks.

## Anti-bot & standard response

- Anubis JS proof-of-work guards all of `www.base-search.net`
  (including help/API doc pages): curl gets HTTP 200 carrying a
  `Making sure you're not a bot!` page (~8KB), never results.
  Only a real browser passes.
- `api.base-search.net` without registration: `Access denied`
  (not a captcha — a registration gate).
- Standard response: one probe of each surface for status
  evidence, then STOP hammering; escalate to the registered API
  or a real browser. Retrying curl against Anubis is futile.

## Parser notes

- `format=json` is concise; `format=dc` is full Dublin Core with
  the DOI in `dcidentifier`.
- A candidate MUST carry a DOI (`dcidentifier:doi:*`) — DOI-less
  records are rejected before verification.
- `doctype` filtering is mandatory for journal-only missions;
  without it the result mix is dominated by non-articles.

## Traps

- BASE metadata tracks Crossref for active DOIs, but dead and
  re-registered DOIs still appear — never skip 2-layer
  verification just because a candidate "came from BASE".
- Cross-sibling-journal content duplicates (same publisher,
  identical title + authors) occur: check manually before
  counting quota — lowercase DOI dedup will not catch them.
- Publisher-side blocks (403s, timeouts) fail Layer 1 even when
  metadata matches — record as observed resolver status, not as
  a BASE problem.

## Fallback chain

- Dorking: `site:base-search.net/Record "<TERMS>"` finds
  canonical Record pages (pointers only, backbone verifies).
- Discovery mirror: Crossref (the same DOI corpus BASE
  harvests), with each unconfirmed record flagged
  `needs_richer_check` for later Record-page confirmation.
  Without registration this keyless path is the intended one:
  run Crossref discovery + standard 2-layer verification,
  flag unconfirmed records, never stall waiting for access.
- Browser pass: confirm `/Record/` indexing for shortlisted DOIs.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Registered: `func=PerformSearch&query=dctitle:<PHRASE>
  dcsubject:<PHRASE>&format=json` with `type:article` filter.
- Fallback: bilingual backbone batches + manual title curation
  BEFORE verification (saves requests), then 2-layer curl per DOI.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
