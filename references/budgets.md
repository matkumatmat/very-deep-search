# Request budgets (per source, per run)

Ceilings cap total HTTP/API requests to each source in one run.
A normal run stays far below its ceiling; the ceiling catches
runaway loops and bursts, not honest gathering. Every ceiling
derives from an observed run (date noted) plus headroom — never
from guessing. Exceeding a ceiling mid-run means STOP that
source, record why, and switch angles; raising a ceiling is a
deliberate edit to this file, never a silent act.

Format (machine-checked by tests/run.sh): `- <SOURCE>: <N> /run`.

Verification traffic (doi.org L1 + Crossref L2) is budgeted
separately: at most 3 requests per candidate (L1 + L2 + one
retry from a different angle), regardless of source.

## Ceilings

- ARXIV: 40 /run — basis: 14 queries observed 2026-10-25 at 4s gaps; service rule >=3s between requests.
- BASE: 80 /run — basis: <60 requests observed 2026-10-24 including fallbacks, sequential 2-3s gaps.
- CORE: 60 /run — basis: keyed API is quota-counted; direct core.ac.uk fetches stay <=10, rest via backbone discovery (observed 2026-10-24).
- CROSSREF: 60 /run — basis: 6 discovery queries observed; polite sleep >=5s, backoff 60s+ on 429.
- DOAJ: 40 /run — basis: search API pageSize <=100, loose service limit; observed polite 1-3s gaps.
- EUROPEPMC: 40 /run — basis: 8 queries observed 2026-10-24 at ~1s gaps, pageSize 25.
- GARUDA: 60 /run — basis: ~14 bilingual queries per run observed 2026-09/10 at 1-2s gaps, no hard service limit.
- ISJD: 20 /run — basis: 1 access probe per run; bulk discovery via the Crossref fallback (observed 2026-10-24).
- MORAREF: 30 /run — basis: ~3s gaps observed 2026-10-25; 1 probe per path under maintenance.
- NELITI: 100 /run — basis: 1s gaps observed 2026-09-13; OAI bulk pages (200 records each) plus detail fetches.
- ONESEARCH: 60 /run — basis: sub-second light searches observed 2026-09-13 with ~1s courtesy gaps.
- OPENAIRE: 50 /run — basis: <30 requests observed 2026-10-24, sequential 1-2s gaps.
- OPENALEX: 80 /run — basis: <50 requests observed (4-5 queries + enrichment), 1s gaps, mailto pool.
- PUBMED: 60 /run — basis: sequential 1s gaps, small retmax; service ~3 req/s keyless (observed 2026-10-24).
- RAMA: 40 /run — basis: few searches + detail pages at ~3s gaps observed 2026-10-25; flaky links get 1 retry.
- RESEARCHGATE: 20 /run — basis: direct fetches near-uniformly 403 (6/6 probes 2026-10-24); ceiling forces fallback discipline.
- SCHOLAR: 12 /run — basis: 4 queries at ~9s gaps observed; bot-sensitive (unusual-traffic block on bursts). Tight by design.
- SEMANTICSCHOLAR: 50 /run — basis: per-DOI lookups at >=4s gaps; /paper/search persistently 429 keyless (observed 2026-10-25).
- SINTA: 800 /run — basis: completeness method needs up to 8 iterative passes over paged lists (10/page); 403 appears after ~50 fast requests, hence 2-3s+jitter gaps (observed 2026-09-13).
- UNPAYWALL: 200 /run — basis: runs stay <50 lookups; service limit 100k/day/email is the real bound (observed 2026-10-24).

## Compliance

- tests/run.sh replays this registry: every card source present
  exactly once, every ceiling a positive integer, exact values
  pinned (rebalancing updates file + test together).
- Blind-test agents report per-source request counts; the
  coordinator checks them against these ceilings (see STATE.md).
