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
  "duplicate identifier" "empty" 'tier "A" or "B"'; do
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
  --manifest "$FIX/pkg-manifest.jsonl" --contract "$FIX/pkg-contract.json" \
  --merged "$TMP/merged-po.jsonl" --excluded "$FIX/pkg-excluded.md" \
  --needs-richer "$FIX/pkg-needs.jsonl" --root "$TMP" -o "$TMP/pkg")"
check "package-exit" 0 "$?"
need "package-summary" "final=2 manifest=3 evidence=2 tier_a=1" "$OUT"
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
need "package-readme-topic" "package test" "$(cat "$TMP/pkg/README.md")"
need "package-readme-tiera" "Tier-A passes: 1" "$(cat "$TMP/pkg/README.md")"
need "package-readme-missing" "Not provided: disputes.md" "$(cat "$TMP/pkg/README.md")"

# 11. packaged final re-validates self-contained inside the package
OUT="$("$VDS" validate "$TMP/pkg/final.jsonl" --root "$TMP/pkg")"
check "package-selfcontained-exit" 0 "$?"
need "package-selfcontained-counts" "pass=2 reject=0 duplicates=0 errors=0" "$OUT"

# 12. package is byte-deterministic across runs
"$VDS" package --final "$FIX/pkg-final.jsonl" \
  --manifest "$FIX/pkg-manifest.jsonl" --contract "$FIX/pkg-contract.json" \
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

# 19. tiers: validate enforces tier labels, package enforces quota + quotes
printf '{"decision": "pass", "evidence_ref": "ev/ok.txt", "identifier": "10.0/t1", "layer1_status": 200, "layer2_match": true, "reason": "R", "reverify": ["curl https://example.org/t1"], "source_url": "https://example.org/t1", "title": "T"}\n' > "$TMP/notier.jsonl"
OUT="$("$VDS" validate "$TMP/notier.jsonl" --root "$TMP")"
check "tier-missing-exit" 1 "$?"
need "tier-missing-msg" 'tier "A" or "B"' "$OUT"
printf '{"decision": "pass", "evidence_ref": "ev/ok.txt", "identifier": "10.0/t2", "layer1_status": 200, "layer2_match": true, "reason": "R", "reverify": ["curl https://example.org/t2"], "source_url": "https://example.org/t2", "tier": "C", "title": "T"}\n' > "$TMP/badtier.jsonl"
OUT="$("$VDS" validate "$TMP/badtier.jsonl" --root "$TMP")"
check "tier-badvalue-exit" 1 "$?"
printf '{"decision": "pass", "evidence_ref": "ev/ok.txt", "identifier": "10.0/t3", "layer1_status": 200, "layer2_match": true, "reason": "R without token", "reverify": ["curl https://example.org/t3"], "source_url": "https://example.org/t3", "tier": "B", "title": "T"}\n' > "$TMP/bnotoken.jsonl"
OUT="$("$VDS" validate "$TMP/bnotoken.jsonl" --root "$TMP")"
check "tier-bnotoken-exit" 1 "$?"
need "tier-bnotoken-msg" "tier-b-block:" "$OUT"
printf '{"decision": "pass", "evidence_ref": "ev/ok.txt", "identifier": "10.0/t4", "layer1_status": 200, "layer2_match": true, "reason": "R tier-b-block: paywall.", "reverify": ["curl https://example.org/t4"], "source_url": "https://example.org/t4", "tier": "B", "title": "T"}\n' > "$TMP/bok.jsonl"
OUT="$("$VDS" validate "$TMP/bok.jsonl" --root "$TMP")"
check "tier-bok-exit" 0 "$?"
printf '{"bytes": 12, "filename": "p1.txt", "identifier": "10.0000/pkg.1", "reason": "full text", "source_url": "https://example.org/pkg/1", "tier": "A", "verdict": "relevant"}\n' > "$TMP/noquote-manifest.jsonl"
OUT="$("$VDS" package --final "$FIX/pkg-final.jsonl" \
  --manifest "$TMP/noquote-manifest.jsonl" --root "$TMP" -o "$TMP/pkgnoq")"
check "tier-a-noquote-exit" 1 "$?"
need "tier-a-noquote-msg" "non-empty evidence_quote" "$OUT"
printf '{"min_tier_a": 2, "quota": {"per_source": 1, "total": 2}, "source_registry": ["TEST"], "topic": "shortfall"}\n' > "$TMP/min2.json"
OUT="$("$VDS" package --final "$FIX/pkg-final.jsonl" \
  --manifest "$FIX/pkg-manifest.jsonl" --contract "$TMP/min2.json" \
  --root "$TMP" -o "$TMP/pkgshort")"
check "tier-shortfall-exit" 1 "$?"
need "tier-shortfall-msg" "tier-a shortfall: 1 Tier-A passes < min_tier_a 2" "$OUT"
"$VDS" init "$TMP/t4" --topic "x" --quota 4 --sources A,B --min-tier-a 1 \
  > /dev/null
check "init-mintiera-exit" 0 "$?"
need "init-mintiera-val" '"min_tier_a": 1' "$(cat "$TMP/t4/contract.json")"
"$VDS" init "$TMP/t5" --topic "x" --quota 2 --sources A --min-tier-a 3 \
  > /dev/null 2>&1
check "init-mintiera-bad-exit" 2 "$?"

# 20. ask jev: mocked decisions server, no live key, no network beyond loopback
printf 'DUMMY-KEY-FOR-MOCKED-TESTS' > "$TMP/jev.key"
printf 'ok' > "$TMP/jev.mode"
cat > "$TMP/jev-mock.py" <<'EOF'
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
fixture = json.load(open(sys.argv[1]))
logpath, modepath, portpath = sys.argv[2], sys.argv[3], sys.argv[4]
mode_state = ["ok", 0]
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/alpha/decisions":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        with open(logpath, "a", encoding="utf-8") as f:
            f.write(json.dumps(body, sort_keys=True) + "\n")
        with open(modepath, encoding="utf-8") as f:
            mode = f.read().strip()
        if mode != mode_state[0]:
            mode_state[0] = mode
            mode_state[1] = 0
        if mode == "fail-twice" and mode_state[1] < 2:
            mode_state[1] += 1
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"boom")
            return
        title = body["state"]["title"]
        resp = json.loads(json.dumps(fixture))
        if "Borderline" in title:
            score, conf, noul, cost = 5.0, 0.55, 0.6, 0.00002
        elif "Offtopic" in title:
            score, conf, noul, cost = 2.0, 0.8, 0.1, 0.00001
        elif "seventy" in title:
            score, conf, noul, cost = 6.3, 0.7, 0.8, 0.00002
        elif "fifty" in title:
            score, conf, noul, cost = 4.5, 0.7, 0.8, 0.00002
        else:
            score, conf, noul, cost = 7.2, 0.94, 0.9, 0.00003
        resp["answers"]["relevance"]["score"] = score
        resp["answers"]["relevance"]["confidence"] = conf
        resp["answers"]["meets_scope"]["noul"] = noul
        resp["usage"]["cost"] = cost
        payload = json.dumps(resp).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def log_message(self, *args):
        pass
srv = HTTPServer(("127.0.0.1", 0), H)
with open(portpath, "w", encoding="utf-8") as f:
    f.write(str(srv.server_address[1]))
srv.serve_forever()
EOF
: > "$TMP/jev-requests.jsonl"
python3 "$TMP/jev-mock.py" "$FIX/jev-response.json" "$TMP/jev-requests.jsonl" \
  "$TMP/jev.mode" "$TMP/jev.port" > "$TMP/jev-mock.log" 2>&1 &
JEVPID=$!
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  [ -f "$TMP/jev.port" ] && break
  sleep 0.2
done
[ -f "$TMP/jev.port" ] || { echo "FAIL: mock server did not start"; exit 1; }
JEVBASE="http://127.0.0.1:$(cat "$TMP/jev.port")"
OUT="$(VDS_JEV_ENDPOINT="$JEVBASE" "$VDS" ask jev --package "$FIX/jev-package" \
  --topic "widgets and gadgets" --scope "I1: assembly studies with measured outcomes" \
  --key-file "$TMP/jev.key" --out "$TMP/scores.jsonl")"
check "ask-exit" 0 "$?"
need "ask-band-relevant" "band=relevant" "$OUT"
need "ask-band-borderline" "band=borderline" "$OUT"
need "ask-band-offtopic" "band=off-topic" "$OUT"
need "ask-band-70" "score=70.0 band=relevant" "$OUT"
need "ask-band-50" "score=50.0 band=borderline" "$OUT"
need "ask-uncertain" "uncertain" "$OUT"
need "ask-scope-no" "scope=no" "$OUT"
need "ask-skipped-tierb" "skipped=1" "$OUT"
need "ask-cost" "total_cost=" "$OUT"
[ "$(wc -l < "$TMP/scores.jsonl")" = "5" ] || {
  echo "FAIL: sidecar should have 5 rows"; exit 1; }
CHECKS=$((CHECKS + 1))
echo "ok: ask-sidecar-rows"
for val in '"score_100": 80.0' '"score_100": 55.6' '"score_100": 22.2' \
  '"meets_scope": false' '"confidence": 0.55'; do
  need "ask-sidecar:$val" "$val" "$(cat "$TMP/scores.jsonl")"
done
need "ask-req-model" '"model": "typesafe/jev-1.14"' \
  "$(cat "$TMP/jev-requests.jsonl")"
NCRIT="$(python3 -c "
import json
bodies = [json.loads(l) for l in open('$TMP/jev-requests.jsonl')]
print(min(len(b['questions']['relevance']['criteria']) for b in bodies))")"
[ "$NCRIT" = "10" ] || { echo "FAIL: criteria cap (got $NCRIT)"; exit 1; }
CHECKS=$((CHECKS + 1))
echo "ok: ask-criteria-cap"
OUT2="$(VDS_JEV_ENDPOINT="$JEVBASE" "$VDS" ask jev --package "$FIX/jev-package" \
  --topic "widgets and gadgets" --scope "I1" --key-file "$TMP/jev.key" \
  --out "$TMP/scores-trunc.jsonl" --abstract-chars 40)"
check "ask-trunc-exit" 0 "$?"
MAXABS="$(python3 -c "
import json
bodies = [json.loads(l) for l in open('$TMP/jev-requests.jsonl')]
print(max(len(b['state']['abstract']) for b in bodies[-5:]))")"
[ "$MAXABS" -le 40 ] || { echo "FAIL: abstract truncation ($MAXABS)"; exit 1; }
CHECKS=$((CHECKS + 1))
echo "ok: ask-abstract-trunc"
HITS_BEFORE="$(wc -l < "$TMP/jev-requests.jsonl")"
cp "$TMP/scores.jsonl" "$TMP/scores-first.jsonl"
OUT3="$(VDS_JEV_ENDPOINT="$JEVBASE" "$VDS" ask jev --package "$FIX/jev-package" \
  --topic "widgets and gadgets" --scope "I1" --key-file "$TMP/jev.key" \
  --out "$TMP/scores.jsonl")"
check "ask-resume-exit" 0 "$?"
if cmp -s "$TMP/scores-first.jsonl" "$TMP/scores.jsonl"; then
  CHECKS=$((CHECKS + 1))
  echo "ok: ask-resume-bytes"
else
  echo "FAIL: resume rewrote different bytes"
  exit 1
fi
need "ask-resume-cached" "fresh=0 cached=5" "$OUT3"
HITS_AFTER="$(wc -l < "$TMP/jev-requests.jsonl")"
[ "$HITS_BEFORE" = "$HITS_AFTER" ] || {
  echo "FAIL: resume made fresh calls"; exit 1; }
CHECKS=$((CHECKS + 1))
echo "ok: ask-resume-nocall"
printf 'fail-twice' > "$TMP/jev.mode"
OUT4="$(VDS_JEV_ENDPOINT="$JEVBASE" "$VDS" ask jev --package "$FIX/jev-package" \
  --topic "widgets and gadgets" --scope "I1" --key-file "$TMP/jev.key" \
  --out "$TMP/scores-retry.jsonl")"
check "ask-retry-exit" 0 "$?"
printf 'ok' > "$TMP/jev.mode"
env -u OPENROUTER_API_KEY "$VDS" ask jev --package "$FIX/jev-package" \
  --topic "t" --scope "s" --out "$TMP/nokey.jsonl" > /dev/null 2>&1
check "ask-nokey-exit" 2 "$?"
"$VDS" ask router --package "$FIX/jev-package" --topic "t" --scope "s" \
  --key-file "$TMP/jev.key" --out "$TMP/x.jsonl" > /dev/null 2>&1
check "ask-badbackend-exit" 2 "$?"
"$VDS" ask jev --package "$FIX" --topic "t" --scope "s" \
  --key-file "$TMP/jev.key" --out "$TMP/y.jsonl" > "$TMP/ask-dirty.log" 2>&1
check "ask-dirty-exit" 1 "$?"
need "ask-dirty-refused" "ask refused" "$(cat "$TMP/ask-dirty.log")"
mkdir -p "$TMP/pdfpkg/evidence"
printf 'not a real pdf' > "$TMP/pdfpkg/evidence/r.pdf"
python3 -c "
import json
r = dict(json.loads(open('$FIX/jev-package/final.jsonl').readline()))
r['evidence_ref'] = 'evidence/r.pdf'
open('$TMP/pdfpkg/final.jsonl', 'w').write(json.dumps(r) + chr(10))"
mkdir -p "$TMP/emptybin"
PYBIN="$(command -v python3)"
PATH="$TMP/emptybin" VDS_JEV_ENDPOINT="$JEVBASE" "$PYBIN" "$VDS" ask jev \
  --package "$TMP/pdfpkg" --topic "t" --scope "s" --key-file "$TMP/jev.key" \
  --out "$TMP/z.jsonl" > "$TMP/ask-pdf.log" 2>&1
check "ask-pdfnopdftotext-exit" 1 "$?"
need "ask-pdfnopdftotext-msg" "pdftotext not found" "$(cat "$TMP/ask-pdf.log")"
kill "$JEVPID" 2>/dev/null

echo "ALL UNIT TESTS PASSED ($CHECKS checks)"
