# AGENTS.md — very-deep-search program repo

Session root for this program is this directory. All paths below are
repo-relative unless stated.

## The `finalize!` command

When the user types `finalize!` (fresh session or ongoing):

1. Read STATE.md, PROJECT.md, PROTOCOL-finalize.md (in that order).
2. Verify actual state: run `muse skills validate . --json` and
   `tests/run.sh`; reconcile STATE.md if reality drifted.
3. Execute the next incomplete unit from STATE.md "Next actions".
4. Update STATE.md (status, gates log, decisions log).
5. STOP at human gates and report: any git push/tag/publish, new
   GitHub repo creation, new external resources, scope changes, or
   ambiguity. Never push, publish, or release on a `finalize!` alone.

If your workspace root is NOT this repo, say so and stop — do not
run `finalize!` from another checkout.

## Working rules

- Lanes own disjoint file sets; coordinator merges. Follow PROJECT.md lanes.
- Always writing in english communicating with user on indonesia.
- English, generic, no absolute paths, no secrets — every file, every commit.
- No evidence = not counted. Deterministic artifacts only.
- Tests before claims: unit (`tests/run.sh`), skill validate, sanitization
  greps (absolute home-dir paths, emails, tokens, origin-topic terms
  outside Example blocks).
- Blind-test discipline: foreign agents get the skill only, never this
  repo's dev notes or prior answers; every run ends with a confusion list.
