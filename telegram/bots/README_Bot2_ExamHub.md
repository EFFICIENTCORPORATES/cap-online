# 1Lavya Exam Hub Bot — README

**Display Name:** 1Lavya Exam Hub
**Bot Username:** @Official1LavyaExamBot
**Script file:** `exam_hub_bot.py`

## What this bot is for

A free, public Telegram bot for **exam practice** — students drill down
to the questions they want, either as **Descriptive** questions (attempt,
then reveal the answer on demand) or **MCQs** (pick an option, get
instant right/wrong feedback + the explanation). Every question shown and
every MCQ attempt is logged to a local SQLite DB for analytics.

## How a student uses it

1. `/start` → bot asks: which **Course**? (CA / CS / CMA)
2. → which **Level**? (options depend on the course — e.g. CA:
   Foundation/Inter/Final, CS: Foundation/Executive/Professional)
   - If that Course+Level combination has no question bank yet, the bot
     says so plainly ("no questions for this Level yet") and offers a
     **Start Over** button — see "Data coverage" below for what's live
     today.
3. → **Descriptive** or **MCQ**?
4. → which **Exam Type**? (MTP / RTP / PYQ / Mix — all types) — same step
   for both modes
5. → which **Year**? (auto-detected per type, or Mix = all years)
6. → which **Chapter**? (or All Chapters)
7. Bot shuffles the matching questions and shows one at a time.
   - **Descriptive:** shown with source/topic/marks/expected time, a
     "👁 Show Answer" button reveals the answer text + any author's note
     on common mistakes (`mistake_text`, if present); "📄 Get as PDF" on
     the answer gets a printable PDF of that question + answer.
   - **MCQ:** shown with source/topic/marks/difficulty, any shared case
     narrative, the stem, and all options — plus one button per option
     letter (A/B/C/D, occasionally just A/B/C — not every MCQ has exactly
     4 options). Tapping an option **immediately** shows ✅/❌, the correct
     option, and its explanation. The option buttons are removed after
     answering so the same question can't be re-answered.
8. **"⏭ Next Question"** moves to the next shuffled question (same mode),
   no repeats until the current filtered set is exhausted.

## Data coverage

Only **CA → Inter** currently has real question data (Advanced
Accounting, both Descriptive and MCQ). Every other Course/Level shows up
in the menu — per Pranav's instruction, the full Course/Level structure
is visible up front — but resolves to a "not available yet" message. This
is controlled by one set in the script:

```python
AVAILABLE_DATA = {("CA", "Inter")}
```

Add more `(course, level)` tuples here once a question bank exists for
them (and point the bot at that bank's data — see "How the backend
works").

## How the backend works

- Runs as a **Python script on a laptop** (not a cloud server) — must
  stay running for the bot to respond.
- **Two separate JSON files**, one per mode:
  - **Descriptive** — `book_questions_extracted.json` (~455 records as of
    2026-08-08). Each record looks like:
    ```json
    {
      "book_id": "M1C1U0-001",
      "src_text": "MTP January 2025 Set 2",
      "qno_text": "Q6(a) [OR-alt 2]",
      "marks_text": "Marks: 4",
      "approx_time_text": "Approx Time: 8 minutes (approx.)",
      "topic_text": "Topic 9: What are Carve Outs/Ins in Ind AS?",
      "question_html": "<p>...</p>",
      "answer_html": "<div><p>...</p></div>",
      "mistake_text": "Author's Note: ...",
      "chapter_slug": "intro-to-as",
      "chapter_label": "Intro to AS",
      ...
    }
    ```
    **Exam Type (MTP/RTP/PYQ)** and **Year** are auto-detected at load
    time by scanning `src_text` for those keywords + a 4-digit year —
    there's no separate field for either in this file.
  - **MCQ** — `mcq_questions_extracted.json` (334 records as of
    2026-08-08). Built by `telegram/tools/build_exam_bot_mcq_export.py`
    from the Question Bank Book pipeline's
    `first_run/output/generated-from-script/questions_index.json` (see
    that script's own docstring for the full transform). Each record:
    ```json
    {
      "mcq_id": "CAI-P1-MTP-2025-01-S1-PI-Q1-a",
      "course": "CA", "level": "Inter",
      "exam_type": "MTP", "year": "2025", "set": "1",
      "qno_text": "Q1(a)",
      "marks": 2, "difficulty": "Easy", "qtype": "case-mcq",
      "case_ref": "CS-1", "case_facts_html": "<p>...</p>",
      "question_html": "<p>What will be the closing balance...</p>",
      "options": {"A": "₹700,000", "B": "...", "C": "...", "D": "..."},
      "correct_option": "C",
      "answer_html": "<p><strong>Answer:</strong> (C) ...</p>",
      "chapter_slug": "as11", "chapter_label": "AS 11: ...",
      "unitcode": "M2-C7-U3",
      "topic_text": "AS 11 (3.4): Foreign currency monetary item..."
    }
    ```
    Unlike the descriptive file, **Exam Type/Year are explicit top-level
    fields already** — no pattern-detection needed. `options` is not
    always exactly 4 keys — a small number of source MCQs are genuinely
    3-option; never assume A–D, iterate whatever's in the dict.
  - Both files are **generated, never hand-edited**. Re-run
    `build_exam_bot_mcq_export.py` whenever `questions_index.json`
    changes upstream.
- **Chapter** menu comes from `chapter_slug`/`chapter_label`, which are
  identical between the two files for the same `unitcode` (the MCQ export
  script reads its chapter mapping straight off the descriptive file so
  both banks' chapter menus always agree).
- `question_html`/`answer_html`/`case_facts_html` are converted from HTML
  into Telegram-safe formatted text (`BeautifulSoup` strips unsupported
  tags, keeps bold/italic/etc.) for the in-chat message. Descriptive
  answers are also separately rendered into a styled PDF (`xhtml2pdf`).

### Activity/analytics database

Every interaction is logged to a local SQLite file at
`telegram/assets/exam_bot/Exam_Bot.db` (gitignored — binary, stays local;
`*.db` is excluded repo-wide). Four tables:

| Table | One row per... | Key columns |
|---|---|---|
| `students` | Telegram user (upserted) | `telegram_user_id` (PK), `username`, `first_name`, `last_name`, `first_seen_at`, `last_seen_at`, `session_count` |
| `bot_sessions` | `/start` (or "Start Over") | `session_id` (PK), `telegram_user_id`, `started_at`, `course`, `level`, `mode` — filled in as the student progresses through the funnel, so you can see where people drop off |
| `descriptive_question_events` | descriptive question shown | `event_id` (PK), `telegram_user_id`, `session_id`, `book_id`, `course`, `level`, `exam_type`, `year`, `chapter_slug`, `chapter_label`, `qno_text`, `marks_text`, `shown_at`, `answer_shown_at` (NULL until "Show Answer" tapped), `pdf_requested_at` (NULL until "Get as PDF" tapped) |
| `mcq_attempts` | MCQ shown | `attempt_id` (PK), `telegram_user_id`, `session_id`, `mcq_id`, `course`, `level`, `exam_type`, `year`, `chapter_slug`, `chapter_label`, `qno_text`, `marks`, `difficulty`, `correct_option`, `shown_at`, `selected_option`/`is_correct`/`answered_at` (all NULL until the student taps an option) |

This gives a direct answer to "which student checked which question, what
did they answer, was it correct" — e.g.:
```sql
-- a student's MCQ accuracy by chapter
SELECT chapter_label,
       COUNT(*) AS attempted,
       SUM(is_correct) AS correct
FROM mcq_attempts
WHERE telegram_user_id = ? AND answered_at IS NOT NULL
GROUP BY chapter_label;
```
Rows are inserted when a question is **shown** and updated in place as
the student acts on it (answer revealed / PDF requested / option
selected) — so you can also see shown-but-abandoned questions (the
nullable columns stay NULL).

## Setup checklist for the developer

1. `pip install python-telegram-bot beautifulsoup4 xhtml2pdf --break-system-packages`
2. Get the bot's API token from **@BotFather** (registered as
   `@Official1LavyaExamBot`)
3. In `exam_hub_bot.py`, set:
   - `BOT_TOKEN` (or `TELEGRAM_EXAM_BOT_TOKEN` environment variable)
   - `JSON_PATH` — descriptive question bank JSON
   - `MCQ_JSON_PATH` — MCQ question bank JSON
   - `DB_PATH` — where the analytics SQLite file should live (created
     automatically on first run if it doesn't exist)
4. Run: `python exam_hub_bot.py`
5. Test the full flow: Course → Level → Mode → Exam Type → Year →
   Chapter → (Descriptive: Show Answer → Get as PDF → Next Question) /
   (MCQ: pick an option → see result+explanation → Next Question), using
   a few real entries. Also test picking a Course/Level with no data
   (e.g. CA → Foundation) to confirm the "not available yet" message and
   Start Over button work.

## Things to watch out for

- **Descriptive Exam Type/Year is pattern-detected**, not an explicit
  field (MCQ's is explicit — see above). Before adding more descriptive
  content, confirm no `src_text` values fall through into "OTHER" /
  "Unknown" buckets due to unexpected formatting.
- **MCQ callback data** (`mcqopt:{mcq_id}:{letter}`) must stay under
  Telegram's 64-byte `callback_data` limit — current `mcq_id`s max out at
  31 chars, well within budget, but re-check if the ID scheme ever
  changes (see `study_hub_bot.py`'s own past `Button_data_invalid` bug
  in `SKILL-study-bot-catalog-pipeline.md` §6 for what this looks like
  when it breaks).
- If `question_html`/`answer_html`/`case_facts_html` ever contain images
  or complex tables, verify they render acceptably both in the stripped
  Telegram text version and in the PDF.
- Re-run `telegram/tools/build_exam_bot_mcq_export.py` after any change
  to `first_run/output/generated-from-script/questions_index.json` —
  it always overwrites `mcq_questions_extracted.json` fresh, nothing is
  hand-patched.
- No payment/premium gating yet — this bot is fully free for now.
