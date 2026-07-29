#!/usr/bin/env python3
"""
generate_qb_front_back_matter.py -- writes front-matter.html and
back-matter.html for the Question Bank Book into first_run/output/.

These are real, standalone HTML files (own <head>/<style>/<body>) so they
can be opened and reviewed individually, exactly like the 34 chapter files
they'll eventually merge alongside -- qb_merge.py reads them the same way
it reads a chapter file (extract style, extract body, wrap in a
.qb-section). They are NOT expected to have the same embedded <style> as
the 34 chapter files (front/back matter needs title-page/copyright-page/
author-bio layouts the chapters never use) -- qb_merge.py's CSS-consistency
check treats front-matter as the reference file precisely because it's the
richest superset, same pattern used on the strategy book (front-matter.html
there also supplied the merged book's shared stylesheet for the same reason).

Facts used in the author bio are the same ones already verified and used in
the strategy book's front matter (same person, same institute) -- not
invented here.
"""

import json
from pathlib import Path
import qb_common as qc

OUTPUT_DIR = qc.OUTPUT_DIR
STYLE = qc.load_book_style()
TYP = STYLE["typography"]
COL = STYLE["colors"]

STATS_PATH = qc.CHAPTERS_DIR / "book_stats.json"

# Front/back-matter-only CSS (title page, copyright page, dedication,
# author bio) now lives in qb_common.front_back_css() so qb_merge.py can
# reuse the exact same rules for the final merged book -- never hand-
# duplicated here. (ToC's own CSS -- .qb-toc-entry etc. -- also lives there,
# but the ToC page itself moved to its own file, generate_qb_toc.py,
# 2026-07-27, per Pranav's request to stop embedding it inside front matter.)
FRONT_BACK_CSS = qc.front_back_css(STYLE)


def wrap_page(title: str, body: str) -> str:
    return qc.wrap_page(title, body, STYLE)


def load_stats() -> dict:
    if not STATS_PATH.exists():
        raise SystemExit(
            f"ERROR: {STATS_PATH} not found -- run generate_book_stats.py "
            "before generate_qb_front_back_matter.py (the front matter now "
            "includes a Book Coverage page built from that file)."
        )
    with STATS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def build_stats_page() -> str:
    """'Book Coverage at a Glance' -- every number here is read straight
    from book_stats.json (itself computed by generate_book_stats.py from
    questions_index.json, no hand-typed figures anywhere in the chain), so
    this page never drifts out of sync with the actual corpus: re-run
    generate_book_stats.py then this script and the page updates itself."""
    stats = load_stats()
    q = stats["questions"]
    m = stats["marks"]
    s = stats["sittings"]
    mn = stats["mistake_notes"]

    sittings_list_html = "".join(f"<li>{label}</li>" for label in s["list"])

    tiles = [
        (str(s["count"]), "Sittings Covered"),
        (str(q["distinct_question_numbers_as_printed"]), "Distinct Questions"),
        (str(q["total_records_including_parts_and_subparts"]), "Question Records<br>(incl. split parts)"),
        (f"{stats['chapters_touched_count']} / 36", "Chapters Touched"),
        (str(m["total_marks_covered_book_wide"]), "Total Marks Covered"),
        (str(mn["real_icai_examiner_comments"]), "Real ICAI<br>Examiner's Comments"),
    ]
    tiles_html = "".join(
        f'<div class="qb-stat-tile"><span class="qb-stat-num">{num}</span>'
        f'<span class="qb-stat-label">{label}</span></div>'
        for num, label in tiles
    )

    return f"""
<h2 class="qb-page-title">Book Coverage at a Glance</h2>
<div class="qb-howto">
<p>This page is generated directly from the book's own question index &mdash;
every number below updates automatically as new sittings are added to a
future edition, never hand-typed.</p>

<div class="qb-stats-grid">{tiles_html}</div>

<h3>Sittings in this edition</h3>
<ul class="qb-stats-sittings">{sittings_list_html}</ul>

<h3>A few honest notes on these numbers</h3>
<ul>
<li>Each MTP/PYQ sitting's questions sum to 114 marks, not the paper's nominal
100 &mdash; Part II offers &ldquo;answer any N of the remaining M&rdquo;, and
this book deliberately includes every optional question shown so you can
practise all of them, not only the subset one particular sitting required.</li>
<li>RTP sittings contribute 0 marks to the total above &mdash; ICAI's own RTP
documents are published without a marks-weighted answer key, not a gap in
this book's tagging.</li>
<li>{mn["author_synthesized_notes"]} of this edition's Common-Student-Mistakes
notes are the author's own synthesized guidance (clearly labelled
&ldquo;Author's Note&rdquo; wherever they appear), because a real ICAI
Examiner's Comment document doesn't exist for every sitting yet.</li>
</ul>
</div>
"""


def build_front_matter() -> str:
    title_page = f"""
<div class="qb-title-page">
  <div><p class="qb-tp-series">CA Intermediate &middot; Advanced Accounts</p></div>
  <div>
    <h1 class="qb-tp-title">The Complete<br>Question Bank</h1>
    <p class="qb-tp-subtitle">Every MTP, RTP, and PYQ question, mapped to its exact chapter and topic</p>
    <div class="qb-tp-rule"></div>
    <p class="qb-tp-author">CA Pranav Pratik Tulshyan</p>
    <p class="qb-tp-credential">AIR 1 (Foundation) &middot; AIR 1 (Intermediate)</p>
  </div>
  <div><p class="qb-tp-publisher">VC Gurukul &middot; Noida</p></div>
</div>
"""

    copyright_page = f"""
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

    dedication_page = """
<div class="qb-dedication-block">
  <span class="qb-ded-to">Dedicated To</span>

  <span class="qb-ded-name">Sunita Tulshyan &amp; Sunil Tulshyan</span>
  <span class="qb-ded-role">Mother &amp; Father</span>
  <span class="qb-ded-note">of whose creation I am, and under whose blessings all my actions are always guided.</span>

  <span class="qb-ded-sep">&middot; &middot; &middot;</span>

  <span class="qb-ded-name">Marvel Tulshyan</span>
  <span class="qb-ded-role">Sister</span>
  <span class="qb-ded-note">who studied CA Inter alongside me, helped me navigate the tough terrain, and was my emotional support at home.</span>

  <span class="qb-ded-sep">&middot; &middot; &middot;</span>

  <span class="qb-ded-name">CA Deepak Pandey</span>
  <span class="qb-ded-role">Managing Director, AOC Nepal (My Inspiration)</span>
  <span class="qb-ded-note">who taught me to dream big.</span>

  <span class="qb-ded-sep">&middot; &middot; &middot;</span>

  <span class="qb-ded-name">CA Mukul Bhatt</span>
  <span class="qb-ded-role">Accounts Teacher, CA Foundation &amp; Intermediate</span>
  <span class="qb-ded-note">who first showed me what accounts could be.</span>

  <span class="qb-ded-sep">&middot; &middot; &middot;</span>

  <span class="qb-ded-name">CA Praveen Sharma</span>
  <span class="qb-ded-role">The God of Accounting (My Idol)</span>
  <span class="qb-ded-note">whom I have always admired as a teacher, and whose standard I aspire to.</span>

  <span class="qb-ded-sep">&middot; &middot; &middot;</span>

  <span class="qb-ded-name">CA Gurpreet Singh &amp; Rahul Bhutani</span>
  <span class="qb-ded-role">Friends &amp; Guides</span>
  <span class="qb-ded-note">who gave me the opportunity to teach the CA fraternity's students, and guided me on my teaching journey.</span>

  <span class="qb-ded-close">A combined effort of all of the above has made this possible.</span>
</div>
"""

    howto_page = f"""
<h2 class="qb-page-title">How to Read This Book</h2>
<div class="qb-howto">
<p>This is a chapter-wise Question Bank: every MTP, RTP, and PYQ descriptive/scenario question that has tested a chapter, collected in one place with the official answer. <strong>MCQs are deliberately not included</strong> &mdash; practise those on the dedicated MCQ platform; this book is for descriptive/scenario practice with full worked solutions.</p>

<h3>Colour key</h3>
<p>
<span class="qb-legend-swatch qb-legend-answer">Answer / Solution</span>
<span class="qb-legend-swatch qb-legend-case">Case Scenario</span>
<span class="qb-legend-swatch qb-legend-examiner">Examiner&rsquo;s Comment</span>
<span class="qb-legend-swatch qb-legend-author">Author&rsquo;s Note</span>
<span class="qb-legend-swatch qb-legend-flagged">Flagged / Unverified</span>
</p>
<ul>
<li><strong>Examiner&rsquo;s Comment</strong> (tan/orange) is a <strong>real</strong> quote from ICAI&rsquo;s own published "Examiner&rsquo;s Comments on the Performance of the Examinees" &mdash; when you see this colour, it is ICAI&rsquo;s own words.</li>
<li><strong>Author&rsquo;s Note</strong> (pale pink) is the author&rsquo;s own identification of a likely pitfall where no real ICAI comment exists for that question &mdash; informed guidance, not an official finding, and may not apply in every case.</li>
<li>A <strong>flagged</strong> card (reddish border) means one detail on that question has not been independently re-verified with full confidence &mdash; still usable for practice, just read the answer a little more critically.</li>
</ul>

<h3>What's on every question card, and why</h3>
<ul>
<li><strong>Source line</strong> &mdash; paper, question number, marks, and <strong>Approx Time</strong> (marks &times; 1.8 minutes, rounded up; RTP questions with no stated marks show a 10&ndash;20 minute range) &mdash; pace your practice the way you'd have to on the real exam.</li>
<li><strong>Topic tag</strong> &mdash; just the topic number and its specific name (e.g. <em>Topic 2.7: Revaluation model for subsequent measurement</em>). You're already inside that chapter's own book, so the chapter name itself isn't repeated on every card &mdash; only the exact sub-topic, so you know precisely where to go back and re-read.</li>
<li><strong>Student Self Notes</strong> &mdash; a small blank box for your own two lines on this specific question.</li>
<li><strong>My NB Page No / My Tag / Revision Phase</strong> &mdash; one compact line under each answer. <strong>My NB Page No</strong> records the page in your own practice notebook where you worked this question by hand. <strong>My Tag</strong> is a freeform label of your own &mdash; try things like "Last-day Revision", "Not Important", "Easy", or "Must Practice" to triage your own revision; the box is intentionally blank so you choose the word. <strong>Revision Phase</strong> is three tick-boxes to mark off as you revisit a question in later revision passes.</li>
</ul>

<h3>"Sanjeevani Booti 2" &mdash; the Error Register (back of the book, not per chapter)</h3>
<p>Six blank, dotted-line pages (three double-sided sheets) at the back of the book &mdash; alternating <strong>Concepts I Forgot</strong> and <strong>Mistakes I Repeated More Than Twice</strong>, with a "Chapter / Topic" column so one shared register can hold entries from any chapter. Revision in the final weeks should mean re-reading <em>your own recorded mistakes</em>, not every question again. If six pages isn't enough, keep a separate notebook for the rest &mdash; the point is the habit, not fitting everything in this book.</p>

<h3>Coming in a future edition</h3>
<p>Two ideas are locked in but not yet built, named here honestly rather than pretended to exist: <strong>OP/PP tags</strong> (marking which sitting is the original version of a recurring question vs. a later practice repeat) and <strong>short chapter names</strong> in the topic tag for the handful of very long chapter titles.</p>
</div>
"""

    stats_page = build_stats_page()

    pages = [
        ('qb-title', 'Title Page', title_page),
        ('qb-copyright', 'Copyright & Disclaimers', copyright_page),
        ('qb-dedication', 'Dedication', dedication_page),
        ('qb-howto', 'How to Read This Book', howto_page),
        ('qb-stats', 'Book Coverage at a Glance', stats_page),
    ]
    body_parts = []
    for slug, _label, content in pages:
        body_parts.append(f'<div class="qb-section" id="{slug}">\n{content}\n</div>')
    return wrap_page("Front Matter: Question Bank Book", "\n".join(body_parts))


ERROR_REGISTER_SHEETS = 3  # -> 6 pages (front+back of each sheet)
ERROR_REGISTER_ROWS_PER_PAGE = 11


def build_error_register_pages() -> str:
    """'Sanjeevani Booti 2' -- ONE shared Error Register appendix at the
    back of the book (2026-07-28, Pranav's request), replacing the old
    design of a dedicated full page per chapter (34 pages total). A
    "Chapter / Topic" column lets one shared register hold entries from any
    chapter, so this costs a fixed 6 pages instead of scaling with chapter
    count. Alternates 'Concepts I Forgot' / 'Mistakes I Repeated More Than
    Twice' across 3 double-sided sheets, matching the original per-chapter
    page's own two-section split."""
    row = (
        '<tr><td class="qb-er-chapter"><span class="qb-er-blank"></span></td>'
        '<td class="qb-er-note"><span class="qb-er-blank qb-er-blank-wide"></span></td>'
        '<td class="qb-er-check"><span class="qb-er-box"></span></td></tr>'
    )
    rows_html = row * ERROR_REGISTER_ROWS_PER_PAGE

    pages = []
    total_pages = ERROR_REGISTER_SHEETS * 2
    for i in range(total_pages):
        section_title = "Concepts I Forgot" if i % 2 == 0 else "Mistakes I Repeated More Than Twice"
        pages.append(f"""
<div class="qb-section qb-er-page">
<h2 class="qb-page-title">Sanjeevani Booti 2: Error Register &mdash; {section_title}</h2>
<p class="qb-matrix-note">Sheet {i // 2 + 1} of {ERROR_REGISTER_SHEETS} &middot; use for any chapter &mdash; write which chapter/topic each entry is about.</p>
<table class="qb-er-table">
<thead><tr><th>Chapter / Topic</th><th>{section_title}</th><th>Revised</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>
""")
    return "\n".join(pages)


def build_back_matter() -> str:
    about_author = f"""
<h2 class="qb-page-title">About the Author</h2>
<div class="qb-bio">
<p>CA Pranav Pratik Tulshyan holds All India Rank 1 in both Foundation (188/200, January 2015) and Intermediate (544/700, February 2016): the only student in the 70-year history of ICAI to achieve this from outside India, across both examinations. He holds AIR 5 in CA Finals. He completed his articleship at Ernst &amp; Young, Gurgaon, and has worked across IOCL and the Ministry of Petroleum and Natural Gas, Government of India. He now teaches CA Inter Accounts at VC Gurukul, Noida.</p>
<p>This Question Bank was built the same way his Advanced Accounts classes are taught: every question placed exactly where it belongs, nothing left to guesswork about what's actually been examined.</p>
</div>
"""

    closing = f"""
<h2 class="qb-page-title">A Closing Note</h2>
<div class="qb-bio">
<p>This is the first edition of this book. It exists because ten sittings' worth of questions, scattered across separate PDFs, is a genuinely painful way to revise a chapter, and there was no reason that pain needed to stay.</p>
<p>It will get better with every edition; more sittings, more chapters fully cross-checked, corrections from students who actually use it in their revision. If you found an error, or a question that's misfiled, or a topic tag that looks wrong, the single most useful thing you can do is email <strong>{qc.ERROR_REPORT_EMAIL}</strong> with the question reference. It gets fixed, and the next student after you never hits it.</p>
<p>Good luck with your attempt.</p>
</div>
"""

    pages = [
        ('qb-author', 'About the Author', about_author),
        ('qb-closing', 'Closing Note', closing),
    ]
    body_parts = []
    for slug, _label, content in pages:
        body_parts.append(f'<div class="qb-section" id="{slug}">\n{content}\n</div>')
    # Error Register pages are already individually wrapped in .qb-section
    # (one per physical page) by build_error_register_pages() -- appended
    # directly, not double-wrapped.
    body_parts.append(build_error_register_pages())
    return wrap_page("Back Matter: Question Bank Book", "\n".join(body_parts))


def main():
    front = build_front_matter()
    back = build_back_matter()
    (OUTPUT_DIR / "front-matter.html").write_text(front, encoding="utf-8")
    (OUTPUT_DIR / "back-matter.html").write_text(back, encoding="utf-8")
    print(f"Written: {OUTPUT_DIR / 'front-matter.html'}")
    print(f"Written: {OUTPUT_DIR / 'back-matter.html'}")


if __name__ == "__main__":
    main()
