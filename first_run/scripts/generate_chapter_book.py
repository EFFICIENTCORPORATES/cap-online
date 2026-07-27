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
import sys
import html as html_lib

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(HERE, "..", "output", "generated-from-script"))
INDEX_PATH = os.path.join(OUTPUT_DIR, "questions_index.json")

MONTH_NAMES = {"01": "January", "02": "February", "03": "March", "04": "April",
               "05": "May", "06": "June", "07": "July", "08": "August",
               "09": "September", "10": "October", "11": "November", "12": "December"}

ERROR_REPORT_EMAIL = "capranavpratiktulshyan@gmail.com"

ERROR_REGISTER_LINE_COUNT = 9

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
.notebook-ref{margin-top:10px;font-size:12.5px;color:#444;border-top:1px dashed #ccc;padding-top:6px;}
.notebook-ref .fill-blank{border-bottom:1px dotted #999;display:inline-block;min-width:160px;}
.self-notes{margin-top:8px;border:1px solid #ccc;background:#fff;border-radius:6px;padding:8px 12px;}
.self-notes .notes-lines{margin-top:4px;}
.self-notes .dotted-line{height:22px;border-bottom:1px dotted rgba(0,0,0,0.4);}
.tag-placeholder{margin-top:8px;font-size:12.5px;color:#444;}
.tag-placeholder .fill-blank{border-bottom:1px dotted #999;display:inline-block;min-width:220px;}
.revision-phase{margin-top:8px;font-size:12.5px;color:#444;}
.revision-phase .box{display:inline-block;border:1px solid #888;width:12px;height:12px;margin:0 3px 0 10px;vertical-align:middle;}
.brand-header{text-align:center;font-size:11px;color:#777;border-bottom:1px solid #eee;padding-bottom:8px;margin-bottom:18px;letter-spacing:.3px;}
.brand-header strong{color:#2c3e50;}
.brand-footer{text-align:center;font-size:11px;color:#777;border-top:1px solid #eee;padding-top:10px;margin-top:36px;line-height:1.8;}
.brand-footer strong{color:#2c3e50;}
.error-register{page-break-before:always;break-before:page;margin-top:40px;}
.error-register h2{margin-top:8px;}
.error-register h3{font-size:15px;color:#444;margin-top:28px;}
.error-register .dotted-line{height:34px;border-bottom:1px dotted rgba(0,0,0,0.4);}
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
    unitcode_disp = html_lib.escape(t["unitcode"].replace("-", "_"))
    standard = t.get("standard")
    title_esc = html_lib.escape(t.get("title") or "")
    subref_esc = html_lib.escape(str(t.get("subtopicref") or ""))
    if standard and standard != "n/a":
        chapter_part = f'{html_lib.escape(standard)} &mdash; {title_esc}'
    else:
        chapter_part = title_esc
    return f'{unitcode_disp} : {chapter_part} / ICAI Study Mat Topic No : {subref_esc}'


def topic_label(row):
    if not row.get("topics"):
        return ""
    return "  &nbsp;+&nbsp;  ".join(topic_full_label(t) for t in row["topics"])


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
        if ec.get("comment_source") == "icai":
            label = "Examiner&rsquo;s Comment"
            prov = "Real ICAI Examiner&rsquo;s Comment, quoted from the official document for this sitting."
            mistake_cls = "mistakes icai"
        else:
            label = "Author&rsquo;s Note"
            prov = "Written by the author, not ICAI &mdash; a likely pitfall, not an official finding. May not apply in every case."
            mistake_cls = "mistakes synth"
        mistakes_html = (
            f'<div class="{mistake_cls}"><strong>{label}:</strong> {html_lib.escape(ec["text"])}'
            f'<span class="prov">{prov}</span></div>'
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
  <div class="notebook-ref">My Notebook Ref No: <span class="fill-blank">&nbsp;</span></div>
  <div class="tag-placeholder">My Tag <span style="color:#999;">(e.g. Last-day Revision, Not Important, Easy, Must Practice)</span>: <span class="fill-blank">&nbsp;</span></div>
  <div class="revision-phase">Revision Phase completed:
    <span class="box"></span>1 &nbsp;
    <span class="box"></span>2 &nbsp;
    <span class="box"></span>3
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

    def section_or_empty(rows, label):
        if not rows:
            return f'<div class="empty-section">No questions in this batch are placed in {chapter_title} for this section. This is an honest finding, not an extraction gap — see the scope note above.</div>'
        return render_all(rows)

    descriptive_html = section_or_empty(descriptive, "Descriptive")
    integrated_html = section_or_empty(integrated, "Integrated")

    error_register_lines = "\n".join('<div class="dotted-line"></div>' for _ in range(ERROR_REGISTER_LINE_COUNT))

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

<h2>I. Descriptive &amp; Scenario-Based Questions (pure {standard_label})</h2>
<p class='section-intro'>Full descriptive/scenario questions where this chapter is the sole topic tested (after independent-question splitting).</p>
{descriptive_html}

<h2>II. Integrated Questions ({standard_label} with Other Standards)</h2>
<p class='section-intro'>Questions where {standard_label} judgment is one part of a larger, genuinely connected question also testing another standard.</p>
{integrated_html}

<div class="note" style="margin-top:48px;">
Found an error? Please email <strong>{ERROR_REPORT_EMAIL}</strong> with the question reference (shown at the top of each card) so it can be fixed in the next edition. Thank you for helping make this book better.
</div>

<div class="error-register">
<h2>Sanjeevani Booti 2: Error Register for {chapter_title}</h2>
<h3>Section 1: Concepts I Forgot</h3>
{error_register_lines}
<h3>Section 2: Mistakes I Repeated More Than Twice</h3>
{error_register_lines}
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
