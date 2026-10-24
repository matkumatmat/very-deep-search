# RESEARCHGATE — Protocol Card (academic network, hard anti-bot)

> Status: behavior observed 2026-10-24. Re-probe on repeated failures.

## Access

- Canonical base: `https://www.researchgate.net`.
- URL patterns: `/publication/<numeric-id>_<slug>` (papers),
  `/scientific-contributions/<Name>-<id>` (authors),
  `/search/publication?q=<query>` (search).
- Without a browser, RG is an EVIDENCE layer (page existence
  via the search-engine index), not a primary fetch channel:
  every direct datacenter fetch observed (6 probes: curl and
  fetch tools) returned 403 anti-bot.
- Discovery companion: Crossref API (`query` /
  `query.bibliographic` + minimal `select=`) with polite ~2s
  delays and browser UA; RG-scoped web search
  (`researchgate.net/publication <title>`) yields the canonical
  page URL per candidate.

## Identity & auth

- PUBLIC PAGES ONLY. Never log in, never register an account.
- A login-wall interstitial means STOP (no login): record the
  URL + timestamp, compensate with other public queries on
  this source (public search, indexed publication/author pages).

## Rate limits & courtesy

- No aggressive bypass ever (no massive rotation, no parallel
  scrapers) — RG is known for hard rate limits + forced login.
- Probe each RG URL once with `curl -L` + browser UA and
  record the code; `403 + "Temporarily Unavailable"` is
  IP/ASN anti-bot, NOT proof the page is missing.

## Anti-bot & standard response

- The block hits BEFORE content on all surfaces observed.
  Misleading detail: the 403 body carries a `<title>` plus the
  word "Login" — that is still a bot block, not a login wall.
- Standard response: compensate via the search-engine index +
  independent DOI verification (doi.org / Crossref), which
  never depends on RG access. Browser is a legitimate
  escalation (anti-bot qualifies) under the shared lock:
  first navigation opens the URL in a fresh tab, reuse it,
  close when done.

## Parser notes

- Anti-bot precedes content: any parse attempt on a 403 body
  is junk — check status first.
- Classic papers may have NO dedicated RG page (only citing
  pages); smaller national journals often lack RG pages too.
  Compensate with the RG search URL + the primary DOI
  landing, and say so in the record.

## Traps

- Always read the Crossref abstract before deciding — title
  alone is never enough (individual-level samples hide behind
  topical titles).
- Landing-variant honesty: redirect-to-dead-`http` with the
  same landing alive as `https` (200) passes ONLY with both
  variants recorded explicitly in `resolver_status` for audit.
- Correct doi.org redirect + 403 landing = REJECT +
  `needs_richer_check`, never a pass on the redirect alone.

## Fallback chain

- Crossref API as the primary candidate + L2 source (clean,
  reliable — mandatory first).
- Web-index RG pages for `url_sumber` + existence proof
  without touching RG anti-bot.
- Browser pass for anti-bot landing promotion.

## Retry budget

- Standard: 1x retry with full headers (Accept,
  Accept-Language) before a final reject verdict.

## Example

> Topic-specific values below are illustration only.

- Discovery: bilingual Crossref batches -> shortlist DOIs ->
  `researchgate.net/publication <TITLE>` per shortlist item.
- Verification: L1 (`doi.org/<DOI>` must end 200 at the
  ARTICLE page) + L2 (Crossref title/year match).

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
