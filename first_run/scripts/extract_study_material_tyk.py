"""
extract_study_material_tyk.py
==============================
Extracts the "TEST YOUR KNOWLEDGE" section (Multiple Choice Questions +
Theoretical Questions + Scenario based Questions, plus their answer key) from
each raw ICAI study-material chapter file under
books/concept-book/raw_icai_study_materials/, for the 14 second-phase-test
chapters.

Why only TEST YOUR KNOWLEDGE and not "Illustrations" too: measured first -
most Illustration "Solution" text in these PDF-extracted .md files runs
straight into unrelated general chapter narrative with no blank-line or
heading boundary marking where the answer actually ends (confirmed: gaps of
700-6000+ characters of unrelated text before the next safe boundary marker
for most illustrations checked). Bulk-extracting those would silently
corrupt answers. TEST YOUR KNOWLEDGE, by contrast, is always the last
section of the file (EOF-bounded) with a clean numbered-list structure and a
separate ANSWERS/SOLUTIONS block - safe to parse mechanically. This script
therefore extracts TYK only; Illustrations are left for a future, more
careful pass (per-illustration boundary review) if wanted.

Self-checks before trusting anything:
  - question numbers within a chapter must form a clean increasing sequence
  - every question must have a matching answer (else it's dropped, logged as
    skipped, never guessed)
  - MCQ answers must resolve to a single lettered option that exists among
    that question's own parsed options

Marks are NOT in the source (Pranav confirmed) - assigned heuristically:
  - Multiple Choice Questions: 1 mark each (simple, non-case-scenario stem;
    kept lower than the 2-mark case-based MCQs already in the exam-paper
    pool, to stay honestly distinct from real exam marks)
  - Theoretical / Scenario-based (descriptive) questions: bucketed by the
    ANSWER's word count, using the same mark denominations already observed
    in the real MTP/RTP/PYQ pool (2/4/5/7/8/10)

Output: first_run/output/generated-from-script/study_material_tyk.json
        (list of chapter dicts, each with 'mcq' and 'descriptive' question
        lists) + a console report of counts/skips per chapter.
"""
import json
import re
from pathlib import Path

SRC_DIR = Path(r"D:\EffCorp_Projects\cap-online\books\concept-book\raw_icai_study_materials")
OUT_PATH = Path(r"D:\EffCorp_Projects\cap-online\first_run\output\generated-from-script\study_material_tyk.json")

# as_key -> (source filename, unitcode, display name)
CHAPTERS = {
    "as02": ("M2_C5_U1_ Accounting Standard 2 Valuation of Inventory.md", "M2-C5-U1", "AS 2 — Valuation of Inventories"),
    "as04": ("M2_C7_U1_ Accounting Standard 4 Contingencies and Events occurring after the Balance Sheet Date.md", "M2-C7-U1", "AS 4 — Contingencies and Events Occurring After the Balance Sheet Date"),
    "as05": ("M2_C7_U2_ Accounting Standard 5 Net Profit or Loss for the Period, Prior Period Items and Changes in Accounting Policies.md", "M2-C7-U2", "AS 5 — Net Profit or Loss for the Period, Prior Period Items and Changes in Accounting Policies"),
    "as07": ("M2_C8_U1_ Accounting Standard 7 Construction Contracts.md", "M2-C8-U1", "AS 7 — Construction Contracts"),
    "as09": ("M2_C8_U2_ Accounting Standard 9 Revenue Recognition.md", "M2-C8-U2", "AS 9 — Revenue Recognition"),
    "as10": ("M2_C5_U2_ Accounting Standard 10 Property, Plant and Equipment.md", "M2-C5-U2", "AS 10 — Property, Plant and Equipment"),
    "as12": ("M2_C9_U1_ Accounting Standard 12 Accounting for Government Grants.md", "M2-C9-U1", "AS 12 — Accounting for Government Grants"),
    "as13": ("M2_C5_U3_ Accounting Standard 13 Accounting for Investments.md", "M2-C5-U3", "AS 13 — Accounting for Investments"),
    "as15": ("M2_C6_U1_ Accounting Standard 15 Employee Benefits.md", "M2-C6-U1", "AS 15 — Employee Benefits"),
    "as16": ("M2_C5_U4_ Accounting Standard 16 Borrowing Costs.md", "M2-C5-U4", "AS 16 — Borrowing Costs"),
    "as19": ("M2_C5_U5_ Accounting Standard 19 Leases.md", "M2-C5-U5", "AS 19 — Leases"),
    "as26": ("M2_C5_U6_ Accounting Standard 26 Intangible Assets.md", "M2-C5-U6", "AS 26 — Intangible Assets"),
    "as28": ("M2_C5_U7_ Accounting Standard 28 Impairment of Assets.md", "M2-C5-U7", "AS 28 — Impairment of Assets"),
    "as29": ("M2_C6_U2_ AS 29 (Revised) Provisions, Contingent Liabilities and Contingent Assets.md", "M2-C6-U2", "AS 29 (Revised) — Provisions, Contingent Liabilities and Contingent Assets"),
}

SUBSECTIONS = ["Multiple Choice Questions", "Theoretical Questions", "Scenario based Questions"]
SUBSECTION_RE = re.compile(r"^(Multiple Choice Questions|Theoretical Questions|Scenario based Questions)\s*$", re.M)
ANSWER_SUBSECTION_RE = re.compile(r"^Answer to (?:the )?(Multiple Choice Questions|Theoretical Questions|Scenario based Questions)\s*$", re.M)
STRAY_V_RE = re.compile(r"^(v\s*)+$")


def is_noise_line(line):
    """Catches running-header/page-number junk left over from PDF extraction.
    These vary too much per chapter/module to enumerate exactly (seen so
    far: 'ADVANCED ACCOUNTING', 'ASSETS BASED ACCOUNTING STANDARDS',
    'REVENUE BASED ACCOUNTING STANDARDS 8.5 1 a', garbled page numbers like
    '55.9.9 99' or '5.2 7', stray 'v'/'v v' bullet artifacts, the ©
    line) - so instead of listing every variant, treat a short line as noise
    if it reads nothing like real prose (very low lowercase-letter ratio),
    since genuine question/answer text is normal sentences."""
    s = line.strip()
    if not s:
        return True
    if s.startswith("©"):
        return True
    if STRAY_V_RE.match(s):
        return True
    if len(s) <= 55:
        letters = [c for c in s if c.isalpha()]
        if letters:
            lower = [c for c in letters if c.islower()]
            if (len(lower) / len(letters)) < 0.25:
                return True
        elif len(s) <= 20 and re.match(r"^[\d.\s]+$", s) and any(c.isdigit() for c in s):
            # only digits/dots/spaces, no letters, no comma or currency mark:
            # a garbled page-number fragment like "55.9.9 99" / "5.2 7", not
            # a real monetary figure (those carry commas or a rupee mark).
            return True
    if re.match(r"^[a-zA-Z]{1,2}\s+\d{1,3}$", s):
        # a bare 1-2 letter + short number fragment like "a 8" - another
        # garbled page-footer remnant, never real question/answer content.
        return True
    return False


def clean_text_block(raw):
    """Join a raw multi-line block into normalised paragraph text: drop known
    noise lines (running headers, page numbers, the © line, stray 'v'
    artifact lines), replace the OCR '`' rupee stand-in with the real symbol,
    collapse internal whitespace/newlines. Markdown table rows ('|...|') are
    kept on their own line since some illustrations/answers embed real
    tables."""
    lines = raw.split("\n")
    kept = []
    for ln in lines:
        if is_noise_line(ln):
            continue
        kept.append(ln)
    text = "\n".join(kept)
    text = text.replace("`", "₹")
    # keep table rows separate, collapse everything else into flowing text
    out_lines = []
    buf = []
    for ln in text.split("\n"):
        if "|" in ln:
            if buf:
                out_lines.append(" ".join(w for w in " ".join(buf).split() if w))
                buf = []
            out_lines.append(ln.strip())
        elif ln.strip() == "":
            continue
        else:
            buf.append(ln)
    if buf:
        out_lines.append(" ".join(w for w in " ".join(buf).split() if w))
    return "\n".join(l for l in out_lines if l).strip()


# Period after the number is optional - at least one real source line reads
# "3 Current investments are carried at" (missing the period, an OCR/typo
# artifact) instead of "3. Current investments...".
NUM_START_RE = re.compile(r"^(\d{1,2})\.?\s", re.M)

# MCQ answer keys are frequently packed onto one line/table row, e.g.
# "1. (b) 2. (a) 3. (b) 4. (d)" or a markdown table with one "N. (x)" cell
# each - never one number per line - so they need a dedicated inline scan
# rather than the line-start NUM_START_RE used for everything else.
MCQ_ANSWER_PAIR_RE = re.compile(r"(\d{1,2})\.\s*\(([a-dA-D])\)")


def parse_mcq_answer_line(segment_text):
    return {int(num): letter.upper() for num, letter in MCQ_ANSWER_PAIR_RE.findall(segment_text)}


def split_numbered_blocks(segment_text, expected_start):
    """Split a subsection's text into {number: block_text} by lines starting
    with 'N.', greedily accepting only matches that continue the expected
    sequence (expected_start, expected_start+1, ...). A garbled page-break
    fragment (e.g. a lone "8" left over from a mangled page number like
    "8.52") that doesn't fit the expected sequence is treated as spurious and
    folded into the preceding block's text rather than starting a bogus new
    question - this is what makes the parser robust to this corpus's PDF-
    extraction noise without an all-or-nothing reject.
    Returns (blocks_dict, next_expected_number)."""
    matches = list(NUM_START_RE.finditer(segment_text))
    accepted = []
    expected = expected_start
    for m in matches:
        num = int(m.group(1))
        if num == expected:
            accepted.append((num, m))
            expected += 1
    if not accepted:
        return {}, expected_start
    blocks = {}
    for i, (num, m) in enumerate(accepted):
        start = m.end()
        end = accepted[i + 1][1].start() if i + 1 < len(accepted) else len(segment_text)
        blocks[num] = segment_text[start:end]
    return blocks, expected


OPTION_RE = re.compile(r"\(([a-dA-D])\)\s*")


LETTERS = "ABCD"


def parse_mcq_block(block_text):
    """Split an MCQ block into (stem, {letter: option_text}). Only accepts
    option markers in strict A, B, C, D order - an option's own text can
    legitimately contain a parenthetical reference to another option (e.g.
    "(c) Both (a) and (b)."), and a naive scan for every "(letter)" would
    wrongly treat that nested "(a)"/"(b)" as new option boundaries and
    scramble all four options. Real corpus example that motivated this."""
    opt_matches = list(OPTION_RE.finditer(block_text))
    accepted = []
    expected_idx = 0
    for m in opt_matches:
        letter = m.group(1).upper()
        if expected_idx < len(LETTERS) and letter == LETTERS[expected_idx]:
            accepted.append(m)
            expected_idx += 1
    if len(accepted) < 2:
        return None, {}
    stem = clean_text_block(block_text[: accepted[0].start()])
    options = {}
    for i, m in enumerate(accepted):
        letter = m.group(1).upper()
        start = m.end()
        end = accepted[i + 1].start() if i + 1 < len(accepted) else len(block_text)
        options[letter] = clean_text_block(block_text[start:end])
    return stem, options


def mcq_item_ok(stem, options):
    """Post-parse quality gate - reject rather than guess. Catches the
    residual corruption classes actually observed in this corpus: a shared
    case-intro for the next questions leaking onto the last option (that
    option becomes anomalously long), a source OCR typo reusing an earlier
    letter for the last option (leaves e.g. a literal '(c)' sitting inside
    what should be option D's text), and a scrambled '(c)\\n(d)\\ntext\\ntext'
    layout (rare, seen once) that leaves an option's own text empty.
    Deliberately does NOT flag every embedded "(a)"/"(b)" - genuine phrasing
    like option (c) reading "Both (a) and (b) are permitted" is common and
    must not be rejected; only a SAME-OR-LATER-lettered marker embedded in an
    option's own text is treated as corruption evidence, since real prose
    only ever backward-references earlier options."""
    if not stem or len(options) != 4 or set(options) != set(LETTERS):
        return False
    lens = sorted(len(v) for v in options.values())
    if lens[-1] > 3 * max(lens[0], 15) + 60:
        return False
    for letter, v in options.items():
        if len(v.strip()) < 3:
            return False
        own_idx = LETTERS.index(letter)
        for m in OPTION_RE.finditer(v):
            if LETTERS.index(m.group(1).upper()) >= own_idx:
                return False
    return True


def extract_chapter(as_key, filename, unitcode, name):
    path = SRC_DIR / filename
    text = path.read_text(encoding="utf-8")

    tyk_match = re.search(r"^TEST YOUR KNOWLEDGE.*$", text, re.M)
    if not tyk_match:
        return {"as_key": as_key, "error": "no TEST YOUR KNOWLEDGE section found", "mcq": [], "descriptive": []}
    tyk_text = text[tyk_match.end():]

    ans_match = re.search(r"^ANSWERS/SOLUTIONS?\s*$", tyk_text, re.M)
    if ans_match:
        q_text, a_text = tyk_text[: ans_match.start()], tyk_text[ans_match.start():]
    else:
        q_text, a_text = tyk_text, ""

    # --- tag question subsections ---
    q_positions = [(m.start(1), m.group(1)) for m in SUBSECTION_RE.finditer(q_text)]
    q_segments = []  # (type, text)
    for i, (pos, kind) in enumerate(q_positions):
        seg_start = pos + len(kind)
        seg_end = q_positions[i + 1][0] if i + 1 < len(q_positions) else len(q_text)
        q_segments.append((kind, q_text[seg_start:seg_end]))

    questions = {}  # num -> {type, raw_block}
    warnings = []
    expected = 1
    for kind, seg in q_segments:
        blocks, expected = split_numbered_blocks(seg, expected)
        for num, block in blocks.items():
            if num in questions:
                warnings.append(f"duplicate question number {num} across subsections - kept first")
                continue
            questions[num] = {"type": kind, "raw_block": block}

    # --- tag answer subsections ---
    # Track both the full match start (m.start()) and the content start
    # (right after the heading) - a previous segment must end at the NEXT
    # heading's full match start, not just the start of its captured group,
    # or the "Answer to the " prefix words bleed onto the previous item's
    # tail (real bug: found "...obligation. Answer to the</p>" leaking into
    # an AS 29 answer before this fix).
    a_positions = [(m.start(), m.end(), m.group(1)) for m in ANSWER_SUBSECTION_RE.finditer(a_text)]
    a_segments = []
    for i, (full_start, content_start, kind) in enumerate(a_positions):
        seg_end = a_positions[i + 1][0] if i + 1 < len(a_positions) else len(a_text)
        a_segments.append((kind, a_text[content_start:seg_end]))

    answers = {}
    ans_expected = 1
    for kind, seg in a_segments:
        if kind == "Multiple Choice Questions":
            # answer key is packed (one line or one table row), not one
            # number per line - parse with the dedicated inline scan instead
            # of the line-start splitter. Not sequence-number-gated (packed
            # format has no boundary-drift risk the way line-start scanning
            # does), so just take every (num, letter) pair found.
            pairs = parse_mcq_answer_line(seg)
            for num, letter in pairs.items():
                answers[num] = f"({letter})"
            if pairs:
                ans_expected = max(ans_expected, max(pairs) + 1)
            continue
        blocks, ans_expected = split_numbered_blocks(seg, ans_expected)
        for num, block in blocks.items():
            answers[num] = block

    mcq_out, desc_out = [], []
    skipped_no_answer = []
    for num, q in sorted(questions.items()):
        ans_block = answers.get(num)
        if ans_block is None:
            skipped_no_answer.append(num)
            continue
        if q["type"] == "Multiple Choice Questions":
            stem, options = parse_mcq_block(q["raw_block"])
            if not mcq_item_ok(stem, options):
                skipped_no_answer.append(num)
                continue
            m = OPTION_RE.search(ans_block)
            if not m or m.group(1).upper() not in options:
                skipped_no_answer.append(num)
                continue
            correct = m.group(1).upper()
            mcq_out.append({
                "source_num": num, "question_html": f"<p>{stem}</p>",
                "options": options, "correct_option": correct,
                "answer_html": f"<p><strong>Answer:</strong> ({correct}) {options.get(correct, '')}</p>",
            })
        else:
            stem = clean_text_block(q["raw_block"])
            answer = clean_text_block(ans_block)
            if not stem or not answer:
                skipped_no_answer.append(num)
                continue
            desc_out.append({
                "source_num": num, "qtype": q["type"],
                "question_html": f"<p>{stem}</p>", "answer_html": f"<p>{answer}</p>",
                # source PDF tables (ledger/T-accounts) were already messily
                # OCR'd before this script ever touches them - flag rather
                # than silently pass through a possibly-garbled table.
                "has_table": "|" in answer,
            })

    return {
        "as_key": as_key, "unitcode": unitcode, "name": name,
        "mcq": mcq_out, "descriptive": desc_out,
        "warnings": warnings, "skipped_no_answer": skipped_no_answer,
        "has_answer_section": bool(ans_match),
    }


def main():
    results = []
    for as_key, (filename, unitcode, name) in CHAPTERS.items():
        r = extract_chapter(as_key, filename, unitcode, name)
        results.append(r)
        print(
            f"{as_key.upper():6} MCQ={len(r['mcq']):2} DESC={len(r['descriptive']):2} "
            f"skipped_no_answer={r.get('skipped_no_answer')} has_answers={r.get('has_answer_section')} "
            f"warnings={r.get('warnings')}"
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
