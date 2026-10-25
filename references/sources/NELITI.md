# NELITI — Protocol Card (hosting CMS + harvester + search)

> Status: behavior observed 2026-09-13. Re-probe on repeated failures.

## Access

- Canonical base: `https://www.neliti.com` — a free-to-use
  website builder + CMS + search engine for repositories,
  journals, and conferences (hosting, not just indexing).
- Search: `/search?q=<keyword>&page=<n>&per_page=<10|20|50|100>`
  with combinable filters: sort (Relevance | Most Recent | A-Z),
  language, date (Since YEAR + custom from/to), type (journal
  articles / theses / books / conference papers / reports /
  datasets), country, accreditation. Journals listing adds field
  (60+ values) and sort by publications/views.
- Detail: `/publications/<id>` or `/<id>/<slug>` (title,
  authors, journal/repo, date, language, abstract, metrics,
  citations, View-original link).
- Download: `/publications/<id>/download/<file_id>` (the
  `file_id` is per-publication — never reuse one across IDs).
- Citations: `/citations/<id>/ris` (RIS/BibTeX).
- OAI-PMH v2.0: `/oai` (`metadataPrefix=oai_dc` only) with
  `ListSets` (200/response, numeric setSpec per journal),
  `ListIdentifiers`, `ListRecords` (200 + `resumptionToken`),
  `GetRecord` (`identifier=oai:neliti:<n>`). `/api` documents
  OAI only — there is no other public REST/JSON API.

## Identity & auth

- No auth for reads; sign-in only for writes.
- Header discipline is MANDATORY (see Anti-bot): browser UA +
  Referer on every fetch.

## Rate limits & courtesy

- ~1s delay between requests; no captcha on search and listing
  pages; no parallel burst.

## Anti-bot & standard response

- CloudFront 403 for bare curl on `/publications/<id>` and
  `/download/...` (search/list pages are unaffected).
- Standard request that succeeds:
  `curl -A "Mozilla/5.0" -H "Referer:
  https://www.neliti.com/publications/<id>/..." .../download/<file_id>`
  returns 200 `%PDF`. Missing Referer or a wrong `file_id`
  returns 403/302 — fix the request, do not retry bare.
- If a HEAD with correct headers still 403s, CloudFront rules
  have drifted (observed 2026-10-25: Referer no longer helps) —
  prefer OAI-PMH for metadata, escalate to a browser-capable
  fetch only for the file itself.

## Parser notes

- Search results: `div` blocks with `a[href="/publications/<id>"]`
  plus views/downloads metrics — the richest filtering of the
  sibling national indexes (no per-field select needed).
- Detail page: download anchor matches `a[href*="/download"]`;
  metrics and View-original links sit on the same page.
- Exact filter-param encoding is not fully captured: verify
  against Network inspection when combining filters, and record
  what worked in the run log.
- OAI `ListRecords` suits bulk harvest (loop `resumptionToken`
  per journal set) but cannot filter by publication year —
  only by modification datestamp.

## Traps

- Search breakdown counts double-count across types — never sum
  type facets as a collection total.
- A free-to-use ad wall (~10s) precedes downloads but does not
  block them — wait it out, do not route around it.
- OAI sets include a `unique` set (content not indexed
  elsewhere) — useful for dedup scoping against sibling lanes.

## Fallback chain

- Internal `q=` + filters first (more precise than dorking).
- Dorking (`site:neliti.com`) as a secondary pointer source.
- OAI-PMH bulk harvest when HTML filtering is insufficient.
- Browser-capable fetch for stubborn 403 downloads.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Discovery: `/search?q=<KEYWORDS>&language=<LANG>&type=<TYPE>
  &from=<YYYY>&to=<YYYY>` + parse `publications/<id>`.
- Fetch: detail page, then PDF download with UA + Referer.
- Bulk: OAI `ListRecords&metadataPrefix=oai_dc&set=<journal-id>`
  looping `resumptionToken`.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
