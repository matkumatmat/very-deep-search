# CORE — Protocol Card (OA aggregator, keyed API + guarded search)

> Status: behavior observed 2026-10-24. Re-probe on repeated failures.

## Access

- Public site: `https://core.ac.uk/` (homepage stable, HTTP 200).
- Search: `https://core.ac.uk/search?q=<keyword>` (see Anti-bot).
- Record file: `https://core.ac.uk/download/pdf/<numeric-id>.pdf`
  (legacy variant `/download/<id>.pdf` still indexed).
- Metadata page: `https://core.ac.uk/outputs/<numeric-id>/`.
- API v3: `https://api.core.ac.uk/v3/search/works` (also
  `search/outputs`, `outputs/<id>/download`); docs at
  `https://api.core.ac.uk/docs/v3` (open, 200); key signup at
  `https://core.ac.uk/api`.
- CORE harvests institutional repositories, OA journals, and
  national repositories — it is an aggregator, not a publisher.

## Identity & auth

- API key is REQUIRED: header `Authorization: Bearer <KEY>` or
  `api_key=<KEY>` param. Signup needs email + human confirmation.
- Autonomous agents MUST NOT self-register a key (human step).
  For a full API run the coordinator supplies `CORE_API_KEY`
  via env, then:
  `curl -H "Authorization: Bearer $CORE_API_KEY"
  "https://api.core.ac.uk/v3/search/works?q=...&limit=50"`.
- Without a key the API answers a Cloudflare redirect page
  (`cdn-cgi`), not JSON. Dataset dumps are registered-only.

## Rate limits & courtesy

- API calls count against quota; PDF downloads are expensive —
  never render/download a CORE PDF unless needed.
- Discovery APIs: polite mailto/UA + 1-2s delays; `per-page<=50`.
- Semantic Scholar without a key 429s easily on shared IPs:
  sleep >=4s, stop on persistent 429, and never drain quota
  owned by another lane's worker.

## Anti-bot & standard response

- Cloudflare 403 `Just a moment...` on `/search` and `/outputs/*`
  for curl — even with full browser headers. Only `/` is stable.
- Standard response: do not re-hammer; use the keyed API or a
  controlled browser. A curl 403 is NEVER negative evidence that
  a record does not exist.

## Parser notes

- Result mix is heavy on theses, dissertations, working papers,
  and reports — for journal quota, theses MUST be filtered out
  (usually DOI-less).
- A valid CORE record pattern is `download/pdf/<id>.pdf` or
  `outputs/<id>/` — record the CORE URL as the evidence URL,
  not the publisher URL.
- Author-name spelling can differ between the CORE PDF and the
  publisher page — use the publisher version, note the variant.

## Traps

- Publisher redeposit (journal moves publisher) can corrupt the
  Crossref year: always cross-check the year against the
  publisher's `Vol/No` archive before deciding the L2 match.
- Small-publisher hosts can be fully dead (`curl 000` on http
  and https) — record `resolver_status: 0` with reason, NEVER
  pass on metadata alone.
- Legacy OJS URLs may redirect to the site homepage: a DOI that
  "resolves" to an index page fails L1 (not an article page).
- OpenAIRE does NOT ingest CORE — it is unsuitable as CORE
  membership proof (fine as generic discovery only).

## Fallback chain

- Tiered keyless discovery: (1) candidates from OpenAlex /
  Semantic Scholar / Crossref; (2) CORE membership proof from
  the search-engine index (`site:core.ac.uk`, `"<title>"
  core.ac.uk`); (3) 2-layer curl verification per DOI.
  Skipping tier (2) is acceptable when L1+L2 pass on the DOI
  directly — note the skip in `reason`. Probes minimal: root /
  search / outputs once each; per-title queries, never a crawl.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Keyed: `v3/search/works?q=<TERMS>&limit=50` with bearer key.
- Keyless: backbone discovery + `site:core.ac.uk` membership
  check + L1 (`doi.org/<DOI>` must end 200 at the ARTICLE page)
  + L2 (Crossref title/year match).

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
