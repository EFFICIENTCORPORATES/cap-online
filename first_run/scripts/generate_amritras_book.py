#!/usr/bin/env python3
"""
generate_amritras_book.py -- "The Amritras of Question Bank": a condensed,
chapter-wise ready-reckoner sibling of QUESTION-BANK-BOOK.html, built for
final revision (not first-time learning).

WHAT THIS IS, AND WHY IT'S A SEPARATE SCRIPT
----------------------------------------------
Same underlying corpus (first_run/output/generated-from-script/
questions_index.json -- ALL 34 sittings, nothing dropped), same chapter
order/labels/study-refs (qb_merge.CHAPTERS, imported not re-typed), same
Topic-wise Marks Mapping logic (generate_chapter_book.build_topic_summary,
imported not re-derived) and the same print/pagination/typography layer
(qb_common.py) as the main Question Bank Book -- but every question renders
as a stripped reference card (sitting / Q.No / Marks / Topic / Examiner's
Comment or Author's Note only -- no question text, no answer text) instead
of the full worked question. Per Pranav's brief (2026-08-27):
  - No accuracy/scope/"how organised" notes per chapter (stated once, in
    front matter, instead of repeated 34 times).
  - Topic-wise Marks Mapping stays, identical format, all 3 paper types.
  - Student Self Notes grown from 2 lines to 3.
  - A NEW 1-page-per-chapter Error Register (this book's own choice --
    the main book deliberately moved to one shared 6-page register at the
    back on 2026-07-28 for print-cost reasons; Amritras is short enough
    per chapter that a dedicated page per chapter is worth it again here).
  - Dedication page dropped; "How to Read This Book" rewritten as
    "How to Understand this Amritras"; title/branding otherwise identical.
  - A new "For the complete book, visit vcgurukul.com" pointer.

This is deliberately its OWN script, not a flag bolted onto
generate_chapter_book.py/qb_merge.py -- the main book's 34 *_Question_Book.html
files are Pranav's already-reviewed, finished screen copies (CLAUDE.md
section 6: "the main content is done"); Amritras must never touch or
regenerate those. Every render function below is fresh, working straight
from questions_index.json, reusing the main pipeline's HELPER FUNCTIONS
(never its finished output files) so the two books can't silently drift
apart on facts (topic labels, marks, comment text, chapter order) while
still being visually/structurally distinct documents.

USAGE
-----
    python generate_amritras_book.py
        Regenerates chapter-coverage-matrix.html (fresh), writes
        amritras-front-matter.html / amritras-table-of-contents.html /
        amritras-back-matter.html (standalone, reviewable individually,
        same convention as the main book's front/back matter), then merges
        everything + all 34 condensed chapters + their error-register pages
        into first_run/output/AMRITRAS-QUESTION-BANK.html, and finally
        resolves real ToC page numbers via a real headless-Chrome pagination
        pass (same mechanism as resolve_qb_toc_pages.py, reused not
        reimplemented) and bakes them in with a second merge pass.

    python generate_amritras_book.py --no-resolve
        Skip the headless-Chrome page-number pass (leaves ToC page numbers
        blank) -- useful if Chrome/Edge or websocket-client isn't available
        in this environment; the file is otherwise complete and correct.
"""
import argparse
import html as html_lib
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import qb_common as qc  # noqa: E402
import generate_chapter_book as gcb  # noqa: E402 -- paper_label/qno_label/marks_span/
                                      # topic_label/build_topic_summary/select_chapter_rows/
                                      # load_index/STYLE all reused directly, never re-derived.
from generate_all_chapter_books import TITLE_OVERRIDES, slug as fc_slug  # noqa: E402
from qb_merge import CHAPTERS  # noqa: E402 -- the one canonical chapter order/labels/refs

OUTPUT_DIR = qc.OUTPUT_DIR
OUT_FILENAME = "AMRITRAS-QUESTION-BANK.html"
AMRITRAS_BOOK_TITLE = "The Amritras of Question Bank"
VCGURUKUL_LINE = 'For the complete book with the full question and worked answer, visit <strong>vcgurukul.com</strong>.'


# ═══════════════════════════════════════════════════════════════════════
# Chapter identity lookup -- filename -> (real final_chapter code, the
# short standard_label, the chapter_title) -- replicates
# generate_all_chapter_books.main()'s own derivation exactly (same
# TITLE_OVERRIDES table, same slug() function, imported not copied) so
# each qb_merge.CHAPTERS entry resolves to the SAME final_chapter code the
# main book's own generator used for that file, never independently
# re-guessed and risking drift (this is exactly the class of bug
# CLAUDE.md section 6's 2026-08-07 entry found and fixed once already).
# ═══════════════════════════════════════════════════════════════════════
def build_fc_lookup(data: list) -> dict:
    chapter_info = {}
    counts = Counter()
    for r in data:
        fc = r["final_chapter"]
        if fc and fc.startswith("LEGACY-"):
            continue
        counts[fc] += 1
        for t in r["topics"]:
            if t["unitcode"] == fc:
                chapter_info[fc] = (t.get("standard"), t.get("title"))
    lookup = {}
    for fc in counts:
        std, title = chapter_info.get(fc, (None, "Unknown"))
        if fc in TITLE_OVERRIDES:
            label, chapter_title = TITLE_OVERRIDES[fc]
        else:
            label, chapter_title = (std or fc), title
        out_filename = f"{fc_slug(fc, std)}_Question_Book.html"
        lookup[out_filename] = (fc, label, chapter_title)
    return lookup


# ═══════════════════════════════════════════════════════════════════════
# Front matter
# ═══════════════════════════════════════════════════════════════════════
def build_title_page() -> str:
    return f"""
<div class="qb-title-page">
  <div><p class="qb-tp-series">CA Intermediate &middot; Advanced Accounts</p></div>
  <div>
    <h1 class="qb-tp-title">THE AMRITRAS<br>of QUESTION BANK</h1>
    <p class="qb-tp-subtitle">A condensed, chapter-wise ready reckoner &mdash; topic mapping, examiner insight &amp; your own revision notes, for final revision before the exam</p>
    <div class="qb-tp-rule"></div>
    <p class="qb-tp-author">CA Pranav Pratik Tulshyan</p>
    <p class="qb-tp-credential">AIR 1 (Foundation) &middot; AIR 1 (Intermediate)</p>
  </div>
  <div>
    <p class="qb-tp-publisher">VC Gurukul &middot; Noida</p>
    <p class="qb-tp-credential" style="margin-top:5mm;">{VCGURUKUL_LINE}</p>
  </div>
</div>
"""


def build_copyright_page() -> str:
    # Verbatim identical to the main book's copyright/disclaimer page
    # (generate_qb_front_back_matter.build_front_matter()) -- Pranav's
    # explicit instruction: "Publication and disclaimers to be the same."
    return f"""
<div class="qb-copyright-page">
  <p>&copy; 2026 CA Pranav Pratik Tulshyan. All rights reserved.</p>
  <p>Published by VC Gurukul, Noida.</p>
  <p>No part of this publication may be reproduced, stored in a retrieval system, or transmitted in any form or by any means, electronic, mechanical, photocopying, recording, or otherwise, without the prior written permission of the author.</p>
  <p><strong>Disclaimer: Source Material.</strong> Questions are drawn from ICAI's own published MTP, RTP, and PYQ papers and their official Suggested Answers / Answer Keys. Examiner's Comments, where quoted, are taken from ICAI's published "Examiners' Comments on the Performance of the Examinees" documents where one exists for that sitting.</p>
  <p><strong>Disclaimer: Accuracy.</strong> This is the first edition of this book, assembled with AI assistance and reviewed as carefully as we could manage, but it has not been independently audited question-by-question. If you spot an error, please email <strong>{qc.ERROR_REPORT_EMAIL}</strong> with the question reference so it can be corrected in the next edition.</p>
  <p><strong>Disclaimer: Author's Notes.</strong> Any note labelled "Author's Note" is the author's own identification of a likely student pitfall, not an official ICAI finding, and may not apply in every case. The label on every note in this book tells you which kind it is.</p>
  <p style="margin-top:8mm; padding-top:3mm; border-top:0.5pt solid #dde3e8; font-size:8pt;">First published 2026 &middot; VC Gurukul, Noida.</p>
</div>
"""


def build_howto_page() -> str:
    return f"""
<h2 class="qb-page-title">How to Understand this Amritras</h2>
<div class="qb-howto">
<p><strong>Amrit Ras</strong> &mdash; the essence, distilled. This book is the essence of <strong>The Complete Question Bank</strong>: the same every MTP/RTP/PYQ question, chapter by chapter, but stripped down to just its coordinates and its insight &mdash; no question text, no worked answer. It exists for the days when you already know how to solve a question, and just need to be reminded that it was asked, where it sits, and what usually goes wrong with it.</p>

<p><strong>Use it this way:</strong> practise from the full Question Bank Book (or your class notes) first. In the last stretch before your exam, flip through this Amritras chapter by chapter &mdash; if a card's Q.No and topic bring the question straight back to mind, tick it off; if it doesn't, that's exactly what your Self Notes space and this chapter's own Error Register are for. {VCGURUKUL_LINE}</p>

<h3>Colour key</h3>
<p>
<span class="qb-legend-swatch qb-legend-examiner">Examiner&rsquo;s Comment</span>
<span class="qb-legend-swatch qb-legend-author">Author&rsquo;s Note</span>
<span class="qb-legend-swatch qb-legend-flagged">Flagged / Unverified</span>
</p>
<ul>
<li><strong>Examiner&rsquo;s Comment</strong> (tan/orange) is a <strong>real</strong> quote from ICAI&rsquo;s own published "Examiner&rsquo;s Comments on the Performance of the Examinees" &mdash; ICAI&rsquo;s own words.</li>
<li><strong>Author&rsquo;s Note</strong> (pale pink) is the author&rsquo;s own identification of a likely pitfall where no real ICAI comment exists for that question &mdash; informed guidance, not an official finding, and may not apply in every case.</li>
<li>A <strong>flagged</strong> card (reddish border) means one detail on that question has not been independently re-verified with full confidence.</li>
</ul>

<h3>What's on every card</h3>
<ul>
<li><strong>Source line</strong> &mdash; sitting, question number, and marks, so you know exactly which paper and how much it was worth.</li>
<li><strong>Topic tag</strong> &mdash; the exact sub-topic within the chapter, so you know precisely where to go back and re-read if a card doesn't ring a bell.</li>
<li><strong>Examiner's Comment / Author's Note</strong> &mdash; the one line of insight worth carrying into the exam hall.</li>
<li><strong>Student Self Notes</strong> &mdash; three blank lines (one more than the main book) for your own reminder on this specific question.</li>
<li><strong>My NB Page No / My Tag / Revision Phase</strong> &mdash; identical to the main book: where you worked this by hand, your own freeform triage word, and three tick-boxes for successive revision passes.</li>
</ul>

<h3>Topic-wise Marks Mapping</h3>
<p>Every chapter opens with the same Topic-wise Marks Mapping table as the main book &mdash; which sub-topic was tested for how many marks, in which sitting, split by MTP / PYQ / RTP. Read this first: it tells you which part of the chapter to revise hardest.</p>

<h3>Sanjeevani Booti &mdash; the Error Register (one page per chapter, this time)</h3>
<p>Unlike the main book's single shared register at the back, Amritras gives each chapter its <strong>own</strong> one-page register &mdash; "Concepts I Forgot" and "Mistakes I Repeated More Than Twice" &mdash; right after that chapter's cards, so you log a mistake the moment it happens while revising that chapter, not thirty chapters later.</p>
</div>
"""


def build_front_matter_body() -> str:
    pages = [
        ("am-title", build_title_page()),
        ("am-copyright", build_copyright_page()),
        ("am-howto", build_howto_page()),
        ("am-stats", build_stats_page_reused()),
    ]
    return "\n".join(f'<div class="qb-section" id="{slug}">\n{content}\n</div>' for slug, content in pages)


def build_stats_page_reused() -> str:
    # "Book Coverage at a Glance" -- Pranav's instruction: identical to the
    # main book, all sittings included. Reused directly from the main
    # book's own generator (same book_stats.json, same page) rather than
    # re-derived, so the two books can never show different totals.
    import generate_qb_front_back_matter as fbm
    return fbm.build_stats_page()


# ═══════════════════════════════════════════════════════════════════════
# Table of Contents -- same chapter order/labels/study-refs as the main
# book (qb_merge.CHAPTERS, imported), page numbers filled in by the
# headless-Chrome resolve pass below (blank on the first merge pass).
# ═══════════════════════════════════════════════════════════════════════
def build_toc_rows(page_numbers: dict = None) -> str:
    rows = []
    for idx, (slug, _filename, label, study_ref) in enumerate(CHAPTERS, start=1):
        page_text = (page_numbers or {}).get(slug, "")
        rows.append(
            f'<div class="qb-toc-entry">'
            f'<span class="qb-toc-num">{idx}.</span>'
            f'<a href="#{slug}">{label}</a>'
            f'<span class="qb-toc-ref">{study_ref}</span>'
            f'<span class="qb-toc-leader"></span>'
            f'<span class="qb-toc-page" data-target-id="{slug}">{page_text}</span>'
            f'</div>'
        )
    return "\n".join(rows)


def build_toc_body(page_numbers: dict = None) -> str:
    return f"""<div class="qb-section" id="am-toc">
<h2 class="qb-page-title">Table of Contents</h2>
<div class="qb-toc-list" id="qb-toc-list">
{build_toc_rows(page_numbers)}
</div>
</div>"""


# ═══════════════════════════════════════════════════════════════════════
# Per-chapter condensed content
# ═══════════════════════════════════════════════════════════════════════
BRAND_HEADER = """<div class="brand-header">
<strong>Pranav Bhaiya</strong> &middot; The Newton of Accounts &middot; AIR 1-1-5<br>
Kahaan &middot; Koncept &middot; Karma &nbsp;&mdash;&nbsp; Always Focus on Karma, Not Results
</div>"""


def brand_footer(standard_label: str, chapter_title: str) -> str:
    return f"""<div class="brand-footer">
#KeepLearning #DreamBig &nbsp;&middot;&nbsp; #LoveWhatYouDo<br>
<strong>{standard_label} — {chapter_title}</strong>
</div>"""


def mistake_box_html(row: dict) -> str:
    ec = row.get("examiner_comment")
    if not (ec and ec.get("text")):
        return '<p class="na" style="margin:8px 0;">No Examiner&rsquo;s Comment / Author&rsquo;s Note recorded for this question.</p>'
    if ec.get("comment_source") == "icai":
        label, cls = "Examiner&rsquo;s Comment", "mistakes icai"
    else:
        label, cls = "Author&rsquo;s Note", "mistakes synth"
    return f'<div class="{cls}"><strong>{label}:</strong> {html_lib.escape(ec["text"])}</div>'


def render_mini_card(row: dict, idx: int, slug_id: str) -> str:
    flagged = row.get("review_status") not in ("verified", None) or row.get("issue")
    cls = "qblock flagged" if flagged else "qblock"
    return f"""
<div class="{cls}" id="{slug_id}-{idx:03d}">
  <div class="qmeta">
    <span class="src">{html_lib.escape(gcb.paper_label(row))}</span> &middot;
    <span class="qno">{html_lib.escape(gcb.qno_label(row))}</span> &middot;
    <span class="marks">Marks: {gcb.marks_span(row)}</span> &middot;
    <span class="topic">{gcb.topic_label(row)}</span>
  </div>
  {mistake_box_html(row)}
  <div class="self-notes"><strong>Student Self Notes:</strong>
    <div class="notes-lines"><div class="dotted-line"></div><div class="dotted-line"></div><div class="dotted-line"></div></div>
  </div>
  <div class="student-fields">
    <span>My NB Page No <span class="fill-blank fill-blank-sm">&nbsp;</span></span>
    <span>My Tag <span class="fill-blank">&nbsp;</span></span>
    <span>Revision Phase <span class="box"></span>1 <span class="box"></span>2 <span class="box"></span>3</span>
  </div>
</div>
"""


def render_section(rows: list, heading: str, slug_id: str, idx_counter: list) -> str:
    if not rows:
        return ""
    cards = []
    for r in rows:
        idx_counter[0] += 1
        cards.append(render_mini_card(r, idx_counter[0], slug_id))
    return f"<h2>{heading}</h2>\n" + "\n".join(cards)


def build_chapter_body(fc: str, standard_label: str, chapter_title: str,
                        home: list, descriptive: list, integrated: list, slug_id: str) -> str:
    idx_counter = [0]
    descriptive_html = render_section(
        descriptive, f"I. Descriptive &amp; Scenario-Based Questions (pure {standard_label})", slug_id, idx_counter
    )
    integrated_html = render_section(
        integrated, f"II. Integrated Questions ({standard_label} with Other Standards)", slug_id, idx_counter
    )
    topic_summary_html = gcb.build_topic_summary(fc, home, standard_label)
    total_shown = len(descriptive) + len(integrated)

    return f"""
{BRAND_HEADER}
<h1>{standard_label} — {chapter_title}</h1>
<p class="section-intro">Amritras summary &mdash; {total_shown} question reference(s) from every MTP/RTP/PYQ sitting testing this chapter. {VCGURUKUL_LINE}</p>
{topic_summary_html}
{descriptive_html}
{integrated_html}
{brand_footer(standard_label, chapter_title)}
"""


def build_error_register_page(slug_id: str, chapter_label: str) -> str:
    def rows(n):
        row = (
            '<tr><td class="qb-er-note"><span class="qb-er-blank qb-er-blank-wide"></span></td>'
            '<td class="qb-er-check"><span class="qb-er-box"></span></td></tr>'
        )
        return row * n

    return f"""<div class="qb-section amritras-er-page" id="{slug_id}-er">
  <div class="qb-running-header">
    <span>{AMRITRAS_BOOK_TITLE}</span>
    <span class="qb-chapter">{chapter_label} &mdash; Error Register</span>
  </div>
  <div class="qb-running-footer"></div>
  <div class="qb-er-page">
  <h2 class="qb-page-title">Sanjeevani Booti &mdash; Error Register: {chapter_label}</h2>
  <p class="qb-matrix-note">One page, this chapter only &mdash; log what you forgot or got wrong while revising {chapter_label}, then tick Revised once you've fixed it.</p>
  <h3 style="font-family:var(--qb-heading-font);font-size:10.5pt;font-weight:700;color:var(--qb-accent);margin:5mm 0 2mm;">Concepts I Forgot</h3>
  <table class="qb-er-table"><thead><tr><th>Note</th><th>Revised</th></tr></thead><tbody>{rows(6)}</tbody></table>
  <h3 style="font-family:var(--qb-heading-font);font-size:10.5pt;font-weight:700;color:var(--qb-accent);margin:6mm 0 2mm;">Mistakes I Repeated More Than Twice</h3>
  <table class="qb-er-table"><thead><tr><th>Note</th><th>Revised</th></tr></thead><tbody>{rows(6)}</tbody></table>
  </div>
</div>"""


def build_chapter_section(slug_id: str, chapter_label: str, study_ref: str, chapter_body_inner: str) -> str:
    # Reuses qc.page_shell() itself (not a hand-rewritten copy of it) by
    # wrapping the fresh body content in a throwaway <html><body> shell --
    # page_shell()'s own id-rewrite regex only matches the main book's
    # id="AS02-NNN" bug pattern, which these freshly-generated ids never
    # produce, so it's a safe no-op here. This guarantees the running-
    # header/footer/study-ref-banner markup can never drift from the main
    # book's own shell, then the one hardcoded qc.BOOK_TITLE occurrence is
    # swapped for this book's own title.
    shell = qc.page_shell(f"<html><body>{chapter_body_inner}</body></html>", slug_id, chapter_label, study_ref)
    return shell.replace(f"<span>{qc.BOOK_TITLE}</span>", f"<span>{AMRITRAS_BOOK_TITLE}</span>", 1)


# ═══════════════════════════════════════════════════════════════════════
# Back matter
# ═══════════════════════════════════════════════════════════════════════
def build_back_matter_body() -> str:
    about_author = f"""
<h2 class="qb-page-title">About the Author</h2>
<div class="qb-bio">
<p>CA Pranav Pratik Tulshyan holds All India Rank 1 in both Foundation (188/200, January 2015) and Intermediate (544/700, February 2016): the only student in the 70-year history of ICAI to achieve this from outside India, across both examinations. He holds AIR 5 in CA Finals. He completed his articleship at Ernst &amp; Young, Gurgaon, and has worked across IOCL and the Ministry of Petroleum and Natural Gas, Government of India. He now teaches CA Inter Accounts at VC Gurukul, Noida.</p>
<p>This Amritras was built the same way his Advanced Accounts classes are taught: every question placed exactly where it belongs, nothing left to guesswork about what's actually been examined.</p>
</div>
"""
    closing = f"""
<h2 class="qb-page-title">A Closing Note</h2>
<div class="qb-bio">
<p>This is the first edition of this Amritras &mdash; the distilled companion to the full Question Bank Book, meant for the final stretch before your exam, when you need the coordinates of every question and its one key insight, not the whole worked solution again.</p>
<p>{VCGURUKUL_LINE} If you found an error, or a question that's misfiled, or a topic tag that looks wrong, the single most useful thing you can do is email <strong>{qc.ERROR_REPORT_EMAIL}</strong> with the question reference.</p>
<p>Good luck with your attempt.</p>
</div>
"""
    pages = [("am-author", about_author), ("am-closing", closing)]
    return "\n".join(f'<div class="qb-section" id="{slug}">\n{content}\n</div>' for slug, content in pages)


# ═══════════════════════════════════════════════════════════════════════
# Merge
# ═══════════════════════════════════════════════════════════════════════
def build_merged_html(sections_html: list, style: dict) -> str:
    fonts_css = (OUTPUT_DIR / "vendor" / "gfonts-local.css").read_text(encoding="utf-8")
    fonts_css = fonts_css.replace("url(fonts/", "url(vendor/fonts/")
    full_style = (
        fonts_css
        + gcb.STYLE               # the same Arial-based shared chapter stylesheet the main book uses
        + qc.print_layer_css(style)
        + qc.front_back_css(style)
    )
    body = "\n\n".join(sections_html)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{AMRITRAS_BOOK_TITLE}</title>
  <style>{full_style}</style>
</head>
<body>
{body}
<script src="vendor/paged.polyfill.js"></script>
</body>
</html>"""


def resolve_page_numbers_for_file(path: Path, target_ids: list) -> dict:
    """Real page numbers via a real headless-Chrome pagination pass -- same
    mechanism as resolve_qb_toc_pages.py (imported, not reimplemented):
    target-counter() is confirmed broken in this vendored paged.js, the
    working path is reading paged.js's own data-page-number stamp per
    physical page."""
    import resolve_qb_toc_pages as rtp
    chrome_path = rtp.find_chrome()
    user_data_dir = Path(r"C:\temp\resolve-amritras-toc-chrome-profile")
    proc = rtp.launch_chrome(chrome_path, user_data_dir)
    try:
        file_url = "file:///" + str(path.resolve()).replace("\\", "/")
        cdp = rtp.CDP(file_url)
        try:
            n_pages = rtp.wait_for_stable_pagination(cdp)
            print(f"Pagination stable at {n_pages} pages.")
            return rtp.resolve_page_numbers(cdp, target_ids)
        finally:
            cdp.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-resolve", action="store_true",
                     help="Skip the headless-Chrome ToC page-number pass.")
    args = ap.parse_args()

    style = qc.load_book_style()

    print("Regenerating chapter-coverage-matrix.html (fresh, shared with the main book)...")
    import generate_qb_coverage_matrix as cm
    cm.main()

    print("Loading questions_index.json...")
    data = gcb.load_index()
    fc_lookup = build_fc_lookup(data)

    print("Building front matter...")
    front_body = build_front_matter_body()
    (OUTPUT_DIR / "amritras-front-matter.html").write_text(
        qc.wrap_page(f"Front Matter: {AMRITRAS_BOOK_TITLE}", front_body, style), encoding="utf-8"
    )

    print("Loading coverage matrix (reused from the main book, unchanged)...")
    coverage_body = qc.extract_body_inner(qc.load_chapter_html("chapter-coverage-matrix.html"))

    print(f"Building {len(CHAPTERS)} condensed chapters + error registers...")
    chapter_sections = []
    for slug_id, filename, chapter_label, study_ref in CHAPTERS:
        fc, standard_label, chapter_title = fc_lookup[filename]
        home, descriptive, integrated = gcb.select_chapter_rows(data, fc)
        chapter_body_inner = build_chapter_body(fc, standard_label, chapter_title, home, descriptive, integrated, slug_id)
        chapter_sections.append(build_chapter_section(slug_id, chapter_label, study_ref, chapter_body_inner))
        chapter_sections.append(build_error_register_page(slug_id, chapter_label))
        print(f"  {slug_id:28s} descriptive={len(descriptive):3d}  integrated={len(integrated):3d}")

    print("Building back matter...")
    back_body = build_back_matter_body()
    (OUTPUT_DIR / "amritras-back-matter.html").write_text(
        qc.wrap_page(f"Back Matter: {AMRITRAS_BOOK_TITLE}", back_body, style), encoding="utf-8"
    )

    print("Building Table of Contents (pass 1, blank page numbers)...")
    toc_body = build_toc_body(None)
    (OUTPUT_DIR / "amritras-table-of-contents.html").write_text(
        qc.wrap_page(f"Table of Contents: {AMRITRAS_BOOK_TITLE}", toc_body, style), encoding="utf-8"
    )

    sections = [front_body, toc_body, coverage_body] + chapter_sections + [back_body]
    out_path = OUTPUT_DIR / OUT_FILENAME
    out_path.write_text(build_merged_html(sections, style), encoding="utf-8")
    print(f"Wrote {out_path} (pass 1, blank ToC page numbers)")

    if args.no_resolve:
        print("Skipping ToC page-number resolution (--no-resolve).")
        return

    print("Resolving real ToC page numbers via headless Chrome...")
    try:
        page_numbers = resolve_page_numbers_for_file(out_path, [c[0] for c in CHAPTERS])
    except SystemExit as e:
        print(f"WARNING: page-number resolution failed ({e}). ToC page numbers left blank; "
              f"re-run this script (or the resolve step) once Chrome/Edge is available.")
        return

    toc_body_final = build_toc_body(page_numbers)
    (OUTPUT_DIR / "amritras-table-of-contents.html").write_text(
        qc.wrap_page(f"Table of Contents: {AMRITRAS_BOOK_TITLE}", toc_body_final, style), encoding="utf-8"
    )
    sections[1] = toc_body_final
    out_path.write_text(build_merged_html(sections, style), encoding="utf-8")
    print(f"Wrote {out_path} (pass 2, real ToC page numbers baked in)")


if __name__ == "__main__":
    main()
