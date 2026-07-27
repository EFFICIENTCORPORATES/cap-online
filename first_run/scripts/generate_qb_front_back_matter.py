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

from pathlib import Path
import qb_common as qc

OUTPUT_DIR = qc.OUTPUT_DIR
STYLE = qc.load_book_style()
TYP = STYLE["typography"]
COL = STYLE["colors"]

# Front/back-matter-only CSS (title page, copyright page, ToC, author bio)
# now lives in qb_common.front_back_css() so qb_merge.py can reuse the exact
# same rules for the final merged book -- never hand-duplicated here.
FRONT_BACK_CSS = qc.front_back_css(STYLE)


def wrap_page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="vendor/gfonts-local.css">
<style>
*, *::before, *::after {{ box-sizing: border-box; }}
body {{ font-family: {TYP['body_font']}; color: {COL['ink']}; margin: 0; padding: 24px; max-width: 980px; margin-left: auto; margin-right: auto; }}
{qc.print_layer_css(STYLE)}
{FRONT_BACK_CSS}
</style>
</head>
<body>
{body}
</body>
</html>"""


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

    how_to_use = f"""
<h2 class="qb-page-title">How to Use This Book</h2>
<div class="qb-howto">
<p>This book collects every Advanced Accounts question from 10 recent ICAI sittings (MTP Jan 2026 Set 1 &amp; 2, MTP May 2026 Set 1 &amp; 2, PYQ Jan 2026, PYQ May 2026, PYQ Sep 2025, RTP Jan 2026, RTP May 2026, RTP Sep 2025), 275 questions in total, and organises them by chapter, in the same teaching sequence your classes follow, not by exam sitting. Instead of hunting through ten separate papers to find every question on AS 2, or Amalgamation, or Branch Accounting, you go to that one chapter here and every question that has ever tested it, across all ten sittings, is already in one place.</p>

<h3>Chapter order</h3>
<p>Chapters run in teaching sequence, the same order your classes cover them in, starting with the Framework and foundational standards and ending with Branch Accounting. Use the Table of Contents to jump straight to the chapter you're revising.</p>

<h3>Inside every chapter</h3>
<p>Each chapter is split into three sections:</p>
<ul>
  <li><strong>I. MCQs</strong>: standalone and case-scenario multiple choice questions.</li>
  <li><strong>II. Descriptive</strong>: full descriptive or scenario questions where this chapter is the only topic being tested.</li>
  <li><strong>III. Integrated</strong>: questions where this chapter's judgment is one part of a larger question that also tests another standard. An empty Section III is normal for many chapters, not a mistake; most multi-topic-looking questions are deliberately split so each topic gets its own clean entry in its own chapter, so genuinely combined questions are the rarer case.</li>
</ul>

<h3>What's attached to every question</h3>
<ul>
  <li><strong>Source and marks</strong>: exactly which sitting, question number, and mark weight it carried.</li>
  <li><strong>Topic tag</strong>: the specific syllabus sub-topic it maps to (e.g. "AS 2 (1.4)"), so you can cross-reference against your own notes or concept book.</li>
  <li><strong>Official answer</strong>: the ICAI Suggested Answer / Answer Key, verbatim.</li>
  <li><strong>A mistake note</strong>, labelled as one of two kinds:</li>
</ul>
<p>
  <span class="qb-legend-swatch qb-legend-examiner">Examiner's Comment</span> a real quote from ICAI's own published feedback on that sitting, where one exists.
</p>
<p>
  <span class="qb-legend-swatch qb-legend-author">Author's Note</span> the author's own identification of a likely pitfall, not an official ICAI finding, and may not apply in every case.
</p>
<p>The label on every note tells you which one you're reading. Never blurred.</p>

<h3>A first edition, said plainly</h3>
<p>This book was assembled with AI assistance from the source PDFs and reviewed carefully, but not independently audited question by question. If something looks wrong, a figure, an answer, a topic tag, please email <strong>{qc.ERROR_REPORT_EMAIL}</strong> with the question reference. It will be fixed in the next edition, and you'll have helped every student who uses this book after you.</p>
</div>
"""

    toc_page = """
<h2 class="qb-page-title">Table of Contents</h2>
<div class="qb-toc-list" id="qb-toc-list">
</div>
"""

    pages = [
        ('qb-title', 'Title Page', title_page),
        ('qb-copyright', 'Copyright & Disclaimers', copyright_page),
        ('qb-howto-page', 'How to Use This Book', how_to_use),
        ('qb-toc', 'Table of Contents', toc_page),
    ]
    body_parts = []
    for slug, _label, content in pages:
        body_parts.append(f'<div class="qb-section" id="{slug}">\n{content}\n</div>')
    return wrap_page("Front Matter: Question Bank Book", "\n".join(body_parts))


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
