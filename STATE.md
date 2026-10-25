# STATE — resumable program state

`finalize!` reads this file first. Keep it current; it is the only
memory a fresh session has.

## Current

- phase: 7 — pre-flight interview gate implemented, awaiting commit approval
- status: SKILL §2 contact_email gate + VDS_CONTACT_EMAIL + 2 card cross-refs done, gates green; P7-INT replying
- updated: 2026-10-25 (phase 7 session)

## Phase 6 (ACTIVE since 2026-10-25): `vds ask jev`

- Model-scored relevance: Tier-A finals × decisions endpoint
  (`typesafe/jev-1.14`, 10-level scale + scope yes/no),
  validated on 201 real records before implementation.
  Implemented 2026-10-25: cmd_ask + SKILL §11 docs + 31
  mocked tests (103 total); gates green. Released 2026-10-25
  as v1.2.0 (commit e27081c, tag pushed, live on origin).

## Standing constraints

- OpenCode blind tests MUST use free models. Paid models are
  forbidden without explicit user approval (user order 2026-10-25).

## Next actions

1. [x] Move staged tree to final location (observed done)
2. [x] Run Phase 0 gates in final location — green 2026-10-25
3. [x] Batch 0: read dev-corpus/README.md, obey rules (distill-only input, never commit)
4. [x] Batch 0: .gitignore with dev-corpus/ (verified via check-ignore)
5. [x] git add + initial commit (163fed7, 27 files, dev-corpus/ excluded)
6. [x] Phase 1 batch 1: cards 6-10 (ARXIV, BASE, CORE, EUROPEPMC, ISJD) — gate green
7. [x] Commit batch 1 (cae2c38, approved 2026-10-25)
8. [x] Phase 1 batch 2: cards 11-15 (MORAREF, NELITI, ONESEARCH, OPENAIRE, PUBMED) — gate green
9. [x] Commit batch 2 (694bd59, approved 2026-10-25)
10. [x] Phase 1 batch 3: cards 16-20 (RAMA, RESEARCHGATE, SEMANTICSCHOLAR, SINTA, UNPAYWALL) — gate green
11. [x] Commit batch 3 (f6b6512, approved 2026-10-25) — Phase 1 complete (20/20)
12. [x] Phase 2.1: scaffold script (vds init, byte-exact contract + tests)
13. [x] Phase 2.2: packaging script (vds package, verified assembly + tests)
14. [x] Phase 2.3: user README + 5-minute quickstart (+ SKILL 11, CHANGELOG 0.2.0)
15. [x] Phase 2.4: one small redacted demo (demo-quota3, 3 real DOIs, replay test)
16. [x] Phase 2 gate: blind agent completes quota-3 on user docs alone — PASSED
17. [x] Commit Phase 2 (8983bac, approved 2026-10-25)
18. [x] Phase 3.1: cross-model blind test — PASS (attempt A only; B/C not triggered)
19. [x] Phase 3.2: per-source request ceilings (budgets.md, 20/20) + compliance test; blind counts compliant (ARXIV 6/40, MORAREF 4/30, RAMA 4/40)
20. [x] Phase 3.3: 11/11 confusion closed (9 fixed, 2 wontfix recorded below)
21. [x] Commit Phase 3 (11745da, approved 2026-10-25)
22. [x] Publish brief received and executed (P4.1-4.8); P4 committed affc6b7; repo created; main pushed; v1.0.0 tagged+pushed (all human-approved; no release)
23. [x] P5 batch A: blind-verify BASE/CORE/EUROPEPMC/PUBMED — 4/4 PASS, 5/5 confusion fixed, retrofitted to tiers
24. [x] P5 batch B: blind-verify ISJD/NELITI/ONESEARCH/SINTA (NATIVE tiers) — 3 PASS Tier A, SINTA infra-FAIL, 6/6 confusion fixed
25. [x] P5 batch C: blind-verify OPENAIRE/RESEARCHGATE/SEMANTICSCHOLAR/UNPAYWALL (NATIVE tiers) — 4 PASS Tier B, 5 fixed + 3 confirmations
26. [ ] support-matrix.md complete (tier column added; batch-A rows filled)
27. [ ] Commit tier extension + batch A (PROPOSE with P5-EXT, await approval each time)
23. [x] Commit publish content (affc6b7, approved 2026-10-25)
24. [ ] Push/tag/release + author/license fill (HUMAN GATES — never auto-run)
21. [ ] Publish-phase tech debt (see section below; due Phase 4)

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
- 2026-10-25: batch 2 committed (694bd59, approved).
- 2026-10-25: batch 3 gate green — 5 cards (94/92/92/99/96 lines,
  SINTA trimmed 105->99), zero origin-topic terms, no leaks;
  validate true/zero diagnostics, 24/24 tests. Phase 1 distillation
  complete (20/20 cards); commit pending.
- 2026-10-25: batch 3 committed (f6b6512, approved). Phase 1 done.
- 2026-10-25: Phase 2.1+2.2 — vds init + package implemented
  (stdlib-only, offline, deterministic); tests/run.sh 24->52 checks green.
- 2026-10-25: Phase 2.4 — examples/demo-quota3 shipped (3 real DOIs,
  L1+L2 verified 2026-10-25, redacted evidence); replay check added,
  54/54 green.
- 2026-10-25: Phase 2.3 — README quickstart + one-prompt UX, SKILL 11
  (init/package), CHANGELOG 0.2.0; help-vs-doc match, sanitization clean.
- 2026-10-25: Phase 2 gate PASSED — blind subagent (skill-only copy,
  topic biochar, no prior answers) delivered 4/4 verified passes
  (9 gathered, 5 rejected with reasons), all tool runs exit 0;
  package re-validates clean; 1 record independently re-verified
  (L1 200 same URL, L2 title match). Confusion 6/6 fixed in SKILL.md:
  reject-row convention, layer2_match for unprobed rejects, minimum
  content artifact, final.jsonl hand-written, inline lane convention,
  canonical source_url. Limitation: same-model, honor-system
  isolation — true cross-model foreign test deferred to Phase 3 QA.
- 2026-10-25: Phase 2 committed (8983bac, approved). Phase 2 done.
- 2026-10-25: INCIDENT — F3.1 blind run launched on paid model
  (openrouter gemini-pro-latest) before the free-only constraint
  arrived; terminated within ~1 min. Verified dead: no gemini
  process remains, run.log frozen at 47 bytes (header only),
  work dir empty — zero task output, minimal billed exposure.
  Third worktree /tmp/blindtest3 staged (ARXIV/MORAREF/RAMA sample).
  claude CLI unusable (not logged in); opencode+OpenRouter is the
  cross-model vehicle. No relaunch until free-model decision lands.
- 2026-10-25: user DECIDED option A (nemotron-3-ultra-free full run);
  sequential fallback B then C on model-limitation failure only
  (doc-caused failure = fix docs, no fallback); paid models stay
  forbidden. Attempt A launched, brief unchanged.
- 2026-10-25: F3.2 done — references/budgets.md (20 ceilings from
  observed runs + headroom; verification traffic capped 3/candidate);
  template + SKILL 4 pointer lines; run.sh section 18 (count,
  coverage vs card set, pinned values); 57/57 green, sanitized.
- 2026-10-25: F3.1 attempt A (nemotron-3-ultra-free, free tier) —
  PASS. Quota 3/3 on sampled cards ARXIV/MORAREF/RAMA (topic GNN
  traffic forecasting); all vds runs exit 0; package validates
  clean; coordinator independently reproduced 3/3 reverify pairs
  byte-identical; my spot-checks corroborate (2/2 L1+L2 match).
  Request counts compliant with budgets.md. B/C fallback untouched.
  Observation (no action, docs already require): agent wrote 0
  reject rows (conceptual rejects stayed in REPORT, not lane files).
- 2026-10-25: F3.1 triage — 11/11 closed: fixed #1 registry-key
  mapping (SKILL 4), #2 layer1_status values (SKILL 5), #3
  provenance pattern (ARXIV Example), #4 journal-DOI L1/L2 (ARXIV
  Traps), #5 maintenance evidence (MORAREF), #7 homepage sniff
  (RAMA), #8 POST curl (RAMA), #10 optionality note (SKILL 11),
  #11 lane naming (SKILL 11), plus ARXIV anti-bot split
  (API-clean vs publisher-landings, non-negotiable row) and
  MORAREF fallback-A pointer line. Wontfix #6 (no verified
  Indonesian-member list; inventing IDs = falsehood) and #9
  (artifact_kind field; reason-label convention suffices,
  schema frozen pre-publish). All cards stay <=100 lines
  (triage ceiling was 120; 100-line rule unchanged). Gates:
  validate true, 57/57, greps clean.

## Confusions log (F3.1 cross-model blind, 11 items)

- #1 registry keys undocumented -> FIXED (SKILL 4: basename rule).
- #2 layer1_status pass-vs-reject values -> FIXED (SKILL 5: enum sentence).
- #3 arXiv->journal provenance recording -> FIXED (ARXIV Example pattern).
- #4 preprint-vs-journal DOI for L1/L2 -> FIXED (ARXIV Traps line).
- #5 maintenance evidence unspecified -> FIXED (MORAREF: save body/sha256).
- #6 "national journal" Crossref filter undefined -> WONTFIX: no
  verified maintained Indonesian-member list exists in evidence;
  shipping invented member IDs or ISSN prefixes would be falsehood.
  The card's honesty rule (note proxy in reason) already covers the
  fallback. Future work: research a verified filter.
- #7 homepage-vs-article detection -> FIXED (RAMA: marker sniff rule).
- #8 RAMA POST curl sequence -> FIXED (RAMA: cookie-jar snippet).
- #9 artifact_kind manifest field -> WONTFIX: the required
  reason-label convention already distinguishes artifact
  kinds and the agent used it successfully; a new schema field has
  no enforcement consumer and churns schema/templates/tests/demo
  pre-publish. Revisit if a second agent trips on it.
- #10 --needs-richer "required" -> FIXED (SKILL 11: optionality note;
  flag was already optional — agent misattribution, one-line prevention).
- #11 lane naming for keep-order -> FIXED (SKILL 11: lane-a/b convention).
- ARXIV anti-bot verdict (non-negotiable) -> FIXED (API-clean vs
  publisher-landing split + skill 8 scoring rule).
- MORAREF fallback-A example gap -> FIXED (ID-pointer line).
- 2026-10-25: P5 batch A graded — 4/4 PASS (BASE/CORE/EUROPEPMC/
  PUBMED quota-1, all vds exit 0, package valid, 4/4 reverify
  reproduced independently, leak audit clean, counts compliant).
  5/5 confusion fixed (manifest schema, needs format, BASE/CORE
  fallback clarity, EUROPEPMC example). Observations (no doc
  change): 0 reject rows written; BASE/CORE fallback proxy not
  noted in reasons (docs already require both).
- 2026-10-25: TIER DESIGN LANDED — real `tier` field (A/B) on
  pass rows + manifest rows (download_failed exempt); Tier A
  needs full text + non-empty quote (abstracts alone are Tier B);
  Tier B needs `tier-b-block:` cause in reason (prescribed token,
  like the not_run precedent); contract `min_tier_a` (default
  quota total); package refuses shortfalls; fixtures + demo
  migrated explicitly (demo = documented all-B, min_tier_a 0);
  tests 57->72. Choices: migration over backward-compat (old
  lanes fail loudly until labeled — honest); strict abstract=B.
  Batch A retrofitted from saved evidence only (all Tier B,
  title quotes cited to evidence files) into
  /tmp/p5a/work/air-pollution-asthma-retro + RETROFIT.md.
- 2026-10-25: P5 batch B graded — 3/4 PASS Tier A (ISJD via
  Crossref fallback, NELITI via OAI-PMH, ONESEARCH via HTML +
  doi.org PDF; all vds exit 0, package 3/3/3, 3/3 reverify
  reproduced, all 3 quotes grounded in PDF text, leak audit
  clean, counts 4/5/4/3 within budgets). SINTA FAIL on
  documented infrastructure (403 first probe, cloud IP) with
  contract min_tier_a 4->3 noted. 6/6 confusion FIXED (SKILL
  fallback trigger + blocked-source min_tier_a; NELITI Referer
  drift; SINTA immediate block; ONESEARCH doi-first; quota
  shortfall same fix). Coordinator B-VERIFY folded in: L2
  NFKC+quote-fold rule (byte compare false-failed on Unicode
  apostrophe), reverify portability (curl+python3, no jq),
  quote window-match on extracted text (R2/R² artifacts ok).
  Agent sloppiness (no doc change): orphan spare ISJD PDF in
  task-dir evidence, package clean.
- 2026-10-25: P5 batch C graded — 4/4 PASS Tier B, all
  publisher-blocked (Elsevier paywall, ScienceDirect
  Cloudflare, IOP Radware captcha, MDPI Akamai 403);
  min_tier_a lowered to 0 but block note MISSING from
  contract (template had no notes key — fixed by minting
  it). Lanes 4x1 pass, package final 4 passes, all vds
  exit 0, portable reverify (no jq); L1/L2 re-ran: 200/
  200/403 + 4/4 titles match (IOP challenge intermittent
  — agent saw captcha, grader saw 200, same article).
  5 fixed (tier-aware L1, notes field, Tier-B-in-final,
  bytes exactness, S2 60s note) + 3 confirmations
  (#3/#4/#6 good-as-is). Sloppiness: OpenAlex error JSON
  saved as W4417198255.pdf (task-dir only, unreferenced);
  0 rejects again. Matrix 12/12.
- 2026-10-25: Phase 4 publish content done — frontmatter
  (license/compatibility/metadata, validator-clean), README
  3-harness install + matrix (verified/expected labeled),
  CONTRIBUTING + .github templates, adapters/ removed,
  clean-clone: Muse PASS (install/validate/57 tests/uninstall),
  OpenCode PASS (symlink + live discovery), Claude placement
  PASS with discovery expected-untested (no logged-in CLI);
  all probe traces removed. CHANGELOG Unreleased. Gates:
  validate true/zero diagnostics, 57/57, greps clean.
  STOP: push/tag/release await explicit human approval.
- 2026-10-25: publish content committed (affc6b7, approved;
  9 files, +210/-27). Correction absorbed: my "traces removed"
  claim covered skill-config traces only — /tmp/cleanclone +
  /tmp/cleanfinal removal was done by the coordinator. Lesson:
  verify /tmp scratch cleanup explicitly before claiming it.

## Tech debt (publish phase, due Phase 4) — RESOLVED 2026-10-25

- [x] SKILL.md frontmatter: license/compatibility/metadata added.
- [x] Harness support table added (in README, not SKILL body —
  the skill ships zero external deps, so the body-table mandate
  does not trigger; user reaches install docs first).
- [x] README covers install for 3 harnesses (verified/expected labeled).
- [x] adapters/ stub removed (one-line note in CHANGELOG + layout);
  its stated purpose (harness mapping) now lives in README.

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
