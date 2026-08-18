"""
Build the Exam Hub Bot's MCQ export file.
-------------------------------------------
Source: first_run/output/generated-from-script/questions_index.json (831 rows,
mixed Part I / Part II records from the Question Bank Book pipeline -- see
CLAUDE.md section 6 for the full pipeline history). That file lives OUTSIDE
telegram/ (it's the Question Bank Book pillar's own output), which used to
make this the one script in telegram/tools/ that couldn't run at all once
telegram/ was detached from the rest of cap-online.

FIXED 2026-08-18 (telegram/ standalone-portability pass, see FIRST_PROMPT.md):
prefers the LIVE first_run/ source when it's actually present (so running
this from inside the full cap-online checkout still picks up fresh sittings
automatically, same as always) and falls back to a bundled snapshot,
telegram/reference-data/questions_index_snapshot.json, when it isn't (so the
script keeps working once telegram/ is copied into an unrelated repo).
Deliberate tradeoff, confirmed rather than assumed: the snapshot WILL go
stale the moment cap-online's Question Bank Book pipeline tags a new
sitting -- re-copy it by hand (see that file's own "_snapshot_note") if you
ever need this script to reflect a newer corpus after the move. See
_resolve_source_index() below for the exact precedence.

This script:
  1. Filters to Part I (MCQ) rows only (part == "I") -- 335 of 831 as of
     2026-08-08.
  2. Drops any row with no usable answer key (answer_letter not a real
     option letter -- currently 1 row, CAI-P1-PYQ-2025-01-PI-Q4, flagged
     "answer-key-letter-only,source-inconsistency" in its own data).
  3. Parses the <ol class="options"><li data-opt="X"> markup out of
     question_html into a plain {letter: text} dict -- NOTE: not every MCQ
     has exactly 4 options; a small number are genuinely 3-option questions
     (e.g. CAI-P1-MTP-2026-01-S1-PI-Q11). Never assume A-D; use whatever
     letters are actually present.
  4. Maps each row's final_chapter (unitcode, e.g. "M2-C7-U3") to the same
     chapter_slug/chapter_label the descriptive bot already uses, by
     reading them straight off book_questions_extracted.json (34 chapters,
     the MCQ data's 28 unitcodes are confirmed a subset -- see project log
     2026-08-08). This keeps both banks' chapter menus identical for the
     same unitcode instead of re-deriving a second slugging scheme.
  5. Writes a lean, self-contained, bot-ready JSON to
     telegram/assets/exam_bot/mcq_questions_extracted.json -- same
     "generated, never hand-edited" pattern as the descriptive
     book_questions_extracted.json in that same folder.

Re-run whenever questions_index.json changes (new sittings tagged, corpus
corrections, etc.) -- this script always reads fresh and overwrites its
output in full; nothing here is hand-patched.

Usage: python telegram/tools/build_exam_bot_mcq_export.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
TELEGRAM_ROOT = os.path.join(REPO_ROOT, "telegram")

LIVE_SOURCE_INDEX = os.path.join(
    REPO_ROOT, "first_run", "output", "generated-from-script", "questions_index.json"
)
BUNDLED_SNAPSHOT_INDEX = os.path.join(
    TELEGRAM_ROOT, "reference-data", "questions_index_snapshot.json"
)


def _resolve_source_index():
    """LIVE first_run/ source wins when present (running from inside the
    full cap-online checkout, unchanged behavior) -- falls back to the
    bundled snapshot only when first_run/ genuinely isn't there (telegram/
    copied into a different repo). Never silently picks a THIRD, unexpected
    file -- exactly these two paths, in exactly this order."""
    if os.path.exists(LIVE_SOURCE_INDEX):
        return LIVE_SOURCE_INDEX, False
    if os.path.exists(BUNDLED_SNAPSHOT_INDEX):
        return BUNDLED_SNAPSHOT_INDEX, True
    raise SystemExit(
        "Neither the live source (" + LIVE_SOURCE_INDEX + ") nor the bundled "
        "snapshot (" + BUNDLED_SNAPSHOT_INDEX + ") exists -- nothing to build from."
    )


SOURCE_INDEX, USING_BUNDLED_SNAPSHOT = _resolve_source_index()

DESCRIPTIVE_JSON = os.path.join(
    REPO_ROOT, "telegram", "assets", "exam_bot", "book_questions_extracted.json"
)
OUTPUT_PATH = os.path.join(
    REPO_ROOT, "telegram", "assets", "exam_bot", "mcq_questions_extracted.json"
)

OPTION_RE = re.compile(
    r'<li[^>]*data-opt="([A-Za-z0-9])"[^>]*>(.*?)</li>', re.IGNORECASE | re.DOTALL
)
STEM_RE = re.compile(r'<p class="stem">(.*?)</p>', re.IGNORECASE | re.DOTALL)


def load_chapter_map():
    """unitcode -> (chapter_slug, chapter_label), read from the already-tagged
    descriptive export so both bot banks agree on chapter naming."""
    with open(DESCRIPTIVE_JSON, "r", encoding="utf-8") as f:
        rows = json.load(f)
    chapter_map = {}
    for r in rows:
        uc = r.get("unitcode")
        if uc and uc not in chapter_map:
            chapter_map[uc] = (r.get("chapter_slug"), r.get("chapter_label"))
    return chapter_map


def parse_options(question_html: str):
    """Pull {letter: option_text} out of the <ol class="options"> markup.
    Does NOT assume 4 options -- some MCQs are genuinely 3-option."""
    options = {}
    for letter, text in OPTION_RE.findall(question_html or ""):
        options[letter.upper()] = text.strip()
    return options


def strip_options_get_stem(question_html: str) -> str:
    """Return just the stem <p> (question text), without the options list --
    the bot renders options separately as buttons."""
    m = STEM_RE.search(question_html or "")
    if m:
        return f"<p>{m.group(1)}</p>"
    # fallback: strip the <ol> block off and return whatever's left
    return re.sub(r"<ol[^>]*>.*?</ol>", "", question_html or "", flags=re.IGNORECASE | re.DOTALL).strip()


def build_qno_text(row: dict) -> str:
    qno = row.get("qno") or "?"
    subpart = row.get("subpart")
    text = f"Q{qno}"
    if subpart:
        text += f"({subpart})"
    if row.get("alt_group"):
        text += f" [Alt {row.get('alt')}]"
    return text


def build_topic_text(row: dict) -> str:
    topics = row.get("topics") or []
    primary = next((t for t in topics if t.get("rank") == "primary"), topics[0] if topics else None)
    if not primary:
        return ""
    label = primary.get("label", "")
    subtitle = primary.get("subtopictitle", "")
    if label and subtitle:
        return f"{label}: {subtitle}"
    return label or subtitle


def main():
    if USING_BUNDLED_SNAPSHOT:
        print(
            "WARNING: first_run/ not found -- building from the bundled snapshot "
            f"({SOURCE_INDEX}), which may be STALE relative to cap-online's real "
            "Question Bank Book corpus. Re-copy that snapshot by hand from a full "
            "cap-online checkout if you need this build to reflect newer sittings."
        )

    with open(SOURCE_INDEX, "r", encoding="utf-8") as f:
        all_rows = json.load(f)

    chapter_map = load_chapter_map()

    mcq_rows = [r for r in all_rows if r.get("part") == "I"]
    print(f"Found {len(mcq_rows)} Part I (MCQ) rows in {SOURCE_INDEX}")

    out = []
    skipped_no_answer = []
    skipped_bad_options = []
    unmapped_chapters = set()

    for r in mcq_rows:
        answer_letter = (r.get("answer_letter") or "").strip().upper()
        options = parse_options(r.get("question_html", ""))

        if not answer_letter or answer_letter not in options:
            skipped_no_answer.append(r["id"])
            continue
        if len(options) < 2:
            skipped_bad_options.append(r["id"])
            continue

        unitcode = r.get("final_chapter")
        chapter_slug, chapter_label = chapter_map.get(unitcode, (None, None))
        if not chapter_slug:
            unmapped_chapters.add(unitcode)
            # LEGACY-* (pre-syllabus-change topics) and any other genuinely
            # unmapped unitcode: skip rather than invent a chapter for it,
            # same policy the chapter-book generator uses for LEGACY codes.
            continue

        out.append({
            "mcq_id": r["id"],
            "course": "CA",
            "level": "Inter",
            "exam_type": (r.get("paper_type") or "OTHER").upper(),
            "year": r.get("exam_year") or "Unknown",
            "set": r.get("set"),
            "qno_text": build_qno_text(r),
            "marks": r.get("marks"),
            "difficulty": r.get("difficulty"),
            "qtype": r.get("qtype"),
            "case_ref": r.get("case_ref"),
            "case_facts_html": r.get("case_facts_html"),
            "question_html": strip_options_get_stem(r.get("question_html", "")),
            "options": options,
            "correct_option": answer_letter,
            "answer_html": r.get("answer_html", ""),
            "chapter_slug": chapter_slug,
            "chapter_label": chapter_label,
            "unitcode": unitcode,
            "topic_text": build_topic_text(r),
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(out)} MCQ records to {OUTPUT_PATH}")
    if skipped_no_answer:
        print(f"Skipped {len(skipped_no_answer)} row(s) with no usable answer key: {skipped_no_answer}")
    if skipped_bad_options:
        print(f"Skipped {len(skipped_bad_options)} row(s) with <2 parsed options: {skipped_bad_options}")
    if unmapped_chapters:
        print(f"Skipped rows for {len(unmapped_chapters)} unmapped unitcode(s): {sorted(unmapped_chapters)}")

    exam_types = sorted({o["exam_type"] for o in out})
    years = sorted({o["year"] for o in out})
    chapters = sorted({o["chapter_slug"] for o in out})
    print(f"Exam types: {exam_types}")
    print(f"Years: {years}")
    print(f"Chapters covered: {len(chapters)}")


if __name__ == "__main__":
    main()
