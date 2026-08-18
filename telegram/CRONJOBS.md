# CRONJOBS.md — every scheduled/unattended job on this platform, one list

**This is the single place that answers "what runs on a timer, and when."** Every
entry below was verified directly against the live Windows Task Scheduler
(`Get-ScheduledTask`/`Get-ScheduledTaskInfo`) on 2026-08-18, not copied from memory
or from another doc — if you're auditing what's actually scheduled on this machine,
trust this file's own verification date, and re-verify with the same commands (see
§4) if it's been a while since.

This machine has no real Unix cron — everything here is a **Windows Task Scheduler**
job (`schtasks`/`Register-ScheduledTask`), plus one **Startup-folder** autostart
entry (fires once at logon, not on a recurring timer, but listed here since it's the
same "unattended automation" category and shares a script with a real recurring job
below). Update this file whenever a job is added, removed, or rescheduled — a stale
list here is worse than no list.

---

## 1. The jobs

### 1LAVYA Bots - Health Check
| | |
|---|---|
| **Schedule** | Every 30 minutes, indefinitely (`PT30M` repetition, no end boundary) |
| **Runs** | `telegram\tools\ensure_bots_running.bat` |
| **Underlying command** | `manage_bots.py ensure-running` — starts any `active` bot (per `bots.json`) that isn't running at all, and RESTARTS any bot that IS running but whose heartbeat has gone stale (a hung process, not just a dead one) |
| **Why it exists** | Self-healing safety net — binds any real outage (crash, hang, a Windows update reboot) to at most 30 minutes of downtime, added 2026-08-15 after the whole platform was found down for ~4.7 hours with nothing catching it |
| **Log** | `telegram/database/run/logs/ensure_bots_running.log` (plain `.bat` `>>` append — not Python, not covered by Layer 1 rotation; covered by Layer 2's `DIRECT_MANAGE_FILES` allowlist once it crosses 5MB) |
| **Doc** | `/CLAUDE.md` §11's 2026-08-15 entry; `LOGGING-ARCHITECTURE.md` §10.1 for the log-file handling |
| **Safe to re-run concurrently?** | Yes, by design — an already-healthy bot is left completely untouched |

### 1LAVYA Platform Backup
| | |
|---|---|
| **Schedule** | Daily at 3:30 AM IST |
| **Runs** | `.venv\Scripts\python.exe telegram\tools\backup_to_cloudflare.py` |
| **What it does** | SQLite-consistent snapshots of `platform.db` + `myfiles_hub.db` (gzipped, 60-day retention) → Cloudflare R2; a full queryable D1 mirror of `platform.db` (wipe + reinsert every run); Fernet-encrypted `.env`/`creds.txt` → R2 (10-snapshot retention); MD5-vs-ETag asset sync of the live-served PDF/JSON/upload folders (`study_bot/`, `faculty/`, `exam_bot/`, `myfiles_bot/uploads/`) |
| **Explicitly excludes** | `assets/backup pdfs/` (pre-restructuring leftover, unused) and `database/run/logs/` (see the Log Rotation job below instead — a deliberately SEPARATE script/schedule, not a 5th phase bolted onto this one) |
| **Log** | `telegram/database/run/logs/backup.log` (now `RotatingFileHandler`-bounded, 20MB × 2 backups, since 2026-08-18) |
| **Alerting** | DM via `watcher_bot.py`'s sender + `alerts.json`'s `admin_chat_ids` on ANY phase failure; silent on success |
| **Audit trail** | `backup_runs` DB table — one row per run, surfaced on the Admin Portal's Bot Status page |
| **Doc** | `telegram/database/README.md`'s "Off-machine backup" section; `backup_to_cloudflare.py`'s own docstring |

### 1LAVYA Log Rotation *(new, 2026-08-18)*
| | |
|---|---|
| **Schedule** | Every 1 hour, indefinitely |
| **Runs** | `.venv\Scripts\python.exe telegram\tools\rotate_logs_to_r2.py` |
| **What it does** | Layer 2 of the log rotation policy — checks the TOTAL size of everything under `telegram/database/run/logs/`; once it crosses **800MB** (an 80% watermark under the **1GB hard ceiling** Pranav set), ships the OLDEST already-rotated log chunks (produced by Layer 1's per-process `RotatingFileHandler`, never an active/open file) to Cloudflare R2 as `logs/{bot_id}/{bot_id}_{UTC_timestamp}.log.gz`, oldest-first, deleting each locally only after a verified upload, until back under budget. Also ships+truncates a small allowlist of non-Python batch-script logs (`ensure_bots_running.log`) once THEY cross their own 5MB threshold |
| **Why hourly, not nightly (unlike the Backup job above)** | Log growth can burst within a single day at real scale — a once-a-day check risks blowing past the local budget before the next run; an hourly check is a cheap no-op almost every time |
| **R2-side retention** | 90 days |
| **Log** | `telegram/database/run/logs/rotate-logs-to-r2.log` (self-bounded, same Layer-1 policy) |
| **Alerting** | Same `watcher_bot.py` DM plumbing as the Backup job, on any ship/delete failure |
| **Doc** | `LOGGING-ARCHITECTURE.md` §10 (the full design, including 4 real bugs found + fixed while building this) |
| **Manual run** | `python telegram/tools/rotate_logs_to_r2.py --dry-run` (report only, touches nothing) / `--force` (act regardless of current total, for testing) |

### 1LAVYA Day End Faculty Reports
| | |
|---|---|
| **Schedule** | Daily at 23:50 IST — 20 minutes after the leaderboard broadcaster's 23:11 IST slot, comfortably before midnight |
| **Runs** | `.venv\Scripts\python.exe telegram\tools\generate_day_end_faculty_reports.py` |
| **What it does** | Generates a "Day End Report" PDF for every real faculty tenant (`kind=="faculty"` in `tenants.json` — `capranav`, `csarunchouhan` today; the platform-wide `1lavya-*` tenants are deliberately excluded, available on-demand instead) and writes it to `telegram/reports/day_end/{tenant_id}/{tenant_id}_{date}.pdf`. Same underlying report the Admin Portal's "Day End (Today)" button generates on-demand — this is the "also keep a standing dated archive" half of that feature |
| **Why a folder archive, not just the dashboard button** | Pranav's explicit ask: "these are initial report... we might not need this later, but now we need a separate pdf as well" — deliberately a plain folder of dated PDFs, not a new DB table or retention policy, while the platform is new |
| **Log** | No dedicated log file today — output isn't redirected by this script itself; relies on Task Scheduler's own run-history for pass/fail |
| **Doc** | `generate_day_end_faculty_reports.py`'s own docstring |

---

## 2. Windows Startup (logon-triggered, not a recurring timer)

### 1LAVYA Bots - Ensure Running.lnk
| | |
|---|---|
| **Location** | `shell:startup` (`C:\Users\<user>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\`) |
| **Fires** | Once, at Windows logon |
| **Target** | The SAME `telegram\tools\ensure_bots_running.bat` the 30-minute Health Check job above also uses — one implementation, two triggers, never two copies of the same logic to keep in sync |
| **Why both a Startup shortcut AND a recurring task** | The Startup shortcut catches the "just rebooted" case immediately, without waiting up to 30 minutes for the next scheduled check |

*(Also present in the same Startup folder: `techflowhub_autostart.bat` — unrelated to
this platform, a different project entirely. Don't touch it, don't confuse it for
one of ours.)*

---

## 3. Deliberately NOT scheduled (named honestly, not an oversight)

- **`telegram/tools/generate_dashboard.py`** (the static pre-Admin-Portal dashboard
  generator) — superseded by `dashboard_server.py`, which is a live-refreshing
  managed process (`manage_bots.py`, not Task Scheduler), not a batch job.
- **`telegram/bots/leaderboard_broadcaster.py`** — a managed, persistent process
  (see `bots.json`'s `1lavya-leaderboard-broadcaster` entry) with its OWN internal
  scheduling loop (checks every cycle, only actually broadcasts at 23:11 IST) — not
  a Task Scheduler job itself, and currently `status: "inactive"` until at least one
  leaderboard in `leaderboards.json` goes live with a real channel.
- **Database migrations / schema changes** — applied by hand (`db.py`'s
  `init_schema()` runs on every process start anyway, idempotent `CREATE TABLE IF
  NOT EXISTS`), no separate scheduled migration runner exists or is needed at this
  scale.

---

## 4. How to re-verify this list yourself

```powershell
# Every 1LAVYA-named scheduled task, current state:
Get-ScheduledTask | Where-Object { $_.TaskName -like '*1LAVYA*' -or $_.TaskName -like '*lavya*' } | Select-Object TaskName, State

# Full detail (schedule + exact command) for one task:
Get-ScheduledTask -TaskName '1LAVYA Log Rotation' | Select-Object -ExpandProperty Actions
Get-ScheduledTask -TaskName '1LAVYA Log Rotation' | Select-Object -ExpandProperty Triggers

# Last/next run + last result (0 = success):
Get-ScheduledTaskInfo -TaskName '1LAVYA Log Rotation'

# The Startup-folder shortcut:
Get-ChildItem ([Environment]::GetFolderPath('Startup'))
```

Every schedule/command in §1-2 above was captured this way on 2026-08-18, including
running the newly-created Log Rotation task twice for real
(`Start-ScheduledTask -TaskName '1LAVYA Log Rotation'`) and confirming
`LastTaskResult: 0` both times before trusting it.
