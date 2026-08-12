#!/usr/bin/env python3
"""
telegram/tools/validate_content_json.py -- content JSON validator (2026-08-10)
--------------------------------------------------------------------------------
Pranav's ask: as more faculty bring their own JSON (each potentially adding
their own extra display fields), how do we guarantee the fields the BOT
CODE actually depends on are always present and correctly shaped, so a
faculty's oddly-shaped file fails loudly here -- not as a silent
`KeyError`/`None` mid-conversation on a real student's screen?

This is NOT a content-quality/fact-checking tool (that's a separate,
deeper concern already handled elsewhere -- e.g. first_run's
extract_book_questions.py/diff_book_vs_index.py for the Question Bank
Book). This only checks: does this record have what QuestionBank/McqBank
(exam_hub_bot.py) actually read from it, correctly typed, internally
consistent? Everything else (extra faculty-specific display fields,
`submodule_code`, `is_miq`, whatever a faculty wants to carry) is left
alone -- ADDITIONAL fields never fail validation, only MISSING/malformed
CORE ones do.

CORE_FIELDS below was built by grepping every `q.get(...)`/`q[...]`
access in exam_hub_bot.py's QuestionBank/McqBank classes and its
send_question/send_answer/send_pdf/send_mcq/handle_mcq_answer functions --
not guessed. If exam_hub_bot.py starts reading a new field, add it here in
the same pass (see this file's own comment above CORE_FIELDS).

THREE SEVERITIES, never silently resolved:
  - ERROR   -- the bot WILL misbehave without this (crash, wrong answer
              shown, a record permanently unreachable). Must be fixed.
  - WARNING -- the bot has a safe fallback (falls back to "" or "Unknown"),
              but the student sees degraded content. Should be fixed.
  - (no io) -- an extra field the bot never reads is never flagged at all,
              at any severity -- that's the whole point of this tool.

USAGE:
    python telegram/tools/validate_content_json.py               # every
                                                                   # content
                                                                   # file
                                                                   # discoverable
                                                                   # from
                                                                   # tenants.json
    python telegram/tools/validate_content_json.py --file <path> --kind mcq
    python telegram/tools/validate_content_json.py --json          # machine-
                                                                     # readable
                                                                     # report

Also importable -- telegram/database/analytics.py's fetch_content_health()
calls validate_all() directly so the dashboard's Content Health view is
always a fresh, live run, never a stale cached report.
"""

import re
import sys
import json
import argparse
from pathlib import Path

_HTML_TAG_RE = re.compile(r"<[^>]+>")

# Added 2026-08-10 after a real production leak: one source docx marked its
# correct option inline with "✓ CORRECT" (not the "✓ CORRECT ANSWER" the
# converter's stripping regex actually matched), so the checkmark reached
# 50 students' screens BEFORE they answered -- defeating the point of an
# MCQ. Scoped to a literal checkmark glyph only (not the bare word
# "correct", which shows up legitimately in normal question phrasing like
# "which of the following is CORRECT" -- that's not a leak, don't flag it).
_LEAKED_MARKER_RE = re.compile(r"[✓✔✅]")  # ✓ ✔ ✅

REPO_ROOT = Path(__file__).resolve().parents[2]
TENANTS_PATH = REPO_ROOT / "telegram" / "config" / "tenants.json"

# ---------------------------------------------------------------------------
# CORE_FIELDS -- the bot-critical field contract, derived from
# exam_hub_bot.py's actual field accesses (2026-08-10). Keep this in sync
# with that file -- see this module's own docstring.
# ---------------------------------------------------------------------------

MCQ_REQUIRED = ["mcq_id", "question_html", "options", "correct_option"]
# chapter_slug/chapter_label missing -> groups under "unknown"; exam_type/year
# missing -> groups under "OTHER"/"Unknown" (McqBank.exam_types()/years() both
# have an explicit .get(..., default) fallback); answer_html missing -> a
# correct/incorrect MCQ result with a blank explanation. All real, all
# survivable, none of them crash -- hence WARNING, not ERROR.
MCQ_RECOMMENDED = ["chapter_slug", "chapter_label", "exam_type", "year", "answer_html"]

DESC_REQUIRED = ["book_id", "question_html", "chapter_slug", "answer_html"]
DESC_RECOMMENDED = ["chapter_label", "qno_text", "marks_text"]
# QuestionBank._detect_exam_type()/_detect_year() only ever run as a fallback
# off src_text when explicit exam_type/year fields are absent -- so a record
# needs ONE of {exam_type+year} OR {src_text}, not both. Neither present means
# the record silently sorts as "OTHER"/"Unknown" forever.


def _is_present(record: dict, field: str) -> bool:
    """Present AND non-empty -- a field set to "" or None counts as missing
    (the bot's own .get(field, default) can't tell "explicitly blank" from
    "never set" either, so neither should this validator).

    HTML TAGS ARE STRIPPED BEFORE THE EMPTINESS CHECK -- added 2026-08-10
    after a real production bug slipped past this validator entirely: all
    650 of a converter's MCQ records had `question_html: "<p></p>"` --
    syntactically a non-empty string, so the original strip()-only check
    said "present," while every one of those questions rendered completely
    blank to real students (options visible, question text empty). A
    student-visible content field with tags but no actual TEXT is exactly
    as broken as one that's the empty string outright -- this validator
    should never again call that "present." Applies uniformly to every
    field, not just question_html/answer_html specifically -- a bare "<p>
    </p>" would be just as wrong on a hypothetical future HTML-bearing
    field this list hasn't been extended to yet."""
    val = record.get(field)
    if val is None:
        return False
    if isinstance(val, str):
        text_only = _HTML_TAG_RE.sub("", val).strip()
        if text_only == "":
            return False
    if isinstance(val, dict) and len(val) == 0:
        return False
    return True


def validate_mcq_record(record: dict, index: int) -> list:
    """Returns a list of {severity, record_id, field, message} dicts."""
    issues = []
    rid = record.get("mcq_id") or f"<record #{index}, no mcq_id>"

    for field in MCQ_REQUIRED:
        if not _is_present(record, field):
            issues.append({"severity": "ERROR", "record_id": rid, "field": field,
                            "message": f"Required field '{field}' is missing or empty."})

    for field in MCQ_RECOMMENDED:
        if not _is_present(record, field):
            issues.append({"severity": "WARNING", "record_id": rid, "field": field,
                            "message": f"Recommended field '{field}' is missing -- "
                                       f"the bot will fall back to a blank/generic value."})

    options = record.get("options")
    if isinstance(options, dict):
        if len(options) < 2:
            issues.append({"severity": "ERROR", "record_id": rid, "field": "options",
                            "message": f"'options' has only {len(options)} entries -- needs at least 2."})
        correct = record.get("correct_option")
        if correct is not None and correct not in options:
            issues.append({"severity": "ERROR", "record_id": rid, "field": "correct_option",
                            "message": f"'correct_option' ({correct!r}) is not a key in 'options' "
                                       f"({sorted(options.keys())}) -- every answer will be marked wrong."})
        # Leaked-answer-marker check -- options only (never answer_html,
        # which is SUPPOSED to reveal the answer, after the student
        # responds). See _LEAKED_MARKER_RE's own comment.
        for letter, text in options.items():
            if isinstance(text, str) and _LEAKED_MARKER_RE.search(text):
                issues.append({"severity": "ERROR", "record_id": rid, "field": f"options.{letter}",
                                "message": f"Option {letter} contains a checkmark character -- "
                                           f"the correct answer may be visible to the student before they answer."})
    elif options is not None:
        issues.append({"severity": "ERROR", "record_id": rid, "field": "options",
                        "message": f"'options' must be an object (letter -> text), got {type(options).__name__}."})

    q_html = record.get("question_html")
    if isinstance(q_html, str) and _LEAKED_MARKER_RE.search(q_html):
        issues.append({"severity": "ERROR", "record_id": rid, "field": "question_html",
                        "message": "Question text contains a checkmark character -- possible leaked answer marker."})

    return issues


def validate_descriptive_record(record: dict, index: int) -> list:
    issues = []
    rid = record.get("book_id") or f"<record #{index}, no book_id>"

    for field in DESC_REQUIRED:
        if not _is_present(record, field):
            issues.append({"severity": "ERROR", "record_id": rid, "field": field,
                            "message": f"Required field '{field}' is missing or empty."})

    for field in DESC_RECOMMENDED:
        if not _is_present(record, field):
            issues.append({"severity": "WARNING", "record_id": rid, "field": field,
                            "message": f"Recommended field '{field}' is missing -- "
                                       f"the bot will fall back to a blank/generic value."})

    has_explicit = _is_present(record, "exam_type") and _is_present(record, "year")
    has_src_text = _is_present(record, "src_text")
    if not has_explicit and not has_src_text:
        issues.append({"severity": "WARNING", "record_id": rid, "field": "exam_type/year/src_text",
                        "message": "Neither explicit exam_type+year NOR src_text is present -- "
                                   "this record will always sort under exam type 'OTHER', year 'Unknown'."})

    return issues


def _check_duplicate_ids(records: list, id_field: str) -> list:
    """A duplicate id doesn't crash anything -- get_by_book_id()/get_by_id()
    just silently return the FIRST match every time, permanently shadowing
    every later record sharing that id. Exactly the kind of bug that never
    shows up until a student reports "this question's answer looks wrong.\""""
    issues = []
    seen = {}
    for i, r in enumerate(records):
        rid = r.get(id_field)
        if not rid:
            continue
        if rid in seen:
            issues.append({"severity": "ERROR", "record_id": rid, "field": id_field,
                            "message": f"Duplicate {id_field} -- also used by record #{seen[rid]}. "
                                       f"Only the first occurrence is ever reachable; the rest are silently shadowed."})
        else:
            seen[rid] = i
    return issues


def validate_file(path: Path, kind: str) -> dict:
    """kind is 'mcq' or 'descriptive'. Returns a report dict -- never raises
    on a content problem (that's what `issues` is for); only raises if the
    file itself can't be read/parsed as JSON, since that's a different,
    louder class of failure the caller should see immediately."""
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if isinstance(data, dict) and "questions" in data:
        data = data["questions"]
    if not isinstance(data, list):
        return {"path": str(path), "kind": kind, "record_count": 0,
                "issues": [{"severity": "ERROR", "record_id": "<file>", "field": None,
                            "message": "Top-level content is not a list (and not a {\"questions\": [...]} wrapper)."}]}

    validator = validate_mcq_record if kind == "mcq" else validate_descriptive_record
    id_field = "mcq_id" if kind == "mcq" else "book_id"

    issues = []
    for i, record in enumerate(data):
        if not isinstance(record, dict):
            issues.append({"severity": "ERROR", "record_id": f"<record #{i}>", "field": None,
                            "message": f"Record is not an object (got {type(record).__name__})."})
            continue
        issues.extend(validator(record, i))
    issues.extend(_check_duplicate_ids(data, id_field))

    return {"path": str(path), "kind": kind, "record_count": len(data), "issues": issues}


def discover_content_files(tenants_path: Path = TENANTS_PATH) -> list:
    """{path, kind, tenant_ids} for every mcq_json/descriptive_json referenced
    anywhere in tenants.json, deduped by resolved path (several tenants
    legitimately point at the same shared flagship file -- see tenants.json's
    own notes on capranav currently sharing 1lavya-examhub's content).

    mcq_json/descriptive_json may be a single relative path (the original
    shape) or a LIST of them (added 2026-08-11, e.g. 1lavya-examhub's
    mcq_json -- see exam_hub_bot.py's own _resolve_content_paths() for why:
    a tenant's flagship auto-generated bank plus a separately-owned subject
    batch, merged at bot load time). Every path in the list is validated as
    its own file here, same as if it were the tenant's only source."""
    data = json.loads(tenants_path.read_text(encoding="utf-8"))
    by_path = {}
    for t in data["tenants"]:
        exam_content = t.get("exam_content") or {}
        for kind, key in (("mcq", "mcq_json"), ("descriptive", "descriptive_json")):
            rel = exam_content.get(key)
            if not rel:
                continue
            rel_list = rel if isinstance(rel, list) else [rel]
            for one_rel in rel_list:
                abs_path = (REPO_ROOT / one_rel).resolve()
                entry = by_path.setdefault(str(abs_path), {"path": abs_path, "kind": kind, "tenant_ids": []})
                entry["tenant_ids"].append(t["tenant_id"])
    return sorted(by_path.values(), key=lambda e: str(e["path"]))


def validate_all(tenants_path: Path = TENANTS_PATH) -> list:
    """One report per discovered file, each with its `tenant_ids` list
    attached -- what telegram/database/analytics.py's fetch_content_health()
    and this script's own CLI both actually call."""
    reports = []
    for entry in discover_content_files(tenants_path):
        path = entry["path"]
        if not path.exists():
            reports.append({"path": str(path), "kind": entry["kind"], "tenant_ids": entry["tenant_ids"],
                             "record_count": 0,
                             "issues": [{"severity": "ERROR", "record_id": "<file>", "field": None,
                                         "message": "File does not exist on disk."}]})
            continue
        try:
            report = validate_file(path, entry["kind"])
        except json.JSONDecodeError as e:
            report = {"path": str(path), "kind": entry["kind"], "record_count": 0,
                       "issues": [{"severity": "ERROR", "record_id": "<file>", "field": None,
                                   "message": f"Not valid JSON: {e}"}]}
        report["tenant_ids"] = entry["tenant_ids"]
        reports.append(report)
    return reports


def _print_human(reports: list):
    total_errors = sum(1 for r in reports for i in r["issues"] if i["severity"] == "ERROR")
    total_warnings = sum(1 for r in reports for i in r["issues"] if i["severity"] == "WARNING")
    for r in reports:
        status = "OK" if not r["issues"] else ("ERRORS" if any(i["severity"] == "ERROR" for i in r["issues"]) else "WARNINGS")
        print(f"\n{r['path']}  [{r['kind']}, {r['record_count']} records, tenants={r.get('tenant_ids', [])}] -- {status}")
        for i in r["issues"]:
            print(f"  [{i['severity']}] {i['record_id']} :: {i['field']} -- {i['message']}")
    print(f"\n{'='*70}\n{len(reports)} file(s) checked -- {total_errors} error(s), {total_warnings} warning(s).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, help="Validate a single file instead of every discoverable one.")
    parser.add_argument("--kind", type=str, choices=["mcq", "descriptive"], help="Required with --file.")
    parser.add_argument("--json", action="store_true", help="Print the machine-readable report instead of the human one.")
    args = parser.parse_args()

    if args.file:
        if not args.kind:
            sys.exit("--kind mcq|descriptive is required with --file.")
        reports = [validate_file(Path(args.file), args.kind)]
        reports[0]["tenant_ids"] = []
    else:
        reports = validate_all()

    if args.json:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    else:
        _print_human(reports)

    has_errors = any(i["severity"] == "ERROR" for r in reports for i in r["issues"])
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
