#!/usr/bin/env python3
"""
generate_qb_toc.py: Table of Contents for the Question Bank Book
=====================================================================

Same job as tools/generate_toc.py, adapted for the Question Bank Book's
different shape: this book's ToC lives INSIDE front-matter.html (the
"Table of Contents" page generate_qb_front_back_matter.py already writes,
currently with an empty `<div class="qb-toc-list" id="qb-toc-list"></div>`)
rather than as its own separate file -- there's no equivalent of the
strategy book's standalone toc.html here.

This script regenerates ONLY that one div's contents inside
front-matter.html (a plain string replace between two known markers) --
front-matter.html has no hand-authored content anywhere in it (confirmed:
it's 100% produced by generate_qb_front_back_matter.py), so overwriting
this one section is safe and expected to be re-run freely, same discipline
as the strategy book's toc.html.

Every row gets a real title link (`<a href="#{slug}">`) plus an EMPTY
`<span class="qb-toc-page" data-target-id="{slug}"></span>` -- filled in
later by resolve_qb_toc_pages.py the same way tools/resolve_toc_pages.py
does it for the strategy book (target-counter() is confirmed broken in
this vendored paged.js version; data-page-number read via a real headless
Chrome pass is the only working mechanism -- see that script's docstring
for the full investigation, not repeated here).

WHERE THE CHAPTER LIST COMES FROM
------------------------------------
Imported directly from qb_merge.py's CHAPTERS, not duplicated here -- if
the book's chapter order or labels ever change, this ToC updates the next
time it's regenerated. There is exactly one place that decides chapter
order and labels.

USAGE
-----
    python generate_qb_toc.py
        Rewrites the qb-toc-list div inside first_run/output/front-matter.html
        with blank page-number spans. Safe to re-run any time.

    python generate_qb_toc.py --check
        Print the rows without writing anything (sanity-check the labels).
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import qb_common as qc  # noqa: E402
from qb_merge import CHAPTERS  # noqa: E402

FRONT_MATTER_PATH = qc.OUTPUT_DIR / "front-matter.html"

_TOC_LIST_OPEN_RE = re.compile(r'<div class="qb-toc-list" id="qb-toc-list">')
_DIV_TAG_RE = re.compile(r'<div\b|</div>')


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


def _find_matching_close(text: str, open_tag_end: int) -> int:
    """Given the index right after a `<div ...>` opening tag, walk forward
    counting nested `<div` opens / `</div>` closes and return the index of
    the `</div>` that actually closes THIS div.

    This replaces a non-greedy regex (`(.*?)(</div>)`) that was confirmed
    (2026-07-26, Pranav caught it as "the Table of Contents has been
    repeated") to silently match only up to the FIRST nested `</div>` --
    correct only while qb-toc-list was still empty. The moment it holds 34
    `<div class="qb-toc-entry">...</div>` rows, the lazy match stopped at
    row 1's own closing tag, so every re-run replaced only row 1 and left
    the old rows 2-34 sitting in the file untouched -- each re-run added a
    full fresh set of 34 rows while only ever removing one stale row,
    explaining exactly the growing duplicate count Pranav saw. Balanced-tag
    counting is correct regardless of how many rows already exist, so this
    script is now safe to re-run on an already-populated file, not just an
    empty one.
    """
    depth = 1
    for m in _DIV_TAG_RE.finditer(text, open_tag_end):
        if m.group() == "</div>":
            depth -= 1
            if depth == 0:
                return m.start()
        else:
            depth += 1
    raise ValueError("unbalanced <div> tags -- no matching </div> found")


def patch_front_matter(rows_html: str) -> None:
    text = FRONT_MATTER_PATH.read_text(encoding="utf-8")
    open_matches = list(_TOC_LIST_OPEN_RE.finditer(text))
    if len(open_matches) != 1:
        raise SystemExit(
            f"ERROR: expected exactly one qb-toc-list div in "
            f"{FRONT_MATTER_PATH}, found {len(open_matches)}. Re-run "
            "generate_qb_front_back_matter.py first if this file has "
            "drifted from its generator's expected shape."
        )
    open_tag = open_matches[0]
    close_start = _find_matching_close(text, open_tag.end())

    new_text = (
        text[:open_tag.end()]
        + "\n" + rows_html + "\n"
        + text[close_start:]
    )
    FRONT_MATTER_PATH.write_text(new_text, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check", action="store_true",
        help="Print the rows without writing anything."
    )
    args = ap.parse_args()

    rows_html = build_toc_rows()

    if args.check:
        print(rows_html)
        return

    if not FRONT_MATTER_PATH.exists():
        raise SystemExit(
            f"ERROR: {FRONT_MATTER_PATH} not found -- run "
            "generate_qb_front_back_matter.py first."
        )

    patch_front_matter(rows_html)
    print(f"Patched {len(CHAPTERS)} ToC rows into: {FRONT_MATTER_PATH}")


if __name__ == "__main__":
    main()
