"""Convert CS Arun Chouhan's CMA Intermediate Law MCQ DOCX papers.

The output is a plain list using the same bot-facing record shape as
telegram/assets/exam_bot/mcq_questions_extracted.json. This converter is
fully deterministic: it reads question/options/explanations from DOCX
paragraphs, cross-checks inline marked answers against the answer-key tables,
and writes a separate validation report. It does not call an AI model and does
not modify the shared CA question bank.

Run from the repository root:

    python telegram/assets/faculty/csarunchouhan-cma-inter-law/convert_inter_law_mcqs.py
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from docx import Document


HERE = Path(__file__).resolve().parent
SOURCE_DIR = HERE / "exam-mcq"
DEFAULT_OUTPUT = HERE / "cma_inter_law_faculty_mcqs.json"
TENANT_OUTPUT = HERE.parents[1] / "exam_bot" / "faculty" / "csarunchouhan" / "mcq_questions_extracted.json"
REPORT_OUTPUT = HERE / "cma_inter_law_faculty_mcqs.validation.json"

FACULTY_ID = "cs_arun_chouhan"
FACULTY_NAME = "CS Arun Chouhan"
COURSE = "CMA"
LEVEL = "Intermediate"
SUBJECT = "Business Laws and Ethics"
EXAM_TYPE = "FACULTY_PRACTICE"
YEAR = "2026"

QUESTION_RE = re.compile(r"^Q\s*(\d+)\.\s*(?:\[(.*?)\]\s*)?(.*)$", re.IGNORECASE)
OPTION_RE = re.compile(r"^\s*([A-Da-d])\s*[.)]\s*(.*)$")
ANSWER_KEY_RE = re.compile(r"Q\.?\s*(\d+)\D+\(?([A-Da-d])\)?", re.IGNORECASE)
MODULE_RE = re.compile(r"\bModule\s+(\d+)\b", re.IGNORECASE)
MIQ_RE = re.compile(r"★+")

# Exact native module codes/titles from knowledge_base_documents.json.
MODULES = {
    7: ("M7", "Factories Act, 1948"),
    8: ("M8", "Payment of Gratuity Act, 1972"),
    9: ("M9", "Employees Provident Fund and Miscellaneous Provisions Act, 1952"),
    10: ("M10", "Employees State Insurance Act, 1948"),
    11: ("M11", "The Code on Wages, 2019"),
    12: ("M12", "Companies Act, 2013"),
}

FILE_MODULES = {
    "AcceptanceDeposits_50MCQs_June2026.docx": 12,
    "AnnualReturn_25MCQs_June2026.docx": 12,
    "CodeOnWages2019_50MCQs_June2026.docx": 11,
    "EPF_MiscProvisionsAct_50MCQs_June2026.docx": 9,
    "ESI_Act1948_50MCQs_June2026.docx": 10,
    "Factories_Act_50_MCQs_June2026 (1).docx": 7,
    "IncorporationOfCompany_50MCQs_June2026.docx": 12,
    "MgmtAdmin_25MCQs_June2026.docx": 12,
    "NegotiableInstrumentsAct_50MCQs_June2026.docx": 12,
    "PaymentOfGratuityAct_50MCQs_June2026.docx": 8,
    "ProspectusAllotment_50MCQs_June2026.docx": 12,
    "RegCharges_50MCQs_June2026.docx": 12,
    "SaleOfGoodsAct1930_50MCQs_June2026.docx": 12,
    "ShareCapitalDebentures_50MCQs_June2026.docx": 12,
}

EXPECTED_COUNTS = {
    "AcceptanceDeposits_50MCQs_June2026.docx": 50,
    "AnnualReturn_25MCQs_June2026.docx": 25,
    "CodeOnWages2019_50MCQs_June2026.docx": 50,
    "EPF_MiscProvisionsAct_50MCQs_June2026.docx": 50,
    "ESI_Act1948_50MCQs_June2026.docx": 50,
    "Factories_Act_50_MCQs_June2026 (1).docx": 50,
    "IncorporationOfCompany_50MCQs_June2026.docx": 50,
    "MgmtAdmin_25MCQs_June2026.docx": 25,
    "NegotiableInstrumentsAct_50MCQs_June2026.docx": 50,
    "PaymentOfGratuityAct_50MCQs_June2026.docx": 50,
    "ProspectusAllotment_50MCQs_June2026.docx": 50,
    "RegCharges_50MCQs_June2026.docx": 50,
    "SaleOfGoodsAct1930_50MCQs_June2026.docx": 50,
    "ShareCapitalDebentures_50MCQs_June2026.docx": 50,
}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def as_html(value: str) -> str:
    return f"<p>{html.escape(clean(value))}</p>"


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_answer_key(document: Document) -> dict[int, str]:
    answers = {}
    qno_only_re = re.compile(r"^Q?\.?\s*(\d+)$", re.IGNORECASE)
    letter_only_re = re.compile(r"^\(?([A-Da-d])\)?$")
    for table in document.tables:
        for row in table.rows:
            cells = [clean(cell.text) for cell in row.cells]
            row_text = " | ".join(cells)
            for qno, option in ANSWER_KEY_RE.findall(row_text):
                answers[int(qno)] = option.upper()
            for index, cell in enumerate(cells[:-1]):
                qno_match = qno_only_re.match(cell)
                option_match = letter_only_re.match(cells[index + 1])
                if qno_match and option_match:
                    answers[int(qno_match.group(1))] = option_match.group(1).upper()
    return answers


def parse_document(path: Path) -> tuple[list[dict], dict]:
    document = Document(path)
    module_no = FILE_MODULES[path.name]
    module_code, module_title = MODULES[module_no]
    questions = {}
    current = None
    inline_answers = {}
    explanation_lines = {}

    for paragraph in document.paragraphs:
        text = clean(paragraph.text)
        if not text:
            continue
        question_match = QUESTION_RE.match(text)
        if question_match:
            qno = int(question_match.group(1))
            topic = clean(question_match.group(2) or "") or None
            topic = MIQ_RE.sub("", topic).strip() if topic else None
            is_miq = bool(question_match.group(2) and MIQ_RE.search(question_match.group(2)))
            current = qno
            questions[qno] = {
                "question_text": clean(question_match.group(3)),
                "topic_text": topic,
                "is_miq": is_miq,
                "options": {},
            }
            explanation_lines[qno] = []
            continue
        if current is None:
            continue

        option_match = OPTION_RE.match(text)
        if option_match:
            option = option_match.group(1).upper()
            value = clean(option_match.group(2))
            # BUG FIXED 2026-08-10: this regex required the literal word
            # "ANSWER" after "CORRECT", so it only stripped "✓ CORRECT
            # ANSWER" (13 of the 14 source files). One file
            # (Factories_Act_50_MCQs_June2026 (1).docx, 50 questions) marks
            # its correct option with the shorter "✓ CORRECT" instead --
            # every one of its 50 records leaked the checkmark AND the word
            # "CORRECT" straight into the option text shown to students
            # BEFORE they answered, defeating the whole point of an MCQ.
            # Verified by scanning every one of the 14 source docx files for
            # every distinct marker phrase actually used, not guessed --
            # exactly two exist ("✓ CORRECT ANSWER" and "✓ CORRECT"), so
            # "ANSWER" is now optional rather than adding a special case.
            marked = bool(re.search(r"✓\s*CORRECT(?:\s*ANSWER)?", value, re.IGNORECASE))
            value = clean(re.sub(r"✓\s*CORRECT(?:\s*ANSWER)?", "", value, flags=re.IGNORECASE))
            questions[current]["options"][option] = value
            if marked:
                inline_answers[current] = option
            continue

        if not questions[current]["options"]:
            # BUG FIXED 2026-08-10: these particular source docx files put
            # "Q<n>. [topic]" on its own paragraph with NO question text
            # after the bracket, and the actual question stem on the very
            # NEXT paragraph, before any options -- e.g.
            # "Q1.  [Section 2(31) -- Definition of Deposit]" then, as a
            # separate paragraph, "Under Section 2(31) of the Companies Act,
            # 2013, 'deposit' means:". The original loop had no branch for
            # "a paragraph that's not a Q-match, not an option, not an
            # Explanation, and no explanation has started yet" -- it fell
            # through silently, discarding the real question text. Found via
            # a live production bug: every one of this file's 650 MCQs
            # rendered to students with visible A/B/C/D options but a
            # completely blank question ("<p></p>"). Appending here (instead
            # of overwriting) also correctly handles a genuine multi-
            # paragraph stem, and never fires once options have started
            # (verified: the option-count check gates it off exactly then).
            existing = questions[current]["question_text"]
            questions[current]["question_text"] = clean(f"{existing} {text}".strip())
            continue

        if re.match(r"^Explanation\s*:", text, re.IGNORECASE):
            text = re.sub(r"^Explanation\s*:\s*", "", text, flags=re.IGNORECASE)
            explanation_lines[current].append(text)
        elif explanation_lines[current]:
            explanation_lines[current].append(text)

    answer_key = parse_answer_key(document)
    records = []
    report = {
        "source_file": path.name,
        "source_document_hash": sha256_file(path),
        "module_code": module_code,
        "module_title": module_title,
        "expected_count": EXPECTED_COUNTS[path.name],
        "questions_found": len(questions),
        "answer_key_entries": len(answer_key),
        "excluded_questions": [],
        "answer_mismatches": [],
        "answer_key_without_question": sorted(set(answer_key) - set(questions)),
        "missing_explanations": [],
        "invalid_option_counts": [],
        "numeric_review_questions": [],
        "issues": [],
    }

    if len(questions) != report["expected_count"]:
        report["issues"].append(
            f"Expected {report['expected_count']} questions but found {len(questions)}"
        )

    for qno in sorted(questions):
        question = questions[qno]
        options = question["options"]
        inline_answer = inline_answers.get(qno)
        table_answer = answer_key.get(qno)
        if inline_answer and table_answer and inline_answer != table_answer:
            report["answer_mismatches"].append({
                "qno": qno,
                "inline_answer": inline_answer,
                "table_answer": table_answer,
            })
        correct = table_answer or inline_answer
        if len(options) != 4 or set(options) != {"A", "B", "C", "D"}:
            report["invalid_option_counts"].append({"qno": qno, "options": sorted(options)})
        if not correct or correct not in options:
            report["excluded_questions"].append({"qno": qno, "reason": "missing_or_invalid_answer"})
            continue
        explanation = clean(" ".join(explanation_lines[qno]))
        if not explanation:
            report["missing_explanations"].append(qno)
        if re.search(r"\d+\s*(?:day|days|year|years|%|percent|crore|lakh)|₹|Rs\.?", question["question_text"], re.IGNORECASE):
            report["numeric_review_questions"].append(qno)

        chapter_slug = f"cma-intermediate-business-laws-and-ethics-{module_code.lower()}"
        records.append({
            "mcq_id": f"CMAI-P5-{module_code}-FACULTY-{YEAR}-Q{qno:02d}-{path.stem[:20].upper().replace(' ', '-')}",
            "course": COURSE,
            "level": LEVEL,
            "exam_type": EXAM_TYPE,
            "year": YEAR,
            "set": "",
            "qno_text": f"Q{qno}",
            "marks": 1,
            "difficulty": None,
            "qtype": "mcq",
            "case_ref": None,
            "case_facts_html": None,
            "question_html": as_html(question["question_text"]),
            "options": {key: options[key] for key in ("A", "B", "C", "D")},
            "correct_option": correct,
            "answer_html": (
                f"<p><strong>Answer:</strong> ({correct}) {html.escape(options[correct])}</p>"
                + (f"<p>{html.escape(explanation)}</p>" if explanation else "")
            ),
            "chapter_slug": chapter_slug,
            "chapter_label": module_title,
            "unitcode": module_code,
            "topic_text": question["topic_text"],
            "source_kind": "faculty_created",
            "faculty_id": FACULTY_ID,
            "faculty_name": FACULTY_NAME,
            "source_file": path.name,
            "source_document_hash": report["source_document_hash"],
            "module_code": module_code,
            "module_title": module_title,
            "is_miq": question["is_miq"],
            "publication_status": "draft",
            "validation_status": "answer_key_cross_checked",
        })

    if report["answer_mismatches"]:
        report["issues"].append("Inline answer and answer-key table disagree")
    if report["excluded_questions"]:
        report["issues"].append("Questions excluded because the answer key or options were unusable")
    if report["missing_explanations"]:
        report["issues"].append("Some records have no faculty explanation")
    return records, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tenant-output", type=Path, default=TENANT_OUTPUT)
    parser.add_argument("--report", type=Path, default=REPORT_OUTPUT)
    args = parser.parse_args()

    all_records = []
    reports = []
    for path in sorted(SOURCE_DIR.glob("*.docx")):
        if path.name not in FILE_MODULES:
            continue
        records, report = parse_document(path)
        all_records.extend(records)
        reports.append(report)

    ids = [record["mcq_id"] for record in all_records]
    duplicate_ids = sorted({value for value in ids if ids.count(value) > 1})
    if duplicate_ids:
        raise SystemExit("Duplicate MCQ IDs: " + ", ".join(duplicate_ids))

    args.output.write_text(json.dumps(all_records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.tenant_output.parent.mkdir(parents=True, exist_ok=True)
    args.tenant_output.write_text(json.dumps(all_records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_directory": str(SOURCE_DIR),
        "record_count": len(all_records),
        "expected_record_count": sum(EXPECTED_COUNTS.values()),
        "files": reports,
    }
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(all_records)} MCQs to {args.output}")
    print(f"Published bot input to {args.tenant_output}")
    print(f"Wrote validation report to {args.report}")
    for item in reports:
        status = "OK" if not item["issues"] else "REVIEW"
        print(f"{status}: {item['source_file']} | found={item['questions_found']} usable={item['questions_found'] - len(item['excluded_questions'])} issues={len(item['issues'])}")
        for issue in item["issues"]:
            print(f"  - {issue}")


if __name__ == "__main__":
    main()
