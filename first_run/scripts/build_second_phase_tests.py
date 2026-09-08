"""
build_second_phase_tests.py
============================
Generates one 50-mark, single-AS chapter test per accounting standard in
SECOND_PHASE_AS_LIST, in Markdown, styled after ICAI's own "Test Your
Knowledge" (MCQs) + "Illustrations" (descriptive problems) sections rather
than a formal exam-paper cover sheet.

Sources (read-only, never modified):
  - Descriptive: first_run/output/generated-from-script/questions_index.json
  - MCQ:         <MCQ_JSON_PATH> (examstudyhub's mcq_questions_extracted.json)

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
from pathlib import Path
from datetime import date

REPO_ROOT = Path(r"D:\EffCorp_Projects\cap-online")
DESC_PATH = REPO_ROOT / "first_run" / "output" / "generated-from-script" / "questions_index.json"
MCQ_PATH = Path(r"D:\EffCorp_Products\Main1Lavya\Main1lavyaAIAgents\examstudyhub\assets\exam_bot\mcq_questions_extracted.json")
OUT_DIR = REPO_ROOT / "first_run" / "TESTS" / "second phase"

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


def norm_fingerprint(html):
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\d+", "#", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text[:400]


def dedup(rows, html_field):
    """De-duplicate on (case facts + question) text, not question text alone -
    several case-based MCQs share a generic question stem ('what will be the
    cost of material') across genuinely different case scenarios (different
    figures in case_facts_html), so case_facts_html must be part of the
    fingerprint or distinct questions get wrongly merged."""
    seen = set()
    kept = []
    skipped = 0
    for r in rows:
        fp = norm_fingerprint(r.get("case_facts_html", "") or "") + "||" + norm_fingerprint(r.get(html_field))
        if fp and fp in seen:
            skipped += 1
            continue
        if fp:
            seen.add(fp)
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
    among all subsets achieving that sum (0/1 knapsack, exact-sum first)."""
    target = max(0, target)
    NEG = -1
    dp = [NEG] * (target + 1)
    dp[0] = 0
    choice = [None] * (target + 1)  # choice[s] = (prev_sum, item_index) that reached s
    for idx, (_key, w) in enumerate(items):
        if w <= 0 or w > target:
            continue
        for s in range(target, w - 1, -1):
            if dp[s - w] != NEG and dp[s - w] + 1 > dp[s]:
                dp[s] = dp[s - w] + 1
                choice[s] = (s - w, idx)
    # find best reachable sum, preferring the largest sum <= target
    best_sum = 0
    for s in range(target, -1, -1):
        if dp[s] != NEG:
            best_sum = s
            break
    keys = []
    s = best_sum
    while s > 0 and choice[s] is not None:
        prev, idx = choice[s]
        keys.append(items[idx][0])
        s = prev
    return best_sum, keys


def build_options_md(options):
    lines = []
    for letter in sorted(options.keys()):
        lines.append(f"- **({letter})** {options[letter]}")
    return "\n".join(lines)


def source_label_mcq(m):
    bits = [m.get("exam_type") or "", m.get("year") or "", f"Set {m['set']}" if m.get("set") else "", m.get("qno_text") or ""]
    return " ".join(b for b in bits if b).strip()


def source_label_desc(d):
    pt = d.get("paper_type") or ""
    yr = d.get("exam_year") or ""
    st = f"Set {d['set']}" if d.get("set") else ""
    qno = d.get("qno") or d.get("parent_qno") or ""
    sub = d.get("subpart") or ""
    qlabel = f"Q{qno}{sub}" if qno else ""
    bits = [pt, yr, st, qlabel]
    return " ".join(b for b in bits if b).strip()


def topics_label(d):
    topics = d.get("topics") or []
    labels = [t.get("label") for t in topics if t.get("label")]
    return "; ".join(labels) if labels else "—"


def render_mcq_section(selected_mcqs):
    out = []
    shown_cases = set()
    for i, m in enumerate(selected_mcqs, 1):
        case_ref = m.get("case_ref")
        if case_ref and m.get("case_facts_html") and case_ref not in shown_cases:
            out.append(f"\n*Case Facts (Case {case_ref}):*\n")
            out.append(m["case_facts_html"])
            out.append("")
            shown_cases.add(case_ref)
        out.append(f"**{i}.** {m.get('question_html', '')}")
        out.append("")
        out.append(build_options_md(m.get("options", {})))
        out.append("")
        marks = m.get("marks", 2)
        out.append(f"*({marks} Marks · Topic: {m.get('topic_text', '—')} · Source: {source_label_mcq(m)})*")
        out.append("")
    return "\n".join(out)


def render_mcq_answers(selected_mcqs):
    out = []
    for i, m in enumerate(selected_mcqs, 1):
        out.append(f"**{i}.** Correct Option: **({m.get('correct_option', '?')})**")
        out.append("")
        out.append(m.get("answer_html", ""))
        out.append("")
    return "\n".join(out)


def render_desc_section(selected_desc):
    out = []
    for i, d in enumerate(selected_desc, 1):
        if d.get("case_facts_html"):
            out.append(f"\n*Case Facts:*\n")
            out.append(d["case_facts_html"])
            out.append("")
        out.append(f"**Q{i}.** {d.get('question_html', '')}")
        out.append("")
        marks = d.get("marks", "?")
        out.append(f"*({marks} Marks · Topic: {topics_label(d)} · Source: {source_label_desc(d)})*")
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
            label = "Examiner's Comment (ICAI)" if src == "icai" else "Author's Note (Synthesized — not ICAI-sourced)"
            out.append(f"> **{label}:** {ec['text']}")
            out.append("")
    return "\n".join(out)


def build_test(as_key, mcq_pool_all, desc_pool_all):
    unitcode = CHAPTER_MAP[as_key]
    name = AS_NAME[as_key]

    mcq_rows = [m for m in mcq_pool_all if m.get("chapter_slug") == as_key and isinstance(m.get("marks"), int)]
    # questions_index.json also tags the Part I MCQs of these same papers (qtype
    # 'mcq'/'case-mcq') - confirmed by identical id strings against mcq_id in
    # mcq_questions_extracted.json (e.g. CAI-P1-MTP-2025-01-S2-PI-Q1 appears in
    # both). Section A already draws on that same MCQ content via the dedicated
    # MCQ pool, so Section B must exclude qtype mcq/case-mcq or the same
    # questions would be double-counted as "descriptive".
    desc_rows = [
        d for d in desc_pool_all
        if d.get("final_chapter") == unitcode
        and d.get("qtype") in ("practical", "theory")
        and isinstance(d.get("marks"), int) and d.get("marks", 0) > 0
    ]

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
        "as_key": as_key, "name": name, "unitcode": unitcode,
        "mcq_marks": mcq_marks_used, "desc_marks": desc_marks_used, "achieved_total": achieved_total,
        "mcq_count": len(selected_mcqs), "desc_count": len(selected_desc),
        "selected_mcqs": selected_mcqs, "selected_desc": selected_desc,
        "max_mcq_available": max_mcq_available, "max_desc_available": max_desc_available,
        "max_total_available": max_total_available,
        "mcq_dupes_removed": mcq_dupes, "desc_dupes_removed": desc_dupes,
        "mcq_pool_size": len(mcq_rows), "desc_pool_size": len(desc_rows),
    }


def render_md(test, generated_on):
    as_key = test["as_key"]
    shortfall = test["achieved_total"] < TARGET_TOTAL
    mcq_pct = round(100 * test["mcq_marks"] / test["achieved_total"]) if test["achieved_total"] else 0
    desc_pct = 100 - mcq_pct if test["achieved_total"] else 0

    lines = []
    lines.append(f"# {test['name']} — Chapter Test (Second Phase)")
    lines.append("")
    lines.append("**CA Inter · Paper 1: Advanced Accounting**")
    lines.append(f"**Chapter Reference:** `{test['unitcode']}`")
    lines.append("")
    lines.append(
        f"**Maximum Marks (target):** {TARGET_TOTAL} &nbsp;|&nbsp; **Marks Achieved:** {test['achieved_total']} "
        f"&nbsp;|&nbsp; **Section A (MCQ):** {test['mcq_marks']} marks, {test['mcq_count']} questions ({mcq_pct}%) "
        f"&nbsp;|&nbsp; **Section B (Descriptive):** {test['desc_marks']} marks, {test['desc_count']} questions ({desc_pct}%)"
    )
    lines.append("")
    suggested_minutes = round(test["achieved_total"] * 1.8)
    lines.append(f"**Suggested Time:** ~{suggested_minutes} minutes")
    lines.append("")
    lines.append(
        "> This test paper is compiled in the style of ICAI's own **\"Test Your Knowledge\"** (MCQ) and "
        "**\"Illustrations\"** (descriptive) sections — questions grouped together, solutions given together "
        "at the end. Every question below is a real, previously chapter-tagged MTP / RTP / PYQ question drawn "
        "from the platform's question bank (`first_run/output/generated-from-script/questions_index.json` for "
        "descriptive, `mcq_questions_extracted.json` for MCQ). Nothing is invented."
    )
    lines.append(">")
    if shortfall:
        chapter_short_name = test["name"].split(chr(8212))[0].strip()
        if test["max_total_available"] < TARGET_TOTAL:
            lines.append(
                f"> **Content note — target not fully met (pool too small):** the tagged question pool currently "
                f"available for {chapter_short_name} in this corpus totals only **{test['max_total_available']} marks** "
                f"({test['max_mcq_available']} MCQ + {test['max_desc_available']} Descriptive) after de-duplication — short "
                f"of the 50-mark target. All available real content has been included below (**{test['achieved_total']} of "
                f"50 marks**); no question was invented or borrowed from another chapter to pad the total. More MTP/RTP/PYQ "
                f"sittings would need to be sourced and tagged for this chapter to reach a full 50-mark paper."
            )
        else:
            lines.append(
                f"> **Content note — target not fully met (mark-denomination gap, not a content shortage):** "
                f"{chapter_short_name}'s tagged pool has **{test['max_total_available']} marks** available in total "
                f"({test['max_mcq_available']} MCQ + {test['max_desc_available']} Descriptive) — enough to reach 50 — but no "
                f"combination of real question marks (MCQs mostly in fixed 2-mark units, descriptive in "
                f"2/4/5/7/&hellip;-mark units) sums to exactly 50 while keeping a reasonable MCQ:Descriptive split. The "
                f"closest achievable exact total was selected instead: **{test['achieved_total']} of 50 marks**. No question "
                f"was invented to force an exact 50."
            )
        lines.append(">")
    lines.append(
        "> **Duplicate-check note:** exact-duplicate question text (the same question re-tagged from more than one "
        "sitting) was removed before selection "
        f"({test['mcq_dupes_removed']} MCQ + {test['desc_dupes_removed']} Descriptive duplicate(s) skipped for this chapter). "
        "This is a same-text guard only — the platform's fuller ≥90%-similarity Original/Practice-question (OP/PP) "
        "detection is still unbuilt (see CLAUDE.md §6), so near-duplicate variants (same structure, different figures) "
        "may still appear."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## Section A — Multiple Choice Questions *(Test Your Knowledge style)* — {test['mcq_marks']} Marks")
    lines.append("")
    if test["selected_mcqs"]:
        lines.append(render_mcq_section(test["selected_mcqs"]))
    else:
        lines.append("*No MCQs were available in the tagged pool for this chapter.*")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## Section B — Descriptive Questions *(Illustrations style)* — {test['desc_marks']} Marks")
    lines.append("")
    if test["selected_desc"]:
        lines.append(render_desc_section(test["selected_desc"]))
    else:
        lines.append("*No descriptive questions were available in the tagged pool for this chapter.*")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Answers")
    lines.append("")
    lines.append("### Section A — MCQ Answer Key & Explanations")
    lines.append("")
    if test["selected_mcqs"]:
        lines.append(render_mcq_answers(test["selected_mcqs"]))
    else:
        lines.append("*N/A*")
    lines.append("")
    lines.append("### Section B — Descriptive Solutions")
    lines.append("")
    if test["selected_desc"]:
        lines.append(render_desc_answers(test["selected_desc"]))
    else:
        lines.append("*N/A*")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "**Provenance note:** boxes marked *Examiner's Comment (ICAI)* reproduce/paraphrase a real ICAI Examiner's "
        "Comment on that exact question. Boxes marked *Author's Note (Synthesized)* are written in ICAI's voice per "
        "this platform's `examiner-comments-writing-skill.md` style guide but are **not** ICAI-sourced, and may not "
        "apply in every case."
    )
    lines.append("")
    lines.append(f"*Generated: {generated_on} · First edition — please report any error to Pranav.*")
    lines.append("")
    return "\n".join(lines)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mcq_pool_all = load_json(MCQ_PATH)
    desc_pool_all = load_json(DESC_PATH)

    generated_on = date.today().isoformat()
    summary_rows = []

    for as_key in AS_LIST:
        test = build_test(as_key, mcq_pool_all, desc_pool_all)
        md = render_md(test, generated_on)
        out_path = OUT_DIR / f"{as_key.upper()}_Test.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
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
        "Built entirely from real, already chapter-tagged questions in the platform's question bank — nothing "
        "invented. Generated by `first_run/scripts/build_second_phase_tests.py`, safe to re-run."
    )
    idx_lines.append("")
    idx_lines.append("| AS | Chapter | Marks Achieved | MCQ | Descriptive | Status |")
    idx_lines.append("|---|---|---|---|---|---|")
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
        idx_lines.append(
            f"| {t['as_key'].upper()} | {t['name']} | {t['achieved_total']}/50 | "
            f"{t['mcq_marks']} marks ({t['mcq_count']}q) | {t['desc_marks']} marks ({t['desc_count']}q) | {status} |"
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
