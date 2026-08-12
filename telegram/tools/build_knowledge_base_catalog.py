"""Build the unified document manifest for the CA/CS/CMA knowledge base.

The Excel catalogs remain human-readable source artifacts. This script turns
them into one deterministic JSON manifest for downstream parsing, while
preserving each publisher's native metadata under ``native_metadata``.

Run from the repository root with:

    python telegram/tools/build_knowledge_base_catalog.py

The output is generated and should not be hand-edited.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
from pypdf import PdfReader


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DOCS = REPO_ROOT / "telegram" / "source-docs"
PDF_ROOT = REPO_ROOT / "telegram" / "assets" / "study_bot"
OUTPUT_PATH = SOURCE_DOCS / "knowledge_base_documents.json"

CA_CATALOG = SOURCE_DOCS / "1Lavya_Study_Hub_File_Mapping.xlsx"
CS_CMA_CATALOG = SOURCE_DOCS / "CS_CMA_Chapter_Catalog.xlsx"
MASTER_CATALOG = SOURCE_DOCS / "StudyHub_Master_Catalog.xlsx"


def normalize(value):
    if value is None:
        return None
    return re.sub(r"\s+", " ", str(value)).strip()


def read_sheet(path: Path, sheet_name: str):
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook[sheet_name]
    rows = list(sheet.iter_rows(values_only=True))
    headers = [normalize(value) for value in rows[0]]
    return [
        {header: value for header, value in zip(headers, row) if header}
        for row in rows[1:]
    ]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pdf_page_count(path: Path):
    try:
        return len(PdfReader(str(path), strict=False).pages)
    except Exception:
        return None


def slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", (value or "").upper()).strip("-")


def document_id(row: dict) -> str:
    parts = [row.get("course"), row.get("level"), row.get("subject")]
    native_code = row.get("native_code")
    if native_code:
        parts.append(native_code)
    parts.append(Path(row["file_name"]).stem)
    return "-".join(slug(part) for part in parts if part)


def build_ca_rows():
    rows = read_sheet(CA_CATALOG, "File Mapping")
    documents = []
    for row in rows:
        module = normalize(row.get("ModuleOrGroup"))
        chapter = normalize(row.get("ChapterNo"))
        filename_match = re.search(r"_(M\d+-C\d+-U\d+)_", row.get("FileName", ""))
        native_code = filename_match.group(1) if filename_match else None
        documents.append({
            "course": normalize(row.get("Course")),
            "institute": "ICAI",
            "level": normalize(row.get("Level")),
            "subject": normalize(row.get("Subject")),
            "document_type": "Study Material",
            "native_structure": "CA_MODULE_CHAPTER_UNIT",
            "native_code": native_code,
            "native_title": normalize(row.get("ChapterName")),
            "file_name": normalize(row.get("FileName")),
            "native_metadata": {
                "module_or_group": module,
                "chapter_no": row.get("ChapterNo"),
                "keywords": normalize(row.get("Keywords")),
                "catalog_source": CA_CATALOG.name,
            },
        })
    return documents


def build_cs_cma_rows():
    rows = read_sheet(CS_CMA_CATALOG, "Chapter Catalog")
    documents = []
    for row in rows:
        if not row.get("FinalPDFFileName") or row.get("PDFPageStart_1indexed") is None:
            continue
        publisher = "ICSI" if normalize(row.get("Course")) == "CS" else "ICMAI"
        native_structure = "CS_LESSON" if publisher == "ICSI" else "CMA_MODULE"
        code = normalize(row.get("ChapterCode"))
        documents.append({
            "course": normalize(row.get("Course")),
            "institute": publisher,
            "level": normalize(row.get("Level")),
            "subject": normalize(row.get("Subject")),
            "document_type": "Study Material",
            "native_structure": native_structure,
            "native_code": code,
            "native_title": normalize(row.get("ChapterName")),
            "file_name": normalize(row.get("FinalPDFFileName")),
            "native_metadata": {
                "group": normalize(row.get("Group")),
                "paper_no": normalize(row.get("PaperNo")),
                "chapter_no": row.get("ChapterNo"),
                "short_chapter_name": normalize(row.get("ShortChapterName")),
                "printed_page_start": row.get("PrintedPageStart"),
                "printed_page_end": row.get("PrintedPageEnd"),
                "pdf_page_start_1indexed": row.get("PDFPageStart_1indexed"),
                "pdf_page_end_1indexed": row.get("PDFPageEnd_1indexed"),
                "verify_score": row.get("VerifyScore"),
                "source_folder": normalize(row.get("SourceFolder")),
                "source_file": normalize(row.get("SourceFile")),
                "notes": normalize(row.get("Notes")),
                "catalog_source": CS_CMA_CATALOG.name,
            },
        })
    return documents


def build_exam_rows():
    """Register existing exam PDFs without pretending they have study hierarchy."""
    rows = read_sheet(MASTER_CATALOG, "Catalog")
    documents = []
    for row in rows:
        if normalize(row.get("Category")) != "Exam Materials":
            continue
        documents.append({
            "course": normalize(row.get("Course")),
            "institute": None,
            "level": normalize(row.get("Level")),
            "subject": normalize(row.get("Subject")),
            "document_type": "Exam Material",
            "native_structure": "EXAM_DOCUMENT",
            "native_code": None,
            "native_title": normalize(row.get("Label")),
            "file_name": normalize(row.get("FileName")),
            "native_metadata": {
                "category": normalize(row.get("Category")),
                "paper_type": normalize(row.get("PaperType")),
                "session": normalize(row.get("Session")),
                "set_label": normalize(row.get("SetLabel")),
                "doc_type": normalize(row.get("DocType")),
                "keywords": normalize(row.get("Keywords")),
                "catalog_source": MASTER_CATALOG.name,
            },
        })
    return documents


def enrich_and_validate(rows):
    seen_ids = set()
    seen_files = set()
    missing = []
    documents = []
    for row in rows:
        filename = row["file_name"]
        path = PDF_ROOT / ("Study Materials" if row["document_type"] == "Study Material" else "Exam Materials") / filename
        doc_id = document_id(row)
        if doc_id in seen_ids:
            raise ValueError(f"Duplicate document_id: {doc_id}")
        if filename in seen_files:
            raise ValueError(f"Duplicate catalog filename: {filename}")
        seen_ids.add(doc_id)
        seen_files.add(filename)
        if not path.exists():
            missing.append(str(path))
            continue
        documents.append({
            "document_id": doc_id,
            **row,
            "source_path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "file_hash": file_hash(path),
            "page_count": pdf_page_count(path),
            "processing_status": "registered",
            "parser_version": None,
            "review_required": bool(row["native_metadata"].get("notes")),
        })

    if missing:
        raise SystemExit("Catalog references missing PDF files:\n" + "\n".join(missing))

    disk_files = {
        path.name
        for category in ("Study Materials", "Exam Materials")
        for path in (PDF_ROOT / category).glob("*.pdf")
    }
    uncatalogued = sorted(disk_files - seen_files)
    if uncatalogued:
        raise SystemExit("PDF files missing from catalogs:\n" + "\n".join(uncatalogued))
    return sorted(documents, key=lambda item: item["document_id"])


def main():
    rows = build_ca_rows() + build_cs_cma_rows() + build_exam_rows()
    documents = enrich_and_validate(rows)
    output = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_catalogs": [CA_CATALOG.name, CS_CMA_CATALOG.name, MASTER_CATALOG.name],
        "document_count": len(documents),
        "documents": documents,
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(documents)} documents to {OUTPUT_PATH}")
    for document_type in ("Study Material", "Exam Material"):
        count = sum(d["document_type"] == document_type for d in documents)
        print(f"  {document_type}: {count}")


if __name__ == "__main__":
    main()