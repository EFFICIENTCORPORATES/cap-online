# Database backups — capranav.com

The live site's database (accounts, sessions, orders, entitlements, contact
messages) lives entirely in **Cloudflare D1** — there is no local database
file for the running site (see the note at the bottom for how that was
confirmed). This document covers the **local safety copy** on top of that:
a scheduled job that exports a snapshot to this machine every 6 hours, in
case D1 itself is ever unreachable, a bad query wipes something, or the
Cloudflare account needs to be recovered from.

## What runs, and when

- **Script**: `tools/backup_d1_snapshot.py`
- **Schedule**: Windows Task Scheduler job **"CA Pranav D1 Backup"**, every
  6 hours, indefinitely (registered `2026-09-02`).
- **What it does**: runs `wrangler d1 export capranav-platform --remote`,
  saves the result as a timestamped `.sql` file in `database-backups/`, logs
  the outcome to `database-backups/backup.log`, then deletes any snapshot
  older than 30 days.

Run it by hand any time:
```
cd capranav_com_revamped
python tools/backup_d1_snapshot.py
```

## Where the files go

`capranav_com_revamped/database-backups/`
- `capranav-platform_YYYYMMDD-HHMMSS.sql` — one full snapshot per run, as
  plain SQL (`CREATE TABLE` + `INSERT` statements — the same format
  `schema.sql` uses, so a snapshot can rebuild the database from scratch).
- `backup.log` — one line per run, success or failure.

**This folder is gitignored and must stay that way.** A snapshot contains
real student data — email addresses, phone numbers, order and shipping
details. It must never be committed, copied into a public place, or shared
outside what you'd normally treat as private customer records.

## Incident: backups silently failed for ~24 hours (2026-09-24 to 2026-09-25)

The 6-hourly job failed four times in a row (20:38, 02:38, 08:38, 14:38). Cause: the script called an
unpinned `npx wrangler`, which tried to download the newest wrangler into the npx cache and hit a locked
file (`EBUSY`). The failure alert email did send. Fix: the script now pins `wrangler@4.137.0`
(`WRANGLER` at the top of `tools/backup_d1_snapshot.py`), which is already cached. A manual run on
2026-09-25 19:43 succeeded (628 KB). When upgrading wrangler, change that one constant and run the
script by hand once.

## Retention

Snapshots older than **30 days** are deleted automatically on every run.
At 4 snapshots/day that's roughly 120 files kept at any time — each is only
a few KB right now, so this costs nothing meaningful in disk space even as
the site grows. Change `RETENTION_DAYS` at the top of
`tools/backup_d1_snapshot.py` if you want a longer or shorter window.

## Restoring from a snapshot

If you ever need to rebuild the database from a snapshot (disaster
recovery, or moving to a fresh D1 database):
```
cd capranav_com_revamped
npx wrangler d1 execute capranav-platform --remote --file=database-backups/capranav-platform_<timestamp>.sql
```
This replays every `CREATE TABLE` and `INSERT` from that snapshot. Only do
this against an *empty* database — replaying it against the live database
will fail on duplicate rows.

## One real thing worth knowing

Cloudflare's own export step warns that **the database is briefly
unavailable to serve queries while an export runs**. On a database this
small (a few KB today), that's a very short window — but it's worth keeping
in mind if the site ever sees a lot more traffic: a login or checkout
request that happens to land in that exact moment could fail and need a
retry. Nothing has been built to work around this yet since it's currently
negligible; revisit if the database grows significantly or this becomes a
real, observed problem.

## No local database file — confirmed, not assumed

The live Worker's `env.DB` binding in `wrangler.toml` points directly at
the remote D1 database (`capranav-platform`, id
`03830ea8-b539-480b-b106-0743aeda1b1f`) — there is no code path anywhere in
`worker/index.js` that writes to a local file. Development (`wrangler dev`)
is always run with `--remote`, which talks to the same real database
instead of spinning up a local SQLite emulator. This backup job is the
*only* thing that writes a database copy to this machine.
