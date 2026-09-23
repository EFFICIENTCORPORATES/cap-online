"""Build Anatomy PDF metadata and optionally upload the source PDFs to R2."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STUDY_DIR = ROOT / "books/ca-inter/smat-may-27-edition/all-modules"
EXAM_DIR = ROOT / "first_run/source"
PYQ_Q_DIR = ROOT / "books/ca-inter/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/deprecated-pyq-question-files"
TOPICS_FILE = ROOT / "first_run/output/sheet-ready-json/study_material_topics_flat.json"
PRIORITY_FILE = ROOT / "books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data/descriptive_topic_priority.json"
GENERATED = Path(__file__).resolve().parent / "generated"
SQL_OUTPUT = GENERATED / "anatomy-documents.sql"
MANIFEST_OUTPUT = GENERATED / "anatomy-documents.json"
BUCKET = "capranav-vault"
MONTH = {"Jan": 1, "May": 5, "Sep": 9, "Nov": 11}


def sql(value):
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def doc_id(key):
    return "DOC-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def sitting_id(paper_type, year, month, set_no=None):
    suffix = f"-S{set_no}" if set_no else ""
    return f"{paper_type}-{year}-{MONTH[month]:02d}{suffix}"


def valid_sittings():
    data = json.loads(PRIORITY_FILE.read_text(encoding="utf-8"))
    found = set()
    for row in data["question_topic_rows"]:
        set_no = row.get("set")
        month = {"January": 1, "May": 5, "September": 9, "November": 11}[row["attempt_month"]]
        suffix = f"-S{set_no}" if set_no else ""
        found.add(f"{row['paper_type']}-{row['exam_year']}-{month:02d}{suffix}")
    return found


def build_manifest():
    valid_units = {row["unique_unit_id"] for row in json.loads(TOPICS_FILE.read_text(encoding="utf-8"))}
    valid_papers = valid_sittings()
    documents = []

    for path in sorted(STUDY_DIR.glob("*.pdf")):
        match = re.match(r"(M\d+)_C(\d+)_U(\d+)[ _]", path.name)
        if not match:
            continue
        unit_id = f"{match.group(1)}-C{match.group(2)}-U{match.group(3)}"
        if unit_id not in valid_units:
            continue
        title = re.sub(r"^M\d+_C\d+_U\d+_\s*", "", path.stem)
        key = f"anatomy/study-material/{unit_id}.pdf"
        documents.append({"document_id": doc_id(key), "title": title, "document_type": "study_material", "r2_key": key, "filename": path.name, "byte_size": path.stat().st_size, "source": str(path), "unit_id": unit_id})

    exam_files = {path.name: path for path in EXAM_DIR.glob("*.pdf")}
    for path in PYQ_Q_DIR.glob("*.pdf"):
        exam_files.setdefault(path.name, path)
    patterns = [
        (re.compile(r"CAInter-AdvAcc-MTP-(Jan|May|Sep|Nov)(\d{4})-Set(\d+)-(Q|Ans)\.pdf$"), "MTP"),
        (re.compile(r"CAInter-AdvAcc-(PYQ|RTP)-(Jan|May|Sep|Nov)(\d{4})-(Q|Ans)\.pdf$"), None),
        (re.compile(r"CAInter-AdvAcc-PYQ_Examiner_Comments-(Jan|May|Sep|Nov)(\d{4})\.pdf$"), "COMMENTS"),
    ]
    for name, path in sorted(exam_files.items()):
        parsed = None
        for pattern, fixed_type in patterns:
            match = pattern.match(name)
            if not match:
                continue
            if fixed_type == "MTP":
                month, year, set_no, kind = match.groups()
                paper = sitting_id("MTP", year, month, set_no)
                doc_type = "question_paper" if kind == "Q" else "answer"
            elif fixed_type == "COMMENTS":
                month, year = match.groups()
                paper = sitting_id("PYQ", year, month)
                doc_type = "examiner_comments"
            else:
                paper_type, month, year, kind = match.groups()
                paper = sitting_id(paper_type, year, month)
                doc_type = "question_paper" if kind == "Q" else "answer"
            parsed = (paper, doc_type)
            break
        if not parsed or parsed[0] not in valid_papers:
            continue
        paper, doc_type = parsed
        key = f"anatomy/exams/{paper}/{doc_type}.pdf"
        title_type = {"question_paper": "Question Paper", "answer": "Suggested Answer", "examiner_comments": "Examiner Comments"}[doc_type]
        documents.append({"document_id": doc_id(key), "title": f"{paper} - {title_type}", "document_type": doc_type, "r2_key": key, "filename": name, "byte_size": path.stat().st_size, "source": str(path), "sitting_id": paper})
    return documents


def write_outputs(documents):
    GENERATED.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUTPUT.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["PRAGMA foreign_keys = ON;", "DELETE FROM aa_unit_documents;", "DELETE FROM aa_sitting_documents;", "DELETE FROM aa_documents;"]
    for doc in documents:
        lines.append(
            "INSERT INTO aa_documents (document_id,title,document_type,r2_key,filename,byte_size) VALUES "
            f"({sql(doc['document_id'])},{sql(doc['title'])},{sql(doc['document_type'])},{sql(doc['r2_key'])},{sql(doc['filename'])},{doc['byte_size']});"
        )
        if doc.get("unit_id"):
            lines.append(f"INSERT INTO aa_unit_documents (unit_id,document_id) VALUES ({sql(doc['unit_id'])},{sql(doc['document_id'])});")
        if doc.get("sitting_id"):
            lines.append(f"INSERT INTO aa_sitting_documents (sitting_id,document_id) VALUES ({sql(doc['sitting_id'])},{sql(doc['document_id'])});")
    lines.append("PRAGMA foreign_key_check;")
    SQL_OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def upload_one(doc):
    npx = shutil.which("npx.cmd") or shutil.which("npx") or "npx"
    command = [npx, "wrangler", "r2", "object", "put", f"{BUCKET}/{doc['r2_key']}", "--remote", "--file", doc["source"], "--content-type", "application/pdf", "--cache-control", "public, max-age=86400"]
    result = subprocess.run(command, cwd=Path(__file__).resolve().parent.parent, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"{doc['filename']}: {(result.stderr or result.stdout)[-600:]}")
    return doc["filename"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", action="store_true", help="Upload every manifest PDF to the existing R2 bucket")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    documents = build_manifest()
    write_outputs(documents)
    print(json.dumps({"study_material": sum(d["document_type"] == "study_material" for d in documents), "exam_documents": sum(d["document_type"] != "study_material" for d in documents), "total": len(documents), "bytes": sum(d["byte_size"] for d in documents)}, indent=2))
    if args.upload:
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 6))) as pool:
            futures = {pool.submit(upload_one, doc): doc for doc in documents}
            complete = 0
            for future in as_completed(futures):
                future.result()
                complete += 1
                print(f"Uploaded {complete}/{len(documents)}")


if __name__ == "__main__":
    main()
