# SQL-QUERY-COOKBOOK.md — Ready-to-run reports for the Admin Portal SQL tab

**What this is:** every SQL report requested so far, saved as copy-paste-ready
scripts, each with **one clearly marked spot** where a number can be changed
to reshape the whole report — built so a non-technical person can run these
and tweak the time window / thresholds without touching anything else in the
script. Pairs with `_claude/skills/SKILL-telegram-sql-query.md` (the
technical reference this cookbook's scripts follow — schema map, join
recipes, gotchas) — read that if you're writing a *new* query from scratch;
this file is just the answers already worked out.

**Where to run these:** Admin Portal → Overview → **SQL Query tab**
(`http://127.0.0.1:8788/?tab=sql`). Paste the whole script, click Run. It's
read-only — nothing here can change or delete real data, only display it.

---

## How to use this file (no coding knowledge needed)

1. Open the query you want below.
2. Copy the **entire** grey code box, including the first few lines.
3. Near the top of every script is a short block that looks like this:
   ```sql
   WITH params AS (
       SELECT 30 AS minutes_back   -- ✏️ EDIT ONLY THIS NUMBER
   ),
   ```
   **This is the only place you ever need to change a number.** Everything
   below it automatically follows whatever number you put here — you never
   need to touch any other line.
4. Paste the edited script into the SQL Query tab and click Run.

**Example:** in the "active students" script, if the line says
`SELECT 2 AS hours_back` and you change the `2` to `10`, the *entire* script
now reports students active in the last **10 hours** instead of 2 — every
other line updates automatically because they all read from this one number.
You do not need to find/replace the number anywhere else.

### Quick reference — what number to change, per script

| # | Report | Change this number... | ...to mean |
|---|---|---|---|
| 1 | Active students, last N minutes | `minutes_back` | how many minutes back to look |
| 2 | Students who practiced > N MCQs in last N hours | `hours_back`, `min_mcqs_required` | the time window, and the MCQ-count cutoff |
| 3 | Unique chat IDs active in last N hours | `hours_back` | how many hours back to look |
| 4 | Top N students by MCQ interaction | `top_n` | how many students to show |
| 5 | Students with email or phone on file | *(none — no time/number involved)* | — |

---

## 1. Students who interacted with the bot in the last N minutes

```sql
WITH params AS (
    SELECT 30 AS minutes_back   -- ✏️ EDIT ONLY THIS NUMBER (currently: last 30 minutes)
),
wallet_balances AS (
    SELECT username, SUM(amount) AS credit_available
    FROM wallet_ledger
    GROUP BY username
),
recent_activity AS (
    SELECT telegram_user_id,
           COUNT(*)                                AS interactions_in_window,
           GROUP_CONCAT(DISTINCT bot_id)            AS bots_used,
           MAX(created_at)                          AS last_event_at
    FROM bot_interactions, params
    WHERE created_at >= strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-' || params.minutes_back || ' minutes')
    GROUP BY telegram_user_id
)
SELECT
    s.telegram_user_id                                                  AS chat_id,
    TRIM(COALESCE(s.first_name,'') || ' ' || COALESCE(s.last_name,''))  AS name,
    s.username                                                          AS telegram_handle,
    s.lavya_username,
    s.mobile_number,
    s.email,
    COALESCE(wb.credit_available, 0)                                    AS credit_available,
    ra.bots_used,
    ra.interactions_in_window,
    ra.last_event_at,
    s.last_seen_at
FROM students s
JOIN recent_activity ra ON ra.telegram_user_id = s.telegram_user_id
LEFT JOIN wallet_balances wb ON wb.username = s.lavya_username
ORDER BY ra.last_event_at DESC;
```

> **📝 Note:** This lists every student who tapped a button, sent a message,
> or downloaded a file on *any* bot within the chosen time window. Want the
> last hour instead of 30 minutes? Change `30` to `60`. Want the last day?
> Change it to `1440` (60 × 24, since this one counts in minutes).

---

## 2. Students who practiced more than N MCQs in the last N hours

```sql
WITH params AS (
    SELECT 24 AS hours_back,          -- ✏️ EDIT: how many hours back to look (currently: 24)
           10 AS min_mcqs_required    -- ✏️ EDIT: minimum MCQs answered to qualify (currently: more than 10)
),
wallet_balances AS (
    SELECT username, SUM(amount) AS credit_available
    FROM wallet_ledger
    GROUP BY username
),
recent_mcq_practice AS (
    SELECT telegram_user_id,
           COUNT(*)                                            AS mcqs_answered,
           SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END)     AS correct_answers,
           GROUP_CONCAT(DISTINCT bot_id)                        AS bots_used,
           MAX(answered_at)                                    AS last_answered_at
    FROM exam_hub_mcq_attempts, params
    WHERE answered_at IS NOT NULL
      AND answered_at >= strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-' || params.hours_back || ' hours')
    GROUP BY telegram_user_id
    HAVING COUNT(*) > params.min_mcqs_required
)
SELECT
    s.telegram_user_id                                                  AS chat_id,
    TRIM(COALESCE(s.first_name,'') || ' ' || COALESCE(s.last_name,''))  AS name,
    s.username                                                          AS telegram_handle,
    s.lavya_username,
    s.mobile_number,
    s.email,
    COALESCE(wb.credit_available, 0)                                    AS credit_available,
    rmp.bots_used,
    rmp.mcqs_answered,
    rmp.correct_answers,
    ROUND(100.0 * rmp.correct_answers / rmp.mcqs_answered, 1)           AS accuracy_pct,
    rmp.last_answered_at,
    s.last_seen_at
FROM students s
JOIN recent_mcq_practice rmp ON rmp.telegram_user_id = s.telegram_user_id
LEFT JOIN wallet_balances wb ON wb.username = s.lavya_username
ORDER BY rmp.mcqs_answered DESC;
```

> **📝 Note:** This counts only MCQs the student actually **answered** (not
> just ones shown to them). Two numbers can be changed here, independently:
> the time window (`hours_back`) and the minimum-questions cutoff
> (`min_mcqs_required`). E.g. set `hours_back` to `168` for "the last 7
> days" and `min_mcqs_required` to `50` for "practiced more than 50
> questions" — both changes are made in the same one block at the top.

---

## 3. Student details + unique chat IDs active in the last N hours

```sql
WITH params AS (
    SELECT 2 AS hours_back   -- ✏️ EDIT ONLY THIS NUMBER (currently: last 2 hours)
),
wallet_balances AS (
    SELECT username, SUM(amount) AS credit_available
    FROM wallet_ledger
    GROUP BY username
),
recent_activity AS (
    SELECT telegram_user_id,
           COUNT(*)                             AS interactions_in_window,
           GROUP_CONCAT(DISTINCT bot_id)         AS bots_used,
           MAX(created_at)                       AS last_event_at
    FROM bot_interactions, params
    WHERE created_at >= strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-' || params.hours_back || ' hours')
    GROUP BY telegram_user_id
)
SELECT
    s.telegram_user_id                                                  AS chat_id,
    TRIM(COALESCE(s.first_name,'') || ' ' || COALESCE(s.last_name,''))  AS name,
    s.username                                                          AS telegram_handle,
    s.lavya_username,
    s.mobile_number,
    s.email,
    COALESCE(wb.credit_available, 0)                                    AS credit_available,
    ra.bots_used,
    ra.interactions_in_window,
    ra.last_event_at,
    s.last_seen_at,
    COUNT(*) OVER ()                                                    AS unique_chat_ids_in_window
FROM students s
JOIN recent_activity ra ON ra.telegram_user_id = s.telegram_user_id
LEFT JOIN wallet_balances wb ON wb.username = s.lavya_username
ORDER BY ra.last_event_at DESC;
```

> **📝 Note:** Every row here is automatically one unique chat ID (that's
> what a "student row" already is in this database), and the
> `unique_chat_ids_in_window` column repeats the total count on every row
> so you can see it alongside the names without scrolling to count rows
> yourself. Change `2` to `10` for "last 10 hours," matching exactly the
> example given when this cookbook was requested.

---

## 4. Top N students by MCQ interaction (all-time)

```sql
WITH params AS (
    SELECT 10 AS top_n   -- ✏️ EDIT ONLY THIS NUMBER (currently: top 10 students)
),
wallet_balances AS (
    SELECT username, SUM(amount) AS credit_available
    FROM wallet_ledger
    GROUP BY username
),
mcq_activity AS (
    SELECT telegram_user_id,
           COUNT(*)                                            AS mcqs_shown,
           COUNT(DISTINCT mcq_id)                               AS distinct_mcqs_shown,
           SUM(CASE WHEN answered_at IS NOT NULL THEN 1 ELSE 0 END) AS mcqs_answered,
           SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END)      AS correct_answers,
           GROUP_CONCAT(DISTINCT bot_id)                        AS bots_used,
           MAX(COALESCE(answered_at, shown_at))                 AS last_mcq_activity_at
    FROM exam_hub_mcq_attempts
    GROUP BY telegram_user_id
)
SELECT
    s.telegram_user_id                                                  AS chat_id,
    TRIM(COALESCE(s.first_name,'') || ' ' || COALESCE(s.last_name,''))  AS name,
    s.username                                                          AS telegram_handle,
    s.lavya_username,
    s.mobile_number,
    s.email,
    COALESCE(wb.credit_available, 0)                                    AS credit_available,
    ma.bots_used,
    ma.mcqs_shown,
    ma.distinct_mcqs_shown,
    ma.mcqs_answered,
    ma.correct_answers,
    ROUND(100.0 * ma.correct_answers / NULLIF(ma.mcqs_answered, 0), 1)  AS accuracy_pct,
    ma.last_mcq_activity_at
FROM students s
JOIN mcq_activity ma ON ma.telegram_user_id = s.telegram_user_id
LEFT JOIN wallet_balances wb ON wb.username = s.lavya_username
ORDER BY ma.mcqs_shown DESC
LIMIT (SELECT top_n FROM params);
```

> **📝 Note:** "Interacted with" counts every MCQ shown to the student
> (whether or not they answered it), so this ranks by total engagement.
> Change `10` to `25` to see the top 25 instead. This report covers all
> time by default (no start/end date) — if a time-boxed version ("top 10
> in the last 7 days") is wanted later, that's a small addition to this
> same script, just ask.

---

## 5. Students with an email ID or phone number on file

```sql
WITH wallet_balances AS (
    SELECT username, SUM(amount) AS credit_available
    FROM wallet_ledger
    GROUP BY username
)
SELECT
    s.telegram_user_id                                                  AS chat_id,
    TRIM(COALESCE(s.first_name,'') || ' ' || COALESCE(s.last_name,''))  AS name,
    s.username                                                          AS telegram_handle,
    s.lavya_username,
    s.email,
    s.mobile_number,
    COALESCE(wb.credit_available, 0)                                    AS credit_available,
    s.first_seen_at,
    s.last_seen_at
FROM students s
LEFT JOIN wallet_balances wb ON wb.username = s.lavya_username
WHERE (s.email IS NOT NULL AND TRIM(s.email) != '')
   OR (s.mobile_number IS NOT NULL AND TRIM(s.mobile_number) != '')
ORDER BY s.last_seen_at DESC;
```

> **📝 Note:** No number to edit here — this isn't a time-based report, it's
> a yes/no filter (does the student have at least one contact detail on
> file). If you instead want students **missing both** (useful for
> chasing contact info before sending reports), swap every `OR`/`IS NOT
> NULL` line for the opposite version — ask and this cookbook can be
> extended with that variant too.

---

## A note on accuracy (read this before trusting any result)

- **"MCQs shown/answered" is not the same as "the full question bank."**
  These numbers only ever reflect what's actually happened on the bots so
  far — see `_claude/skills/SKILL-telegram-sql-query.md` §1 for why.
- **Wallet balance** (`credit_available`) is always computed live from the
  full ledger history, never a stored number — it will always be
  up to date at the moment you click Run.
- Every query run through the SQL tab is logged for audit purposes
  (who ran what, when) — normal, expected, nothing to worry about.
