"""
Layer 2 -> Layer 3: generate one chapter's Question Book HTML by querying
questions_index.json (built by extract_questions.py) for every question whose
data-final-chapter matches the target unit, plus (separately) any question that
touches the chapter as a secondary tag on a genuinely connected multi-topic question.

Quality bar: books/question-bank/metadata-index/AS10_Question_Book.html (hand-built
sample). Sections: I. Descriptive (pure chapter), II. Integrated (cross-standard,
connected questions only - see SKILL-question-bank-question-splitting.md). MCQs are
deliberately excluded from the book (2026-07-26 decision) - they still live in the
sitting HTML (Layer 1) and questions_index.json (Layer 2), just never rendered here.

Usage:  python generate_chapter_book.py <unitcode> <standard-label> <chapter-title> <output-filename>
Example: python generate_chapter_book.py M2-C5-U1 "AS 2" "Valuation of Inventories" AS02_Question_Book.html
"""
import json
import math
import os
import re
import sys
import html as html_lib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qb_common as qc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(HERE, "..", "output", "generated-from-script"))
INDEX_PATH = os.path.join(OUTPUT_DIR, "questions_index.json")

MONTH_NAMES = {"01": "January", "02": "February", "03": "March", "04": "April",
               "05": "May", "06": "June", "07": "July", "08": "August",
               "09": "September", "10": "October", "11": "November", "12": "December"}

ERROR_REPORT_EMAIL = "capranavpratiktulshyan@gmail.com"

STYLE = """
body{font-family:Arial,Helvetica,sans-serif;margin:24px;max-width:980px;margin-left:auto;margin-right:auto;color:#222;background:#fff;line-height:1.5;}
h1{font-size:24px;margin-bottom:4px;}
h2{font-size:19px;margin-top:44px;border-bottom:2px solid #333;padding-bottom:6px;}
.note{background:#fff8e1;border:1px solid #e0c46c;padding:12px 16px;border-radius:6px;font-size:13px;margin:16px 0;}
.empty-section{background:#f0f0f0;border:1px dashed #999;padding:12px 16px;border-radius:6px;font-size:13px;margin:16px 0;color:#555;font-style:italic;}
.section-intro{font-size:13.5px;color:#444;margin-top:-6px;}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:12.5px;}
th,td{border:1px solid #999;padding:5px 7px;text-align:left;vertical-align:top;}
th{background:#2c3e50;color:#fff;}
.qblock{border:1px solid #ccc;border-radius:8px;padding:14px 18px;margin:18px 0;background:#fdfdfd;}
.qblock.flagged{border-color:#d98a8a;background:#fffaf7;}
.qmeta{font-size:12px;color:#555;margin-bottom:10px;padding-bottom:8px;border-bottom:1px dashed #ccc;}
.qmeta .src{font-weight:bold;color:#2c3e50;}
.qmeta .marks{font-weight:bold;}
.badge{display:inline-block;background:#fff3e0;border:1px solid #e0b46c;border-radius:10px;padding:1px 8px;font-size:11px;margin-left:6px;}
.badge.icai{background:#e0f0ff;border-color:#6ca8e0;}
.question{margin:10px 0;}
.answer-block{margin:10px 0;background:#eafbea;padding:8px 12px;border-radius:6px;}
.case-facts{background:#f5f5fb;border-left:3px solid #8888c0;padding:6px 12px;margin-bottom:8px;font-size:13px;}
.mistakes{margin:10px 0;padding:8px 12px;border-radius:6px;font-size:13.5px;border-left:3px solid #999;}
.mistakes.icai{background:#fff3e0;border-left-color:#e0b46c;color:#5a3d0a;}
.mistakes.synth{background:#fdf1f1;border-left-color:#d98a8a;color:#7a2f2f;}
.mistakes .prov{font-style:italic;color:#666;font-size:11.5px;display:block;margin-top:4px;}
.na{color:#999;font-style:italic;}
.self-notes{margin-top:8px;border:1px solid #ccc;background:#fff;border-radius:6px;padding:8px 12px;}
.self-notes .notes-lines{margin-top:4px;}
.self-notes .dotted-line{height:22px;border-bottom:1px dotted rgba(0,0,0,0.4);}
.student-fields{margin-top:8px;font-size:12px;color:#444;border-top:1px dashed #ccc;padding-top:6px;display:flex;flex-wrap:wrap;gap:14px;align-items:center;}
.student-fields .fill-blank{border-bottom:1px dotted #999;display:inline-block;min-width:120px;}
.student-fields .fill-blank-sm{min-width:60px;}
.student-fields .box{display:inline-block;border:1px solid #888;width:11px;height:11px;margin:0 2px 0 6px;vertical-align:middle;}
.brand-header{text-align:center;font-size:11px;color:#777;border-bottom:1px solid #eee;padding-bottom:8px;margin-bottom:18px;letter-spacing:.3px;}
.brand-header strong{color:#2c3e50;}
.brand-footer{text-align:center;font-size:11px;color:#777;border-top:1px solid #eee;padding-top:10px;margin-top:36px;line-height:1.8;}
.brand-footer strong{color:#2c3e50;}
.topic-summary{margin:18px 0 30px;}
.topic-summary h3{font-size:16px;margin-bottom:2px;color:#2c3e50;}
.topic-summary-table{font-size:11px;}
.topic-summary-table th{background:#445566;}
.topic-summary-table td.tsc{text-align:left;font-weight:600;}
.topic-summary-table td.tst{font-weight:700;background:#fdf6e3;}
.topic-summary-table td.tsz{color:#bbb;}
"""


def load_index():
    with open(INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)


def paper_label(row):
    ptype = row.get("paper_type") or ""
    month = MONTH_NAMES.get(row.get("exam_month"), row.get("exam_month") or "")
    year = row.get("exam_year") or ""
    label = f"{ptype} {month} {year}".strip()
    if row.get("set"):
        label += f" Set {row['set']}"
    return label


def qno_label(row):
    if row.get("parent_qno") and row.get("subpart"):
        base = f"Q{row['parent_qno']}({row['subpart']})"
    elif row.get("subpart"):
        base = f"Q{row.get('qno','')}({row['subpart']})"
    else:
        base = f"Q{row.get('qno','')}"
    if row.get("alt_group"):
        base += f" [OR-alt {row.get('alt')}]"
    return base


def marks_span(row):
    if row.get("marks") is None:
        return '<span class="na">Not stated in source</span>'
    return str(row["marks"])


def approx_time_label(row):
    marks = row.get("marks")
    if marks is None:
        return "10&ndash;20 minutes (approx.)"
    minutes = math.ceil(marks * 1.8)
    return f"{minutes} minutes (approx.)"


def topic_full_label(t):
    """Compact per-question topic reference. Used to say just 'AS 2 -- AS 2 --
    Valuation of Inventories' on every single question -- the chapter is
    already named in this file's own title and the ToC, so repeating it here
    was pure redundancy (Pranav, 2026-07-28). Now shows only the topic
    number + its specific abbreviated/authored name, via
    qb_common.abbreviated_topic_label() (file 1's topic_name_abbvtd where the
    ref matches its topic_no scheme, else the per-question data-subtopictitle
    -- never the chapter-level data-title, which is what caused this to
    look redundant in the first place)."""
    subref = str(t.get("subtopicref") or "")
    label = qc.abbreviated_topic_label(t.get("unitcode"), subref, t.get("subtopictitle"))
    if label:
        return f'Topic {html_lib.escape(subref)}: {html_lib.escape(label)}' if subref else html_lib.escape(label)
    if subref:
        return f'Topic {html_lib.escape(subref)}'
    return ""


def topic_label(row):
    if not row.get("topics"):
        return ""
    return "  &nbsp;+&nbsp;  ".join(topic_full_label(t) for t in row["topics"])


def _ref_sort_key(ref):
    """Sort subtopic refs numerically ('2.10' after '2.9', not before) by
    extracting every digit run -- a plain string sort would put '2.10'
    before '2.9'. Refs with no digits (or missing) sort last."""
    nums = [int(p) for p in re.findall(r"\d+", ref or "")]
    return (0, nums) if nums else (1, [])


def subtopic_key(row, unitcode):
    """Which of THIS chapter's subtopics a row belongs to, for the
    Topic-wise Marks Mapping table -- uses only topic-tag(s) whose own
    data-unitcode matches this chapter (a connected multi-topic question's
    OTHER tagged standards are irrelevant here). Falls back to a single
    'General' bucket if the row has no subtopicref recorded for this
    chapter (should be rare post-tagging, not an error).

    Label uses qc.abbreviated_topic_label() (topic_name_abbvtd or
    data-subtopictitle), NEVER the chapter-level data-title -- using
    data-title here was the exact bug found 2026-07-28 (every row in a
    chapter's table showed the same chapter name repeated; see
    project_log.md's "real bug" entry for the full diagnosis)."""
    matches = [t for t in row.get("topics", []) if t.get("unitcode") == unitcode]
    if not matches:
        return ("", "General / not sub-tagged")
    t = matches[0]
    ref = t.get("subtopicref") or ""
    label = qc.abbreviated_topic_label(unitcode, ref, t.get("subtopictitle"))
    if not label:
        label = html_lib.escape(t.get("title") or "General")
    else:
        label = html_lib.escape(label)
    display = f"{html_lib.escape(ref)} &mdash; {label}" if ref else label
    return (ref, display)


def _topic_subtable(paper_type, sessions, ordered_buckets, is_marks):
    """One MTP/PYQ/RTP mini-table (topic rows x that paper type's sessions
    + Total) for build_topic_summary(). Split out per paper type for the
    identical reason generate_qb_coverage_matrix.py splits the whole-book
    matrix into 3 pages: a busy chapter (e.g. AS 2) can appear in nearly
    every one of the 34 sittings, so even ONE chapter's combined MTP+PYQ+RTP
    session list can run past 20 columns -- the exact print-width problem
    this whole design exists to avoid, just rediscovered one level deeper
    than expected (found 2026-07-28 while reviewing AS02's first combined-
    table draft: 22 columns). Splitting by paper type keeps each table to
    at most ~9 session columns, matching the whole-book page split."""
    if not sessions:
        return ""
    header_cells = "".join(f"<th>{qc.session_label(y, m)}</th>" for (y, m) in sessions)
    rows_html = []
    for (_ref, label), bucket_rows in ordered_buckets:
        cells = []
        total = 0
        for (y, m) in sessions:
            cell_rows = [
                r for r in bucket_rows
                if r.get("paper_type") == paper_type and r.get("exam_year") == y and r.get("exam_month") == m
            ]
            v = qc.dedup_marks_sum(cell_rows) if is_marks else qc.dedup_count(cell_rows)
            total += v
            cls = ' class="tsz"' if v == 0 else ""
            cells.append(f"<td{cls}>{v if v else '&ndash;'}</td>")
        if total == 0:
            continue  # this topic has no presence in this paper type -- skip the row, not a blank one
        rows_html.append(f'<tr><td class="tsc">{label}</td>{"".join(cells)}<td class="tst">{total}</td></tr>')
    if not rows_html:
        return ""
    unit_label = "Marks" if is_marks else "Count"
    return f"""
<p class="section-intro" style="margin-top:10px;"><strong>{paper_type}</strong> ({unit_label}{'; RTP publishes no marks key, so this is question count, not marks' if not is_marks else ''}):</p>
<table class="topic-summary-table">
<thead><tr><th>Topic</th>{header_cells}<th>Total</th></tr></thead>
<tbody>{"".join(rows_html)}</tbody>
</table>
"""


def build_topic_summary(unitcode, home_rows, standard_label):
    """'Topic-wise Marks Mapping' -- which subtopic of this chapter was
    tested for how many marks, in which sitting. Pranav's request
    (2026-07-28): lets a student see which PART of a chapter matters most,
    the same idea as the whole-book Chapter-wise Sitting Summary
    (generate_qb_coverage_matrix.py) one level deeper. Uses `home_rows`
    (every qtype, including MCQs excluded from the printed book below) so
    the marks signal reflects true exam importance, not just what's
    rendered on the page.

    Split into up to 3 mini-tables (MTP/PYQ marks, RTP count) -- see
    _topic_subtable()'s docstring for why a single combined table doesn't
    work even at chapter scale for a busy chapter."""
    if not home_rows:
        return ""

    buckets = {}
    for r in home_rows:
        key = subtopic_key(r, unitcode)
        buckets.setdefault(key, []).append(r)
    ordered_buckets = sorted(buckets.items(), key=lambda kv: _ref_sort_key(kv[0][0]))

    subtables = "".join(
        _topic_subtable(pt, qc.sessions_for(home_rows, pt), ordered_buckets, is_marks=(pt != "RTP"))
        for pt in ("MTP", "PYQ", "RTP")
    )
    if not subtables:
        return ""

    return f"""
<div class="topic-summary">
<h3>Topic-wise Marks Mapping &mdash; {standard_label}</h3>
<p class="section-intro">Which topic of the study material was tested for how many marks, in which sitting &mdash; use this to see which parts of {standard_label} matter most.</p>
{subtables}
</div>
"""


def render_qblock(row, idx, chapter_slug):
    flagged = row.get("review_status") not in ("verified", None) or row.get("issue")
    cls = "qblock flagged" if flagged else "qblock"

    question_html = ""
    if row.get("case_facts_html"):
        question_html += f'<div class="case-facts"><strong>Case Scenario:</strong> {row["case_facts_html"]}</div>'
    question_html += row["question_html"]

    badges = ""
    if row.get("compulsory"):
        badges += '<span class="badge">Compulsory</span>'

    mistakes_html = ""
    ec = row.get("examiner_comment")
    if ec and ec.get("text"):
        # The "Written by the author, not ICAI..." / "Real ICAI Examiner's
        # Comment..." provenance sentence used to repeat on every single
        # box -- stated once already in front matter's How to Read This
        # Book colour key, so printing it again on ~500+ boxes was pure
        # repetition (Pranav, 2026-07-28). Removed here; the label itself
        # ("Examiner's Comment:" vs "Author's Note:") plus the colour still
        # carry the distinction on the page.
        if ec.get("comment_source") == "icai":
            label = "Examiner&rsquo;s Comment"
            mistake_cls = "mistakes icai"
        else:
            label = "Author&rsquo;s Note"
            mistake_cls = "mistakes synth"
        mistakes_html = (
            f'<div class="{mistake_cls}"><strong>{label}:</strong> {html_lib.escape(ec["text"])}</div>'
        )

    answer_letter_line = ""
    if row.get("answer_letter"):
        answer_letter_line = f'<p><em>Correct option: <strong>{row["answer_letter"]}</strong></em></p>'

    return f"""
<div class="{cls}" id="{chapter_slug}-{idx:03d}">
  <div class="qmeta">
    <span class="src">{html_lib.escape(paper_label(row))}</span> &middot;
    <span class="qno">{html_lib.escape(qno_label(row))}</span> &middot;
    <span class="marks">Marks: {marks_span(row)}</span> &middot;
    <span class="marks">Approx Time: {approx_time_label(row)}</span> &middot;
    <span class="topic">{topic_label(row)}</span>
    {badges}
  </div>
  <div class="question"><strong>Question:</strong> <div>{question_html}</div></div>
  <div class="answer-block"><strong>Answer / Solution:</strong> {answer_letter_line}<div>{row["answer_html"]}</div></div>
  {mistakes_html}
  <div class="self-notes"><strong>Student Self Notes:</strong>
    <div class="notes-lines"><div class="dotted-line"></div><div class="dotted-line"></div></div>
  </div>
  <div class="student-fields">
    <span>My NB Page No <span class="fill-blank fill-blank-sm">&nbsp;</span></span>
    <span>My Tag <span class="fill-blank">&nbsp;</span></span>
    <span>Revision Phase <span class="box"></span>1 <span class="box"></span>2 <span class="box"></span>3</span>
  </div>
</div>
"""


def build_book(unitcode, standard_label, chapter_title, out_filename):
    data = load_index()
    home = [r for r in data if r["final_chapter"] == unitcode]
    integrated = [
        r for r in data
        if r["final_chapter"] != unitcode
        and any(t["unitcode"] == unitcode for t in r["topics"])
        and r["topic_count"] > 1
    ]

    descriptive = [r for r in home if r["qtype"] not in ("mcq", "case-mcq")]

    source_files = sorted(set(r["source_file"] for r in data))
    total_shown = len(descriptive) + len(integrated)
    chapter_slug = unitcode.replace("-", "")

    idx_counter = [0]

    def render_all(rows):
        out = []
        for r in rows:
            idx_counter[0] += 1
            out.append(render_qblock(r, idx_counter[0], chapter_slug))
        return "\n".join(out)

    def render_section(rows, heading, intro):
        # An empty section is now omitted entirely -- heading, intro, and
        # placeholder note all skipped (Pranav, 2026-07-28: a chapter with
        # no Integrated questions used to still print the full "II.
        # Integrated..." heading + intro sentence + an explanatory
        # empty-section note, pure wasted space repeated across every thin
        # chapter). The "empty Integrated is normal, not an extraction gap"
        # explanation now lives once in front matter / How to Read This
        # Book instead of being restated per chapter.
        if not rows:
            return ""
        return f"<h2>{heading}</h2>\n<p class='section-intro'>{intro}</p>\n{render_all(rows)}\n"

    descriptive_html = render_section(
        descriptive,
        f"I. Descriptive &amp; Scenario-Based Questions (pure {standard_label})",
        f"Full descriptive/scenario questions where this chapter is the sole topic tested (after independent-question splitting).",
    )
    integrated_html = render_section(
        integrated,
        f"II. Integrated Questions ({standard_label} with Other Standards)",
        f"Questions where {standard_label} judgment is one part of a larger, genuinely connected question also testing another standard.",
    )
    topic_summary_html = build_topic_summary(unitcode, home, standard_label)

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{standard_label} — {chapter_title}</title>
<style>{STYLE}</style>
</head>
<body>

<div class="brand-header">
<strong>Pranav Bhaiya</strong> &middot; The Newton of Accounts &middot; AIR 1-1-5<br>
Kahaan &middot; Koncept &middot; Karma &nbsp;&mdash;&nbsp; Always Focus on Karma, Not Results
</div>

<h1>{standard_label} — {chapter_title}</h1>
<p>Every MTP/RTP/PYQ question that tests this chapter, collected in one place, with official answers and topic tags — so you can practise every question this topic has been examined with, without hunting through separate papers.</p>

<div class="note">
<strong>A note on accuracy (please read):</strong> This is the first edition of this book, assembled with AI assistance and reviewed as carefully as we could manage, but it has not been independently audited question-by-question. If you spot an error &mdash; a wrong figure, a wrong answer, anything that looks off &mdash; please email <strong>{ERROR_REPORT_EMAIL}</strong> with the question reference so it can be corrected in the next edition.
</div>

<div class="note">
<strong>Scope of this book ({total_shown} questions):</strong> Covers {len(source_files)} sittings: {', '.join(s.replace('.html','').replace('_',' ') for s in source_files)}. MCQs on this chapter are deliberately not included here — practise those on the dedicated MCQ platform; this book is for descriptive/scenario practice with full worked answers.
</div>

<div class="note">
<strong>How this book is organised:</strong> Two sections — <strong>I. Descriptive (pure {standard_label})</strong> and <strong>II. Integrated</strong> (questions where {standard_label} is one part of a larger question that also tests another standard). An empty Section II for a chapter is normal and expected, not a mistake — most multi-topic-looking questions are split so each topic gets its own clean entry, so genuinely combined questions are the rarer case. Each answer includes either a real <strong>Examiner's Comment</strong> (tan/orange box, quoted from ICAI's own published feedback, where one exists for that sitting) or an <strong>Author's Note</strong> (pale pink box, a likely pitfall identified by the author, not an official ICAI finding, and may not apply in every case) &mdash; see <strong>How to Read this Book.md</strong> for the full key to every colour and symbol used.
</div>

{topic_summary_html}
{descriptive_html}
{integrated_html}

<div class="note" style="margin-top:48px;">
Found an error? Please email <strong>{ERROR_REPORT_EMAIL}</strong> with the question reference (shown at the top of each card) so it can be fixed in the next edition. Thank you for helping make this book better.
</div>

<div class="brand-footer">
#KeepLearning #DreamBig &nbsp;&middot;&nbsp; #LoveWhatYouDo<br>
<strong>{standard_label} — {chapter_title}</strong>
</div>

</body>
</html>
"""

    out_path = os.path.join(OUTPUT_DIR, out_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Wrote {out_path}")
    print(f"  Descriptive: {len(descriptive)} | Integrated: {len(integrated)} (MCQs excluded from book by design)")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    build_book(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
