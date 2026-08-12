"""Extract Arun Chouhan's CMA Intermediate Companies Act descriptive PDF.

The source is a faculty revision document where each prompt is followed by an
``Ans.`` marker. This converter preserves the existing Exam Hub descriptive
JSON keys and adds faculty/source metadata. It is intentionally review-aware:
question boundaries are inferred from the extracted PDF text and every record
keeps its source page range.

Run from the repository root:

    python telegram/assets/faculty/csarunchouhan-cma-inter-law/faculty_descriptive_pdf_to_json.py
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from pypdf import PdfReader


HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE / "descp-companies-act.pdf"
DEFAULT_OUTPUT = HERE / "cma_inter_law_companies_act_descriptive.json"
TENANT_OUTPUT = (
    HERE.parents[1]
    / "exam_bot"
    / "faculty"
    / "csarunchouhan"
    / "book_questions_extracted.json"
)

FACULTY_ID = "cs_arun_chouhan"
FACULTY_NAME = "CS Arun Chouhan"
COURSE = "CMA"
LEVEL = "Intermediate"
SUBJECT = "Business Laws and Ethics"
CHAPTER_SLUG = "companies-act-2013"
CHAPTER_LABEL = "The Companies Act, 2013"
UNITCODE = "CMA-INT-P1-COMPANIES-ACT-2013"
SRC_TEXT = "Faculty Practice — CS Arun Chouhan — CMA Intermediate Law — Companies Act, 2013"

QUESTION_HINTS = (
    "Circumstance under which corporate veil",
    "What are the legal requirement",
    "Discuses the provisions about",
    "Discuss the provision relating to conversion of a private company",
    "Describe t he procedure for conver sion of OPC",
    "What are the documents to be submitted",
    "Explain registered office under companies",
    "What is MOA and procedure",
    "What is the procedure for rectification",
    "In which manner the memorandum",
    "What are the features of Companies Registered under Sec. 8",
    "What is prospectus?",
    "Explain the provision relating to pay commission",
    "What are the conditions is issuing global",
    "What is the liability for mis-statement",
    "Write short note on red herring",
    "Write short note on shelf prospectus",
    "What are the requirements for private placements",
    "Section 42(1) – What is Private Placements",
    "Explain the provisions of Section 39",
    "What are the conditions to issue equity shares",
    "What is bonus share?",
    "Sweat equity shares are issued",
    "What are the conditions to issue preference shares",
    "What are the obligations of a company in respect of buy back",
    "What is the quortum of meeting",
    "What is the procedure for conducting a poll",
    "Discuss briefly the methods of voting",
    "In which form the report of AGM",
    "Explain Director and legal position",
    "Explain the duties of directors",
    "What is director Identification Number",
    "What are the grounds for disqualification",
    "Explain the powers of the Board of Director",
    "Explain the procedure of removal",
    "Explain the provision relating to resignation",
    "Explain the ceiling of managerial remuneration",
    "Explain the constitution, composition and function",
    "Explain the provisions relating to reporting of fraud",
    "Explain audit report and matter",
    "Explain the powers and duties of auditors",
    "Explain the rights of shareholders",
    "Explain the board’s report",
    "Explain the concept and importance of annual return",
    "What are the terms and conditions for acceptance of deposits",
    "What are the conditions for the issue of secured debentures",
    "State the provisions relating to Debenture Trustee",
)
ANS_RE = re.compile(r"^\s*Ans\.?\s*$", re.IGNORECASE)
PAGE_RE = re.compile(r"^---PAGE (\d+)---$")


def clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line or "").strip()


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_to_html(lines: list[str]) -> str:
    paragraphs = []
    current = []
    for line in lines:
        line = clean_line(line)
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return "\n".join(f"<p>{html.escape(paragraph)}</p>" for paragraph in paragraphs)


def extract_lines(source: Path) -> list[dict]:
    reader = PdfReader(str(source), strict=False)
    lines = []
    for page_no, page in enumerate(reader.pages, start=1):
        for raw in (page.extract_text() or "").splitlines():
            text = clean_line(raw)
            lines.append({"text": text, "page": page_no})
    return lines


def candidate_question(line: dict) -> bool:
    text = line["text"]
    return bool(text) and not ANS_RE.match(text) and not PAGE_RE.match(text) and any(
        text.lower().startswith(hint.lower()) for hint in QUESTION_HINTS
    )


def parse_records(lines: list[dict], source: Path) -> tuple[list[dict], list[str]]:
    candidates = [i for i, line in enumerate(lines) if candidate_question(line)]
    issues = []
    records = []
    for position, question_start in enumerate(candidates):
        next_question = candidates[position + 1] if position + 1 < len(candidates) else len(lines)
        segment = lines[question_start:next_question]
        question_end = next(
            (offset for offset, line in enumerate(segment[1:], start=1) if not line["text"]),
            1,
        )
        question_lines = [line["text"] for line in segment[:question_end]]
        answer_lines = [line["text"] for line in segment[question_end:]]
        question_lines = [x for x in question_lines if x and not PAGE_RE.match(x) and not ANS_RE.match(x)]
        answer_lines = [x for x in answer_lines if x and not PAGE_RE.match(x) and not ANS_RE.match(x)]
        if not answer_lines:
            issues.append(f"Empty answer for Q{len(records) + 1} near PDF page {lines[question_start]['page']}")
        records.append({
            "question_lines": question_lines,
            "answer_lines": answer_lines,
            "page_start": lines[question_start]["page"],
            "page_end": lines[next_question - 1]["page"] if next_question > question_start else lines[question_start]["page"],
        })
    answer_markers = sum(1 for line in lines if ANS_RE.match(line["text"]))
    if answer_markers != len(records):
        issues.append(f"Detected question headings={len(records)}; source Ans markers={answer_markers}")
    return records, issues


def build_output(source: Path) -> tuple[list[dict], list[str]]:
    records, issues = parse_records(extract_lines(source), source)
    source_hash = sha256_file(source)
    output = []
    for index, record in enumerate(records, start=1):
        question_html = text_to_html(record["question_lines"])
        answer_html = text_to_html(record["answer_lines"])
        output.append({
            "book_id": f"CMAINTLAW-COMPANIESACT-{index:03d}",
            "flagged": False,
            "src_text": SRC_TEXT,
            "qno_text": f"Q{index}",
            "marks_text": "Marks: Not stated in source",
            "approx_time_text": "Approx Time: 10–20 minutes (approx.)",
            "topic_text": None,
            "badges": [],
            "question_html": question_html,
            "answer_html": answer_html,
            "answer_letter": None,
            "mistake_type": None,
            "mistake_text": None,
            "chapter_slug": CHAPTER_SLUG,
            "unitcode": UNITCODE,
            "chapter_label": CHAPTER_LABEL,
            "section": "descriptive",
            "course": COURSE,
            "level": LEVEL,
            "subject": SUBJECT,
            "exam_type": "FACULTY_PRACTICE",
            "year": None,
            "source_kind": "faculty_created",
            "faculty_id": FACULTY_ID,
            "faculty_name": FACULTY_NAME,
            "source_file": source.name,
            "source_document_hash": source_hash,
            "source_pdf_page_start": record["page_start"],
            "source_pdf_page_end": record["page_end"],
            "publication_status": "draft",
            "validation_status": "extracted_needs_review",
        })
    return output, issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    questions, issues = build_output(args.source)
    args.output.write_text(json.dumps(questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    TENANT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    TENANT_OUTPUT.write_text(json.dumps(questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(questions)} descriptive questions to {args.output}")
    print(f"Published bot input to {TENANT_OUTPUT}")
    print(f"Source: {args.source.name} | SHA-256: {questions[0]['source_document_hash'] if questions else sha256_file(args.source)}")
    if issues:
        print("REVIEW ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Boundary extraction completed without structural issues.")
    print(f"Generated at {datetime.now(timezone.utc).isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
