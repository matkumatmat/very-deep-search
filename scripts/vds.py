#!/usr/bin/env python3
"""vds - scaffold, validate, merge, and package very-deep-search tasks.

Standard library only. Offline and deterministic, except `ask`, which
calls one pinned online decisions endpoint (see JEV_ENDPOINT).

Schema (one JSON object per line):
  identifier   canonical ID, lowercase-normalized for dedup (required,
               non-empty, no whitespace)
  title        non-empty string
  source_url   non-empty string
  layer1_status  int or non-empty string, recorded as observed
  layer2_match boolean
  decision     "pass" or "reject" only
  reason       non-empty string, cites criterion + observed evidence
  reverify     list of exact re-verification commands (mandatory
               non-empty for "pass")
  evidence_ref workspace-relative path to saved evidence (mandatory for
               "pass"; the file must exist and be non-empty)

Exit codes: 0 = clean, 1 = data errors found (or merge refused),
2 = bad usage. Findings go to stdout as one report stream; the exit
code signals the verdict.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

REQUIRED_FIELDS = (
    "identifier",
    "title",
    "source_url",
    "layer1_status",
    "layer2_match",
    "decision",
    "reason",
    "reverify",
    "evidence_ref",
)

DECISIONS = ("pass", "reject")


def norm_key(identifier):
    """Dedup key: stripped, lowercased identifier."""
    return identifier.strip().lower()


def is_nonempty_str(value):
    return isinstance(value, str) and value.strip() != ""


def validate_record(obj, root):
    """Return a list of error strings for one record (empty means valid)."""
    if not isinstance(obj, dict):
        return ["record is not a JSON object"]
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in obj:
            errors.append("missing field %r" % (field,))
    if errors:
        return errors
    ident = obj["identifier"]
    if not is_nonempty_str(ident):
        errors.append("identifier must be a non-empty string")
    elif any(ch.isspace() for ch in ident.strip()):
        errors.append("identifier must not contain whitespace")
    if not is_nonempty_str(obj["title"]):
        errors.append("title must be a non-empty string")
    if not is_nonempty_str(obj["source_url"]):
        errors.append("source_url must be a non-empty string")
    layer1 = obj["layer1_status"]
    if isinstance(layer1, bool) or not isinstance(layer1, (int, str)):
        errors.append("layer1_status must be int or string")
    elif isinstance(layer1, str) and layer1.strip() == "":
        errors.append("layer1_status must be non-empty")
    if not isinstance(obj["layer2_match"], bool):
        errors.append("layer2_match must be boolean")
    decision = obj["decision"]
    if decision not in DECISIONS:
        errors.append("decision must be one of pass|reject")
    if not is_nonempty_str(obj["reason"]):
        errors.append("reason must be a non-empty string")
    reverify = obj["reverify"]
    if not isinstance(reverify, list) or any(
        not is_nonempty_str(cmd) for cmd in reverify
    ):
        errors.append("reverify must be a list of non-empty command strings")
    evidence = obj["evidence_ref"]
    if not isinstance(evidence, str):
        errors.append("evidence_ref must be a string path")
    if decision == "pass":
        if isinstance(reverify, list) and not reverify:
            errors.append("pass requires non-empty reverify")
        if isinstance(evidence, str) and evidence.strip() == "":
            errors.append("pass requires non-empty evidence_ref")
        elif isinstance(evidence, str) and evidence.strip():
            rel = evidence.strip()
            full = rel if os.path.isabs(rel) else os.path.join(root, rel)
            if not os.path.isfile(full):
                errors.append("evidence file not found: %s" % (rel,))
            elif os.path.getsize(full) == 0:
                errors.append("evidence file is empty: %s" % (rel,))
        tier = obj.get("tier")
        if tier not in ("A", "B"):
            errors.append('pass requires tier "A" or "B"')
        elif tier == "B":
            rsn = obj.get("reason", "")
            if not isinstance(rsn, str) or "tier-b-block:" not in rsn.lower():
                errors.append(
                    'tier B rows must state "tier-b-block: <cause>" in reason'
                )
    return errors


def iter_jsonl_lines(handle):
    """Yield (lineno, text) for non-blank lines."""
    for lineno, text in enumerate(handle, start=1):
        if text.strip() == "":
            continue
        yield lineno, text


def validate_file(path, label, root, out_lines):
    """Validate one file. Returns (passed, rejected, duplicates, errors)."""
    n_pass = n_reject = n_dup = n_err = 0
    seen = {}
    if path == "-":
        handle = sys.stdin
    else:
        try:
            handle = open(path, "r", encoding="utf-8")
        except OSError as exc:
            out_lines.append("%s: cannot open: %s" % (label, exc))
            return (0, 0, 0, 1)
    with handle:
        for lineno, text in iter_jsonl_lines(handle):
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                out_lines.append("%s:%d: invalid JSON: %s" % (label, lineno, exc))
                n_err += 1
                continue
            for err in validate_record(obj, root):
                out_lines.append("%s:%d: %s" % (label, lineno, err))
                n_err += 1
            decision = obj.get("decision") if isinstance(obj, dict) else None
            if decision == "pass":
                n_pass += 1
            elif decision == "reject":
                n_reject += 1
            if isinstance(obj, dict) and is_nonempty_str(obj.get("identifier", "")):
                key = norm_key(obj["identifier"])
                if key in seen:
                    out_lines.append(
                        "%s:%d: duplicate identifier of line %d (%s)"
                        % (label, lineno, seen[key], key)
                    )
                    n_dup += 1
                    n_err += 1
                else:
                    seen[key] = lineno
    return (n_pass, n_reject, n_dup, n_err)


def cmd_validate(args):
    out_lines = []
    total_err = 0
    for path in args.files:
        label = "<stdin>" if path == "-" else path
        n_pass, n_reject, n_dup, n_err = validate_file(
            path, label, args.root, out_lines
        )
        total_err += n_err
        out_lines.append(
            "%s: pass=%d reject=%d duplicates=%d errors=%d"
            % (label, n_pass, n_reject, n_dup, n_err)
        )
    sys.stdout.write("\n".join(out_lines) + "\n")
    return 1 if total_err else 0


def load_validated(path, label, root, out_lines):
    """Load records from a file already known to be valid.

    Returns (records, ok) where records is a list of (lineno, obj).
    """
    records = []
    try:
        handle = open(path, "r", encoding="utf-8")
    except OSError as exc:
        out_lines.append("%s: cannot open: %s" % (label, exc))
        return (records, False)
    with handle:
        for lineno, text in iter_jsonl_lines(handle):
            records.append((lineno, json.loads(text)))
    return (records, True)


def cmd_merge(args):
    out_lines = []
    lanes = []
    seen_lanes = set()
    for spec in args.inputs:
        if "=" not in spec:
            out_lines.append("bad input %r: expected LANE=PATH" % (spec,))
            sys.stdout.write("\n".join(out_lines) + "\n")
            return 2
        lane, path = spec.split("=", 1)
        lane = lane.strip()
        if not lane or lane in seen_lanes:
            out_lines.append("bad input %r: empty or repeated lane" % (spec,))
            sys.stdout.write("\n".join(out_lines) + "\n")
            return 2
        seen_lanes.add(lane)
        lanes.append((lane, path))
    order = [name.strip() for name in args.keep_order.split(",")]
    if set(order) != seen_lanes or len(order) != len(seen_lanes):
        out_lines.append("keep-order must name each input lane exactly once")
        sys.stdout.write("\n".join(out_lines) + "\n")
        return 2
    by_lane = dict(lanes)
    total_err = 0
    for lane, path in lanes:
        _, _, _, n_err = validate_file(path, path, args.root, out_lines)
        total_err += n_err
    if total_err:
        out_lines.append(
            "merge refused: %d validation error(s), fix inputs first"
            % (total_err,)
        )
        sys.stdout.write("\n".join(out_lines) + "\n")
        return 1
    kept = {}
    first_seen = {}
    dropped = []
    n_records = 0
    for lane in order:
        path = by_lane[lane]
        records, ok = load_validated(path, path, args.root, out_lines)
        if not ok:
            sys.stdout.write("\n".join(out_lines) + "\n")
            return 1
        if args.pass_only:
            records = [
                (n, o) for (n, o) in records if o.get("decision") == "pass"
            ]
        for lineno, obj in records:
            n_records += 1
            key = norm_key(obj["identifier"])
            if key not in kept:
                kept[key] = obj
                first_seen[key] = (lane, path, lineno)
            else:
                dropped.append((key, lane, path, lineno))
    merged = [kept[key] for key in kept]
    parent = os.path.dirname(os.path.abspath(args.output))
    try:
        os.makedirs(parent, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as handle:
            for obj in merged:
                handle.write(
                    json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n"
                )
    except OSError as exc:
        out_lines.append("cannot write %s: %s" % (args.output, exc))
        sys.stdout.write("\n".join(out_lines) + "\n")
        return 1
    if args.report:
        groups = {}
        for key, lane, path, lineno in dropped:
            groups.setdefault(key, []).append(
                {"lane": lane, "file": path, "line": lineno}
            )
        try:
            with open(args.report, "w", encoding="utf-8") as handle:
                for key in sorted(groups):
                    lane, path, lineno = first_seen[key]
                    handle.write(
                        json.dumps(
                            {
                                "identifier": key,
                                "kept": {
                                    "lane": lane,
                                    "file": path,
                                    "line": lineno,
                                },
                                "dropped": groups[key],
                            },
                            sort_keys=True,
                        )
                        + "\n"
                    )
        except OSError as exc:
            out_lines.append("cannot write %s: %s" % (args.report, exc))
            sys.stdout.write("\n".join(out_lines) + "\n")
            return 1
    out_lines.append(
        "merge: files=%d records=%d unique=%d duplicates=%d -> %s"
        % (len(lanes), n_records, len(kept), len(dropped), args.output)
    )
    sys.stdout.write("\n".join(out_lines) + "\n")
    return 0


DEFAULT_INCLUSION = (
    "I1: studies that test or discuss the topic against outcomes "
    "measured at the work-unit level (unit, division, branch, or "
    "organization acting as a unit), with data.",
)

DEFAULT_EXCLUSION = (
    "E1: individual-level outcomes, even when the title names the topic.",
    "E2: opinion pieces without data.",
    "E3: duplicate identifiers (keep first by keep-order).",
    "E4: identifiers failing two-layer verification.",
)

DEFAULT_L1 = (
    "doi.org/<ID> must end HTTP 200 at the article landing page with "
    "article markers; challenge, login, or empty bodies fail Tier A "
    "but may pass as Tier B when L2 matches and the block cause is "
    "recorded."
)

DEFAULT_L2 = (
    "api.crossref.org/works/<ID> title + year must match the candidate."
)

DEFAULT_EVIDENCE_BUDGET = (
    "one staging row + one evidence artifact per claim; trim raw dumps "
    "to verdict-supporting fields."
)

OVER_GATHER_DEFAULT = 1.5


def cmd_init(args):
    task = args.task_dir
    contract_path = os.path.join(task, "contract.json")
    if os.path.exists(contract_path) and not args.force:
        sys.stdout.write(
            "init refused: %s exists (use --force to rewrite)\n"
            % (contract_path,)
        )
        return 1
    topic = args.topic.strip()
    if not topic:
        sys.stdout.write("init: topic must be non-empty\n")
        return 2
    if args.quota < 1:
        sys.stdout.write("init: quota must be a positive integer\n")
        return 2
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    if not sources:
        sys.stdout.write("init: sources must name at least one source\n")
        return 2
    if args.over_gather < 1.0:
        sys.stdout.write("init: over-gather must be >= 1.0\n")
        return 2
    inclusion = list(args.inclusion) if args.inclusion else list(
        DEFAULT_INCLUSION
    )
    exclusion = list(args.exclusion) if args.exclusion else list(
        DEFAULT_EXCLUSION
    )
    if any(not is_nonempty_str(t) for t in inclusion + exclusion):
        sys.stdout.write("init: inclusion/exclusion entries must be non-empty\n")
        return 2
    per_source = args.per_source
    if per_source is not None and per_source < 1:
        sys.stdout.write("init: per-source must be a positive integer\n")
        return 2
    if per_source is None:
        per_source = -(-args.quota // len(sources))
    min_tier_a = args.min_tier_a
    if min_tier_a is None:
        min_tier_a = args.quota
    if (
        isinstance(min_tier_a, bool)
        or not isinstance(min_tier_a, int)
        or min_tier_a < 0
        or min_tier_a > args.quota
    ):
        sys.stdout.write("init: min-tier-a must be between 0 and quota\n")
        return 2
    contract = {
        "topic": topic,
        "inclusion": inclusion,
        "exclusion": exclusion,
        "source_registry": sources,
        "quota": {"total": args.quota, "per_source": per_source},
        "min_tier_a": min_tier_a,
        "notes": "",
        "over_gather_ratio": args.over_gather,
        "verification_contract": {
            "layer1": args.l1.strip() if args.l1 else DEFAULT_L1,
            "layer2": args.l2.strip() if args.l2 else DEFAULT_L2,
        },
        "evidence_budget": (
            args.evidence_budget.strip()
            if args.evidence_budget
            else DEFAULT_EVIDENCE_BUDGET
        ),
    }
    if not is_nonempty_str(contract["verification_contract"]["layer1"]):
        sys.stdout.write("init: layer1 must be non-empty\n")
        return 2
    if not is_nonempty_str(contract["verification_contract"]["layer2"]):
        sys.stdout.write("init: layer2 must be non-empty\n")
        return 2
    if not is_nonempty_str(contract["evidence_budget"]):
        sys.stdout.write("init: evidence-budget must be non-empty\n")
        return 2
    try:
        os.makedirs(os.path.join(task, "workspace"), exist_ok=True)
        os.makedirs(os.path.join(task, "evidence"), exist_ok=True)
        with open(contract_path, "w", encoding="utf-8") as handle:
            handle.write(
                json.dumps(contract, sort_keys=True, indent=2,
                           ensure_ascii=False)
                + "\n"
            )
    except OSError as exc:
        sys.stdout.write("cannot write %s: %s\n" % (contract_path, exc))
        return 1
    sys.stdout.write(
        "init: %s (quota=%d sources=%d per_source=%d)\n"
        % (contract_path, args.quota, len(sources), per_source)
    )
    return 0


MANIFEST_REQUIRED = (
    "bytes",
    "filename",
    "identifier",
    "reason",
    "source_url",
    "verdict",
)

MANIFEST_VERDICTS = ("relevant", "not_relevant", "download_failed")

NEEDS_REQUIRED = ("identifier", "reason", "queued_by", "status")

NEEDS_STATUSES = ("queued", "promoted", "dropped")


def safe_rel(path):
    """Return a normalized relative path, or None if it escapes base."""
    norm = os.path.normpath(path.strip().replace("\\", "/"))
    if not norm or norm == "." or os.path.isabs(norm):
        return None
    if norm == ".." or norm.startswith("../"):
        return None
    return norm


def validate_manifest_row(obj, ev_dir):
    """Return error strings for one manifest row (empty means valid)."""
    if not isinstance(obj, dict):
        return ["manifest row is not a JSON object"]
    errors = []
    for field in MANIFEST_REQUIRED:
        if field not in obj:
            errors.append("manifest missing field %r" % (field,))
    if errors:
        return errors
    verdict = obj["verdict"]
    if verdict not in MANIFEST_VERDICTS:
        errors.append(
            "verdict must be one of relevant|not_relevant|download_failed"
        )
    if not is_nonempty_str(obj["identifier"]):
        errors.append("manifest identifier must be a non-empty string")
    if not is_nonempty_str(obj["reason"]):
        errors.append("manifest reason must be a non-empty string")
    if not is_nonempty_str(obj["source_url"]):
        errors.append("manifest source_url must be a non-empty string")
    quote = obj.get("evidence_quote")
    if quote is not None and (
        not isinstance(quote, str) or len(quote) > 300
    ):
        errors.append("evidence_quote must be a string of max 300 chars")
    raw = obj["bytes"]
    if verdict == "download_failed":
        if raw != "download_failed":
            errors.append(
                'download_failed verdict requires bytes "download_failed"'
            )
        return errors
    tier = obj.get("tier")
    if tier not in ("A", "B"):
        errors.append('manifest rows must carry tier "A" or "B"')
    elif tier == "A":
        if not isinstance(quote, str) or not quote.strip():
            errors.append("tier A rows must carry a non-empty evidence_quote")
    elif tier == "B":
        rsn = obj.get("reason", "")
        if not isinstance(rsn, str) or "tier-b-block:" not in rsn.lower():
            errors.append(
                'tier B rows must state "tier-b-block: <cause>" in reason'
            )
    fname = obj["filename"]
    if not isinstance(fname, str) or safe_rel(fname) is None:
        errors.append("filename must be a relative path inside the evidence dir")
    else:
        full = os.path.join(ev_dir, safe_rel(fname))
        if not os.path.isfile(full):
            errors.append("manifest file not found: %s" % (fname.strip(),))
        elif os.path.getsize(full) == 0:
            errors.append("manifest file is empty: %s" % (fname.strip(),))
        elif isinstance(raw, bool) or not isinstance(raw, int):
            errors.append("bytes must be the integer file size")
        elif raw != os.path.getsize(full):
            errors.append(
                "bytes %d != file size %d for %s"
                % (raw, os.path.getsize(full), fname.strip())
            )
    return errors


def validate_needs_row(obj):
    """Return error strings for one needs-richer-check row."""
    if not isinstance(obj, dict):
        return ["needs row is not a JSON object"]
    errors = []
    for field in NEEDS_REQUIRED:
        if field not in obj:
            errors.append("needs row missing field %r" % (field,))
    if errors:
        return errors
    if not is_nonempty_str(obj["identifier"]):
        errors.append("needs identifier must be a non-empty string")
    if not is_nonempty_str(obj["reason"]):
        errors.append("needs reason must be a non-empty string")
    if not is_nonempty_str(obj["queued_by"]):
        errors.append("needs queued_by must be a non-empty string")
    if obj["status"] not in NEEDS_STATUSES:
        errors.append("needs status must be one of queued|promoted|dropped")
    return errors


def load_jsonl_rows(path, label, out_lines):
    """Load (lineno, obj) rows; appends JSON errors, returns (rows, ok)."""
    rows = []
    try:
        handle = open(path, "r", encoding="utf-8")
    except OSError as exc:
        out_lines.append("%s: cannot open: %s" % (label, exc))
        return (rows, False)
    ok = True
    with handle:
        for lineno, text in iter_jsonl_lines(handle):
            try:
                rows.append((lineno, json.loads(text)))
            except json.JSONDecodeError as exc:
                out_lines.append(
                    "%s:%d: invalid JSON: %s" % (label, lineno, exc)
                )
                ok = False
    return (rows, ok)


def package_readme(contract, counts, files, missing):
    """Build the deterministic package README text."""
    lines = []
    if contract and is_nonempty_str(contract.get("topic", "")):
        lines.append("# Package: %s" % (contract["topic"].strip(),))
        lines.append("")
        quota = contract.get("quota", {})
        sources = contract.get("source_registry", [])
        lines.append(
            "Contract: quota %s (%s per source); sources: %s."
            % (
                quota.get("total", "not recorded"),
                quota.get("per_source", "not recorded"),
                ", ".join(sources) if sources else "not recorded",
            )
        )
        lines.append(
            "Over-gather ratio: %s."
            % (contract.get("over_gather_ratio", "not recorded"),)
        )
        lines.append("")
    else:
        lines.append("# very-deep-search package")
        lines.append("")
    lines.append("## Contents")
    lines.append("")
    for name in sorted(files):
        lines.append("- %s" % (name,))
    lines.append("")
    if missing:
        lines.append("Not provided: %s." % (", ".join(sorted(missing)),))
        lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append("final pass records: %d" % (counts["final_pass"],))
    lines.append("Tier-A passes: %d" % (counts["tier_a"],))
    lines.append("manifest rows: %d" % (counts["manifest"],))
    lines.append("evidence files: %d" % (counts["evidence"],))
    lines.append("")
    lines.append("## Reproduce")
    lines.append("")
    lines.append("From this directory, with vds.py available:")
    lines.append("")
    lines.append("    vds.py validate final.jsonl --root .")
    lines.append("")
    lines.append(
        "Then run each record's reverify commands and compare "
        "against its evidence file under evidence/."
    )
    lines.append("")
    return "\n".join(lines)


def cmd_package(args):
    out_lines = []
    total_err = 0
    ev_dir = (
        args.evidence_dir
        if args.evidence_dir
        else os.path.join(args.root, "evidence")
    )
    _, _, _, n_err = validate_file(
        args.final, args.final, args.root, out_lines
    )
    total_err += n_err
    if args.merged:
        _, _, _, n_err = validate_file(
            args.merged, args.merged, args.root, out_lines
        )
        total_err += n_err
    manifest_rows, ok = load_jsonl_rows(
        args.manifest, args.manifest, out_lines
    )
    if not ok:
        total_err += 1
    manifest_ids = set()
    for lineno, obj in manifest_rows:
        for err in validate_manifest_row(obj, ev_dir):
            out_lines.append("%s:%d: %s" % (args.manifest, lineno, err))
            total_err += 1
        if isinstance(obj, dict) and is_nonempty_str(obj.get("identifier", "")):
            manifest_ids.add(norm_key(obj["identifier"]))
    if args.needs_richer:
        needs_rows, ok = load_jsonl_rows(
            args.needs_richer, args.needs_richer, out_lines
        )
        if not ok:
            total_err += 1
        for lineno, obj in needs_rows:
            for err in validate_needs_row(obj):
                out_lines.append(
                    "%s:%d: %s" % (args.needs_richer, lineno, err)
                )
                total_err += 1
    contract = None
    if args.contract:
        try:
            with open(args.contract, "r", encoding="utf-8") as handle:
                contract = json.load(handle)
        except (OSError, ValueError) as exc:
            out_lines.append("%s: cannot load: %s" % (args.contract, exc))
            total_err += 1
            contract = None
    final_rows, ok = load_validated(args.final, args.final, args.root, out_lines)
    if not ok:
        total_err += 1
        final_rows = []
    pass_ids = set()
    pass_evidence = set()
    tier_a_ids = set()
    for _, obj in final_rows:
        if not isinstance(obj, dict):
            continue
        if obj.get("decision") != "pass":
            continue
        if is_nonempty_str(obj.get("identifier", "")):
            pass_ids.add(norm_key(obj["identifier"]))
            if obj.get("tier") == "A":
                tier_a_ids.add(norm_key(obj["identifier"]))
        rel = obj.get("evidence_ref", "")
        if isinstance(rel, str) and rel.strip():
            pass_evidence.add(rel.strip())
    for key in sorted(pass_ids - manifest_ids):
        out_lines.append(
            "%s: no manifest row for final identifier %s"
            % (args.manifest, key)
        )
        total_err += 1
    if isinstance(contract, dict):
        min_a = contract.get("min_tier_a")
        if min_a is None:
            quota = contract.get("quota", {})
            if isinstance(quota, dict) and isinstance(
                quota.get("total"), int
            ):
                min_a = quota["total"]
            else:
                min_a = len(pass_ids)
        if (
            isinstance(min_a, bool)
            or not isinstance(min_a, int)
            or min_a < 0
        ):
            out_lines.append(
                "%s: min_tier_a must be a non-negative integer"
                % (args.contract,)
            )
            total_err += 1
        elif len(tier_a_ids) < min_a:
            out_lines.append(
                "tier-a shortfall: %d Tier-A passes < min_tier_a %d"
                % (len(tier_a_ids), min_a)
            )
            total_err += 1
    copies = []
    optionals = {
        "contract.json": args.contract,
        "merged.jsonl": args.merged,
        "excluded-from-final.md": args.excluded,
        "needs-richer-check.jsonl": args.needs_richer,
        "disputes.md": args.disputes,
    }
    copies.append((args.final, "final.jsonl"))
    copies.append((args.manifest, "manifest.jsonl"))
    for dest, src in sorted(optionals.items()):
        if src:
            copies.append((src, dest))
    for rel in sorted(pass_evidence):
        safe = safe_rel(rel)
        if safe is None:
            out_lines.append("evidence_ref escapes task root: %s" % (rel,))
            total_err += 1
            continue
        copies.append((os.path.join(args.root, safe), safe))
    for _, obj in manifest_rows:
        if not isinstance(obj, dict):
            continue
        if obj.get("verdict") == "download_failed":
            continue
        fname = obj.get("filename", "")
        if isinstance(fname, str) and safe_rel(fname) is not None:
            copies.append(
                (
                    os.path.join(ev_dir, safe_rel(fname)),
                    "evidence/" + safe_rel(fname),
                )
            )
    if total_err:
        out_lines.append(
            "package refused: %d error(s), fix inputs first" % (total_err,)
        )
        sys.stdout.write("\n".join(out_lines) + "\n")
        return 1
    out_dir = args.output
    if os.path.exists(out_dir):
        if not os.path.isdir(out_dir):
            out_lines.append("package refused: %s is not a directory" % (out_dir,))
            sys.stdout.write("\n".join(out_lines) + "\n")
            return 1
        if os.listdir(out_dir) and not args.force:
            out_lines.append(
                "package refused: %s not empty (use --force)" % (out_dir,)
            )
            sys.stdout.write("\n".join(out_lines) + "\n")
            return 1
        if args.force:
            try:
                shutil.rmtree(out_dir)
            except OSError as exc:
                out_lines.append("cannot clear %s: %s" % (out_dir, exc))
                sys.stdout.write("\n".join(out_lines) + "\n")
                return 1
    payloads = {}
    for src, dest in copies:
        try:
            with open(src, "rb") as handle:
                data = handle.read()
        except OSError as exc:
            out_lines.append("cannot read %s: %s" % (src, exc))
            sys.stdout.write("\n".join(out_lines) + "\n")
            return 1
        if dest in payloads and payloads[dest] != data:
            out_lines.append(
                "package refused: conflicting bytes for %s" % (dest,)
            )
            sys.stdout.write("\n".join(out_lines) + "\n")
            return 1
        payloads[dest] = data
    counts = {
        "final_pass": len(pass_ids),
        "tier_a": len(tier_a_ids),
        "manifest": len(manifest_rows),
        "evidence": len(
            [d for d in payloads if d != "final.jsonl"
             and d != "manifest.jsonl"
             and d not in optionals]
        ),
    }
    files = sorted(payloads) + ["README.md"]
    missing = sorted(
        name for name, src in optionals.items() if not src
    )
    payloads["README.md"] = package_readme(
        contract, counts, files, missing
    ).encode("utf-8")
    try:
        for dest in sorted(payloads):
            full = os.path.join(out_dir, dest)
            parent = os.path.dirname(full)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(full, "wb") as handle:
                handle.write(payloads[dest])
    except OSError as exc:
        out_lines.append("cannot write %s: %s" % (out_dir, exc))
        sys.stdout.write("\n".join(out_lines) + "\n")
        return 1
    sys.stdout.write(
        "\n".join(
            out_lines
            + [
                "package: final=%d manifest=%d evidence=%d tier_a=%d -> %s"
                % (
                    counts["final_pass"],
                    counts["manifest"],
                    counts["evidence"],
                    counts["tier_a"],
                    out_dir,
                )
            ]
        )
        + "\n"
    )
    return 0


JEV_ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
JEV_MODEL = "typesafe/jev-1.14"
JEV_PATH = "/api/alpha/decisions"
JEV_KEY_ENV = "OPENROUTER_API_KEY"
JEV_MAX_ATTEMPTS = 3
JEV_TIMEOUT_SECS = 30
JEV_RETRY_SLEEP_SECS = (1, 2)
JEV_ABSTRACT_CHARS_DEFAULT = 1500

JEV_RELEVANCE_LEVELS = (
    "Unrelated: shares no subject matter with the topic.",
    "Adjacent field only: same broad discipline, different subject.",
    "Shared vocabulary, different problem: keywords overlap but the "
    "study addresses another question.",
    "Background context: useful setting for the topic, no direct findings.",
    "Partially relevant: touches one aspect of the scope without evidence.",
    "Moderately relevant: addresses the topic with limited or indirect "
    "evidence.",
    "Relevant: directly studies the topic with supporting data.",
    "Strongly relevant: core findings answer part of the scope.",
    "Highly relevant: central to the topic and scope with solid evidence.",
    "Definitive: directly answers the scope question with strong evidence.",
)
JEV_RELEVANCE_INSTRUCTIONS = (
    "How relevant is this record's content to the research topic and scope?"
)
JEV_SCOPE_INSTRUCTIONS = "Does this record fall inside the stated scope?"
JEV_SCOPE_TRUE = "The record's subject and findings fall inside the scope."
JEV_SCOPE_FALSE = "The record falls outside the stated scope."

DOI_RE = re.compile(r"^10\.\d{4,}/\S+$")


def jev_band(score_100):
    if score_100 >= 70:
        return "relevant"
    if score_100 >= 50:
        return "borderline"
    return "off-topic"


def jev_endpoint_url():
    """Pinned decisions endpoint. VDS_JEV_ENDPOINT overrides the base URL
    for mocked tests only; the API path stays pinned."""
    base = os.environ.get("VDS_JEV_ENDPOINT")
    if base:
        return base.rstrip("/") + JEV_PATH
    return JEV_ENDPOINT


def jev_request_body(topic, scope, title, abstract):
    return {
        "model": JEV_MODEL,
        "state": {
            "topic": topic,
            "scope": scope,
            "title": title,
            "abstract": abstract,
        },
        "questions": {
            "relevance": {
                "type": "score",
                "instructions": JEV_RELEVANCE_INSTRUCTIONS,
                "criteria": list(JEV_RELEVANCE_LEVELS),
            },
            "meets_scope": {
                "type": "noul",
                "instructions": JEV_SCOPE_INSTRUCTIONS,
                "criteria": {"true": JEV_SCOPE_TRUE, "false": JEV_SCOPE_FALSE},
            },
        },
    }


def jev_call_once(url, key, body):
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=JEV_TIMEOUT_SECS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def jev_transient(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in (408, 429, 500, 502, 503, 504)
    return isinstance(exc, urllib.error.URLError)


def jev_call(url, key, body):
    """Call the decisions endpoint with retries. Returns the parsed
    response, or raises RuntimeError after transient retries."""
    last = None
    for attempt in range(JEV_MAX_ATTEMPTS):
        try:
            return jev_call_once(url, key, body)
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code == 401:
                raise RuntimeError("unauthorized (HTTP 401): check the key")
            if not jev_transient(exc):
                raise RuntimeError("decisions HTTP %d" % (exc.code,))
        except (urllib.error.URLError, ValueError) as exc:
            last = exc
        if attempt < JEV_MAX_ATTEMPTS - 1:
            time.sleep(JEV_RETRY_SLEEP_SECS[attempt])
    raise RuntimeError("decisions call failed after %d attempts: %s"
                       % (JEV_MAX_ATTEMPTS, last))


def jev_parse_response(resp):
    """Parse one decisions response into a score dict. Raises ValueError
    on any contract violation."""
    if not isinstance(resp, dict):
        raise ValueError("response is not a JSON object")
    answers = resp.get("answers")
    if not isinstance(answers, dict):
        raise ValueError("response has no answers object")
    rel = answers.get("relevance")
    if not isinstance(rel, dict) or rel.get("type") != "score":
        raise ValueError("missing relevance score answer")
    score = rel.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError("relevance score is not a number")
    if score < 0 or score > 9:
        raise ValueError("relevance score out of range 0-9")
    conf = rel.get("confidence")
    if conf is not None and (
        isinstance(conf, bool) or not isinstance(conf, (int, float))
    ):
        raise ValueError("relevance confidence is not a number")
    scope = answers.get("meets_scope")
    if not isinstance(scope, dict) or scope.get("type") != "noul":
        raise ValueError("missing meets_scope noul answer")
    prob = scope.get("noul")
    if isinstance(prob, bool) or not isinstance(prob, (int, float)):
        raise ValueError("meets_scope noul is not a number")
    usage = resp.get("usage")
    cost = None
    if isinstance(usage, dict) and usage.get("cost") is not None:
        cost = usage["cost"]
        if isinstance(cost, bool) or not isinstance(cost, (int, float)):
            raise ValueError("usage cost is not a number")
    return {
        "score_100": round(score / 9 * 100, 1),
        "confidence": conf,
        "meets_scope": prob >= 0.5,
        "model": resp.get("model") or JEV_MODEL,
        "cost": cost,
    }


def jev_extract_doi(record):
    ident = record.get("identifier", "")
    if isinstance(ident, str) and DOI_RE.match(ident.strip()):
        return ident.strip()
    url = record.get("source_url", "")
    if isinstance(url, str) and "doi.org/" in url:
        tail = url.split("doi.org/", 1)[1].split()[0]
        tail = tail.split("?")[0].split("#")[0].strip().rstrip("/")
        if DOI_RE.match(tail):
            return tail
    return ""


def jev_extract_text(evidence_path):
    """Extract scoring text from an evidence file. Returns (text, error)."""
    try:
        with open(evidence_path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        return ("", "cannot read evidence: %s" % (exc,))
    if evidence_path.lower().endswith(".pdf"):
        pdftotext = shutil.which("pdftotext")
        if not pdftotext:
            return ("", "pdftotext not found: cannot extract PDF text")
        try:
            proc = subprocess.run(
                [pdftotext, evidence_path, "-"],
                capture_output=True,
                timeout=60,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return ("", "pdftotext failed: %s" % (exc,))
        if proc.returncode != 0:
            return ("", "pdftotext failed (exit %d)" % (proc.returncode,))
        raw = proc.stdout
    text = " ".join(raw.decode("utf-8", errors="replace").split())
    if not text:
        return ("", "evidence has no extractable text")
    return (text, "")


def jev_read_key(key_file):
    if key_file:
        try:
            with open(key_file, "r", encoding="utf-8") as handle:
                key = handle.read().strip()
        except OSError as exc:
            return ("", "cannot read key file: %s" % (exc,))
        if not key:
            return ("", "key file is empty")
        return (key, "")
    key = os.environ.get(JEV_KEY_ENV, "").strip()
    if not key:
        return ("", "no key: pass --key-file or set %s" % (JEV_KEY_ENV,))
    return (key, "")


def jev_load_scored(out_path):
    """Load already-scored rows keyed by identifier. Missing file means
    nothing scored yet. Returns (rows, error)."""
    rows = {}
    try:
        handle = open(out_path, "r", encoding="utf-8")
    except FileNotFoundError:
        return (rows, "")
    except OSError as exc:
        return (rows, "cannot read output: %s" % (exc,))
    with handle:
        for lineno, text in iter_jsonl_lines(handle):
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                return (rows, "output line %d: invalid JSON: %s"
                        % (lineno, exc))
            ident = obj.get("identifier") if isinstance(obj, dict) else None
            if not is_nonempty_str(ident):
                return (rows, "output line %d: missing identifier" % (lineno,))
            rows[norm_key(ident)] = obj
    return (rows, "")


def cmd_ask(args):
    if args.backend != "jev":
        sys.stdout.write("ask: unknown backend %r (only 'jev')\n"
                         % (args.backend,))
        return 2
    if args.abstract_chars < 1:
        sys.stdout.write("ask: --abstract-chars must be >= 1\n")
        return 2
    key, err = jev_read_key(args.key_file)
    if err:
        sys.stdout.write("ask: %s\n" % (err,))
        return 2
    if len(JEV_RELEVANCE_LEVELS) != 10:
        sys.stdout.write("ask: relevance criteria must be exactly 10 levels "
                         "(API limit)\n")
        return 2
    package = args.package
    final_path = os.path.join(package, "final.jsonl")
    out_lines = []
    _, _, _, n_err = validate_file(final_path, "final.jsonl", package,
                                   out_lines)
    if n_err:
        out_lines.append("ask refused: final.jsonl has %d errors; "
                         "fix them before spending scoring calls" % (n_err,))
        sys.stdout.write("\n".join(out_lines) + "\n")
        return 1
    records = []
    with open(final_path, "r", encoding="utf-8") as handle:
        for _, text in iter_jsonl_lines(handle):
            records.append(json.loads(text))
    eligible, skipped = [], 0
    for record in records:
        if record.get("decision") == "pass" and record.get("tier") == "A":
            eligible.append(record)
        else:
            skipped += 1
    if not eligible:
        sys.stdout.write("ask jev: no Tier-A passes to score "
                         "(skipped=%d)\n" % (skipped,))
        return 0
    abstracts = []
    for record in eligible:
        rel = record["evidence_ref"].strip()
        full = rel if os.path.isabs(rel) else os.path.join(package, rel)
        text, err = jev_extract_text(full)
        if err:
            sys.stdout.write("ask: %s: %s\n" % (record["identifier"], err))
            return 1
        abstracts.append(text[:args.abstract_chars])
    scored, err = jev_load_scored(args.out)
    if err:
        sys.stdout.write("ask: %s\n" % (err,))
        return 1
    try:
        appender = open(args.out, "a", encoding="utf-8")
    except OSError as exc:
        sys.stdout.write("ask: cannot write output: %s\n" % (exc,))
        return 2
    url = jev_endpoint_url()
    rows, n_fresh = [], 0
    with appender:
        for record, abstract in zip(eligible, abstracts):
            ident = record["identifier"]
            hit = scored.get(norm_key(ident))
            if hit is not None:
                rows.append((ident, hit, True))
                continue
            body = jev_request_body(args.topic, args.scope,
                                    record.get("title", ""), abstract)
            try:
                parsed = jev_parse_response(jev_call(url, key, body))
            except (RuntimeError, ValueError) as exc:
                sys.stdout.write("ask: %s: %s\n" % (ident, exc))
                return 1
            row = {"identifier": ident,
                   "doi": jev_extract_doi(record)}
            row.update(parsed)
            appender.write(json.dumps(row, sort_keys=True,
                                      ensure_ascii=False) + "\n")
            appender.flush()
            rows.append((ident, row, False))
            n_fresh += 1
    ordered = [row for _, row, _ in rows]
    try:
        with open(args.out, "w", encoding="utf-8") as handle:
            for row in ordered:
                handle.write(json.dumps(row, sort_keys=True,
                                        ensure_ascii=False) + "\n")
    except OSError as exc:
        sys.stdout.write("ask: cannot rewrite output: %s\n" % (exc,))
        return 1
    table = ["ask jev: topic=%r eligible=%d skipped=%d"
             % (args.topic, len(eligible), skipped)]
    total_cost, n_cached = 0.0, 0
    cost_known = True
    for ident, row, cached in rows:
        band = jev_band(row["score_100"])
        conf = row["confidence"]
        notes = []
        if conf is None or conf < 0.6:
            notes.append("uncertain")
        if cached:
            notes.append("cached")
            n_cached += 1
        if row["cost"] is None:
            cost_known = False
        else:
            total_cost += row["cost"]
        table.append("%s score=%s band=%s conf=%s scope=%s%s" % (
            ident, row["score_100"], band, conf,
            "yes" if row["meets_scope"] else "no",
            " " + " ".join(notes) if notes else "",
        ))
    table.append("ask jev: fresh=%d cached=%d total_cost=%s"
                 % (n_fresh, n_cached,
                    round(total_cost, 6) if cost_known else "n/a"))
    sys.stdout.write("\n".join(table) + "\n")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="vds.py",
        description="Scaffold, validate, merge, and package "
        "very-deep-search tasks. Offline, deterministic, standard "
        "library only.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_init = sub.add_parser(
        "init", help="scaffold a task directory with an input contract"
    )
    p_init.add_argument("task_dir", help="task directory to create")
    p_init.add_argument("--topic", required=True, help="research topic")
    p_init.add_argument(
        "--quota", required=True, type=int, help="total unique passes wanted"
    )
    p_init.add_argument(
        "--sources",
        required=True,
        help="comma-separated source registry names",
    )
    p_init.add_argument(
        "--per-source", type=int, default=None,
        help="per-source target (default: quota split across sources)",
    )
    p_init.add_argument(
        "--min-tier-a", type=int, default=None,
        help="minimum Tier-A passes (default: quota total)",
    )
    p_init.add_argument(
        "--over-gather", type=float, default=OVER_GATHER_DEFAULT,
        help="over-gather ratio, >= 1.0 (default: 1.5)",
    )
    p_init.add_argument(
        "--inclusion", action="append", default=None,
        help="inclusion criterion (repeatable; replaces default)",
    )
    p_init.add_argument(
        "--exclusion", action="append", default=None,
        help="exclusion criterion (repeatable; replaces defaults)",
    )
    p_init.add_argument(
        "--l1", default=None, help="Layer-1 contract (default: journal/DOI)"
    )
    p_init.add_argument(
        "--l2", default=None, help="Layer-2 contract (default: journal/DOI)"
    )
    p_init.add_argument(
        "--evidence-budget", default=None, help="evidence budget statement"
    )
    p_init.add_argument(
        "--force", action="store_true",
        help="rewrite an existing contract.json",
    )
    p_init.set_defaults(func=cmd_init)
    p_val = sub.add_parser(
        "validate", help="validate staging files against the record schema"
    )
    p_val.add_argument("files", nargs="+", help="JSONL files ('-' = stdin)")
    p_val.add_argument(
        "--root",
        default=".",
        help="base directory for evidence_ref paths (default: .)",
    )
    p_val.set_defaults(func=cmd_validate)
    p_merge = sub.add_parser(
        "merge", help="validate, then merge lane files with global dedup"
    )
    p_merge.add_argument(
        "inputs", nargs="+", help="lane inputs as LANE=PATH (repeatable)"
    )
    p_merge.add_argument(
        "--keep-order",
        required=True,
        help="comma-separated lane names, winner first",
    )
    p_merge.add_argument("-o", "--output", required=True, help="merged file")
    p_merge.add_argument(
        "--report", default=None, help="optional duplicate-report JSONL file"
    )
    p_merge.add_argument(
        "--pass-only",
        action="store_true",
        help="merge pass rows only (final merge mode)",
    )
    p_merge.add_argument(
        "--root",
        default=".",
        help="base directory for evidence_ref paths (default: .)",
    )
    p_merge.set_defaults(func=cmd_merge)
    p_pkg = sub.add_parser(
        "package", help="verify and assemble the deterministic final package"
    )
    p_pkg.add_argument(
        "--final", required=True, help="final.jsonl (proof-backed subset)"
    )
    p_pkg.add_argument(
        "--manifest", required=True, help="content manifest JSONL"
    )
    p_pkg.add_argument(
        "-o", "--output", required=True, help="package directory to create"
    )
    p_pkg.add_argument("--merged", default=None, help="merged.jsonl (all passes)")
    p_pkg.add_argument(
        "--contract", default=None, help="task contract.json"
    )
    p_pkg.add_argument(
        "--excluded", default=None, help="excluded-from-final.md"
    )
    p_pkg.add_argument(
        "--needs-richer", default=None, help="needs-richer-check.jsonl"
    )
    p_pkg.add_argument(
        "--disputes", default=None, help="adjudication disputes file"
    )
    p_pkg.add_argument(
        "--root",
        default=".",
        help="base directory for evidence_ref paths (default: .)",
    )
    p_pkg.add_argument(
        "--evidence-dir",
        default=None,
        help="evidence directory (default: <root>/evidence)",
    )
    p_pkg.add_argument(
        "--force", action="store_true",
        help="clear a non-empty output directory first",
    )
    p_pkg.set_defaults(func=cmd_package)
    p_ask = sub.add_parser(
        "ask", help="score Tier-A finals for relevance (online, key needed)"
    )
    p_ask.add_argument(
        "backend", choices=["jev"],
        help="scoring backend (only 'jev')",
    )
    p_ask.add_argument(
        "--package", required=True, help="package directory (final.jsonl)"
    )
    p_ask.add_argument("--topic", required=True, help="research topic")
    p_ask.add_argument(
        "--scope", required=True, help="scope statement scored against"
    )
    p_ask.add_argument(
        "--key-file", default=None,
        help="file holding the OpenRouter key (or set OPENROUTER_API_KEY)",
    )
    p_ask.add_argument(
        "--out", required=True, help="scores sidecar JSONL to write"
    )
    p_ask.add_argument(
        "--abstract-chars", type=int,
        default=JEV_ABSTRACT_CHARS_DEFAULT,
        help="evidence text chars sent per record (default: 1500)",
    )
    p_ask.set_defaults(func=cmd_ask)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
