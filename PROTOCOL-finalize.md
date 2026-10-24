# PROTOCOL-finalize.md

Exact procedure behind the `finalize!` command (defined in AGENTS.md).

## Preconditions

- Workspace root IS this repo. Otherwise stop and say so.
- STATE.md exists and is readable. Otherwise stop: bootstrap is missing.

## Procedure

1. Read STATE.md → PROJECT.md → this file. Note current phase, status,
   and next actions.
2. Verify (never trust STATE.md blindly):
   - `muse skills validate . --json` → record valid/diagnostics.
   - `tests/run.sh` → record pass count.
   - `git status --short` (if a repo) → record dirtiness.
3. Reconcile: if observed state disagrees with STATE.md, update STATE.md
   first and say what drifted.
4. Execute the next incomplete "Next actions" unit, in order, following
   that phase's gate in PROJECT.md. One unit per `finalize!` unless
   the unit is trivially small — then continue while green.
5. Update STATE.md: flip completed boxes, append gates/decisions log,
   set new status + timestamp.
6. Human gates — STOP and report, do not proceed past:
   git push, tag, release, repo creation, publish, new external
   resources/accounts, scope changes, failing gates you cannot fix,
   or any ambiguity about user intent.
7. Report: what ran, gate results (commands + observed output), what
   changed, what is next, and what needs the human.

## Non-goals

- `finalize!` never invents scope beyond STATE.md next actions.
- `finalize!` never pushes, publishes, or releases. Those need an explicit
  user ask naming the action.
