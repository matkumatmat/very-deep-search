# SINTA — Protocol Card (national author/journal aggregator)

> Status: behavior observed 2026-09-13. Re-probe on repeated failures.

## Access

- Canonical base: `https://sinta.kemdiktisaintek.go.id`
  (SINTA v3). Legacy `https://sinta.kemdikbud.go.id` is
  unreliable (transport errors / redirects) — do not use it.
- HTML (public path): `/authors`, `/affiliations`,
  `/affiliations/authors/<affil_id>?page=<N>&sort=<order>`
  (10/page), `/affiliations/<id>`, `/departments/<id>`,
  `/journals?q=<kw>&mode=<title|all>&affil=<id>`,
  `/journals/profile/<id>`, plus `/books`, `/iprs`,
  `/researches`, `/comservices`, `/scopus`, `/google`,
  `/wcu`, `/insight`.
- Official API (`http://apisinta.kemdikbud.go.id`) is NOT
  for public use: login -> Bearer; paths
  `/v3/<env>/<uniq>/<resource>/<action>/<type>/<id>`;
  all-POST `{items:10-100, page, order:1-5}`; 500 req/day;
  scope-limited by caller. API mode only with user-supplied
  `SINTA_USERNAME/PASSWORD/UNIQ` via env.
- SINTA links into Garuda, RAMA, and sibling services
  (network footer) — one ecosystem, separate surfaces.

## Identity & auth

- HTML path: none. Browser-like UA (rotated).
- API path: ministry-issued credentials + uniq — never
  hardcoded; unsuitable for a generic public plugin.

## Rate limits & courtesy

- Sequential ONLY: 2-3s delay + random 1-2s jitter. No
  parallel, no async burst. Exponential backoff, stop on 403.
- Run from a local/VPS network: cloud-notebook IPs are
  blocked (possibly on the first request, not only after
  bursts), and 403s appear after ~50+ fast requests.

## Anti-bot & standard response

- No visible captcha — but inconsistent HTTP 403 on bursts
  or flagged IPs. Standard response: backoff, slow down,
  stop on repeat 403. Never retry a 403 into a burst.

## Parser notes

- Author entries: name, SINTA ID, dept, scores, h-indexes
  via CSS/XPath. Classes restyle often — expect updates.
- Journal search modes: `basic` (list fields: name, level,
  ISSNs, affiliation, scores, h-index) vs `detail`
  (per-item `/journals/profile/<id>` fetch).
- `/journals` searches journal NAMES, not article titles —
  an article title present in the Scholar tab returns 0
  here. For ARTICLES, follow the affiliation-profile tabs
  (`view=garuda|scopus|googlescholar`), never `/journals`;
  `/journals` is only for journal metadata (accreditation).
- SINTA IDs are user-verifiable via
  `/authors/profile/<sinta_id>`; for papers, Garuda/RAMA
  links verify better than SINTA alone.

## Traps (critical)

- SINTA is an INDEX/aggregator, not a repository: profile
  tabs show different counts per upstream (Scopus vs
  Garuda vs Scholar) — SINTA only recaps. Never treat it
  as a fulltext or primary-metadata source.
- Tied scores (especially 0) randomize list order PER
  REQUEST: single-pass scraping captures only ~95%.
  Fix: iterative sequential scraping (4-8 passes) + dedup
  by SINTA ID, validating `len(unique)==expected` before
  stopping, with per-iteration state saved.
- No reliable total count in HTML: loop until a page
  returns <10 items or dedup reaches the expected count.

## Fallback chain

- HTML scraping is the only public road; API only with
  user-supplied credentials.
- Dorking is irrelevant — direct fetch is more verifiable.
- Reference implementations exist as libraries/CLI tools
  (affiliation/author/department fetch, basic|detail
  modes, json/csv output) — consult before hand-rolling.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Authors: `/affiliations/authors/<ID>?page=<N>` queue,
  SINTA-ID set, iterate to `unique == expected` (max 8).
- Journals: `/journals?q=<NAME>&mode=title` for metadata;
  tab-follow for articles.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
