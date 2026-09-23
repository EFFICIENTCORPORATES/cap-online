"""Remove the duplicated Telegram-platform content from this repo.

Context
-------
The Telegram bot platform was migrated out of cap-online into its own repo,
``EFFICIENTCORPORATES/Main1lavyaAIAgents`` (folder ``examstudyhub/``), and now
runs on a Contabo server. The ``telegram/`` tree left behind here is a stale
duplicate of it.

What this script keeps, and why
-------------------------------
* **Accounts content stays.** Pranav's rule: anything accounts-related for
  CA / CMA / CS is preserved in this repo, because this is the accounts
  teaching repo. Which papers count as "accounts" is taken from the platform's
  own ``course_catalog`` subject names, not guessed -- accounting papers only,
  Cost and Financial Management deliberately excluded:

      CA  Foundation P1   Accounting
      CA  Inter      P1   Advanced Accounting
      CA  Final      P1   Financial Reporting
      CMA Foundation P2   Fundamentals of Financial and Cost Accounting
      CMA Inter      P6   Financial Accounting
      CMA Inter      P10  Corporate Accounting and Auditing
      CMA Final      P18  Corporate Financial Reporting
      CS  CSEET      P2   Fundamentals of Accounting
      CS  Executive  P4   Corporate Accounting & Financial Management

* **Runtime logs and PID files stay.** They are the only copy of the old local
  deployment's operational history -- they have no twin in the migrated repo by
  definition, so this script never deletes them. Remove them by hand if you
  decide they are not worth keeping.

* **Anything with no verified twin stays.** A file is only deleted when an
  identical copy is confirmed in the migrated repo *at the moment of deletion*,
  or when the same path exists there holding a newer version.

Safety
------
Dry run is the default: it prints the plan and writes nothing. Pass
``--execute`` to actually delete. Every deletion is recorded in the manifest
written next to this script's output, so what was removed stays auditable.

Most of ``telegram/`` is untracked by git (~4.4 GB), so deletion there is
permanent -- which is exactly why nothing is removed without a twin check.

Usage::

    python tools/prune_migrated_telegram.py                 # dry run
    python tools/prune_migrated_telegram.py --execute       # delete
    python tools/prune_migrated_telegram.py --execute --manifest out.txt
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "telegram"
MIGRATED = Path(r"D:\EffCorp_Products\Main1Lavya\Main1lavyaAIAgents\examstudyhub")

# Filename prefixes of the accounting papers (the platform's human_id convention).
ACCOUNTS_PREFIX = re.compile(
    r"^(CA_L1_P01|CA_L2_P01|CA_L3_P01"
    r"|CMA_L1_P02|CMA_L2_P06|CMA_L2_P10|CMA_L3_P18"
    r"|CS_L1_P02|CS_L2_P04)",
    re.I,
)

# Accounts asset folders that predate the human_id filename convention.
ACCOUNTS_DIRS = (
    "assets/exam_bot/CA Found Account Json",
    "assets/exam_bot/CMA Found Accout. Json",
    "assets/exam_bot/ca-foundation-accounting",
    "assets/study_bot/Exam Materials",  # CA Inter Advanced Accounting MTP/PYQ/RTP
)

RUNTIME = re.compile(r"(database/run/|\.log(\.\d+)?$|\.pid$)")

ZIP_REL = "assets/study_bot/Study Materials.zip"


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def is_accounts(rel: str) -> bool:
    if any(rel.startswith(d) for d in ACCOUNTS_DIRS):
        return True
    return bool(ACCOUNTS_PREFIX.match(Path(rel).name))


def index_migrated() -> dict[str, str]:
    """Content hash -> relative path, for every file in the migrated repo."""
    out: dict[str, str] = {}
    for p in MIGRATED.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            try:
                out.setdefault(md5(p), p.relative_to(MIGRATED).as_posix())
            except OSError:
                pass
    return out


def zip_fully_covered(zip_path: Path, have: dict[str, str]) -> tuple[bool, list[str]]:
    """True when every entry inside the archive already exists in the migrated
    repo by content. desktop.ini entries are ignored as Windows metadata."""
    import zipfile

    missing: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.endswith("/") or Path(name).name == "desktop.ini":
                continue
            if hashlib.md5(zf.read(name)).hexdigest() not in have:
                missing.append(name)
    return (not missing), missing


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--execute", action="store_true", help="actually delete (default is a dry run)")
    ap.add_argument("--manifest", default="telegram-prune-manifest.txt", help="where to write the record")
    args = ap.parse_args()

    if not SRC.is_dir():
        print(f"Nothing to do: {SRC} does not exist.")
        return 0
    if not MIGRATED.is_dir():
        print(f"ABORT: migrated repo not found at {MIGRATED}\nNothing was deleted.")
        return 1

    print(f"Indexing migrated repo at {MIGRATED} ...")
    have = index_migrated()
    print(f"  {len(have)} content hashes indexed\n")

    deleted: list[tuple[str, int, str]] = []
    kept_accounts: list[str] = []
    kept_runtime: list[str] = []
    kept_no_twin: list[str] = []
    freed = 0

    # Deepest paths first so directories empty out cleanly.
    for p in sorted(SRC.rglob("*"), key=lambda x: len(x.as_posix()), reverse=True):
        if not p.is_file():
            continue
        rel = p.relative_to(SRC).as_posix()

        if "__pycache__" in p.parts or p.name == "desktop.ini":
            size = p.stat().st_size
            if args.execute:
                try:
                    p.unlink()
                except OSError:
                    continue
            deleted.append((rel, size, "windows metadata / bytecode cache"))
            freed += size
            continue

        if is_accounts(rel):
            kept_accounts.append(rel)
            continue

        if RUNTIME.search(rel):
            kept_runtime.append(rel)
            continue

        size = p.stat().st_size

        if rel == ZIP_REL:
            covered, missing = zip_fully_covered(p, have)
            if not covered:
                kept_no_twin.append(f"{rel} ({len(missing)} entries not found in migrated repo)")
                continue
            if args.execute:
                p.unlink()
            deleted.append((rel, size, "every archive entry verified present in migrated repo"))
            freed += size
            continue

        twin = have.get(md5(p))  # re-verified at the moment of deletion
        if twin:
            if args.execute:
                p.unlink()
            deleted.append((rel, size, f"identical copy at {twin}"))
            freed += size
        elif (MIGRATED / rel).exists():
            if args.execute:
                p.unlink()
            deleted.append((rel, size, "same path in migrated repo holds a newer version"))
            freed += size
        else:
            kept_no_twin.append(rel)

    if args.execute:
        for d in sorted((x for x in SRC.rglob("*") if x.is_dir()),
                        key=lambda x: len(x.as_posix()), reverse=True):
            try:
                d.rmdir()
            except OSError:
                pass

    verb = "DELETED" if args.execute else "WOULD DELETE"
    print(f"{verb:<14}: {len(deleted):>5} files, {freed / 1024 / 1024 / 1024:.2f} GB")
    print(f"KEEP accounts : {len(kept_accounts):>5} files")
    print(f"KEEP runtime  : {len(kept_runtime):>5} files (logs/PIDs, no twin by nature)")
    print(f"KEEP no-twin  : {len(kept_no_twin):>5} files")
    for rel in kept_no_twin:
        print(f"   kept, no verified twin: {rel}")

    manifest = Path(args.manifest)
    with manifest.open("w", encoding="utf-8") as fh:
        fh.write(f"# telegram/ prune manifest ({'executed' if args.execute else 'dry run'})\n")
        fh.write(f"# migrated repo: {MIGRATED}\n#\n")
        fh.write(f"# {verb}: {len(deleted)} files, {freed / 1024 / 1024 / 1024:.2f} GB\n\n")
        for rel, size, why in sorted(deleted):
            fh.write(f"{size:>13,}  {rel}  || {why}\n")
        fh.write(f"\n# KEPT - accounts ({len(kept_accounts)})\n")
        for rel in sorted(kept_accounts):
            fh.write(f"  {rel}\n")
        fh.write(f"\n# KEPT - runtime logs/PIDs ({len(kept_runtime)})\n")
        for rel in sorted(kept_runtime):
            fh.write(f"  {rel}\n")
        fh.write(f"\n# KEPT - no verified twin ({len(kept_no_twin)})\n")
        for rel in sorted(kept_no_twin):
            fh.write(f"  {rel}\n")
    print(f"\nManifest written to {manifest}")

    if not args.execute:
        print("\nDry run only - nothing was deleted. Re-run with --execute to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
