#!/usr/bin/env python3
"""
generate_qb_coverage_matrix.py -- "Chapter-wise Sitting Summary": a
marks-coverage matrix (rows = the book's 34 chapters, in the same
teaching-sequence order as qb_merge.CHAPTERS; columns = exam sessions)
showing which chapters have been tested how heavily, across every
MTP/RTP/PYQ sitting in this edition. Pranav's request (2026-07-28): a
student should be able to see at a glance which chapters actually matter,
not just read a flat chapter-by-chapter Table of Contents.

WHY THREE SEPARATE PAGES (MTP / RTP / PYQ), NOT ONE TABLE
------------------------------------------------------------
34 sittings as individual columns doesn't fit an A4 page even in landscape.
Pranav's own proposed fix, applied here: one column per exam SESSION, not
per individual paper/set (an MTP session's Set 1 + Set 2 collapse into one
column -- see qb_common.sessions_for()), split into three pages by paper
type: MTP (~7 sessions), PYQ (~9), RTP (~7). Each ends with a row-summed
Total column, which doubles as a "which chapters matter most" ranking.

WHY RTP SHOWS QUESTION COUNT, NOT MARKS
------------------------------------------
ICAI's RTP documents carry no per-question marks-weighted answer key (see
book_stats.json's own "sittings_without_marks_in_source" note) -- a marks
matrix for RTP would just be a page of zeros. Question count is the
next-best coverage signal and is used instead, with the page's own note
saying so explicitly rather than silently changing units on the reader.

LEGACY-* chapters (pre-syllabus-change topics, see CLAUDE.md section 6) are
excluded here for the same reason they're excluded from chapter books --
there's no real chapter row for them to belong to.

Reads questions_index.json directly. Never hand-edit output/chapter-
coverage-matrix.html -- re-run this script any time the corpus changes
(HOW-TO-BUILD-THE-BOOK.md documents where this fits in the build sequence).

Usage: python generate_qb_coverage_matrix.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qb_common as qc  # noqa: E402
from qb_merge import CHAPTERS  # noqa: E402 -- the one canonical chapter order/labels

INDEX_PATH = qc.OUTPUT_DIR / "generated-from-script" / "questions_index.json"
OUT_PATH = qc.OUTPUT_DIR / "chapter-coverage-matrix.html"

STYLE = qc.load_book_style()


def load_index() -> list:
    with INDEX_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def short_chapter_label(unitcode: str, chapter_label: str) -> str:
    """Compact row label for a narrow matrix column. Prefers file 1's own
    chapter_name_short (e.g. Framework's full name is too long for this
    column even after the ':'-split fallback -- Pranav, 2026-07-28); falls
    back to the ':'-split heuristic ('AS 2: Valuation of Inventories' ->
    'AS 2') if the chapter isn't found there for some reason."""
    lookup = qc.chapter_name_short_lookup()
    short = lookup.get(unitcode)
    if short:
        return short
    return chapter_label.split(":")[0].strip()


def build_page(paper_type: str, rows: list, metric_note: str) -> str:
    sessions = qc.sessions_for(rows, paper_type)
    is_marks = paper_type != "RTP"

    by_key = {}
    for r in rows:
        if r.get("paper_type") != paper_type:
            continue
        fc = r.get("final_chapter")
        if not fc or fc.startswith("LEGACY-"):
            continue
        key = (fc, r.get("exam_year"), r.get("exam_month"))
        by_key.setdefault(key, []).append(r)

    col_headers = "".join(f"<th>{qc.session_label(y, m)}</th>" for (y, m) in sessions)

    body_rows = []
    for slug, _filename, chapter_label, fc in CHAPTERS:
        cells = []
        row_total = 0
        for (y, m) in sessions:
            cell_rows = by_key.get((fc, y, m), [])
            value = qc.dedup_marks_sum(cell_rows) if is_marks else qc.dedup_count(cell_rows)
            row_total += value
            cls = " qb-matrix-zero" if value == 0 else ""
            cells.append(f'<td class="{cls.strip()}">{value if value else "&ndash;"}</td>')
        body_rows.append(
            f'<tr><td class="qb-matrix-chapter">{short_chapter_label(fc, chapter_label)}</td>'
            f'{"".join(cells)}<td class="qb-matrix-total">{row_total}</td></tr>'
        )

    table = (
        '<table class="qb-matrix-table">'
        f'<thead><tr><th>Chapter</th>{col_headers}<th>Total</th></tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        "</table>"
    )

    return f"""
<div class="qb-matrix-page qb-section">
<h2 class="qb-page-title">{paper_type} Coverage by Chapter and Session</h2>
<p class="qb-matrix-note">{metric_note}</p>
{table}
</div>
"""


def main():
    rows = load_index()

    pages = [
        build_page(
            "MTP", rows,
            "Marks tested per chapter, per session &mdash; Set 1 and Set 2 of the same "
            "session are combined into one column. Total sums across every MTP session "
            "in this edition; a higher total means this chapter has been examined more "
            "heavily in Mock Test Papers.",
        ),
        build_page(
            "PYQ", rows,
            "Marks tested per chapter, per session, drawn from ICAI's own published "
            "Suggested Answers &mdash; this is the closest signal to real exam "
            "importance in this table.",
        ),
        build_page(
            "RTP", rows,
            "Question <strong>COUNT</strong> per chapter, per session, not marks &mdash; "
            "ICAI's RTP documents carry no per-question marks-weighted answer key, so "
            "count is the best available coverage signal here. Do not compare these "
            "numbers directly against the MTP/PYQ marks pages.",
        ),
    ]
    body = "\n".join(pages)
    html_out = qc.wrap_page("Chapter-wise Sitting Summary", body, STYLE)
    OUT_PATH.write_text(html_out, encoding="utf-8")
    print(f"Written: {OUT_PATH}")


if __name__ == "__main__":
    main()
