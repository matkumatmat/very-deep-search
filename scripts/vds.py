#!/usr/bin/env python3
"""vds - validate and merge JSONL staging files (very-deep-search).

Standard library only. Offline. Deterministic: the same inputs always
produce byte-identical outputs.

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
import sys

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


def build_parser():
    parser = argparse.ArgumentParser(
        prog="vds.py",
        description="Validate and merge very-deep-search JSONL staging "
        "files. Offline, deterministic, standard library only.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
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
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
