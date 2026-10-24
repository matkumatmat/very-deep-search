# PUBMED — Protocol Card (biomedical literature API)

> Status: behavior observed 2026-10-24. Re-probe on repeated failures.

## Access

- E-utilities base (open, no credentials):
  `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
- esearch (PMIDs):
  `esearch.fcgi?db=pubmed&retmode=json&retmax=<N>&term=<QUERY>`
  returns `esearchresult.idlist[]`.
- esummary (metadata per PMID):
  `esummary.fcgi?db=pubmed&retmode=json&id=<PMID,...>` returns
  `result[<uid>].{title, fulljournalname, pubdate,
  articleids[], authors[]}`.
- efetch (abstracts for screening):
  `efetch.fcgi?db=pubmed&retmode=xml&id=<PMID,...>` returns
  `PubmedArticle` with `ArticleTitle`, multi-part
  `AbstractText`, `ELocationID[@EIdType=doi]`,
  `PublicationType`.
- Record landing: `https://pubmed.ncbi.nlm.nih.gov/<PMID>/` —
  use as the evidence URL (always openable, no paywall).

## Identity & auth

- No key required (~3 req/s without one; 10 req/s with
  `api_key`). Browser-like UA on all calls.

## Rate limits & courtesy

- Sequential, `sleep 1s` between calls, small `retmax`
  (5-40). No burst.

## Anti-bot & standard response

- None from NCBI — no captcha, no 403 observed.
- Publisher landings are the trap: observed blockers return
  HTTP 403 to curl for VALID DOIs while the `doi.org/<DOI>`
  redirect itself lands on the correct article URL. Strict
  status: REJECTED (no observed HTTP 200) + recommend
  browser re-verification at merge. Never pass on a correct
  redirect alone.

## Parser notes

- `esummary.articleids[]` always carries the PMID; the DOI
  sits in `idtype: doi` for most modern articles. Old
  records without any DOI are automatically out of quota.
- The Crossref title may be in the original language while
  PubMed carries the translation — judge the L2 match by
  meaning, not identical strings.
- Never include from title alone: screen every efetch
  abstract against the inclusion criteria (unit-level
  outcome vs individual-level vs mapping review).

## Traps

- Biomedical corpus: generic terms skew technical ("control
  system" hits devices/IoT) or collide with clinical senses
  of common words ("center" hits surgery literature).
  Expect noise; abstract screening is mandatory.
- Over-constrained exact-combined queries return 0 — a zero
  proves phrasing failure, not literature absence. Loosen
  deliberately.
- Spelling variants can explode into six-figure false
  positives — avoid blind variant expansion here.
- Mapping/systematic reviews do not test influence — screen
  them out unless reviews are explicitly includable.

## Fallback chain

- E-utilities cover all discovery + metadata; PubMed HTML
  scraping is never needed. Dorking is irrelevant for
  discovery.
- Browser ONLY for Layer-1 re-verification of anti-bot
  publisher landings (never for discovery).

## Retry budget

- Standard: 1x retry from a different angle, then verdict.

## Example

> Topic-specific values below are illustration only.

- esearch: `"<EXACT PHRASE>"` (main pool), `"<PHRASE>" AND
  (<UNIT> OR <UNIT> OR <UNIT>)` for unit-scoped variants.
- Pipeline: esearch -> esummary (DOI) -> efetch (abstract)
  -> unit-vs-individual screening -> 2-layer verification.

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
