"""
telegram/admin_portal/document_catalog.py -- the 3 document-level
catalogue views (Study Materials, Exam Materials, Revision Material) plus
the Question Bank chapter-level MCQ/Descriptive count catalogue
(2026-08-12).
--------------------------------------------------------------------------------
Pranav's ask: "this course catalog should be part of a table in our db and
should be the single source of truth" was already built (course_catalog,
see populate_course_catalog.py) -- that's the CHAPTER/UNIT TAXONOMY layer.
This module adds the DOCUMENT layer on top of it: which real file exists
for which chapter, read live from telegram/source-docs/
knowledge_base_documents.json (built by tools/build_knowledge_base_catalog.py
from the same source Excel catalogs course_catalog itself is built from --
see that script's own docstring). Never hand-edited; regenerate it via
that script after adding/renaming any Study/Exam Material PDF.

FOUR catalogues, one function each below:
  - study_materials_rows()   -- course_catalog chapters, each joined to its
                                 real Study Material document(s), chapter
                                 granularity (not unit -- see _document_
                                 chapter_key()'s own docstring for why).
  - exam_materials_rows()    -- Exam Material documents, listed flat (not
                                 chapter-addressable -- these are exam
                                 papers, not syllabus chapters). Today only
                                 CA Inter Advanced Accounting has any (58
                                 files) -- every other course/level/subject
                                 legitimately shows empty, same "not sourced
                                 yet" honesty as Revision Material below,
                                 not a bug.
  - revision_material_rows() -- same shape as study_materials_rows(), but
                                 for document_type == "Revision Material".
                                 Legitimately empty everywhere today (no
                                 Revision Material PDFs exist on disk yet --
                                 confirmed, not assumed, by checking the
                                 folder directly).
  - question_bank_rows()     -- MCQ + Descriptive counts per chapter,
                                 computed from every real question's own
                                 human_id (course/level/paper/chapter/unit
                                 are baked into that ID -- see
                                 generate_mcq_human_ids.py), not a separate
                                 hand-maintained count. 100% accurate by
                                 construction: a chapter's count IS the
                                 number of real records whose human_id
                                 resolves to it, nothing is estimated.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_DOCUMENTS_PATH = REPO_ROOT / "telegram" / "source-docs" / "knowledge_base_documents.json"

# Reused, not re-derived -- see populate_course_catalog.py's own comments
# on both of these for the full reasoning (the Module-4-restart offset for
# CA Inter Corporate and Other Laws, and the flat-filename M-C-U pattern).
import populate_course_catalog as pcc  # noqa: E402 -- telegram/tools/ is on sys.path (see app.py)
import generate_mcq_human_ids as gen_ids  # noqa: E402


def _load_kb_documents() -> list:
    """Loaded fresh every call (not cached) -- this file is small (~1-2MB,
    ~1100 rows) and this is a single-admin internal tool, so a stale-cache
    class of bug isn't worth the complexity of invalidating it correctly."""
    if not KB_DOCUMENTS_PATH.exists():
        return []
    data = json.loads(KB_DOCUMENTS_PATH.read_text(encoding="utf-8"))
    return data.get("documents", [])


def _document_chapter_no(doc: dict):
    """Best-effort CHAPTER-level (not unit-level) key for a
    knowledge_base_documents.json row, mirroring populate_course_catalog.py's
    own per-source chapter_no derivation so a document lands on the same
    chapter row course_catalog itself would assign it to. Chapter, not
    unit, granularity deliberately -- unit-level matching would require
    re-deriving the SAME multi-unit-chapter special cases
    populate_course_catalog.py already handles (roman-numeral Labels,
    auxiliary-file exclusion, etc.) a second time here, which is exactly
    the kind of driftable duplication this codebase avoids elsewhere.
    Chapter-level is unambiguous and 100% accurate for "which file(s)
    exist for this chapter" -- the actual ask.

    Returns None if this document's document_type isn't chapter-addressable
    (Exam Material) or its chapter can't be determined.
    """
    if doc["document_type"] not in ("Study Material", "Revision Material"):
        return None

    course, level, subject = doc["course"], doc["level"], doc["subject"]
    nm = doc.get("native_metadata") or {}

    if course == "CA" and subject == "Advanced Accounting":
        m = re.match(r"M(\d+)-C(\d+)-U(\d+)", doc.get("native_code") or "")
        return int(m.group(2)) if m else None

    if course == "CA":
        chapter_no = nm.get("chapter_no")
        if not chapter_no:
            return None
        m = pcc.CA_FLAT_FNAME_UNIT_RE.search(doc["file_name"])
        module = int(m.group("module")) if m else None
        offset = pcc.CHAPTER_NO_MODULE_OFFSET.get((level, subject, module), 0)
        return int(chapter_no) + offset

    # CS / CMA -- chapter_no is carried straight from the Chapter Catalog,
    # no restart/offset cases found in that source (verified: ICSI/ICMAI
    # material has no cross-module restart pattern like CA's Other Laws).
    chapter_no = nm.get("chapter_no")
    return int(chapter_no) if chapter_no is not None else None


def _chapter_taxonomy_rows(conn, course, level, subject):
    """course_catalog rows for this subject, collapsed to one row per
    chapter_no (unit rows folded into a single 'units' list) -- the
    display grain every document-level catalogue below uses."""
    rows = conn.execute(
        "SELECT chapter_no, chapter_name, chapter_name_short, unit_no, unit_name "
        "FROM course_catalog WHERE course=? AND level=? AND subject=? ORDER BY chapter_no, unit_no",
        (course, level, subject),
    ).fetchall()
    by_chapter = {}
    for chapter_no, chapter_name, chapter_name_short, unit_no, unit_name in rows:
        entry = by_chapter.setdefault(chapter_no, {
            "chapter_no": chapter_no, "chapter_name": chapter_name,
            "chapter_name_short": chapter_name_short, "units": [],
        })
        if unit_no and unit_name:
            entry["units"].append(unit_name)
    return sorted(by_chapter.values(), key=lambda r: r["chapter_no"])


def _document_rows_by_chapter(course, level, subject, document_type):
    docs = _load_kb_documents()
    by_chapter = defaultdict(list)
    for doc in docs:
        if doc["course"] != course or doc["level"] != level or doc["subject"] != subject:
            continue
        if doc["document_type"] != document_type:
            continue
        chapter_no = _document_chapter_no(doc)
        if chapter_no is None:
            continue
        by_chapter[chapter_no].append(doc)
    return by_chapter


def study_materials_rows(conn, course, level, subject) -> list:
    chapters = _chapter_taxonomy_rows(conn, course, level, subject)
    by_chapter = _document_rows_by_chapter(course, level, subject, "Study Material")
    out = []
    for c in chapters:
        docs = by_chapter.get(c["chapter_no"], [])
        out.append({
            **c,
            "file_count": len(docs),
            "file_names": [d["file_name"] for d in docs],
            "total_pages": sum(d.get("page_count") or 0 for d in docs),
            "status": "available" if docs else "missing",
        })
    return out


def revision_material_rows(conn, course, level, subject) -> list:
    chapters = _chapter_taxonomy_rows(conn, course, level, subject)
    by_chapter = _document_rows_by_chapter(course, level, subject, "Revision Material")
    out = []
    for c in chapters:
        docs = by_chapter.get(c["chapter_no"], [])
        out.append({
            **c,
            "file_count": len(docs),
            "file_names": [d["file_name"] for d in docs],
            "total_pages": sum(d.get("page_count") or 0 for d in docs),
            "status": "available" if docs else "not sourced yet",
        })
    return out


def exam_materials_rows(course, level, subject) -> list:
    """Exam Materials aren't chapter-addressable (they're whole papers --
    an MTP/PYQ/RTP set), so this is a flat listing, not a taxonomy join."""
    docs = _load_kb_documents()
    out = []
    for doc in docs:
        if doc["course"] != course or doc["level"] != level or doc["subject"] != subject:
            continue
        if doc["document_type"] != "Exam Material":
            continue
        nm = doc.get("native_metadata") or {}
        out.append({
            "file_name": doc["file_name"], "native_title": doc.get("native_title"),
            "paper_type": nm.get("paper_type"), "session": nm.get("session"),
            "set_label": nm.get("set_label"), "doc_type": nm.get("doc_type"),
            "page_count": doc.get("page_count"),
        })
    out.sort(key=lambda r: (r["paper_type"] or "", r["session"] or "", r["set_label"] or "", r["doc_type"] or ""))
    return out


def question_bank_rows(conn, course, level, subject) -> list:
    """Chapter-level MCQ + Descriptive counts, derived from every real
    question's own human_id -- see this module's own docstring for why
    that's 100% accurate by construction rather than a maintained count."""
    chapters = _chapter_taxonomy_rows(conn, course, level, subject)
    counts = defaultdict(lambda: {"mcq": 0, "descriptive": 0})

    hid_re = re.compile(r"^(?P<course>CA|CS|CMA)_L\d+_P\w+_C(?P<chapter>\d+)_U\d+_\d+$")
    for src in gen_ids.CONTENT_SOURCES:
        if src["course"] != course or src["level"] != level:
            continue
        # A CONTENT_SOURCES entry is scoped to (course, level, paper_no),
        # not directly to subject -- confirm via course_catalog that this
        # paper_no really is the selected subject's paper before counting.
        row = conn.execute(
            "SELECT 1 FROM course_catalog WHERE course=? AND level=? AND paper_no=? AND subject=? LIMIT 1",
            (course, level, src["paper_no"], subject),
        ).fetchone()
        if not row:
            continue
        if not src["path"].exists():
            continue
        data = json.loads(src["path"].read_text(encoding="utf-8"))
        records = data["questions"] if isinstance(data, dict) and "questions" in data else data
        kind = "mcq" if src["id_field"] == "mcq_id" else "descriptive"
        for r in records:
            m = hid_re.match(r.get("human_id") or "")
            if not m:
                continue
            counts[int(m.group("chapter"))][kind] += 1

    out = []
    for c in chapters:
        cnt = counts.get(c["chapter_no"], {"mcq": 0, "descriptive": 0})
        out.append({**c, "mcq_count": cnt["mcq"], "descriptive_count": cnt["descriptive"],
                     "total_count": cnt["mcq"] + cnt["descriptive"]})
    return out
