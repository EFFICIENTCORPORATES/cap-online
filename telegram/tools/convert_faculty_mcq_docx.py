#!/usr/bin/env python3
"""
telegram/tools/convert_faculty_mcq_docx.py -- deterministic MCQ converter
(added 2026-08-10, per Pranav's instruction: "deterministic, less AI-driven")
-----------------------------------------------------------------------------
Converts a faculty's .docx (filled in per telegram/config/FACULTY-MCQ-
TEMPLATE.md) into a draft JSON file matching the schema
telegram/assets/exam_bot/faculty/{tenant}/mcq_questions_extracted.json
already uses -- pure regex + python-docx table parsing, ZERO calls to any
AI model. Nothing here writes an explanation that wasn't already in the
source document (rule 5 of the template) -- a question with no
"Explanation:" paragraph comes out with answer_html: null and a
"needs_explanation" flag in the report; someone (a human, or a separate,
explicit AI-assisted pass reviewed like every other faculty content batch
in this repo) has to fill that in deliberately before the question is
usable, never automatically.

Never silently guesses or drops a question -- every anomaly (missing
answer-key entry, mismatched option count, a numeric figure worth
double-checking) is listed in the _conversion_report block of the output,
not resolved on the script's own judgment. Draft output always needs a
human pass before its own_content.status can move past "not_ingested" --
see tenants.json's own status field discipline.

USAGE:
    python convert_faculty_mcq_docx.py <input.docx> \\
        --course CMA --level Intermediate \\
        --chapter-slug cma-inter-p5-m12-companies-act \\
        --chapter-label "Module 12: Companies Act, 2013" \\
        --unitcode CMA-INTER-P5-M12 \\
        --exam-type PRACTICE --year 2026 \\
        --mcq-id-prefix CMAI-P5-M12-PRACTICE-2026 \\
        --out draft_mcqs.json

Then hand-review draft_mcqs.json (especially anything the report flags)
before merging it into the tenant's real mcq_questions_extracted.json.
"""

import re
import json
import argparse
from pathlib import Path

from docx import Document

QUESTION_RE = re.compile(r"^Q(\d+)\.\s*(?:\[(.*?)\]\s*)?(.*)$")
OPTION_RE = re.compile(r"^\(([a-dA-D])\)\s*(.*)$")
EXPLANATION_RE = re.compile(r"^Explanation:\s*(.*)$", re.IGNORECASE)

# Flags a question worth a "is this figure still current" human check --
# exactly the class of fact that produced 2 of the 5 real defects found in
# CS Arun Chouhan's own less-structured docx (see
# _claude memory 1lavya-csarunchouhan-demo-content for the concrete case).
NUMERIC_FLAG_RE = re.compile(r"\d+\s*(day|days|%|percent|crore|lakh)|₹|Rs\.", re.IGNORECASE)

VALID_LETTERS = ("A", "B", "C", "D")


def parse_questions(doc: Document) -> dict:
    """Paragraphs only -- the Answer Key table is handled separately by
    parse_answer_key(). Returns {qno: {question_text, topic, options, explanation}}."""
    questions = {}
    current = None
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        qm = QUESTION_RE.match(text)
        if qm:
            qno = int(qm.group(1))
            current = qno
            questions[qno] = {
                "question_text": qm.group(3).strip(),
                "topic": (qm.group(2) or "").strip() or None,
                "options": {},
                "explanation": None,
            }
            continue

        om = OPTION_RE.match(text)
        if om and current is not None:
            letter = om.group(1).upper()
            questions[current]["options"][letter] = om.group(2).strip()
            continue

        em = EXPLANATION_RE.match(text)
        if em and current is not None:
            questions[current]["explanation"] = em.group(1).strip()
            continue

        # Anything else (section headers, instructions, priority-star notes)
        # is deliberately ignored -- not part of the schema, never guessed at.

    return questions


def parse_answer_key(doc: Document) -> dict:
    """Reads every table in the document, tolerating both real shapes seen
    in practice: a single cell self-describing "Q1 -> (b)" (Arun's
    original Foundation file's style), or a two-column "Q1" | "b" layout
    (this template's own recommended style, rule 4). Returns {qno: letter}."""
    answer_key = {}
    single_cell_re = re.compile(r"Q\.?\s*(\d+)\D+\(?([a-dA-D])\)?")
    qno_only_re = re.compile(r"^Q\.?\s*(\d+)$", re.IGNORECASE)
    letter_only_re = re.compile(r"^\(?([a-dA-D])\)?$")

    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            i = 0
            while i < len(cells):
                cell = cells[i]
                m = single_cell_re.search(cell)
                if m:
                    answer_key[int(m.group(1))] = m.group(2).upper()
                    i += 1
                    continue
                qm = qno_only_re.match(cell)
                if qm and i + 1 < len(cells):
                    lm = letter_only_re.match(cells[i + 1])
                    if lm:
                        answer_key[int(qm.group(1))] = lm.group(1).upper()
                        i += 2
                        continue
                i += 1
    return answer_key


def build_records(questions: dict, answer_key: dict, args) -> tuple:
    """Cross-references questions against the answer key -- never trusts an
    inline marker (there isn't one in this template; see rule 3). Returns
    (records, report) -- report never gets silently swallowed by the
    caller, always written into the output JSON."""
    records = []
    report = {
        "total_questions_found": len(questions),
        "total_answer_key_entries": len(answer_key),
        "excluded_no_answer_key_entry": [],
        "excluded_bad_option_count": [],
        "answer_key_entries_with_no_question": [],
        "needs_explanation": [],
        "verify_figure_currency": [],
    }

    for qno in sorted(answer_key):
        if qno not in questions:
            report["answer_key_entries_with_no_question"].append(qno)

    for qno in sorted(questions):
        q = questions[qno]
        options = q["options"]

        if len(options) < 2 or len(options) > 4 or any(k not in VALID_LETTERS for k in options):
            report["excluded_bad_option_count"].append({"qno": qno, "option_count": len(options)})
            continue

        correct = answer_key.get(qno)
        if not correct or correct not in options:
            report["excluded_no_answer_key_entry"].append(qno)
            continue

        explanation = q["explanation"]
        if not explanation:
            report["needs_explanation"].append(qno)

        if NUMERIC_FLAG_RE.search(q["question_text"]) or any(NUMERIC_FLAG_RE.search(v) for v in options.values()):
            report["verify_figure_currency"].append(qno)

        mcq_id = f"{args.mcq_id_prefix}-Q{qno:02d}"
        record = {
            "mcq_id": mcq_id,
            "course": args.course,
            "level": args.level,
            "exam_type": args.exam_type,
            "year": args.year,
            "set": "",
            "qno_text": f"Q{qno}",
            "marks": args.marks,
            "difficulty": args.difficulty,
            "qtype": "mcq",
            "case_ref": None,
            "case_facts_html": None,
            "question_html": f"<p>{q['question_text']}</p>",
            "options": {k: v for k, v in sorted(options.items())},
            "correct_option": correct,
            "answer_html": (
                f"<p><strong>Answer: ({correct}).</strong></p><p>{explanation}</p>" if explanation else None
            ),
            "chapter_slug": args.chapter_slug,
            "chapter_label": args.chapter_label,
            "unitcode": args.unitcode,
            "topic_text": q["topic"] or args.chapter_label,
        }
        records.append(record)

    return records, report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input_docx", type=Path)
    ap.add_argument("--course", required=True)
    ap.add_argument("--level", required=True)
    ap.add_argument("--chapter-slug", required=True)
    ap.add_argument("--chapter-label", required=True)
    ap.add_argument("--unitcode", required=True)
    ap.add_argument("--exam-type", default="PRACTICE")
    ap.add_argument("--year", default="2026")
    ap.add_argument("--marks", type=int, default=1)
    ap.add_argument("--difficulty", default="Medium")
    ap.add_argument("--mcq-id-prefix", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    doc = Document(str(args.input_docx))
    questions = parse_questions(doc)
    answer_key = parse_answer_key(doc)
    records, report = build_records(questions, answer_key, args)

    output = {
        "_source_note": (
            f"Deterministic conversion, {args.input_docx.name} -> this file, via "
            f"convert_faculty_mcq_docx.py -- pure regex/table parsing, no AI involved. "
            f"See _conversion_report below for exactly what was excluded/flagged. "
            f"Every 'needs_explanation' question has answer_html: null and MUST be "
            f"filled in (from the faculty, not invented) before use."
        ),
        "_conversion_report": report,
        "questions": records,
    }
    args.out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Parsed {report['total_questions_found']} questions, {report['total_answer_key_entries']} answer key entries.")
    print(f"Wrote {len(records)} usable records to {args.out}")
    if report["excluded_no_answer_key_entry"]:
        print(f"  EXCLUDED (no answer key entry): {report['excluded_no_answer_key_entry']}")
    if report["excluded_bad_option_count"]:
        print(f"  EXCLUDED (bad option count): {report['excluded_bad_option_count']}")
    if report["answer_key_entries_with_no_question"]:
        print(f"  WARNING (answer key entry with no matching question): {report['answer_key_entries_with_no_question']}")
    if report["needs_explanation"]:
        print(f"  NEEDS EXPLANATION (answer_html is null, fill in before use): {report['needs_explanation']}")
    if report["verify_figure_currency"]:
        print(f"  VERIFY FIGURE CURRENCY (numeric limit/date/amount mentioned): {report['verify_figure_currency']}")


if __name__ == "__main__":
    main()
