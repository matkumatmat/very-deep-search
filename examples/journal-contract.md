# Example: journal-domain input contract

A filled input contract (§2 of SKILL.md) for a journal-gathering task.
Replace every `<PLACEHOLDER>`; delete this paragraph in real use.

## Contract

- `topic`: `<RESEARCH TOPIC, e.g. effect of <X> on <Y> in <Z>>`
- `inclusion`:
  - I1: studies that test or discuss `<X>` against `<Y>` measured at
    the work-unit level (unit, division, branch, or organization
    acting as a unit), with data (empirical, review-of-evidence, or
    formal modeling with stated data).
- `exclusion`:
  - E1: individual-level outcomes (personal/employee/managerial
    performance), even when the title mentions `<X>`.
  - E2: opinion pieces without data.
  - E3: duplicate identifiers (keep first by keep-order).
  - E4: identifiers failing two-layer verification.
  - E5: sources outside the registry without coordinator approval.
- `source_registry`: `<e.g. CROSSREF, OPENALEX, GARUDA>` — each needs
  a card under `references/sources/` before gathering.
- `quota`: `<TOTAL, e.g. 50>` unique passing journals; per-source
  targets `<e.g. 3+ each>`.
- `over_gather_ratio`: 1.5 (raise to 2.0 for sources with observed
  Layer-1 attrition above 50%).
- `verification_contract`:
  - L1: `curl -s -o /dev/null -w "%{http_code} %{url_effective}" -m 40
    -L -A "<UA>" "https://doi.org/<DOI>"` must end HTTP 200 at the
    article landing page. Anything else = fail.
  - L2: `curl -s "https://api.crossref.org/works/<DOI>"` title + year
    must match the candidate. Mismatch = fail.
- `evidence_budget`: one staging row + one evidence artifact per
  claim; trim raw API dumps to the fields that support the verdict.

## Record illustration (one row)

```json
{
  "decision": "pass",
  "evidence_ref": "evidence/<SANITIZED-ID>.json",
  "identifier": "<DOI, lowercase>",
  "layer1_status": 200,
  "layer2_match": true,
  "reason": "meets I1 (<unit-level DV>); L1 200 at article page; L2 title+year match",
  "reverify": [
    "curl -sIL \"https://doi.org/<DOI>\"",
    "curl -s \"https://api.crossref.org/works/<DOI>\""
  ],
  "source_url": "<article landing page>",
  "title": "<article title>"
}
```

## Lane split illustration

- Lane A (national sources, target 20+), Lane B (aggregator APIs,
  target 20+), Lane C (web discovery + merge, target 10+).
- Fewer than 4 sources total: work inline per the subagent gate
  (SKILL.md §6) instead of fanning out.
