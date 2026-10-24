# Changelog

## Unreleased — artifact tiers (Phase 5)

- Content tiers: every pass row carries `tier` (`"A"` = full
  text retrieved with a relevance quote, `"B"` = metadata-only
  with a `tier-b-block:` cause). A saved abstract alone is
  Tier B: abstracts screen, only full text verifies.
- Contract `min_tier_a` (`vds.py init --min-tier-a`, default:
  quota total — quota counts Tier A unless explicitly
  lowered); `vds.py package` refuses Tier-A shortfalls.
- Enforcement: `validate` checks tier labels + block tokens;
  `package` checks Tier-A quotes + quota. BREAKING at
  validation: pre-tier lane files fail until migrated (add
  tier labels; the demo shows the Tier-B pattern).
- Demo migrated to documented all-Tier-B (`min_tier_a: 0`).
- Tests: 57 → 72 checks, all offline.

## 1.0.0 — publish hardening

- `SKILL.md` frontmatter: `license`, `compatibility`
  (muse/opencode/claude), `metadata`. License MIT, author
  matkumatmat (human-confirmed); see `LICENSE`.
- `README.md`: per-harness install instructions with
  verified-vs-expected labels, harness support matrix,
  license line.
- `CONTRIBUTING.md`: new-card end to end (template, 100-line
  rule, budgets entry, blind mini-gate) plus PR and issue
  templates under `.github/`.
- `adapters/` stub removed: harness mapping now lives in
  README Install + Harness support.
- Clean-clone install verified on Muse Code and OpenCode;
  Claude Code discovery expected, untested.
- Author + MIT license (human-confirmed).

## 0.2.0 — Runner UX

- `vds.py init`: scaffold a task directory with a byte-exact
  `contract.json` (journal-domain defaults, overridable) plus
  `workspace/` and `evidence/`.
- `vds.py package`: verify (final, manifest rows with byte-size
  checks, needs rows, manifest coverage) then assemble the
  deterministic final package with a generated README; refuses
  on any error and writes nothing.
- `README.md`: 5-minute quickstart with a paste-ready agent
  prompt; `examples/demo-quota3/`: complete quota-3 task
  (3 real verified DOIs, redacted evidence) with a byte-exact
  replay check.
- `SKILL.md` §11 documents `init` + `package` (`--help` stays
  authoritative). Tests: 24 → 54 checks, all offline.

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
