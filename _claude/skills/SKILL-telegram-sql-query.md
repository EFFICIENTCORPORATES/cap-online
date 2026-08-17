# SKILL — Writing SQL Queries Against the 1LAVYA Platform Database

> **What this is:** a reference for writing correct, useful SQL against
> `telegram/database/platform.db` — every real table, what it holds, how tables
> actually join to each other (verified against live data, not guessed), the
> SQLite-specific gotchas already hit while building this, and — most
> important — what the database genuinely does **not** contain, so a query
> never silently claims more than it can deliver. Built 2026-08-17 alongside
> the Admin Portal's read-only SQL Query tab (`admin_portal/sql_query_tool.py`,
> `:8788/?tab=sql`), the tool this skill assumes you're writing queries for.
> `telegram/database/schema.sql` is the ground truth if this ever drifts from
> it — every claim below was checked against that file and against real rows,
> not assumed.

---

## 1. Read this first: the database is INTERACTIONS, not CONTENT

**The single most important fact about this schema, and the one most likely
to produce a confidently-wrong query if missed:** MCQ/descriptive question
*content* (question text, options, the correct answer as originally authored,
chapter/topic tags at authoring time) lives in **JSON files** under
`telegram/assets/exam_bot/` (`mcq_questions_extracted.json`,
`book_questions_extracted.json`, and per-faculty/per-chapter variants) — **not
in any database table.** `platform.db` only stores what happened *around*
that content: who was shown which question, when, what they picked, whether
it was correct.

Concretely: `exam_hub_mcq_attempts` has a `correct_option` column and looks
like a question table, but it is a **log** — one row is written every single
time a question is *shown* to *any* student (see `exam_hub_bot.py`'s
`db_log_mcq_shown()`; note the wallet-billing comment on why it's "shown," not
"answered"). A query against it for "all MCQs" will therefore only ever
return questions that have been shown to at least one student at least once —
never the full ~5,000+ question bank, and with one row per attempt, not one
per question, until you deduplicate (`SELECT DISTINCT` or `GROUP BY` on
`mcq_id`/`human_id` — see §5). **Always say so explicitly** when handing back
a result from this table (e.g. "N questions have been shown so far with this
property" — never "here are all the questions with this property").

If someone genuinely needs the complete, canonical question bank (not just
what's been attempted), that means reading the JSON files directly — a
different job than this SQL tool, which only ever sees `platform.db`.

## 2. How to actually run a query

- **Admin Portal → Overview → SQL Query tab** (`http://127.0.0.1:8788/?tab=sql`,
  or `admin_portal/sql_query_tool.py` directly for scripting/testing). Paste
  a `SELECT`/`WITH` query, hit Run.
- **Read-only, enforced two independent ways** (not just a convention):
  the submitted text must be a single `SELECT`/`WITH` statement, AND it runs
  against a genuinely read-only SQLite connection
  (`sqlite3.connect("file:...?mode=ro", uri=True)`) that physically refuses
  any write regardless of what text slipped past validation. `UPDATE`/
  `DELETE`/`DROP`/`ATTACH`/`PRAGMA` are all rejected outright — never write a
  query expecting to modify data through this tool.
- **Global + per-column filters, sortable columns, pagination (20/100/500)**
  are all applied *after* the query runs, over the full fetched result (up to
  `sql_query_tool.FETCH_ROW_LIMIT`, 20,000 rows) — so filtering finds a match
  anywhere in the result, not just on the visible page. You don't need to
  hand-write `WHERE`/`ORDER BY`/`LIMIT` for basic filtering/sorting/paging —
  the tool's own UI does that on top of whatever you write. Write the query
  to shape the DATA (joins, calculated columns, aggregation); let the UI
  handle browsing it.
- **Export** (CSV/Excel/JSON) re-runs your query and applies whatever
  filters/sort are currently active — never just the on-screen page.
- Every query run (accepted or rejected) is audit-logged
  (`admin_actions.action_type IN ('sql_query_run','sql_query_rejected','sql_query_export')`).

## 3. SQLite dialect notes — real gotchas hit while building this

- **This is SQLite, not Postgres/MySQL.** No `RIGHT JOIN`/`FULL OUTER JOIN`
  (rewrite as `LEFT JOIN` the other way, or `UNION`). No native regex. No
  `SPLIT_PART`.
- **A `VALUES` table needs column aliasing via `WITH`, not `FROM (...) AS
  t(cols)`.** `SELECT * FROM (VALUES (1,'a'),(2,'b')) AS t(id, name)` is a
  **syntax error** in this SQLite build (confirmed directly — "near '(':
  syntax error"). Use `WITH t(id, name) AS (VALUES (1,'a'),(2,'b')) SELECT
  * FROM t` instead — verified working.
- **Balances are never a stored column** — `wallet_ledger` is append-only;
  a student's real balance is always `SUM(amount)` computed at query time,
  never read from a field. Same append-only-log shape for
  `report_flow_events`, `leaderboard_broadcast_log`, `test_activity_log` —
  these are full histories, not current-state snapshots (current state, where
  it exists, lives in a sibling table — e.g. `test_sessions` for "what's the
  score right now" vs. `test_activity_log` for "what actually happened, in
  order").
- **Splitting a fixed-format string** (e.g. parsing `human_id`) has no
  built-in function in this SQLite build — use a `WITH RECURSIVE` split (a
  working, verified template is in §5.3 below). `ltrim(x, '0')` is the
  correct way to strip leading zeros from a numeric-as-text field (e.g. a
  paper number) while leaving a trailing letter suffix intact — `ltrim('013A',
  '0')` → `'13A'`; guard the all-zero case (`ltrim('000','0')` → `''`) with
  `CASE WHEN ltrim(x,'0')='' THEN '0' ELSE ltrim(x,'0') END`.
- **NULL-handling**: use `COALESCE`/`|| ''` defensively — several tables
  have real, common NULL values (`students.last_name`, `chapter_slug` for a
  malformed record, `email`/`mobile_number` before verification) and a raw
  `||` concatenation against a NULL silently produces NULL for the whole
  expression, not an error.

## 4. Schema map, grouped by concern

Every table below is real (checked directly against `schema.sql`, including
columns added later via `db.py`'s `_COLUMN_MIGRATIONS`, which don't appear in
the `CREATE TABLE` statement itself — noted where relevant).

### 4.1 Identity & wallet — the core "who is this student, what do they have"

| Table | One row per | Key columns | Notes |
|---|---|---|---|
| `students` | one Telegram chat_id/device | `telegram_user_id` (PK), `username` (their Telegram @handle), `first_name`, `last_name`, `email`, `mobile_number`, `lavya_username` (→ `student_profiles.username`), `last_seen_at` | The **device/session identity**. A student using 3 phones has 3 rows here. `last_seen_at` updates on essentially every interaction — the right column for "last active." |
| `student_profiles` | one **permanent person** | `username` (PK, COLLATE NOCASE, locked forever once claimed), `display_name`, `course`, `level`, `exam_attempt` | The **person identity** — one username can link multiple `students` rows (multiple phones, one wallet/leaderboard/progress). This is what `wallet_ledger`/`leaderboard_participants` key on, not `telegram_user_id`. |
| `student_academic_profiles` | one (username, course, level) | `course`, `level`, `exam_attempt` | A student can prep multiple courses at once (e.g. CA Inter + CMA Foundation) — this is the current source of truth for that; `student_profiles.course/level/exam_attempt` are a frozen historical trace, not actively updated anymore. |
| `wallet_ledger` | one credit/debit **event** | `username`, `event_type` (`signup_grant`/`mcq_debit`/`descriptive_debit`/`test_debit`/`recharge_credit`/`manual_adjustment`/`refund`/`grant_expired`), `amount` (signed), `created_at` | **Balance = `SUM(amount) WHERE username=?`, always** — never a stored field. Append-only. |
| `wallet_grants` | one signup bonus | `username`, `amount_credits`, `granted_at`, `expires_at`, `expired_amount` | Tracks the one-time 1000-credit signup bonus's 365-day expiry lifecycle — separate from the ledger row that actually moved the balance. |
| `payments` | one real Razorpay transaction attempt | `kind` (`faculty_onboarding_fee`/`student_credit_recharge`), `telegram_user_id`, `username`, `amount_inr`, `status` (`pending`/`completed`/`failed`/`refunded`), `created_at` | **A student "made a payment" means `status='completed'`** — `pending`/`failed` rows are real attempts that never actually paid. See §5.2. |

### 4.2 Bot interaction logs — what students actually did

| Table | One row per | Key columns | Notes |
|---|---|---|---|
| `bot_interactions` | any tap/message, any bot | `bot_id`, `telegram_user_id`, `event_type` (free-text: `start`/`callback`/`message`/`file_sent`) | The lightweight, uniform "messages per day" log across every bot kind. |
| `user_activity_log` | any tap/message, any bot (added 2026-08-17) | `correlation_id`, `bot_id`, `telegram_user_id`, `conversation_id`, `handler_kind`, `action`, `action_detail` (PII redacted), `handler_name`, `status` | Finer-grained than `bot_interactions` — ties a row to an exact Python handler and (via `correlation_id`) the matching raw log-file traceback if `status='error'`. See `LOGGING-ARCHITECTURE.md`. |
| `study_hub_events` | a Study Hub download/search | `event_type` (`file_download`/`search_query`/`search_no_match`), `course`, `level`, `subject`, `file_label`, `query_text` | |
| `exam_hub_sessions` | one Exam Hub picker session | `course`, `level`, `mode`, `subject` (subject added via migration) | Referenced by `exam_hub_mcq_attempts.session_id`/`exam_hub_descriptive_events.session_id`. |
| `exam_hub_mcq_attempts` | one MCQ **shown** (not "answered") | `mcq_id`, `human_id` (migration-added), `content_owner` (migration-added), `course`, `level`, `chapter_slug`, `chapter_label`, `correct_option` (always set), `selected_option`/`is_correct` (NULL until answered), `shown_at`/`answered_at` | **The table for "which MCQs, tagged with what" — but see §1.** `chapter_label` is a snapshot at *shown_at* time — an older row can show a stale value even after the live content's label was later corrected (e.g. the 2026-08-17 "Module 1" → real-name fix in `exam_hub_bot.py` does not retroactively rewrite already-logged rows). No `subject` or `topic_text` column — see §5.3/§6 for deriving subject via `course_catalog`. |
| `exam_hub_descriptive_events` | one descriptive question **shown** | `book_id`, `course`, `level`, `chapter_slug`, `chapter_label`, `marks_text`, `shown_at`/`answer_shown_at`/`pdf_requested_at` | Same shape/caveats as `exam_hub_mcq_attempts`, no correct-option concept (it's not multiple-choice). |
| `mcq_issue_reports` | one student-filed "Report Issue in MCQ" | `mcq_id`, `human_id`, `course`/`level`/`subject`/`chapter_slug`/`chapter_label` (self-reported at report time), `category`, `description`, `status` | |

### 4.3 Content taxonomy — the one real source of truth for chapter/unit names

| Table | One row per | Key columns | Notes |
|---|---|---|---|
| `course_catalog` | one (course, level, paper, chapter, unit) | `course`, `level`, `level_num`, `paper_no` (TEXT — some papers split A/B, e.g. `'7A'`), `subject`, `chapter_no`, `chapter_name`, `chapter_name_short`, `unit_no` (**0 = single-unit chapter, or a CS/CMA chapter with no real ICSI/ICMAI sub-unit structure**), `unit_name` | **The canonical source for chapter/subject names** — see §5.3 for how to join a question's `human_id` against this. Has NO topic/subtopic-level granularity (chapter/unit is the finest grain) and is NOT keyed by `chapter_slug` (a different identifier system used in the JSON content/attempt logs) — join via parsed `human_id` fields, not by string-matching slugs/labels. |

### 4.4 Test Mode (paid, timed mock tests)

| Table | One row per | Key columns |
|---|---|---|
| `predesigned_tests` | one real MTP/PYQ sitting available as a test | `catalog_key` (PK), `course`/`level`/`subject`, `exam_type`, `total_marks`, `mcq_count`/`descriptive_count` |
| `test_sessions` | one test a student started | `test_id` (PK), `username`, `catalog_key`, `status` (`in_progress`/`submitted`/`expired`/`abandoned`), `mcq_score`/`mcq_max`, `current_seq_no` |
| `test_questions` | one question within a test | `test_id`+`seq_no` (PK), `qtype`, `source_id` (mcq_id/book_id), `human_id`, `marks`, `status`, `chapter_slug`, `topic_text` (**this table DOES snapshot `topic_text`, unlike `exam_hub_mcq_attempts`** — but only for questions that were part of an actual Test Mode attempt, a much smaller set than practice-mode attempts) |
| `test_mcq_answers` | current answer state, one per test question | `selected_option`, `is_correct` |
| `test_uploads` | one uploaded photo/page of a descriptive answer | `test_id`, `seq_no`, `page_no`, `file_path` |
| `test_activity_log` | one timestamped event during a test | `test_id`, `seq_no` (nullable), `action_type` (free-text), `detail` |

### 4.5 Reporting, leaderboards, admin, misc

| Table | Purpose |
|---|---|
| `student_report_milestones` / `report_deliveries` / `report_flow_events` | The 20-question performance-report pipeline: whether a milestone was prompted/declined/fulfilled, the final delivery outcome, and a full step-by-step conversational trail (`report_flow_events.detail` **can hold real collected contact values** — same PII sensitivity as `students`). |
| `faculty_report_deliveries` | Audit trail for the Faculty Comprehensive Report (Admin Portal), one row per download/email. |
| `faculty_master` | Faculty contact/admin details (`tenant_id` PK) — deliberately does NOT duplicate `tenants.json`'s content-routing fields. |
| `leaderboard_participants` | Who's opted into which `leaderboard_id` (keyed by `username`, config lives in `config/leaderboards.json`, not the DB). |
| `leaderboard_broadcast_log` | Audit trail for nightly leaderboard channel broadcasts. |
| `access_requests` | Self-service requests for a 2nd level within a course a student already has. |
| `admin_actions` | Every real action taken through the Admin Portal — who, what, when. |
| `bot_heartbeats` / `bot_alert_state` | Bot process liveness + the watcher's edge-triggered up/down alert state. |
| `content_ingestion_log` | New-content-added log for the Overview dashboard — **only covers content added after 2026-08-13**, no historical backfill. |
| `backup_runs` | One row per nightly off-machine backup invocation. |
| `admin_accounts` | Login credentials for scoped `bot_admin` accounts (separate from the single super-admin login in `.env`). |

## 5. Verified join recipes (tested against real data, not theoretical)

### 5.1 Student contact info + live wallet balance
```sql
WITH wallet_balances AS (
    SELECT username, SUM(amount) AS credit_available
    FROM wallet_ledger GROUP BY username
)
SELECT s.telegram_user_id AS chat_id,
       TRIM(COALESCE(s.first_name,'') || ' ' || COALESCE(s.last_name,'')) AS name,
       s.mobile_number, s.email,
       COALESCE(wb.credit_available, 0) AS credit_available,
       s.last_seen_at AS last_interaction
FROM students s
LEFT JOIN wallet_balances wb ON wb.username = s.lavya_username
ORDER BY s.last_seen_at DESC;
```
Join key is `students.lavya_username = wallet_ledger.username` — **not**
`telegram_user_id`, since wallet identity is per-person (`student_profiles`),
not per-device. `LEFT JOIN` so a student who's never touched a wallet-gated
flow still shows up with 0, not silently disappears.

### 5.2 Students who ever completed a real payment
```sql
SELECT s.telegram_user_id AS chat_id,
       TRIM(COALESCE(s.first_name,'') || ' ' || COALESCE(s.last_name,'')) AS name,
       COUNT(p.payment_id) AS payments_made, SUM(p.amount_inr) AS total_paid_inr,
       MIN(p.created_at) AS first_payment_at, MAX(p.created_at) AS last_payment_at
FROM students s
JOIN payments p ON p.telegram_user_id = s.telegram_user_id
               AND p.kind = 'student_credit_recharge' AND p.status = 'completed'
GROUP BY s.telegram_user_id
ORDER BY last_payment_at DESC;
```
A plain `JOIN` (not `LEFT`) does the filtering — students with zero completed
payments produce no row. `status='completed'` is the important filter; a
`failed` Razorpay attempt is not a payment that was actually made.
`p.kind='student_credit_recharge'` excludes the unrelated
`faculty_onboarding_fee` kind this same table also tracks.

### 5.3 Deriving subject/chapter name for an attempted MCQ (human_id parse)

`exam_hub_mcq_attempts` has no `subject` column, and `course_catalog` has no
`chapter_slug` column — the only reliable bridge between them is a
question's `human_id` (`{COURSE}_L{level_num}_P{paper_no}_C{chapter_no}_
U{unit_no}_{seq}`, e.g. `CMA_L3_P13_C4_U1_00007`), parsed and joined to
`course_catalog`. Verified end-to-end against every real attempted MCQ on the
platform (177 distinct questions, 0 left unresolved) with this exact pattern:

```sql
WITH RECURSIVE attempted AS (
    SELECT DISTINCT mcq_id, human_id, course, level, correct_option
    FROM exam_hub_mcq_attempts
    WHERE human_id IS NOT NULL   -- older rows predate human_id existing; excluded, not silently mis-joined
),
split(mcq_id, human_id, course, level, correct_option, idx, part, rest) AS (
    SELECT mcq_id, human_id, course, level, correct_option, 1,
           substr(human_id || '_', 1, instr(human_id || '_', '_') - 1),
           substr(human_id || '_', instr(human_id || '_', '_') + 1)
    FROM attempted
    UNION ALL
    SELECT mcq_id, human_id, course, level, correct_option, idx + 1,
           substr(rest, 1, instr(rest, '_') - 1),
           substr(rest, instr(rest, '_') + 1)
    FROM split WHERE rest != ''
),
parsed AS (
    SELECT mcq_id, human_id, course, level, correct_option,
        MAX(CASE WHEN idx=2 THEN CAST(substr(part,2) AS INTEGER) END) AS level_num,
        MAX(CASE WHEN idx=3 THEN
            CASE WHEN ltrim(substr(part,2),'0')='' THEN '0' ELSE ltrim(substr(part,2),'0') END
        END) AS paper_no,
        MAX(CASE WHEN idx=4 THEN CAST(substr(part,2) AS INTEGER) END) AS chapter_no,
        MAX(CASE WHEN idx=5 THEN CAST(substr(part,2) AS INTEGER) END) AS unit_no
    FROM split GROUP BY mcq_id, human_id, course, level, correct_option
)
SELECT p.human_id, p.mcq_id, p.course, p.level,
       COALESCE(cc_exact.subject, cc_flat.subject) AS subject,
       COALESCE(cc_exact.chapter_name, cc_flat.chapter_name) AS chapter_name,
       p.correct_option
FROM parsed p
LEFT JOIN course_catalog cc_exact
  ON cc_exact.course=p.course AND cc_exact.level_num=p.level_num AND cc_exact.paper_no=p.paper_no
 AND cc_exact.chapter_no=p.chapter_no AND cc_exact.unit_no=p.unit_no
-- Fallback: CS/CMA chapters have no real ICSI/ICMAI sub-unit structure, so
-- course_catalog stores them flat at unit_no=0 even when a question's own
-- human_id encodes a real per-question sub-unit (U1, U2, ...). Without this
-- fallback, every CS/CMA row silently fails to match (confirmed: 10 of 10
-- CMA Final Law rows were unmatched until this was added). Same fallback
-- exam_hub_bot.py's own _disambiguate_chapter_labels() needed, 2026-08-17.
LEFT JOIN course_catalog cc_flat
  ON cc_flat.course=p.course AND cc_flat.level_num=p.level_num AND cc_flat.paper_no=p.paper_no
 AND cc_flat.chapter_no=p.chapter_no AND cc_flat.unit_no=0;
```

**Topic name is not available this way, or any way, via SQL** — `topic_text`
only exists in the source JSON and in `test_questions` (Test Mode attempts
only, a much smaller set than practice attempts) — see §6.

## 6. Known limitations — say these out loud, don't paper over them

- **"All questions/MCQs" via SQL means "all *attempted* questions."** The
  true canonical question bank is the JSON content files, never queryable
  through this DB-only tool. Always state the caveat when delivering a
  result shaped like "all X."
- **Topic-level granularity is only in Test Mode's `test_questions.topic_text`**,
  never in ordinary MCQ/descriptive practice logs — a query asked for
  "topic name" against `exam_hub_mcq_attempts`/`exam_hub_descriptive_events`
  cannot be answered from the DB at all; say so rather than substituting
  chapter name silently.
- **`chapter_label` on an attempt/event row is a snapshot**, not a live
  value — don't assume it reflects the content's current, corrected state.
- **A `human_id` can be missing** on older records (pre-dates the 2026-08-11
  retrofit) — always `WHERE human_id IS NOT NULL` before parsing it, rather
  than let a parse silently produce garbage for a NULL.
- **Question content fields (question text, options, answer explanation)
  are never in the DB at all** — don't attempt to `SELECT` them; they don't
  exist here even for attempted questions (only `correct_option`/
  `selected_option`, which are letters, not the option text itself).

## 7. Related docs

- `telegram/database/schema.sql` — ground truth; re-check here if this skill
  and the schema ever disagree.
- `telegram/database/README.md` — the DB's operational story (WAL mode,
  retry logic, off-machine backup).
- `telegram/admin_portal/sql_query_tool.py` — the actual read-only query
  engine this skill assumes; its own docstring covers the safety design in
  full.
- `telegram/COURSE-CATALOG.md` — the full story behind `course_catalog` and
  `human_id`, if the parsing in §5.3 needs deeper context.
- `telegram/LOGGING-ARCHITECTURE.md` — `user_activity_log`'s full design.
- `/TELEGRAM-TEST-MODE-SYSTEM.md` — Test Mode's full data model (§6 of that
  doc is the canonical table-by-table reference for §4.4 above).
