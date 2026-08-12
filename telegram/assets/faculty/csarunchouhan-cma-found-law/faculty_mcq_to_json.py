"""Convert CS Arun Chouhan's CMA Foundation MCQ DOCX files to bot JSON.

This script is deliberately self-contained and only reads DOCX files in this
folder. It writes the generated JSON beside the script and does not modify the
shared Exam Hub files.

Run from the repository root:

    python telegram/assets/faculty/csarunchouhan-cma-found-law/faculty_mcq_to_json.py
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
DEFAULT_OUTPUT = HERE / "cma_foundation_law_faculty_mcqs.json"
FACULTY_ID = "cs_arun_chouhan"
FACULTY_NAME = "CS Arun Chouhan"

QUESTION_RE = re.compile(r"^\s*Q\s*(\d+)\s*[.)]\s*(.*)$", re.IGNORECASE)
OPTION_RE = re.compile(r"^\s*\(?([a-dA-D])\)?\s*[.)\-:]\s*(.*)$")
ANSWER_RE = re.compile(r"Q\s*(\d+)\s*(?:→|->|:)\s*\(?([a-dA-D])\)?", re.IGNORECASE)
SUBMODULE_RE = re.compile(r"^\s*[▶>]?\s*(\d+(?:\.\d+)+)\s+(.+?)(?:\s+\[Q\d+.*)?$", re.IGNORECASE)
MODULE_RE = re.compile(r"MODULE\s+(\d+)\s*[–—-]\s*(.+)$", re.IGNORECASE)
COUNT_RE = re.compile(r"(\d+)\s+MCQs", re.IGNORECASE)

EXPECTED_COUNTS = {
    "CMA_Foundation_Module1_40_MCQs.docx": 40,
    "CMA_Foundation_Module2_150_MCQs_June2026.docx": 150,
    "CMA_Foundation_Module3_60_MCQs_June2026.docx": 60,
    "CMA_Foundation_Module4_50_MCQs_June2026.docx": 50,
    "CMA_Foundation_Module5_75_MCQs_June2026.docx": 75,
}


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def as_html(text: str) -> str:
    return f"<p>{html.escape(clean_text(text))}</p>"


def parse_metadata(path: Path, document: Document) -> dict:
    paragraphs = [clean_text(p.text) for p in document.paragraphs if clean_text(p.text)]
    module_no = None
    module_title = None
    for paragraph in paragraphs[:20]:
        match = MODULE_RE.search(paragraph)
        if match:
            module_no = int(match.group(1))
            module_title = clean_text(match.group(2))
            break

    count_match = COUNT_RE.search(" ".join(paragraphs[:20]))
    expected_count = int(count_match.group(1)) if count_match else EXPECTED_COUNTS.get(path.name)
    year_match = re.search(r"(?:June|December)\s+(20\d{2})", path.stem, re.IGNORECASE)
    exam_year = year_match.group(1) if year_match else None

    return {
        "module_no": module_no,
        "module_title": module_title,
        "expected_count": expected_count,
        "exam_year": exam_year,
        "source_file": path.name,
        "source_document_hash": sha256_file(path),
    }


def answer_key_from_tables(document: Document) -> dict[int, str]:
    answers: dict[int, str] = {}
    for table in document.tables:
        for row in table.rows:
            row_text = " | ".join(clean_text(cell.text) for cell in row.cells)
            for question_no, option in ANSWER_RE.findall(row_text):
                answers[int(question_no)] = option.upper()
    return answers


def parse_document(path: Path) -> tuple[list[dict], dict]:
    document = Document(path)
    metadata = parse_metadata(path, document)
    answers = answer_key_from_tables(document)
    skipped_questions = []
    questions = []
    current = None
    current_submodule = None

    def finish_current():
        nonlocal current
        if current is None:
            return
        if metadata["expected_count"] and current["_question_no"] > metadata["expected_count"]:
            skipped_questions.append(f"Q{current['_question_no']}")
            current = None
            return
        current["question_html"] = as_html(current.pop("_question_text"))
        current["options"] = {
            key: clean_text(value) for key, value in current.pop("_options").items()
        }
        question_no = current["_question_no"]
        answer = answers.get(question_no)
        current["correct_option"] = answer
        current["answer_html"] = (
            f"<p><strong>Answer:</strong> ({answer})</p>" if answer else None
        )
        current["qno_text"] = f"Q{question_no}"
        current["question_no"] = question_no
        current.pop("_question_no")
        questions.append(current)
        current = None

    for paragraph in document.paragraphs:
        text = clean_text(paragraph.text)
        if not text:
            continue

        submodule_match = SUBMODULE_RE.match(text)
        if submodule_match and not text.upper().startswith("Q"):
            current_submodule = {
                "code": submodule_match.group(1),
                "title": clean_text(submodule_match.group(2)),
            }
            continue

        question_match = QUESTION_RE.match(text)
        if question_match:
            finish_current()
            question_no = int(question_match.group(1))
            question_text = clean_text(question_match.group(2))
            is_miq = "★" in question_text or "MIQ" in question_text.upper()
            question_text = clean_text(question_text.replace("★", "").replace("MIQ", ""))
            current = {
                "_question_no": question_no,
                "_question_text": question_text,
                "_options": {},
                "is_miq": is_miq,
                "submodule_code": current_submodule["code"] if current_submodule else None,
                "submodule_title": current_submodule["title"] if current_submodule else None,
            }
            continue

        if current is None:
            continue

        option_match = OPTION_RE.match(text)
        if option_match:
            current["_options"][option_match.group(1).upper()] = option_match.group(2)
        else:
            # A wrapped question or option line is retained rather than lost.
            if current["_options"]:
                last_option = next(reversed(current["_options"]))
                current["_options"][last_option] += " " + text
            else:
                current["_question_text"] += " " + text

    finish_current()

    records = []
    chapter_slug = f"cma-foundation-paper-1-module-{metadata['module_no']}"
    unitcode = f"CMA-FND-P1-M{metadata['module_no']}"
    for question in questions:
        question_no = question.pop("question_no")
        question["mcq_id"] = (
            f"CMAF-P1-FACULTY-{FACULTY_ID.upper().replace('_', '-')}-"
            f"M{metadata['module_no']}-Q{question_no}"
        )
        question["course"] = "CMA"
        question["level"] = "Foundation"
        question["exam_type"] = "FACULTY_PRACTICE"
        question["year"] = metadata["exam_year"]
        question["set"] = None
        question["marks"] = 1
        question["difficulty"] = None
        question["qtype"] = "normal"
        question["case_ref"] = None
        question["case_facts_html"] = None
        question["chapter_slug"] = chapter_slug
        question["chapter_label"] = metadata["module_title"] or f"Module {metadata['module_no']}"
        question["unitcode"] = unitcode
        question["topic_text"] = (
            f"{question['submodule_code']}: {question['submodule_title']}"
            if question["submodule_code"] else None
        )
        question["source_kind"] = "faculty_created"
        question["faculty_id"] = FACULTY_ID
        question["faculty_name"] = FACULTY_NAME
        question["source_file"] = metadata["source_file"]
        question["source_document_hash"] = metadata["source_document_hash"]
        question["publication_status"] = "draft"
        question["validation_status"] = "answer_key_matched" if question["correct_option"] else "missing_answer_key"
        records.append(question)

    metadata["actual_count"] = len(records)
    metadata["answer_count"] = sum(1 for record in records if record["correct_option"])
    metadata["validation_issues"] = []
    metadata["skipped_questions"] = skipped_questions
    if skipped_questions:
        metadata["validation_issues"].append(
            "Questions beyond the declared count were excluded: " + ", ".join(skipped_questions)
        )
    if metadata["expected_count"] != metadata["actual_count"]:
        metadata["validation_issues"].append(
            f"Expected {metadata['expected_count']} questions but extracted {metadata['actual_count']}"
        )
    missing_answers = [record["qno_text"] for record in records if not record["correct_option"]]
    if missing_answers:
        metadata["validation_issues"].append(
            "Missing answer keys: " + ", ".join(missing_answers)
        )
    invalid_options = [
        record["qno_text"] for record in records
        if len(record["options"]) != 4
        or set(record["options"]) != {"A", "B", "C", "D"}
        or record["correct_option"] not in record["options"]
    ]
    if invalid_options:
        metadata["validation_issues"].append(
            "Invalid option structure: " + ", ".join(invalid_options)
        )
    return records, metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    all_records = []
    reports = []
    source_dir = HERE / "exam-mcq"
    for path in sorted(source_dir.glob("*.docx")):
        records, report = parse_document(path)
        all_records.extend(records)
        reports.append(report)

    duplicate_ids = sorted(
        record["mcq_id"] for record in all_records
        if sum(other["mcq_id"] == record["mcq_id"] for other in all_records) > 1
    )
    if duplicate_ids:
        raise SystemExit("Duplicate MCQ IDs: " + ", ".join(sorted(set(duplicate_ids))))

    args.output.write_text(
        json.dumps(all_records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(all_records)} MCQs to {args.output}")
    for report in reports:
        status = "OK" if not report["validation_issues"] else "REVIEW"
        print(
            f"{status}: {report['source_file']} | "
            f"expected={report['expected_count']} extracted={report['actual_count']} "
            f"answers={report['answer_count']}"
        )
        for issue in report["validation_issues"]:
            print(f"  - {issue}")
    print(f"Generated at {datetime.now(timezone.utc).isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
