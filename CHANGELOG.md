# Changelog

## 0.1.1 — foreign-agent hardening

Validated by an independent foreign-agent run from a clean repo
(4 proof-backed passes from 27 candidates, 4/4 `reverify` commands
reproduced by a third party, zero schema errors, zero path leaks).
That run surfaced 9 findings, all fixed here:

- `vds.py merge` gains `--pass-only` (final merge mode); §11
  documents it plus a corrected `LANE=PATH` CLI example (`--help`
  declared authoritative on drift).
- `merged.jsonl` (all passes) vs `final.jsonl` (proof-backed subset)
  vs `excluded-from-final.md` now defined distinctly (§3.5, §10).
- L1 contract requires 200 AND a non-challenge body; 200 carrying a
  JS stub, CAPTCHA, or login shell = blocked (§2, §8).
- `layer1_status` sentinel `"not_run"` blessed for unprobed rejects (§5).
- Inline fallbacks added where the text assumed subagents: merger
  cross-sample (§3.5) and same-model second-pass adjudication (§9).
- `needs-richer-check.jsonl` queue format defined (§10).
- GARUDA.md now states the canonical base domain + dead legacy
  domain (a foreign run burned 5 requests learning this).

## 0.1.0 — initial draft

- `SKILL.md`: input contract, 7-stage pipeline, record schema,
  orchestration rules with subagent gate (inline at 3 or fewer
  sources, ask above), HTTP-first escalation, failure runbook,
  adjudication, final package, prohibitions.
- `scripts/vds.py`: `validate` + `merge` (stdlib-only, offline,
  byte-deterministic). 21 unit checks green; legacy conformance:
  20/34/16 pass counts reproduced, 70-record merge reproduced at
  58 unique / 12 duplicates with identifier set exactly matching
  the independently produced final set.
- `references/sources/`: backbone protocol cards (CROSSREF,
  OPENALEX, SCHOLAR, GARUDA, DOAJ).
- `templates/`: source-guide skeleton, record + manifest schemas.
- `examples/`: filled journal-domain input contract.
- `tests/`: fixtures, expected outputs, `run.sh` runner.
- `adapters/`: stub for future harness notes.
