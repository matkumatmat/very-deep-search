# SCHOLAR — Protocol Card (Google Scholar, HTML)

> Status: behavior observed 2026-10. Markup and tolerance drift;
> re-probe parsers on empty results.

## Access

- Search: `https://scholar.google.com/scholar?q=<query>&hl=en`
- No official API. HTML scraping only.
- Pagination: 10 results/page, next via `start=10,20,...`

## Identity & auth

- Browser-like UA is MANDATORY (desktop Chrome + `Accept` +
  `Accept-Language`). Without it, Scholar returns empty/error pages.

## Rate limits & courtesy

- Sequential with ~9s delay: 4/4 requests returned HTTP 200 with no
  captcha under these conditions.
- On `unusual traffic`/captcha: stop immediately, record, fall back
  to backbone discovery (Crossref/OpenAlex) using the same queries.
  Browser is a last resort, never a retry loop.

## Anti-bot & standard response

- Search-level: captcha (see above).
- Publisher landing level (Layer 1): toll publishers return 403 to
  automated clients even with full browser headers + HTTP/2, while
  the `url_effective` redirect is correct. Strict verdict: reject +
  queue `needs_richer_check`. A correct redirect is not a pass.

## Parser notes

- Result blocks: `<div class="gs_r gs_or gs_scl"` — match the class
  PREFIX (trailing `data-cid`/`data-did` attributes break naive
  `...scl">` matching; this exact bug cost one run its first parse).
- Title: `<h3 class="gs_rt">`; meta: `<div class="gs_a">`; links from
  `href` inside `h3`.
- Titles may be truncated (`...`) or prefixed `[PDF]`/`[BOOK]`:
  canonical title always comes from the Layer-2 authority, never
  from Scholar.
- Scholar yields no DOI: resolve each candidate's DOI via a backbone
  bibliographic query per title. Candidates without a resolvable DOI
  do not count toward quota (record as reject + reason).

## Fallback chain

- Blocked/captcha search -> backbone discovery, same queries.
- `url_sumber` equivalent: the Scholar query URL where the candidate
  was found (re-openable in a browser).

## Retry budget

- 1x retry with full browser headers + HTTP/2 for 403 landings.
  Persistent: verdict + queue, no further retries.

## Example

> Topic-specific values below are illustration only.

- EN: `<TOPIC> responsibility center performance`
- EN quoted: `"<TOPIC>" "business unit performance"`
- Local-language query to catch national journals missed by EN-only.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
