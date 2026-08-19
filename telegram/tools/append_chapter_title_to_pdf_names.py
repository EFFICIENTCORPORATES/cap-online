"""
One-shot follow-up to rename_source_pdfs_canonical.py: appends the human-
readable chapter title back onto each canonical stem, so a filename is
identifiable by eye again while staying machine-parseable.

  CA_L3_P03_C1_U0.pdf  ->  CA_L3_P03_C1_U0_QualityControl.pdf

Title comes straight from knowledge_base_documents.json's native_title
(already computed, no re-derivation) -- slugified (alnum only, no spaces,
capped length). Same safe sequence as the canonical rename: dry-run by
default, --execute to actually rename, then patch the two source Excels
and rebuild the two downstream catalogs.

Usage: python telegram/tools/append_chapter_title_to_pdf_names.py [--execute]
"""
import json
import re
import sys
from pathlib import Path

import openpyxl

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_JSON = REPO_ROOT / "telegram" / "source-docs" / "knowledge_base_documents.json"
CA_CATALOG = REPO_ROOT / "telegram" / "source-docs" / "1Lavya_Study_Hub_File_Mapping.xlsx"
CS_CMA_CATALOG = REPO_ROOT / "telegram" / "source-docs" / "CS_CMA_Chapter_Catalog.xlsx"

MAX_TITLE_LEN = 40


def slugify_title(title: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", title or "")
    out = ""
    for w in words:
        piece = w[0].upper() + w[1:]
        if len(out) + len(piece) > MAX_TITLE_LEN:
            break
        out += piece
    return out or "Untitled"


def build_plan():
    docs = json.loads(KB_JSON.read_text(encoding="utf-8"))["documents"]
    plan = []
    for d in docs:
        if d["document_type"] != "Study Material":
            continue
        old_path = REPO_ROOT / d["source_path"]
        stem = old_path.stem
        slug = slugify_title(d.get("native_title") or "")
        new_name = f"{stem}_{slug}{old_path.suffix}"
        plan.append((d["file_name"], new_name, old_path))
    return plan


def main():
    execute = "--execute" in sys.argv
    plan = build_plan()

    missing = [p for _, _, p in plan if not p.exists()]
    if missing:
        print(f"ABORT: {len(missing)} files missing on disk, e.g. {missing[0]}")
        sys.exit(1)

    news = [n for _, n, _ in plan]
    if len(news) != len(set(news)):
        print("ABORT: collision in planned new names.")
        sys.exit(1)

    if not execute:
        print(f"DRY RUN -- {len(plan)} files. Sample:")
        for old, new, _ in plan[:8]:
            print(f"  {old}  ->  {new}")
        print("\nRe-run with --execute to rename + patch catalogs.")
        return

    old_to_new = {}
    for old_name, new_name, old_path in plan:
        old_path.rename(old_path.parent / new_name)
        old_to_new[old_name] = new_name
    print(f"Renamed {len(plan)} files.")

    for xlsx_path, col_name in [(CA_CATALOG, "FileName"), (CS_CMA_CATALOG, "FinalPDFFileName")]:
        wb = openpyxl.load_workbook(xlsx_path)
        patched = 0
        for ws in wb.worksheets:
            header = [c.value for c in ws[1]]
            if col_name not in header:
                continue
            col_idx = header.index(col_name)
            for row in ws.iter_rows(min_row=2):
                cell = row[col_idx]
                if cell.value in old_to_new:
                    cell.value = old_to_new[cell.value]
                    patched += 1
        wb.save(xlsx_path)
        print(f"Patched {patched} '{col_name}' cells in {xlsx_path.name}")


if __name__ == "__main__":
    main()
