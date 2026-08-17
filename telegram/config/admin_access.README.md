# `admin_access.json` — bot_admin scope registry

Added 2026-08-17, part of the Phase 1 logging build (see
`telegram/LOGGING-ARCHITECTURE.md`). Same pattern as `bots.json`/
`tenants.json`/`leaderboards.json`: a hand-edited JSON file is the single
source of truth for *authorization policy* — who is allowed to see which
bot's data — kept deliberately separate from *authentication* (passwords),
which lives in the `admin_accounts` DB table instead. Restart
`1lavya-admin-portal` to pick up an edit (this file is read at each portal
process's own startup/request time via `auth.py`, same as every other
config file on this platform).

## Two roles, two different places

- **super_admin** (`role == "admin"` in the existing session model) — this
  is Pranav's own existing login (`telegram/.env`'s `ADMIN_PORTAL_USERNAME`/
  `PASSWORD_HASH`, unchanged by this file). Sees every bot's everything,
  unconditionally. **Never listed in this file** — adding an entry here
  cannot widen or narrow the super-admin's own access, by design.
- **bot_admin** — a new, deliberately narrower role. Can log in (via a row
  in `admin_accounts`, created with `manage_bot_admin.py`) and see **only**
  the Activity Log page (`/logs/activity`), **only** for the `bot_id`(s)
  listed for their username here. No other Admin Portal page is reachable
  by this role at all — every other route still requires `role_required("admin")`
  exactly as before this file existed, so a bot_admin account is
  structurally incapable of reaching Bot Restart, Student Master, or any
  other existing module, without a single line of those routes needing to
  change.

## Two steps to actually activate a bot_admin, in order

1. `python telegram/admin_portal/manage_bot_admin.py <username>` — creates
   the login (prints a one-time password, same "shown once, never stored"
   discipline as `set_password.py`).
2. Add (or flip to `"status": "active"`) an entry in this file for that same
   `username`, naming the `bot_ids` they should see.

Both steps are required — a DB account with no entry here logs in but sees
an empty Activity Log (no bot_id is in scope); an entry here with no DB
account can never log in at all. Neither step alone grants real access.

## Fields

- `username` — must exactly match (case-insensitive) the `username` column
  in `admin_accounts`.
- `status` — `"active"` or `"inactive"`. An inactive entry is treated as
  "no scope at all," same as not being listed — this repo's own established
  "designed, not yet turned on" placeholder convention (see
  `leaderboards.json`'s identical use of this field).
- `bot_ids` — a list, not a single value — one bot_admin CAN be scoped to
  more than one `bot_id` if a faculty ever runs more than one bot (Pranav's
  own `capranav-study`/`capranav-exam` split is exactly this shape, should
  his own team ever need a narrower account).
- `note` — free text, human context only, never read by code.
