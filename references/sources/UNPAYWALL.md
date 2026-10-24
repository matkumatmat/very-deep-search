# UNPAYWALL — Protocol Card (per-DOI open-access lookup)

> Status: behavior observed 2026-10-24. Re-probe on repeated failures.

## Access

- Unpaywall is NOT a search engine: the public endpoint is
  per-DOI lookup only — no keyword search exists. Discovery
  runs through Crossref/OpenAlex (or a known DOI list);
  Unpaywall enriches each DOI with OA status + fulltext
  location. Lane flow: discovery -> DOI list -> Unpaywall
  v2 per DOI -> 2-layer verification -> staging.
- REST: `GET https://api.unpaywall.org/v2/<DOI>?email=<EMAIL>`
  returns one JSON object: `doi`, `doi_url`, `title`,
  `genre`, `year`, `published_date`, `is_oa`, `oa_status`
  (gold|green|bronze|hybrid|closed), `best_oa_location`
  (`.url_for_landing_page` / `.url` -> the evidence URL),
  `journal_name`, `journal_issns`, `publisher`,
  `z_authors[].raw_author_name`.
- Docs: `https://unpaywall.org/products/api`.
- Codeless alternative: the Simple Query Tool (paste up to
  1,000 DOIs on the site, results arrive via email).
- Bulk alternative: the database snapshot (download, not API).
- OpenAlex consumes Unpaywall as one OA surface; the two
  are complementary (OpenAlex: discovery + embedded OA;
  Unpaywall: `oa_status` granularity + version/embargo
  history via `oa_locations`).

## Identity & auth

- Contact email is REQUIRED as a query param; missing or
  invalid email -> HTTP 422. Disposable/`example.com`
  domains are rejected — use the operator's real
  contactable address via env/placeholder, never hardcoded.
- Identified UA with `mailto:` on every call.

## Rate limits & courtesy

- 100,000 requests/day/email. A full lane run stays under
  ~50 — negligible, but still: sequential, >=1s gaps, no
  parallel burst.
- Above ~10k DOIs/day: download the snapshot instead of
  hammering the API. Never scrape `unpaywall.org` HTML
  for mass lookup.

## Anti-bot & standard response

- None on the API. Browser ONLY when a publisher landing
  challenges (Cloudflare "Just a moment", login session,
  JS render) — the API path itself never needs one.

## Parser notes

- `closed` articles still return a record (no OA location)
  — useful as DOI-existence confirmation + comparison
  metadata, not as failure.
- Unpaywall-vs-Crossref title identity is a strong-match
  signal for the L2 verdict.

## Traps

- Migrating publisher domains: a resolver chain may end at
  the publisher HOMEPAGE instead of the article page.
  Never pass on a blind chain — probe the canonical
  article URL separately (OJS pattern
  `/index.php/<journal>/article/view/<id>`) and confirm
  the `<title>` carries the article title before passing.
- Publisher anti-bot (403) with a matching L2 is a
  contractual L1 fail: reject with explicit reason +
  browser-rehab path, never evade.
- Discovery-side noise (standards, templates, preprints
  from long-tail queries) needs manual filtering to the
  inclusion criteria BEFORE verification burns requests.

## Fallback chain

- Crossref/OpenAlex for discovery; Unpaywall for OA proof;
  doi.org + Crossref for the 2-layer contract; Simple
  Query Tool for codeless mass checks; snapshot for bulk.

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- Discovery: Crossref `/works?query=<BILINGUAL TERMS>&rows=8
  &select=DOI,title,author,published,container-title,publisher`.
- Enrichment: `/v2/<DOI>?email=<CONTACT>` sequential;
  store `oa_status` + `best_oa_location` as OA proof.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
