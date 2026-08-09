"""
Stage 1 of the Study Bot catalog pipeline: SCAN + VERIFY the nested ICAI
source tree (telegram/assets/study_bot/<course-slug>/Module N/*.pdf).

What it does:
  1. Walks every course-slug folder, parses each PDF's ICAI-standard
     filename (M{module}_C{chapter}_U{unit}_ <Title>.pdf) into structured
     fields.
  2. Extracts real text from the PDF itself (first page, falling back to
     page 2/3 if page 1 is a blank cover) using pypdf.
  3. Fuzzy-scores the filename-stated title against the extracted text
     (rapidfuzz partial_ratio) so a human/AI reviewer can tell, per file,
     whether the filename can be trusted or needs a manual look.
  4. Writes a full report (CSV + JSON) to telegram/tools/_reports/ for
     review. This script NEVER writes into assets/study_bot or deletes
     anything -- it is read-only against the source tree.

Run: python telegram/tools/scan_study_bot_source.py
See _claude/skills/SKILL-study-bot-catalog-pipeline.md for the full
pipeline this is step 1 of.
"""

import csv
import json
import re
from pathlib import Path

from pypdf import PdfReader
from rapidfuzz import fuzz

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "telegram" / "assets" / "study_bot"
REPORT_DIR = Path(__file__).resolve().parent / "_reports"
REPORT_DIR.mkdir(exist_ok=True)

# M{module}_C{chapter}_U{unit}_ <title>.pdf  (ICAI's own convention)
FNAME_RE = re.compile(r"^M(?P<module>\d+)_C(?P<chapter>\d+)_U(?P<unit>\d+)_\s*(?P<title>.+)$")
# Fallback: title itself states "Chapter N ..." (seen in ca-found-quants,
# where module/chapter/unit are all 0 and not informative)
CHAPTER_IN_TITLE_RE = re.compile(r"^Chapter\s+(\d+)\b", re.IGNORECASE)
UNIT_IN_TITLE_RE = re.compile(r"^Unit\s+([IVXLCM]+)\b", re.IGNORECASE)


def extract_text(pdf_path: Path, max_pages: int = 3, min_chars: int = 40) -> str:
    """Return text from the first page that actually has content."""
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        return f"__READ_ERROR__: {e}"

    collected = []
    for i, page in enumerate(reader.pages[:max_pages]):
        try:
            text = page.extract_text() or ""
        except Exception as e:
            text = f"__PAGE_ERROR__: {e}"
        collected.append(text)
        if len(text.strip()) >= min_chars:
            break
    return "\n".join(collected)[:4000]


def parse_filename(stem: str):
    m = FNAME_RE.match(stem)
    if m:
        return {
            "module": int(m.group("module")),
            "chapter": int(m.group("chapter")),
            "unit": int(m.group("unit")),
            "title": m.group("title").strip(),
            "parsed_ok": True,
        }
    return {"module": None, "chapter": None, "unit": None, "title": stem, "parsed_ok": False}


def main():
    rows = []
    course_dirs = sorted(p for p in SOURCE_ROOT.iterdir() if p.is_dir())
    print(f"Found {len(course_dirs)} course folders under {SOURCE_ROOT}")

    for course_dir in course_dirs:
        course_slug = course_dir.name
        pdfs = sorted(course_dir.rglob("*.pdf"))
        print(f"  {course_slug}: {len(pdfs)} PDFs")
        for pdf_path in pdfs:
            module_dir = pdf_path.parent.name  # e.g. "Module 1"
            stem = pdf_path.stem
            parsed = parse_filename(stem)

            text = extract_text(pdf_path)
            text_lower = text.lower()

            if parsed["parsed_ok"]:
                score = fuzz.partial_ratio(parsed["title"].lower(), text_lower)
            else:
                score = None

            # secondary hint: does title look like "Chapter N ..." /
            # "Unit <roman> ..." embedded text (ca-found-quants style)?
            title_chapter_hint = None
            title_unit_hint = None
            cm = CHAPTER_IN_TITLE_RE.match(parsed["title"])
            if cm:
                title_chapter_hint = int(cm.group(1))
            um = UNIT_IN_TITLE_RE.match(parsed["title"])
            if um:
                title_unit_hint = um.group(1)

            rows.append({
                "course_slug": course_slug,
                "module_dir": module_dir,
                "relpath": str(pdf_path.relative_to(SOURCE_ROOT)),
                "filename": pdf_path.name,
                "module_no": parsed["module"],
                "chapter_no": parsed["chapter"],
                "unit_no": parsed["unit"],
                "title_from_filename": parsed["title"],
                "parsed_ok": parsed["parsed_ok"],
                "title_chapter_hint": title_chapter_hint,
                "title_unit_hint": title_unit_hint,
                "fuzzy_score": score,
                "text_snippet": text[:300].replace("\n", " | "),
                "text_len": len(text.strip()),
            })

    rows.sort(key=lambda r: (r["fuzzy_score"] if r["fuzzy_score"] is not None else -1))

    json_path = REPORT_DIR / "source_scan.json"
    csv_path = REPORT_DIR / "source_scan.csv"
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nTotal PDFs scanned: {len(rows)}")
    unparsed = [r for r in rows if not r["parsed_ok"]]
    print(f"Filename-unparseable (no M_C_U_ prefix): {len(unparsed)}")
    for r in unparsed:
        print(f"    {r['relpath']}")
    no_text = [r for r in rows if r["text_len"] < 40]
    print(f"Near-empty text extraction (<40 chars, likely scanned/blank): {len(no_text)}")
    for r in no_text:
        print(f"    {r['relpath']}")
    low_score = [r for r in rows if r["fuzzy_score"] is not None and r["fuzzy_score"] < 55]
    print(f"Low fuzzy-match score (<55, filename vs page text): {len(low_score)}")
    for r in low_score:
        print(f"    [{r['fuzzy_score']}] {r['relpath']}  ->  {r['title_from_filename']!r}")

    print(f"\nFull report written to:\n  {csv_path}\n  {json_path}")


if __name__ == "__main__":
    main()
