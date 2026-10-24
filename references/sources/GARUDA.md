# GARUDA — Protocol Card (HTML harvester)

> Status: behavior observed 2026-09/10. Re-probe on repeated failures.

## Access

- Canonical base: `https://garuda.kemdiktisaintek.go.id` (verify with
  one probe first; the legacy `https://garuda.kemdikbud.go.id` is
  DNS-dead — do not use it).
- Harvester via OAI-PMH from publishers; metadata + original links,
  not its own fulltext storage.
- Search: `GET /documents/?q=<keywords>&select=<title|abstract|author|doi>&from=<YYYY>&to=<YYYY>&pdf=1`
  (`q` required, min length 3-4; `select` defaults to title).
- Detail: `GET /documents/detail/<numeric-id>` (most stable surface).
- Journal/publisher/area listings exist; for journal lists, crawl
  `/journal` alphabetically rather than via query search.

## Identity & auth

- No auth, no captcha observed. Browser UA + 1-2s delay.
- curl MUST use `-L` (without it, an empty 302).

## Rate limits & courtesy

- Undocumented; stay sequential with 1-2s delay regardless.

## Anti-bot & standard response

- None observed. Wrong params (`title=` instead of `q`+`select`)
  return HTTP 500 — a caller bug, not a block.

## Parser notes

- Title: `<a class="title-article"><xmp>...</xmp>`; authors:
  `a.author-article[href*="/author/view"]`; journal: `<xmp
  class="subtitle-article">`; abstract: `<xmp
  class="abstract-article">` (often bilingual, full text on detail page).
- Unescape literal `\n` sequences before parsing.
- Class attributes drift: `title-article` was gone by 2026-10 while
  `<xmp>` blocks remained. Robust fallback: positional order —
  journal, issue, title, authors..., abstract — instead of classes.
- Detail links: Show Abstract | Download Original | Original Source |
  Check in Google Scholar | DOI.
- `select` changes the searched field: the same query returns
  different counts for title vs abstract — choose deliberately.
- Numeric detail IDs are incremental: never brute-force them.

## Traps (critical)

- Old records (roughly 2012-2018) usually show NO article DOI; DOIs
  visible on the page belong to the BIBLIOGRAPHY. Never record a
  page DOI. Resolve the article DOI via a backbone title query, then
  run two-layer verification. Candidates that stay DOI-less are
  recorded as reject (proof of coverage).

## Fallback chain

- Backbone (Crossref/OpenAlex) for DOI resolution and L2.
- `Download Original` direct PDF when open access; else the
  publisher's Original Source link for the content pass.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Discovery: `site:<GARUDA-DOMAIN> "<TOPIC>"` plus ~14 bilingual
  internal queries alternating `select=title` / `select=abstract`.
- Detail fetch per candidate ID, then backbone DOI resolution.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
