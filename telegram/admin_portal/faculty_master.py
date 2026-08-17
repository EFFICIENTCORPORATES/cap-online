"""
telegram/admin_portal/faculty_master.py -- Faculty Master DB table
(2026-08-14, Pranav's direct ask: "maintain a faculty table where we can
store the details of the faculty... should we have this in a JSON file or
should we keep this inside a table in db?" -- confirmed: DB table.)
--------------------------------------------------------------------------------
Owns all reads/writes of the `faculty_master` DB table (schema.sql) --
administrative/contact details only: contact_email, contact_phone,
free-text notes. See that table's own schema.sql comment for the full
reasoning on why this is a NEW, separate table rather than new fields on
telegram/config/tenants.json: tenants.json stays exclusively the
CONTENT-ROUTING config the bot scripts read directly at process startup
(content_scope, own_content, exam_content, kind); this table is the
CRUD-editable administrative layer for the same tenant, entered and edited
through a real Admin Portal form (Masters > Faculty Details) with a full
audit trail (admin_actions, same as every other write in this portal) --
something a hand-edited JSON file can't safely offer without a lot more
plumbing (file locking, concurrent-write safety, etc.) that a DB table
already gives for free.

Deliberately does NOT duplicate tenants.json's `onboarding_fee` (amount/
paid/paid_at) -- that already exists and is already read by
analytics.fetch_faculty_roster(); list_faculty_master() below reads it
alongside this table's own fields for one coherent view, without creating
a second copy of the same fact.

One row per tenant_id, upserted (never duplicated) via
upsert_faculty_master() -- created on first save, updated after.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
TENANTS_PATH = REPO_ROOT / "telegram" / "config" / "tenants.json"


def load_tenants() -> dict:
    data = json.loads(TENANTS_PATH.read_text(encoding="utf-8"))
    return {t["tenant_id"]: t for t in data["tenants"]}


def _row_to_dict(row) -> dict:
    tenant_id, contact_email, contact_phone, notes, created_at, updated_at = row
    return {
        "tenant_id": tenant_id, "contact_email": contact_email, "contact_phone": contact_phone,
        "notes": notes, "created_at": created_at, "updated_at": updated_at,
    }


def get_faculty_master(conn, tenant_id: str) -> dict | None:
    row = conn.execute(
        "SELECT tenant_id, contact_email, contact_phone, notes, created_at, updated_at "
        "FROM faculty_master WHERE tenant_id=?",
        (tenant_id,),
    ).fetchone()
    return _row_to_dict(row) if row else None


def list_faculty_master(conn) -> list:
    """Every tenant in tenants.json (regardless of kind -- platform
    tenants can carry admin notes too), left-joined against whatever
    faculty_master row exists for it (None fields if nothing's been
    entered yet -- an unentered faculty is a normal, expected state, not
    an error). Onboarding-fee status is read straight from tenants.json
    alongside it -- see module docstring on why that's not duplicated
    into this table."""
    tenants = load_tenants()
    rows_by_tenant = {}
    for row in conn.execute(
        "SELECT tenant_id, contact_email, contact_phone, notes, created_at, updated_at FROM faculty_master"
    ).fetchall():
        d = _row_to_dict(row)
        rows_by_tenant[d["tenant_id"]] = d

    out = []
    for tenant_id, t in tenants.items():
        fee = t.get("onboarding_fee") or {}
        master = rows_by_tenant.get(tenant_id, {
            "tenant_id": tenant_id, "contact_email": None, "contact_phone": None,
            "notes": None, "created_at": None, "updated_at": None,
        })
        out.append({
            **master,
            "display_name": t.get("display_name", tenant_id),
            "kind": t.get("kind"),
            "onboarding_fee_amount_inr": fee.get("amount_inr"),
            "onboarding_fee_paid": fee.get("paid"),
            "onboarding_fee_paid_at": fee.get("paid_at"),
        })
    out.sort(key=lambda r: (r["kind"] != "faculty", r["display_name"]))
    return out


def upsert_faculty_master(conn, tenant_id: str, contact_email: str = None,
                           contact_phone: str = None, notes: str = None) -> None:
    now = platform_db.now()
    existing = get_faculty_master(conn, tenant_id)
    if existing:
        platform_db.execute_with_retry(
            conn,
            "UPDATE faculty_master SET contact_email=?, contact_phone=?, notes=?, updated_at=? WHERE tenant_id=?",
            (contact_email, contact_phone, notes, now, tenant_id),
        )
    else:
        platform_db.execute_with_retry(
            conn,
            "INSERT INTO faculty_master (tenant_id, contact_email, contact_phone, notes, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?)",
            (tenant_id, contact_email, contact_phone, notes, now, now),
        )
