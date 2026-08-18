# LOGGING-ARCHITECTURE.md — how this platform should observe itself

**Status: Phase 0 + Phase 1 + Phase 2 BUILT and deployed, 2026-08-17; log ROTATION
(§6's own deferred item) BUILT and deployed 2026-08-18 — see §10.** The design in §1-8
was written 2026-08-17; §9 records exactly what shipped that day and how it was
verified before touching any live, student-facing bot. §7's roadmap originally
phased this as 0→1→2→3; in practice Pranav asked for 0–2 plus a working, RBAC'd
viewer (originally §7's Phase 3) all in one pass — §9 is the accurate record of what
that actually became. Written 2026-08-17, prompted directly by a real debugging
session that day (see `/CLAUDE.md` §11's most recent entries) where diagnosing two
live bugs meant manually grepping multi-megabyte plain-text log files and, for one
of the two, reproducing the bug by hand against the live database because the
failure left no error trace at all. This doc exists so the next incident is a query,
not an archaeology dig.

**§10 is the current, active section for anyone touching logging/rotation today** —
read it first if that's your task; §1-9 are the original design record, still
accurate, but §10 is where the most recent real bugs and their fixes live.

**Read order**: §1 (the reference taxonomy) if you want the industry background this
is built on; skip straight to §2 (evaluation) and §3 (the architecture decision) if you
already know the concepts and just want this platform's plan.

---

## 0. Scope and non-goals

This platform is ~100 students, one Windows PC, SQLite, hand-managed bot processes
(see `/CLAUDE.md`'s "known scale-readiness gaps" callout). Google and Uber's logging
infrastructure (Kafka ingestion, Elasticsearch, Jaeger, petabyte-scale retention
tiering) exists to survive **thousands of services and millions of events per
second**. Copying their *infrastructure* here would be actively bad engineering —
disproportionate cost and complexity for zero benefit at this scale. What's worth
copying is their **principles**: structured events, one correlation ID per unit of
work, separating "what a user did" from "what a developer needs to debug code," and
never logging more than you can actually use. Everything below is those principles,
right-sized to one SQLite file and a handful of Windows processes — not a scaled-down
Kafka pipeline.

---

## 1. The reference taxonomy (industry background)

Researched directly (not from memory) against Google Cloud's own observability docs,
Uber's engineering blog, and general industry practice — see this doc's own commit
history / the conversation that produced it for the full source list.

Serious engineering orgs organize observability into **three pillars**: logs (what
exactly happened), metrics (how much/how often, cheaply, over time), and traces (how
one request moved through the whole system). Within "logs," the distinct *types* are:

| # | Type | What it's for |
|---|------|----------------|
| 1 | Application/debug logs | Free-text, leveled (DEBUG/INFO/WARN/ERROR), written by developers for developers |
| 2 | Access/request logs | One row per inbound request: who, what, status, latency |
| 3 | Audit logs | Who did what to which resource, when — compliance/accountability, usually scoped to sensitive actions |
| 4 | User activity / event (clickstream) logs | Every meaningful user-initiated action as a structured event — for product analytics AND replaying one user's exact journey |
| 5 | Error/exception logs | Crash tracebacks, broken out so they can be alerted on separately |
| 6 | Transaction/financial logs | Immutable ledger of money-moving events, for reconciliation and fraud detection |
| 7 | Security logs | Auth attempts, permission changes, anomalous access |
| 8 | Change/deployment logs | Every deploy/restart/config change — who, what, when |
| 9 | Performance/latency logs | How long each operation actually took |
| 10 | Distributed tracing / correlation IDs | One ID stamped on every log line and downstream call for one unit of work, so "everything about this one incident" is one query |
| 11 | Availability/heartbeat logs | Is the service alive right now |
| 12 | Metrics | Numeric aggregates, queried without touching raw logs |

Plus two practices that make all of the above actually usable at any real volume:
**structured (JSON) logging** (so logs are queryable, not just grep-able) and
**log-level/sampling/retention discipline** (INFO by default, DEBUG on demand, full
retention only for ERROR/WARN).

---

## 2. Evaluation — what this platform already has vs. the real gaps

| # | Type | Current state | Verdict |
|---|------|----------------|---------|
| 1 | App/debug logs | `logging.basicConfig()` per bot, plain text, `manage_bots.py` redirects stdout/stderr to `database/run/logs/{bot_id}.log`. Uncapped, no rotation, no separation from httpx's own noisy INFO traffic (which is most of the file's bulk) | **Have it, needs hygiene** — §6 |
| 2 | Access/request logs | httpx's own INFO lines (`getUpdates`, `editMessageText`, ...) are *in* the raw log, but unstructured and not really "ours" | **Superseded by #4** once built — no separate access log needed for a bot this size |
| 3 | Audit logs | Genuinely strong already: `wallet_ledger` (idempotent, signed amounts, reference column), `payments`, `admin_actions`, `access_requests` — all append-only with a reason/reference field | **Have it, nothing to add** |
| 4 | User activity / event logs | `bot_interactions` exists but is deliberately coarse (`event_type` is just `'start'/'callback'/'message'`, no detail — see schema.sql's own comment on why). Per-feature tables (`study_hub_events`, `exam_hub_mcq_attempts`, `report_flow_events`, `test_activity_log`, ...) are rich but each only covers its own feature | **The real gap — this is what you asked for.** §3–4 |
| 5 | Error/exception logs | Real tracebacks ARE in the raw log (PTB logs unhandled exceptions via `"No error handlers are registered, logging exception"`), but mixed into the same file as everything else, no error IDs, nothing separates "this needs attention" from routine traffic | **Have the data, missing the isolation** — §6 |
| 6 | Transaction/financial logs | `wallet_ledger`/`payments` — already idempotent, already append-only. This is the one category that already matches the research almost exactly | **Have it, nothing to add** |
| 7 | Security logs | No failed-login log for the Admin Portal; no rate-limiting/abuse log anywhere (already flagged as a platform gap in `/CLAUDE.md`'s scale-readiness callout, independent of this doc) | **Real gap, lower priority at 100 students** — deferred, see §8 |
| 8 | Change/deployment logs | Git history + `bot_heartbeats.started_at` gives "when did a process last restart," nothing structured for "who changed `tenants.json`" | **Minor gap** — single-operator context (Pranav + AI sessions) makes this low priority today |
| 9 | Performance/latency logs | Nothing captures how long a DB call, a Telegram API call, or a handler invocation actually took | **Real gap** — §3–4 (the decorator captures this for free) |
| 10 | Correlation IDs | Nothing ties one user's tap to the log lines and DB rows it produced. Yesterday's debugging had to manually eyeball timestamps across a 9MB file to find the right lines | **The other real gap** — §5 |
| 11 | Availability/heartbeat logs | `bot_heartbeats`, well-established, dashboard already reads it | **Have it, nothing to add** |
| 12 | Metrics | `analytics.py` computes aggregates from the DB at query time for the Admin Portal — functionally serves the same purpose as streaming metrics at this scale | **Have it (right-sized), nothing to add** |

**Bottom line: build #4 (fine-grained activity log) and #10 (correlation IDs)
together — they're the same piece of work — plus the log-hygiene items in #1/#5
(§6). Everything else is either already solid or genuinely not worth building yet
at 100 students.**

---

## 3. The architecture decision: one decorator, not N hand-edited functions

Your question directly: **yes, a single decorator/dispatch layer is the right
answer for the generic "who did what, when" trail — and it's *wrong* as a total
replacement for the rich, domain-specific logging this platform already does well.**
Both things are true at once; here's why, precisely.

### What a decorator CAN capture automatically, with zero edits to existing handlers

Every real handler in this codebase already has a predictable shape: an
`async def handler(update, context)` registered against a `CommandHandler`,
`CallbackQueryHandler`, or `MessageHandler`. And every action already carries a
machine-readable name for free:

- **Callback taps**: `callback_data` is already namespaced `action:value` almost
  everywhere on this platform (`profile:edit_email`, `walletrc:amount:50`,
  `chapter:3`) — the action name is `data.split(":")[0]`, no parsing needed.
- **Text messages**: every trigger phrase across every flow is already a known,
  short string (`fuzzy_trigger.py`'s `KNOWN_TRIGGERS` set is literally this
  registry already) — the action name is the matched trigger, or `"free_text"` if
  nothing matched.

So a decorator wrapping a handler can, generically, for *every* handler on the
platform, without a single edit inside any of them: identify who (telegram_user_id),
what (the action name derived as above), when (a timestamp), how long it took
(wrap start/end), and whether it succeeded or raised — and log all of that to one
table. This is precisely your "type `profile` and send, log it with a timestamp"
ask, and it costs zero changes inside `profile_flow.py`, `wallet_flow.py`,
`test_flow.py`, or any of the ~10 other flow modules.

### What a decorator CANNOT do, and must not try to

A generic wrapper has no idea that a `wallet_ledger` debit was for 500 credits at
a `test_debit` rate, or that an MCQ answer was wrong, or which chapter a question
belonged to — that's *domain* meaning, and only the code inside `wallet.py`,
`exam_hub_bot.py`'s `send_mcq()`, etc. knows it. Trying to make the decorator smart
enough to infer that would mean re-deriving business logic inside a cross-cutting
wrapper — exactly the kind of tangled, hard-to-reason-about magic that makes systems
worse, not better. **The rich per-feature tables this platform already has
(`wallet_ledger`, `exam_hub_mcq_attempts`, `study_hub_events`, `test_activity_log`,
...) stay exactly as they are, written explicitly inside the flow that knows what
happened.** The decorator adds a new, universal *envelope* layer underneath all of
them — it doesn't replace any of them.

This is the same two-layer split `bot_interactions` (generic) vs. the per-feature
tables (rich) already establishes on this platform today — this work makes the
generic layer dramatically more granular, it doesn't invent a new pattern.

### The concrete design

One new shared module, `telegram/bots/activity_logger.py` (same shape as
`cancel_utils.py`/`fuzzy_trigger.py` — a dependency-free leaf every bot imports):

```python
import functools
import time
import uuid

def log_activity(handler_kind: str):
    """handler_kind: 'command' | 'callback' | 'text' | 'photo' -- which kind of
    update this wraps, for a coarse filter without inspecting every row."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update, context):
            correlation_id = str(uuid.uuid4())
            context.user_data["_correlation_id"] = correlation_id
            telegram_user_id = _extract_user_id(update)          # update.effective_user.id
            action, action_detail = _extract_action(update)      # see below
            started = time.monotonic()
            status, error_summary = "ok", None
            try:
                return await func(update, context)
            except Exception as e:
                status, error_summary = "error", f"{type(e).__name__}: {e}"
                raise   # never swallow -- PTB's own error path must still see it
            finally:
                duration_ms = round((time.monotonic() - started) * 1000)
                _write_activity_row(
                    correlation_id=correlation_id, bot_id=BOT_ID,
                    telegram_user_id=telegram_user_id, handler_kind=handler_kind,
                    action=action, action_detail=action_detail,
                    handler_name=func.__name__, duration_ms=duration_ms,
                    status=status, error_summary=error_summary,
                )
        return wrapper
    return decorator
```

Applied at registration time, not inside every function body:

```python
app.add_handler(CommandHandler("start", log_activity("command")(start)))
app.add_handler(CallbackQueryHandler(log_activity("callback")(button_router), pattern=r"..."))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_activity("text")(text_router)))
```

One line per handler registration, in `main()` only — **never inside
`profile_flow.py`, `wallet_flow.py`, `test_flow.py`, or any flow module.** A new
flow added next month gets this for free the moment its handler is registered the
normal way.

`_extract_action()`'s job is exactly the two bullet points above (split
`callback_data` on `:`, or match against known trigger phrases) — with one
deliberate exception, covered next.

---

## 4. What actually gets written, and to where

New table, additive (never touches `bot_interactions` or any existing table):

```sql
CREATE TABLE IF NOT EXISTS user_activity_log (
    activity_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    correlation_id    TEXT NOT NULL,      -- ties this row to the SAME id stamped into the text log for this request (see §5)
    bot_id            TEXT NOT NULL,
    telegram_user_id  INTEGER NOT NULL,
    conversation_id   TEXT,               -- see "what counts as a session" below
    handler_kind      TEXT NOT NULL,      -- 'command' | 'callback' | 'text' | 'photo'
    action             TEXT NOT NULL,      -- e.g. 'profile', 'walletrc', 'chapter', 'free_text'
    action_detail       TEXT,              -- the REST of callback_data after the action, or a short text summary -- see redaction rules below, NEVER the raw text verbatim for certain states
    handler_name          TEXT NOT NULL,    -- the Python function name -- ties a row straight back to one place in the code
    duration_ms              INTEGER,
    status                     TEXT NOT NULL CHECK (status IN ('ok', 'error')),
    error_summary               TEXT,        -- exception type + message ONLY, never a full traceback (that stays in the text log, correlation_id links them)
    created_at                    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_user_activity_log_user  ON user_activity_log(telegram_user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_activity_log_corr   ON user_activity_log(correlation_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_log_action  ON user_activity_log(bot_id, action, created_at);
```

**"What counts as a session"**: this platform doesn't have one universal session
concept today (`exam_hub_sessions.session_id` is a real DB row, but it's Exam-Hub-
specific and doesn't cover Study Hub/profile/report activity). Rather than inventing
a second competing session concept, `conversation_id` is a UUID minted fresh
whenever `context.user_data` is cleared (`/start`, "Start Over", a bot restart) and
carried in `context.user_data["_conversation_id"]` for as long as that dict lives —
lightweight, requires no new DB table, and answers exactly "everything this chat_id
did in one continuous conversation," which is what a "session" means in every log
type in §1 anyway.

**Reading it back** (this is the "how do we actually use this" answer): "what did
telegram_user_id X do in the last hour" is one `WHERE` clause; "everything about
one specific bug report" is `WHERE correlation_id = ?` across BOTH this table and
the text log (§5); "which action fails most often" is `GROUP BY action, status`.
No new tooling needed beyond what the Admin Portal already has (§7 proposes a
viewer page there, later, not now).

### Redaction — the one place a blanket "log everything" rule has to bend

`profile_flow.py`/`report_flow.py`/`wallet_flow.py` all have text-input states that
collect an email address, a mobile number, or a rupee amount. Logging that raw text
verbatim into `action_detail` means the activity log itself becomes a second place
those values live, unencrypted, outside the one system (`students.email`/
`.mobile_number`) that's supposed to own them — a real compliance/privacy risk the
research flagged explicitly (this is exactly what GDPR-style audits check for).
**Rule**: `_extract_action()` maintains a small denylist of states
(`AWAITING_EMAIL`, `CONFIRMING_EMAIL`, `AWAITING_MOBILE`, `CONFIRMING_MOBILE`, the
wallet custom-amount prompt) where `action_detail` is written as the literal string
`"<redacted>"` instead of the real text — the `action` name (e.g. `"profile"`,
state `"awaiting_email"`) is still logged, just not the value itself. Every other
free-text field on this platform (a search query, a display name, an MCQ option
letter) has no such sensitivity and logs normally.

---

## 5. Correlation IDs: tying the DB row back to the text-log lines

§4's table gives you the structured side. The *raw* `.log` file (needed for real
tracebacks — `error_summary` is deliberately just the exception type + message, not
a full traceback) needs the same `correlation_id` stamped onto every line it writes
during that same request, or the two are still two separate haystacks.

Python's `logging` module supports exactly this via `contextvars` + a custom
`Filter`, with no per-call-site changes needed (same "instrument once, benefit
everywhere" shape as the decorator):

```python
import contextvars
_correlation_id_var = contextvars.ContextVar("correlation_id", default="-")

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = _correlation_id_var.get()
        return True
```

`activity_logger.py`'s decorator sets `_correlation_id_var.set(correlation_id)` at
the top of `wrapper()` (in addition to stashing it in `context.user_data`, for the
DB row); every `logging.basicConfig()` call across every bot adds
`%(correlation_id)s` to its format string and installs the filter once. Every log
line written anywhere during that handler's execution — including a real
`logger.exception(...)` traceback from deep inside `wallet.py` or `test_flow.py` —
now carries the same ID. Finding "everything about incident X" becomes: grep the
`.log` file for that one ID, or `SELECT * FROM user_activity_log WHERE
correlation_id = ?` — either direction, same answer.

---

## 6. Log file hygiene (independent of the activity log, worth doing regardless)

Found directly while debugging on 2026-08-17 — the raw log files are already
9–10MB, ungoverned, and made yesterday's search harder than it needed to be:

1. **Silence httpx's own INFO noise.** Every `getUpdates`/`editMessageText` call
   logs a full line at INFO — this is the majority of every file's bulk and isn't
   even our own code's output. `logging.getLogger("httpx").setLevel(logging.WARNING)`
   in each bot's startup, one line, keeps our own `INFO` logs while dropping this.
2. **Rotate.** Swap `logging.basicConfig()`'s default (no rotation, unbounded
   growth) for `logging.handlers.RotatingFileHandler` or
   `TimedRotatingFileHandler` — but note `manage_bots.py` currently redirects
   `stdout`/`stderr` at the OS process level (`subprocess.Popen(..., stdout=log_file)`),
   not via Python's own `logging` handlers, so rotation needs to move to a real
   `FileHandler` inside each bot's `logging.basicConfig()` instead of relying on
   shell redirection — a real, scoped change to `manage_bots.py` + every bot's
   startup, not just a config tweak.
3. **Structured format.** Add `correlation_id` per §5, and consider a JSON
   formatter once the activity log table proves the pattern is worth it — not
   blocking, plain text with a consistent correlation_id field already gets most
   of the value.

---

## 7. Roadmap

Phased so each step ships independently, gets a real regression check (this
platform's own established discipline — every fix in `/CLAUDE.md`'s history has
one), and doesn't block on the next.

**Phase 0 — log hygiene (§6), no schema change, near-zero risk**
Silence httpx INFO noise, move to a real `FileHandler` + rotation. Immediate,
low-effort, makes every future debugging session easier starting the same day.

**Phase 1 — the activity log + decorator (§3–4), the core of this doc**
`user_activity_log` table, `activity_logger.py`, wired into every handler
registration across `study_hub_bot.py`, `exam_hub_bot.py`, `faculty_bot.py`,
`myfiles_hub_bot.py`. Redaction denylist from day one, not bolted on after. Smoke
test: drive a handful of real handlers (a callback, a text trigger, a redacted
state, a forced exception) and assert the right rows land with the right fields —
same discipline every other smoke test on this platform already follows.

**Phase 2 — correlation IDs into the text logger (§5)**
`contextvars` + `logging.Filter`, format string updated in every bot's
`logging.basicConfig()`. Verify by forcing one real exception and confirming the
same ID appears in both the `.log` line and the `user_activity_log` row for that
tap.

**Phase 3 — Admin Portal viewer (optional, once Phase 1–2 have real data)**
A "Student Activity Timeline" page — pick a `telegram_user_id`, see every logged
action in order, jump straight to the correlated raw-log lines for any row marked
`status='error'`. Reuses the exact pagination/filter/export infrastructure
`admin_portal/exporters.py` already has for every other Analytics view — new query
function in `analytics.py`, new template, nothing new to build at the plumbing
level.

**Explicitly deferred, not scheduled, named honestly:**
- **Security logs (§2 row 7)** — failed-admin-login logging, rate-limiting/abuse
  detection. Real gap, but lower priority than #4/#10 at 100 students; already
  tracked as its own item in `/CLAUDE.md`'s scale-readiness callout independent of
  this doc.
- **Change/deployment logs (§2 row 8)** — low priority while this repo has a
  single human operator plus AI sessions instead of a multi-engineer team.
- **True distributed tracing / external log aggregation (Jaeger-style, per §0)** —
  only worth revisiting if this platform ever migrates off a single Windows PC
  onto real hosted infrastructure (the #1 item in `/CLAUDE.md`'s own
  scale-readiness list) — building it now would be solving a problem this
  platform doesn't have yet.

---

## 8. Open decisions needing Pranav's input before Phase 1 starts

Per this repo's own "ask before assuming on foundational changes" discipline:

1. **Retention** — how long should `user_activity_log` rows live? Unlike
   `wallet_ledger` (financial, permanent by nature), a fine-grained tap-by-tap log
   grows fast and most of it is only useful for near-term debugging. A sensible
   default (e.g. 90 days, then a periodic sweep) needs an explicit number, not an
   assumption.
2. **Who can see it** — the Admin Portal viewer in Phase 3 would let anyone with
   admin login read a specific student's full action-by-action history. Worth
   confirming that's the intended access level before it's built, not after.
3. **Redaction denylist completeness** — §4's list (email/mobile/wallet amount) is
   what exists today; any future flow that collects sensitive free text needs to
   remember to add itself to that list. Worth a lint/checklist item, not just
   documentation, before Phase 1 ships.

---

## 9. What actually got built (2026-08-17, implementation record)

Pranav's real ask went beyond §7's original Phase 0-only framing: log hygiene AND
the activity log AND correlation IDs AND a working, RBAC-gated viewer, "in one
initial phase," with an explicit, repeated instruction to be careful since real
students were practicing on these bots at the time. Built and verified in that
order, never skipping the verification step before moving to the next piece.

**Delivered:**
- **§6 hygiene**: httpx's own INFO noise silenced (`logging.getLogger("httpx").
  setLevel(logging.WARNING)`) in all 4 bots. Log ROTATION was deliberately NOT done
  via restructuring each bot's file handler (§6 originally proposed this) --
  `manage_bots.py`'s existing `subprocess.Popen(stdout=log_file)` redirection is a
  working, unmodified mechanism; touching it carried more risk than benefit for
  this pass. Rotation stays open, not shipped.
- **§3-4 activity log**: `user_activity_log` table, `telegram/bots/activity_logger.py`
  (`@log_activity` decorator), wired into the actual handler REGISTRATIONS (never
  inside any flow module) of all 4 bots -- including `myfiles_hub_bot.py`'s
  `ConversationHandler`, deliberately scoped out of the original plan but included
  once the same wrapping pattern proved safe on the other 3 bots first.
- **§5 correlation IDs**: `contextvars` + a `logging.Filter`, `LOG_FORMAT_WITH_
  CORRELATION` in every bot's `logging.basicConfig()`.
- **RBAC + viewer** (collapsed forward from §7's Phase 3, plus a genuinely new
  ask not in the original plan): a second login role, `bot_admin` --
  `admin_accounts` DB table (credentials) + `telegram/config/admin_access.json`
  (scope policy, git-tracked, same pattern as `bots.json`/`tenants.json`) +
  `telegram/admin_portal/manage_bot_admin.py` (account management, mirrors
  `set_password.py`). A `bot_admin` can reach exactly one page,
  `/logs/activity`, scoped to their own `bot_id`(s) -- every other existing route
  stays `role_required("admin")` completely untouched, so the new role is
  structurally incapable of reaching anything else, with zero changes to those
  routes. The existing super-admin login (`telegram/.env`) is untouched.

**Four real bugs found by this work's own tests, before any live bot was
touched with the change that would have shipped them:**
1. `CorrelationIdFilter` attached to the root **logger** via `addFilter()` silently
   never ran for records from any NAMED child logger (httpx, apscheduler, a bot's
   own `logging.getLogger(__name__)`) -- Python only re-applies a logger's own
   filters at the record's originating logger, not at each ancestor during
   propagation. Caught by this session's own "import every bot with a real BOT_ID,
   check for tracebacks" discipline -- every bot crashed on its first log line
   before any handler even ran. Fixed by attaching the filter to the root logger's
   **handlers** instead (`Handler.handle()` does re-check its own filters for
   every record that reaches it, regardless of origin).
2. The decorator's own exception-handling had only one layer of defense: if
   `_write_activity_row()` itself raised for a reason its internal `try/except`
   didn't anticipate, the wrapped handler's real return value could be clobbered.
   Found by this module's own smoke test deliberately monkeypatching that function
   to simulate a total DB outage. Fixed with a second, redundant `try/except`
   directly in `wrapper()`'s own `finally` block.
3. A single shared `try/except` around both `telegram_user_id` and `action`
   extraction meant a failure in ONE discarded an already-successfully-computed
   value from the OTHER -- specifically, a real `telegram_user_id` could get reset
   to `None`, which then failed `user_activity_log`'s own `NOT NULL` constraint and
   silently dropped the row. Found via an end-to-end check against real
   `exam_hub_bot.py` handlers wrapped exactly as `main()` registers them (the
   existing smoke tests call handlers directly, unwrapped, so this specific path
   was never exercised until this check was written on purpose). Fixed by giving
   each extraction its own independent `try/except`.
4. Redaction only had ONE mechanism (`context.user_data` flags), which
   `myfiles_hub_bot.py`'s `ConversationHandler`-based state (a completely different
   architecture from every other flow module) cannot be detected by at all --
   would have logged real emails and OTP codes verbatim the moment that bot's
   `AUTH_EMAIL`/`AUTH_OTP`/`DELETE_OTP` handlers were wrapped. Found by reasoning
   through myfiles_hub_bot.py's actual state machine before wiring it in, not by a
   test failure. Fixed with an explicit `always_redact=True` parameter on
   `log_activity()`, used only for those three handlers.

**Verification, before any bot restart**: `smoke_test_activity_logger.py` (36
checks, entirely synthetic, zero live-bot dependency) proves the decorator/
redaction/correlation mechanism correct in isolation. Every real bot module
(`exam_hub_bot`, `study_hub_bot`, `faculty_bot`, `myfiles_hub_bot`) re-imported
with its real `BOT_ID` (including both `capranav-*` and the flagship `1lavya-*`
variants) and checked for tracebacks -- this is what caught bug #1. A further
end-to-end check drove real `exam_hub_bot.py` handlers through the EXACT wrapped
callable `main()` constructs (not the raw functions the existing smoke tests
already called) -- this is what caught bug #3. `smoke_test_admin_portal.py` grew
by 18 checks covering the full RBAC surface: a real `bot_admin` login seeing only
their own bot's rows, provably blocked from every other existing route (403, not
a redirect), unable to widen scope via a raw query argument, and one check against
the REAL (unmocked) `verify_bot_admin_credentials()` confirming a username with no
active `admin_access.json` entry can never log in regardless of password. Full
existing regression suite (9 smoke test files, 400+ checks total) re-run clean
after every stage. Bots restarted ONE AT A TIME, each verified (fresh PID, fresh
heartbeat, zero tracebacks since restart) before moving to the next.

**Still open, named honestly**: log rotation (§6, deliberately deferred, see
above -- **built 2026-08-18, see §10**); §8's three questions (retention period for
`user_activity_log` specifically -- distinct from §10's R2-side log-file retention,
which IS now answered -- full audit of who should see `/logs/activity`, keeping the
redaction denylist complete as new flows get added) remain genuinely unanswered --
nothing in this pass required an answer to ship, but they don't go away either.

**Correction, 2026-08-18**: a routine activity-log review the next day found the
correlation-ID mechanism above (§5, bug #1's fix) had its OWN bug from day one --
`activity_logger.py`'s decorator reset the `contextvars` correlation ID
unconditionally in its `finally` block, which runs BEFORE a re-raised exception
actually leaves the function -- so by the time `telegram.ext.Application` logged the
real traceback moments later (same task, no intervening `.set()` call), the ID was
already back to `"-"`. Confirmed against all 3 real tracebacks in production at the
time: every one showed `[-]` instead of its row's actual correlation UUID, directly
contradicting this section's own "verify by forcing one real exception" claim above.
**Fixed 2026-08-18**: the `finally` block now only resets on the SUCCESS path (`if
status == "ok":`) -- on error, the ID is deliberately left set so PTB's own traceback
logger (same task, moments later) gets the real value; the next wrapped call's own
`.set()` overwrites it before anything else meaningful runs, so nothing leaks
long-term. Verified with a direct repro (not just the existing smoke test, which
never exercised the actual PTB-exception-logging-after-wrapper-returns sequence) both
for the error path (ID survives) and the success path (still resets cleanly, no
regression). `smoke_test_activity_logger.py`'s existing 36 checks re-run clean.

---

## 10. Log rotation, built 2026-08-18 (§6's deferred item, now closed)

Pranav's ask, verbatim shape: **1GB total local budget** for everything under
`telegram/database/run/logs/`, combined; anything that would push the total over
that gets **zipped and shipped to Cloudflare R2, under a folder identifiable by
timestamp**; and the logs staying on the local machine needed **confirmed** to
already be covered by continuous off-machine backup.

### 10.0 The backup claim, checked and corrected before building anything

Pranav believed the logs were already both R2-backed-up and git-tracked. Neither was
true, confirmed directly rather than assumed:
- `telegram/tools/backup_to_cloudflare.py`'s own docstring says outright:
  *"DELIBERATELY EXCLUDED: ... `database/run/logs/` (diagnostic, regenerates
  itself)."* The nightly backup job has never touched the logs folder.
- `.gitignore` line 127 excludes `telegram/database/run/` entirely, and `git
  ls-files telegram/database/run/` returned zero tracked files -- confirmed, not
  inferred.

This is exactly why §10's design below folds R2 shipping into the rotation policy
itself (Layer 2) rather than assuming a separate mechanism already had it covered.

### 10.1 The two-layer design

**Layer 1 -- per-process bounded rotation** (`telegram/database/log_rotation.py`,
new). Every process's `logging.basicConfig()` now gets an explicit
`handlers=log_rotation.build_handlers(bot_id)` instead of the old implicit
stderr-only default. `build_rotating_handler(bot_id)` wraps
`logging.handlers.RotatingFileHandler` at `MAX_BYTES = 20MB`, `BACKUP_COUNT = 2` --
so each process keeps at most 1 active + 2 rotated chunks (~60MB worst case) locally,
writing to the EXACT SAME path (`database/run/logs/{bot_id}.log`) `manage_bots.py`
and the Admin Portal's Bot-wise Logs viewer already expect -- zero changes needed in
either consumer, only WHO writes that file changed.

Wired into all 9 active processes (all 6 real Telegram bots via `study_hub_bot.py`/
`exam_hub_bot.py`/`myfiles_hub_bot.py`, `faculty_bot.py`'s own call is a documented
no-op since `study_hub_bot`'s import wins the root-logger race first) plus
`dashboard_server.py`, `watcher_bot.py`, `admin_portal/app.py` (which had NO logging
config at all before this), and `leaderboard_broadcaster.py` (currently inactive,
fixed for when it goes live). `backup_to_cloudflare.py`'s own already-explicit
`FileHandler` was also upgraded to `RotatingFileHandler` for consistency (low-risk --
it's a run-to-completion batch job, no cross-restart file-lock concern at all).

**Layer 2 -- the global ~1GB ceiling, overflow to R2**
(`telegram/tools/rotate_logs_to_r2.py`, new). Runs hourly (Task Scheduler -- see
`CRONJOBS.md`), reuses `backup_to_cloudflare.py`'s R2 client/bucket/credentials
directly (imported, not duplicated -- same bucket, new `logs/` key prefix). Checks
the TOTAL size of everything under `database/run/logs/`; once it crosses an **800MB
watermark** (80% of the 1GB ceiling -- headroom against bursty growth between hourly
checks, never actually hits the hard limit in practice), ships the OLDEST
already-rotated chunks (`{bot_id}.log.1`, `.log.2`, ...) to R2 as
`logs/{bot_id}/{bot_id}_{UTC_timestamp}.log.gz`, deleting each locally only after a
verified successful upload, oldest-first, until back under the watermark. **Never
touches an active `{bot_id}.log`** (still open, owned by a live process) -- only
files Layer 1 has already rotated OUT, which Python's logging module closes before
renaming, so nothing holds them open once they exist under that name. A small
allowlist (`DIRECT_MANAGE_FILES`, currently just `ensure_bots_running.log`) covers
non-Python batch-script logs with no owning long-running process holding them open --
shipped whole + TRUNCATED (never deleted, since the `.bat` script's next `>>` append
assumes the file still exists) once they cross their own 5MB threshold. R2-side
retention: 90 days (matches §8's original suggested default for the DB-side
question, now answered for the log-file side specifically). On any failure, alerts
via the same `watcher_bot.py` DM plumbing `backup_to_cloudflare.py` already uses.

`--dry-run` reports what WOULD ship/delete, touches nothing; `--force` ships
regardless of the current total (for testing).

### 10.2 `manage_bots.py`'s own change

`start_bot()` used to redirect the child process's stdout/stderr straight into
`f"{bot_id}.log"` -- the SAME file Layer 1's `RotatingFileHandler` now owns directly.
Two independent writers holding the same file open (one unbounded OS-level append,
one in-process handler that occasionally renames/truncates it) would fight each
other. Fixed: that redirect now goes to a separate, small `f"{bot_id}.crash.log"`
instead -- its only real job is catching something that happens BEFORE the bot's own
`logging.basicConfig()` runs (an import error at the very top of the script) or
bypasses the logging module entirely (Python's unhandled-exception printer, the
`warnings` module -- both write straight to real OS-level stderr independent of any
logging handler). `start_bot()` also now sets `env["BOT_MANAGED"] = "1"` on every
process it launches -- see the next section for why.

### 10.3 Four real bugs found while building this, each caught by actually checking

Every one of these was caught by inspecting the REAL restarted processes' real log
files and a real Task-Scheduler-triggered run -- not by reading the code, matching
this platform's own established "0 structural errors isn't enough" discipline
(`/CLAUDE.md` §7, `FIRST_PROMPT.md`'s own lessons list).

1. **StreamHandler duplication into crash.log.** The first draft of every process's
   `handlers=[...]` list included a bare `logging.StreamHandler()` alongside the
   `RotatingFileHandler`, for local/interactive terminal visibility. That
   StreamHandler writes to stderr -- which `manage_bots.py`'s own redirect (10.2)
   ALSO captures wholesale into `crash.log`. Result: every routine log line was
   being duplicated into TWO files, one bounded and one NOT -- the exact "two full
   copies in two places" class of bug already found once this same day (see #4
   below) reintroduced by this fix's own first draft. Confirmed by restarting a bot
   and watching BOTH `{bot_id}.log` AND `{bot_id}.crash.log` grow in lockstep with
   ordinary apscheduler tick lines. Fixed: `env["BOT_MANAGED"]` (10.2) + a new
   `log_rotation.build_handlers()` that only adds the StreamHandler when that env
   var is NOT set -- a developer's manual `python study_hub_bot.py` run still gets
   live terminal output, a `manage_bots.py`-launched process does not duplicate.
2. **Werkzeug bypasses root-logger handlers entirely.** `admin_portal/app.py`'s
   Flask/Werkzeug dev server does NOT simply propagate its request-log lines to the
   root logger's handlers, contrary to this doc's own first-draft comment claiming
   it does. Werkzeug's `serving` module checks whether the `'werkzeug'` logger
   already has a handler of ITS OWN; finding none, it attaches a bare
   `StreamHandler` directly to that logger with `propagate=False` -- so every
   request line ("GET / 302") went straight to stderr, captured by
   `manage_bots.py`'s redirect into the unbounded `crash.log`, bypassing the
   bounded handler entirely. Caught by literally curling the restarted process and
   checking which file the request line landed in. Fixed: `admin_portal/app.py` now
   explicitly assigns `logging.getLogger("werkzeug").handlers` to the SAME handler
   list and sets `.propagate = False` itself, BEFORE `app.run()` ever gets a chance
   to trigger Werkzeug's own auto-attach check -- finding handlers already present,
   it never adds its own. Re-verified against the live process: the same curl now
   lands correctly in the bounded `.log`, `crash.log` stays at 0 bytes.
3. **`rotate_logs_to_r2.py`'s own log landed in `backup_to_cloudflare.py`'s file.**
   Import order bug: `rotate_logs_to_r2.py` imported `backup_to_cloudflare` (which
   calls its OWN `logging.basicConfig()` at import time) BEFORE calling its own
   `logging.basicConfig()` -- Python's `basicConfig()` is a no-op once the root
   logger already has handlers, so `backup_to_cloudflare`'s config silently won the
   race every time. Caught by triggering the real Task Scheduler job and finding
   `rotate-logs-to-r2.log` untouched (0 bytes) while `backup.log` had gained new
   entries at exactly the scheduled run's timestamp. Fixed: moved
   `rotate_logs_to_r2.py`'s own `logging.basicConfig()` call to run BEFORE `import
   backup_to_cloudflare`. Re-verified against a real, second Task-Scheduler-triggered
   run: the entry now lands in the correct file.
4. **A pre-existing duplicate log file, found auditing every process's setup.**
   `myfiles_hub_bot.py` had its OWN separate `FileHandler` writing to
   `assets/myfiles_bot/myfiles_hub.log` (next to its DB), IN ADDITION to
   `manage_bots.py`'s OS-level capture of that same handler-set's StreamHandler
   output into `database/run/logs/1lavya-myfileshub.log` -- two full copies, in two
   locations, and (confirmed by reading `admin_portal/app.py`'s log-viewer route
   directly) neither the Admin Portal nor anything else ever read the
   `assets/myfiles_bot/` copy. Already 12.5MB, pure waste. Consolidated onto the
   same `log_rotation.build_handlers()` every other bot now uses, writing only to
   the one path that's actually read; the orphaned 12.5MB file was deleted.

### 10.4 Verification

`telegram/tools/smoke_test_log_rotation.py` (new, 29 checks, zero real-file/real-R2
dependency): Layer 1's rotation actually triggering and producing a `.log.1`
sibling; Layer 2's watermark trigger, oldest-first ordering, `--dry-run` touching
nothing, a failed upload leaving the local file in place (never deleted on
failure), `DIRECT_MANAGE_FILES` shipping-then-TRUNCATING (never deleting); a
permanent regression guard for bug #1 (`BOT_MANAGED` correctly suppresses the
StreamHandler only when set); a permanent regression guard for bug #2's general
pattern (a third-party logger pre-armed with our handlers + `propagate=False`
actually receives records, the general shape of the Werkzeug fix). All entirely
inside a temp directory with a `LOG_DIR` monkeypatch restored in a `finally` block --
never touches the real `database/run/logs/` or makes a real network call.

Full existing regression suite re-run clean after every stage (`smoke_test_
activity_logger.py` 36/36, `smoke_test_report_flow.py`, `smoke_test_profile_flow.py`
59/59, `smoke_test_leaderboards.py` 28/28, `smoke_test_test_flow.py` 99/99,
`smoke_test_exam_hub_wallet.py` 41/41, `smoke_test_wallet_flow.py` 21/21,
`smoke_test_admin_portal.py`, `smoke_test_course_catalog.py`'s content-validator
check -- all passing, zero regressions from this pass).

All 9 active processes restarted ONE AT A TIME (the 10th, `1lavya-leaderboard-
broadcaster`, stays inactive per its own unrelated gating), each verified before
moving to the next: fresh PID, fresh heartbeat, `crash.log` confirmed to stay at (or
return to) 0 bytes -- except `1lavya-myfileshub`'s, which correctly caught one
pre-existing, one-time `PTBUserWarning` (bypasses the logging module entirely, same
category as a genuine crash, correctly still caught). `user_activity_log` showed 0
new `status='error'` rows across the entire restart sequence.

The real Windows Scheduled Task ("1LAVYA Log Rotation", hourly, see `CRONJOBS.md`)
was triggered twice for real during this build (`Start-ScheduledTask`) -- both times
`LastTaskResult: 0`, `NextRunTime` correctly one hour out, and (after bug #3's fix)
its own log content landing in the correct file.

### 10.5 What's genuinely NOT covered, named honestly

- **`user_activity_log`'s own retention** (§8 Q1, the DB-table row-count question --
  distinct from this section's R2 log-FILE retention, which IS answered at 90 days)
  is still open.
- **No dedicated smoke-test coverage for `mcq_issue_flow.py`** or the
  `safe_edit_message_text`/correlation-ID fixes made earlier the same day (2026-08-18)
  during the activity-log review that prompted this whole rotation pass -- those were
  verified by direct repro + full existing-suite re-runs + live-process restarts, not
  a new permanent smoke-test file, since they're outside this doc's own scope
  (Markdown-parsing and Telegram-API-quirk fixes, not logging architecture).
- **The existing large log files won't shrink retroactively.** Several bots' current
  active `.log` files (e.g. `csarunchouhan.log` at ~11MB) are still under the new
  20MB Layer-1 threshold, so they won't rotate until they cross it naturally --
  expected, not a bug; the policy governs growth going forward, not a one-time
  cleanup of pre-existing content.

---

## 11. Two more §8/§7 items closed the same day (2026-08-18, later)

Asked directly what was still pending per this doc; both answered and built the same
session rather than left open further.

### 11.1 §8 Q1 answered: `user_activity_log` retention = 180 days

Pranav's explicit choice (AskUserQuestion, 2026-08-18) -- distinct from §10's R2
log-FILE retention (90 days), which governs shipped `.log.gz` chunks, not this DB
table's own rows. New `telegram/tools/purge_activity_log.py` -- deletes
`user_activity_log` rows older than `RETENTION_DAYS = 180` via
`strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-180 days')`, the same format the column
itself is stored in (no Python-vs-SQLite format mismatch risk). `--dry-run` reports
the count without touching anything. Deliberately a SEPARATE script from
`backup_to_cloudflare.py`/`rotate_logs_to_r2.py` (different concern -- deleting DB
rows, not shipping files -- and a much lighter cadence, daily is generous for a
180-day window), matching this platform's established "one script, one job"
precedent. Scheduled via a new Task Scheduler job, "1LAVYA Activity Log Purge",
daily -- see `CRONJOBS.md`.

Verified with a real, synthetic-row test against the real DB (not just a 0-rows-
deleted no-op run, which wouldn't have proven the `WHERE` clause correct): inserted
one row 200 days old and one row 1 day old, ran the real purge, confirmed the old
row was deleted and the recent row survived, cleaned up. New permanent regression
test, `telegram/tools/smoke_test_purge_activity_log.py` (5 checks, including an
exactly-at-the-180-day-boundary case), plus the real Task Scheduler job triggered
once for real (`LastTaskResult: 0`, correct `NextRunTime`, output confirmed landing
in its own `purge-activity-log.log`, not another script's -- learned that exact
import-order lesson the hard way in §10's bug #3, applied correctly here from the
start).

### 11.2 §7's "security logs" item, the cheap slice: failed-login logging + lockout

Not the full deferred pillar (still no IP-reputation/abuse-pattern detection, still
not scheduled) -- specifically the piece flagged as worth doing NOW rather than
deferred further: the Admin Portal controls live bot restarts and (with Test Mode
billing live) real money, and had zero record of anyone attempting to brute-force
its login before this.

New `admin_login_attempts` DB table (`schema.sql`) -- one row per login attempt,
success or failure, for BOTH the super-admin and every `bot_admin` account (one
shared login route, one shared table). `admin_portal/auth.py` gained
`log_login_attempt()` (best-effort, never blocks the actual login outcome -- same
"logging must never break the product" principle `activity_logger.py` already
established) and `is_locked_out()` -- `MAX_FAILED_ATTEMPTS = 5` within a
`LOCKOUT_WINDOW_MINUTES = 15` rolling window. `app.py`'s `/login` route checks
`is_locked_out()` FIRST, before even looking at the submitted password -- a
locked-out account is refused even with the CORRECT password, which is the whole
point.

**Deliberate design choice, stated plainly rather than left implicit**: a
SUCCESSFUL login does NOT reset the failure counter -- it's a pure rolling window
that only ages out after `LOCKOUT_WINDOW_MINUTES`. More conservative (an attacker
who gets lucky once doesn't get a fresh attempt budget) at the cost of a legitimate
admin who mistypes a few times, gets it right, then mistypes again minutes later
finding themselves locked out. No real harm either way -- the lockout is time-boxed,
never permanent, never requires a manual unlock.

Verified three ways: (1) a real, synthetic-username test directly against
`auth.py`'s functions (4 failures = not locked, 5th = locked, a different username
unaffected, a success does NOT reset the count); (2) a new Step 2b in
`smoke_test_admin_portal.py` (10 checks) driving the REAL `/login` route through
Flask's test client, confirming the lockout message renders and no session is
created even when the password would otherwise verify; (3) a live curl-based test
against the actual restarted, running process -- 5 failed POSTs, a 6th correctly
showing "Too many failed attempts," confirmed via a direct query against the real
`admin_login_attempts` table, cleaned up. `1lavya-admin-portal` restarted, confirmed
clean (fresh PID, `crash.log` stays at 0 bytes, the real login flow for the actual
admin account re-verified working immediately after via the existing Step 3 check).

**Still deferred, unchanged**: IP-based rate limiting/reputation, a dedicated Admin
Portal viewer page for `admin_login_attempts` (the table exists and is queryable via
the existing SQL Query tab today; a dedicated Analytics view wasn't asked for this
pass), and change/deployment logs (§7 -- still low priority at single-operator
scale). Full regression suite (10 smoke-test files) re-run clean after both 11.1 and
11.2; `health_check.py`: same pre-existing failures, nothing new.
