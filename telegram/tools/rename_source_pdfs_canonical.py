"""
Rename every registered Study/Exam Material PDF (telegram/assets/study_bot/)
to a canonical, human_id-style stem: {COURSE}_L{level_num}_P{paper_no}_C{chapter}_U{unit}[-{n}].pdf

Source of truth for the mapping (no re-deriving from scratch):
  - telegram/source-docs/knowledge_base_documents.json  (course/level/subject/native_code/source_path per file)
  - telegram/database/platform.db's course_catalog table  (authoritative level_num + paper_no per course/level/subject)

After renaming, the two upstream Excel catalogs are patched (FileName /
FinalPDFFileName columns only -- old name -> new name, nothing else touched),
then build_master_catalog.py and build_knowledge_base_catalog.py are re-run
so every downstream artifact (StudyHub_Master_Catalog.xlsx,
knowledge_base_documents.json) reflects the new names. build_master_catalog.py
already self-validates disk<->catalog both ways and fails loudly on mismatch.

Also adds a `canonical_id` field to knowledge_base_documents.json (the new
stem) alongside the existing document_id -- see build_knowledge_base_catalog.py.

--dry-run (default): prints the plan, writes nothing.
--execute: renames on disk + patches the two source Excels.

Usage: python telegram/tools/rename_source_pdfs_canonical.py [--execute]
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

import openpyxl

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_JSON = REPO_ROOT / "telegram" / "source-docs" / "knowledge_base_documents.json"
DB_PATH = REPO_ROOT / "telegram" / "database" / "platform.db"
CA_CATALOG = REPO_ROOT / "telegram" / "source-docs" / "1Lavya_Study_Hub_File_Mapping.xlsx"
CS_CMA_CATALOG = REPO_ROOT / "telegram" / "source-docs" / "CS_CMA_Chapter_Catalog.xlsx"

FULL_CODE_RE = re.compile(r"^M(\d+)-C(\d+)-U(\d+)$")
SINGLE_CODE_RE = re.compile(r"^[ML](\d+)$")


def load_paper_lookup():
    """(course, level, subject) -> (level_num, paper_no), from the
    platform's own course_catalog table -- the same authority the rest of
    the platform already uses for this (see COURSE-CATALOG.md)."""
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute("SELECT DISTINCT course, level, subject, level_num, paper_no FROM course_catalog").fetchall()
    conn.close()
    lookup = {}
    for course, level, subject, level_num, paper_no in rows:
        lookup[(course, level, subject)] = (level_num, _pad_paper_no(paper_no))
    return lookup


def _pad_paper_no(paper_no):
    """"3" -> "03", "13" -> "13", "6A" -> "06A" -- matches the human_id
    convention already used platform-wide (e.g. "CA_L2_P03_C1_U0_00001")."""
    s = str(paper_no).strip()
    m = re.match(r"^(\d+)([A-Za-z]*)$", s)
    if not m:
        return s
    digits, suffix = m.groups()
    return digits.zfill(2) + suffix


def parse_native_code(native_code):
    """Returns (chapter, unit) or None if unparseable."""
    nc = (native_code or "").strip()
    m = FULL_CODE_RE.match(nc)
    if m:
        return int(m.group(2)), int(m.group(3))
    m = SINGLE_CODE_RE.match(nc)
    if m:
        return int(m.group(1)), 0
    return None


def build_plan():
    docs = json.loads(KB_JSON.read_text(encoding="utf-8"))["documents"]
    paper_lookup = load_paper_lookup()

    plan = []          # (doc, old_path, new_stem, ext)
    skipped = []        # (doc, reason)
    stem_counts = {}

    for d in docs:
        key = (d["course"], d["level"], d["subject"])
        if key not in paper_lookup:
            skipped.append((d, f"no course_catalog match for {key}"))
            continue
        level_num, paper_no = paper_lookup[key]

        parsed = parse_native_code(d.get("native_code"))
        if parsed is None:
            skipped.append((d, f"unparseable native_code {d.get('native_code')!r}"))
            continue
        chapter, unit = parsed

        stem = f"{d['course']}_L{level_num}_P{paper_no}_C{chapter}_U{unit}"
        stem_counts[stem] = stem_counts.get(stem, 0) + 1
        plan.append([d, stem])

    # disambiguate collisions with a running -2, -3... suffix, stable order
    seen = {}
    for entry in plan:
        d, stem = entry
        if stem_counts[stem] > 1:
            seen[stem] = seen.get(stem, 0) + 1
            entry[1] = f"{stem}-{seen[stem]}"

    return plan, skipped


def main():
    execute = "--execute" in sys.argv
    plan, skipped = build_plan()

    old_to_new = {}   # old file_name -> new file_name (for Excel patching)
    rename_ops = []    # (old_path: Path, new_path: Path)

    for d, new_stem in plan:
        old_path = REPO_ROOT / d["source_path"]
        new_name = new_stem + old_path.suffix
        new_path = old_path.parent / new_name
        old_to_new[d["file_name"]] = new_name
        rename_ops.append((old_path, new_path, d["file_name"], new_name))

    print(f"Total registered documents: {len(plan) + len(skipped)}")
    print(f"Renameable: {len(plan)}   Skipped (left as-is): {len(skipped)}")
    if skipped:
        print("\nSkipped documents (need manual attention, not touched):")
        for d, reason in skipped:
            print(f"  {d['file_name']}: {reason}")

    missing_on_disk = [op for op in rename_ops if not op[0].exists()]
    if missing_on_disk:
        print(f"\nABORT: {len(missing_on_disk)} source files listed in the catalog are missing on disk:")
        for op in missing_on_disk[:10]:
            print(f"  {op[0]}")
        sys.exit(1)

    collisions = [op for op in rename_ops if op[1].exists() and op[1] not in [o[0] for o in rename_ops]]
    if collisions:
        print(f"\nABORT: {len(collisions)} target filenames already exist on disk and aren't part of this rename set:")
        for op in collisions[:10]:
            print(f"  {op[1]}")
        sys.exit(1)

    if not execute:
        print(f"\nDRY RUN -- {len(rename_ops)} files would be renamed. Sample:")
        for op in rename_ops[:8]:
            print(f"  {op[2]}  ->  {op[3]}")
        print("\nRe-run with --execute to actually rename + patch catalogs.")
        return

    # --- execute: rename files on disk ---
    renamed = 0
    for old_path, new_path, _, _ in rename_ops:
        old_path.rename(new_path)
        renamed += 1
    print(f"Renamed {renamed} files on disk.")

    # --- patch the two source Excel catalogs' FileName columns ---
    for xlsx_path, col_name in [(CA_CATALOG, "FileName"), (CS_CMA_CATALOG, "FinalPDFFileName")]:
        wb = openpyxl.load_workbook(xlsx_path)
        patched = 0
        for ws in wb.worksheets:
            header = [c.value for c in ws[1]]
            if col_name not in header:
                continue
            col_idx = header.index(col_name) + 1
            for row in ws.iter_rows(min_row=2):
                cell = row[col_idx - 1]
                old_name = cell.value
                if old_name in old_to_new:
                    cell.value = old_to_new[old_name]
                    patched += 1
        wb.save(xlsx_path)
        print(f"Patched {patched} '{col_name}' cells in {xlsx_path.name}")

    # write the plan for the downstream knowledge_base_documents.json rebuild
    plan_out = REPO_ROOT / "telegram" / "tools" / "_last_pdf_rename_plan.json"
    plan_out.write_text(json.dumps(old_to_new, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Old->new mapping written to {plan_out} (for reference / downstream rebuilds).")


if __name__ == "__main__":
    main()
