#!/usr/bin/env python3
"""
strategy_book_merge.py — CA Inter Strategy Book: whole-book assembler
=======================================================================

WHAT THIS SCRIPT DOES
----------------------
`tools/strategy_book_parser.py` renders each section of the book (Bucket 0,
Bucket 1, ... AI Section, Emergency, ...) as its OWN independent, standalone
HTML file in `books/strategy-book/design/templates/build/`. That is
deliberate and stays exactly as-is — it's what lets you preview or edit one
bucket at a time without touching anything else.

This script does the OTHER half of the job: it takes those independent files,
in a specific book order, and stitches them into ONE continuous HTML document
so that paged.js can paginate the ENTIRE book as a single flow — which is the
only way to get continuous page numbers and running headers/footers that
correctly switch over as the reader crosses from one bucket into the next.

Merging is not just "glue the files together". Read section-by-section
below for WHY each step exists — several of these are fixes for real bugs
that were found (and verified, not guessed) while building this script.
If you are tempted to simplify this file, read the docstring of the
function you're about to touch first.


WHY A DEDICATED SCRIPT AND NOT JUST `cat file1 file2 file3 > book.html`
------------------------------------------------------------------------
Naive concatenation of the full standalone files would break the result in
several concrete ways:

1.  DUPLICATE <style> BLOCKS. Every generated file embeds the full CSS.
    Verified by diffing 4 different generated files byte-for-byte: the CSS
    is IDENTICAL across every section (it only depends on page geometry,
    never on section colour/label — those are inline styles on individual
    elements, never baked into the shared stylesheet). So the merged file
    only needs ONE copy of it, not 14. This script re-verifies that
    assumption at run time (see `extract_style`) rather than trusting it
    blindly forever — if a future edit ever makes one section's CSS diverge
    from the others, this script will refuse to merge silently.

2.  DUPLICATE <script src=".../paged.polyfill.js"> TAGS. Each standalone
    file loads paged.js once. If all 14 copies of that <script> tag survive
    into the merged file, the browser would initialise the paged.js engine
    14 times against the same DOM — at best wasted work, at worst the
    engine re-processing an already-paginated document and corrupting its
    own output. The merged file must have exactly ONE <script> tag, at the
    very end, after all the content.

3.  DUPLICATE / COLLIDING IDS. Every strategy heading is rendered with
    `id="s{number}"`, and that number restarts at 1 in every bucket.
    Confirmed directly: bucket-0.html and bucket-1.html both contain
    id="s1", id="s2", id="s3" ... Concatenated as-is, the merged book would
    have duplicate ids scattered throughout — invalid HTML, and any
    internal link to "#s3" would only ever jump to the FIRST bucket's
    strategy 3, never the intended one. This script rewrites every such id
    to be prefixed with its section slug (id="bucket-1-s3") while stitching.

4.  NO PAGE-BREAK BETWEEN SECTIONS. A lone section file doesn't need to
    force a break before its own content — there's nothing before it in
    that file. But once sections are concatenated, each one needs to start
    on a fresh right-hand (recto) page, the normal convention for book
    chapters, and the one that matches this book's edge-tab design (already
    right-page-only). This script wraps each section's content in a
    `.book-section` div and adds `break-before: right` — a rule that only
    makes sense for the merged file, so it isn't part of the shared
    per-section CSS at all.

5.  A RELATIVE SCRIPT PATH THAT ONLY WORKS FROM ONE FOLDER. Every generated
    file references paged.js as "../vendor/paged.polyfill.js" — correct
    because the generated files live in .../templates/build/. If the merged
    file were written anywhere else, that reference would silently fail:
    no error dialog, paged.js simply never runs, and the "book" just looks
    like one long unstyled scroll with no pagination. This script always
    writes its output into the SAME build/ folder, so the existing relative
    path keeps working unchanged.

6.  A BOOK ORDER THAT CAN GO STALE. The order sections appear in the final
    book (cover, front matter, routing, Bucket 0..6, AI section, Emergency,
    Personal Pages, Author's Journey) is a decision, not something
    derivable from filenames or folder listing order. It is expressed here
    as an explicit, human-edited tuple (BOOK_ORDER below) rather than
    encoded into the filenames themselves (which would mean renaming
    multiple files any time the order changes — easy to get subtly wrong).
    Because the order is separate from the folder contents, this script
    actively cross-checks the two: any slug in BOOK_ORDER whose file is
    missing is a hard error (can't silently produce a book missing a
    chapter); any .html file sitting in build/ that ISN'T in BOOK_ORDER is a
    loud warning (protects against a newly-added section quietly never
    making it into the merged book because someone forgot to list it here).


USAGE
-----
    python tools/strategy_book_merge.py
        Merge using the default BOOK_ORDER below, write
        design/templates/build/FULL-BOOK.html

    python tools/strategy_book_merge.py --order cover,front-matter,bucket-0
        Merge only these sections, in this exact order (handy for testing
        a subset without waiting for the whole book to paginate).

    python tools/strategy_book_merge.py --force
        Proceed even if the per-section CSS has drifted (see point 1 above)
        or if a build/ file isn't listed in BOOK_ORDER — normally both are
        hard stops. Use this only once you've deliberately confirmed the
        divergence/omission is intentional.

After running, open the output file in Chrome, wait for paged.js to finish
repainting it into pages (a full book will take noticeably longer than a
single bucket — this is normal, not a hang), then Ctrl+P -> Save as PDF with
Background graphics enabled. See _claude/skills/SKILL-html-to-pdf.md §9 for
why the plain `--print-to-pdf` CLI path does not work for paged.js output.
"""

import argparse
import re
import sys
from pathlib import Path

# ── Book order ──────────────────────────────────────────────────────────────
# Front-to-back order of the finished book. This is a DECISION, kept here as
# plain data, deliberately separate from filenames (see point 6 in the module
# docstring for why). Edit this tuple — never rename files — when the book's
# structure changes.
BOOK_ORDER = (
    "cover",
    "front-matter",
    "routing",
    "bucket-0",
    "bucket-1",
    "bucket-2",
    "bucket-3",
    "bucket-4",
    "bucket-5",
    "bucket-6",
    "ai-section",
    "emergency",
    "personal-pages",
    "authors-journey",
)

BOOK_TITLE = "The Comprehensive CA Intermediate Exam Preparation Guide"

# CSS that only makes sense once sections are concatenated — deliberately
# NOT part of tools/strategy_book_parser.py's get_css(), because a single
# standalone section file has no "previous section" to break away from.
MERGE_ONLY_CSS = """
/* ── Added only for the merged whole-book file (strategy_book_merge.py) ──
   Forces every section onto a fresh right-hand (recto) page, matching
   normal book chapter-start convention and this book's right-page-only
   edge-tab design. */
.book-section { break-before: right; }
"""

# Matches the id="s3" pattern strategy_book_parser.py emits for every
# strategy heading. The number restarts at 1 in every bucket (verified: e.g.
# bucket-0.html and bucket-1.html both contain id="s1", id="s2" ...), so it
# MUST be made unique per section before sections are concatenated, or the
# merged document ends up with duplicate ids (invalid HTML, and internal
# "#s3" links would only ever resolve to the first bucket that defines it).
_STRAT_ID_RE = re.compile(r'id="s(\d+)"')

# Matches the paged.js <script> tag that every standalone file ends with.
# Exactly one copy of this must survive into the merged file (see point 2
# in the module docstring) — this regex strips it out of each section
# fragment so it can be re-added, once, at the very end.
_PAGEDJS_SCRIPT_RE = re.compile(
    r'\s*<script src="[^"]*paged\.polyfill\.js"></script>\s*'
)


def load_section_html(build_dir: Path, slug: str) -> str:
    """Read one generated section file as UTF-8 text.

    Explicit encoding='utf-8' everywhere in this script, matching
    strategy_book_parser.py's own discipline — this repo has a documented
    history of cross-mount UTF-8/UTF-16 corruption (see CLAUDE.md), and this
    content already contains em-dashes, curly quotes, and ★ characters that
    a platform-default codepage (cp1252 on Windows) would mangle silently.
    """
    path = build_dir / f"{slug}.html"
    return path.read_text(encoding="utf-8")


def extract_style(html_text: str) -> str:
    """Pull the <style>...</style> inner text out of one generated file."""
    m = re.search(r"<style>(.*?)</style>", html_text, re.DOTALL)
    if not m:
        raise ValueError("No <style> block found — is this really a "
                          "strategy_book_parser.py-generated file?")
    return m.group(1)


def extract_body_inner(html_text: str) -> str:
    """Pull everything between <body> and </body>, minus the paged.js
    <script> tag (which is re-added exactly once by build_merged_html)."""
    m = re.search(r"<body>(.*)</body>", html_text, re.DOTALL)
    if not m:
        raise ValueError("No <body>...</body> found — is this really a "
                          "strategy_book_parser.py-generated file?")
    body = m.group(1)
    body = _PAGEDJS_SCRIPT_RE.sub("", body)
    return body.strip()


def rewrite_strategy_ids(body_inner: str, slug: str) -> str:
    """Prefix every id="sN" with the section slug -> id="{slug}-sN".

    Why: strategy numbers restart at 1 in every bucket (this was verified,
    not assumed — see module docstring point 3), so the raw ids collide the
    moment two sections share one document. This is the one correctness fix
    in this whole script that must never be skipped, even under --force.
    """
    return _STRAT_ID_RE.sub(lambda m: f'id="{slug}-s{m.group(1)}"', body_inner)


def wrap_section(body_inner: str, slug: str) -> str:
    """Wrap a section's content so it starts on a fresh right-hand page.

    A standalone section file has nothing before it, so it never needed a
    forced page break. Once sections are concatenated, each one needs to
    start clean on a recto page (see module docstring point 4) — that rule
    lives in MERGE_ONLY_CSS and is applied via this wrapper div, which only
    exists in the merged output, never in the per-section files.
    """
    return f'<div class="book-section" data-section="{slug}">\n{body_inner}\n</div>'


def validate_order(order: list, build_dir: Path, output_name: str, force: bool) -> None:
    """Cross-check BOOK_ORDER (or --order) against what's actually in build/.

    Two failure modes are checked, deliberately in both directions:
      - a slug in `order` with no matching file  -> the merged book would be
        missing a chapter outright. Always a hard error, --force does not
        override this (there is nothing sensible to merge instead).
      - a .html file that exists in build/ but ISN'T in `order`           -> it
        would silently never make it into the merged book. Hard error
        unless --force is passed (in which case it's a loud warning) —
        this is precisely the mistake of adding a new section to MASTER.md
        and forgetting to list its slug here.
    """
    missing = [slug for slug in order if not (build_dir / f"{slug}.html").exists()]
    if missing:
        raise SystemExit(
            "ERROR: BOOK_ORDER lists section(s) with no generated file:\n  "
            + "\n  ".join(missing)
            + f"\nRun: python tools/strategy_book_parser.py --section all"
        )

    all_slugs = {p.stem for p in build_dir.glob("*.html")}
    output_stem = Path(output_name).stem
    orphaned = sorted(all_slugs - set(order) - {output_stem})
    if orphaned:
        msg = (
            "sections exist in build/ but are NOT listed in BOOK_ORDER "
            "(they will be silently left out of the merged book):\n  "
            + "\n  ".join(orphaned)
        )
        if force:
            print(f"WARNING: {msg}\n(--force: proceeding anyway)")
        else:
            raise SystemExit(
                f"ERROR: {msg}\n"
                "Add them to BOOK_ORDER (or pass --order explicitly), or "
                "re-run with --force if leaving them out is intentional."
            )


def check_css_consistency(build_dir: Path, order: list, force: bool) -> str:
    """Verify every section's embedded CSS is byte-identical before reusing
    just one copy of it for the whole merged book.

    This was verified true for the current generator (get_css() depends only
    on page geometry, never on section colour/label — see Claude_V2.md §13.5)
    but that's a fact about today's code, not a law of nature. If someone
    later hand-edits one generated file, or changes the generator so CSS
    starts depending on section-specific state, this check is what catches
    the drift instead of silently shipping a merged book where some section
    quietly renders with the wrong stylesheet.
    """
    first_slug = order[0]
    reference = extract_style(load_section_html(build_dir, first_slug))
    diverged = []
    for slug in order[1:]:
        style = extract_style(load_section_html(build_dir, slug))
        if style != reference:
            diverged.append(slug)

    if diverged:
        msg = (
            f"CSS in the following section(s) differs from '{first_slug}':\n  "
            + "\n  ".join(diverged)
            + "\nMerging would silently apply the WRONG stylesheet to them."
        )
        if force:
            print(f"WARNING: {msg}\n(--force: proceeding with '{first_slug}' CSS anyway)")
        else:
            raise SystemExit(
                f"ERROR: {msg}\n"
                "Regenerate all sections from the same generator version "
                "(python tools/strategy_book_parser.py --section all), or "
                "pass --force if this divergence is deliberate."
            )
    return reference


def warn_if_stale(build_dir: Path, order: list) -> None:
    """Warn (don't block) if MASTER.md was edited more recently than any of
    the build/ files being merged — a strong hint the build/ folder needs
    regenerating first, otherwise the merged book reflects stale content."""
    master = (
        Path(__file__).resolve().parent.parent
        / "books" / "strategy-book" / "working" / "CA-Inter-Strategy-Book-MASTER.md"
    )
    if not master.exists():
        return
    master_mtime = master.stat().st_mtime
    stale = [
        slug for slug in order
        if (build_dir / f"{slug}.html").stat().st_mtime < master_mtime
    ]
    if stale:
        print(
            "WARNING: MASTER.md is newer than these generated files — "
            "the merge may reflect stale content:\n  " + "\n  ".join(stale)
            + "\nConsider: python tools/strategy_book_parser.py --section all"
        )


def check_vendor_present(build_dir: Path) -> None:
    """Sanity-check the paged.js file the merged output will reference
    actually exists, before writing a file that would otherwise silently
    fail to paginate with no visible error (see module docstring point 5)."""
    vendor = build_dir.parent / "vendor" / "paged.polyfill.js"
    if not vendor.exists():
        raise SystemExit(
            f"ERROR: {vendor} not found — the merged file's "
            '<script src="../vendor/paged.polyfill.js"> reference would '
            "silently fail to load and paged.js would never run."
        )


def build_merged_html(build_dir: Path, order: list, shared_style: str) -> str:
    """Assemble the final single-document HTML.

    Structure:
      - ONE <head> (meta/title/style/fonts already inside shared_style) —
        never one per section (see module docstring point 1).
      - Each section's body content, id-rewritten and page-break-wrapped,
        concatenated in `order`.
      - ONE paged.js <script> tag at the very end (see module docstring
        point 2) — not one per section.
    """
    sections_html = []
    for slug in order:
        text = load_section_html(build_dir, slug)
        body_inner = extract_body_inner(text)
        body_inner = rewrite_strategy_ids(body_inner, slug)
        sections_html.append(wrap_section(body_inner, slug))

    body = "\n\n".join(sections_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{BOOK_TITLE}</title>
  <style>{shared_style}{MERGE_ONLY_CSS}</style>
</head>
<body>
{body}
<script src="../vendor/paged.polyfill.js"></script>
</body>
</html>"""


def main():
    ap = argparse.ArgumentParser(
        description="Merge independent strategy-book section HTML files "
                    "into one paged.js-paginated whole-book file."
    )
    ap.add_argument(
        "--build-dir", default=None,
        help="Folder containing the generated per-section .html files "
             "(default: books/strategy-book/design/templates/build/, "
             "resolved relative to this script's location)"
    )
    ap.add_argument(
        "--output", default="FULL-BOOK.html",
        help="Output filename, written INTO --build-dir (must stay there "
             "so the ../vendor/paged.polyfill.js reference keeps working — "
             "see module docstring point 5)."
    )
    ap.add_argument(
        "--order", default=None,
        help="Comma-separated list of section slugs, overriding BOOK_ORDER "
             '(e.g. --order cover,front-matter,bucket-0). Useful for '
             "merging a quick subset while testing."
    )
    ap.add_argument(
        "--force", action="store_true",
        help="Proceed past CSS-divergence and orphaned-section warnings "
             "instead of stopping (never overrides a missing-file error — "
             "there's nothing sensible to substitute for a missing chapter)."
    )
    args = ap.parse_args()

    if args.build_dir:
        build_dir = Path(args.build_dir)
    else:
        build_dir = (
            Path(__file__).resolve().parent.parent
            / "books" / "strategy-book" / "design" / "templates" / "build"
        )
    if not build_dir.is_dir():
        raise SystemExit(f"ERROR: build dir not found: {build_dir}")

    order = list(args.order.split(",")) if args.order else list(BOOK_ORDER)

    validate_order(order, build_dir, args.output, args.force)
    check_vendor_present(build_dir)
    warn_if_stale(build_dir, order)
    shared_style = check_css_consistency(build_dir, order, args.force)

    merged = build_merged_html(build_dir, order, shared_style)

    out_path = build_dir / args.output
    out_path.write_text(merged, encoding="utf-8")

    print(f"Merged {len(order)} sections -> {out_path}")
    print(f"  ({len(merged):,} characters)")
    print(
        "Next: open this file in Chrome, wait for paged.js to finish "
        "paginating (a full book takes noticeably longer than a single "
        "bucket — that's expected), then Ctrl+P -> Save as PDF with "
        "Background graphics enabled."
    )


if __name__ == "__main__":
    main()
