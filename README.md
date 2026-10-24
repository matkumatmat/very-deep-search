# very-deep-search

Multi-agent gather-and-verify pipeline for deep literature search:
collect candidates from many sources, verify each through two
independent layers with saved evidence, merge deterministically,
adjudicate disagreements, and package a verifiable final set.

## Install

From a clone of this repository:

```sh
muse skills install <path-to>/very-deep-search
```

Then verify:

```sh
muse skills validate <path-to>/very-deep-search --json
```

Expected: `valid: true` with zero diagnostics and warnings.

## Use

The skill body is `SKILL.md`: input contract, 7 pipeline stages,
source protocol cards, record schema, orchestration rules (including
the subagent gate), failure runbook, adjudication, and packaging.
An agent follows it top to bottom; no other reading order is needed.

- `references/sources/<SOURCE>.md`: per-source protocol cards
  (backbone set included; add more following `templates/source-guide.md`).
- `examples/journal-contract.md`: a filled input-contract example.
- `scripts/vds.py`: offline validator + deterministic merger
  (`validate`, `merge`; run with `--help`).
- `tests/run.sh`: unit tests for `vds.py` (no network).

## Layout

```
SKILL.md                  skill body (start here)
README.md                 this file
CHANGELOG.md              release history
scripts/vds.py            validate + merge (stdlib-only, offline)
tests/                    fixtures + expected outputs + run.sh
templates/                source-guide skeleton, record + manifest schemas
references/sources/       per-source protocol cards
examples/                 filled input-contract example
adapters/                 future non-Muse harness notes (stub)
```

## Validity rule

A `pass` claim is valid if and only if the user can reproduce it with
the recorded `reverify` commands against the saved `evidence_ref`
artifact. No evidence = not counted.
