# 1Lavya MyFiles Hub Bot — README

**Display Name:** 1Lavya MyFiles Hub
**Bot Username:** @Official1LavyaMyFilesBot
**Script file:** `myfiles_hub_bot.py`

## What this bot is for

A personal cloud file manager inside Telegram — students upload their own
files (or links) and tag them, then can retrieve or bulk-download them
later without needing an app. Positioned as a lighter-weight alternative
to Google Drive: no separate app to open, downloads happen straight in
chat.

**Tagging is free-form, not a folder hierarchy.** There is no fixed
Category/Subject/Level/Chapter structure. Each student owns their own tag
list — create, rename, or delete tags anytime — and picks up to 5 tags per
upload from a multi-select keyboard. A file can carry several tags at once,
and retrieval lets a student combine tags with **ALL (AND)** or **ANY (OR)**
matching.

## How a student uses it

0. **Waking the bot**: `/start`, or a casual opener ("Hi", "Hey", "Hello",
   "Hiya", "Yo", "Namaste" — case-insensitive) for a chat that hasn't
   started a conversation yet. `/start` also always works as a reset even
   mid-conversation (e.g. if a student gets stuck) — greetings only fire
   as a fresh opener, they won't misfire on ordinary replies mid-flow
   (typing "hi" as a chapter name, for instance, is safe).
1. `/start` (or a greeting) → bot asks: **existing user or new user?**
2. Either way → student enters their **email address** → bot emails a
   **6-digit OTP** → student enters it in chat to verify
3. New users are also asked to set a **display name** — and are seeded with
   a **starter set of tags** (Study Material, Practice/Exam Material,
   Accounting, Costing, Taxation, Law, Audit) they're free to rename, delete,
   or add to from that point on. No student ever starts from a totally blank
   tag list.
4. Once verified, main menu offers:
   - **📤 Upload a file/link** — send a document, a photo, or paste a link.
     - Send several at once (e.g. an album of photos) and the bot buffers
       them for ~1.5s, then asks whether they all share the same tags:
       - **Yes** → one multi-select tag picker, applied to every file in
         the batch.
       - **No** → the bot discards the batch and asks the student to send
         only similarly-tagged files together, or one at a time.
     - A single item skips that question and goes straight to a
       **multi-select tag picker**: tap tags to check/uncheck them (up to
       5), or **➕ New Tag** to create one on the fly and have it
       auto-selected, then **✅ Done** to save. A student with zero tags
       yet is asked to create their first one before the picker appears.
     - After saving (single item or a whole batch), the bot never just
       goes quiet — it confirms what was saved (and which tags), then asks
       explicitly: **📤 Upload more files** or **✅ Done for now** (rather
       than dropping straight into the full main menu).
   - **📥 My Files** — the same multi-select tag picker as upload, plus a
     **Match: ANY (OR) / ALL (AND)** toggle button, then **🔍 Show results**.
     Example: picking "Study Material" + "Accounts" with **ALL** shows only
     files carrying both; with **ANY** it shows files carrying either.
     - From the results list: send one file, or **send all** (auto-zipped
       if large). There is no delete option here — deletion is a
       separate, deliberate menu action (see below).
   - **🏷️ My Tags** — the tag list itself: **➕ Create New Tag**, or per
     existing tag, **✏️ rename** / **🗑️ delete** (with a one-tap confirm).
     Deleting a tag only removes it from whatever files had it — the files
     themselves are never touched.
   - **📊 My Stats** — total files/links uploaded, total storage used, and
     a breakdown by tag (a file with several tags counts under each one).
   - **🗑️ Delete My Files** — a separate, explicit entry point (never
     shown inline with normal browsing). Filter by tags the same way as
     My Files, review what would be removed, then tap to request removal.
     The bot emails a confirmation OTP explaining plainly what will
     happen; entering it in chat is required before anything is removed.
     Deletion is still a **soft delete** (hidden from the student, not
     erased from storage) — the email is worded to match that, not to
     claim permanence.

## How the backend works

- Runs as a **Python script on a laptop** (not a cloud server) — must
  stay running to respond.
- **SQLite database** (`myfiles_hub.db`) holds six tables:
  - `users` — chat_id, email, display_name, verified flag
  - `otps` — pending OTP codes with expiry (auto-cleared after use); a
    `purpose` column (`login` or `delete`) keeps a login code from ever
    being usable to confirm a deletion, or vice versa
  - `files` — every uploaded file/link, storage path or URL, a
    `file_size_bytes` column (used by My Stats and the activity log), and
    an `is_deleted` soft-delete flag. (Legacy `category`/`subject`/`level`/
    `chapter` columns still exist for the handful of rows saved before the
    tag redesign, but nothing new writes to them.)
  - `tags` — one row per student-created tag (chat_id, name, created_at).
    Fully student-owned, not a shared/fixed list. Name matching is
    case-insensitive per student, so "Accounts" and "accounts" collapse
    to one tag.
  - `file_tags` — the many-to-many join between `files` and `tags` (a
    file can carry several tags; a tag can label many files). Capped at
    `MAX_TAGS_PER_FILE` (5) per file by the app, not the schema.
  - `activity_log` — one row per login, register, upload, retrieve,
    delete request/confirm, and tag create/rename/delete: chat_id, email,
    action, detail (e.g. filename or tag name), file size, timestamp
  - SQLite was chosen over Excel specifically because multiple students
    can upload/tag/delete at the same time — Excel isn't safe for
    concurrent read/write. The data can still be exported to Excel
    anytime for the client's reporting needs.
  - `init_db()` runs a small, idempotent migration on every startup
    (`ALTER TABLE ... ADD COLUMN` / `CREATE TABLE IF NOT EXISTS`, guarded
    by a `PRAGMA table_info` check where relevant) so an already-existing
    database picks up new columns/tables without needing to be deleted
    and recreated. Verified safe against the real database before this
    change shipped — existing rows were untouched, new tables/columns
    just appeared alongside them.
- **Storage**: real uploaded files (documents and photos) are saved to
  `BASE_STORAGE_PATH/<telegram_chat_id>/` — one folder per student,
  named by their unique Telegram chat ID. Links (no file, just a URL)
  are stored only as a database row — no disk object.
- **Batch uploads**: files sent together (e.g. a Telegram photo album)
  arrive as separate messages sharing no explicit "done" signal, so the
  bot buffers them for `BATCH_DEBOUNCE_SECONDS` (1.5s) after the last
  item before asking about tagging — implemented with a cancel-and-
  reschedule `asyncio.create_task`, no extra dependency required. Because
  that background task can't move python-telegram-bot's own conversation
  state, the tag-picker's callback handlers are deliberately registered
  in two states (the upload-wait state and the tag-select state) so the
  very first tap after the bot-initiated prompt is always caught correctly
  regardless of which state the library still thinks it's in.
- **OTP delivery**: sent via email using SMTP (e.g. a Gmail account with
  an App Password) — see config block in the script. Two kinds of OTP
  email exist: the login code, and a separate delete-confirmation code
  whose body explicitly states what removal does and does not do.
- **Bulk download**: when a student requests multiple files, the bot
  zips them into ~45MB parts (Telegram's hard cap is 50MB) and sends
  each zip as a separate message.
- **Delete = soft delete only, gated behind OTP**: marking `is_deleted = 1`
  in the database. The file always stays on disk; it's just hidden from
  the student's view and search results. Reaching this action requires
  the student to deliberately choose **🗑️ Delete My Files** from the main
  menu (never shown by default while browsing) and then enter the emailed
  confirmation code.
- **Activity logging**: every key action writes a row to `activity_log`
  (best-effort — a logging failure never blocks the bot). Run
  `python myfiles_activity_report.py` for a readable summary (per-student
  file counts/storage, activity counts by type, recent events), or add
  `--csv path.csv` to export the full log. The bot's own operational
  logs (startup, errors) are also now written to
  `<folder containing myfiles_hub.db>\myfiles_hub.log`, not just the
  console, so they survive after the terminal closes.

## Setup checklist for the developer

1. `pip install python-telegram-bot python-dotenv --break-system-packages`
   (sqlite3, smtplib, zipfile are all standard library — no extra
   install needed for those)
2. Get the bot's API token from **@BotFather** (registered as
   `@Official1LavyaMyFilesBot`)
3. Copy `telegram/.env.example` to `telegram/.env` (gitignored — never
   commit it) and fill in:
   - `TELEGRAM_MYFILES_BOT_TOKEN` — the BotFather token
   - `MYFILES_SMTP_EMAIL` / `MYFILES_SMTP_PASSWORD` — for sending OTP
     emails (Gmail needs an **App Password**, not the real account
     password)
   - `myfiles_hub_bot.py` loads `telegram/.env` automatically at startup
     (via `python-dotenv`) — no shell exports needed for local runs.
4. In `myfiles_hub_bot.py`, still set directly (not secrets, just local
   paths — not yet repo-relative, see "Things to flag" below):
   - `BASE_STORAGE_PATH` — where per-student folders get created
     (currently `telegram\assets\myfiles_bot\uploads`)
   - `DB_PATH` — where the SQLite database file lives
     (currently `telegram\assets\myfiles_bot\myfiles_hub.db`)
5. Run: `python myfiles_hub_bot.py` — this also auto-creates the SQLite
   tables on first run.
5. Test the full loop with a real email you control: register → receive
   OTP → verify (confirm the starter tags show up in My Tags) → upload a
   photo and a document (try sending 2-3 at once too, picking 2+ tags and
   also trying ➕ New Tag mid-upload) → retrieve via My Files with an
   AND search and an OR search → try "send all" → rename and delete a
   tag in My Tags → check My Stats → try Delete My Files end-to-end
   (confirmation email + OTP).
6. Check `python myfiles_activity_report.py` prints what you'd expect
   after that test loop.

## Things to flag with the client before launch

- **Secrets fixed 2026-08-09**: the bot token and Gmail App Password used
  to be hardcoded directly in `myfiles_hub_bot.py` (a live, working token
  and password, in a file that was about to be committed unencrypted).
  Both now load from `telegram/.env` (gitignored) via `python-dotenv` —
  see the setup checklist above. `BASE_STORAGE_PATH`/`DB_PATH` are still
  hardcoded absolute `D:\...` paths, not secrets but also not
  repo-relative yet (unlike `study_hub_bot.py`) — worth the same fix if
  this bot ever needs to run from a different machine/clone.
- **No student allow-list yet.** Right now *any* email address can
  register — there's no check against a pre-approved list of enrolled
  students. There's a `# TODO: validate against enrolled student list`
  comment in `auth_email_received()` where that check can be added if
  the client wants registration restricted.
- **`STARTER_TAGS` and `MAX_TAGS_PER_FILE` are hardcoded** near the top of
  the script — the starter set is just a convenience seed for new
  students (they can rename/delete every one of them immediately), and
  5 tags/file is an easy number to change if it turns out too low/high
  in practice.
- **Tags are entirely student-owned and per-student** — there's no
  shared/global tag list across students, and no admin view into what
  tags exist across the whole student base yet. If the client wants to
  see "what tags are students actually using" in aggregate later, that's
  a small addition to `myfiles_activity_report.py` (tag creates are
  already logged to `activity_log`), not a schema change.
- **Tag names are case-insensitive per student** ("Accounts" and
  "accounts" collapse to one tag) but two *different* students can each
  have their own "Accounts" tag — tags never leak across students.
- **Batch upload has a ~1.5s pause by design** — after sending a file,
  the bot waits briefly to see if more are coming before asking about
  tags. Expected, not a bug, but worth explaining to students so a short
  pause after uploading doesn't read as the bot being unresponsive.
- **Deletion is still soft-delete**, now explicit about it in the
  confirmation email — flagged in the previous review round and kept
  soft-delete deliberately (see the OTP-confirmation email wording). If
  the client later wants files genuinely erased from disk on deletion,
  that's a separate, bigger decision (loses the current safety net) and
  should be a deliberate ask, not a silent change.
- No payment/premium gating yet — fully free for now.
