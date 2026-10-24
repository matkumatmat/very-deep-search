# Contributing

## Adding a new source card (end to end)

1. Read `templates/source-guide.md` and one shipped card (e.g.
   `references/sources/OPENAIRE.md`) for shape and tone.
2. Research the source live: probe access, note rate limits,
   anti-bot behavior, parser details, and fallbacks. Record
   dates and raw observations in your own notes (never commit
   session logs or topic-coupled queries).
3. Write `references/sources/<SOURCE>.md` from the template:
   every section filled, max 100 lines, canonical base domain
   plus known-dead legacy domains, English, generic.
   Topic-specific values live ONLY in the Example block (use
   `<PLACEHOLDERS>`); the rest must read cleanly for any topic.
4. Add a request ceiling to `references/budgets.md`: one line
   in the exact `- <SOURCE>: <N> /run — basis: ...` format,
   with N from your observed run plus headroom, then update
   the pinned values in `tests/run.sh` (section 18) to match.
5. Run the gates from the repo root and keep them green:
   `muse skills validate . --json` (valid, zero diagnostics),
   `tests/run.sh` (all pass), and sanitization greps — no
   absolute paths, emails, tokens, or origin-topic terms
   outside Example blocks.
6. Blind mini-gate: someone (or some model session) that did
   NOT write the card reads it cold, runs one discovery
   query straight from the card, and writes confusion notes.
   Every note closes as a card fix or a recorded wontfix
   with rationale before merge.
7. Open a PR using `.github/pull_request_template.md`.

## Other changes

- `scripts/vds.py`: stdlib only, offline, deterministic.
  Every behavior change ships with `tests/run.sh` coverage
  in the same PR. `--help` is authoritative over prose docs.
- Docs: same gates as cards (English, generic, sanitized).

## Issue templates

- Bug reports: `.github/ISSUE_TEMPLATE/bug_report.md`.
- New-source requests: `.github/ISSUE_TEMPLATE/new_source.md`.
