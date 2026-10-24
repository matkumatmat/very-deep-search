# RAMA — Protocol Card (national thesis repository)

> Status: behavior observed 2026-10-25. Re-probe on repeated failures.

## Access

- Canonical base: `https://rama.kemdiktisaintek.go.id/` (national
  repository of student theses; HTTP 200 observed).
- Legacy `https://rama.kemdikbud.go.id/` is DNS-dead — do not use it.
- Coverage: undergraduate theses / master theses / dissertations
  from university repositories (EPrints/DSpace, OAI-linked).
  NOT journals: records are thesis metadata + origin-repo link,
  with NO DOI field.
- Quota implication: RAMA cannot supply DOI journals directly.
  Its role is national-coverage proof at thesis level plus a
  guide for fallback queries to the journal versions.
- Search: GET `/` first (cookie/session needed), then
  `POST /search/all/` with `q=<query>` + `kondisi=<1|2|3>`
  (1=All, 2=By Title, 3=By Institution). Result cards link to
  `/document/detail/oai:<repo>:<id>-<code>`; paging via
  `/search/all/<query>/<offset>`.
- Detail page (fixed pattern): REPOSITORY INFO block (origin
  URL, platform, document count) + TITLE + institution +
  author + subject + datestamp + abstract.
- No public API.

## Identity & auth

- No auth. Browser UA for HTML; descriptive UA + mailto for
  backbone API calls.

## Rate limits & courtesy

- Sequential, ~3s delay, stop on 403, no parallel burst.
- Never brute-force numeric/OAI detail IDs.

## Anti-bot & standard response

- None observed (consistent 200 with browser UA).
- Connection is FLAKY (occasional curl 000 on search and
  paging): use `--retry 2` with backoff, repeat a failed path
  at most 1x, then switch angles (detail page / Crossref)
  instead of hammering the same endpoint.
- If 403/Cloudflare appears: flag `needs_richer_check`, stop
  curl, take the browser path.

## Parser notes

- Confirm DOI absence per record (grep for `10.xxxx/`) —
  record as "DOI-less thesis", never assume.
- Top-ranked samples matched the query in testing, so title
  ranking works even though the hit counter does not (Traps).

## Traps

- The "millions of results" figure is the TOTAL collection
  (display bug), not query hits — judge relevance by sampling
  records, never by that number.
- L1 edge cases observed: resolver 200 landing on the journal
  HOMEPAGE (OJS migration) must be recorded explicitly, never
  hidden; resolver 404 (lost archive file) = reject —
  Crossref-registered does not guarantee a live file; missing
  year in Crossref = reject.
- Author-matching RAMA-thesis -> Crossref-journal (same author,
  journal version) is an open research question, not an
  established claim — do not assert it without evidence.

## Fallback chain

- Crossref API (bilingual queries, national-journal bias to
  keep coverage relevance: "the journal version of the same
  literature RAMA holds at thesis level") + full 2-layer
  verification per candidate. Every fallback record's reason
  must state the fallback plainly.
- Dorking (`site:<RAMA-DOMAIN> "<TERMS>"`) enumerates detail
  IDs when web search is down — never a verification substitute.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Live: homepage GET, `POST /search/all/` (`q=<BILINGUAL
  TERMS>`, `kondisi=2`), detail pages, 3-4 thesis records as
  coverage proof (rejected: no DOI).
- Fallback: `/works?query=<TERMS>&rows=12&select=DOI,title,
  author,container-title,publisher,published,URL` + 2-layer curl.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
