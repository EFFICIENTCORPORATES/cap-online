#!/usr/bin/env python3
"""
telegram/tools/merge_faculty_mcq_sources.py -- combine a faculty's per-level/
per-subject MCQ source files into the ONE JSON the bot actually reads
(2026-08-10)
--------------------------------------------------------------------------------
The concrete problem this fixes: CS Arun Chouhan has separate per-level MCQ
converters (`telegram/assets/faculty/csarunchouhan-cma-found-law/...` for
Foundation, `csarunchouhan-cma-inter-law/convert_inter_law_mcqs.py` for
Intermediate), and the Intermediate converter writes DIRECTLY to the
tenant's shared, bot-facing file (`telegram/assets/exam_bot/faculty/
csarunchouhan/mcq_questions_extracted.json`, the exact path
`tenants.json`'s `exam_content.mcq_json` points at). That's fine as long as
only one source ever exists -- the moment a second one does (Foundation),
whichever converter runs last silently clobbers the other's content with
no merge step in between. Found exactly this on 2026-08-10: the tenant file
had 650 Intermediate-only records, zero Foundation, because the Foundation
set had never been through a merge step at all, just left in its own
separate, never-wired-in file.

This script is the merge step: reads every configured source file for a
tenant, concatenates them, fails LOUDLY on any mcq_id collision across
sources (never silently drops or overwrites one record with another), and
writes the combined result to the tenant's configured `mcq_json` path (read
from `tenants.json`, never hardcoded here, so a tenant's file path only
ever needs to change in one place). Then runs
`telegram/tools/validate_content_json.py`'s own checks against the result
before declaring success -- a merge that produces a file the bot can't
safely load is not a successful merge.

OPERATIONAL RULE, important: if a per-level converter that writes directly
to the tenant's shared file (like `convert_inter_law_mcqs.py`) is re-run
later, its direct write will again only contain ITS OWN level's records --
**re-run this merge script immediately afterward**, or the other source's
content silently disappears from the live file again, exactly like it did
before this script existed. Consider pointing future per-level converters
at their own dedicated output file only (never the shared tenant path
directly) and always routing through this script instead, to remove the
footgun structurally rather than relying on remembering the rule.

USAGE:
    python telegram/tools/merge_faculty_mcq_sources.py csarunchouhan
    python telegram/tools/merge_faculty_mcq_sources.py csarunchouhan --dry-run

Add a new tenant by adding an entry to MCQ_SOURCES below.
"""

import sys
import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TENANTS_PATH = REPO_ROOT / "telegram" / "config" / "tenants.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_content_json  # noqa: E402

# ---------------------------------------------------------------------------
# Per-tenant list of source files to merge, in order (order only matters for
# readability of the merged file -- record identity/behavior is unaffected).
# Add a new tenant/source here, not by hand-editing any output file.
# ---------------------------------------------------------------------------
MCQ_SOURCES = {
    "csarunchouhan": [
        REPO_ROOT / "telegram" / "assets" / "faculty" / "csarunchouhan-cma-found-law" / "cma_foundation_law_faculty_mcqs.json",
        REPO_ROOT / "telegram" / "assets" / "faculty" / "csarunchouhan-cma-inter-law" / "cma_inter_law_faculty_mcqs.json",
    ],
}


def load_records(path: Path) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("questions", data) if isinstance(data, dict) else data


def resolve_tenant_mcq_path(tenant_id: str) -> Path:
    data = json.loads(TENANTS_PATH.read_text(encoding="utf-8"))
    for t in data["tenants"]:
        if t["tenant_id"] == tenant_id:
            rel = (t.get("exam_content") or {}).get("mcq_json")
            if not rel:
                sys.exit(f"Tenant '{tenant_id}' has no exam_content.mcq_json configured in tenants.json.")
            if isinstance(rel, list):
                # mcq_json became list-capable 2026-08-11 (see
                # exam_hub_bot.py's _resolve_content_paths()) for tenants
                # that MERGE multiple already-built source files at bot
                # load time. This script instead WRITES a converted result
                # to one file -- there's no single correct target to guess
                # among several, so fail loudly rather than silently
                # picking rel[0] and possibly writing to the wrong file.
                sys.exit(
                    f"Tenant '{tenant_id}' has a LIST of mcq_json sources ({rel}) -- "
                    f"this script only supports a single write-target path. Pass the "
                    f"intended target file explicitly, or point this tenant back at one "
                    f"file if that's what's intended."
                )
            return REPO_ROOT / rel
    sys.exit(f"Unknown tenant_id '{tenant_id}' in tenants.json.")


def merge(tenant_id: str, dry_run: bool = False):
    sources = MCQ_SOURCES.get(tenant_id)
    if not sources:
        sys.exit(f"No MCQ_SOURCES configured for '{tenant_id}' -- add an entry to this script.")

    out_path = resolve_tenant_mcq_path(tenant_id)

    all_records = []
    seen_ids = {}
    for src in sources:
        if not src.exists():
            sys.exit(f"Source file does not exist: {src}")
        records = load_records(src)
        print(f"  {src.name}: {len(records)} records")
        for r in records:
            mcq_id = r.get("mcq_id")
            if mcq_id and mcq_id in seen_ids:
                sys.exit(f"COLLISION: mcq_id '{mcq_id}' appears in both {seen_ids[mcq_id]} and {src.name} -- "
                         f"refusing to merge until this is resolved (never silently overwriting one with the other).")
            if mcq_id:
                seen_ids[mcq_id] = src.name
        all_records.extend(records)

    print(f"\nMerged total: {len(all_records)} records from {len(sources)} source(s), 0 id collisions.")

    if dry_run:
        print(f"\n[dry-run] Would write to: {out_path} -- no file written.")
        return

    out_path.write_text(json.dumps(all_records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path} ({len(all_records)} records).")

    # Never declare success on an unchecked write -- run the same
    # bot-facing field validation the dashboard's Content Health card uses.
    report = validate_content_json.validate_file(out_path, "mcq")
    errors = [i for i in report["issues"] if i["severity"] == "ERROR"]
    warnings = [i for i in report["issues"] if i["severity"] == "WARNING"]
    print(f"Post-merge validation: {len(errors)} error(s), {len(warnings)} warning(s).")
    if errors:
        for e in errors:
            print(f"  [ERROR] {e['record_id']} :: {e['field']} -- {e['message']}")
        sys.exit("Merge produced a file with validation errors -- fix the source(s) and re-run.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tenant_id")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen, write nothing.")
    args = parser.parse_args()
    merge(args.tenant_id, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
