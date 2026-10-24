# <SOURCE> — Protocol Card

> Status: behavior observed <YYYY-MM-DD>. Re-probe on repeated failures.
> Fill every section before gathering (document-before-gather).
> Max 100 lines. Topic-specific values allowed ONLY in Example.

## Access

- Endpoints, parameters, and what the source is (API / harvester /
  index / repository / HTML-only).

## Identity & auth

- Required identity (polite pools, contact emails, API keys).
- Secrets via env vars / `<PLACEHOLDERS>` — never hardcoded.

## Rate limits & courtesy

- Observed limits, delays, sequential-only rules.

## Anti-bot & standard response

- Known blocks and the exact standard response for each.

## Parser notes

- Selectors, pagination, encodings, and traps that broke a naive parse.

## Traps

- Ways this source silently yields wrong data (if none observed, write
  "none observed" — do not invent any).

## Fallback chain

- Ordered fallbacks when the primary path is down, ending in the
  condition for declaring the source exhausted for this run.

## Retry budget

- Probe 1x, retry 1x from a different angle, backoff, then STOP.
- Request ceiling: see `references/budgets.md` (shared policy;
  never exceed mid-run without recording why).

## Example

> Topic-specific values below are illustration only.

- (queries / commands with the run's real topic)

## Run log

- (append: timestamp, queries, candidate/pass/reject counts, failures)
