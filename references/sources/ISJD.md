# ISJD — Protocol Card (national journal index, access-fragile)

> Status: behavior observed 2026-10-24. Re-probe on repeated failures.

## Access

- Canonical base: `https://isjd.brin.go.id/` (Indonesian
  Scientific Journal Database, run by BRIN, ex LIPI/PDII).
- Legacy alias `isjd.pdii.lipi.go.id` is dead — do not use it.
- Observed 2026-10-24: the canonical domain did NOT resolve DNS
  from the gather environment (curl 000, fetch DNS fail) — treat
  as possibly migrating/dead until a fresh probe says otherwise.
- ISJD is an index/abstracts service, NOT a fulltext host: take
  metadata plus the publisher OJS link as companion evidence URL.

## Identity & auth

- None observed (site unreachable at observation time).
- If live: browser UA, sequential, stop on 403 — same courtesy
  as sibling national-index cards.

## Rate limits & courtesy

- If live: sequential, 2-3s delay, stop on 403/429, no parallel
  burst.
- One access probe per run; never aggressively retry a dead
  host (max 1 re-probe from a different angle, then flag).

## Anti-bot & standard response

- None observed (site unreachable). Default posture: browser UA,
  sequential, stop on 403/429.

## Parser notes

- If live: identify the internal search form first via a single
  fetch + inspect (which param: `q`? `search`? title/author
  fields?) — never guess params with repeated blind requests.
- Expect an old-site format with no API.

## Traps

- Domain unstable across regimes (`pdii.lipi.go.id` ->
  `brin.go.id`) — always probe the canonical base first; a dead
  alias is infrastructure, not a block to route around.
- ISJD records are often DOI-less (old non-OJS journals):
  DOI-less candidates are auto-rejected under the verification
  contract, however topical.
- The Crossref fallback is DOI-first biased: it misses DOI-less
  legacy journals the live index would surface. Note the bias.

## Fallback chain

- Probe once: live -> direct crawl (§Parser notes); dead ->
  Crossref REST discovery (bilingual queries + implicit
  national-journal class filter, `rows` + minimal `select=`,
  identified UA) with mandatory 2-layer verification per
  candidate, and flag `needs_access_check` on the run.
- Dorking (`site:isjd.brin.go.id "<TERMS>"`) only when live —
  on a dead site it yields no gather evidence.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Live: single homepage fetch, form identification, then
  per-field discovery + publisher-link capture.
- Dead: `/works?query=<BILINGUAL TERMS>&rows=15&select=DOI,
  title,author,container-title,publisher,published,URL` + 2-layer
  curl per DOI.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
