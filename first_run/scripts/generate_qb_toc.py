#!/usr/bin/env python3
"""
generate_qb_toc.py: Table of Contents for the Question Bank Book
=====================================================================

Writes a standalone first_run/output/table-of-contents.html -- its own
file, not embedded inside front-matter.html (moved out 2026-07-27 per
Pranav's request: "you may remove the Table of content from front matter
and make a separate File altogether").

100% SCRIPT-DERIVED, NOT HAND-TYPED -- confirmed for Pranav, since he asked
directly: every row's chapter order, label, and study-material reference
code is read straight from qb_merge.py's CHAPTERS tuple (imported below,
never re-typed here) -- if that tuple's order or labels change, this ToC
updates the next time this script runs, with zero manual editing. The one
thing that ISN'T computed here is the page NUMBER on each row -- nobody
can know what page a chapter starts on until paged.js has actually laid
out the whole merged book in a real browser (font metrics, line-wrapping,
everything before it matters). Every row starts with an empty
`<span class="qb-toc-page" data-target-id="{slug}"></span>`, filled in
afterwards by resolve_qb_toc_pages.py, which reads the real
`data-page-number` paged.js stamps on each physical page once the book is
merged and rendered (see that script's own docstring for why
target-counter(), the "obvious" CSS-only answer, doesn't work in this
vendored paged.js version).

BECAUSE THIS FILE IS NOW FULLY OWNED BY THIS SCRIPT (no other script or
person ever hand-edits table-of-contents.html), regenerating it is a plain
full-file rewrite every time, not a patch of an existing file -- this is
also what fixes the earlier duplication bug for good: that bug came from
patching a div THAT ALREADY HAD ROWS IN IT using a regex that stopped at
the wrong closing tag. A script that always writes a fresh file from
scratch cannot have that class of bug, because there is never leftover
content to accidentally preserve.

USAGE
-----
    python generate_qb_toc.py
        Writes first_run/output/table-of-contents.html with blank page
        numbers. Safe to re-run any time.

    python generate_qb_toc.py --check
        Print the rows without writing anything (sanity-check the labels).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import qb_common as qc  # noqa: E402
from qb_merge import CHAPTERS  # noqa: E402

TOC_PATH = qc.OUTPUT_DIR / "table-of-contents.html"


def build_toc_rows() -> str:
    rows = []
    for idx, (slug, _filename, label, study_ref) in enumerate(CHAPTERS, start=1):
        rows.append(
            f'<div class="qb-toc-entry">'
            f'<span class="qb-toc-num">{idx}.</span>'
            f'<a href="#{slug}">{label}</a>'
            f'<span class="qb-toc-ref">{study_ref}</span>'
            f'<span class="qb-toc-leader"></span>'
            f'<span class="qb-toc-page" data-target-id="{slug}"></span>'
            f'</div>'
        )
    return "\n".join(rows)


def build_toc_page(style: dict) -> str:
    rows_html = build_toc_rows()
    body = f"""<div class="qb-section" id="qb-toc">
<h2 class="qb-page-title">Table of Contents</h2>
<div class="qb-toc-list" id="qb-toc-list">
{rows_html}
</div>
</div>"""
    return qc.wrap_page("Table of Contents: Question Bank Book", body, style)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check", action="store_true",
        help="Print the rows without writing anything."
    )
    args = ap.parse_args()

    if args.check:
        print(build_toc_rows())
        return

    style = qc.load_book_style()
    TOC_PATH.write_text(build_toc_page(style), encoding="utf-8")
    print(f"Written {len(CHAPTERS)} rows -> {TOC_PATH}")


if __name__ == "__main__":
    main()
