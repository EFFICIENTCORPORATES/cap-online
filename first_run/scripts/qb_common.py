"""
qb_common.py -- shared helpers for the Question Bank Book front/back matter
generator and the whole-book merge script.

WHY THIS EXISTS
----------------
The 34 chapter files in first_run/output/*_Question_Book.html are the
finished content (Pranav's words: "the main content is done") -- this module
never touches their question/answer text. What it adds is everything needed
to turn 34 independent, screen-only review pages into one printable book:

1. A real page-geometry + paged.js print layer. first_run/schema/book-style.json
   already anticipated this (see its "page_geometry_for_future_print_stage"
   block, explicitly marked "not yet used") -- this module is what actually
   wires it in, reusing the exact architecture proven on the strategy book
   (position: running() for repeating headers/footers, a literal @page rule
   templated from the same JSON that drives the :root CSS variables, since
   @page does not reliably resolve var()).

2. A fix for a real bug found while checking mergeability: every chapter file
   hardcodes id="AS02-001", id="AS02-002"... regardless of which chapter it
   actually is (a copy-paste artifact from generate_chapter_book.py, which
   still has "AS02-" hardcoded in its render_qblock() f-string). Confirmed
   directly: AS10_Question_Book.html and AS20_Question_Book.html both contain
   id="AS02-001". Merged as-is, every chapter's ids would collide. Fixed here
   at merge time by rewriting to a chapter-slug prefix, not by touching the
   34 source files.

WHY THE EXISTING book-style.css IS DELIBERATELY *NOT* USED HERE
-------------------------------------------------------------------
book-style.css looks like the obvious shared stylesheet to reuse, and was
clearly intended to be -- but checked before assuming: it doesn't define
selectors for several classes the actual chapter files use throughout
(.case-facts, .mistakes, .badge, .options/li[data-opt], .stem, .note,
.empty-section, .build-info). Those were added to generate_chapter_book.py's
own inline STYLE string after book-style.css was written and never
backported. Swapping to book-style.css would render all of those completely
unstyled. Confirmed all 34 files' embedded <style> blocks are byte-identical
to each other (so there's exactly one real stylesheet in use, safe to take a
single copy of) -- it's just a different one than book-style.css. This
module takes that verified, actually-matching stylesheet and *appends* the
new print layer to it, rather than replacing it.

Typography for genuinely NEW content this module writes (front/back matter,
running headers, the ToC) uses book-style.json's intended Source Sans 3 /
Archivo pair -- there's no prior styling commitment for content that didn't
exist before, so no reason not to use the nicer, already-designed system
there. The 34 chapters' existing question/answer text keeps its current
Arial-based styling untouched, exactly as delivered.
"""

import json
import re
from pathlib import Path

FIRST_RUN = Path(__file__).resolve().parent.parent
OUTPUT_DIR = FIRST_RUN / "output"
SCHEMA_DIR = FIRST_RUN / "schema"
VENDOR_DIR = OUTPUT_DIR / "vendor"
BOOK_STYLE_JSON = SCHEMA_DIR / "book-style.json"

# The 34 *_Question_Book.html chapter files were moved from output/ directly
# into output/generated-from-script/ sometime between this pipeline's first
# working merge (2026-07-26 morning) and the print-cost-reduction pass later
# the same day -- discovered when qb_merge.py's validate_order() suddenly
# reported all 34 files missing. Not this script's doing (confirmed: front-
# matter.html/back-matter.html/vendor/ all stayed in output/ root, and the
# 34 files' content itself was also freshly regenerated at the same time,
# per their mtimes) -- someone else's reorganization + a fresh
# generate_all_chapter_books.py run, done outside this pipeline's control.
# load_chapter_html() below searches both locations so this pipeline keeps
# working whichever layout is current, instead of hardcoding one path that
# silently goes stale the next time output/ gets reorganized.
CHAPTERS_DIR = OUTPUT_DIR / "generated-from-script"

ERROR_REPORT_EMAIL = "capranavpratiktulshyan@gmail.com"
BOOK_TITLE = "CA Inter Advanced Accounts: The Complete Question Bank"

# The id="AS02-NNN" bug -- confirmed identical across every chapter file,
# regardless of that file's real chapter. Rewritten per-chapter at merge time.
_BUGGY_ID_RE = re.compile(r'id="AS02-(\d+)"')


def load_book_style() -> dict:
    with BOOK_STYLE_JSON.open(encoding="utf-8") as f:
        return json.load(f)


def load_chapter_html(filename: str) -> str:
    """Reads a chapter/front-matter/back-matter file by name, checking
    output/ directly first (front-matter.html, back-matter.html) and
    output/generated-from-script/ second (the 34 chapter books -- see
    CHAPTERS_DIR comment above for why both locations are checked)."""
    for candidate in (OUTPUT_DIR / filename, CHAPTERS_DIR / filename):
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"'{filename}' not found in {OUTPUT_DIR} or {CHAPTERS_DIR}"
    )


def extract_style_block(html_text: str) -> str:
    m = re.search(r"<style>(.*?)</style>", html_text, re.DOTALL)
    if not m:
        raise ValueError("No <style> block found -- unexpected chapter file shape.")
    return m.group(1)


def extract_body_inner(html_text: str) -> str:
    m = re.search(r"<body>(.*)</body>", html_text, re.DOTALL)
    if not m:
        raise ValueError("No <body>...</body> found -- unexpected chapter file shape.")
    return m.group(1).strip()


def rewrite_qblock_ids(body_inner: str, slug: str) -> str:
    """Fix the id="AS02-NNN" bug: rewrite to id="{slug}-NNN", unique per
    chapter. See module docstring point 2 -- this is not optional, merging
    two chapters without this produces duplicate/invalid HTML ids."""
    return _BUGGY_ID_RE.sub(lambda m: f'id="{slug}-{m.group(1)}"', body_inner)


_QBLOCK_OPEN_RE = re.compile(r'<div class="qblock[^"]*"[^>]*>')
_DIV_TAG_RE_G = re.compile(r'<div\b|</div>')

_STUDENT_NOTES_HTML = (
    '<div class="qb-student-notes">'
    '<span class="qb-sn-label">Your Notes:</span>'
    '<span class="qb-sn-line"></span>'
    '<span class="qb-sn-notebook">Practiced in Notebook &mdash; Page No.:</span>'
    '<span class="qb-sn-notebook-line"></span>'
    '</div>'
)


def inject_student_notes(body_inner: str) -> str:
    """Adds a compact "Your Notes" + "Notebook Page No." line to every
    .qblock, right before its own closing </div> -- added 2026-07-26,
    Pranav's request: students want space to jot a quick note and record
    which physical notebook/page they practiced a question in.

    Applied ONLY at merge time (here), never to the 34 source chapter
    files -- those are the on-screen review copies (nobody hand-writes in
    a screen), the merged/printed book is the only place this is actually
    useful. Deliberately a single compact two-line strip, not a large
    ruled box: this book already had a print-cost-reduction pass earlier
    the same day (margins/font shrunk 707 -> 388 pages), and 750+ questions
    each gaining a few mm adds up fast -- kept minimal on purpose. Easy to
    make taller later (edit _STUDENT_NOTES_HTML/its CSS) if a bigger box
    turns out to matter more than the extra pages it costs.

    Uses the same balanced-<div>-counting approach as
    generate_qb_toc.py's _find_matching_close() rather than a non-greedy
    regex, for the identical reason: a qblock's own closing </div> is NOT
    the first </div> encountered after its opening tag (it contains nested
    divs itself -- .question, .answer-block, .mistakes, etc.), so a lazy
    regex would silently insert the notes strip in the wrong place instead
    of after all of a question's real content.
    """
    out = []
    pos = 0
    for m in _QBLOCK_OPEN_RE.finditer(body_inner):
        depth = 1
        close_idx = None
        for tag in _DIV_TAG_RE_G.finditer(body_inner, m.end()):
            if tag.group() == "</div>":
                depth -= 1
                if depth == 0:
                    close_idx = tag.start()
                    break
            else:
                depth += 1
        if close_idx is None:
            raise ValueError("unbalanced <div> tags inside a .qblock -- "
                              "cannot safely insert student-notes strip")
        out.append(body_inner[pos:close_idx])
        out.append(_STUDENT_NOTES_HTML)
        pos = close_idx
    out.append(body_inner[pos:])
    return "".join(out)


def verify_shared_style(filenames: list) -> str:
    """Every chapter file's embedded <style> block must be byte-identical
    before it's safe to take just one copy of it for the merged book (see
    module docstring). Raises loudly instead of silently using a possibly-
    wrong stylesheet for some chapters."""
    styles = {}
    for fn in filenames:
        styles[fn] = extract_style_block(load_chapter_html(fn))
    reference_fn = filenames[0]
    reference = styles[reference_fn]
    diverged = [fn for fn in filenames[1:] if styles[fn] != reference]
    if diverged:
        raise SystemExit(
            f"ERROR: embedded <style> in these chapter files differs from "
            f"'{reference_fn}': {diverged}. Merging would silently apply the "
            f"wrong stylesheet to them -- re-verify before proceeding."
        )
    return reference


def print_layer_css(style: dict) -> str:
    """The additive print/pagination layer -- appended after the verified
    shared chapter stylesheet, never replacing it. See module docstring."""
    typ = style["typography"]
    col = style["colors"]
    geo = style["page_geometry_for_future_print_stage"]
    spc = style["spacing"]

    return f"""
/* ══════════════════════════════════════════════════════════════════════
   PRINT / PAGINATION LAYER (added by qb_common.py -- not part of the
   34 chapter files' own embedded style, which is left untouched above).
   Page geometry is templated from book-style.json's
   page_geometry_for_future_print_stage block -- literal values here AND
   in the :root block below, both from the same source, since @page does
   not reliably resolve var(). Edit book-style.json, never these numbers
   directly. ══════════════════════════════════════════════════════════ */

:root {{
  --qb-heading-font: {typ['heading_font']};
  --qb-body-font: {typ['body_font']};
  --qb-ink: {col['ink']};
  --qb-muted-ink: {col['muted_ink']};
  --qb-accent: {col['accent']};
  --qb-gold: #C9A227;
}}

.qb-book-content {{ max-width: none; }}  /* the 980px on-screen review cap doesn't apply once @page controls width */

/* Running header: book title + current chapter, repeats on every physical page */
.qb-running-header {{
  position: running(qbHeader);
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-family: var(--qb-heading-font);
  font-size: 8pt;
  letter-spacing: 0.03em;
  color: var(--qb-muted-ink);
  padding-bottom: 1.5mm;
  border-bottom: 0.5pt solid #d5dae0;
}}
.qb-running-header .qb-chapter {{ font-weight: 700; color: var(--qb-accent); }}

/* Running footer: repeats on every physical page; the page number itself
   comes from a separate @bottom-right box using counter(page), not this
   running element -- same split used on the strategy book and for the
   same reason (a running element's content is fixed at the point it's
   redefined in the flow; the page number must be evaluated per-page). */
.qb-running-footer {{
  position: running(qbFooter);
  font-family: var(--qb-heading-font);
  font-size: 7.5pt;
  color: var(--qb-muted-ink);
  padding-top: 1.5mm;
  border-top: 0.5pt solid #d5dae0;
}}

/* Overflow-proofing: never slice a table, options list, answer paragraph,
   or callout mid-way across a page break. The 34 chapter files' own
   embedded style has no break-inside rules at all (confirmed) -- added
   here rather than in the 34 files.

   NOTE (2026-07-26, revised from the original version of this rule):
   .qblock itself is deliberately NOT in this list anymore. It was
   originally included ("never slice a QUESTION across a page break"), but
   measured directly against the real output: with .qblock included, 312 of
   334 content pages (93%) held exactly ONE qblock, each with ~282px of the
   ~960px page left blank (~29% wasted) -- because break-inside:avoid on a
   large container means the WHOLE thing jumps to the next page the moment
   it doesn't fit the remaining space, not just the part that doesn't fit.
   Pranav caught this directly ("each question starting from a new page...
   space getting wasted"). The fix keeps the same guarantee at a smaller
   grain: a single question's stem/options, a single answer paragraph, a
   single table, and a single mistake/note box each still can never be cut
   mid-way -- but the page break IS now allowed to fall at the natural
   boundary BETWEEN a question's own Question / Answer / Mistakes /
   Extraction-note blocks (they're already separate sibling <div>s inside
   .qblock -- confirmed by reading a real qblock's markup, not guessed).
   That's a normal, readable place for a real book to break a page; an
   unbroken 282px gap in the middle of a chapter is not. */
.question, .answer-block, .mistakes, .extraction-note,
table, .note, .empty-section, .case-facts {{
  break-inside: avoid;
}}
h1, h2 {{ break-after: avoid; }}

/* Forces each front-matter page, chapter, and back-matter page onto a
   fresh physical page. Only meaningful once sections are concatenated --
   a lone chapter file has nothing to break away from, so this lives here,
   not in the 34 source files. */
.qb-section {{ break-before: page; }}

/* ── PRINT-COST REDUCTION (added 2026-07-26, Pranav's explicit request:
   printing cost tracks page count, so shrink both margins -- see @page
   below -- and the chapter content's own text size). This is an ADDITIVE
   OVERRIDE only, scoped under .qb-book-content for higher specificity than
   the 34 files' own bare-tag rules (e.g. their plain "table{{...}}" rule is
   (0,0,1) specificity; ".qb-book-content table" here is (0,1,1) and wins
   without needing !important) -- the 34 source files themselves are never
   edited.
   Values come from book-style.json's typography.chapter_print_* /
   spacing.chapter_print_* fields -- change the size there, not here. */
.qb-book-content {{
  font-size: {typ['chapter_print_body_size']};
  line-height: {typ['chapter_print_line_height']};
}}
.qb-book-content h1 {{ font-size: {typ['chapter_print_h1_size']}; }}
.qb-book-content h2 {{ font-size: {typ['chapter_print_h2_size']}; }}
.qb-book-content table {{ font-size: {typ['chapter_print_table_size']}; }}
.qb-book-content .qmeta,
.qb-book-content .badge,
.qb-book-content .note,
.qb-book-content .empty-section,
.qb-book-content .section-intro,
.qb-book-content .extraction-note {{ font-size: {typ['chapter_print_small_size']}; }}
.qb-book-content .qblock {{
  margin: {spc['chapter_print_qblock_margin']};
  padding: {spc['chapter_print_qblock_padding']};
}}

/* Student self-notes + notebook-page-reference strip (added 2026-07-26,
   Pranav's request) -- injected once per question by
   qb_common.inject_student_notes(), never in the 34 source chapter files.
   Deliberately compact: two label+blank-line rows, not a ruled box -- see
   inject_student_notes()'s docstring for the print-cost reasoning. */
.qb-student-notes {{
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 2mm;
  margin-top: 2mm;
  padding-top: 1.5mm;
  border-top: 0.5pt dashed #c7cdd3;
  font-family: var(--qb-heading-font);
  font-size: 7pt;
  color: var(--qb-muted-ink);
  break-inside: avoid;
}}
.qb-sn-label, .qb-sn-notebook {{ flex-shrink: 0; white-space: nowrap; }}
.qb-sn-line {{ flex: 1 1 40mm; min-width: 20mm; border-bottom: 0.5pt dotted #b5c0ca; }}
.qb-sn-notebook-line {{ flex: 0 0 18mm; border-bottom: 0.5pt dotted #b5c0ca; }}

/* Study-material cross-reference banner (added 2026-07-26, Pranav's
   request) -- one line at the top of each chapter, pointing to the
   matching study-material chapter code (e.g. "M2-C5-U1"), so a student can
   go straight from a Question Bank chapter to the right study-material
   chapter. Shown once per chapter here, not in the running header -- see
   page_shell()'s docstring in this file for why. */
.qb-study-ref {{
  font-family: var(--qb-heading-font);
  font-size: 8.5pt;
  color: var(--qb-muted-ink);
  letter-spacing: 0.02em;
  margin-bottom: 3mm;
}}
.qb-study-ref strong {{ color: var(--qb-accent); }}

@page {{
  size: {geo['page_width']} {geo['page_height']};
  margin: {geo['margin_top']} {geo['margin_outer']} {geo['margin_bottom']} {geo['margin_inner']};

  @top-center    {{ content: element(qbHeader); }}
  @bottom-center {{ content: element(qbFooter); }}
  @bottom-right  {{
    content: counter(page);
    font-family: var(--qb-heading-font);
    font-size: 8pt;
    font-weight: 700;
    color: var(--qb-ink);
  }}
}}
"""


def front_back_css(style: dict) -> str:
    """CSS for front/back-matter-only layouts (title page, copyright page,
    ToC, author bio). Not needed by the 34 chapter files, so it's kept out
    of print_layer_css() above (which every section gets); shared here
    between generate_qb_front_back_matter.py (standalone preview files) and
    qb_merge.py (the final merged book), so the two never drift apart."""
    col = style["colors"]
    return f"""
.qb-title-page {{
  /* Content-box height available on one physical page is page_height minus
     top+bottom margins (254mm - 20mm - 20mm = 214mm, from book-style.json).
     min-height was originally 220mm -- 6mm TALLER than that, which is
     exactly what caused a confirmed bug (2026-07-26): flex containers do
     not fragment predictably across a CSS page break, so the overflow
     silently scattered this page's own children (author name, credential
     line) onto a LATER physical page instead of visibly overflowing on
     page 1 where it would have been obvious. Kept safely under 214mm, plus
     break-inside: avoid as a second line of defence -- if it ever slightly
     overflows again (e.g. a future font-metric change), the whole block
     moves to the next page intact rather than fragmenting across two. */
  min-height: 190mm;
  break-inside: avoid;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 20mm 0 12mm;
  text-align: center;
}}
.qb-tp-series {{
  font-family: var(--qb-heading-font);
  font-size: 8pt;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--qb-muted-ink);
}}
.qb-tp-title {{
  font-family: var(--qb-heading-font);
  font-size: 26pt;
  font-weight: 800;
  line-height: 1.15;
  color: var(--qb-ink);
  margin: 10mm 0 4mm;
}}
.qb-tp-subtitle {{
  font-family: var(--qb-body-font);
  font-size: 12pt;
  color: var(--qb-muted-ink);
  margin-bottom: 8mm;
}}
.qb-tp-rule {{ height: 1.5pt; background: var(--qb-gold); width: 18mm; margin: 0 auto 6mm; }}
.qb-tp-author {{ font-family: var(--qb-heading-font); font-size: 13pt; font-weight: 700; color: var(--qb-ink); }}
.qb-tp-credential {{ font-family: var(--qb-body-font); font-size: 9.5pt; color: var(--qb-muted-ink); margin-top: 1.5mm; }}
.qb-tp-publisher {{ font-family: var(--qb-heading-font); font-size: 8.5pt; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--qb-muted-ink); }}

.qb-copyright-page {{ padding-top: 55mm; font-size: 9pt; color: var(--qb-muted-ink); line-height: 1.75; }}
.qb-copyright-page p {{ margin-bottom: 4mm; }}
.qb-copyright-page strong {{ color: var(--qb-ink); }}

.qb-page-title {{
  font-family: var(--qb-heading-font);
  font-size: 17pt;
  font-weight: 800;
  color: var(--qb-ink);
  margin-bottom: 6mm;
}}

.qb-howto p, .qb-howto li {{ font-family: var(--qb-body-font); font-size: 10pt; line-height: 1.65; color: var(--qb-ink); }}
.qb-howto h3 {{
  font-family: var(--qb-heading-font);
  font-size: 10.5pt;
  font-weight: 700;
  margin: 6mm 0 2mm;
  color: var(--qb-accent);
}}
.qb-howto ul {{ margin: 2mm 0 4mm 5mm; padding-left: 4mm; }}
.qb-howto li {{ margin-bottom: 1.5mm; }}
.qb-legend-swatch {{
  display: inline-block;
  padding: 1pt 6pt;
  border-radius: 4pt;
  font-size: 8.5pt;
  font-weight: 700;
  margin-right: 4mm;
}}
.qb-legend-examiner {{ background: {col['examiner_comment_bg']}; border: 1px solid {col['examiner_comment_border']}; }}
.qb-legend-author {{ background: {col['synthesized_comment_bg']}; border: 1px solid {col['synthesized_comment_border']}; }}

.qb-toc-entry {{
  display: flex;
  align-items: baseline;
  gap: 2mm;
  margin: 0 0 3mm;
  font-family: var(--qb-heading-font);
  font-size: 9.5pt;
  break-inside: avoid;
}}
.qb-toc-entry .qb-toc-num {{ color: var(--qb-muted-ink); width: 8mm; flex-shrink: 0; }}
.qb-toc-entry a {{ color: var(--qb-ink); text-decoration: none; font-weight: 600; }}
.qb-toc-ref {{
  font-family: var(--qb-body-font);
  font-size: 8pt;
  color: var(--qb-muted-ink);
  background: #eef1f4;
  border-radius: 3pt;
  padding: 0.5pt 4pt;
  flex-shrink: 0;
}}
.qb-toc-leader {{ flex: 1; border-bottom: 1px dotted #b5c0ca; margin-bottom: 1.2pt; }}
.qb-toc-page {{ font-family: var(--qb-heading-font); font-weight: 700; font-size: 9.5pt; color: var(--qb-ink); }}

.qb-bio p {{ font-family: var(--qb-body-font); font-size: 10pt; line-height: 1.7; color: var(--qb-ink); margin-bottom: 3mm; }}
"""


def page_shell(html_text: str, slug: str, chapter_label: str, study_ref: str = None) -> str:
    """Wraps one chapter's (id-fixed) body content with the running-header/
    footer elements and the .qb-section page-break wrapper. Used identically
    for chapters, front matter, and back matter (chapter_label describes
    whichever it is, e.g. 'AS 2: Valuation of Inventories' or 'Front Matter').

    study_ref (added 2026-07-26, Pranav's request) is the chapter's
    unique_chapter_id from the canonical topic/page index (e.g. "M2-C5-U1"),
    shown once as a banner at the top of the chapter's own content -- NOT
    repeated into the running header, which already redraws on every single
    physical page; putting a study-material pointer there would just repeat
    noise 10-30 times per chapter instead of stating it once where a student
    actually reads it, at the point they open the chapter."""
    body_inner = rewrite_qblock_ids(extract_body_inner(html_text), slug)
    body_inner = inject_student_notes(body_inner)
    ref_banner = (
        f'<div class="qb-study-ref">Study Material Reference: '
        f'<strong>{study_ref}</strong></div>\n'
        if study_ref else ""
    )
    return f"""<div class="qb-section" id="{slug}">
  <div class="qb-running-header">
    <span>{BOOK_TITLE}</span>
    <span class="qb-chapter">{chapter_label}</span>
  </div>
  <div class="qb-running-footer"></div>
  <div class="qb-book-content">
{ref_banner}{body_inner}
  </div>
</div>"""


def base_head(title: str, extra_css: str = "") -> str:
    """Shared <head> for standalone front-matter/back-matter preview files
    (not used for the final merged book, which builds its own single head --
    see qb_merge.py). Lets front/back matter be opened and reviewed on
    their own before merging, same convenience the strategy book's
    per-section files give."""
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="vendor/gfonts-local.css">
<style>
body {{ font-family: {load_book_style()['typography']['body_font']}; }}
{extra_css}
</style>"""
