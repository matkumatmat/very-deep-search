# OPENALEX — Protocol Card

> Status: behavior observed 2026-10. Re-probe on repeated failures.

## Access

- Search: `GET https://api.openalex.org/works?search=<query>&per-page=<N>&select=<fields>`
- Detail: `GET https://api.openalex.org/works/https://doi.org/<DOI>`
- Open data (CC0), no login/token. Indexes small publishers that
  Western aggregators miss, plus non-English journals.

## Identity & auth

- Polite pool: `User-Agent: <project> (mailto:$VDS_CONTACT_EMAIL)`
  gives ~10 req/s + priority. Anonymous pool is slow.
  Collect the address at the SKILL.md §2 pre-flight interview gate.

## Rate limits & courtesy

- Sequential, 1s delay between requests (well under the limit).
- No parallel burst. A full source run is typically under 50 requests.

## Anti-bot & standard response

- None on the API. Publisher-side Layer-1 failures (403, DNS,
  timeouts) are recorded as-is on the record, not an OpenAlex problem.

## Parser notes

- `search=` is relevance-ranked (title+abstract), NOT date-ordered:
  always take `publication_year` from metadata.
- `select` is mandatory for economy (without it, responses include
  the huge `abstract_inverted_index`). Suggested:
  `id,doi,title,publication_year,authorships,primary_location,cited_by_count,type`
- `doi: null` (old books, theses): drop before verification.
- `primary_location.landing_page_url` is the best `source_url`;
  fallback `https://doi.org/<DOI>` when null.
- Dead DOIs stay indexed: never skip two-layer verification.

## Fallback chain

- OpenAlex is a discovery backbone for throttled sources (it carried
  discovery when another aggregator's search endpoint returned
  persistent 429 from a shared egress IP).

## Retry budget

- Recheck every ambiguous L1 status (406/302/403/DNS) at least 2x
  (default UA, then browser UA) before a reject verdict.

## Example

> Topic-specific values below are illustration only.

- `search=<TOPIC TERMS>&per-page=15&select=id,doi,title,publication_year,authorships,primary_location`
- Screen titles against unit-vs-individual criteria BEFORE verifying
  (saves requests); shortlist ~12-15 DOIs for two-layer verification.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
