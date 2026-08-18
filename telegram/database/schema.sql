-- telegram/database/schema.sql
-- ---------------------------------------------------------------------------
-- Central 1LAVYA platform schema: shared student identity + wallet ledger +
-- payments, used by EVERY bot process (platform bots and every faculty bot
-- alike) -- see telegram/config/tenants.json for the tenant registry this
-- joins against via tenant_id (a free-text string here, not a DB foreign key,
-- since tenants.json stays the single source of truth for tenant metadata --
-- see telegram/config/tenants.README.md).
--
-- Design/schema artifact -- this file is not wired into any bot yet. See
-- telegram/database/README.md for the live-DB + 5-second-delay snapshot-DB
-- split this is meant to run under, and the analytics queries it supports.
--
-- SQLite syntax (per the 2026-08-09 decision to stay on SQLite until real
-- concurrent load proves it can't keep up -- see memory
-- 1lavya-bot-infra-plan). Kept close enough to standard SQL to port to
-- PostgreSQL later without a redesign: swap `INTEGER PRIMARY KEY AUTOINCREMENT`
-- for `SERIAL PRIMARY KEY` / `GENERATED ALWAYS AS IDENTITY`, and
-- `strftime(...)` defaults for `now()`.
-- ---------------------------------------------------------------------------

PRAGMA foreign_keys = ON;

-- One row per real student, shared across every tenant/bot -- this is the
-- 2026-08-09 "centralized account model" decision (memory:
-- 1lavya-centralized-account-model). Telegram user ID is the natural,
-- already-stable key every bot already has.
CREATE TABLE IF NOT EXISTS students (
    telegram_user_id   INTEGER PRIMARY KEY,
    username            TEXT,
    first_name          TEXT,
    last_name            TEXT,
    email                TEXT,                      -- populated once verified via any bot that does email OTP (e.g. MyFiles Hub)
    first_seen_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    last_seen_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Added 2026-08-11 for the student report pipeline (telegram/tools/
-- generate_student_report.py + telegram/bots/report_flow.py). These 4
-- columns are NOT created here -- SQLite has no `ADD COLUMN IF NOT EXISTS`
-- (confirmed by testing directly: it's a syntax error, unlike
-- `CREATE TABLE`/`CREATE INDEX IF NOT EXISTS`, which SQLite does support --
-- an assumption worth testing before relying on next time, not just here).
-- `db.py`'s `_run_column_migrations()` adds them at startup instead,
-- checking `PRAGMA table_info` first so it's safely re-runnable -- see that
-- function's own docstring for the full column list and reasoning
-- (`mobile_number`, `email_verification_method`, `mobile_verification_method`,
-- `report_channel_preference`).

-- Every wallet-affecting event, append-only. THE BALANCE IS NEVER STORED --
-- it is always SUM(amount) over this table for a student. This is the
-- single most important rule in this schema (see memory
-- 1lavya-faculty-onboarding-model / the 2026-08-09 feedback round): a mutable
-- balance column is how real financial data silently corrupts under a crash
-- or a double-fired payment webhook. A ledger can always be audited and
-- replayed; a balance column can't.
-- RESHAPED 2026-08-15 (Test Mode billing rollout, third round of that
-- discussion -- see telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md §9
-- for the full decision trail). Originally keyed by telegram_user_id;
-- changed to `username` (student_profiles.username) so a student's balance
-- follows them across every linked phone/chat_id, consistent with how
-- leaderboard/profile data already aggregate identity on this platform.
-- Consequence, by design: a student must have claimed a 1LAVYA username
-- before they can recharge or spend from the wallet -- there is no
-- "pending credit against a chat_id with no username yet" state; the bot
-- routes them into profile_flow.py's username-creation step first, same
-- precondition leaderboard-joining already has.
--
-- This table had zero real rows when reshaped (verified directly against
-- the live platform.db before migrating, same discipline the
-- faculty_master table's mid-session reshape used on 2026-08-14) -- see
-- db.py's _migrate_wallet_ledger_shape() for the one-time drop+recreate
-- this required (a column identity change + a widened CHECK constraint,
-- neither of which SQLite's ALTER TABLE can express, unlike the simple
-- ADD COLUMN migrations in _COLUMN_MIGRATIONS below).
CREATE TABLE IF NOT EXISTS wallet_ledger (
    ledger_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username              TEXT NOT NULL REFERENCES student_profiles(username),
    tenant_id            TEXT NOT NULL,   -- which bot context this happened in, e.g. 'capranav', '1lavya-examhub'; 'platform' for platform-level events not tied to any one bot
    event_type           TEXT NOT NULL CHECK (event_type IN (
                              'signup_grant',         -- ONE-TIME 1000-credit (₹10-equivalent) bonus on a student's first-ever interaction with any 1LAVYA bot -- RENAMED from 'free_monthly_grant' 2026-08-16 (that name/shape was never actually used -- 0 rows -- before this rename; see wallet_grants below for the 365-day expiry this grant carries, tracked separately from this ledger row since expiry needs its own lifecycle, not just a balance entry)
                              'mcq_debit',            -- -1 credit, one per MCQ shown (see telegram/database/README.md for why "shown" not "answered")
                              'descriptive_debit',    -- -10 credits, one per descriptive practice question shown (₹1/10 questions, flat regardless of marks -- locked 2026-08-15)
                              'test_debit',           -- -10 credits per mark of an assembled Test Mode session, charged once at "Start Test" (₹1/10 marks -- covers question delivery + upload/PDF assembly ONLY, not AI evaluation, which is priced separately and not yet decided)
                              'recharge_credit',      -- +N credits from a paid top-up (see payments table for the money side)
                              'manual_adjustment',    -- admin correction; `reference` must explain why
                              'refund',                -- reversal of a recharge_credit or manual_adjustment
                              'grant_expired'           -- offsetting debit posted by the wallet_grants sweep once a signup_grant's 365-day window passes unused -- see wallet_grants below
                          )),
    amount                INTEGER NOT NULL,   -- signed: positive = credit, negative = debit. Units are credits; RECOMMENDED (not yet re-confirmed by Pranav) exchange rate is 1 credit = ₹0.01, which makes every locked rate above a clean whole-credit number -- see TEST-MODE-ROADMAP.md §9.2.
    reference             TEXT,               -- mcq_id / book_id / test_id for a debit (whichever applies); payments.gateway_txn_id (the Razorpay Payment Link id) for a recharge; free-text reason for manual_adjustment/refund
    idempotency_key       TEXT UNIQUE,        -- set on debits/credits that could otherwise be double-applied by a retry/restart (e.g. "test_debit:{test_id}", "recharge:{payment_link_id}") -- NULL is fine for events that are naturally safe to repeat (a mcq_debit's own PK-per-row already prevents literal duplication at the call site)
    created_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_wallet_ledger_username ON wallet_ledger(username);
CREATE INDEX IF NOT EXISTS idx_wallet_ledger_tenant  ON wallet_ledger(tenant_id);
CREATE INDEX IF NOT EXISTS idx_wallet_ledger_month   ON wallet_ledger(username, event_type, created_at);

-- Real money, both directions: faculty's flat one-time ₹5,000 onboarding fee,
-- and a student's credit-pack recharge (see tenants.README.md /
-- 1lavya-faculty-onboarding-model memory for why literal ₹1 charges aren't
-- practical -- recharges are packs, ₹20 minimum -- locked 2026-08-15, see
-- TEST-MODE-ROADMAP.md §9.4).
--
-- Gateway locked 2026-08-15: Razorpay, live keys, via the Payment Links
-- product (a Payment Link generated per recharge attempt and sent to the
-- student in-chat -- no website checkout). `gateway_txn_id` holds the
-- Razorpay Payment Link id (e.g. "plink_...") from the moment it's created,
-- not just once paid -- this is what makes a retried "create the link"
-- call idempotent (the UNIQUE constraint rejects a second row for a link
-- that's already being tracked) and is also the reconciliation key a
-- polling job checks via GET /v1/payment_links/{id} (see
-- telegram/database/razorpay_client.py). `status` moves pending ->
-- completed once that poll (or, later, a webhook) confirms `paid`.
--
-- `username` is who the credits actually go to -- separate from
-- `telegram_user_id`, which stays as the audit record of which chat_id/
-- phone actually initiated this specific recharge attempt. They're
-- expected to always resolve to the same person today (a recharge requires
-- a username to already exist -- see wallet_ledger's own note above), kept
-- as two columns because they answer two different questions ("whose
-- balance grew" vs. "which device did this"). This table was empty
-- (verified against the live platform.db) when `username` was added, so it
-- got the same inline-CREATE-TABLE treatment as wallet_ledger's reshape
-- rather than a column migration -- see db.py's
-- _migrate_wallet_ledger_shape() (handles both tables despite the name).
CREATE TABLE IF NOT EXISTS payments (
    payment_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    kind                  TEXT NOT NULL CHECK (kind IN ('faculty_onboarding_fee', 'student_credit_recharge')),
    tenant_id             TEXT,               -- the faculty tenant_id for an onboarding fee; the tenant/bot_id the student recharged from, for a recharge (informational -- wallet itself is shared, see wallet_ledger)
    telegram_user_id      INTEGER REFERENCES students(telegram_user_id),  -- NULL for a faculty_onboarding_fee (faculty isn't a student row)
    username              TEXT REFERENCES student_profiles(username),   -- NULL for a faculty_onboarding_fee; the student whose wallet this recharge credits
    amount_inr            NUMERIC NOT NULL,
    credits_granted       INTEGER,            -- NULL for faculty_onboarding_fee; the pack size for a recharge (mirrored into wallet_ledger.amount on completion)
    gateway                TEXT,               -- 'razorpay' for every recharge going forward (locked 2026-08-15); 'upi_manual' reserved for a hand-credited stopgap, not currently used anywhere
    gateway_txn_id         TEXT UNIQUE,        -- idempotency key: a retried/duplicate webhook (or poll) for the same txn_id must be a no-op, not a double-credit
    status                 TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    created_at             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completed_at           TEXT
);

CREATE INDEX IF NOT EXISTS idx_payments_student ON payments(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_payments_tenant  ON payments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_payments_username ON payments(username);

-- ===========================================================================
-- WALLET GRANTS -- added 2026-08-16 (Pranav: a one-time ₹10-equivalent
-- signup bonus for every student, framed to them only as "free MCQs /
-- Descriptive Questions / Test marks," expiring 365 days after grant if
-- unused, never renewed -- see
-- telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md §0/§9 for the full
-- decision trail).
--
-- Separate from wallet_ledger on purpose: the ledger's `signup_grant` row
-- is what actually moves the balance (a plain +1000 credit) and is
-- permanent/append-only like every other ledger row. THIS table tracks the
-- grant's own EXPIRY LIFECYCLE, which the ledger has no concept of --
-- when it was granted, when it expires, and (once swept) how much of it
-- was actually clawed back unused. One row per grant per username (today,
-- always exactly one -- 'signup_bonus' is the only grant_type, and there
-- is deliberately no renewal).
--
-- Expiry math, kept deliberately simple for v1 rather than full FIFO
-- lot-accounting: at sweep time, `expired_amount = min(amount_credits,
-- current_balance)` -- i.e. NEVER claws back more than this specific
-- grant's own original size, and NEVER claws back more than the student
-- currently has (so a student who has since made a real Razorpay recharge
-- never has their PAID credits wrongly zeroed out by an old free grant's
-- expiry -- the cap at `amount_credits` is what guarantees that). This is
-- an approximation (it doesn't track "was this specific credit spent
-- before that one" in strict FIFO order), documented as such -- correct
-- for the common case (a grant-only balance, which is every student's
-- reality until recharges exist for real), and safe (never over-claws)
-- even once recharges are common.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS wallet_grants (
    grant_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username           TEXT NOT NULL REFERENCES student_profiles(username),
    grant_type          TEXT NOT NULL CHECK (grant_type IN ('signup_bonus')),
    amount_credits        INTEGER NOT NULL,
    ledger_reference        TEXT,    -- the wallet_ledger.idempotency_key this grant posted under, e.g. "signup_grant:{username}" -- lets a sweep trace straight back to the original credit row
    granted_at              TEXT NOT NULL,
    expires_at                TEXT NOT NULL,
    expired_amount              INTEGER,   -- NULL until swept; the actual amount clawed back (<= amount_credits, capped by balance at sweep time -- see comment above)
    swept_at                      TEXT
);

CREATE INDEX IF NOT EXISTS idx_wallet_grants_username ON wallet_grants(username);
CREATE INDEX IF NOT EXISTS idx_wallet_grants_sweep     ON wallet_grants(expires_at, swept_at);

-- ---------------------------------------------------------------------------
-- Content-ownership tagging convention (documentation only -- NOT a table
-- here; applies to the existing catalog artifacts: StudyHub_Master_Catalog
-- .xlsx, questions_index.json, mcq_questions_extracted.json, etc.):
--
--   content_owner = "1lavya"            -- shared pool, matched via a
--                                           tenant's content_scope filter
--   content_owner = "<tenant_id>"       -- e.g. "capranav" -- faculty-owned,
--                                           served only to that tenant's bot,
--                                           regardless of content_scope
--
-- Defaults to "1lavya" where absent, so every row that exists today (all of
-- it pre-dates faculty content) is backward-compatible with no migration.
-- Applying this tag is a change to the catalog-building scripts
-- (build_master_catalog.py, generate_all_chapter_books.py, etc.), not to
-- this DB -- tracked as a follow-up, not done in this pass.
-- ---------------------------------------------------------------------------

-- ===========================================================================
-- WIRED IN 2026-08-10: every bot process below writes to THIS ONE FILE
-- (telegram/database/platform.db -- see telegram/database/db.py for the
-- shared connection helper every bot imports) instead of its own separate
-- .db file. bot_id always refers to telegram/config/bots.json's bot_id
-- field (free-text here too, same reasoning as tenant_id above -- bots.json
-- stays the single source of truth for what a bot_id even is).
--
-- Design principle locked in 2026-08-10 (Pranav's choice): tables are
-- shared PER BOT KIND (one events schema for every "study" bot, one for
-- every "exam" bot, ...), not one physical table per individual bot
-- instance -- adding capranav-study next to 1lavya-studyhub is a new row
-- in bots.json, never a new table. Every query that wants "just this bot"
-- adds `WHERE bot_id = ?`.
-- ===========================================================================

-- One row per bot process, upserted every heartbeat interval (see
-- telegram/database/db.py's send_heartbeat(), called from a JobQueue in
-- every bot). This is how the dashboard (telegram/tools/generate_dashboard.py)
-- and `manage_bots.py status` know a bot is actually alive right now, not
-- just that it was configured to exist -- last_heartbeat_at older than a
-- few missed intervals means the process is down or stuck, whether or not
-- its OS-level PID is still technically running.
CREATE TABLE IF NOT EXISTS bot_heartbeats (
    bot_id               TEXT PRIMARY KEY,
    pid                  INTEGER,
    started_at           TEXT NOT NULL,
    last_heartbeat_at    TEXT NOT NULL
);

-- The generic, uniform interaction log every bot writes to on every
-- meaningful student action (a command, a button tap, a free-text
-- message) -- deliberately lightweight and identically shaped across all
-- bot kinds, so the dashboard's "messages per day/unique visitors" charts
-- are one simple query, not three different ones unioned together. The
-- bot-kind-specific tables below are for RICH per-feature analytics (MCQ
-- accuracy by chapter, etc.) that this table intentionally doesn't carry.
CREATE TABLE IF NOT EXISTS bot_interactions (
    interaction_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id               TEXT NOT NULL,
    telegram_user_id     INTEGER NOT NULL,
    event_type           TEXT NOT NULL,   -- e.g. 'start', 'callback', 'message', 'file_sent' -- free-text, not enum-constrained (kept intentionally loose across 3+ very different bot kinds)
    created_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_bot_interactions_bot_time ON bot_interactions(bot_id, created_at);
CREATE INDEX IF NOT EXISTS idx_bot_interactions_user      ON bot_interactions(telegram_user_id);

-- Study Hub's detailed log (file downloads, free-text searches) --
-- superset of what bot_interactions captures generically, kept separate so
-- study_hub_bot.py's own per-feature analytics don't bloat the generic
-- table's row shape.
CREATE TABLE IF NOT EXISTS study_hub_events (
    event_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id               TEXT NOT NULL,
    telegram_user_id     INTEGER NOT NULL,
    event_type           TEXT NOT NULL CHECK (event_type IN ('file_download', 'search_query', 'search_no_match')),
    category              TEXT,
    course                TEXT,
    level                 TEXT,
    subject               TEXT,
    file_label            TEXT,
    query_text            TEXT,           -- only for search_query/search_no_match
    created_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_study_hub_events_bot ON study_hub_events(bot_id, created_at);

-- Exam Hub's session/question/MCQ logs -- same shape exam_hub_bot.py
-- already had in its own per-tenant Exam_Bot.db (students/bot_sessions/
-- descriptive_question_events/mcq_attempts), migrated here with a bot_id
-- column added to each, and `students` folded into the one shared
-- `students` table above instead of a separate per-bot copy (this was
-- already the 2026-08-09 "centralized account model" decision -- Exam
-- Hub's own students table was the one piece of this DB that hadn't
-- caught up to it yet).
CREATE TABLE IF NOT EXISTS exam_hub_sessions (
    session_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id               TEXT NOT NULL,
    telegram_user_id     INTEGER NOT NULL,
    started_at           TEXT NOT NULL,
    course                TEXT,
    level                 TEXT,
    mode                  TEXT
);

CREATE INDEX IF NOT EXISTS idx_exam_hub_sessions_bot ON exam_hub_sessions(bot_id, started_at);

-- "Time spent on bot" (2026-08-11, for the student report pipeline) is
-- deliberately NOT an explicit ended_at column here. First design was
-- "close any still-open session when the next one starts" -- rejected
-- before shipping: the gap between two sessions can be days, and treating
-- "next session started" as "previous session ended" would silently count
-- that entire idle gap as active time, badly overstating engagement for
-- exactly the students who take breaks between practice sessions.
-- generate_student_report.py instead computes each session's real span as
-- MAX(activity timestamp) - started_at, from the actual mcq_attempts/
-- descriptive_events rows tied to that session_id -- never wider than
-- what real recorded activity actually spans.

CREATE TABLE IF NOT EXISTS exam_hub_descriptive_events (
    event_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id               TEXT NOT NULL,
    telegram_user_id     INTEGER NOT NULL,
    session_id            INTEGER REFERENCES exam_hub_sessions(session_id),
    book_id               TEXT NOT NULL,
    course                TEXT,
    level                 TEXT,
    exam_type             TEXT,
    year                  TEXT,
    chapter_slug           TEXT,
    chapter_label           TEXT,
    qno_text               TEXT,
    marks_text              TEXT,
    shown_at                TEXT NOT NULL,
    answer_shown_at          TEXT,
    pdf_requested_at          TEXT
);

CREATE INDEX IF NOT EXISTS idx_exam_desc_events_bot  ON exam_hub_descriptive_events(bot_id);
CREATE INDEX IF NOT EXISTS idx_exam_desc_events_book ON exam_hub_descriptive_events(book_id);

CREATE TABLE IF NOT EXISTS exam_hub_mcq_attempts (
    attempt_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id                TEXT NOT NULL,
    telegram_user_id      INTEGER NOT NULL,
    session_id             INTEGER REFERENCES exam_hub_sessions(session_id),
    mcq_id                 TEXT NOT NULL,
    course                 TEXT,
    level                  TEXT,
    exam_type              TEXT,
    year                   TEXT,
    chapter_slug            TEXT,
    chapter_label            TEXT,
    qno_text                TEXT,
    marks                   INTEGER,
    difficulty               TEXT,
    correct_option            TEXT NOT NULL,
    selected_option            TEXT,
    is_correct                 INTEGER,
    shown_at                    TEXT NOT NULL,
    answered_at                  TEXT
);

CREATE INDEX IF NOT EXISTS idx_exam_mcq_attempts_bot     ON exam_hub_mcq_attempts(bot_id);
CREATE INDEX IF NOT EXISTS idx_exam_mcq_attempts_mcq     ON exam_hub_mcq_attempts(mcq_id);
CREATE INDEX IF NOT EXISTS idx_exam_mcq_attempts_chapter ON exam_hub_mcq_attempts(chapter_slug);

-- MyFiles Hub is explicitly OUT of scope for this migration -- its users/
-- otps/files/tags/file_tags/activity_log tables stay exactly where they
-- are (myfiles_hub.db, per telegram/bots/myfiles_hub_bot.py), since that's
-- primary application data (who owns which file), not "logs" in the sense
-- this section is about. It DOES get a bot_heartbeats row (see db.py),
-- purely so the dashboard can show it as online/offline alongside every
-- other bot -- that's the only piece of this file it touches.

-- One row per monitored bot_id, tracking the watcher's last-known up/down
-- verdict -- added 2026-08-10 for telegram/bots/watcher_bot.py (Pranav:
-- "a fresh DM ... regarding the Bot being down for any reason"). Exists
-- purely to make alerts edge-triggered instead of level-triggered: without
-- remembering "I already told you this bot is down," every single check
-- tick (default every 60s) would re-send the same DM forever. A transition
-- FROM 'up' TO 'down' sends exactly one down-alert; a transition back to
-- 'up' sends exactly one recovery message; staying in the same state sends
-- nothing. Surviving a watcher restart is the whole point of persisting
-- this in the DB instead of an in-memory dict.
CREATE TABLE IF NOT EXISTS bot_alert_state (
    bot_id               TEXT PRIMARY KEY,
    last_status          TEXT NOT NULL CHECK (last_status IN ('up', 'down')),
    since_at             TEXT NOT NULL,   -- when it entered last_status
    last_alert_sent_at   TEXT             -- NULL if no alert has ever fired for this bot_id
);

-- ===========================================================================
-- STUDENT REPORT PIPELINE -- added 2026-08-11 (Phase 2 of the branding-kit
-- -> report-pipeline -> leaderboard -> admin-portal roadmap). Milestones
-- are PLATFORM-WIDE (Pranav's explicit choice, matches the centralized-
-- account model) -- a student's total counts across every bot they've ever
-- used, not per-bot. See telegram/bots/report_flow.py for the full
-- conversational flow this table pair drives.
-- ===========================================================================

-- One row per (student, milestone) -- e.g. ('20_questions_report_prompt').
-- Exists so the bot asks "want a report?" exactly once per milestone, not
-- on every single message once the threshold is crossed. 'declined' is a
-- real, permanent answer for THIS milestone (never re-nagged) -- it does
-- not block a later, separate milestone (e.g. the Phase 3 leaderboard
-- prompt) from asking again if contact info is still missing then.
CREATE TABLE IF NOT EXISTS student_report_milestones (
    telegram_user_id     INTEGER NOT NULL,
    milestone_type        TEXT NOT NULL,
    status                 TEXT NOT NULL CHECK (status IN ('prompted', 'declined', 'fulfilled')),
    triggered_at            TEXT NOT NULL,
    resolved_at              TEXT,
    PRIMARY KEY (telegram_user_id, milestone_type)
);

-- One row per report actually generated -- an audit trail, and how a
-- re-run/admin tool can see what was already sent instead of guessing.
-- Never stores the PDF bytes themselves (that would duplicate real content
-- data into a logging table) -- `criteria` is enough to regenerate the
-- exact same report on demand if ever needed again.
CREATE TABLE IF NOT EXISTS report_deliveries (
    delivery_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id       INTEGER NOT NULL,
    generated_at             TEXT NOT NULL,
    criteria                  TEXT,      -- e.g. "all-time", "last_100", "since:2026-01-01" -- human-readable, not a serialized query
    channels_requested        TEXT,      -- e.g. "email,telegram" -- what the student's report_channel_preference said at generation time
    email_status               TEXT CHECK (email_status IN ('sent', 'failed') OR email_status IS NULL),
    telegram_status             TEXT CHECK (telegram_status IN ('sent', 'failed') OR telegram_status IS NULL),
    error_detail                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_report_deliveries_student ON report_deliveries(telegram_user_id, generated_at);

-- Added 2026-08-11, same day, per Pranav's ask after debugging the missed-
-- milestone bug: "there should be a log maintained of the message sent and
-- user name collected... all such messages sent. There should be a
-- complete trail." report_deliveries above only logs the FINAL send
-- outcome -- this logs every single step of the conversation (prompt
-- shown, channel chosen, a rejected/invalid attempt, a value collected
-- pending confirmation, a confirmed value, a retry) so a support
-- conversation like "the bot never asked me" can be diagnosed from the
-- data alone, not just re-derived from milestone/students state. `detail`
-- deliberately CAN hold real contact values (a collected mobile/email) --
-- this table carries the same PII sensitivity as `students` already does,
-- same DB file, same access controls, nothing new exposed.
CREATE TABLE IF NOT EXISTS report_flow_events (
    event_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id      INTEGER NOT NULL,
    event_type             TEXT NOT NULL,
    detail                  TEXT,
    created_at                TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_report_flow_events_student ON report_flow_events(telegram_user_id, created_at);

-- ===========================================================================
-- FACULTY COMPREHENSIVE REPORT -- added 2026-08-14 (Pranav: a full
-- content-availability + chapter-wise + student-wise + last-7-days +
-- student-x-chapter + question-difficulty report per faculty/tenant, for
-- any date range, downloadable as PDF/XLSX/HTML and emailable to the
-- faculty). See telegram/admin_portal/faculty_report.py for the query and
-- render layer this table supports. Audit trail only -- never stores the
-- PDF/XLSX bytes themselves, same discipline as report_deliveries above --
-- one row per report actually downloaded or emailed from the Admin Portal.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS faculty_report_deliveries (
    delivery_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id         TEXT NOT NULL,
    generated_at        TEXT NOT NULL,
    range_label           TEXT,
    delivered_to            TEXT,   -- an email address, or 'download:pdf'/'download:xlsx'/'download:html' for a direct download (no email)
    status                     TEXT NOT NULL CHECK (status IN ('sent', 'failed', 'downloaded')),
    error_detail                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_faculty_report_deliveries_tenant ON faculty_report_deliveries(tenant_id, generated_at);

-- ===========================================================================
-- FACULTY MASTER -- added 2026-08-14 (Pranav's direct ask: "maintain a
-- faculty table where we can store the details of the faculty," asked
-- explicitly as a DB table vs a JSON file -- DB table confirmed). Holds
-- ADMINISTRATIVE/CONTACT details only -- email, phone, free-text notes --
-- editable through a real form in the Admin Portal (Masters > Faculty
-- Details), with an audit trail (admin_actions, same as every other
-- write in this portal).
--
-- Deliberately does NOT duplicate CONTENT-ROUTING fields (content_scope,
-- own_content, exam_content, kind, welcome_message) -- those stay in
-- telegram/config/tenants.json, unchanged, because the bot scripts read
-- that file DIRECTLY at process startup; moving them here would mean
-- rewriting every bot's own content-loading code for no benefit this ask
-- needs. Same split-by-concern precedent bots.json (routing/tokens) vs
-- tenants.json (content) already established in this schema's history --
-- this table is the administrative-data half of the SAME tenant, not a
-- competing definition of it.
--
-- Also deliberately does NOT duplicate `onboarding_fee` (amount_inr/paid/
-- paid_at) -- that already lives in tenants.json and is already read by
-- analytics.fetch_faculty_roster(); adding a second copy here would
-- create exactly the dual-source-of-truth risk this table's own design
-- is trying to avoid. The Faculty Details admin page shows that fee
-- status READ-ONLY (sourced from tenants.json) alongside what IS
-- editable here, for one coherent view -- editing fee status stays a
-- direct tenants.json edit until/unless that's explicitly migrated too.
--
-- tenant_id is matched by CONVENTION against tenants.json's own tenant_id
-- (not a real SQL foreign key -- tenants.json isn't a DB table) --
-- telegram/admin_portal/faculty_master.py is the one place that owns
-- reading/writing this table; see its own module docstring.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS faculty_master (
    tenant_id       TEXT PRIMARY KEY,
    contact_email     TEXT,
    contact_phone       TEXT,
    notes                 TEXT,
    created_at              TEXT NOT NULL,
    updated_at                TEXT NOT NULL
);

-- ===========================================================================
-- STUDENT PROFILE / IDENTITY SYSTEM -- added 2026-08-11 (telegram/bots/
-- profile_flow.py), built as the identity foundation for the Phase 3
-- (Leaderboard) roadmap item, per Pranav's explicit confirmation ("build
-- it now as that foundation, so Phase 3 doesn't need to rebuild it
-- later"). One `username` (locked forever once claimed, Instagram-handle
-- style) can be shared across MULTIPLE `students` rows (multiple phones/
-- chat_ids for the same real person) -- Pranav's original scenario: "a
-- student might practice using his 3 mobile numbers... these will have 3
-- unique CHAT IDs... but we will ask him if he already has a username...
-- so his progress will always be mapped to the 1LAVYA username."
--
-- email/mobile_number stay on `students` (per chat_id, NOT here) --
-- deliberately: Pranav's own example says a student "might give different
-- email ids as well" across phones, so those are correctly modeled as
-- per-chat-id already (see the report-pipeline columns added earlier this
-- session). Only the truly SHARED identity fields live here.
--
-- Avatar is NOT a column here -- Pranav's choice: pulled live from the
-- student's Telegram profile photo (via getUserProfilePhotos) whenever
-- needed, not stored or editable through this bot at all. Zero new
-- storage, zero moderation risk, always current.
-- ===========================================================================

-- `username COLLATE NOCASE` on the PRIMARY KEY makes uniqueness case-
-- INSENSITIVE ("JohnDoe" and "johndoe" can't both be claimed) while still
-- storing/displaying exactly what the student typed -- COLLATE only
-- affects comparison, never storage.
CREATE TABLE IF NOT EXISTS student_profiles (
    username             TEXT PRIMARY KEY COLLATE NOCASE,
    display_name          TEXT,
    course                  TEXT,
    level                    TEXT,
    exam_attempt              TEXT,
    created_at                  TEXT NOT NULL,
    updated_at                    TEXT NOT NULL
);

-- students.lavya_username (added via db.py's _run_column_migrations(), see
-- that function's own note on why ALTER TABLE ADD COLUMN happens in Python
-- not here) -- nullable, set at most ONCE per chat_id (profile_flow.py
-- enforces "locked forever" at the application layer: it will never offer
-- to change an already-set lavya_username, only to set one that's
-- currently NULL, either by creating a new student_profiles row or linking
-- to an existing one).

-- ===========================================================================
-- MULTI-COURSE ACADEMIC PROFILES -- added 2026-08-16 (Pranav: a student
-- may genuinely be preparing for more than one course/level at once, e.g.
-- CS Final + CA Inter + CMA Foundation simultaneously -- each with its OWN
-- target exam attempt, since those can differ per course/level too).
--
-- Deliberately ADDITIVE, not a replacement of student_profiles.course/
-- level/exam_attempt above: those three columns stay in place (untouched,
-- never dropped -- SQLite table surgery on a table with real rows is a real
-- risk this codebase avoids per its own established discipline, see
-- db.py's _migrate_wallet_ledger_shape() comment on only ever doing that
-- against a table verified EMPTY). Instead, db.py's own migration copies
-- any existing single course/level/exam_attempt for a username into this
-- table as its first row (idempotent, INSERT...WHERE NOT EXISTS, safe to
-- run on every startup) -- from that point on, THIS table is the single
-- source of truth every piece of code should read/write; the old columns
-- are left as a frozen, no-longer-updated historical trace.
--
-- ONE ROW PER (username, course, level) -- a student can hold at most one
-- profile per course+level pair (adding the SAME course+level twice is a
-- no-op, not a duplicate). Locked rule (Pranav, 2026-08-16): a student can
-- self-service add profiles for as many DIFFERENT courses as they like
-- (CA + CS + CMA all at once is normal), but at most ONE LEVEL per course
-- via self-service -- a SECOND level within a course they already have
-- (e.g. already "CA Inter", now wants "CA Final" too) is exactly the
-- faculty/manager-testing scenario Pranav described, and routes through
-- access_requests below instead of being added directly.
CREATE TABLE IF NOT EXISTS student_academic_profiles (
    profile_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL REFERENCES student_profiles(username),
    course          TEXT NOT NULL,
    level           TEXT NOT NULL,
    exam_attempt    TEXT,        -- "{Month} {Year}", same free-text shape as student_profiles.exam_attempt; independent per course/level per Pranav's explicit note
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    UNIQUE (username, course, level)
);

CREATE INDEX IF NOT EXISTS idx_student_academic_profiles_username ON student_academic_profiles(username);

-- Real trust/optics gate for the "second level in the same course" case
-- above -- Pranav's exact spec: "this will be sent for approval... in
-- backend this should move into an auto approval... within 10 seconds the
-- response should be given as this is approved." No real human review
-- exists yet (self-service request -> a ~10s delayed job flips it to
-- approved and creates the real student_academic_profiles row) -- but the
-- request/audit trail is real and ready for when actual manual review is
-- wanted later, without changing the student-facing flow at all. Open to
-- ANY student, not faculty-restricted (Pranav's confirmed choice,
-- 2026-08-16) -- there's no separate faculty/manager identity concept on
-- this platform today to gate it on.
CREATE TABLE IF NOT EXISTS access_requests (
    request_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username         TEXT NOT NULL REFERENCES student_profiles(username),
    telegram_user_id INTEGER NOT NULL,   -- the chat_id that made the request -- who gets notified once it resolves (a username can span multiple chat_ids; the requester's own chat is the natural one to tell, not every linked device)
    bot_id           TEXT NOT NULL,      -- which bot's token to notify through (context.bot only works within the same bot process that created the request)
    course           TEXT NOT NULL,
    level            TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    requested_at    TEXT NOT NULL,
    resolved_at     TEXT,
    resolved_by     TEXT     -- 'auto' for the ~10s background approval every request gets today; reserved for a real admin username once manual review exists
);

CREATE INDEX IF NOT EXISTS idx_access_requests_status ON access_requests(status);
CREATE INDEX IF NOT EXISTS idx_access_requests_username ON access_requests(username);

-- ===========================================================================
-- LEADERBOARDS -- added 2026-08-11 (Phase 3 of the branding-kit ->
-- report-pipeline -> leaderboard -> admin-portal roadmap). Pranav's spec:
-- a student can opt into up to 5 live leaderboards, each scoped to exactly
-- the course/level (etc.) it's meant for -- a CA Inter student never sees
-- a CA Final/CMA Inter/CS Inter board. Each leaderboard is broadcast
-- nightly at 11:11pm IST to one or more Telegram channels.
--
-- A LEADERBOARD'S DEFINITION (display name, eligibility rule, which
-- metrics it ranks by, its target channels, its min-attempts floor) is
-- NOT a DB table -- it lives in telegram/config/leaderboards.json, same
-- "JSON is the single source of truth for what an ID even means" pattern
-- bot_id/tenant_id already follow elsewhere in this file (Pranav's
-- explicit choice, 2026-08-11: a hand-edited config file now, folding into
-- the Phase 4 admin portal's data source later rather than being replaced
-- by it). Only real STUDENT ACTIVITY against a leaderboard_id lives here.
--
-- Participation is keyed by `username` (student_profiles), NOT
-- telegram_user_id -- a student's ranking metrics (accuracy, questions
-- attempted, time spent) are computed by AGGREGATING ACROSS EVERY chat_id
-- linked to their username (see telegram/database/leaderboard_metrics.py),
-- consistent with the profile system's "one identity, several phones"
-- design directly above. A student with no username yet cannot join any
-- leaderboard -- profile_flow.py's leaderboard menu only appears once a
-- username exists.
-- ===========================================================================

CREATE TABLE IF NOT EXISTS leaderboard_participants (
    username             TEXT NOT NULL REFERENCES student_profiles(username),
    leaderboard_id       TEXT NOT NULL,   -- free-text, matches a telegram/config/leaderboards.json entry's leaderboard_id
    joined_at            TEXT NOT NULL,
    PRIMARY KEY (username, leaderboard_id)
);

-- The "max 5 leaderboards per student" cap is enforced at the application
-- layer (profile_flow.py checks COUNT(*) for this username before allowing
-- a new join), same as username format validation -- not a SQL CHECK
-- constraint, since SQLite can't express a per-group row-count limit
-- declaratively without a trigger, and every other cross-row business rule
-- in this schema already lives in Python for the same reason.
CREATE INDEX IF NOT EXISTS idx_leaderboard_participants_lb ON leaderboard_participants(leaderboard_id);

-- One row per nightly broadcast actually sent (or attempted) to one
-- channel -- the same "complete trail" discipline report_flow_events
-- established (Pranav, 2026-08-11: "there should be a log maintained...
-- a complete trail"), applied to leaderboard broadcasts. Never stores the
-- full rendered message (that's reconstructable from
-- leaderboard_metrics.py + leaderboards.json at any time) -- just enough
-- to audit what went out, when, to how many qualifying students.
CREATE TABLE IF NOT EXISTS leaderboard_broadcast_log (
    broadcast_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    leaderboard_id         TEXT NOT NULL,
    channel_chat_id          TEXT NOT NULL,
    metrics_included           TEXT,        -- comma-separated metric keys actually rendered this run
    participant_count             INTEGER,  -- how many opted-in students met the min-attempts floor at send time
    status                          TEXT NOT NULL CHECK (status IN ('sent', 'failed')),
    error_detail                     TEXT,
    sent_at                          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_leaderboard_broadcast_log_lb ON leaderboard_broadcast_log(leaderboard_id, sent_at);

-- ===========================================================================
-- ADMIN PORTAL -- added 2026-08-11 (Phase 4 of the roadmap, foundation tier:
-- Flask app + login + sidebar shell + Bot Status/Restart + Bot Logs). See
-- telegram/admin_portal/README.md.
-- ===========================================================================

-- Every real, production-affecting action taken through the portal --
-- who, what, when. Same "complete trail" discipline already established
-- for report_flow_events/leaderboard_broadcast_log, applied here because
-- this portal can restart live bots and (in later phases) edit faculty
-- tokens/master config -- exactly the kind of action that needs an
-- honest record of who did it and when, not just whether it succeeded.
-- `username` is free text (not a foreign key into a users table -- there
-- is no users table yet, single-admin login only; this column is exactly
-- what a future multi-user RBAC upgrade will read from, unchanged).
CREATE TABLE IF NOT EXISTS admin_actions (
    action_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username          TEXT NOT NULL,
    action_type        TEXT NOT NULL,   -- e.g. 'bot_restart' today; 'master_edit'/'faculty_add'/... in later phases
    target               TEXT,           -- action-specific, e.g. a bot_id
    detail                TEXT,
    created_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_admin_actions_time ON admin_actions(created_at);

-- ===========================================================================
-- COURSE CATALOG -- added 2026-08-11 (Pranav's ask: "this course catalog
-- should be part of a table in our db and should be the single source of
-- truth for all MCQs and descriptive questions... Chapter ID, Unit ID,
-- Chapter name for each Course, Level, Subject should be derived from
-- this course content"). One row per (course, level, paper, chapter,
-- unit) -- the finest grain any current content is tagged at. CS/CMA
-- chapters have no real sub-unit structure in ICSI/ICMAI's own material
-- (confirmed against CS_CMA_Chapter_Catalog.xlsx) -- those rows use
-- unit_no=0, the SAME "no further sub-units" convention CA's own
-- single-unit chapters already use (see the U0 migration documented
-- earlier in this file's history for student_profiles/topic-index.json).
--
-- Populated by telegram/tools/populate_course_catalog.py from THREE
-- already-verified real sources (never hand-typed): CA Inter Advanced
-- Accounting from books/concept-book/syllabus-engine/data/1-ca-inter-adv-
-- accounts-topic-page-index.json (the canonical, "never edit" topic/page
-- index); CS/CMA (all subjects) from telegram/source-docs/
-- CS_CMA_Chapter_Catalog.xlsx's "Chapter Catalog" sheet (chapter numbers/
-- names read directly off each subject's own printed ToC); CA Foundation
-- Quantitative Aptitude from telegram/source-docs/
-- StudyHub_Master_Catalog.xlsx (chapter numbers/names read directly off
-- the real study material file names/cover pages). paper_no for every
-- subject that currently HAS question content was independently
-- cross-checked against telegram/tools/cs_cma_common.py /
-- build_study_bot_catalog.py's own already-verified (real cover-page-
-- read) COURSE_META/FILE_META tables before being trusted here -- see
-- populate_course_catalog.py's own module docstring for the exact
-- per-subject provenance trail.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS course_catalog (
    catalog_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    course                TEXT NOT NULL,     -- 'CA' | 'CS' | 'CMA'
    level                  TEXT NOT NULL,    -- 'Foundation' | 'Inter' | 'Final' | 'CSEET' | 'Executive' | 'Professional' | 'Intermediate' -- CMA uses 'Intermediate', CA uses 'Inter' -- real, deliberate, NOT a typo (matches profile_flow.py's own COURSE_LEVELS taxonomy exactly)
    level_num              INTEGER NOT NULL, -- 1/2/3, per Pranav's confirmed mapping (2026-08-11): Foundation/CSEET=1, Inter/Executive/Intermediate=2, Final/Professional=3
    paper_no                TEXT NOT NULL,   -- e.g. '1', '5', '7A' -- kept as TEXT (some ICAI/ICMAI papers split A/B, e.g. Direct/Indirect Tax)
    subject                  TEXT NOT NULL,  -- full official subject name
    chapter_no                INTEGER NOT NULL,
    chapter_name                TEXT NOT NULL,
    chapter_name_short            TEXT,       -- abridged name, Pranav's own ask ("abridged names for subjects and chapters and units")
    unit_no                        INTEGER NOT NULL DEFAULT 0,  -- 0 = single-unit chapter / no ICSI-ICMAI sub-unit structure
    unit_name                       TEXT,
    unit_name_short                  TEXT,
    session                              TEXT NOT NULL DEFAULT '',  -- e.g. 'May26', 'May27' -- added 2026-08-18, blank for every subject with only ONE live ICAI edition. A subject with more than one (GST first) keeps ONE Subject entry (never duplicated in the bot's picker) and uses this column to tell editions apart instead -- see study_hub_bot.py's editions_for()/"ed:" drill-down step and populate_course_catalog.py's rows_from_studyhub_catalog() for where it's actually populated (read straight from each file's own FileName via build_master_catalog.py's session_from_filename(), never hand-typed).
    source                             TEXT NOT NULL,  -- which real source file this row was read from -- see module docstring above
    updated_at                          TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_course_catalog_key
    ON course_catalog(course, level, paper_no, chapter_no, unit_no, session);
CREATE INDEX IF NOT EXISTS idx_course_catalog_lookup ON course_catalog(course, level, subject);

-- ===========================================================================
-- MCQ ISSUE REPORTS -- added 2026-08-13. A student can flag a problem with
-- an MCQ directly from the "Correct Answer" screen ("Report Issue in MCQ"
-- button) -- see telegram/bots/mcq_issue_flow.py for the full
-- category-picker + free-text conversational flow this table supports.
-- No admin-UI triage is built yet -- rows are visible today via the Admin
-- Portal's existing generic "Data Export -> any real table" page (already
-- works for any table with zero new code, per its own design), and via
-- direct SQL. A dedicated triage view is a natural future Admin Portal
-- module, not built in this pass.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS mcq_issue_reports (
    report_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id                TEXT NOT NULL,
    telegram_user_id      INTEGER NOT NULL,
    mcq_id                 TEXT NOT NULL,
    human_id                TEXT,   -- the globally-unique, student-facing question ID (see COURSE-CATALOG.md) -- added 2026-08-13, alongside the internal mcq_id
    course                  TEXT,
    level                    TEXT,
    subject                   TEXT,
    chapter_slug               TEXT,
    chapter_label               TEXT,
    category                     TEXT NOT NULL CHECK (category IN (
                                      'wrong_question', 'wrong_answer', 'typo_error',
                                      'wrong_mapping', 'other'
                                  )),
    description                   TEXT NOT NULL,
    status                         TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'dismissed')),
    created_at                      TEXT NOT NULL,
    resolved_at                      TEXT
);

CREATE INDEX IF NOT EXISTS idx_mcq_issue_reports_mcq    ON mcq_issue_reports(mcq_id);
CREATE INDEX IF NOT EXISTS idx_mcq_issue_reports_status ON mcq_issue_reports(status, created_at);

-- ===========================================================================
-- TEST MODE -- added 2026-08-16 (Pre-Designed Tests only, per the confirmed
-- scope -- see telegram/assets/exam_bot/Tests/TEST-MODE-ROADMAP.md for the
-- full design). Reuses real MTP/PYQ sittings (RTP excluded -- neither its
-- MCQs nor its descriptive questions carry reliable stated marks, confirmed
-- by inspecting every real RTP record before this table was designed) as
-- ready-made timed tests. CA Inter Advanced Accounting only, today -- the
-- only subject with genuine "one real paper" sitting data (see
-- predesigned_tests.course/level/subject below, which is what lets a
-- student asking for another subject be told honestly "not available yet"
-- rather than silently shown nothing).
-- ===========================================================================

-- Generated by telegram/tools/generate_predesigned_tests.py from the real,
-- already-loaded question banks (never hand-typed) -- one row per real
-- sitting (an MTP Set counts as its own sitting; PYQ has no sets). A
-- sitting with 0 usable marks on both sides (i.e. every RTP sitting) is
-- never emitted. `active=0` lets a specific sitting be hidden without
-- deleting its row (e.g. a sitting later found to have a real content bug).
CREATE TABLE IF NOT EXISTS predesigned_tests (
    catalog_key         TEXT PRIMARY KEY,   -- e.g. "CA-Inter-AdvAcc-MTP-2024-05-S1"
    course               TEXT NOT NULL,
    level                 TEXT NOT NULL,
    subject                TEXT NOT NULL,
    exam_type                TEXT NOT NULL,   -- 'MTP' | 'PYQ' (never 'RTP' -- see comment above)
    year                      TEXT NOT NULL,
    month                      TEXT,           -- e.g. "May" -- NULL only if genuinely undetectable (never expected in practice, both source patterns always carry it)
    set_no                      TEXT,           -- NULL for PYQ (no sets); '1'/'2' for MTP
    title                        TEXT NOT NULL,
    total_marks                   INTEGER NOT NULL,
    duration_minutes                INTEGER NOT NULL,
    mcq_count                        INTEGER NOT NULL,
    mcq_marks                         INTEGER NOT NULL,
    descriptive_count                  INTEGER NOT NULL,
    descriptive_marks                   INTEGER NOT NULL,
    active                                INTEGER NOT NULL DEFAULT 1,
    generated_at                            TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predesigned_tests_scope ON predesigned_tests(course, level, subject, active);

-- One row per test a student has actually started. `username` is who pays/
-- is scored (the wallet identity -- see identity.py); `telegram_user_id`/
-- `bot_id` are the actual device/bot context, kept separately for the same
-- reason payments.username vs payments.telegram_user_id are (schema.sql's
-- own comment on that table explains the split). `test_id` is a plain
-- readable string (not autoincrement) so it can double as a wallet debit's
-- idempotency-key reference and a file-path component (see test_uploads)
-- without a lookup.
CREATE TABLE IF NOT EXISTS test_sessions (
    test_id             TEXT PRIMARY KEY,
    bot_id                TEXT NOT NULL,
    telegram_user_id       INTEGER NOT NULL,
    username                 TEXT NOT NULL REFERENCES student_profiles(username),
    catalog_key                TEXT NOT NULL REFERENCES predesigned_tests(catalog_key),
    total_marks                  INTEGER NOT NULL,
    mcq_count                      INTEGER NOT NULL,
    descriptive_count                INTEGER NOT NULL,
    duration_minutes                   INTEGER NOT NULL,
    started_at                           TEXT NOT NULL,
    expires_at                             TEXT NOT NULL,
    status                                   TEXT NOT NULL CHECK (status IN (
                                                 'in_progress', 'submitted', 'expired', 'abandoned'
                                             )),
    submitted_at                               TEXT,
    mcq_score                                    INTEGER,   -- NULL until submitted
    mcq_max                                        INTEGER,
    grace_offered_at                               TEXT,      -- set the FIRST (and only) time the "need extra minutes?" offer is shown, so it's never offered twice -- see wallet_flow.py's twin note on offering things exactly once
    grace_requested_minutes                          INTEGER,  -- NULL if never asked or the student chose "submit now"; otherwise 2/3/5 -- the actual extension granted
    current_seq_no                                    INTEGER   -- the question currently being shown -- 2026-08-16, Pranav's ask: exact-point resume after a dropped phone/dead battery, AND what the no-activity heartbeat (test_activity_log) checks against to know it should stop rescheduling itself once the student has moved on
);

CREATE INDEX IF NOT EXISTS idx_test_sessions_user   ON test_sessions(telegram_user_id, status);
CREATE INDEX IF NOT EXISTS idx_test_sessions_expiry ON test_sessions(status, expires_at);

-- One row per question WITHIN a test -- seq_no is the test's OWN numbering
-- (1..N), never the source sitting's own qno_text, per the roadmap's own
-- design note (a test question's identity inside the test must never be
-- confused with its identity in the original paper).
CREATE TABLE IF NOT EXISTS test_questions (
    test_id          TEXT NOT NULL REFERENCES test_sessions(test_id),
    seq_no             INTEGER NOT NULL,
    qtype                TEXT NOT NULL CHECK (qtype IN ('mcq', 'descriptive')),
    source_id              TEXT NOT NULL,   -- mcq_id or book_id
    human_id                 TEXT,
    marks                      INTEGER NOT NULL,
    status                       TEXT NOT NULL CHECK (status IN (
                                     'pending', 'answered', 'skipped',       -- mcq (also reused for a descriptive question the student explicitly "passed" on -- see test_flow.py's PASS_UPLOAD_PHRASES)
                                     'not_uploaded', 'uploaded'              -- descriptive
                                 )),
    chapter_slug                   TEXT,     -- snapshotted at test-build time (2026-08-16, Pranav's ask: track every question down to topic/subtopic for concept-level analysis) -- never re-derived from the live content bank later, so a test's own record stays stable even if content is re-tagged afterward
    topic_text                       TEXT,
    PRIMARY KEY (test_id, seq_no)
);

CREATE INDEX IF NOT EXISTS idx_test_questions_test ON test_questions(test_id);

CREATE TABLE IF NOT EXISTS test_mcq_answers (
    test_id           TEXT NOT NULL,
    seq_no              INTEGER NOT NULL,
    selected_option        TEXT,
    is_correct                INTEGER,   -- NULL until the test is submitted -- never computed/shown mid-test
    answered_at                 TEXT,
    PRIMARY KEY (test_id, seq_no)
);

-- One row per uploaded PAGE (a student's answer to one descriptive question
-- may span several photos). page_no orders pages WITHIN a question;
-- file_path points into telegram/assets/exam_bot/Tests/uploads/{test_id}/
-- {seq_no}/ (gitignored in full -- binary + personal data, never committed).
CREATE TABLE IF NOT EXISTS test_uploads (
    upload_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id              TEXT NOT NULL,
    seq_no                 INTEGER NOT NULL,
    page_no                  INTEGER NOT NULL,
    file_path                  TEXT NOT NULL,
    telegram_file_id             TEXT,
    mime_type                      TEXT,
    uploaded_at                      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_test_uploads_question ON test_uploads(test_id, seq_no, page_no);

-- ===========================================================================
-- TEST ACTIVITY LOG -- added 2026-08-16 (Pranav: capture every point of
-- possible data during a test -- question views, MCQ option picks AND
-- later changes, upload pages, passive no-activity heartbeats every 60s,
-- reminders, the grace-period offer/choice, submission -- all timestamped,
-- so a student's understanding can be analyzed later at topic/subtopic
-- granularity, not just "got it right or wrong").
--
-- Deliberately ONE lean append-only event log, not a wide table-per-action-
-- type -- same "subject/action/object + timestamp" shape Pranav proposed,
-- and the same architectural pattern this schema already uses elsewhere
-- (wallet_ledger, report_flow_events, leaderboard_broadcast_log): an
-- append-only log is what makes "resume from the exact point, lose at most
-- 60 seconds of data even if the phone dies mid-test" possible at all --
-- test_sessions/test_questions/test_mcq_answers stay the CURRENT-STATE
-- tables (fast to query for "what's the score"), this table is the FULL
-- HISTORY underneath them (fast to query for "what actually happened, in
-- order"). `test_questions.chapter_slug`/`topic_text` (added same day)
-- carry the topic/subtopic tag onto every question snapshot, so per-topic
-- analysis is a straightforward join from here, not a re-parse of the
-- live content bank.
--
-- action_type values (free-text, not CHECK-constrained -- new action
-- types are expected to be added over time as the test-taking flow grows,
-- same reasoning bot_interactions.event_type already documents for
-- exactly this tradeoff): 'test_started', 'question_viewed',
-- 'mcq_option_selected', 'mcq_option_changed', 'upload_page_added',
-- 'upload_done', 'upload_overwrite_chosen', 'upload_append_chosen',
-- 'question_passed', 'no_activity_heartbeat', 'reminder_sent',
-- 'grace_offered', 'grace_chosen', 'submit_confirmation_shown',
-- 'test_submitted'.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS test_activity_log (
    activity_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id             TEXT NOT NULL,
    seq_no                INTEGER,            -- NULL for a test-level event not tied to one question (test_started, test_submitted, grace_offered)
    action_type             TEXT NOT NULL,
    detail                     TEXT,            -- free-text or JSON-encoded payload -- e.g. the selected option, previous+new option on a change, page count, minutes chosen
    occurred_at                   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_test_activity_log_test ON test_activity_log(test_id, occurred_at);

-- ===========================================================================
-- CONTENT INGESTION LOG -- added 2026-08-13, for the Admin Portal Overview
-- rebuild's "New Questions Added" trend (which subjects/chapters got new
-- content, and when). One row per content BATCH wired into a tenant's
-- exam_content (mcq_json/descriptive_json) in telegram/config/tenants.json
-- -- not one row per question, and not auto-derived from file mtimes (an
-- mtime reflects the last EDIT, e.g. a typo fix, not first publication --
-- would misdate old content as "new" the moment anyone touches it).
--
-- HONEST GAP, not a bug: there is no historical ingestion-date data before
-- this table existed. Every content batch wired into the platform before
-- 2026-08-13 has NO row here and will not appear in date-ranged "new
-- questions" charts that only cover dates before this table's first real
-- entry -- confirmed decision (Pranav, 2026-08-13): track forward from
-- today rather than attempt an approximate git-history backfill. See
-- telegram/database/README.md.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS content_ingestion_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at       TEXT NOT NULL,
    qtype           TEXT NOT NULL CHECK (qtype IN ('mcq', 'descriptive')),
    course          TEXT,
    level           TEXT,
    subject         TEXT,
    chapter_label   TEXT,
    question_count  INTEGER NOT NULL,
    source_file     TEXT,
    content_owner   TEXT,     -- '1lavya' or a faculty tenant_id, same convention as exam_hub_bot.py's _infer_content_owner()
    note            TEXT
);

CREATE INDEX IF NOT EXISTS idx_content_ingestion_log_date ON content_ingestion_log(logged_at);
CREATE INDEX IF NOT EXISTS idx_content_ingestion_log_scope ON content_ingestion_log(course, level, subject);

-- ===========================================================================
-- BACKUP RUNS -- added 2026-08-16 (telegram/tools/backup_to_cloudflare.py,
-- see that file's own docstring and telegram/database/README.md's
-- "Off-machine backup" section for the full pipeline). One row per
-- invocation -- inserted as 'running' at start, finalized at the end (or
-- on a top-level failure) -- so the Admin Portal's Bot Status page can show
-- a real "Backup Snapshot Summary" without parsing log files or making a
-- live R2/D1 call on every page load (same "one query against the local
-- DB, not a live external call" pattern every other audit table in this
-- schema already follows). NOTE: because the DB-snapshot phase runs BEFORE
-- this row is finalized, that run's own snapshot/D1-mirror will legitimately
-- show its own row as 'running', not 'success' -- expected, not a bug; the
-- NEXT run's snapshot/mirror correctly shows it finalized.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS backup_runs (
    run_id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at                 TEXT NOT NULL,
    finished_at                  TEXT,
    status                         TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    duration_seconds                 REAL,
    platform_db_snapshot_kb            REAL,
    myfiles_db_snapshot_kb                REAL,
    secrets_backed_up                       INTEGER,
    d1_tables_mirrored                        INTEGER,
    d1_rows_mirrored                            INTEGER,
    assets_uploaded                               INTEGER,
    assets_unchanged                                INTEGER,
    assets_failed                                     INTEGER,
    failed_phases                                       TEXT,   -- comma-separated phase names, NULL if none
    error_detail                                          TEXT
);

CREATE INDEX IF NOT EXISTS idx_backup_runs_started ON backup_runs(started_at);

-- ===========================================================================
-- LOGGING/OBSERVABILITY -- Phase 1, added 2026-08-17. Full design/reasoning
-- lives in telegram/LOGGING-ARCHITECTURE.md -- read that before touching
-- either table below; this is only the schema, not the "why."
-- ===========================================================================

-- The fine-grained "who did what, when" trail every bot handler now writes
-- to via telegram/bots/activity_logger.py's @log_activity decorator --
-- deliberately additive, does NOT replace bot_interactions (kept exactly
-- as-is, existing dashboard queries still read it unchanged) or any
-- per-feature table (wallet_ledger, exam_hub_mcq_attempts, ...), which stay
-- the source of truth for domain-specific detail this generic envelope
-- can't infer. See LOGGING-ARCHITECTURE.md §3 for the two-layer reasoning.
CREATE TABLE IF NOT EXISTS user_activity_log (
    activity_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    correlation_id    TEXT NOT NULL,      -- same id stamped into the raw .log text for this same request -- see LOGGING-ARCHITECTURE.md §5
    bot_id            TEXT NOT NULL,
    telegram_user_id  INTEGER NOT NULL,
    conversation_id   TEXT,               -- a UUID minted whenever context.user_data is cleared (/start, restart) -- the closest thing this platform has to "one session," see §4
    handler_kind      TEXT NOT NULL CHECK (handler_kind IN ('command', 'callback', 'text', 'photo')),
    action             TEXT NOT NULL,      -- e.g. 'profile', 'walletrc', 'chapter', 'free_text' -- derived automatically from callback_data's own prefix or a matched trigger phrase, never hand-authored per call site
    action_detail       TEXT,              -- the rest of callback_data after the action, or a short text summary -- REDACTED ("<redacted>") for any state on activity_logger.py's own denylist (email/mobile/wallet-amount collection), never the raw value
    handler_name          TEXT NOT NULL,    -- the Python function name -- ties a row straight back to one place in the code
    duration_ms              INTEGER,
    status                     TEXT NOT NULL CHECK (status IN ('ok', 'error')),
    error_summary               TEXT,        -- exception type + message ONLY, never a full traceback (that stays in the text log; correlation_id links the two)
    created_at                    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_user_activity_log_user   ON user_activity_log(telegram_user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_activity_log_corr   ON user_activity_log(correlation_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_log_bot    ON user_activity_log(bot_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_activity_log_status ON user_activity_log(status, created_at);

-- Login credentials for the NEW "bot_admin" role (2026-08-17) -- a faculty-
-- scoped admin who can view ONLY the Activity Log page, ONLY for their own
-- bot_id(s). Deliberately SEPARATE from the existing single super-admin
-- login (telegram/.env's ADMIN_PORTAL_USERNAME/PASSWORD_HASH, set via
-- set_password.py) -- that account is untouched by this table, stays the
-- one and only 'admin' role (== super_admin, sees every bot), exactly as
-- before, so nothing about Pranav's own login changes. Rows here are
-- purely additive accounts for someone else (e.g. a faculty's own admin
-- contact) who should see LESS than the full portal, never more.
--
-- WHO gets which bot_id(s) is authorization POLICY, not a secret -- that
-- lives in telegram/config/admin_access.json (human-editable, git-tracked,
-- same "JSON is the source of truth for what an id even means" pattern
-- tenants.json/bots.json/leaderboards.json already use). This table is
-- ONLY authentication (can this username log in at all) -- password
-- hashes never belong in a git-tracked file, same reasoning telegram/.env
-- is gitignored for the super-admin's own hash.
CREATE TABLE IF NOT EXISTS admin_accounts (
    admin_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash  TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

-- ===========================================================================
-- BROADCAST MESSAGES -- added 2026-08-18. Pranav's explicit ask, verbatim
-- (after the 2026-08-17 welcome-bonus broadcast, an ad hoc script with no
-- persistence): "all these broadcast message which are being done...should
-- get stored in a persistent table inside of a database..with all relevant
-- details like timestamp, category, chat id, bot id, message content
-- html.. and also if we can track their interactions on these message then
-- the same should also get tracked and stored." Two tables, same
-- "current-state row + append-only-enough trail" shape this platform
-- already uses for wallet_ledger/leaderboard_broadcast_log/
-- faculty_report_deliveries -- one row per CAMPAIGN (the message itself,
-- sent once, to many people) and one row per DELIVERY (one specific
-- chat_id's copy, its send outcome, and -- new -- whether/how they
-- interacted with it). Every future broadcast (welcome bonuses, milestone
-- congratulations, announcements, etc.) should write through these tables
-- via telegram/database/broadcast.py rather than being a one-off,
-- unlogged script -- see that module's own docstring.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS broadcast_campaigns (
    campaign_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category                TEXT NOT NULL,   -- free text, not enum-constrained -- e.g. 'welcome_bonus', 'mcq_milestone_congrats' -- same "loose on purpose, categories will grow" reasoning as bot_interactions.event_type
    message_text             TEXT NOT NULL,  -- the plain-text template (before any per-recipient personalization, e.g. an MCQ count)
    message_html               TEXT,         -- the exact HTML/markup actually sent (parse_mode=HTML), if any -- NULL if the send was plain text
    criteria_description          TEXT,       -- human-readable description of who was targeted, e.g. "MCQs answered > 10, all-time, real students, excluding admin/smoke-test accounts"
    created_by                      TEXT,     -- e.g. a script filename or 'admin:pranav-session' -- audit, not a login
    created_at                        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS broadcast_deliveries (
    delivery_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id             INTEGER NOT NULL REFERENCES broadcast_campaigns(campaign_id),
    telegram_user_id          INTEGER NOT NULL,   -- the chat_id this specific copy was sent to
    bot_id                      TEXT NOT NULL,    -- which bot process actually sent it (resolved per-recipient -- a student can only be DM'd by a bot they've started)
    message_text                  TEXT,           -- the ACTUAL text sent to THIS recipient (may differ from the campaign's own template, e.g. their real MCQ count) -- kept per-row so the true historical record never needs reconstructing from a template + external data later
    sent_at                          TEXT,
    status                             TEXT NOT NULL CHECK (status IN ('sent', 'failed')),
    error_detail                         TEXT,
    interacted_at                          TEXT,   -- NULL until the recipient does something trackable (e.g. taps a button embedded in the message) -- never guessed/inferred from unrelated activity
    interaction_type                         TEXT   -- e.g. 'report_button_tap' -- free text, not enum-constrained, same reasoning as category above
);

CREATE INDEX IF NOT EXISTS idx_broadcast_deliveries_campaign ON broadcast_deliveries(campaign_id);
CREATE INDEX IF NOT EXISTS idx_broadcast_deliveries_user     ON broadcast_deliveries(telegram_user_id);

-- Admin Portal login attempts (LOGGING-ARCHITECTURE.md sec7's "security logs" item,
-- built 2026-08-18: the cheap slice, not the full deferred pillar). Covers BOTH the
-- super-admin and every bot_admin account -- one shared login route, one shared
-- table. Every attempt is logged, success or failure (an audit trail of who logged
-- in when is useful on its own, not just for the lockout check below). Username is
-- stored AS TYPED, not validated against a real account first -- a wrong username is
-- itself a signal worth keeping (e.g. someone guessing "admin"/"pranav"/"root").
CREATE TABLE IF NOT EXISTS admin_login_attempts (
    attempt_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL,
    success          INTEGER NOT NULL CHECK (success IN (0, 1)),
    remote_addr       TEXT,        -- request.remote_addr -- this app is bound to 127.0.0.1 only (see its own module docstring), so this is mostly a formality today, kept for when/if that ever changes
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_admin_login_attempts_username ON admin_login_attempts(username, created_at);
