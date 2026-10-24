# STATE — resumable program state

`finalize!` reads this file first. Keep it current; it is the only
memory a fresh session has.

## Current

- phase: 1 — Cards batch 2 (11-15) done, uncommitted
- status: 5 cards distilled, batch gate green; awaiting commit/next-batch order
- updated: 2026-10-25 (batch session)

## Next actions

1. [x] Move staged tree to final location (observed done)
2. [x] Run Phase 0 gates in final location — green 2026-10-25
3. [x] Batch 0: read dev-corpus/README.md, obey rules (distill-only input, never commit)
4. [x] Batch 0: .gitignore with dev-corpus/ (verified via check-ignore)
5. [x] git add + initial commit (163fed7, 27 files, dev-corpus/ excluded)
6. [x] Phase 1 batch 1: cards 6-10 (ARXIV, BASE, CORE, EUROPEPMC, ISJD) — gate green
7. [x] Commit batch 1 (cae2c38, approved 2026-10-25)
8. [x] Phase 1 batch 2: cards 11-15 (MORAREF, NELITI, ONESEARCH, OPENAIRE, PUBMED) — gate green
9. [ ] Commit batch 2 (needs explicit approval)
10. [ ] Phase 1 batch 3: cards 16-20 (RAMA, RESEARCHGATE, SEMANTICSCHOLAR, SINTA, UNPAYWALL)

## Card order (Phase 1)

- Cards 1-5 shipped: CROSSREF, OPENALEX, SCHOLAR, GARUDA, DOAJ.
- Cards 6-20 = remaining 15 corpus sources, alphabetical by key:
  batch 1 ARXIV/BASE/CORE/EUROPEPMC/ISJD; batch 2 MORAREF/NELITI/
  ONESEARCH/OPENAIRE/PUBMED; batch 3 RAMA/RESEARCHGATE/
  SEMANTICSCHOLAR/SINTA/UNPAYWALL.

## Gates log

- 2026-10-25: staged tree — skill validate true/zero diagnostics,
  24/24 unit checks, sanitization greps clean. Observed in staging;
  re-run after move.
- 2026-10-25: final location — `muse skills validate . --json`
  valid=true, zero diagnostics; `tests/run.sh` 24/24 passed;
  sanitization greps clean (no absolute paths, emails, tokens);
  `git status` shows fresh git init, no commits, no remote.
- 2026-10-25: Batch 0 — dev-corpus/ present (20 sources x 5 files),
  rules read; .gitignore created, check-ignore confirms
  dev-corpus/README.md ignored.
- 2026-10-25: initial commit 163fed7 (27 files, dev-corpus/ excluded).
- 2026-10-25: batch 1 gate green — 5 cards (84/98/99/88/78 lines,
  all sections, canonical+dead domains), zero origin-topic terms,
  no paths/emails/tokens; validate true/zero diagnostics, 24/24 tests.
- 2026-10-25: batch 1 committed (cae2c38, approved).
- 2026-10-25: batch 2 gate green — 5 cards (85/97/80/100/93 lines,
  OPENAIRE trimmed 103->100), zero origin-topic terms, no leaks;
  validate true/zero diagnostics, 24/24 tests.

## Decisions log

- Runner v1 = skill + scripts + one-prompt UX (no agentless auto-scraper).
- Parallelism via Orca child worktrees; fallback subagent isolation.
- finalize! defined in AGENTS.md + PROTOCOL-finalize.md.
- 2026-10-25: reconciled drift — move + git init were already done
  outside a finalize! session; boxes 1-2 flipped after re-verifying
  gates in place. Initial commit still needs explicit human approval.
- 2026-10-25: Batch 0 before commit per user order; commit approved
  once .gitignore exists. Card numbering alphabetical by source key.
  Session logs (logs.md) never read for distillation.
