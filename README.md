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

## Quickstart (5 minutes)

You need Python 3 (no packages) and this repo on disk. The
walkthrough below reproduces the shipped demo; substitute your
own topic for a real run.

```sh
# 1. Scaffold a task directory with an input contract.
scripts/vds.py init my-task --topic "cover crops and soil organic carbon" \
  --quota 3 --sources CROSSREF

# 2. Gather. Give your agent SKILL.md plus this prompt (edit the caps):
#    "Run the very-deep-search pipeline for <TOPIC> with quota <N>
#     from sources <A, B>. Contract: my-task/contract.json.
#     Write lane files to my-task/workspace/, evidence to
#     my-task/evidence/. Verify every pass record through both
#     layers, then validate, merge, and package with scripts/vds.py."
#    Quota 3 or fewer sources: the agent works inline (see the
#    subagent gate, SKILL.md section 6).

# 3. Validate, merge, package (the agent runs these; you can replay them).
#    Between merge and package the agent runs the content pass
#    (SKILL.md section 3, stage 4): it writes my-task/manifest.jsonl
#    and my-task/final.jsonl (the proof-backed subset of merged.jsonl).
scripts/vds.py validate my-task/workspace/*.jsonl --root my-task
scripts/vds.py merge a=my-task/workspace/lane-a.jsonl --keep-order a \
  --pass-only -o my-task/merged.jsonl --root my-task
scripts/vds.py package --final my-task/final.jsonl \
  --manifest my-task/manifest.jsonl --merged my-task/merged.jsonl \
  --contract my-task/contract.json --root my-task -o my-task/package
```

A `pass` claim is valid if and only if you can reproduce it
with its recorded `reverify` commands against its saved
`evidence_ref` artifact. No evidence = not counted.

Prefer watching before running? Replay the demo offline (no
network): see `examples/demo-quota3/README.md`.

## Use

The skill body is `SKILL.md`: input contract, 7 pipeline stages,
source protocol cards, record schema, orchestration rules (including
the subagent gate), failure runbook, adjudication, and packaging.
An agent follows it top to bottom; no other reading order is needed.

- `references/sources/<SOURCE>.md`: per-source protocol cards
  (20 shipped; add more following `templates/source-guide.md`).
- `examples/journal-contract.md`: a filled input-contract example.
- `examples/demo-quota3/`: a complete quota-3 task with a
  byte-exact replay check (`tests/run.sh`, section 17).
- `scripts/vds.py`: offline task tool (`init`, `validate`,
  `merge`, `package`; run with `--help`, which is authoritative).
- `tests/run.sh`: unit tests for `vds.py` (no network).

## Layout

```
SKILL.md                  skill body (start here)
README.md                 this file
CHANGELOG.md              release history
scripts/vds.py            init + validate + merge + package (stdlib-only, offline)
tests/                    fixtures + expected outputs + run.sh
templates/                source-guide skeleton, record + manifest schemas
references/sources/       per-source protocol cards (20)
examples/                 filled input-contract example + quota-3 demo
adapters/                 future non-Muse harness notes (stub)
```

## Validity rule

A `pass` claim is valid if and only if the user can reproduce it with
the recorded `reverify` commands against the saved `evidence_ref`
artifact. No evidence = not counted.
