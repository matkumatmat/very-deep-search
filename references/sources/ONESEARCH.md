# ONESEARCH — Protocol Card (national library union catalog)

> Status: behavior observed 2026-09-13. Re-probe on repeated failures.

## Access

- Canonical base: `https://onesearch.id` (Indonesia OneSearch,
  National Library; VuFind + Solr backend, harvesting IOS nodes).
- Search:
  `/Search/Results?lookfor=<keyword>&type=<AllFields|Title|
  Author|Subject|CallNumber|ISN|tag>&limit=20&sort=relevance`
- Record: `/Record/<id>` (e.g. `IOS<number>.article-<n>`) with
  fulltext links, Save-record, and Z39.88 metadata.
- Advanced: `/Search/Advanced` (multi-field boolean groups with
  ALL/ANY/NO-Terms match + Limit-To collection listbox).
- Facets: sector, institution, publication date (via embedded
  `pivotdata` JSON), topic treemap; views: list/grid/visual/AI.

## Identity & auth

- No auth, no key. Bare curl succeeds on search and records.

## Rate limits & courtesy

- Light and fast (sub-second searches observed); stay
  sequential with ~1s courtesy delays regardless.

## Anti-bot & standard response

- None on OneSearch itself — no captcha, no CloudFront/CF
  block, unlike some sibling indexes.
- Provider links VARY: sniff the `fulltext` href domain before
  fetching — OJS-style hosts (`jurnal.*`, `ojs.*`, `ejournal.*`)
  verify via bare-curl HEAD (200 `application/pdf` observed),
  while OPAC/catalog hosts may sit behind JS challenges and
  fail curl. Flag the latter `needs_richer_check`, do not
  force them.

## Parser notes

- Results: `div#result<n>` / `div.row.result.clearfix`,
  `a.title[href="/Record/<id>"]`, `a.fulltext`
  (`Available online:`) direct to the provider OJS — no media
  token or expiry hop.
- Detail: `span.Z3988` carries `rft.title` and friends for
  structured metadata.
- Advanced-search params beyond `type` are not fully mapped —
  inspect before scripting exotic combinations.

## Traps

- Result counts run SMALL (single/double digits where sibling
  indexes return thousands for the same query) — the catalog is
  curated/deduplicated, so small-N is normal, not a failure.
  Top records cross-verify against sibling indexes.
- Fulltext availability is per-provider: a record existing does
  not imply a fetchable PDF — always HEAD the `fulltext` link.

## Fallback chain

- Cross-verify records against sibling national indexes (the
  same article is often indexed in several).
- Provider-domain sniffing decides curl vs browser per link.
- Advanced search + facets when basic queries under-recall.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Discovery: `/Search/Results?lookfor=<KEYWORDS>&type=AllFields`.
- Detail: fetch `/Record/<id>`, extract `a.fulltext`, HEAD it:
  OJS 200 -> content pass; OPAC challenge -> `needs_richer_check`.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
