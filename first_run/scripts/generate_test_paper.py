"""
Generates standalone AS-wise Test Papers (Question paper + separate Answer key)
for classroom use, by hand-picking the best/most comprehensive questions for a
given AS out of the already-tagged Layer 2 pool (questions_index.json) -- NOT
part of the main Question Bank Book pipeline (that pipeline includes every
tagged question per chapter; this script includes only a curated subset,
picked for exam-simulation quality and total-marks targeting).

Reuses the same branding/CSS language as generate_chapter_book.py
(Pranav Bhaiya / Newton of Accounts branding, qblock/answer-block/mistakes
styling) so these test papers look like they belong to the same book series,
just restyled as an actual sit-down test (cover page with Time Allowed /
Maximum Marks / student fields / instructions, sequential Q1-Q4 numbering).

Usage: python generate_test_paper.py
(Selections are hardcoded below -- this is a one-off classroom-test build,
not a queryable generator like generate_chapter_book.py. Edit SELECTIONS to
build a different set of test papers.)
"""
import json
import math
import os
import sys
import html as html_lib

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(HERE, "..", "output", "generated-from-script"))
INDEX_PATH = os.path.join(OUTPUT_DIR, "questions_index.json")
TESTS_DIR = os.path.normpath(os.path.join(HERE, "..", "TESTS"))

MONTH_NAMES = {"01": "January", "02": "February", "03": "March", "04": "April",
               "05": "May", "06": "June", "07": "July", "08": "August",
               "09": "September", "10": "October", "11": "November", "12": "December"}

ERROR_REPORT_EMAIL = "capranavpratiktulshyan@gmail.com"

# ---------------------------------------------------------------------------
# Curated selections -- picked from questions_index.json by hand for:
#   (a) total marks 20-25 per AS, (b) each Q self-contained/comprehensive,
#   (c) no two questions in the same paper testing the same narrow point
#       (checked pairwise against the source PDFs' own text -- several
#       questions in the pool are near-verbatim repeats across sittings,
#       e.g. "Colour Limited leased a Machine to Red Limited" appears in
#       both MTP Jan 2026 and PYQ May 2024 -- only one instance used per
#       paper), (d) RTP-sourced rows excluded throughout because RTPs
#       carry no official marks (data-marks is genuinely absent in the
#       source, not a tagging gap) -- a graded test paper needs real marks.
# ---------------------------------------------------------------------------
SELECTIONS = {
    "AS02": {
        "code": "M2-C5-U1",
        "title": "AS 2 — Valuation of Inventories",
        "short": "AS 2",
        "ids": [
            "CAI-P1-MTP-2026-01-S1-PII-Q2-a",
            "CAI-P1-MTP-2023-11-S1-PII-Q1-b",
            "CAI-P1-PYQ-2023-11-PII-Q1-c",
            "CAI-P1-MTP-2026-01-S2-PII-Q6-a-alt2",
        ],
    },
    "AS10": {
        "code": "M2-C5-U2",
        "title": "AS 10 — Property, Plant and Equipment",
        "short": "AS 10",
        "ids": [
            "CAI-P1-PYQ-2025-05-PII-Q1-a",
            "CAI-P1-MTP-2023-05-S1-PII-Q6-a",
            "CAI-P1-MTP-2023-11-S1-PII-Q1-d",
            "CAI-P1-PYQ-2023-05-PII-Q1-a",
        ],
    },
    "AS16": {
        "code": "M2-C5-U4",
        "title": "AS 16 — Borrowing Costs",
        "short": "AS 16",
        "ids": [
            "CAI-P1-MTP-2026-01-S1-PII-Q1-b",
            "CAI-P1-MTP-2023-05-S1-PII-Q6-c",
            "CAI-P1-MTP-2023-11-S1-PII-Q1-c",
            "CAI-P1-MTP-2025-09-S2-PII-Q6-a",
        ],
    },
    "AS19": {
        "code": "M2-C5-U5",
        "title": "AS 19 — Leases",
        "short": "AS 19",
        "ids": [
            "CAI-P1-MTP-2026-05-S2-PII-Q2-a",
            "CAI-P1-PYQ-2025-01-PII-Q1-b",
            "CAI-P1-MTP-2025-01-S1-PII-Q6-b",
            "CAI-P1-MTP-2024-05-S1-PII-Q1-b",
        ],
    },
    "AS26": {
        "code": "M2-C5-U6",
        "title": "AS 26 — Intangible Assets",
        "short": "AS 26",
        "ids": [
            "CAI-P1-MTP-2025-01-S2-PII-Q1-b",
            "CAI-P1-MTP-2025-01-S1-PII-Q1-b",
            "CAI-P1-MTP-2024-05-S2-PII-Q1-a",
            "CAI-P1-PYQ-2024-09-PII-Q1-a",
        ],
    },
    "AS28": {
        "code": "M2-C5-U7",
        "title": "AS 28 — Impairment of Assets",
        "short": "AS 28",
        "ids": [
            "CAI-P1-PYQ-2025-09-PII-Q3-b",
            "CAI-P1-PYQ-2026-05-PII-Q1-b",
            "CAI-P1-MTP-2024-05-S1-PII-Q1-c",
            "CAI-P1-PYQ-2025-05-PII-Q6-a-alt2",
        ],
    },
}

STYLE = """
body{font-family:Arial,Helvetica,sans-serif;margin:24px;max-width:980px;margin-left:auto;margin-right:auto;color:#222;background:#fff;line-height:1.5;}
h1{font-size:23px;margin-bottom:4px;color:#2c3e50;}
h2{font-size:16px;margin-top:8px;color:#555;font-weight:normal;}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:12.5px;}
th,td{border:1px solid #999;padding:5px 7px;text-align:left;vertical-align:top;}
th{background:#2c3e50;color:#fff;}
.brand-header{text-align:center;font-size:11px;color:#777;border-bottom:1px solid #eee;padding-bottom:8px;margin-bottom:18px;letter-spacing:.3px;}
.brand-header strong{color:#2c3e50;}
.brand-footer{text-align:center;font-size:11px;color:#777;border-top:1px solid #eee;padding-top:10px;margin-top:36px;line-height:1.8;}
.brand-footer strong{color:#2c3e50;}
.cover{border:2px solid #2c3e50;border-radius:10px;padding:20px 26px;margin:18px 0 28px;}
.cover-meta{display:flex;flex-wrap:wrap;gap:10px 32px;margin:14px 0;font-size:14px;}
.cover-meta div{flex:1 1 220px;}
.cover-meta b{color:#2c3e50;}
.student-line{margin:8px 0;font-size:14px;}
.student-line .fill{display:inline-block;border-bottom:1px solid #888;min-width:260px;margin-left:8px;}
.instructions{background:#fff8e1;border:1px solid #e0c46c;padding:12px 18px;border-radius:6px;font-size:13px;margin:16px 0;}
.instructions ol{margin:6px 0 0 18px;padding:0;}
.instructions li{margin:3px 0;}
.qsection-table{margin:16px 0 8px;}
.qsection-table th{background:#445566;}
.qblock{border:1px solid #ccc;border-radius:8px;padding:16px 20px;margin:20px 0;background:#fdfdfd;page-break-inside:avoid;}
.qblock.answer{background:#eafbea;border-color:#a9d8a9;}
.qmeta{font-size:12px;color:#555;margin-bottom:10px;padding-bottom:8px;border-bottom:1px dashed #ccc;}
.qmeta .src{font-weight:bold;color:#2c3e50;}
.qmeta .marks{font-weight:bold;}
.qnum{display:inline-block;background:#2c3e50;color:#fff;border-radius:50%;width:26px;height:26px;text-align:center;line-height:26px;font-weight:bold;margin-right:8px;}
.question{margin:10px 0;}
.answer-block{margin:10px 0;background:#eafbea;padding:10px 14px;border-radius:6px;}
.case-facts{background:#f5f5fb;border-left:3px solid #8888c0;padding:6px 12px;margin-bottom:8px;font-size:13px;}
.mistakes{margin:10px 0;padding:8px 12px;border-radius:6px;font-size:13.5px;border-left:3px solid #999;}
.mistakes.icai{background:#fff3e0;border-left-color:#e0b46c;color:#5a3d0a;}
.mistakes.synth{background:#fdf1f1;border-left-color:#d98a8a;color:#7a2f2f;}
.mistakes .prov{font-style:italic;color:#666;font-size:11.5px;display:block;margin-top:4px;}
.rough-work{border:1px dashed #aaa;border-radius:6px;margin-top:14px;padding:10px 14px;color:#999;font-size:12px;}
.rough-work .line{height:26px;border-bottom:1px dotted #ccc;}
.total-row{font-size:14px;font-weight:bold;color:#2c3e50;text-align:right;margin:6px 0 0;}
"""

BRAND_HEADER = """<div class="brand-header">
<strong>Pranav Bhaiya</strong> &middot; The Newton of Accounts &middot; AIR 1-1-5<br>
Kahaan &middot; Koncept &middot; Karma &nbsp;&mdash;&nbsp; Always Focus on Karma, Not Results
</div>"""


def brand_footer(chapter_title):
    return f"""<div class="brand-footer">
#KeepLearning #DreamBig &nbsp;&middot;&nbsp; #LoveWhatYouDo<br>
<strong>{html_lib.escape(chapter_title)} &mdash; Test Paper</strong>
</div>"""


def load_index():
    with open(INDEX_PATH, encoding="utf-8") as f:
        rows = json.load(f)
    return {r["id"]: r for r in rows}


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
        return f"Q{row['parent_qno']}({row['subpart']}) of the original paper"
    if row.get("subpart"):
        return f"Q{row.get('qno','')}({row['subpart']}) of the original paper"
    return f"Q{row.get('qno','')} of the original paper"


def approx_time_label(marks):
    minutes = math.ceil(marks * 1.8)
    return f"~{minutes} min"


def topic_line(row):
    topics = row.get("topics") or []
    labels = []
    for t in topics:
        std = t.get("standard") or ""
        title = t.get("subtopictitle") or t.get("title") or ""
        labels.append(f"{std}: {title}" if std else title)
    return " + ".join(labels)


def mistakes_html(row):
    ec = row.get("examiner_comment") or {}
    text = (ec.get("text") or "").strip()
    if not text:
        return ""
    if ec.get("comment_source") == "icai":
        return (f'<div class="mistakes icai"><strong>Examiner&rsquo;s Comment (real ICAI-sourced):</strong> {text}'
                f'<span class="prov">Source: {html_lib.escape(ec.get("source_citation") or "ICAI Examiner\'s Comment")}</span></div>')
    return (f'<div class="mistakes synth"><strong>Author&rsquo;s Note (likely pitfall, not an official ICAI finding):</strong> {text}</div>')


def build_question_paper(as_key, meta, index):
    rows = [index[i] for i in meta["ids"]]
    total_marks = sum(r["marks"] for r in rows)
    total_time = sum(math.ceil(r["marks"] * 1.8) for r in rows)

    parts = [f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html_lib.escape(meta['title'])} — Test Paper (Questions)</title>
<style>{STYLE}</style>
</head>
<body>
{BRAND_HEADER}

<div class="cover">
<h1>{html_lib.escape(meta['title'])} &mdash; Chapter Test</h1>
<h2>CA Inter &middot; Paper 1: Advanced Accounting</h2>
<div class="cover-meta">
<div><b>Maximum Marks:</b> {total_marks}</div>
<div><b>Time Allowed:</b> {total_time} minutes (approx.)</div>
<div><b>Number of Questions:</b> {len(rows)} (all compulsory)</div>
</div>
<div class="student-line">Student Name: <span class="fill">&nbsp;</span></div>
<div class="student-line">Date: <span class="fill" style="min-width:140px;">&nbsp;</span> &nbsp;&nbsp; Attempt No: <span class="fill" style="min-width:100px;">&nbsp;</span></div>
</div>

<div class="instructions">
<strong>Instructions:</strong>
<ol>
<li>All {len(rows)} questions are compulsory. Marks for each question are shown alongside the question number.</li>
<li>Show full working notes &mdash; marks are awarded for method, not only the final figure.</li>
<li>State clearly any assumptions made, wherever the question is silent on a point.</li>
<li>This paper draws on real ICAI MTP/PYQ questions on {html_lib.escape(meta['short'])}, selected to cover the chapter&rsquo;s main tested concepts comprehensively.</li>
<li>Answers should be written as per Accounting Standards applicable for CA Inter, ICAI.</li>
</ol>
</div>

<table class="qsection-table">
<thead><tr><th>Q. No.</th><th>Concept Tested</th><th>Marks</th></tr></thead>
<tbody>"""]
    for n, r in enumerate(rows, 1):
        parts.append(f"<tr><td>Q{n}</td><td>{html_lib.escape(topic_line(r))}</td><td>{r['marks']}</td></tr>")
    parts.append(f"<tr><td colspan='2' style='text-align:right;'><strong>Total</strong></td><td><strong>{total_marks}</strong></td></tr>")
    parts.append("</tbody></table>")

    for n, r in enumerate(rows, 1):
        parts.append(f"""
<div class="qblock">
  <div class="qmeta">
    <span class="qnum">{n}</span>
    <span class="marks">Marks: {r['marks']}</span> &middot;
    <span class="marks">{approx_time_label(r['marks'])}</span>
  </div>
  <div class="question">{r['question_html']}</div>
  <div class="rough-work">Rough Work / Working Notes
    <div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div><div class="line"></div>
  </div>
</div>""")

    parts.append(f"\n<p style='text-align:center;color:#999;font-size:12px;margin-top:26px;'>&mdash; End of Question Paper &mdash;</p>\n")
    parts.append(brand_footer(meta["title"]))
    parts.append("\n</body>\n</html>\n")
    return "".join(parts), total_marks


def build_answer_key(as_key, meta, index, total_marks):
    rows = [index[i] for i in meta["ids"]]
    parts = [f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html_lib.escape(meta['title'])} — Test Paper (Answer Key)</title>
<style>{STYLE}</style>
</head>
<body>
{BRAND_HEADER}

<div class="cover">
<h1>{html_lib.escape(meta['title'])} &mdash; Chapter Test: Answer Key</h1>
<h2>CA Inter &middot; Paper 1: Advanced Accounting &middot; Maximum Marks: {total_marks}</h2>
</div>

<div class="instructions">
<strong>How to use this key:</strong> Mark your own attempt against the working shown below before checking the final figure &mdash; in Advanced Accounting most marks sit in the working notes, not the final total. Where an <strong>Author&rsquo;s Note</strong> appears, it flags a mistake students commonly make on that exact question; read it even if your final answer was correct.
</div>
"""]
    for n, r in enumerate(rows, 1):
        src = paper_label(r)
        qno = qno_label(r)
        parts.append(f"""
<div class="qblock answer">
  <div class="qmeta">
    <span class="qnum">{n}</span>
    <span class="marks">Marks: {r['marks']}</span> &middot;
    <span class="src">Source: {html_lib.escape(src)}, {html_lib.escape(qno)}</span> &middot;
    <span class="topic">{html_lib.escape(topic_line(r))}</span>
  </div>
  <div class="answer-block">{r['answer_html']}</div>
  {mistakes_html(r)}
</div>""")

    parts.append(f"\n<p style='text-align:center;color:#999;font-size:12px;margin-top:26px;'>&mdash; End of Answer Key &mdash;</p>\n")
    parts.append(f"""<div class="instructions" style="margin-top:24px;">
<strong>A note on accuracy:</strong> These questions are drawn verbatim from ICAI's own MTP/PYQ papers via the Question Bank Book pipeline, reviewed for accuracy but not independently audited question-by-question in this specific test-paper compilation. If you spot an error, please email <strong>{ERROR_REPORT_EMAIL}</strong>.
</div>""")
    parts.append(brand_footer(meta["title"]))
    parts.append("\n</body>\n</html>\n")
    return "".join(parts)


def main():
    index = load_index()
    os.makedirs(TESTS_DIR, exist_ok=True)
    summary = []
    for as_key, meta in SELECTIONS.items():
        for qid in meta["ids"]:
            if qid not in index:
                raise SystemExit(f"ERROR: id not found in questions_index.json: {qid} ({as_key})")
            if index[qid].get("marks") is None:
                raise SystemExit(f"ERROR: {qid} ({as_key}) has no stated marks -- cannot use in a graded paper")

        q_html, total_marks = build_question_paper(as_key, meta, index)
        a_html = build_answer_key(as_key, meta, index, total_marks)

        q_path = os.path.join(TESTS_DIR, f"{as_key}_Test_Paper_Questions.html")
        a_path = os.path.join(TESTS_DIR, f"{as_key}_Test_Paper_Answers.html")
        with open(q_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(q_html)
        with open(a_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(a_html)

        summary.append((as_key, meta["title"], len(meta["ids"]), total_marks))
        print(f"{as_key}: {total_marks} marks, {len(meta['ids'])} questions -> {os.path.basename(q_path)} / {os.path.basename(a_path)}")

    print("\nAll test papers written to:", TESTS_DIR)
    print("\nSummary:")
    for as_key, title, n, marks in summary:
        print(f"  {as_key:6s} {title:45s} {n} questions, {marks} marks")


if __name__ == "__main__":
    main()
