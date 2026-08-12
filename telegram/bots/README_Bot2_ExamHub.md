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

**Rewritten 2026-08-12 to be Mode-first** (Pranav's explicit choice — see
CLAUDE.md §11's 2026-08-12 entries): every step below only ever offers
options that have real content behind them, derived live from what's
actually loaded (never a hand-maintained "show everything, gate later"
list) — a student never taps into a dead end. Any step collapses
automatically (no picker shown) when there's only one real option — e.g.
today's CA Inter Advanced Accounting student sees Mode, then goes
straight to Exam Type with zero extra taps, exactly like before this
rewrite.

1. `/start` → bot asks: **Descriptive** or **MCQ**? (skipped entirely if
   only one mode has any content for this bot)
2. → which **Course**? (CA / CS / CMA — only ones with real content for
   that Mode, further narrowed by this bot's tenant scope)
3. → which **Level**? (e.g. CA: Foundation/Inter/Final)
4. → which **Subject**? (new step, added 2026-08-12 — e.g. CA Foundation
   currently has 3: Accounting, Business Economics, Quantitative
   Aptitude. Previously MISSING entirely: all of a course+level's
   subjects were silently merged into one undifferentiated Chapter list.
   Subject buttons carry a small integer index, not the literal subject
   name, in `callback_data` — some subject names exceed Telegram's
   64-byte limit on their own.)
5. → which **Exam Type**? (MTP / RTP / PYQ / Mix — all types)
6. → which **Year**? (auto-detected per type, or Mix = all years)
7. → which **Chapter**? (or All Chapters — also index-based `callback_data`,
   fixed 2026-08-12: a raw slugified chapter name could exceed 64 bytes
   and silently break the ENTIRE chapter list, not just the long one —
   see "Things to watch out for" below)
8. Bot shuffles the matching questions and shows one at a time.
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
9. **"⏭ Next Question"** moves to the next shuffled question (same mode),
   no repeats until the current filtered set is exhausted.

**Added 2026-08-13, question meta line (both Descriptive and MCQ):** every
question now shows its `human_id` (🆔) first -- the platform's globally-
unique, human-readable question ID (see COURSE-CATALOG.md), the same one
used in `mcq_issue_reports` and the Admin Portal. Also as of this date,
this bot's pool includes **every question on the platform**, not just
1LAVYA-authored content -- a standing rule (see `tenants.json`'s
`1lavya-examhub` entry): a faculty's own content is still theirs to
license via their own bot's `content_scope`, but it ALSO always joins
this bot's pool, tagged with `_content_owner` (inferred from the file's
own path, `.../faculty/<tenant_id>/...` vs. everything else) purely for
provenance -- never as an access restriction here.

**Added 2026-08-13, MCQ answer screen:**
- **"\U0001F6A9 Report Issue in MCQ"** -- a 4th button alongside Next
  Question/Chapter List/I'm Done. Picks a category (Wrong Question / Wrong
  Answer / Typo Error / Wrong Mapping / Other), then a free-text
  description, stored in the `mcq_issue_reports` DB table (see
  `telegram/bots/mcq_issue_flow.py`), tagged with the question's
  `human_id`. Has its own Admin Portal page as of 2026-08-13 ("MCQ Issue
  Reports" under Analytics) -- read-only/paginated/filterable/exportable,
  no status-editing UI yet (still also reachable via "Data Export").
- **"\U0001F3C1 I'm Done"** now shows a quick today's-summary (MCQs
  attempted/answered/correct, descriptive questions viewed, time spent
  today) before offering the existing on-demand performance-report flow
  (Yes/No, reusing `report_flow.py`'s already-built channel-picker/
  delivery pipeline). Previously "I'm Done" was wired to the SAME bare
  `restart` callback as "Start Over" -- it silently reset with no summary
  at all; fixed as part of this same change.

## Data coverage

**Rewritten 2026-08-12** — there is no hand-maintained `AVAILABLE_DATA`
constant anymore (removed in the Mode-first rewrite). Every Mode/Course/
Level/Subject actually shown in the menu is derived live from what's
really loaded in `bank`/`mcq_bank` (see `_available_modes()`/
`QuestionBank.courses()`/`.levels()`/`.subjects()` and their `McqBank`
twins in `exam_hub_bot.py`), intersected with this tenant's
`content_scope` from `tenants.json`. A course/level/subject with zero
real questions simply never appears as a button — the student never taps
into a dead end, so there's no "not available yet" gate to configure by
hand anymore either. To add coverage for a new course/level/subject, add
the content (with correct `human_id`s so it resolves against
`course_catalog` — see "COURSE/LEVEL/SUBJECT RESOLUTION" in
`exam_hub_bot.py`) and it appears automatically on next bot restart, no
script edit needed.

## How the backend works

**This whole section was stale before 2026-08-13** — it described the
bot's original single-tenant, pre-multi-source shape (2026-08-08). Fully
rewritten to match the actual current code; see `/CLAUDE.md` §11 for the
dated history of each individual change if you need it.

- Runs as a **Python script on a laptop** (not a cloud server) — must
  stay running for the bot to respond.
- **Content comes from a LIST of JSON files per mode** (`descriptive_json`/
  `mcq_json` in this bot's `tenants.json` row — a single string is also
  accepted for a narrowly-scoped faculty bot with only one source file),
  merged at load time by `_load_and_merge_json_sources()`. The flagship
  `1lavya-examhub` tenant currently merges **5 MCQ sources** (CA Inter
  Advanced Accounting, CA Foundation Quantitative Aptitude, CA Foundation
  Accounting, CA Foundation Business Economics, CMA Foundation +
  Intermediate Law) and **2 descriptive sources** (the flagship's own
  455-question bank, csarunchouhan's 47-question Companies Act bank) —
  per the 2026-08-13 standing rule that every question on the platform
  joins this pool (see the "How a student uses it" section above). Adding
  a new subject/faculty batch is a `tenants.json` config change, not a
  code change.
- **Every record, once loaded, is annotated with**:
  - `_course` / `_level` / `_subject` — resolved via
    `_resolve_course_level_subject()`: explicit fields win if present,
    otherwise derived from `human_id` joined against the `course_catalog`
    DB table (see COURSE-CATALOG.md). A record's own `exam_type`/`year`
    win if present (MCQ records always have them); descriptive records
    without them fall back to pattern-detection over `src_text`.
  - `_chapter_label` — the label actually shown in the Chapter picker.
    Usually equals the raw `chapter_label` field, EXCEPT where
    `_disambiguate_chapter_labels()` detects that label is shared by more
    than one distinct `chapter_slug` within the same (course, level,
    subject) — then the real unit/chapter name (again via `course_catalog`)
    is appended, so the picker never shows visually-identical buttons that
    actually lead to different question sets.
  - `_content_owner` — inferred from the source file's own path
    (`.../faculty/<tenant_id>/...` → that tenant_id, else `"1lavya"`) —
    pure provenance, logged to the DB, never an access filter.
  - `human_id` — expected to already be present on every real record
    (see `tools/generate_mcq_human_ids.py`); shown to the student as the
    first line (🆔) of every question.
- Two example records (both from real, currently-loaded files):
  ```json
  {
    "book_id": "M1C1U0-001", "human_id": "CA_L2_P01_C1_U0_00123",
    "src_text": "MTP January 2025 Set 2", "qno_text": "Q6(a) [OR-alt 2]",
    "marks_text": "Marks: 4", "approx_time_text": "Approx Time: 8 minutes (approx.)",
    "topic_text": "Topic 9: What are Carve Outs/Ins in Ind AS?",
    "question_html": "<p>...</p>", "answer_html": "<div><p>...</p></div>",
    "mistake_text": "Author's Note: ...",
    "chapter_slug": "intro-to-as", "chapter_label": "Intro to AS"
  }
  ```
  ```json
  {
    "mcq_id": "CAI-P1-MTP-2025-01-S1-PI-Q1-a", "human_id": "CA_L2_P01_C7_U3_00042",
    "course": "CA", "level": "Inter",
    "exam_type": "MTP", "year": "2025", "set": "1", "qno_text": "Q1(a)",
    "marks": 2, "difficulty": "Easy", "qtype": "case-mcq",
    "case_ref": "CS-1", "case_facts_html": "<p>...</p>",
    "question_html": "<p>What will be the closing balance...</p>",
    "options": {"A": "₹700,000", "B": "...", "C": "...", "D": "..."},
    "correct_option": "C", "answer_html": "<p><strong>Answer:</strong> (C) ...</p>",
    "chapter_slug": "as11", "chapter_label": "AS 11: ...",
    "unitcode": "M2-C7-U3", "topic_text": "AS 11 (3.4): Foreign currency monetary item..."
  }
  ```
  `options` is not always exactly 4 keys — a small number of source MCQs
  are genuinely 3-option; never assume A–D, iterate whatever's in the dict.
- All content files are **generated, never hand-edited** — re-run
  whichever tool built the source file (`build_exam_bot_mcq_export.py`,
  `ingest_ca_foundation_accounting_economics_mcqs.py`, etc.) whenever the
  upstream source changes.
- `question_html`/`answer_html`/`case_facts_html` are converted from HTML
  into Telegram-safe formatted text (`BeautifulSoup` strips unsupported
  tags, keeps bold/italic/etc.) for the in-chat message. Descriptive
  answers are also separately rendered into a styled PDF (`xhtml2pdf`).

### Activity/analytics database

**Migrated 2026-08-10** off this bot's original separate per-tenant
`Exam_Bot.db` onto the ONE shared `telegram/database/platform.db` every
bot now writes to (via `telegram/database/db.py`) — see
`telegram/database/README.md` for the full shared-DB picture. The 3
Exam-Hub-specific tables (all carry a `bot_id` column, since every "exam"
bot shares one table set):

| Table | One row per... | Key columns |
|---|---|---|
| `exam_hub_sessions` | `/start` (or "Start Over") | `session_id` (PK), `bot_id`, `telegram_user_id`, `started_at`, `course`, `level`, `mode`, `subject` (added 2026-08-12) — filled in as the student progresses, so you can see where people drop off |
| `exam_hub_descriptive_events` | descriptive question shown | `event_id` (PK), `bot_id`, `telegram_user_id`, `session_id`, `book_id`, `course`, `level`, `exam_type`, `year`, `chapter_slug`, `chapter_label`, `qno_text`, `marks_text`, `shown_at`, `answer_shown_at` (NULL until "Show Answer" tapped), `pdf_requested_at` (NULL until "Get as PDF" tapped), `content_owner`/`human_id` (added 2026-08-13) |
| `exam_hub_mcq_attempts` | MCQ shown | `attempt_id` (PK), `bot_id`, `telegram_user_id`, `session_id`, `mcq_id`, `course`, `level`, `exam_type`, `year`, `chapter_slug`, `chapter_label`, `qno_text`, `marks`, `difficulty`, `correct_option`, `shown_at`, `selected_option`/`is_correct`/`answered_at` (all NULL until the student taps an option), `content_owner`/`human_id` (added 2026-08-13) |

`students` is the ONE shared table every bot on the platform writes to
(the "centralized account model" — see `/CLAUDE.md` §11) — not Exam-Hub-
specific, so it isn't repeated here; see `database/schema.sql`.

This gives a direct answer to "which student checked which question, what
did they answer, was it correct" — e.g.:
```sql
-- a student's MCQ accuracy by chapter, this bot only
SELECT chapter_label,
       COUNT(*) AS attempted,
       SUM(is_correct) AS correct
FROM exam_hub_mcq_attempts
WHERE bot_id = '1lavya-examhub' AND telegram_user_id = ? AND answered_at IS NOT NULL
GROUP BY chapter_label;

-- MCQs served, broken down by which faculty's content it actually was
SELECT content_owner, COUNT(*) FROM exam_hub_mcq_attempts GROUP BY content_owner;
```
Rows are inserted when a question is **shown** and updated in place as
the student acts on it (answer revealed / PDF requested / option
selected) — so you can also see shown-but-abandoned questions (the
nullable columns stay NULL). Also see `mcq_issue_reports` (student-filed
"Report Issue in MCQ" submissions, own table, own Admin Portal page) —
not part of this shown/answered event trail, a separate concern.

## Setup checklist for the developer

1. `pip install python-telegram-bot[job-queue] beautifulsoup4 xhtml2pdf python-dotenv --break-system-packages`
2. Get the bot's API token from **@BotFather** (registered as
   `@Official1LavyaExamBot` for the flagship; a faculty bot has its own).
   Put it in `telegram/.env` under the env-var name `bots.json` names for
   this `bot_id` (`bot_token_env`) — never hardcoded in the script.
3. **Nothing else to configure by hand** — `BOT_TOKEN`, `JSON_PATH`
   (descriptive), and `MCQ_JSON_PATH` (MCQ) all resolve automatically at
   import time from `BOT_ID` → `telegram/config/bots.json` (token env var,
   script) → `telegram/config/tenants.json` (that bot's `exam_content`
   lists). Set `BOT_ID` before launching (defaults to `"1lavya-examhub"`):
   ```
   $env:BOT_ID = "capranav-exam"; python telegram/bots/exam_hub_bot.py
   ```
   Analytics go to the one shared `telegram/database/platform.db` — no
   separate DB path to configure (see "Activity/analytics database" below).
4. Run: `python exam_hub_bot.py`
5. Test the full flow: Mode → Course → Level → Subject → Exam Type →
   Year → Chapter → (Descriptive: Show Answer → Get as PDF → Next
   Question) / (MCQ: pick an option → see result+explanation → Next
   Question), using a few real entries covering a multi-subject Course+
   Level (e.g. CA Foundation) to confirm the Subject step actually
   differentiates instead of merging chapters across subjects.

## Things to watch out for

- **Descriptive Exam Type/Year is pattern-detected**, not an explicit
  field (MCQ's is explicit — see above). Before adding more descriptive
  content, confirm no `src_text` values fall through into "OTHER" /
  "Unknown" buckets due to unexpected formatting.
- **Every generated callback_data (`subject:{i}`, `chapter:{i}`,
  `mcqopt:{mcq_id}:{letter}`) must stay under Telegram's 64-byte
  `callback_data` limit.** Subject and Chapter use a small integer INDEX
  into a list stashed in `context.user_data`, not the literal name/slug —
  fixed 2026-08-12 after a real production bug: some content sources
  slugify a full chapter/unit name (over 100 bytes in one case), and
  putting that raw string in callback_data made Telegram reject the
  WHOLE keyboard, not just the long button — see the "year" action's own
  comment in `exam_hub_bot.py` for the full story.  `mcqopt:` still
  embeds the literal `mcq_id` + option letter directly (current `mcq_id`s
  max out at 31 chars, well within budget) — re-check if that ID scheme
  ever changes (see `study_hub_bot.py`'s own past `Button_data_invalid`
  bug in `SKILL-study-bot-catalog-pipeline.md` §6 for what this looks
  like when it breaks).
- **Course/Level/Subject are derived from `human_id` via `course_catalog`
  when a record has no explicit `course`/`level`/`subject` field** (see
  `_resolve_course_level_subject()`) — any new content batch needs a
  correctly-formed `human_id` (`{COURSE}_L{n}_P{paper}_C{c}_U{u}_{seq}`)
  matching a real `course_catalog` row, or it silently buckets into
  "Unknown" (logged as a warning at startup — check the log after adding
  a new content file).
- If `question_html`/`answer_html`/`case_facts_html` ever contain images
  or complex tables, verify they render acceptably both in the stripped
  Telegram text version and in the PDF.
- Re-run `telegram/tools/build_exam_bot_mcq_export.py` after any change
  to `first_run/output/generated-from-script/questions_index.json` —
  it always overwrites `mcq_questions_extracted.json` fresh, nothing is
  hand-patched.
- No payment/premium gating yet — this bot is fully free for now.
