"""
Builds the ONE unified catalog the Study Hub bot reads, covering all three
categories now under telegram/assets/study_bot/ (Study Materials / Revision
Material / Exam Materials) and all three courses (CA / CS / CMA).

Inputs (all read-only):
  - telegram/source-docs/1Lavya_Study_Hub_File_Mapping.xlsx   (CA study chapters)
  - telegram/source-docs/CS_CMA_Chapter_Catalog.xlsx           (CS/CMA study chapters)
  - telegram/assets/study_bot/Exam Materials/*.pdf             (filenames parsed directly)
  - telegram/assets/study_bot/Revision Material/*.pdf          (best-effort, see below)

Output:
  - telegram/source-docs/StudyHub_Master_Catalog.xlsx  (sheet "Catalog")

Every row is one real file under telegram/assets/study_bot/<Category>/ --
this script cross-checks that at the end and fails loudly (not silently)
if a catalog row's FileName doesn't actually exist on disk, or if a real
file on disk has no catalog row.

Run: python telegram/tools/build_master_catalog.py
(after 1Lavya_Study_Hub_File_Mapping.xlsx and CS_CMA_Chapter_Catalog.xlsx
are already built/current -- see SKILL-study-bot-catalog-pipeline.md and
SKILL-cs-cma-toc-pipeline.md)
"""

import re
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cs_cma_common import REPO_ROOT

STUDY_BOT_ROOT = REPO_ROOT / "telegram" / "assets" / "study_bot"
CA_CATALOG = REPO_ROOT / "telegram" / "source-docs" / "1Lavya_Study_Hub_File_Mapping.xlsx"
CS_CMA_CATALOG = REPO_ROOT / "telegram" / "source-docs" / "CS_CMA_Chapter_Catalog.xlsx"
OUT_PATH = REPO_ROOT / "telegram" / "source-docs" / "StudyHub_Master_Catalog.xlsx"

CATEGORY_STUDY = "Study Materials"
CATEGORY_REVISION = "Revision Material"
CATEGORY_EXAM = "Exam Materials"

HEADERS = [
    "Category", "Course", "Level", "Subject", "Label", "ShortLabel",
    "ChapterNo", "PaperType", "Session", "SetLabel", "DocType",
    "Keywords", "FileName",
]


def normalize_ws(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


# ---------------------------------------------------------------------------
# Study Materials -- from the two existing per-course catalogs
# ---------------------------------------------------------------------------
def load_ca_study_rows():
    wb = openpyxl.load_workbook(CA_CATALOG, data_only=True)
    ws = wb["File Mapping"]
    headers = [c.value for c in ws[1]]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        d = dict(zip(headers, r))
        rows.append({
            "Category": CATEGORY_STUDY,
            "Course": d["Course"],
            "Level": d["Level"],
            "Subject": d["Subject"],
            "Label": d["ChapterName"],
            "ShortLabel": d["ChapterName"][:35],
            "ChapterNo": d["ChapterNo"],
            "PaperType": "", "Session": "", "SetLabel": "", "DocType": "",
            "Keywords": d.get("Keywords", ""),
            "FileName": d["FileName"],
        })
    return rows


def load_cs_cma_study_rows():
    wb = openpyxl.load_workbook(CS_CMA_CATALOG, data_only=True)
    ws = wb["Chapter Catalog"]
    headers = [c.value for c in ws[1]]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        d = dict(zip(headers, r))
        if not d.get("FinalPDFFileName") or d.get("PDFPageStart_1indexed") is None:
            continue  # e.g. the ESG "merged into an earlier lesson" row -- no file exists for it
        rows.append({
            "Category": CATEGORY_STUDY,
            "Course": d["Course"],
            "Level": d["Level"],
            "Subject": d["Subject"],
            "Label": d["ChapterName"],
            "ShortLabel": d["ShortChapterName"],
            "ChapterNo": d["ChapterNo"],
            "PaperType": "", "Session": "", "SetLabel": "", "DocType": "",
            "Keywords": f"{d['Subject']}, {d['ChapterName']}".lower(),
            "FileName": d["FinalPDFFileName"],
        })
    return rows


# ---------------------------------------------------------------------------
# Exam Materials -- parsed directly from filenames
# ---------------------------------------------------------------------------
# CourseLevel prefix -> (Course, Level). One entry per {course}{level_code}
# combination used by build_study_bot_catalog.py (CA) / build_cs_cma_catalog.py
# (CS/CMA) -- see those scripts for where each convention comes from.
COURSELEVEL_PREFIXES = {
    "CAFoundation": ("CA", "Foundation"), "CAInter": ("CA", "Inter"), "CAFinal": ("CA", "Final"),
    "CSExec": ("CS", "Executive"), "CSProf": ("CS", "Professional"), "CSEET": ("CS", "CSEET"),
    "CMAFoundation": ("CMA", "Foundation"), "CMAFound": ("CMA", "Foundation"),
    "CMAInter": ("CMA", "Intermediate"), "CMAFinal": ("CMA", "Final"),
}

MTP_RE = re.compile(
    r"^(?P<cl>[A-Za-z]+)-(?P<subj>[A-Za-z0-9]+)-(?P<pt>MTP)-(?P<sess>[A-Za-z]+\d+)-"
    r"(?P<set>Set\d+)-(?P<doc>Q|Ans)\.pdf$", re.IGNORECASE,
)
PYQ_EC_RE = re.compile(
    r"^(?P<cl>[A-Za-z]+)-(?P<subj>[A-Za-z0-9]+)-(?P<pt>PYQ)_Examiner_Comments-"
    r"(?P<sess>[A-Za-z]+\d+)\.pdf$", re.IGNORECASE,
)
SIMPLE_RE = re.compile(
    r"^(?P<cl>[A-Za-z]+)-(?P<subj>[A-Za-z0-9]+)-(?P<pt>PYQ|RTP)-(?P<sess>[A-Za-z]+\d+)-"
    r"(?P<doc>Q|Ans)\.pdf$", re.IGNORECASE,
)

DOC_LABEL = {"Q": "Questions", "Ans": "Answers", "EC": "Examiner Comments"}


def split_courselevel(cl: str):
    if cl in COURSELEVEL_PREFIXES:
        return COURSELEVEL_PREFIXES[cl]
    return None, cl  # unrecognized -- keep as Level so it's still visible, not silently dropped


def subject_lookup_from_study_rows(study_rows):
    """(Course, CourseLevelPrefix-ish SubjectShort-in-filename) is hard to
    reverse cleanly, so instead: build "<CourseLevel>-<SubjectShort>" ->
    Subject full name from the study rows already loaded, and match Exam
    filenames' own "<cl>-<subj>-" prefix against those same prefixes.
    CS/CMA study filenames are "<cl>-<subj>_..." (2 segments before the
    underscore); CA study filenames are "<cl>-<subj>-<session>_..." (an
    extra dash-separated segment first) -- this matches just the first
    two segments either way."""
    prefix_to_subject = {}
    for row in study_rows:
        m = re.match(r"^([A-Za-z]+)-([A-Za-z0-9]+)[-_]", row["FileName"])
        if m:
            prefix_to_subject[f"{m.group(1)}-{m.group(2)}"] = row["Subject"]
    return prefix_to_subject


def load_exam_rows(study_rows):
    folder = STUDY_BOT_ROOT / CATEGORY_EXAM
    prefix_to_subject = subject_lookup_from_study_rows(study_rows)
    rows = []
    unmatched = []

    for pdf_path in sorted(folder.glob("*.pdf")):
        fname = pdf_path.name
        m = MTP_RE.match(fname) or PYQ_EC_RE.match(fname) or SIMPLE_RE.match(fname)
        if not m:
            unmatched.append(fname)
            continue
        gd = m.groupdict()
        course, level = split_courselevel(gd["cl"])
        subj_prefix = f"{gd['cl']}-{gd['subj']}"
        subject = prefix_to_subject.get(subj_prefix, gd["subj"])  # fall back to the raw short code
        doc = gd.get("doc") or "EC"
        set_label = gd.get("set", "") or ""
        paper_type = gd["pt"]

        label_parts = [paper_type, gd["sess"]]
        if set_label:
            label_parts.append(set_label)
        label_parts.append(DOC_LABEL.get(doc, doc))
        label = " ".join(label_parts)

        rows.append({
            "Category": CATEGORY_EXAM,
            "Course": course or "",
            "Level": level,
            "Subject": subject,
            "Label": label,
            "ShortLabel": label[:35],
            "ChapterNo": "",
            "PaperType": paper_type,
            "Session": gd["sess"],
            "SetLabel": set_label,
            "DocType": DOC_LABEL.get(doc, doc),
            "Keywords": f"{subject} {paper_type} {gd['sess']} {set_label} {DOC_LABEL.get(doc, doc)}".lower(),
            "FileName": fname,
        })

    if unmatched:
        print(f"WARNING: {len(unmatched)} Exam Materials file(s) didn't match any known naming "
              f"pattern -- not catalogued, review naming or extend the regexes in this script:")
        for u in unmatched:
            print("  ", u)

    return rows


# ---------------------------------------------------------------------------
# Revision Material -- currently empty; best-effort generic handling so the
# pipeline doesn't need touching again the moment it's populated.
# ---------------------------------------------------------------------------
def load_revision_rows(study_rows):
    folder = STUDY_BOT_ROOT / CATEGORY_REVISION
    prefix_to_subject = subject_lookup_from_study_rows(study_rows)
    rows = []
    for pdf_path in sorted(folder.glob("*.pdf")):
        fname = pdf_path.name
        m = re.match(r"^([A-Za-z]+)-([A-Za-z0-9]+)[-_]", fname)
        course, level, subject = "", "", ""
        if m:
            course, level = split_courselevel(m.group(1))
            course = course or ""
            subj_prefix = f"{m.group(1)}-{m.group(2)}"
            subject = prefix_to_subject.get(subj_prefix, m.group(2))
        label = normalize_ws(Path(fname).stem.replace("_", " ").replace("-", " "))
        rows.append({
            "Category": CATEGORY_REVISION,
            "Course": course, "Level": level, "Subject": subject,
            "Label": label, "ShortLabel": label[:35], "ChapterNo": "",
            "PaperType": "", "Session": "", "SetLabel": "", "DocType": "",
            "Keywords": label.lower(), "FileName": fname,
        })
    return rows


# ---------------------------------------------------------------------------
def write_excel(rows):
    wb = openpyxl.Workbook()
    readme = wb.active
    readme.title = "Read Me First"
    readme.column_dimensions["A"].width = 100
    readme["A1"] = "Study Hub Master Catalog (auto-generated)"
    readme["A1"].font = Font(bold=True, size=13)
    lines = [
        "",
        "GENERATED by telegram/tools/build_master_catalog.py. Do not hand-edit --",
        "fix the source catalogs (1Lavya_Study_Hub_File_Mapping.xlsx for CA,",
        "CS_CMA_Chapter_Catalog.xlsx for CS/CMA) or this script, and re-run.",
        "",
        "One row per real file under telegram/assets/study_bot/<Category>/.",
        "Category is one of: Study Materials, Revision Material, Exam Materials.",
        "Study Materials rows use ChapterNo/Label; Exam Materials rows use",
        "PaperType/Session/SetLabel/DocType instead -- Study-only and Exam-only",
        "columns are blank on rows from the other category.",
        "",
        "See _claude/skills/SKILL-study-bot-catalog-pipeline.md and",
        "SKILL-cs-cma-toc-pipeline.md for the full pipeline.",
    ]
    for i, line in enumerate(lines, start=2):
        readme[f"A{i}"] = line

    ws = wb.create_sheet("Catalog")
    widths = [16, 6, 14, 42, 55, 35, 9, 9, 10, 9, 16, 55, 65]
    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    for col_idx, (h, w) in enumerate(zip(HEADERS, widths), start=1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = Font(bold=True)
        cell.fill = header_fill
        ws.column_dimensions[cell.column_letter].width = w
    ws.freeze_panes = "A2"

    for row_idx, r in enumerate(rows, start=2):
        for col_idx, h in enumerate(HEADERS, start=1):
            ws.cell(row=row_idx, column=col_idx, value=r[h])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_PATH)


def cross_check_against_disk(rows):
    """Every catalog row's file must exist; every real file must have a
    catalog row. Report both directions -- never silently drop or invent."""
    problems = []
    by_cat = {}
    for r in rows:
        by_cat.setdefault(r["Category"], set()).add(r["FileName"])

    for category in (CATEGORY_STUDY, CATEGORY_REVISION, CATEGORY_EXAM):
        folder = STUDY_BOT_ROOT / category
        on_disk = {p.name for p in folder.glob("*.pdf")} if folder.exists() else set()
        catalogued = by_cat.get(category, set())

        missing_files = catalogued - on_disk
        for fn in sorted(missing_files):
            problems.append(f"[{category}] catalog row references a file NOT on disk: {fn}")

        uncatalogued = on_disk - catalogued
        for fn in sorted(uncatalogued):
            problems.append(f"[{category}] file on disk has NO catalog row: {fn}")

    return problems


def main():
    ca_rows = load_ca_study_rows()
    cs_cma_rows = load_cs_cma_study_rows()
    study_rows = ca_rows + cs_cma_rows
    exam_rows = load_exam_rows(study_rows)
    revision_rows = load_revision_rows(study_rows)

    all_rows = study_rows + revision_rows + exam_rows
    write_excel(all_rows)

    print(f"Wrote {len(all_rows)} rows to {OUT_PATH}")
    print(f"  Study Materials: {len(study_rows)}  (CA {len(ca_rows)} + CS/CMA {len(cs_cma_rows)})")
    print(f"  Revision Material: {len(revision_rows)}")
    print(f"  Exam Materials: {len(exam_rows)}")

    problems = cross_check_against_disk(all_rows)
    if problems:
        print(f"\n{len(problems)} catalog/disk MISMATCH(es):")
        for p in problems:
            print("  ", p)
    else:
        print("\nOK: every catalog row has a matching file on disk, and vice versa, in all 3 categories.")


if __name__ == "__main__":
    main()
