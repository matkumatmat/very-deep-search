# Support matrix: protocol cards

One row per card: when it was last verified, by which blind run,
the verdict, and the content tier the run achieved. Verdicts:

- `PASS` — blind run met quota from this card; per-card verdict
  recorded with observed evidence. Evidence path + date cited.
- `FAIL` — blind run could not meet quota from this card (see
  notes; patched or exemption-recorded before this row flips).
- `EXERCISED` — card used in a passing pipeline run, but no
  per-card verdict was recorded (weaker than PASS).
- `LEGACY` — verified before this program kept /tmp artifacts;
  claim rests on the cited release note, not on artifacts.
- `PENDING` — scheduled, no run yet.

Tier column: `A` = full text retrieved with a relevance quote
in free-agent hands; `B` = metadata-only (honest, never
content-verified). Retroactively assessed rows say so.

Evidence rule: every `PASS`/`FAIL` row cites blind-run artifacts
under `/tmp` by path + date. No evidence = no verdict.

## Rows

| Card | Last verified | Model | Verdict | Tier | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| ARXIV | 2026-10-25 | opencode/nemotron-3-ultra-free | PASS | B | /tmp/blindtest3/work/gnn-traffic/package (2026-10-25) | F3.1 sampled run; tier B assessed retroactively (metadata snapshots); anti-bot split patched from its verdict |
| BASE | 2026-10-25 | opencode/nemotron-3-ultra-free | PASS | B | /tmp/p5a/work/air-pollution-asthma-retro/package (2026-10-25) | P5 batch A quota-1; retrofit (metadata snapshot, title quote); requests 3 vs ceiling 80 |
| CORE | 2026-10-25 | opencode/nemotron-3-ultra-free | PASS | B | /tmp/p5a/work/air-pollution-asthma-retro/package (2026-10-25) | P5 batch A quota-1; retrofit (metadata snapshot, title quote); requests 3 vs ceiling 60 |
| CROSSREF | 2026-10-25 | muse-subagent (same-model) | EXERCISED | — | /tmp/blindtest/work/biochar-task/package (2026-10-25) | Phase-2 pipeline blind; no per-card verdict recorded |
| DOAJ | 0.1.1 foreign-agent run | foreign (pre-program) | LEGACY | — | none retained | CHANGELOG 0.1.1; needs a fresh blind run for strict compliance |
| EUROPEPMC | 2026-10-25 | opencode/nemotron-3-ultra-free | PASS | B | /tmp/p5a/work/air-pollution-asthma-retro/package (2026-10-25) | P5 batch A quota-1; primary API worked first try; retrofit (metadata snapshot, title quote); requests 3 vs ceiling 40 |
| GARUDA | 0.1.1 foreign-agent run | foreign (pre-program) | LEGACY | — | none retained | CHANGELOG 0.1.1 (canonical/dead-domain fix from that run); needs a fresh blind run for strict compliance |
| ISJD | — | — | PENDING | — | — | Phase 5 batch B (native tier schema) |
| MORAREF | 2026-10-25 | opencode/nemotron-3-ultra-free | PASS | B | /tmp/blindtest3/work/gnn-traffic/package (2026-10-25) | F3.1 sampled run; tier B assessed retroactively (metadata snapshots) |
| NELITI | — | — | PENDING | — | — | Phase 5 batch B (native tier schema) |
| ONESEARCH | — | — | PENDING | — | — | Phase 5 batch B (native tier schema) |
| OPENAIRE | — | — | PENDING | — | — | Phase 5 batch C (native tier schema) |
| OPENALEX | 2026-10-25 | muse-subagent (same-model) | EXERCISED | — | /tmp/blindtest/work/biochar-task/package (2026-10-25) | Phase-2 pipeline blind; no per-card verdict recorded |
| PUBMED | 2026-10-25 | opencode/nemotron-3-ultra-free | PASS | B | /tmp/p5a/work/air-pollution-asthma-retro/package (2026-10-25) | P5 batch A quota-1; E-utilities worked; retrofit (metadata snapshot, title quote); requests 3 vs ceiling 60 |
| RAMA | 2026-10-25 | opencode/nemotron-3-ultra-free | PASS | B | /tmp/blindtest3/work/gnn-traffic/package (2026-10-25) | F3.1 sampled run; tier B assessed retroactively (metadata snapshots) |
| RESEARCHGATE | — | — | PENDING | — | — | Phase 5 batch C (native tier schema) |
| SCHOLAR | 0.1.1 foreign-agent run | foreign (pre-program) | LEGACY | — | none retained | CHANGELOG 0.1.1; needs a fresh blind run for strict compliance |
| SEMANTICSCHOLAR | — | — | PENDING | — | — | Phase 5 batch C (native tier schema) |
| SINTA | — | — | PENDING | — | — | Phase 5 batch B (native tier schema) |
| UNPAYWALL | — | — | PENDING | — | — | Phase 5 batch C (native tier schema) |
