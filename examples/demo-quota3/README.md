# Demo: quota-3 task (redacted)

A complete minimal task: contract, one lane file with 3 verified
passes, trimmed evidence artifacts, manifest, merged/final sets,
and the expected package output. Identifiers are real and were
verified by the maintainer on 2026-10-25 (L1: resolver HTTP 200
at the article page; L2: Crossref title+year match). Evidence
artifacts are redacted to verdict-supporting fields only.

Topic and records are illustration, not a literature review:
do not cite this demo as coverage of the topic.

Tiers: all 3 records are Tier B (metadata snapshots, no full
text) and the contract sets `min_tier_a: 0` to document that
choice — quota normally counts Tier A only (see SKILL.md
section 3, stage 4). The replay therefore also proves that a
documented all-Tier-B package assembles cleanly.

## Replay (offline, no network)

From the repository root:

```sh
scripts/vds.py validate examples/demo-quota3/workspace/lane-a.jsonl \
  --root examples/demo-quota3
scripts/vds.py merge a=examples/demo-quota3/workspace/lane-a.jsonl \
  --keep-order a --pass-only -o /tmp/demo-merged.jsonl \
  --root examples/demo-quota3
scripts/vds.py package --final examples/demo-quota3/final.jsonl \
  --manifest examples/demo-quota3/manifest.jsonl \
  --merged examples/demo-quota3/merged.jsonl \
  --contract examples/demo-quota3/contract.json \
  --excluded examples/demo-quota3/excluded-from-final.md \
  --needs-richer examples/demo-quota3/needs-richer-check.jsonl \
  --root examples/demo-quota3 -o /tmp/demo-package
diff -r examples/demo-quota3/package-expected /tmp/demo-package \
  && echo REPLAY-IDENTICAL
```

Expected: validate `pass=3 ... errors=0`, merge `records=3
unique=3 duplicates=0`, package `final=3 manifest=3
evidence=3`, and a byte-identical replay.

## Re-verify (needs network)

Run any record's `reverify` commands from
`workspace/lane-a.jsonl` and compare against its file under
`evidence/`. Publisher pages change over time: a future
mismatch is new information, not a demo bug — record what
you observe.
