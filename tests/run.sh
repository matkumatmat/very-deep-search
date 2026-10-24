#!/bin/sh
# Unit tests for scripts/vds.py. Generic fixtures only; no network.
# Fails on the first mismatch. Exit 0 = all green.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VDS="$ROOT/scripts/vds.py"
FIX="$ROOT/tests/fixtures"
EXP="$ROOT/tests/expected"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM
mkdir -p "$TMP/ev"
for f in abc1 abc2 ok k1 k2 k2b k3 k1c; do
  printf 'evidence for %s\n' "$f" > "$TMP/ev/$f.txt"
done
: > "$TMP/ev/empty.txt"

CHECKS=0
check() {
  # check <name> <want_exit> <got_exit>
  if [ "$2" = "$3" ]; then
    CHECKS=$((CHECKS + 1))
    echo "ok: $1"
  else
    echo "FAIL: $1 (want exit $2, got $3)"
    exit 1
  fi
}
need() {
  # need <name> <pattern> <text>
  if printf '%s' "$3" | grep -q "$2"; then
    CHECKS=$((CHECKS + 1))
  else
    echo "FAIL: $1 (pattern not found: $2)"
    printf '%s\n' "$3"
    exit 1
  fi
}

# 1. clean fixture validates with exact counts
OUT="$("$VDS" validate "$FIX/valid.jsonl" --root "$TMP")"
CODE=$?
need "validate-clean-counts" "pass=2 reject=1 duplicates=0 errors=0" "$OUT"
check "validate-clean-exit" 0 "$CODE"

# 2. dirty fixture: every failure mode surfaces, exit 1
OUT="$("$VDS" validate "$FIX/invalid.jsonl" --root "$TMP")"
CODE=$?
for pat in "invalid JSON" "missing field" "decision must be" \
  "whitespace" "must be boolean" "non-empty reverify" "not found" \
  "duplicate identifier" "empty"; do
  need "validate-dirty:$pat" "$pat" "$OUT"
done
check "validate-dirty-exit" 1 "$CODE"

# 3. merge happy path: counts + byte-exact output + report
"$VDS" merge "a=$FIX/merge-a.jsonl" "b=$FIX/merge-b.jsonl" \
  "c=$FIX/merge-c.jsonl" --keep-order a,b,c -o "$TMP/merged.jsonl" \
  --report "$TMP/dups.jsonl" --root "$TMP" > "$TMP/merge.log"
check "merge-exit" 0 "$?"
need "merge-counts" "records=7 unique=5 duplicates=2" "$(cat "$TMP/merge.log")"
if diff -u "$EXP/merged.jsonl" "$TMP/merged.jsonl" > "$TMP/merge.diff"; then
  CHECKS=$((CHECKS + 1))
  echo "ok: merge-bytes"
else
  echo "FAIL: merged bytes differ from expected"
  cat "$TMP/merge.diff"
  exit 1
fi
[ "$(wc -l < "$TMP/dups.jsonl")" = "2" ] || {
  echo "FAIL: dup report should have 2 lines"
  exit 1
}
CHECKS=$((CHECKS + 1))
echo "ok: merge-report"

# 3b. merge --pass-only restricts to pass rows (final merge mode)
"$VDS" merge "a=$FIX/merge-a.jsonl" "b=$FIX/merge-b.jsonl" \
  "c=$FIX/merge-c.jsonl" --keep-order a,b,c --pass-only \
  -o "$TMP/merged-po.jsonl" --root "$TMP" > "$TMP/merge-po.log"
check "merge-passonly-exit" 0 "$?"
need "merge-passonly-counts" "records=5 unique=3 duplicates=2" "$(cat "$TMP/merge-po.log")"
if diff -u "$EXP/merged-pass-only.jsonl" "$TMP/merged-po.jsonl" > "$TMP/merge-po.diff"; then
  CHECKS=$((CHECKS + 1))
  echo "ok: merge-passonly-bytes"
else
  echo "FAIL: pass-only merged bytes differ from expected"
  cat "$TMP/merge-po.diff"
  exit 1
fi

# 4. merge is byte-deterministic across runs
"$VDS" merge "a=$FIX/merge-a.jsonl" "b=$FIX/merge-b.jsonl" \
  "c=$FIX/merge-c.jsonl" --keep-order a,b,c -o "$TMP/merged2.jsonl" \
  --root "$TMP" > /dev/null
if cmp -s "$TMP/merged.jsonl" "$TMP/merged2.jsonl"; then
  CHECKS=$((CHECKS + 1))
  echo "ok: merge-deterministic"
else
  echo "FAIL: merge output differs between runs"
  exit 1
fi

# 5. merge refuses invalid input and writes nothing
"$VDS" merge "a=$FIX/merge-a.jsonl" "bad=$FIX/invalid.jsonl" \
  --keep-order a,bad -o "$TMP/nope.jsonl" --root "$TMP" > "$TMP/refused.log"
check "merge-refused-exit" 1 "$?"
need "merge-refused-msg" "merge refused" "$(cat "$TMP/refused.log")"
if [ ! -e "$TMP/nope.jsonl" ]; then
  CHECKS=$((CHECKS + 1))
  echo "ok: merge-refused-nowrite"
else
  echo "FAIL: refused merge wrote output"
  exit 1
fi

# 6. keep-order mismatch is a usage error (exit 2)
"$VDS" merge "a=$FIX/merge-a.jsonl" --keep-order a,b -o "$TMP/x.jsonl" \
  > /dev/null 2>&1
check "merge-badorder-exit" 2 "$?"

echo "ALL UNIT TESTS PASSED ($CHECKS checks)"
