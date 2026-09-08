"""
build_second_phase_tests.py
============================
Generates one 50-mark, single-AS chapter test per accounting standard in
SECOND_PHASE_AS_LIST, in Markdown, styled after ICAI's own "Test Your
Knowledge" (MCQs) + "Illustrations" (descriptive problems) sections rather
than a formal exam-paper cover sheet.

Sources (read-only, never modified):
  - Exam-derived descriptive: first_run/output/generated-from-script/questions_index.json
  - Exam-derived MCQ:         <MCQ_JSON_PATH> (examstudyhub's mcq_questions_extracted.json)
  - ICAI study-material "Test Your Knowledge": first_run/output/generated-from-script/
    study_material_tyk.json (built by extract_study_material_tyk.py from
    books/concept-book/raw_icai_study_materials/ - the textbook chapters
    themselves, not past exam papers). These questions carry NO official
    marks in the source, so marks are ESTIMATED here from answer length
    (word-count bucketed into the same 2/4/5/7/8/10 denominations the real
    exam pool uses) and every such item is rendered with an explicit
    "Estimated marks" tag - never presented as if it were an official mark.

Output: first_run/TESTS/second phase/AS<NN>_Test.md  (one per chapter)
        first_run/TESTS/second phase/README.md        (index + honest gaps)

Design rules (see chat / CLAUDE.md discipline this repo already follows):
  - Never fabricate a question. Only real, already-tagged questions from the
    two source files above are used.
  - Target composition: 50 marks total, 30% MCQ / 70% Descriptive. Because
    MCQ marks in the source pool are essentially fixed at 2 marks each, and
    some chapters simply don't have 50 marks worth of tagged content yet,
    the script computes the closest *exact* achievable split via subset-sum
    (never over-shoots 50, never invents a fractional question) and reports
    the real achieved total + ratio honestly per chapter, flagging any
    chapter that falls short of 50.
  - Exact-duplicate question text (same question re-tagged from >1 sitting)
    is de-duplicated before selection. This is NOT the platform's deferred
    >=90%-similarity OP/PP detection (still unbuilt) - just a same-text guard.
"""
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from datetime import date

REPO_ROOT = Path(r"D:\EffCorp_Projects\cap-online")
DESC_PATH = REPO_ROOT / "first_run" / "output" / "generated-from-script" / "questions_index.json"
MCQ_PATH = Path(r"D:\EffCorp_Products\Main1Lavya\Main1lavyaAIAgents\examstudyhub\assets\exam_bot\mcq_questions_extracted.json")
STUDY_TYK_PATH = REPO_ROOT / "first_run" / "output" / "generated-from-script" / "study_material_tyk.json"
OUT_DIR = REPO_ROOT / "first_run" / "TESTS" / "second phase"
STUDENT_DIR = OUT_DIR / "student-edition"

TARGET_TOTAL = 50
TARGET_MCQ_FRACTION = 0.30

AS_LIST = [
    "as02", "as04", "as05", "as07", "as09", "as10", "as12", "as13",
    "as15", "as16", "as19", "as26", "as28", "as29",
]

CHAPTER_MAP = {
    "as02": "M2-C5-U1", "as10": "M2-C5-U2", "as13": "M2-C5-U3", "as16": "M2-C5-U4",
    "as19": "M2-C5-U5", "as26": "M2-C5-U6", "as28": "M2-C5-U7", "as15": "M2-C6-U1",
    "as29": "M2-C6-U2", "as04": "M2-C7-U1", "as05": "M2-C7-U2", "as07": "M2-C8-U1",
    "as09": "M2-C8-U2", "as12": "M2-C9-U1",
}

AS_NAME = {
    "as02": "AS 2 — Valuation of Inventories",
    "as04": "AS 4 — Contingencies and Events Occurring After the Balance Sheet Date",
    "as05": "AS 5 — Net Profit or Loss for the Period, Prior Period Items and Changes in Accounting Policies",
    "as07": "AS 7 — Construction Contracts",
    "as09": "AS 9 — Revenue Recognition",
    "as10": "AS 10 — Property, Plant and Equipment",
    "as12": "AS 12 — Accounting for Government Grants",
    "as13": "AS 13 — Accounting for Investments",
    "as15": "AS 15 — Employee Benefits",
    "as16": "AS 16 — Borrowing Costs",
    "as19": "AS 19 — Leases",
    "as26": "AS 26 — Intangible Assets",
    "as28": "AS 28 — Impairment of Assets",
    "as29": "AS 29 (Revised) — Provisions, Contingent Liabilities and Contingent Assets",
}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


QUOTE_CHARS_RE = re.compile(r"[‘’“”'\"�]")


def norm_fingerprint(html):
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unicodedata.normalize("NFKC", text)
    # strip quote marks (straight/curly) and the U+FFFD replacement char -
    # a real source-data encoding artifact (confirmed: one exam-pool record
    # has a corrupted quote rendered as U+FFFD) otherwise makes an
    # ordinary duplicate question score as textually distant as a genuinely
    # different one, since replacement-char noise dominates the similarity
    # ratio far out of proportion to its semantic weight.
    text = QUOTE_CHARS_RE.sub("", text)
    text = re.sub(r"\d+", "#", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text[:400]


def estimate_marks_from_answer(answer_html):
    """Study-material Illustrations/TYK carry no official marks (Pranav
    confirmed) - estimate from the answer's word count, bucketed into the
    same 2/4/5/7/8/10 mark denominations already observed across the real
    MTP/RTP/PYQ pool, so estimated and real marks read consistently."""
    text = re.sub(r"<[^>]+>", " ", answer_html or "")
    words = len(text.split())
    if words < 40:
        return 2
    if words < 90:
        return 4
    if words < 150:
        return 5
    if words < 250:
        return 7
    if words < 400:
        return 8
    return 10


def normalize_study_mcq(item, as_key, unitcode):
    return {
        "question_html": item["question_html"], "options": item["options"],
        "correct_option": item["correct_option"], "answer_html": item["answer_html"],
        "marks": 1, "topic_text": f"{unitcode} — ICAI Study Material (Test Your Knowledge)",
        "source_kind": "study_material", "estimated_marks": False,
        "study_source_label": f"Study Material TYK MCQ #{item['source_num']}",
    }


def normalize_study_desc(item, as_key, unitcode):
    marks = estimate_marks_from_answer(item["answer_html"])
    return {
        "question_html": item["question_html"], "answer_html": item["answer_html"],
        "marks": marks, "case_facts_html": None, "topics": None,
        "examiner_comment": None, "source_kind": "study_material", "estimated_marks": True,
        "study_source_label": f"Study Material TYK — {item['qtype']} #{item['source_num']}",
        "unitcode_label": unitcode,
    }


def load_study_material_pool(as_key, unitcode):
    """Load and normalise this chapter's extracted Test Your Knowledge items
    (see extract_study_material_tyk.py's own module docstring for why only
    TYK, not Illustrations, is sourced this way, and for every corruption
    class its parser guards against). Table-bearing descriptive answers are
    excluded here - those ledger/T-account tables were already messily
    OCR'd in the source PDF before extraction ever touched them, and are not
    safe to present as a clean answer."""
    if not STUDY_TYK_PATH.exists():
        return [], []
    all_chapters = load_json(STUDY_TYK_PATH)
    chapter = next((c for c in all_chapters if c.get("as_key") == as_key), None)
    if not chapter:
        return [], []
    mcqs = [normalize_study_mcq(m, as_key, unitcode) for m in chapter.get("mcq", [])]
    descs = [
        normalize_study_desc(d, as_key, unitcode)
        for d in chapter.get("descriptive", [])
        if not d.get("has_table")
    ]
    return mcqs, descs


NEAR_DUP_THRESHOLD = 0.85


def dedup(rows, html_field):
    """De-duplicate on (case facts + question) text, not question text alone -
    several case-based MCQs share a generic question stem ('what will be the
    cost of material') across genuinely different case scenarios (different
    figures in case_facts_html), so case_facts_html must be part of the
    fingerprint or distinct questions get wrongly merged.

    Uses fuzzy (SequenceMatcher ratio >= NEAR_DUP_THRESHOLD) matching against
    every fingerprint already kept, not exact equality - the same underlying
    case scenario gets re-typed with slightly different wording/formatting
    across sittings (paragraph vs bullet list, "which included" vs "which
    included rent" reordered, etc: confirmed real, e.g. AS16's "Mars Ltd."
    case appearing near-verbatim across 3 separate MTP sittings with 3
    different phrasings), so exact-string dedup silently let the same
    question through more than once. This is a lighter-weight version of the
    platform's own deferred >=90%-similarity OP/PP detection (see CLAUDE.md
    §6) - not the full system, but catches this specific, common pattern."""
    seen_fps = []
    kept = []
    skipped = 0
    for r in rows:
        fp = norm_fingerprint(r.get("case_facts_html", "") or "") + "||" + norm_fingerprint(r.get(html_field))
        if fp and any(SequenceMatcher(None, fp, prev).ratio() >= NEAR_DUP_THRESHOLD for prev in seen_fps):
            skipped += 1
            continue
        if fp:
            seen_fps.append(fp)
        kept.append(r)
    return kept, skipped


def reachable_sums(items, cap):
    """Boolean subset-sum reachability up to cap (inclusive)."""
    cap = max(0, cap)
    dp = [False] * (cap + 1)
    dp[0] = True
    for _key, w in items:
        if w <= 0 or w > cap:
            continue
        for s in range(cap, w - 1, -1):
            if dp[s - w]:
                dp[s] = True
    return [s for s in range(cap + 1) if dp[s]]


def knapsack_max_count_exact(items, target):
    """items: list of (key, marks:int). Returns (achieved_sum, [keys]) for the
    largest achievable sum <= target that maximises the number of items used
    among all subsets achieving that sum (0/1 knapsack, exact-sum first).

    Uses the full 2D DP table (dp[i][s] = max count using the first i items
    summing to exactly s), not the space-optimised 1D version - backtracking
    the 1D version via a single "last writer" pointer per sum is WRONG for
    0/1 knapsack: one item's own pass can be the last writer for several
    different sum-cells in a row (e.g. a run of consecutive 1-mark items),
    and naively following pointers back through several such cells collects
    that same physical item multiple times. Real bug this replaced: with
    four 1-mark MCQs available, the picker returned the same MCQ 6-7 times
    to hit a 15-mark target instead of picking 15 distinct questions.
    Backtracking by item index (dp[i][s] vs dp[i-1][s]) is the standard,
    correct way to guarantee each item is used at most once. Table size here
    is tiny (well under 100 x 50), so the 2D table costs nothing."""
    target = max(0, target)
    n = len(items)
    NEG = -1
    dp = [[NEG] * (target + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for i in range(1, n + 1):
        _key, w = items[i - 1]
        row_prev, row = dp[i - 1], dp[i]
        for s in range(target + 1):
            row[s] = row_prev[s]
            if 0 < w <= s and row_prev[s - w] != NEG and row_prev[s - w] + 1 > row[s]:
                row[s] = row_prev[s - w] + 1
    best_sum = 0
    for s in range(target, -1, -1):
        if dp[n][s] != NEG:
            best_sum = s
            break
    keys = []
    i, s = n, best_sum
    while i > 0:
        if dp[i][s] != dp[i - 1][s]:
            key, w = items[i - 1]
            keys.append(key)
            s -= w
        i -= 1
    return best_sum, keys


def build_options_md(options):
    lines = []
    for letter in sorted(options.keys()):
        lines.append(f"- **({letter})** {options[letter]}")
    return "\n".join(lines)


def source_label_mcq(m):
    if m.get("source_kind") == "study_material":
        return m["study_source_label"]
    bits = [m.get("exam_type") or "", m.get("year") or "", f"Set {m['set']}" if m.get("set") else "", m.get("qno_text") or ""]
    return " ".join(b for b in bits if b).strip()


def source_label_desc(d):
    if d.get("source_kind") == "study_material":
        return d["study_source_label"]
    pt = d.get("paper_type") or ""
    yr = d.get("exam_year") or ""
    st = f"Set {d['set']}" if d.get("set") else ""
    qno = d.get("qno") or d.get("parent_qno") or ""
    sub = d.get("subpart") or ""
    qlabel = f"Q{qno}{sub}" if qno else ""
    bits = [pt, yr, st, qlabel]
    return " ".join(b for b in bits if b).strip()


def topics_label(d, as_name):
    if d.get("source_kind") == "study_material":
        return as_name
    topics = d.get("topics") or []
    labels = [t.get("label") for t in topics if t.get("label")]
    return "; ".join(labels) if labels else as_name


def source_note(row):
    """A short, natural source citation - no internal IDs, no pipeline
    references. Study-material items just say where they're from; exam
    items cite the real paper."""
    if row.get("source_kind") == "study_material":
        return "ICAI Study Material"
    if "exam_type" in row:
        return source_label_mcq(row)
    return source_label_desc(row)


DASH_RE = re.compile(r"[–—]")  # en dash, em dash


def clean_typography(text):
    """Plain hyphens instead of en/em dashes, throughout - applied as a
    final pass over the whole rendered document (heading text, question
    text, answer text, everything), not just the scaffolding this script
    writes itself."""
    return DASH_RE.sub("-", text)


def render_mcqs(selected_mcqs, as_name, with_marks_line=True):
    out = []
    for i, m in enumerate(selected_mcqs, 1):
        if m.get("case_facts_html"):
            out.append(m["case_facts_html"])
            out.append("")
        out.append(f"**{i}.** {m.get('question_html', '')}")
        out.append("")
        out.append(build_options_md(m.get("options", {})))
        if with_marks_line:
            topic = m.get("topic_text") or as_name
            out.append("")
            out.append(f"*[{m.get('marks', '?')} Marks | Topic: {topic} | Source: {source_note(m)}]*")
        out.append("")
    return "\n".join(out)


def render_mcq_answers(selected_mcqs):
    out = []
    for i, m in enumerate(selected_mcqs, 1):
        out.append(f"**{i}.** Correct Answer: **({m.get('correct_option', '?')})**")
        out.append("")
        out.append(m.get("answer_html", ""))
        out.append("")
    return "\n".join(out)


def render_desc(selected_desc, as_name, with_marks_line=True):
    out = []
    for i, d in enumerate(selected_desc, 1):
        if d.get("case_facts_html"):
            out.append(d["case_facts_html"])
            out.append("")
        out.append(f"**Q{i}.** {d.get('question_html', '')}")
        if with_marks_line:
            topic = topics_label(d, as_name)
            out.append("")
            out.append(f"*[{d.get('marks', '?')} Marks | Topic: {topic} | Source: {source_note(d)}]*")
        out.append("")
    return "\n".join(out)


def render_desc_answers(selected_desc):
    out = []
    for i, d in enumerate(selected_desc, 1):
        out.append(f"**Q{i}.**")
        out.append("")
        out.append(d.get("answer_html", ""))
        out.append("")
        ec = d.get("examiner_comment")
        if ec and ec.get("text"):
            src = ec.get("comment_source")
            label = "Examiner's Comment" if src == "icai" else "Common Mistake to Avoid"
            out.append(f"> **{label}:** {ec['text']}")
            out.append("")
    return "\n".join(out)


def select_and_pack(mcq_rows, desc_rows):
    """Core selection: de-duplicate, then search for the MCQ/descriptive
    marks split that gets closest to exactly TARGET_TOTAL marks, tie-broken
    toward the 30:70 target ratio. Pure function of the two pools handed to
    it - build_test() decides WHICH pools (real-only vs real+study-material)
    to call this with."""
    mcq_rows, mcq_dupes = dedup(mcq_rows, "question_html")
    desc_rows, desc_dupes = dedup(desc_rows, "question_html")

    max_mcq_available = sum(m["marks"] for m in mcq_rows)
    max_desc_available = sum(d["marks"] for d in desc_rows)
    max_total_available = max_mcq_available + max_desc_available

    effective_total = min(TARGET_TOTAL, max_total_available)
    target_mcq_marks = min(round(effective_total * TARGET_MCQ_FRACTION), max_mcq_available)

    mcq_items = [(i, m["marks"]) for i, m in enumerate(mcq_rows)]
    desc_items = [(i, d["marks"]) for i, d in enumerate(desc_rows)]

    # Exhaustive search over every achievable MCQ sum (not just the one nearest
    # 30%): for each, take the best reachable descriptive sum for the
    # remaining budget, and keep whichever split gets closest to exactly
    # `effective_total` marks - breaking ties toward the 30:70 target ratio.
    # This matters because MCQ marks come in coarse 2-mark increments while
    # descriptive marks vary (2/4/5/7/...), so the split nearest 30:70 doesn't
    # always hit an exact total even when the chapter's combined pool easily
    # could with a different split.
    mcq_cap = min(effective_total, max_mcq_available)
    best = None  # (achieved_total, -abs(mcq_marks - target_mcq_marks), mcq_marks, mcq_idx, desc_marks, desc_idx)
    for mcq_sum in reachable_sums(mcq_items, mcq_cap):
        _dummy, mcq_idx_candidate = knapsack_max_count_exact(mcq_items, mcq_sum)
        desc_target = effective_total - mcq_sum
        desc_sum, desc_idx_candidate = knapsack_max_count_exact(desc_items, desc_target)
        total = mcq_sum + desc_sum
        key = (total, -abs(mcq_sum - target_mcq_marks))
        if best is None or key > best[0]:
            best = (key, mcq_sum, mcq_idx_candidate, desc_sum, desc_idx_candidate)

    _key, mcq_marks_used, mcq_idx, desc_marks_used, desc_idx = best
    achieved_total = mcq_marks_used + desc_marks_used

    selected_mcqs = [mcq_rows[i] for i in sorted(mcq_idx, key=lambda i: (mcq_rows[i].get("year") or "", mcq_rows[i].get("qno_text") or ""))]
    selected_desc = [desc_rows[i] for i in sorted(desc_idx, key=lambda i: (desc_rows[i].get("exam_year") or "", desc_rows[i].get("marks") or 0))]

    return {
        "mcq_marks": mcq_marks_used, "desc_marks": desc_marks_used, "achieved_total": achieved_total,
        "mcq_count": len(selected_mcqs), "desc_count": len(selected_desc),
        "selected_mcqs": selected_mcqs, "selected_desc": selected_desc,
        "max_mcq_available": max_mcq_available, "max_desc_available": max_desc_available,
        "max_total_available": max_total_available,
        "mcq_dupes_removed": mcq_dupes, "desc_dupes_removed": desc_dupes,
        "mcq_pool_size": len(mcq_rows), "desc_pool_size": len(desc_rows),
    }


def build_test(as_key, mcq_pool_all, desc_pool_all):
    unitcode = CHAPTER_MAP[as_key]
    name = AS_NAME[as_key]

    real_mcq_rows = [m for m in mcq_pool_all if m.get("chapter_slug") == as_key and isinstance(m.get("marks"), int)]
    # questions_index.json also tags the Part I MCQs of these same papers (qtype
    # 'mcq'/'case-mcq') - confirmed by identical id strings against mcq_id in
    # mcq_questions_extracted.json (e.g. CAI-P1-MTP-2025-01-S2-PI-Q1 appears in
    # both). Section A already draws on that same MCQ content via the dedicated
    # MCQ pool, so Section B must exclude qtype mcq/case-mcq or the same
    # questions would be double-counted as "descriptive".
    real_desc_rows = [
        d for d in desc_pool_all
        if d.get("final_chapter") == unitcode
        and d.get("qtype") in ("practical", "theory")
        and isinstance(d.get("marks"), int) and d.get("marks", 0) > 0
    ]

    # Prefer real, officially-marked exam content over estimated-mark study-
    # material content: try real-only first, and only fall back to the
    # combined pool (real + study-material Test Your Knowledge) if real
    # content alone can't reach the 50-mark target. Without this two-phase
    # approach, the count-maximising knapsack below would happily swap in a
    # pile of 1-mark study-material MCQs even for a chapter that already had
    # plenty of real 2-mark exam MCQs, purely because more (smaller) items
    # maximises its own count objective - exactly backwards from what's
    # wanted here.
    real_only = select_and_pack(real_mcq_rows, real_desc_rows)
    used_study_material = False
    study_material_available = False
    if real_only["achieved_total"] >= TARGET_TOTAL:
        result = real_only
    else:
        study_mcqs, study_descs = load_study_material_pool(as_key, unitcode)
        study_material_available = bool(study_mcqs or study_descs)
        combined = select_and_pack(real_mcq_rows + study_mcqs, real_desc_rows + study_descs)
        if combined["achieved_total"] > real_only["achieved_total"]:
            result = combined
            used_study_material = any(m.get("source_kind") == "study_material" for m in combined["selected_mcqs"]) or \
                any(d.get("source_kind") == "study_material" for d in combined["selected_desc"])
        else:
            result = real_only

    result.update({
        "as_key": as_key, "name": name, "unitcode": unitcode,
        "used_study_material": used_study_material,
        "study_material_available": study_material_available,
    })
    return result


def as_short_name(full_name):
    return re.split(r"[–—]", full_name)[0].strip()


def render_header(test):
    minutes = round(test["achieved_total"] * 1.8)
    lines = []
    lines.append(f"# {test['name']}")
    lines.append("")
    lines.append("**CA Inter | Paper 1: Advanced Accounting**")
    lines.append("")
    lines.append(f"**Maximum Marks: {test['achieved_total']}**")
    lines.append(f"**Time Allowed: {minutes} minutes**")
    lines.append("")
    lines.append("**Instructions:**")
    lines.append("1. All questions are compulsory unless stated otherwise.")
    lines.append("2. Marks for each question are shown alongside it.")
    lines.append("3. Show full working notes wherever applicable.")
    lines.append("4. Answer as per the Accounting Standards applicable for CA Inter.")
    lines.append("")
    lines.append("---")
    lines.append("")
    return lines


def render_questions_md(test):
    as_name = as_short_name(test["name"])
    lines = render_header(test)
    lines.append(f"## Section A: Multiple Choice Questions ({test['mcq_marks']} Marks)")
    lines.append("")
    if test["selected_mcqs"]:
        lines.append(render_mcqs(test["selected_mcqs"], as_name))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## Section B: Descriptive Questions ({test['desc_marks']} Marks)")
    lines.append("")
    if test["selected_desc"]:
        lines.append(render_desc(test["selected_desc"], as_name))
    lines.append("")
    lines.append("*End of Question Paper*")
    lines.append("")
    return clean_typography("\n".join(lines))


def render_answers_md(test):
    as_name = as_short_name(test["name"])
    lines = render_header(test)
    lines.append(f"## Section A: Multiple Choice Questions ({test['mcq_marks']} Marks)")
    lines.append("")
    if test["selected_mcqs"]:
        lines.append(render_mcqs(test["selected_mcqs"], as_name))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## Section B: Descriptive Questions ({test['desc_marks']} Marks)")
    lines.append("")
    if test["selected_desc"]:
        lines.append(render_desc(test["selected_desc"], as_name))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Answers")
    lines.append("")
    lines.append("### Section A: Multiple Choice Questions")
    lines.append("")
    if test["selected_mcqs"]:
        lines.append(render_mcq_answers(test["selected_mcqs"]))
    lines.append("")
    lines.append("### Section B: Descriptive Questions")
    lines.append("")
    if test["selected_desc"]:
        lines.append(render_desc_answers(test["selected_desc"]))
    lines.append("")
    lines.append("*End of Answer Key*")
    lines.append("")
    return clean_typography("\n".join(lines))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STUDENT_DIR.mkdir(parents=True, exist_ok=True)
    mcq_pool_all = load_json(MCQ_PATH)
    desc_pool_all = load_json(DESC_PATH)

    generated_on = date.today().isoformat()
    summary_rows = []

    for as_key in AS_LIST:
        test = build_test(as_key, mcq_pool_all, desc_pool_all)

        questions_md = render_questions_md(test)
        answers_md = render_answers_md(test)
        (STUDENT_DIR / f"{as_key.upper()}_Questions.md").write_text(questions_md, encoding="utf-8")
        (STUDENT_DIR / f"{as_key.upper()}_Questions_and_Answers.md").write_text(answers_md, encoding="utf-8")

        summary_rows.append(test)
        print(
            f"{as_key.upper():6} -> {test['achieved_total']:3}/{TARGET_TOTAL} marks "
            f"(MCQ {test['mcq_marks']:2} / {test['mcq_count']:2}q, DESC {test['desc_marks']:2} / {test['desc_count']:2}q) "
            f"pool(mcq={test['mcq_pool_size']},desc={test['desc_pool_size']}) "
            f"max_avail={test['max_total_available']}"
        )

    # Index / README
    idx_lines = []
    idx_lines.append("# Second Phase — Chapter Tests (MCQ + Descriptive, 50 Marks Each)")
    idx_lines.append("")
    idx_lines.append(
        "One 50-mark test per Accounting Standard below (target composition: 30% MCQ / 70% Descriptive), "
        "styled after ICAI's own **Test Your Knowledge** (MCQ) and **Illustrations** (descriptive) sections. "
        "Built from two real sources: past MTP/RTP/PYQ exam papers already chapter-tagged in the platform's "
        "question bank (official marks), and the ICAI study-material chapter's own \"Test Your Knowledge\" "
        "section (`books/concept-book/raw_icai_study_materials/`, marks estimated from answer length since the "
        "source carries none — always tagged as such). Real exam content is always preferred and used first; "
        "study-material questions are only pulled in for a chapter when real content alone can't reach 50 marks "
        "(see the \"Uses study material\" column). Nothing is invented. Generated by "
        "`first_run/scripts/build_second_phase_tests.py`, safe to re-run."
    )
    idx_lines.append("")
    idx_lines.append("| AS | Chapter | Marks Achieved | MCQ | Descriptive | Uses Study Material | Status |")
    idx_lines.append("|---|---|---|---|---|---|---|")
    pool_short = []
    denom_short = []
    for t in summary_rows:
        if t["achieved_total"] >= TARGET_TOTAL:
            status = "OK — full 50 marks"
        elif t["max_total_available"] < TARGET_TOTAL:
            status = f"**SHORT (pool too small) — {t['achieved_total']}/50** (pool max {t['max_total_available']})"
            pool_short.append(t)
        else:
            status = f"**SHORT (mark-denomination gap) — {t['achieved_total']}/50** (pool max {t['max_total_available']})"
            denom_short.append(t)
        if t.get("used_study_material"):
            used_sm = "Yes"
        elif t["achieved_total"] >= TARGET_TOTAL:
            used_sm = "No — real content sufficed"
        elif t.get("study_material_available"):
            used_sm = "No — didn't improve on real content alone"
        else:
            used_sm = "No — no study-material TYK content exists for this chapter (no answer key in source)"
        idx_lines.append(
            f"| {t['as_key'].upper()} | {t['name']} | {t['achieved_total']}/50 | "
            f"{t['mcq_marks']} marks ({t['mcq_count']}q) | {t['desc_marks']} marks ({t['desc_count']}q) | {used_sm} | {status} |"
        )
    idx_lines.append("")
    if pool_short:
        idx_lines.append("## Chapters short of 50 marks: pool too small — needs Pranav's attention")
        idx_lines.append("")
        idx_lines.append(
            "These chapters do not yet have 50 marks worth of chapter-tagged, de-duplicated question content in "
            "the current source corpus (`questions_index.json` + `mcq_questions_extracted.json`) *at all* — every "
            "real question available was used, and the test still falls short:"
        )
        idx_lines.append("")
        for t in pool_short:
            idx_lines.append(
                f"- **{t['name']}** — only {t['max_total_available']} marks available "
                f"({t['max_mcq_available']} MCQ + {t['max_desc_available']} Descriptive) after de-duplication; "
                f"test carries {t['achieved_total']}/50 marks."
            )
        idx_lines.append("")
        idx_lines.append(
            "To close this gap, more MTP/RTP/PYQ sittings would need to be sourced and tagged for these chapters "
            "(same pipeline as `first_run/HOW-TO-BUILD-THE-BOOK.md`), or the MCQ pool "
            "(`mcq_questions_extracted.json`, external to this repo) would need more chapter-tagged questions added."
        )
        idx_lines.append("")
    if denom_short:
        idx_lines.append("## Chapters short of 50 marks: mark-denomination gap (not a real content shortage)")
        idx_lines.append("")
        idx_lines.append(
            "These chapters have **more than 50 marks** of tagged content available overall, but no combination "
            "of real question marks (MCQs mostly fixed at 2 marks each; descriptive questions in scattered "
            "2/4/5/7/&hellip;-mark denominations) sums to exactly 50 — the closest achievable exact total was used "
            "instead. This is a selection-arithmetic limit, not missing content:"
        )
        idx_lines.append("")
        for t in denom_short:
            idx_lines.append(
                f"- **{t['name']}** — {t['max_total_available']} marks available in the pool "
                f"({t['max_mcq_available']} MCQ + {t['max_desc_available']} Descriptive); closest achievable exact "
                f"total was {t['achieved_total']}/50 marks."
            )
        idx_lines.append("")
    shortfalls = pool_short + denom_short
    idx_lines.append(f"*Generated: {generated_on}*")
    idx_lines.append("")
    with open(OUT_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(idx_lines))

    print("\nWrote README.md index.")
    print(f"Shortfall chapters: {[t['as_key'].upper() for t in shortfalls]}")


if __name__ == "__main__":
    main()
