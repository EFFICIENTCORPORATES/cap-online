#!/usr/bin/env python3
"""backlog_to_issues.py - turn the rows of docs/BACKLOG.md into GitHub issues (dry-run by default).

Why: docs/BACKLOG.md is the single index of pending work. GitHub Issues give each item a number, an
owner label and a place to discuss it. This script keeps the two aligned instead of hand-copying.

Safety:
  * Does nothing but print the plan unless you pass --execute.
  * Idempotent: ids already recorded in docs/backlog-issues.json are skipped, and the repo's existing
    issues are searched for the "[<id>]" title prefix before anything is created.
  * The repo is PUBLIC (backlog BL-R01), so every issue it creates is public. Items are written to
    contain no secrets or personal data; still read the plan before --execute. Where issues should live
    (this repo or EFFICIENTCORPORATES/task-hub) is decision BL-R02: do not run --execute until it is made.

Usage:
  python tools/backlog_to_issues.py                         # dry-run, prints every issue it would create
  python tools/backlog_to_issues.py --only BL-M01 S-A1      # restrict to some ids
  python tools/backlog_to_issues.py --repo OWNER/REPO --execute

Needs the GitHub CLI (`gh`) logged in with permission to create issues and labels.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "docs/BACKLOG.md"
MAPPING = ROOT / "docs/backlog-issues.json"
DEFAULT_REPO = "EFFICIENTCORPORATES/cap-online"

AREA = {"BL-R": "area:repo", "BL-M": "area:must-practice", "S-": "area:website", "Q-": "area:question-bank", "BL-O": "area:other"}
ID_PATTERN = re.compile(r"^(BL-[A-Z]\d+|S-[AB]\d+|Q-CR-\d+)$")


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True).stdout


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("**", "").replace("`", "")).strip()


def parse_rows() -> list[dict]:
    rows = []
    for line in BACKLOG.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not ID_PATTERN.match(cells[0]):
            continue
        rows.append(
            {
                "id": cells[0], "item": cells[1], "priority": cells[2], "who": cells[3], "status": cells[4],
                "detail": cells[5] if len(cells) > 5 else "",
            }
        )
    return rows


def labels_for(row: dict) -> list[str]:
    who = row["who"].lower()
    owner = "owner:pranav" if who.startswith("pranav") else "owner:agent" if who.startswith("agent") else "owner:both"
    area = next((v for k, v in AREA.items() if row["id"].startswith(k)), "area:other")
    return [f"priority:{row['priority']}", owner, area]


def title_for(row: dict) -> str:
    first = clean(row["item"]).split(". ")[0]
    if len(first) > 80:
        first = first[:80].rsplit(" ", 1)[0].rstrip(",;:") + "..."
    return f"[{row['id']}] {first}"


def body_for(row: dict) -> str:
    detail = f"\n**Detail:** {clean(row['detail'])}" if row["detail"] else ""
    return (
        f"{clean(row['item'])}\n\n**Who:** {row['who']}  \n**Status when created:** {row['status']}{detail}\n\n"
        f"_Source of truth: `docs/BACKLOG.md` (id `{row['id']}`). Update that file in the same commit as the work, "
        f"then update or close this issue._"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--execute", action="store_true", help="actually create labels and issues (default: dry-run)")
    ap.add_argument("--only", nargs="*", help="only these backlog ids")
    args = ap.parse_args()

    rows = parse_rows()
    if args.only:
        rows = [r for r in rows if r["id"] in set(args.only)]
    mapping = json.loads(MAPPING.read_text(encoding="utf-8")) if MAPPING.exists() else {}
    existing = json.loads(run(["gh", "issue", "list", "-R", args.repo, "--state", "all", "--limit", "500", "--json", "number,title"]))
    by_prefix = {m.group(1): i["number"] for i in existing if (m := re.match(r"\[([^\]]+)\]", i["title"]))}

    todo = []
    for row in rows:
        known = mapping.get(row["id"]) or by_prefix.get(row["id"])
        if known:
            mapping[row["id"]] = known
            continue
        todo.append(row)

    all_labels = sorted({label for r in todo for label in labels_for(r)})
    print(f"{len(rows)} backlog rows read, {len(rows) - len(todo)} already have an issue, {len(todo)} to create in {args.repo}")
    print(f"labels needed: {', '.join(all_labels) or 'none'}\n")
    for row in todo:
        print(f"- {title_for(row)}   [{', '.join(labels_for(row))}]")

    if not args.execute:
        print("\nDry-run only. Nothing was created. Re-run with --execute once BL-R02 is decided.")
        return 0

    for label in all_labels:
        run(["gh", "label", "create", label, "-R", args.repo, "--force", "--color", "5319e7" if label.startswith("priority") else "0e8a16"])
    for row in todo:
        url = run(
            ["gh", "issue", "create", "-R", args.repo, "--title", title_for(row), "--body", body_for(row)]
            + [arg for label in labels_for(row) for arg in ("--label", label)]
        ).strip()
        mapping[row["id"]] = int(url.rstrip("/").rsplit("/", 1)[1])
        print("created", row["id"], url)
    MAPPING.write_text(json.dumps(dict(sorted(mapping.items())), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {MAPPING.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
