# BACKUP-STRATEGY.md — the 1LAVYA platform's off-machine backup system

**Status as of 2026-08-22**: built 2026-08-16, running nightly since. This audit
(2026-08-22) found and fixed **three real bugs** in the six nights since launch —
see §8. Read that section before assuming the system has been flawless just because
it was "verified" at build time; verification at build time is not the same as
verification under six real nights of production drift.

---

## 1. Why this exists

The whole platform — every bot, the Admin Portal, `platform.db` — runs on **one
standalone Windows PC**. See `/CLAUDE.md`'s "known scale-readiness gaps" callout,
gap #1: a single hardware/power/OS-update failure on this one machine could destroy
the only copy of every student's data, wallet balance, MCQ history, and every
sourced PDF/JSON content file, permanently, all at once. This document describes
the system built to make that survivable. It does **not** solve the other half of
gap #1 (no auto-restart-on-crash / no hosted-infra failover) — that's a service-
continuity problem, this is a data-survival problem. They're separate risks with
separate fixes; conflating them would be a mistake.

## 2. What's backed up, and what isn't

Everything under `telegram/` that is **not already safe via `git push`**:

| Data | In git? | In this backup? |
|---|---|---|
| Python code (`bots/`, `tools/`, `admin_portal/`, `database/*.py`) | ✅ | No — already safe |
| Question-bank JSON, `config/*.json` (tenants/bots/leaderboards/alerts) | ✅ | No — already safe |
| `database/platform.db` — every student, wallet ledger, MCQ attempt, admin action | ❌ (gitignored, `**/*.db`) | **Yes** — the single most important thing this system protects |
| `assets/myfiles_bot/myfiles_hub.db` + its `uploads/` (real student-uploaded files) | ❌ | **Yes** |
| `assets/study_bot/`, `assets/faculty/`, `assets/exam_bot/` (PDFs + JSON actually served to students) | ❌ (`**/*.pdf`) | **Yes** |
| `.env`, `creds.txt` (every bot token, API key, admin password hash) | ❌ | **Yes** — encrypted |
| `assets/backup pdfs/` (1.5GB, documented elsewhere in this repo as pre-restructuring leftover, unread by any code) | ❌ | **No** — deliberately excluded, Pranav's explicit call, 2026-08-13 |
| `database/run/logs/` (bot process logs) | ❌ | **No** — diagnostic, regenerates itself; has its own separate hourly overflow-shipping job, see `LOGGING-ARCHITECTURE.md` §6/§10 |

## 3. The strategy, and why this one over the alternatives

This is a **three-layer hybrid**, not one single technique — each layer of data got
whichever approach actually fits it, not a one-size-fits-all copy job.

### 3a. `platform.db` / `myfiles_hub.db` → full snapshot, nightly

**Chosen**: a complete, consistent copy every night, gzip-compressed, kept on a
60-day rolling window.

**Alternatives considered**:
- *Incremental/differential backups* (only changed pages) — the standard choice at
  real scale, but this database is ~700KB compressed. The complexity of a
  chain-of-increments (and the real risk of one broken link corrupting the whole
  chain) buys nothing at this size.
- *Continuous replication* (Litestream-style continuous WAL streaming) — would give
  near-zero data loss (RPO in seconds, not hours), but needs an always-running
  background process. This platform's backup model is a scheduled batch job, not a
  persistent service, and adding one more always-on process is its own reliability
  cost.
- **Full nightly snapshot won**: cheapest, simplest to restore (one file = one
  point in time, nothing to replay), and the DB is small enough that "cheap" is
  genuinely cheap.

Uses SQLite's own `.backup()` API — **never a raw file copy**. `platform.db` has
multiple bot processes writing to it concurrently in WAL mode at any given moment;
a raw copy could grab a half-written file. The backup API produces a real,
transactionally-consistent snapshot regardless of what's writing at the same
instant.

### 3b. D1 mirror of `platform.db` → full refresh, nightly

**Chosen**: in addition to the R2 snapshot files, a live copy of the same data in
Cloudflare D1 (a serverless SQL database), fully rebuilt (drop + recreate every
table's schema, then reinsert every row) on every run.

**Why on top of the R2 snapshots, not instead of them**: an R2 snapshot is a
gzipped file — to actually look at the data, you'd have to download it, gunzip it,
and open it locally. D1 is queryable *right now*, from the Cloudflare dashboard or
API, without any restore step. It's a convenience/verification layer on top of the
real disaster-recovery mechanism (the R2 snapshots), not a replacement for it.

**Alternatives considered**:
- *R2 snapshots only* — sufficient for disaster recovery, insufficient for "let me
  just check the data is healthy" without a restore.
- *A full hosted Postgres migration* — a much bigger, unrelated decision. This
  platform's SQLite-vs-Postgres choice is explicitly "gated on real load" (see
  memory `1lavya-bot-infra-plan`) — conflating that decision with backup strategy
  would be scope creep.
- D1 won as the lightweight middle ground: same vendor as R2, no new engine to
  learn or pay for, live-queryable today.

**Why "drop + recreate" and not "create if missing"**: see §8.1 — the original
design assumed `CREATE TABLE IF NOT EXISTS` was enough, and that assumption broke
in production. Since the row data is already being fully wiped and reinserted every
run regardless, dropping and recreating the table's *schema* too costs nothing
extra and makes schema drift structurally impossible instead of merely unlikely.

### 3c. Asset files (PDFs/JSON, several GB) → incremental delta sync

**Chosen**: compare each local file's MD5 against what's already in R2 (via R2's
own ETag, which is a plain MD5 for a single-part upload) and only upload
new/changed files.

**Alternatives considered**:
- *Full re-upload every night* — simplest code, but wasteful: re-transferring
  several gigabytes of mostly-static content every night for no reason. Measured
  directly: the very first run took **~22 minutes**; the first fully-incremental
  run after that took **35 seconds**.
- Delta sync won, obviously, once those numbers are in front of you.

**A deliberate asymmetry**: this sync can only *add* objects to R2, never delete
one because a local file went missing. A backup that can destroy backed-up content
because a local file got moved or deleted by mistake isn't a safety net — it's a
second way to lose data.

### 3d. `.env` / `creds.txt` → encrypted full backup

**Chosen**: Fernet symmetric encryption (a PBKDF2-derived key from a passphrase)
before the file ever leaves the machine, retained by count (last 10 versions).

**Alternatives considered**:
- *Don't back these up at all* — rejected: losing this machine would mean manually
  regenerating every Telegram bot token via BotFather, plus Razorpay/Cloudflare
  keys, by hand — a real, avoidable outage on top of whatever else was already
  going wrong.
- *A dedicated secrets manager* (Cloudflare Secrets Store, HashiCorp Vault, AWS
  Secrets Manager) — more "proper," but disproportionate infrastructure for this
  platform's current scale.
- Symmetric encryption won: no new service, and the only new thing to protect is
  one passphrase (which must live somewhere other than this same machine — see §6).

### 3e. Storage backend: Cloudflare R2

**Chosen** over AWS S3 / Google Cloud Storage / Backblaze B2 / a second local or
NAS drive.

- A second local/NAS drive was rejected outright — it doesn't address the actual
  risk (one building, one point of failure). Fire, theft, or a single hardware
  failure exposes a second local drive exactly as much as the first.
- Among cloud options, R2 won because: it's the same vendor already used for the
  platform's email service (and soon the domain itself); it's S3-API-compatible so
  existing tooling (`boto3`) worked unmodified; and it has **zero egress fees** —
  which matters specifically for a restore scenario where you're pulling everything
  back down, not just pushing it up.
- **Account**: the existing EfficientCorporates (ECPL) Cloudflare account, not a
  separate 1LAVYA account also on file — Pranav's call, since `1lavya.com`'s domain
  currently lives on ECPL. Revisit if/when the domain migrates.

### 3f. Scheduling: Windows Task Scheduler

**Chosen** over an always-on managed process (like the bots, via `bots.json`/
`manage_bots.py`).

An always-on process would tie this backup's own survival to the same
process-management layer whose failure this backup partly exists to protect
against, and would show as permanently "offline" between runs for no benefit (it's
a batch job, not a service). Task Scheduler runs independently, at a fixed
off-peak time (**3:30 AM daily**), survives a bot-management-layer crash, and
(confirmed over 6 real nights, see §7) has never once failed to *trigger* — every
failure since launch has been in the backup's own logic, not in getting it to run.

## 4. Architecture

```
telegram/.env                         -- CF_BACKUP_* credentials (see that file's
                                          own comments for exactly how the R2
                                          Access Key ID/Secret were derived)
telegram/tools/backup_to_cloudflare.py -- the whole pipeline, one script
telegram/database/schema.sql           -- backup_runs table (audit trail)
telegram/admin_portal/backup_status.py -- reads backup_runs for the Admin Portal

Cloudflare R2 bucket: 1lavya-platform-backups
  db-snapshots/platform_db/*.db.gz      -- 60-day retention
  db-snapshots/myfiles_hub_db/*.db.gz   -- 60-day retention
  secrets/env/*.enc                     -- last 10 kept
  secrets/creds/*.enc                   -- last 10 kept
  assets/study_bot/...                  -- mirrors telegram/assets/study_bot/
  assets/faculty/...                    -- mirrors telegram/assets/faculty/
  assets/exam_bot/...                   -- mirrors telegram/assets/exam_bot/
  assets/myfiles_bot/uploads/...        -- mirrors telegram/assets/myfiles_bot/uploads/

Cloudflare D1 database: 1lavya_platform_mirror
  -- every table in platform.db, full mirror, rebuilt nightly
```

## 5. Monitoring — how to know it's actually working

Don't just trust that a scheduled task exists — three independent signals, so a
failure can't hide:

1. **`backup_runs` table** (`platform.db`) — one row per run: started/finished
   times, status, every phase's real metrics (snapshot sizes, D1 tables/rows,
   assets uploaded/unchanged/failed, secrets backed up), and — critically — the
   exact error text of whatever failed.
2. **Admin Portal → Bot Status (`/bots`)** — a "Backup Snapshot Summary" card
   reading directly from `backup_runs`: last-run status, key metrics, and a
   10-run history table.
3. **Failure DM** — on any failed run, a Telegram DM to every configured admin
   `chat_id` (via the same `watcher_bot.py` sender used for bot down/up alerts),
   naming which phase(s) failed. **Silent on success** — no nightly "it worked"
   noise, matching the platform's existing edge-triggered alerting philosophy.

**A logging gap fixed 2026-08-22**: the DM-sending function only logged on its own
failure, never on success — so a run that failed and then successfully sent its
alert left *zero trace* in the log either way, making "did Pranav actually get
notified about these 4 failed nights" genuinely unanswerable after the fact. Fixed
to log the outcome explicitly, always.

## 6. What you (Pranav) need to do — this doesn't run itself unattended forever

1. **Save `CF_BACKUP_ENCRYPTION_PASSPHRASE` in a password manager.** It currently
   lives only in `telegram/.env`. If this machine's disk dies, that line dies with
   it, and the encrypted secrets backups in R2 become permanently unreadable — the
   whole point of encrypting them before upload is defeated if the only key is
   stored right next to what it protects.
2. **Check your Telegram DMs from the 1LAVYA MyFiles Hub bot periodically** — that's
   where failure alerts land. Don't rely on remembering to check the Admin Portal.
3. **Verify this PC's system clock stays accurate.** One backup run (2026-08-21)
   failed with an SSL certificate error that traced back to the machine's clock
   being set to the year **2030** at that moment — every real TLS certificate looks
   "expired" to a system that thinks it's 4 years in the future. This self-corrected
   by the next run and didn't cause data loss (it failed at the very first step,
   before touching anything), but it's worth knowing this machine's clock isn't
   fully trustworthy — check Windows time sync settings, or the CMOS battery if
   this recurs.
4. **Periodically glance at the Admin Portal's Backup Snapshot Summary** — an
   automated system that fails silently-to-the-owner is worse than no automation;
   the alert DM is the primary signal, this is the fallback.

## 7. Real track record, six nights (2026-08-16 → 2026-08-22)

| Night | DB snapshots | Secrets | D1 mirror | Assets | Overall |
|---|---|---|---|---|---|
| 08-17 | ✅ | ✅ | ✅ | ✅ | Success |
| 08-18 | ✅ | ✅ | ✅ | ✅ | Success |
| 08-19 | ✅ | ✅ | ❌ (schema drift, §8.2) | ✅ | Failed |
| 08-20 | ✅ | ✅ | ❌ (same) | ✅ | Failed |
| 08-21 | ✅ | ✅ | ❌ (same) | ✅ | Failed |
| 08-21 (clock anomaly) | ❌ | ❌ | ❌ | ❌ | Failed at first step (§8.4) |
| 08-22 | ✅ | ✅ | ❌ (same, pre-fix) | ✅ | Failed |

**The important nuance**: on every one of those 6 real nights, `platform.db` and
`myfiles_hub.db` were successfully snapshotted, and asset files kept syncing
correctly. **The actual disaster-recovery data was never at risk** — only the D1
*convenience mirror* went stale for 4 days. That distinction matters: this system's
phases are deliberately isolated (one phase failing doesn't abort the others),
and that design paid off exactly as intended here — a real bug degraded one
layer without silently taking down the whole backup.

## 8. Real bugs found and fixed (read this — verification at build time was not enough)

Everything below was caught by actually re-running the pipeline against real,
evolved production state on 2026-08-22 — not by re-reading the code.

### 8.1 — D1 replay didn't survive a second run against a non-empty database (found 2026-08-16, day of launch)

`CREATE TABLE IF NOT EXISTS` was assumed to come from `sqlite_master.sql`'s stored
text — it doesn't; SQLite silently strips the clause from the canonical stored DDL.
First-ever run (empty D1 database) worked by coincidence; a second run collided.
Fixed by re-inserting the clause before replay, verified against the real
already-populated database before trusting it.

### 8.2 — D1 mirror silently stopped picking up schema changes (found 2026-08-22, had been broken since 08-19)

A `session` column was added to `course_catalog` locally (via `ALTER TABLE`, by
unrelated feature work) on or before 2026-08-19. `CREATE TABLE IF NOT EXISTS` is a
no-op against a table D1 already has — so that column never reached D1, and **every
nightly run for 4 consecutive nights failed** the moment the insert step tried to
write a column D1's copy of the table didn't have. Fixed structurally: the D1
mirror now `DROP TABLE IF EXISTS` + recreates every table's schema from the current
authoritative DDL on every run, rather than assuming an existing table needs no
updates. Since row data was already being fully wiped and reinserted every run
regardless, this costs nothing extra and makes the entire bug *class* — not just
this one instance of it — impossible going forward. Verified against the real,
4-nights-stale D1 database: 37 tables, 12,834 rows, zero errors.

### 8.3 — Every asset object was stored under a doubled `assets/assets/...` prefix (found 2026-08-22, present since launch)

A path-construction bug: the relative path computed from the assets directory
already started with `assets/`, and the code prepended another `assets/` on top.
Present in every single object since the very first run — **not a data-loss bug**
(every file's content was always correct and intact, just filed under a redundant,
undocumented path that didn't match what this document or the Admin Portal claimed)
— but a real defect that would have confused anyone doing an actual restore. Fixed
in the key-construction logic; the ~2,500 already-uploaded objects were re-synced
onto the correct prefix as part of this fix's rollout (old doubled-prefix copies
cleaned up in the same pass — see the repo's commit/session history for the exact
cleanup date if reconciling object counts later).

### 8.4 — One run failed with an SSL "certificate expired" error that was actually a system-clock problem

See §6, point 3. Not a bug in this backup system — a machine-clock anomaly that
made a real, valid Cloudflare TLS certificate appear expired to Python's SSL
validation for one run. Self-corrected by the next run. Documented here because it
looked, at first glance, like a Cloudflare-side or certificate-management problem,
and wasn't.

### 8.5 — Failure alerts left no log trace either way

See §5. Fixed so the outcome of a failure-alert send is always logged, not just on
its own failure path.

## 9. Restore procedure (disaster recovery)

1. **Database**: download the newest `db-snapshots/platform_db/*.db.gz` (or
   `myfiles_hub_db/*.db.gz`), gunzip it, and use the result directly as
   `platform.db` / `myfiles_hub.db` — it's a real, complete SQLite file, not a
   diff. Nothing to replay.
2. **Secrets**: `python telegram/tools/backup_to_cloudflare.py --decrypt-secret
   <downloaded-file>` writes the decrypted plaintext to stdout (needs
   `CF_BACKUP_ENCRYPTION_PASSPHRASE` set in the environment it's run from — see §6
   on why that passphrase must exist somewhere other than the dead machine).
3. **Assets**: a plain S3 `GetObject`/sync pulls files back from the `assets/`
   prefix into `telegram/assets/`.
4. **Quick data check without a full restore**: query the D1 mirror directly
   (Cloudflare dashboard or API) — useful for confirming the data is healthy or
   answering "what did we have as of last night" before committing to a full
   machine restore.

## 10. Honest limitations

- **RPO (Recovery Point Objective) ≈ 24 hours.** Worst case, if the machine died
  right before a scheduled 3:30 AM run, up to a day of new student activity could
  be lost. This is a deliberate tradeoff (see §3a) for the platform's current scale,
  not an oversight — continuous replication would close this gap but adds an
  always-on process this design deliberately avoided.
- **RTO (Recovery Time Objective) is manual, not automatic.** This system makes
  data survivable; it does not make the *service* self-healing. If this PC dies,
  bots do not come back up somewhere else on their own — someone has to execute
  the restore procedure (§9) on a new machine. That's the "auto-restart-on-crash /
  move to hosted infra" half of gap #1, and it's a separate, larger decision, not
  yet made.
- **A backup that's never actually restored from is a hypothesis, not a proven
  fact.** Everything in §9 has been exercised in pieces (the encrypted-secrets
  round trip was proven end-to-end at launch; the D1 mirror's data integrity is
  cross-checked against the source every run) but a *full* cold-machine restore
  has never been rehearsed. Worth doing once, deliberately, before it's ever needed
  for real.
