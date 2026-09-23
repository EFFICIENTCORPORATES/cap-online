"""Build a deterministic D1 seed for The Anatomy of Advanced Accounts.

The generated SQL only replaces `aa_*` content. Existing capranav.com users,
orders, sessions, entitlements, and payment data are never touched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOPICS_FILE = ROOT / "first_run/output/sheet-ready-json/study_material_topics_flat.json"
QUESTIONS_FILE = ROOT / "first_run/output/sheet-ready-json/question_bank_descriptive_flat.json"
MATCHES_FILE = ROOT / "first_run/output/generated-from-script/pyq_study_matches.json"
PRIORITY_FILE = ROOT / "books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data/descriptive_topic_priority.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "generated/anatomy-seed.sql"

MONTHS = {"January": 1, "May": 5, "September": 9, "November": 11}


def sql(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def number(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return value
    match = re.search(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group()) if match else None


def study_item_id(match):
    identity = "|".join(
        str(match.get(key) or "")
        for key in ("study_source_file", "study_item_type", "study_item_no")
    )
    return "SMI-" + hashlib.sha1(identity.encode("utf-8")).hexdigest()[:16]


def unit_from_source(source_file):
    if not source_file:
        return None
    match = re.search(r"(M\d+_C\d+_U\d+)", source_file)
    return match.group(1).replace("_", "-") if match else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    topics = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    matches = json.loads(MATCHES_FILE.read_text(encoding="utf-8")) if MATCHES_FILE.exists() else []
    topic_catalog = {row["unique_topic_id"]: row for row in topics}

    # The priority pipeline contains reviewed current-syllabus overrides and
    # the latest September 2026 PYQ, which arrived after the flat May snapshot.
    # Merge it here so D1 remains current without making Excel authoritative.
    if PRIORITY_FILE.exists():
        priority = json.loads(PRIORITY_FILE.read_text(encoding="utf-8"))
        priority_rows = {}
        for row in priority.get("question_topic_rows", []):
            priority_rows.setdefault(row["question_id"], []).append(row)
        question_by_id = {row["question_id"]: row for row in questions}
        for qid, rows in priority_rows.items():
            tids = list(dict.fromkeys(row["topic_id"] for row in rows if row.get("topic_id") in topic_catalog))
            if qid in question_by_id:
                if tids:
                    q = question_by_id[qid]
                    q["topic_ids"] = tids
                    q["topic_names"] = [topic_catalog[tid]["topic_name"] for tid in tids]
                    q["chapter_ids"] = list(dict.fromkeys(topic_catalog[tid]["unique_unit_id"] for tid in tids))
                    q["final_chapter_id"] = q["chapter_ids"][0]
                    q["final_chapter_name"] = topic_catalog[tids[0]]["chapter_name"]
                    q["final_unit_name"] = topic_catalog[tids[0]]["unit_name"]
                continue
            first = rows[0]
            final_unit = topic_catalog[tids[0]]["unique_unit_id"] if tids else None
            q = {
                "exam_year": first["exam_year"], "paper_type": first["paper_type"],
                "attempt_month": first["attempt_month"], "set": first.get("set"),
                "paper_label": first["paper_label"], "question_no": first.get("question_no"),
                "sub_part": first.get("sub_part"), "or_alternative": first.get("or_alternative"),
                "or_group": "Q6a" if "-Q6-a-alt" in qid else None,
                "marks": first.get("question_marks"),
                "count_in_offered_total": 0 if first.get("or_alternative") == "alt2" else 1,
                "marks_issue": None, "question_type": first.get("question_type"),
                "final_chapter_id": final_unit,
                "final_chapter_name": topic_catalog[tids[0]]["chapter_name"] if tids else None,
                "final_unit_name": topic_catalog[tids[0]]["unit_name"] if tids else None,
                "topic_ids": tids,
                "topic_names": [topic_catalog[tid]["topic_name"] for tid in tids],
                "chapter_ids": list(dict.fromkeys(topic_catalog[tid]["unique_unit_id"] for tid in tids)),
                "source_file": "books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/sources/pyq-september-2026-question-paper.html",
                "question_id": qid,
                "topic_mapping_review": None,
            }
            questions.append(q)
            question_by_id[qid] = q

        existing_matches = {row["question_id"] for row in matches}
        for row in priority.get("question_classifications", []):
            if row.get("paper_type") != "PYQ" or row["question_id"] in existing_matches:
                continue
            matches.append({
                "question_id": row["question_id"],
                "match_status": f"Category {row.get('category')}: {row.get('classification_basis')}",
                "similarity_percent": row.get("similarity_percent"),
                "study_item_type": row.get("study_item_type"),
                "study_item_no": row.get("study_item_no"),
                "study_source_file": row.get("study_source_file"),
                "study_question_excerpt": row.get("study_question_excerpt"),
                "match_note": row.get("classification_basis"),
            })
    else:
        priority = {"topic_rankings": []}
    topic_priority = {row["topic_id"]: row for row in priority.get("topic_rankings", [])}
    match_by_question = {row["question_id"]: row for row in matches}

    modules = {}
    chapters = {}
    units = {}
    for row in topics:
        module_id = row["module_acronym"]
        module_no = int(re.sub(r"\D", "", module_id))
        modules[module_id] = (module_no, row["module"])
        chapter_id = f"{module_id}-C{row['chapter_no']}"
        chapters[chapter_id] = {
            "module_id": module_id,
            "chapter_no": row["chapter_no"],
            "name": row["chapter_name"],
            "short_name": row.get("chapter_name_short"),
        }
        units[row["unique_unit_id"]] = {
            "chapter_id": chapter_id,
            "unit_no": row.get("unit_no"),
            "name": row["unit_name"],
            "standard": row.get("standard"),
            "teaching_sequence": number(row.get("teaching_sequence")),
        }

    sittings = {}
    for q in questions:
        set_suffix = f"-S{q['set']}" if q.get("set") is not None else ""
        month_no = MONTHS[q["attempt_month"]]
        sitting_id = f"{q['paper_type']}-{q['exam_year']}-{month_no:02d}{set_suffix}"
        sittings[sitting_id] = {
            "paper_type": q["paper_type"],
            "month": q["attempt_month"],
            "month_no": month_no,
            "year": q["exam_year"],
            "set": q.get("set"),
            "label": q["paper_label"],
        }
        q["_sitting_id"] = sitting_id

    # Wrangler's remote D1 import rejects explicit SQL BEGIN/COMMIT. The
    # import operation itself handles rollback on failure.
    lines = ["PRAGMA foreign_keys = ON;"]
    for table in (
        "aa_pyq_study_matches", "aa_study_item_topics", "aa_study_items",
        "aa_question_topics", "aa_question_units", "aa_questions", "aa_sittings",
        "aa_topics", "aa_units", "aa_chapters", "aa_modules", "aa_subjects",
    ):
        lines.append(f"DELETE FROM {table};")

    lines.append(
        "INSERT INTO aa_subjects (subject_id,name,short_name,course_level,active_edition) VALUES "
        "('CAI-AA','CA Intermediate Advanced Accounting','Advanced Accounting','CA Intermediate','May 2027');"
    )
    for display, (module_id, (module_no, name)) in enumerate(sorted(modules.items(), key=lambda x: x[1][0]), 1):
        lines.append(
            "INSERT INTO aa_modules (module_id,subject_id,module_no,name,display_order) VALUES "
            f"({sql(module_id)},'CAI-AA',{module_no},{sql(name)},{display});"
        )
    for display, (chapter_id, row) in enumerate(sorted(chapters.items(), key=lambda x: (int(x[1]["module_id"][1:]), int(x[1]["chapter_no"]))), 1):
        lines.append(
            "INSERT INTO aa_chapters (chapter_id,module_id,chapter_no,name,short_name,display_order) VALUES "
            f"({sql(chapter_id)},{sql(row['module_id'])},{sql(row['chapter_no'])},{sql(row['name'])},{sql(row['short_name'])},{display});"
        )
    for display, (unit_id, row) in enumerate(sorted(units.items()), 1):
        lines.append(
            "INSERT INTO aa_units (unit_id,chapter_id,unit_no,name,accounting_standard,teaching_sequence,display_order) VALUES "
            f"({sql(unit_id)},{sql(row['chapter_id'])},{sql(row['unit_no'])},{sql(row['name'])},{sql(row['standard'])},{sql(row['teaching_sequence'])},{display});"
        )
    topic_ids = set()
    for display, row in enumerate(topics, 1):
        topic_ids.add(row["unique_topic_id"])
        lines.append(
            "INSERT INTO aa_topics (topic_id,unit_id,topic_no,name,short_name,page_number,display_order,overall_rank,priority_band) VALUES "
            f"({sql(row['unique_topic_id'])},{sql(row['unique_unit_id'])},{sql(row['topic_no'])},{sql(row['topic_name'])},"
            f"{sql(row.get('topic_name_short'))},{sql(row.get('page_number'))},{display},"
            f"{sql(topic_priority.get(row['unique_topic_id'], {}).get('overall_rank'))},"
            f"{sql(topic_priority.get(row['unique_topic_id'], {}).get('priority_band'))});"
        )
    for sitting_id, row in sorted(sittings.items(), key=lambda x: (x[1]["year"], x[1]["month_no"], x[1]["paper_type"], x[1]["set"] or 0)):
        # The source file contains descriptive questions only. Under the new
        # scheme (2024 onward), Part II offers 84 marks and students answer 70;
        # the separate MCQ section is intentionally outside this dataset.
        if row["paper_type"] in {"PYQ", "MTP"}:
            expected_offered = 84 if row["year"] >= 2024 else 120
            expected_required = 70 if row["year"] >= 2024 else 100
        else:
            expected_offered = None
            expected_required = None
        lines.append(
            "INSERT INTO aa_sittings (sitting_id,paper_type,attempt_month,attempt_month_no,exam_year,set_no,label,expected_required_marks,expected_offered_marks) VALUES "
            f"({sql(sitting_id)},{sql(row['paper_type'])},{sql(row['month'])},{row['month_no']},{row['year']},{sql(row['set'])},{sql(row['label'])},{sql(expected_required)},{sql(expected_offered)});"
        )

    question_ids = set()
    topic_links = 0
    for q in questions:
        qid = q["question_id"]
        question_ids.add(qid)
        final_unit = q.get("final_chapter_id") if q.get("final_chapter_id") in units else None
        lines.append(
            "INSERT INTO aa_questions (question_id,sitting_id,question_no,sub_part,alternative_code,alternative_group,marks,count_in_offered_total,marks_issue,question_type,final_unit_id,source_file,topic_mapping_review) VALUES "
            f"({sql(qid)},{sql(q['_sitting_id'])},{sql(q['question_no'])},{sql(q.get('sub_part'))},{sql(q.get('or_alternative'))},"
            f"{sql(q.get('or_group'))},{sql(number(q.get('marks')))},{int(q.get('count_in_offered_total',1))},{sql(q.get('marks_issue'))},"
            f"{sql(q.get('question_type'))},{sql(final_unit)},{sql(q['source_file'])},{sql(q.get('topic_mapping_review'))});"
        )
        linked_units = [u for u in q.get("chapter_ids", []) if u in units]
        if final_unit and final_unit not in linked_units:
            linked_units.append(final_unit)
        for unit_id in dict.fromkeys(linked_units):
            lines.append(
                "INSERT INTO aa_question_units (question_id,unit_id,is_primary) VALUES "
                f"({sql(qid)},{sql(unit_id)},{1 if unit_id == final_unit else 0});"
            )
        for pos, topic_id in enumerate(dict.fromkeys(q.get("topic_ids", []))):
            if topic_id not in topic_ids:
                continue
            topic_links += 1
            lines.append(
                "INSERT INTO aa_question_topics (question_id,topic_id,is_primary,mapping_status) VALUES "
                f"({sql(qid)},{sql(topic_id)},{1 if pos == 0 else 0},'source-mapped');"
            )

    study_items = {}
    for match in matches:
        if not match.get("study_source_file") or not match.get("study_item_type"):
            continue
        sid = study_item_id(match)
        source_unit = unit_from_source(match.get("study_source_file"))
        valid_unit = source_unit if source_unit in units else None
        study_items[sid] = {
            "type": match.get("study_item_type"),
            "no": match.get("study_item_no"),
            "source": match.get("study_source_file"),
            "excerpt": match.get("study_question_excerpt"),
            "unit": valid_unit,
            "chapter": units[valid_unit]["chapter_id"] if valid_unit else None,
        }
    for sid, item in study_items.items():
        lines.append(
            "INSERT INTO aa_study_items (study_item_id,item_type,item_no,source_file,question_excerpt,scope_level,unit_id,chapter_id) VALUES "
            f"({sql(sid)},{sql(item['type'])},{sql(item['no'])},{sql(item['source'])},{sql(item['excerpt'])},'unit',{sql(item['unit'])},{sql(item['chapter'])});"
        )
    for qid, match in match_by_question.items():
        if qid not in question_ids:
            continue
        sid = study_item_id(match) if match.get("study_source_file") and match.get("study_item_type") else None
        review_status = "verified" if match.get("similarity_percent") is not None else "pending"
        lines.append(
            "INSERT INTO aa_pyq_study_matches (question_id,study_item_id,match_status,similarity_percent,match_note,review_status) VALUES "
            f"({sql(qid)},{sql(sid)},{sql(match.get('match_status') or 'Not reviewed')},{sql(number(match.get('similarity_percent')))},{sql(match.get('match_note'))},{sql(review_status)});"
        )

    import_id = datetime.now(timezone.utc).strftime("anatomy-%Y%m%dT%H%M%SZ")
    lines.append(
        "INSERT INTO aa_import_runs (import_id,source_topics_file,source_questions_file,source_matches_file,topics_count,questions_count,topic_links_count) VALUES "
        f"({sql(import_id)},{sql(TOPICS_FILE.relative_to(ROOT).as_posix())},{sql(QUESTIONS_FILE.relative_to(ROOT).as_posix())},"
        f"{sql(MATCHES_FILE.relative_to(ROOT).as_posix())},{len(topics)},{len(questions)},{topic_links});"
    )
    lines.append("PRAGMA foreign_key_check;")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({
        "modules": len(modules), "chapters": len(chapters), "units": len(units),
        "topics": len(topics), "sittings": len(sittings), "questions": len(questions),
        "question_topic_links": topic_links, "study_items": len(study_items),
        "pyq_match_rows": sum(1 for qid in match_by_question if qid in question_ids),
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
