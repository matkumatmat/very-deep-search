---
name: very-deep-search
description: Multi-agent gather-and-verify pipeline for deep literature search: gather candidates from many sources in parallel, verify each through two independent layers with saved evidence, merge deterministically, adjudicate disagreements, and package a verifiable final set.
---

# Very Deep Search

A battle-tested pipeline for deep search tasks where every claimed result
must be independently verifiable by the user. Designed for
literature/journal gathering; adaptable to any domain with verifiable
identifiers.

## 1. When to use

Use this skill when the task is: collect N verified items from multiple
sources, with evidence, deduplicated, and packaged for audit. Typical
signals: "gather N verified journals/papers", "collect with proof",
"deduplicated final set".

Do not use for: single-source lookups, casual browsing, or tasks where
unverified answers are acceptable.

## 2. Input contract

Do not start gathering until all of these are fixed:

- `topic`: the research topic or query scope.
- `inclusion` / `exclusion`: explicit criteria. Every record's `decision`
  must cite which criterion it meets or violates.
- `source_registry`: list of sources. Each source needs a protocol card
  (see §4) before it is gathered.
- `quota`: total target plus per-lane/per-source targets.
- `over_gather_ratio`: default 1.5x quota (attrition from anti-bot and
  dead identifiers is normal, not failure).
- `verification_contract`: the domain's Layer 1 (locator resolution) and
  Layer 2 (independent metadata match). For journals: L1 = identifier
  resolver returns HTTP 200 at the correct landing page AND the body is
  a real page (article markers present); a 200 carrying a JS-challenge
  stub, CAPTCHA, login shell, or empty frame = blocked: fail L1 and
  queue for richer check. Never trust status alone — sniff the body.
  L2 = authoritative metadata (title + year) matches the candidate.
- `evidence_budget`: evidence per claim is mandatory; trim bulky raw
  evidence so agent handoffs stay small.

## 3. Pipeline stages

1. **Registry**: fix the input contract (§2).
2. **Per-source gather (fan-out)**: one worker per source, each writing
   only to its own temp staging file (`<lane-tmp>/<lane>-<source>.tmp.jsonl`).
   Workers read this skill plus their source's protocol card.
3. **Lane synthesis (fan-in)**: one synthesis step per lane merges temp
   files into `<workspace>/<lane>.jsonl` with lowercase-normalized
   dedup. Subagents never write lane files directly.
4. **Content pass**: download/read the underlying content for each `pass`
   record; verify the content matches the claim; store artifacts plus a
   short evidence quote (max 300 chars) in a manifest. Minimum
   artifact: the full text when reachable (PDF or extracted text);
   when the full text is inaccessible but the landing body carries
   article markers and authoritative metadata confirms the claim, a
   trimmed metadata snapshot plus the body-marker note is acceptable —
   label which kind each manifest row holds in its reason. Failures
   are classified (`download_failed` + reason), never forced.
5. **Global merge + gate**: validate schema of every lane file, then
   merge with deterministic keep-order into `merged.jsonl` (all `pass`
   rows — use the tool's pass-only mode). `final.jsonl` is NOT tool
   output: you hand-write it during the content pass as the
   proof-backed subset whose content artifacts verified relevant;
   rows in merged-but-not-final are listed with reasons in
   `excluded-from-final.md`. Rejects stay in lane files as coverage
   proof. Re-resolve a cross-sample of identifiers the merger never
   checked; inline, where gatherer and merger are the same agent,
   re-resolve a small sample yourself and label it as such. Any flip
   is recorded with reason.
6. **Adjudication**: an independent judge re-scores a sample or the full
   set on two separate facets plus an overall choice; every
   judge-vs-gather disagreement is adjudicated (`keep`/`flip` + reason).
   Facet-vs-choice paradox is a prompt bug signal, not a data signal.
7. **Final package**: a complete verified archive, a proof-backed final
   subset, a manifest, a README, and a rejected-with-reasons file.
   Metadata-only records are excluded explicitly, never silently.

## 4. Source protocol cards

Every source must have a protocol card at `references/sources/<SOURCE>.md`
before gathering. If none exists, write it first
(document-before-gather). The registry key is the card basename
(`ARXIV.md` → `ARXIV`); use exactly that in `contract.json` and
`vds.py init --sources`. Each card (max 100 lines):

- Access vectors and exact endpoints/parameters, including the canonical
  base domain plus any known-dead legacy domains (never a bare
  placeholder where a real domain is known).
- Authentication/identity requirements (polite pools, contact emails via
  env vars, API keys via env vars — never hardcoded).
- Rate limits and courtesy delays, observed empirically.
- Known anti-bot behaviors and the standard response.
- Parser notes (selectors, pagination, encoding traps).
- Fallback chain when the primary path is down.
- Retry budget: probe 1x for status, 1x retry for ambiguous results from
  a different angle, backoff on 429, then STOP and switch angles —
  never hammer the same door. Per-source request ceilings per run
  live in `references/budgets.md` (policy; exceeding one mid-run
  means stopping that source, not raising it silently).

Run log: append each run (timestamp, queries, counts, failures) to the
card's log section or a sibling log file. Honest provenance: what was
not recorded is marked `not recorded` — never invented.

## 5. Record schema

One JSON object per line. Generic field names; instantiate per domain:

- `identifier`: the canonical ID, lowercase-normalized for dedup.
- `title`, `source_url`, plus domain metadata fields. Record the
  canonical `source_url`: strip session/query params the site appends
  per resolve (re-record if the canonical form changes).
- `layer1_status`: observed locator-resolution status, recorded as-is.
  For `reject` rows screened out before probing, the explicit sentinel
  is `"not_run"`.
- `layer2_match`: boolean, independent metadata match.
- `decision`: `pass` or `reject` only.
- `reason`: cites the criterion and the observed evidence.
- `reverify`: exact commands that reproduce the verification
  (mandatory for `pass`).
- `evidence_ref`: path (workspace-relative) to saved evidence
  (mandatory for `pass`).

Rules: no evidence = not counted. `pass` with empty `reverify` or a
missing evidence file is rejected by validation. Rejected records are
kept with reasons — they prove coverage. `reject` rows still carry
every field: use `evidence_ref: ""` and `reverify: []`. For rejects
screened before probing, `layer1_status` is `"not_run"` and
`layer2_match` is `false`, with the reason noting L2 was not run.
`layer1_status` for `pass` is the observed success (`200`, or an
equivalent success string such as `"200-ok"`); for `reject` it is
the observed failure (`404`, `403`, a challenge note) or `"not_run"`.

## 6. Orchestration

- **Subagent gate**: with 3 or fewer sources, the main agent works
  inline. With more than 3, the main agent must ask the user before
  fanning out to subagents (subagents-driven vs inline). The threshold
  (default 3) is overridable per project.
- **Naming**: workers are named `<lane>-<source>`; lanes own disjoint
  file sets. Inline (gate not triggered) with 2-3 sources: still write
  one lane file per source (`lane-a.jsonl`, `lane-b.jsonl`, ...), note
  the source-to-lane mapping in the run notes, and merge with
  `LANE=PATH` labels as usual.
- **Write isolation**: workers write only temp files; only synthesis
  writes lane files; only the merger writes the final file. No
  exceptions.
- **Progress signaling**: file-based markers (e.g. `<LANE>-DONE`,
  `NEED-HELP`, `MERGED`) plus staging file line counts. Do not trust
  "accepted" statuses without log/file confirmation.
- **Shared resources**: exactly one lock file per shared resource
  (protocol: HELD/FREE + expiry + START/END markers). Shared output
  directories use skip-if-identical (byte comparison), never blind
  overwrite.
- **Handoffs**: every worker returns a structured summary
  (candidates/passed/rejected + ID list). Retrospectives record
  failures explicitly, including total failures with zero output.

## 7. HTTP-first escalation

API/plain-HTTP first. Escalate to richer methods (browser, JS rendering,
sessions) only for verified blocks: anti-bot challenges, login walls,
JS-only pages. Claims that are substantively valid but
infrastructurally blocked are queued (`needs_richer_check`, see §10),
never silently passed or silently dropped — recovery is a later
explicit pass. Total tool unavailability is reported as zero output,
not claimed as partial success.

## 8. Failure runbook

Expect and classify (do not retry blindly):

- **Anti-bot**: 403/444 challenges, JS proof-of-work, bare redirects
  without Location, IP blocks. Response: stop, record status as-is,
  queue for richer check.
- **Challenge bodies**: HTTP 200 carrying a JS stub, CAPTCHA page,
  login shell, or empty frame is a BLOCK, not a pass: fail Layer 1,
  queue for richer check. Status 200 without article markers proves
  nothing.
- **Infrastructure**: DNS failures, domain migrations (probe aliases),
  total maintenance pages, throttling (backoff, then stop), shared
  egress-IP throttling (switch discovery to a backbone source).
- **Data**: dead identifiers (resolver 404 + authority empty),
  retroactive re-deposits (tolerate with annotation, do not
  auto-reject), hijacked domains, cross-publication content duplicates
  (check manually — ID dedup will not catch them), identifier-like
  strings that belong to something else (e.g. bibliography entries).

Over-gather exists because of this taxonomy. Classify, record, move on.

## 9. Adjudication

An independent judge (different model/pass) scores records on two
separate facets (e.g. topic-fit, criterion-fit) plus one overall choice
(include/exclude/uncertain). Design the choice criteria as explicitly
as the facet prompts. Inline single-model fallback: run a structured
second pass that re-reads the criteria fresh, scores the same facets +
choice, and labels the output as same-model adjudication with its
limitation. Disagreements between gather verdicts and judge verdicts
are each adjudicated with a recorded `keep`/`flip` decision and reason.
Title-only records (no abstract/content) carry low confidence.

## 10. Final package

- `merged.jsonl`: every passing record with verdicts (all lanes).
- `final.jsonl`: the proof-backed subset (content artifacts verified).
- `excluded-from-final.md`: merged-but-not-final rows with reasons.
- `needs-richer-check.jsonl`: queued items, one row each
  (`identifier`, `reason`, `queued_by`, `status`: one of
  queued/promoted/dropped).
- Manifest: one row per artifact (identifier, filename, source URL,
  size, evidence quote, verdict).
- Excluded-with-reasons file for adjudicated disputes.
- README describing contents and reproduction steps.

Package deterministically: same inputs produce byte-identical outputs.

## 11. Scripts

`scripts/vds.py` (Python 3, standard library only, offline,
deterministic):

- `vds.py init <task-dir> --topic <t> --quota <n>
  --sources <a,b> [--per-source <n>] [--over-gather <r>]
  [--inclusion <c>]... [--exclusion <c>]... [--l1 <t>] [--l2 <t>]
  [--evidence-budget <t>] [--force]`: writes `contract.json`
  (byte-exact for the same arguments) plus `workspace/` and
  `evidence/`; journal-domain defaults, overridable. Refuses an
  existing contract without `--force`. Exit 0 ok, 1 refused,
  2 bad usage.
- `vds.py validate <files...>`: schema, decision enum, identifier
  format, intra-file dedup, mandatory evidence + reverify for `pass`.
  Exit 0 clean, 1 errors found, 2 bad usage.
- `vds.py merge LANE=PATH ... --keep-order <lanes> -o <out>
  [--report <file>] [--pass-only]`: validates first (invalid input
  refuses the merge), global dedup with deterministic keep-order,
  duplicate report. Merges every row given by default; `--pass-only`
  restricts to `pass` rows. The final merge always uses `--pass-only`.
  Name lanes `lane-a`, `lane-b`, ... in contract source order;
  `--keep-order` must list the same labels. Byte-deterministic output.
- `vds.py package --final <f> --manifest <m> -o <out-dir>
  [--merged <f>] [--contract <c>] [--excluded <md>]
  [--needs-richer <f>] [--disputes <md>] [--root <dir>]
  [--evidence-dir <dir>] [--force]`: validates final (+ merged,
  manifest rows, needs rows), requires one manifest row per final
  `pass` identifier, then assembles the package (copies +
  evidence + generated README). Any error refuses the package
  and writes nothing. Refuses a non-empty output dir without
  `--force`. All bracketed flags are optional; omitted files are
  listed as not provided in the generated README.
  Exit 0 ok, 1 errors found, 2 bad usage.

Example:

```sh
vds.py init my-task --topic "<TOPIC>" --quota 3 --sources CROSSREF,OPENALEX
vds.py merge lane-a=a.jsonl lane-b=b.jsonl --keep-order lane-a,lane-b -o merged.jsonl
```

Run `vds.py --help` for the interface. Agents must be able to use it
without reading its source. When this section and `--help` disagree,
`--help` wins — and report the drift as a skill bug.

## 12. Prohibitions

- No pirated/login-bypass sources in any registry.
- No secrets, credentials, contact emails, or absolute filesystem paths
  in skill files. Use workspace-relative paths and `<PLACEHOLDERS>` /
  env vars.
- No session dumps, personal data, or research corpora in the skill
  package.
- No force-downloading paywalled or access-controlled content.
- No burst traffic: every source interaction follows its card's
  courtesy rules.
