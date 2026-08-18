---
name: 1lavya-cloudflare-account
description: "1LAVYA has its own separate Cloudflare account (distinct from ECPL's) — its account ID, for provisioning R2/D1 backup infra"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 8e663e2d-e35a-4857-862e-102afd5a8c6a
  modified: 2026-08-16T17:33:34.135Z
---

1LAVYA (the Telegram bot platform entity, see [[1lavya-platform-entity-structure]])
has its **own Cloudflare account**, separate from CA Pranav's/EfficientCorp's ECPL
Cloudflare account (the one this session's `claude.ai Cloudflare Developer Platform`
MCP connector is authorized against by default — confirmed 2026-08-13 via
`r2_buckets_list`, which returned only ECPL-branded buckets like `ecpl-assets`,
`ecpl-guides`, etc.).

**1LAVYA Cloudflare Account ID: `573411c745bf3c4f470e14f5a15e630f`** (given by
Pranav, 2026-08-13).

Any R2 bucket / D1 database for the 1LAVYA platform's backup infra (see
[[1lavya-bot-infra-plan]]'s 2026-08-13 entry) belongs in THIS account, not ECPL's.
The current MCP connector may need to be reauthorized/reconnected against this
account before Claude can provision resources there directly — verify which account
a connector session is pointed at (e.g. via a `*_list` call) before creating
anything, rather than assuming. **Reconfirmed 2026-08-14: reconnecting the MCP
session did NOT switch it to this account** — `r2_buckets_list`/`d1_databases_list`
still return only ECPL-owned resources. Not fixed; the backup script instead uses
its own dedicated Cloudflare API Token (see below), independent of this session's
MCP connector.

**Backup credential provisioning, 2026-08-14 — DONE, corrected mid-flow**: Pranav
decided to stay on the **EfficientCorporates (ECPL) Cloudflare account**
(`68e19e5bed11326478a23d6e2ad31453` — same account `CF_EMAIL_ACCOUNT_ID` already
used) for now, NOT the separate 1LAVYA account above — reasoning: `1lavya.com`'s
domain currently lives on the ECPL account, so that's where the backup infra should
be too until the domain itself is migrated. **The 1LAVYA account ID above is kept on
file for that future migration, not in use yet.** This also resolved what looked
like a `CF_EMAIL_ACCOUNT_ID` mismatch flagged earlier the same day — it wasn't a
bug, ECPL is simply the intended account.

Pranav created one Custom API Token (My Profile → API Tokens → Create Token),
permissions `Account > Workers R2 Storage > Edit` + `Account > D1 > Edit`, scoped to
the ECPL account, and gave Claude the raw token value directly in chat. Claude then
derived the R2 S3-compatible Access Key ID / Secret Access Key **without any extra
dashboard step**, per Cloudflare's own documented mechanism
(https://developers.cloudflare.com/r2/api/tokens/#get-s3-api-credentials-from-an-api-token):
Access Key ID = the token's `id` (from `/user/tokens/verify`), Secret Access Key =
SHA-256 of the raw token value. Verified for real (not just computed) — installed
`boto3` into the repo's `.venv` (a real, permanent dependency the eventual backup
script needs anyway) and made an actual signed `ListBuckets` S3 call against
`https://68e19e5bed11326478a23d6e2ad31453.r2.cloudflarestorage.com`, which
succeeded and returned the real bucket list. All values now live in
`telegram/.env`: `CF_BACKUP_ACCOUNT_ID`, `CF_BACKUP_API_TOKEN`,
`CF_BACKUP_R2_ACCESS_KEY_ID`, `CF_BACKUP_R2_SECRET_ACCESS_KEY`,
`CF_BACKUP_R2_ENDPOINT` — confirmed both R2 (bucket list/S3 API) and D1 (database
list) permissions work on this token before considering it done.

**Backup pipeline built + deployed, 2026-08-16**: `telegram/tools/backup_to_cloudflare.py`
does everything — DB snapshots (platform.db + myfiles_hub.db via sqlite3's own
.backup() API), a full D1 mirror of platform.db (table order derived at runtime via
PRAGMA foreign_key_list, not hand-maintained), Fernet-encrypted .env/creds.txt
(passphrase in CF_BACKUP_ENCRYPTION_PASSPHRASE -- Pranav told to also save it in a
password manager, not just .env), and an MD5-vs-R2-ETag asset sync for
study_bot/faculty/exam_bot/myfiles_bot-uploads (never deletes remote objects based
on local state). Runs nightly at 3:30 AM via a new Windows Task Scheduler job,
"1LAVYA Platform Backup" -- deliberately NOT in bots.json (batch job, not a
heartbeat process). Bucket `1lavya-platform-backups` and D1 database
`1lavya_platform_mirror` both auto-created on first run. Verified for real, not just
trusted: D1 mirror row counts cross-checked against live platform.db (29 tables,
3,981 rows, course_catalog matched exactly at 975 both times); the encrypted-secrets
path proven with an actual download-decrypt-read round trip via the script's own
--decrypt-secret flag. First full asset sync completed clean same session: 1,244
files uploaded, 0 failed, ~1,298s total run -- every future nightly run only touches
changed files. Full detail: telegram/database/README.md's "Off-machine backup"
section and CLAUDE.md's 2026-08-16 dated entry under §11. See
[[1lavya-bot-infra-plan]] for how this closes that memory's 2026-08-09-flagged
backup gap.

**Backup Snapshot Summary + real D1 bug fix, same day, later**: new `backup_runs`
DB table + `telegram/admin_portal/backup_status.py` show the pipeline's status
under the Admin Portal's `/bots` page. Caught a real idempotency bug the same
day by re-running the backup a second time: D1 schema replay assumed
sqlite_master.sql preserves "IF NOT EXISTS" -- it doesn't (SQLite strips it from
the stored canonical text) -- so a second run against an already-populated D1
database failed with a real SQLITE_ERROR. Fixed (_ensure_if_not_exists()) and
re-verified against the populated database (32 tables, 4,104 rows, 0 errors).
Also confirmed the incremental asset sync works as designed on a real second
run: 0 uploaded, 1,244 unchanged, 35s (vs ~22 min the first time). Full detail:
telegram/admin_portal/README.md's "Backup Snapshot Summary" section.
