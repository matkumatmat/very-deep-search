# MORAREF — Protocol Card (national reference index, maintenance-prone)

> Status: behavior observed 2026-10-25. Re-probe on repeated failures.

## Access

- Canonical base: `https://moraref.kemenag.go.id/` (Ministry of
  Religious Affairs Reference, Indonesia).
- Coverage: Indonesian journals/articles, weighted toward
  religious-university publishers plus general national journals.
- Article deep URL: `/documents/article/<numeric-id>` (long
  numeric IDs, visible in the search-engine index).
- Aggregator like SINTA: metadata + links only; fulltext always
  lives at the publisher site (mostly OJS).
- No documented public API. Possible hidden JSON endpoints
  (e.g. `/api/...`) are unexplored — do not assume any.

## Identity & auth

- No auth observed. Browser UA for HTML; descriptive UA + mailto
  for backbone API calls.

## Rate limits & courtesy

- Sequential, ~3s delay between requests, stop on 403, no
  parallel burst.
- Respect a maintenance page: 1x probe per path to confirm
  status, never aggressive scraping of a static page.

## Anti-bot & standard response

- None observed (site was in total maintenance at observation
  time: every path returned HTTP 200 with the SAME static
  maintenance page, ~4KB).
- Standard response to that signal: live crawl STOPS — a 200
  carrying identical static content on all paths is
  maintenance, not data. Switch to the fallback chain.
- Maintenance evidence: save the static page body (or its
  sha256) as the `site_down` evidence artifact, so the
  verdict is reproducible.
- If the site recovers and shows 403/Cloudflare: flag
  `needs_richer_check`, stop curl, take the browser path.

## Parser notes

- When UP: use the site search box (bilingual queries), collect
  title, authors, journal, year, detail link, and DOI when
  listed; open each detail page, then run verification.
- When DOWN: the search-engine index still enumerates article
  IDs (`site:moraref.kemenag.go.id`) but yields minimal
  metadata — IDs are pointers, never verification.

## Traps

- Site status fluctuates (total maintenance observed) — always
  probe status BEFORE crawling, and re-probe periodically:
  when the site recovers, re-run the primary queries live.
- Links to international publishers often 403 via curl: reject
  honestly or queue for browser verification, never force.
- The Crossref fallback is a coverage PROXY, not Moraref
  coverage — every fallback-sourced record must say so in its
  reason field.

## Fallback chain

- Fallback A — search-engine index for article-ID enumeration
  (take `/documents/article/<id>` URLs from results as ID
  pointers) + 2-layer DOI verification per candidate.
- Fallback B — Crossref API (`/works?query=&rows=&select=`
  minimal), prioritizing national journals as the coverage
  proxy, fallback noted in each record's reason.
- Browser pass for anti-bot landing promotion.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Live: bilingual site-search queries, detail pages, DOI capture.
- Down: `site:<MORAREF-DOMAIN> "<TOPIC>"` for IDs; `/works?
  query=<TOPIC>&rows=10&select=DOI,title,author,container-title,
  publisher,published,URL` + 2-layer curl per DOI.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
