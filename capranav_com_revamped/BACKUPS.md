# Backups and recovery (capranav.com)

Set up end to end on 2026-09-25. Read this first if something is lost, broken or being moved.
It replaces nothing in DATABASE-BACKUP.md (the local snapshot job); it puts every backup layer in one place.

## What exists, and where each thing is protected

| Thing | Where it lives | Backup |
|---|---|---|
| Site code, pages, styles, `videos.json`, topic and Must Practice data, tools, docs | This repo | **GitHub** (`EFFICIENTCORPORATES/cap-online`), every commit |
| D1 database `capranav-platform`: students, sessions, orders, purchases, contact messages, admin users, plus the `aa_*` anatomy tables | Cloudflare D1 | 1. **Full export every 6 hours to this PC**, kept 30 days (`database-backups/`).<br>2. **The newest export copied off the PC** to R2 `capranav-backups/d1/full/YYYYMMDD.sql`, expiring after 90 days.<br>3. **Nightly dump of the critical tables** by the Worker to R2 `capranav-backups/d1/critical/YYYY/MM/DD.sql.gz`, pruned after 90 days.<br>4. Cloudflare's own D1 Time Travel (point-in-time restore); check the current retention for your plan in the dashboard. |
| R2 bucket `capranav-vault`: the two book PDFs and 98 published study-material and question-paper PDFs (100 objects, about 150 MB) | Cloudflare R2 | **Nightly incremental mirror** by the Worker to R2 `capranav-backups/vault/<same key>`. Never deletes from the mirror. Originals also exist on Pranav's PC (`books/`, `first_run/output/final_deliverable/`) |
| Anatomy (`aa_*`) tables | D1 | Rebuildable from git: `tools/build_anatomy_seed.py` then the SQL files (ANATOMY.md). Also inside every full export |
| Secrets: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `CF_EMAIL_ACCOUNT_ID`, `CF_EMAIL_API_TOKEN` | Cloudflare Worker secrets (write-only) | **Not backed up by design.** Re-issue from Razorpay and Cloudflare, or keep a copy in a password manager (Pranav's action) |
| DNS zone for capranav.com | Cloudflare | See "DNS snapshot" below. Export the full zone from the dashboard and keep it |
| Worker configuration (bindings, cron, rate limits) | `wrangler.toml` in git | GitHub |

## Schedules

* **Every 6 hours, on the PC:** Windows Task Scheduler job "CA Pranav D1 Backup" runs
  `tools/backup_d1_snapshot.py`: exports D1, saves it in `database-backups/` (gitignored, contains student data),
  uploads the newest export to R2, prunes local snapshots older than 30 days, and emails
  capranavpratiktulshyan@gmail.com if the export fails. It pins `wrangler@4.137.0` (an unpinned `npx wrangler`
  broke the job on 2026-09-24, see DATABASE-BACKUP.md).
* **Nightly at 03:00 IST (21:30 UTC), in Cloudflare:** the Worker's Cron Trigger (`crons` in `wrangler.toml`)
  runs `worker/lib/backup.js`: dumps the critical tables, mirrors any new or changed vault objects, prunes old
  dumps, writes `status.json`, and emails the owner (from `alerts@capranav.com`; this alert path has not been exercised yet) if anything failed. It works
  even when the PC is off.

## Checking that backups are healthy

```
cd capranav_com_revamped
npx wrangler r2 object get capranav-backups/status.json --remote --pipe
```
`ok: true`, a recent `at`, `vault.failures: []`. Last verified on 2026-09-25: first run copied 100 objects
(157 MB), the second run skipped all 100 (so re-runs cost nothing), and the critical dump held
student_profiles 1, orders 3, entitlements 1 and 0 rows in the other four tables.

Local: `database-backups/backup.log` has one line per run; look for `OK:` lines and `WARNING`/`FAILED`.
A gap of more than a day between `OK:` lines means the scheduled task is not running.

## Restoring

**A. Someone deleted or corrupted data in D1 (it is still there, but wrong)**
Use D1 Time Travel first: dashboard, D1, capranav-platform, Time Travel, pick a moment before the damage. This
is the fastest and loses nothing after that moment except what you choose to redo. If it is not available:

**B. The D1 database is gone or must be rebuilt**
1. Create a new database: `npx wrangler d1 create capranav-platform` and put the new id in `wrangler.toml`.
2. Load a full export (any of `database-backups/*.sql` on the PC, or `capranav-backups/d1/full/YYYYMMDD.sql`):
   `npx wrangler r2 object get capranav-backups/d1/full/20260925.sql --remote --file restore.sql`
   `npx wrangler d1 execute capranav-platform --remote --file=restore.sql`
   Do this against an **empty** database (replaying into a live one fails on duplicate keys).
3. If only the critical dump exists: run `schema.sql` and the two migration files first, then the dump:
   `npx wrangler r2 object get capranav-backups/d1/critical/2026/09/25.sql.gz --remote --file crit.sql.gz`,
   `gunzip crit.sql.gz`, `npx wrangler d1 execute capranav-platform --remote --file=crit.sql`, then rebuild the
   anatomy tables from git (ANATOMY.md).
4. `npx wrangler deploy` and test a login and the dashboard.

**C. The vault bucket lost its files**
`npx wrangler r2 object get capranav-backups/vault/<key> --remote --file <key>` for each key, then
`npx wrangler r2 object put capranav-vault/<key> --file <key> --remote`. The keys are `question-bank-book.pdf`,
`strategy-book.pdf` and the `anatomy/...` keys listed in the `aa_documents` table. The originals on the PC can
also be re-uploaded with `tools/sync_anatomy_pdfs.py`.

**D. The whole Cloudflare account is lost**
Code, data files and configuration come from GitHub; the database from any full export you have kept off
Cloudflare (see "Gaps"); secrets from Razorpay and your password manager; DNS from your zone export.

## Restore test (done 2026-09-25)

The nightly critical dump was downloaded from R2, decompressed, and loaded into a fresh database built from
`schema.sql`: all seven tables loaded with the expected row counts, no errors. **Repeat this drill every quarter**
and after any schema change (a new column must also be added to the dump list if it is a new critical table:
edit `CRITICAL_TABLES` in `worker/lib/backup.js`).

## DNS snapshot (partial, from public DNS on 2026-09-25)

| Record | Value |
|---|---|
| Nameservers | `tess.ns.cloudflare.com`, `todd.ns.cloudflare.com` |
| `capranav.com` A / AAAA | Cloudflare proxy addresses (`172.67.156.251`, `104.21.66.52`; `2606:4700:3036::ac43:9cfb`, `2606:4700:3035::6815:4234`) |
| MX / TXT at the apex | none published |
| `www.capranav.com` | no answer in this check |

This is only what public DNS shows. The email-sending records and any dashboard-only settings are not in it.
**Action for Pranav:** dashboard, capranav.com, DNS, Records, Export, and keep the file with your other records.

## Gaps (honest)

* Every backup layer above except GitHub and the PC copies is inside the same Cloudflare account. An account
  takeover or a billing suspension would affect them together. The PC copy of the 6-hourly export is the one
  independent copy of the database; keep the PC's own backups (or copy `database-backups/` somewhere else
  periodically).
* The nightly dump covers only the critical tables; the 6-hourly export covers everything.
* Secrets are not backed up (deliberate). DNS is only partly captured.
* The Windows job depends on the PC being on; a missed run is not alerted until the next run notices.
* No automated restore test yet; it is a manual quarterly drill.
