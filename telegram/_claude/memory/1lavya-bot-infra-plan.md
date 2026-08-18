---
name: 1lavya-bot-infra-plan
description: "Hosting/DB decisions for the 1LAVYA bot platform — stay on local server through early faculty onboarding, SQLite vs Postgres is a performance-driven decision, and a live-DB + 5s-delay snapshot-DB split is required for analytics"
metadata: 
  node_type: memory
  type: project
  originSessionId: eff70d38-31a6-4cc7-baf2-a93b1aa25479
  modified: 2026-08-16T14:51:06.446Z
---

Decided 2026-08-09, see [[1lavya-platform-entity-structure]] for the platform this
applies to:

**Hosting**: deliberately staying on the current local machine as the "server" through
onboarding the first ~3 (and likely up to 5-10) faculty — not moving to a VPS/cloud
yet. Reasoning: this phase will see frequent code and even business-model changes,
and local iteration is far more convenient than a remote deploy loop. Pranav
considers this machine to have "proper backup and net bandwidth" for acceptable
uptime at this scale. **Revisit hosting once faculty count / traffic actually
stresses this** — don't treat "stay local" as permanent, it's an explicit early-stage
tradeoff, not a belief that a laptop is fine forever.

**Database engine**: currently SQLite (per-bot, as already built). Pranav is **open to
switching to PostgreSQL** specifically if SQLite's concurrent read/write performance
becomes a real problem at scale (many students, many simultaneous MCQ
attempts/wallet transactions) — but wants to stay on SQLite if it holds up. Treat this
as a to-be-measured decision, not yet made either way — don't migrate preemptively.

**Live DB + delayed snapshot DB split** (locked requirement, not yet built): all
real-time read/write traffic (MCQ attempts, wallet debits/credits, uploads, etc.)
hits one **Live DB**. A separate **snapshot DB, refreshed on a ~5-second delay**, is
required specifically for analytics queries — so heavy/slow analytics reads never
contend with live transactional traffic. Confirmed analytics needs the snapshot must
support:
- Number of unique students (platform-wide and/or per faculty)
- Total number of MCQs (served/attempted — clarify which when building)
- Wallet recharge activity and current balances
- Count of 1LAVYA-exclusive content items vs. faculty-owned content items

This snapshot-DB requirement applies regardless of whether the engine ends up being
SQLite or Postgres — it's an architecture decision (replication/polling snapshot),
not specific to either engine.

**Backup gap, confirmed 2026-08-09**: despite the "proper backup and net bandwidth"
framing above, Pranav confirmed on direct question there is actually **no dedicated
backup mechanism today** — just the machine itself, no cloud sync, no periodic copy
elsewhere. Flagged as something to put in place before real money (₹5,000 faculty
fees, wallet recharges) starts flowing through the live DB — not yet urgent since the
platform is still pre-launch (see [[1lavya-centralized-account-model]] for the launch
status note), but don't let building continue indefinitely without this being solved.

**Launch status, confirmed 2026-08-09**: platform is **pre-launch** — no faculty or
student has a committed live date yet, even though 2 faculty (Pranav, Arun Chouhan)
are onboarded with content sitting on disk. This means normal build sequencing is
fine (data model correctness > shipping speed) — re-check this status periodically,
since it directly changes prioritization.

**Backup gap being addressed, 2026-08-13**: real inventory taken of `telegram/` —
`database/platform.db` (880KB, 83 real students/395 MCQ attempts/etc.),
`assets/myfiles_bot/myfiles_hub.db` + its `uploads/` folder, and 1,803 sourced PDFs
(~1.4GB actually served, plus a redundant 1.5GB `assets/backup pdfs/` explicitly
excluded from backup scope) are **100% local-only, zero off-machine copy** — all
gitignored by design (binaries/secrets never go in git per this repo's rules).
Python code + question-bank JSON + config JSON are already safe via GitHub push.
Pranav confirmed the plan: **Cloudflare R2 (primary backup target) + a D1 mirror of
platform.db (queryable off-site copy)**, both to be provisioned in a **separate
1LAVYA Cloudflare account** (account ID `573411c745bf3c4f470e14f5a15e630f`) — NOT
the ECPL account this session's Cloudflare MCP connector is currently authorized
against (confirmed via `r2_buckets_list`: only ECPL-branded buckets like
`ecpl-assets` are visible). Backup job runs via Windows Task Scheduler (Pranav's
choice over an always-on managed process) on this same local PC. `.env`/`creds.txt`
get encrypted before upload, never sent plaintext. Requirements-gathering step
handed to Pranav 2026-08-13 — **built and deployed 2026-08-16**, see
[[1lavya-cloudflare-account]] for the full build (`telegram/tools/
backup_to_cloudflare.py`, nightly 3:30 AM Task Scheduler job, verified working end
to end). This closes the "no dedicated backup mechanism" gap noted below as of
2026-08-16 — the remaining half of gap #1 (auto-restart-on-crash / hosted infra) is
still open.
