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

# 7. init scaffolds a byte-exact contract plus workspace/evidence dirs
OUT="$("$VDS" init "$TMP/task1" --topic "widgets and gadgets" --quota 3 \
  --sources CROSSREF,OPENALEX)"
check "init-exit" 0 "$?"
need "init-summary" "quota=3 sources=2 per_source=2" "$OUT"
if diff -u "$EXP/contract-init.json" "$TMP/task1/contract.json" > "$TMP/init.diff"; then
  CHECKS=$((CHECKS + 1))
  echo "ok: init-bytes"
else
  echo "FAIL: init contract bytes differ from expected"
  cat "$TMP/init.diff"
  exit 1
fi
[ -d "$TMP/task1/workspace" ] && [ -d "$TMP/task1/evidence" ] || {
  echo "FAIL: init must create workspace/ and evidence/"
  exit 1
}
CHECKS=$((CHECKS + 1))
echo "ok: init-dirs"

# 8. init refuses to overwrite without --force; --force rewrites identical bytes
OUT="$("$VDS" init "$TMP/task1" --topic "other" --quota 1 --sources X)"
check "init-refused-exit" 1 "$?"
need "init-refused-msg" "init refused" "$OUT"
"$VDS" init "$TMP/task1" --topic "widgets and gadgets" --quota 3 \
  --sources CROSSREF,OPENALEX --force > /dev/null
check "init-force-exit" 0 "$?"
if cmp -s "$EXP/contract-init.json" "$TMP/task1/contract.json"; then
  CHECKS=$((CHECKS + 1))
  echo "ok: init-deterministic"
else
  echo "FAIL: init --force output differs"
  exit 1
fi

# 9. init usage errors (fresh dirs): bad quota, empty sources
"$VDS" init "$TMP/t2" --topic "x" --quota 0 --sources A > /dev/null 2>&1
check "init-badquota-exit" 2 "$?"
"$VDS" init "$TMP/t3" --topic "x" --quota 1 --sources " , " > /dev/null 2>&1
check "init-badsources-exit" 2 "$?"

# 10. package happy path: summary + exact layout + honest README
mkdir -p "$TMP/evidence"
printf 'proof-alpha\n' > "$TMP/evidence/p1.txt"
printf 'proof-beta-ok\n' > "$TMP/evidence/p2.txt"
OUT="$("$VDS" package --final "$FIX/pkg-final.jsonl" \
  --manifest "$FIX/pkg-manifest.jsonl" --contract "$TMP/task1/contract.json" \
  --merged "$TMP/merged-po.jsonl" --excluded "$FIX/pkg-excluded.md" \
  --needs-richer "$FIX/pkg-needs.jsonl" --root "$TMP" -o "$TMP/pkg")"
check "package-exit" 0 "$?"
need "package-summary" "final=2 manifest=3 evidence=2" "$OUT"
(cd "$TMP/pkg" && find . -type f | LC_ALL=C sort) > "$TMP/pkg.files"
cat > "$TMP/pkg.want" <<'EOF'
./README.md
./contract.json
./evidence/p1.txt
./evidence/p2.txt
./excluded-from-final.md
./final.jsonl
./manifest.jsonl
./merged.jsonl
./needs-richer-check.jsonl
EOF
if diff -u "$TMP/pkg.want" "$TMP/pkg.files" > "$TMP/pkg.diff"; then
  CHECKS=$((CHECKS + 1))
  echo "ok: package-layout"
else
  echo "FAIL: package layout differs"
  cat "$TMP/pkg.diff"
  exit 1
fi
need "package-readme-topic" "widgets and gadgets" "$(cat "$TMP/pkg/README.md")"
need "package-readme-missing" "Not provided: disputes.md" "$(cat "$TMP/pkg/README.md")"

# 11. packaged final re-validates self-contained inside the package
OUT="$("$VDS" validate "$TMP/pkg/final.jsonl" --root "$TMP/pkg")"
check "package-selfcontained-exit" 0 "$?"
need "package-selfcontained-counts" "pass=2 reject=0 duplicates=0 errors=0" "$OUT"

# 12. package is byte-deterministic across runs
"$VDS" package --final "$FIX/pkg-final.jsonl" \
  --manifest "$FIX/pkg-manifest.jsonl" --contract "$TMP/task1/contract.json" \
  --merged "$TMP/merged-po.jsonl" --excluded "$FIX/pkg-excluded.md" \
  --needs-richer "$FIX/pkg-needs.jsonl" --root "$TMP" -o "$TMP/pkg2" > /dev/null
if diff -r "$TMP/pkg" "$TMP/pkg2" > /dev/null; then
  CHECKS=$((CHECKS + 1))
  echo "ok: package-deterministic"
else
  echo "FAIL: package output differs between runs"
  exit 1
fi

# 13. package refuses on missing manifest coverage and writes nothing
head -1 "$FIX/pkg-manifest.jsonl" > "$TMP/short-manifest.jsonl"
OUT="$("$VDS" package --final "$FIX/pkg-final.jsonl" \
  --manifest "$TMP/short-manifest.jsonl" --root "$TMP" -o "$TMP/pkgbad")"
check "package-refused-exit" 1 "$?"
need "package-refused-msg" "no manifest row for final identifier" "$OUT"
if [ ! -e "$TMP/pkgbad" ]; then
  CHECKS=$((CHECKS + 1))
  echo "ok: package-refused-nowrite"
else
  echo "FAIL: refused package wrote output"
  exit 1
fi

# 14. package refuses a non-empty output dir without --force
OUT="$("$VDS" package --final "$FIX/pkg-final.jsonl" \
  --manifest "$FIX/pkg-manifest.jsonl" --root "$TMP" -o "$TMP/pkg")"
check "package-nonempty-exit" 1 "$?"
need "package-nonempty-msg" "not empty" "$OUT"
"$VDS" package --final "$FIX/pkg-final.jsonl" \
  --manifest "$FIX/pkg-manifest.jsonl" --root "$TMP" -o "$TMP/pkg" --force \
  > /dev/null
check "package-force-exit" 0 "$?"

# 15. package refuses a manifest whose bytes disagree with the file
sed 's/"bytes": 12/"bytes": 13/' "$FIX/pkg-manifest.jsonl" > "$TMP/bad-manifest.jsonl"
OUT="$("$VDS" package --final "$FIX/pkg-final.jsonl" \
  --manifest "$TMP/bad-manifest.jsonl" --root "$TMP" -o "$TMP/pkgbad2")"
check "package-badbytes-exit" 1 "$?"
need "package-badbytes-msg" "bytes 13 != file size 12" "$OUT"

# 16. package refuses a needs-richer row with a bad status
printf '{"identifier": "10.0000/x", "queued_by": "t", "reason": "r", "status": "maybe"}\n' \
  > "$TMP/bad-needs.jsonl"
OUT="$("$VDS" package --final "$FIX/pkg-final.jsonl" \
  --manifest "$FIX/pkg-manifest.jsonl" --needs-richer "$TMP/bad-needs.jsonl" \
  --root "$TMP" -o "$TMP/pkgbad3")"
check "package-badneeds-exit" 1 "$?"
need "package-badneeds-msg" "needs status must be" "$OUT"

# 17. demo replay: packaging the shipped demo reproduces package-expected
DEMO="$ROOT/examples/demo-quota3"
"$VDS" package --final "$DEMO/final.jsonl" --manifest "$DEMO/manifest.jsonl" \
  --merged "$DEMO/merged.jsonl" --contract "$DEMO/contract.json" \
  --excluded "$DEMO/excluded-from-final.md" \
  --needs-richer "$DEMO/needs-richer-check.jsonl" --root "$DEMO" \
  -o "$TMP/demo-replay" > /dev/null
check "demo-replay-exit" 0 "$?"
if diff -r "$DEMO/package-expected" "$TMP/demo-replay" > /dev/null; then
  CHECKS=$((CHECKS + 1))
  echo "ok: demo-replay-bytes"
else
  echo "FAIL: demo replay differs from package-expected"
  exit 1
fi

# 18. budgets registry: 20/20 card sources, parseable ceilings, pinned values
BUD="$ROOT/references/budgets.md"
grep -E '^- [A-Z]+: [0-9]+ /run — basis: .+' "$BUD" | LC_ALL=C sort \
  > "$TMP/bud.lines"
[ "$(wc -l < "$TMP/bud.lines")" = "20" ] || {
  echo "FAIL: budgets.md must hold exactly 20 ceiling lines"
  exit 1
}
CHECKS=$((CHECKS + 1))
echo "ok: budgets-count"
(cd "$ROOT/references/sources" && ls *.md | sed 's/\.md$//' | LC_ALL=C sort) \
  > "$TMP/bud.cards"
sed -E 's/^- ([A-Z]+):.*/\1/' "$TMP/bud.lines" > "$TMP/bud.sources"
if diff -u "$TMP/bud.cards" "$TMP/bud.sources" > "$TMP/bud.diff"; then
  CHECKS=$((CHECKS + 1))
  echo "ok: budgets-coverage"
else
  echo "FAIL: budget sources differ from card set"
  cat "$TMP/bud.diff"
  exit 1
fi
sed -E 's/^- ([A-Z]+): ([0-9]+) .*/\1:\2/' "$TMP/bud.lines" > "$TMP/bud.vals"
cat > "$TMP/bud.want" <<'EOF'
ARXIV:40
BASE:80
CORE:60
CROSSREF:60
DOAJ:40
EUROPEPMC:40
GARUDA:60
ISJD:20
MORAREF:30
NELITI:100
ONESEARCH:60
OPENAIRE:50
OPENALEX:80
PUBMED:60
RAMA:40
RESEARCHGATE:20
SCHOLAR:12
SEMANTICSCHOLAR:50
SINTA:800
UNPAYWALL:200
EOF
if diff -u "$TMP/bud.want" "$TMP/bud.vals" > "$TMP/bud.vdiff"; then
  CHECKS=$((CHECKS + 1))
  echo "ok: budgets-values"
else
  echo "FAIL: budget values differ from pinned policy"
  cat "$TMP/bud.vdiff"
  exit 1
fi

echo "ALL UNIT TESTS PASSED ($CHECKS checks)"
