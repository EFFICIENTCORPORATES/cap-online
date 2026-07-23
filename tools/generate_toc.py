#!/usr/bin/env python3
"""
generate_toc.py — Table of Contents for the CA Inter Strategy Book
=====================================================================

WHAT THIS DOES AND WHY IT'S A SEPARATE STEP FROM THE PAGE NUMBERS THEMSELVES
------------------------------------------------------------------------------
This script produces `build/toc.html` — one row per section, in book order,
each linking to that section's opening anchor. It does NOT compute or write
any page number. It cannot: nobody knows what page Bucket 3 starts on until
paged.js has actually laid out the entire merged book, and that depends on
font metrics, line-wrapping, and how much content came before it -- none of
which this script (or any Python script) has any way to calculate correctly.

Every ToC row emits a clickable title link (`<a href="#bucket-3">`) plus a
separate, empty `<span class="toc-page" data-target-id="bucket-3"></span>`
that starts life blank. CSS target-counter() looked like the obvious way to
fill that span in automatically at layout time -- it's a real CSS Paged
Media feature, and paged.js's CSS parser accepts the syntax without
complaint -- but empirically it does NOT resolve to an actual value in this
vendored paged.js version (confirmed by testing against a matching,
still-open upstream bug: pagedjs/pagedjs#145, "TOC page number always
zero"). See Claude_V2.md for the full investigation.

The actual, verified-working mechanism: run `tools/resolve_toc_pages.py`
AFTER the first merge. It drives a real headless Chrome instance, waits for
paged.js to genuinely finish (polls `data-page-number` stability over real
wall-clock time -- a lesson from this same book's earlier debugging), looks
up which physical page each `data-target-id` anchor landed inside, and
rewrites this file's empty `.toc-page` spans with the real page number as
plain static text. Merge a second time afterward and the numbers are baked
in correctly. This is a two-pass build (content, then position, then a
final pass with position now known) -- the same principle LaTeX or InDesign
use for any cross-reference, just implemented against a live browser
instead of a typesetting log file.

WHERE THE ANCHORS COME FROM
------------------------------
strategy_book_parser.py's `_h1()` now writes `id="{slug}"` on every
section's opening heading (the `.bucket-banner` div for buckets, `.section-h1`
for everything else). Slugs are already unique across the whole merged book
(they're literal filenames), so -- unlike the `id="sN"` strategy-heading ids
-- these never need merge-time rewriting.

WHERE THE BOOK ORDER COMES FROM
-----------------------------------
Imported directly from strategy_book_merge.py's BOOK_ORDER, not duplicated
here. If the book's order ever changes, this ToC updates automatically the
next time it's regenerated -- there is exactly one place that decides section
order, not two lists that can quietly drift out of sync with each other.

"front-matter" is deliberately excluded from the listed rows (a ToC doesn't
usually list itself / the front matter it's physically part of -- real books
start their contents list at Chapter 1, not the title page), but front-matter
still needs to exist in BOOK_ORDER for the merge itself.

USAGE
-----
    python tools/generate_toc.py
        Writes build/toc.html. Safe to re-run any time -- unlike
        front-matter.html and authors-journey.html, this file has no
        hand-authored content and is always fully regenerable.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from strategy_book_parser import SECTION_META, INK, build_page  # noqa: E402
from strategy_book_merge import BOOK_ORDER  # noqa: E402

BUILD_DIR = (
    Path(__file__).resolve().parent.parent
    / "books" / "strategy-book" / "design" / "templates" / "build"
)

# Slugs excluded from the listed rows (see module docstring) -- "toc" is
# this page itself, "front-matter" is the front matter this ToC sits inside.
EXCLUDED_FROM_LISTING = {"toc", "front-matter", "cover"}


def _slug_to_meta() -> dict:
    """SECTION_META is keyed by MASTER.md heading text, not slug -- build
    the slug -> meta lookup this script actually needs, once."""
    return {meta["slug"]: meta for meta in SECTION_META.values()}


def _display_label(slug: str, meta: dict) -> str:
    """'Bucket 3 — Revision Phase' for buckets, plain label otherwise.
    Uses SECTION_META's already-correct, human-written label field --
    deliberately NOT a naive .title() of the raw MASTER.md heading (that
    exact bug already bit authors-journey.html once this session: naive
    title-casing mangled 'CPT' into 'Cpt' and an apostrophe-s into 'S').
    """
    if meta["slug"].startswith("bucket-"):
        return f'Bucket {meta["index"]}: {meta["label"]}'
    return meta["label"]


def build_toc_rows(order: tuple) -> str:
    slug_meta = _slug_to_meta()
    rows = []
    for slug in order:
        if slug in EXCLUDED_FROM_LISTING:
            continue
        meta = slug_meta.get(slug)
        if not meta:
            raise SystemExit(
                f"ERROR: no SECTION_META entry found for slug '{slug}' -- "
                "generate_toc.py needs a color/label to build its row. "
                "Add an entry to SECTION_META in strategy_book_parser.py."
            )
        label = _display_label(slug, meta)
        # .toc-page starts empty -- tools/resolve_toc_pages.py fills in the
        # real page number as plain text after the first merge (see module
        # docstring for why target-counter() couldn't be used here).
        rows.append(
            f'<div class="toc-entry">'
            f'<a href="#{slug}" style="color:{meta["color"]}">{label}</a>'
            f'<span class="toc-leader"></span>'
            f'<span class="toc-page" data-target-id="{slug}" style="color:{meta["color"]}"></span>'
            f'</div>'
        )
    return "\n".join(rows)


def main():
    rows_html = build_toc_rows(BOOK_ORDER)
    body_html = (
        '<h1 class="section-h1">Table of Contents</h1>\n'
        '<div class="toc-list">\n'
        f'{rows_html}\n'
        '</div>'
    )
    page_html = build_page(body_html, slug="toc", color=INK, label="Contents")

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BUILD_DIR / "toc.html"
    out_path.write_text(page_html, encoding="utf-8")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
