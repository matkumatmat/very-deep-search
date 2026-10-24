# very-deep-search — program

Public home of the very-deep-search skill: a multi-agent
gather-and-verify pipeline for deep literature search.

## Two audiences

- End user: installs the skill, pastes one prompt, receives a report
  (quota met, real PDFs, reproducible verifications). Entry: README.md.
- Tester/developer: white-box segmentation — unit tests, legacy
  conformance, blind foreign-agent tests with confusion lists,
  request budgets, sanitization gates. Entry: tests/ + this file.

## Lanes (parallel workstreams)

- Cards: protocol cards 6–20 (batches of 5).
- Runner: user-facing scaffold/package UX + quickstart + demo.
- QA: blind foreign-agent tests per batch; every confusion item must
  close (fix or documented wontfix).
- Upstream: issue/PR triage post-publish (cadence set by maintainer).
- Efficiency: request/time budgets per quota; card drift re-probes.
- Coordinator: gates, merges, STATE.md, releases. Human gates: any
  push/tag/publish, new external resources, scope changes.

## Phases

0. Bootstrap (this tree + finalize! protocol). Gate: validate + 24 tests.
1. Cards 6–20 in 3 batches. Gate per batch: card checklist + sanitasi.
2. Runner UX. Gate: blind foreign agent completes quota-3 on user docs alone.
3. QA hardening. Gate: zero open confusion items; budgets met.
4. Publish (public GitHub, docs, v1.0.0). Gate: clean-clone install works.
5. Steady state (upstream + efficiency, continuous).

## Conventions

- English, generic, no absolute paths, no secrets in committed files.
- Deterministic artifacts; evidence for every claim.
- See AGENTS.md (repo working agreement) and PROTOCOL-finalize.md.
