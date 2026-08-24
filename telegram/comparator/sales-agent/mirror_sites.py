"""
mirror_sites.py -- Comparator site-mirroring queue processor.

Reads website_links.txt (one URL per line, this file's own directory),
figures out which sites already have a completed local mirror (by checking
for a non-empty "<slug>/site-mirror/" folder), and downloads the mirror for
sites that don't yet -- ONE site per run by default, so each mirror can be
reviewed before moving to the next, and so this script is always safe to
re-run (it never re-downloads a site that's already done).

Every quirk below was found the hard way, in this same session, mirroring
coceducation.com by hand -- see that folder's own SCRAPING-INCIDENT-CASE-
STUDY.md for the full incident writeup. This script bakes the fixes in so
nobody has to rediscover them:

  1. wget2 on Windows percent-encodes the drive-letter colon in -P output
     paths (D:\\... -> D%3A\\...), scattering output into a garbage-named
     folder instead of the real destination. Worked around here by always
     launching wget2 with its OWN working directory set to the target
     folder and a bare relative -P value -- and, belt-and-braces, by
     auto-detecting and auto-repairing any "D%3A*"-prefixed folder left
     behind after a run, exactly like the manual cleanup done for
     coceducation.com.
  2. A URL path segment ending in a literal "." (e.g. some CDN's
     ".../coc-education-pvt.-ltd./admin/...") gets silently stripped by
     Windows when wget2 tries to create that directory, breaking every
     write under it. Only bites during a --span-hosts CDN-follow-up pass,
     not a same-domain --mirror run, but this script's folder-repair logic
     also covers the general "wget2 wrote into an unexpected sibling path"
     case that bug produces.
  3. Only the main domain is ever mirrored by a plain --mirror pass --
     images/fonts hosted on a separate CDN domain are deliberately skipped
     (Telegram-CDN-tracker-script style hosts, Google Fonts, analytics,
     etc. would otherwise get pulled in too if we blindly spanned hosts).
     This script logs every external host it saw referenced but did not
     follow, so a deliberate, reviewed follow-up pass can be run per site
     if the CDN content actually matters -- it never does this
     automatically.

Requires wget2 (`winget install --id GNU.Wget2 -e`). Respects robots.txt
(wget2's default) and paces requests politely by default -- even though
none of the current target sites are known to rate-limit, there's no
reason not to be polite regardless of that assumption holding.

Usage:
    python mirror_sites.py                  # process the next pending site
    python mirror_sites.py --all            # process every pending site, in order
    python mirror_sites.py --status         # show what's done / pending, no downloading
    python mirror_sites.py --redo SLUG      # force a fresh re-download of one site
    python mirror_sites.py --wait SECONDS   # override the default 1s politeness delay
"""

from __future__ import annotations

import argparse
import glob
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
LINKS_FILE = HERE / "website_links.txt"
MASTER_LOG = HERE / "mirror-run-log.txt"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_WAIT_SECONDS = "1"
TIMEOUT_SECONDS = "30"
TRIES = "3"


# --------------------------------------------------------------------------
# wget2 discovery -- don't hardcode one machine's install path
# --------------------------------------------------------------------------

def find_wget2() -> str:
    """Locate wget2.exe. Tries PATH first, then the standard winget install
    location (winget doesn't always land on PATH in every shell/session --
    see this session's own history: it was missing from Git Bash's PATH
    even though PowerShell's PATH had it after a refresh)."""
    found = shutil.which("wget2") or shutil.which("wget2.exe")
    if found:
        return found

    candidates = glob.glob(
        str(Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet"
            / "Packages" / "GNU.Wget2_*" / "wget2.exe")
    )
    if candidates:
        return candidates[0]

    raise RuntimeError(
        "wget2 not found on PATH or in the standard winget install location.\n"
        "Install it with:  winget install --id GNU.Wget2 -e --source winget\n"
        "then re-run this script from a shell where `wget2 --version` works."
    )


# --------------------------------------------------------------------------
# Link list + slug handling
# --------------------------------------------------------------------------

def read_links(path: Path = LINKS_FILE) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Link list not found: {path}")
    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def slug_for(url: str) -> str:
    """coceducation.com's own mirror folder was just 'coceducation' -- match
    that convention: strip scheme + www, take the first DNS label."""
    host = urlparse(url).netloc or urlparse(url).path
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    return host.split(".")[0]


# --------------------------------------------------------------------------
# Status tracking
# --------------------------------------------------------------------------

@dataclass
class SiteStatus:
    url: str
    slug: str
    site_dir: Path
    mirror_dir: Path
    done: bool
    file_count: int = 0
    total_bytes: int = 0
    status_json: dict = field(default_factory=dict)


def check_status(url: str) -> SiteStatus:
    slug = slug_for(url)
    site_dir = HERE / slug
    mirror_dir = site_dir / "site-mirror"

    file_count = 0
    total_bytes = 0
    if mirror_dir.exists():
        for f in mirror_dir.rglob("*"):
            if f.is_file():
                file_count += 1
                total_bytes += f.stat().st_size

    status_json_path = site_dir / "mirror-status.json"
    status_json = {}
    if status_json_path.exists():
        try:
            status_json = json.loads(status_json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    # "Done" = a mirror folder exists with real content in it. A status.json
    # marked failed/incomplete does NOT count as done, even if some files
    # made it to disk, so a failed run gets retried on the next invocation
    # rather than silently treated as finished.
    done = file_count > 0 and status_json.get("result") == "success"

    return SiteStatus(
        url=url, slug=slug, site_dir=site_dir, mirror_dir=mirror_dir,
        done=done, file_count=file_count, total_bytes=total_bytes,
        status_json=status_json,
    )


def print_status_table(statuses: list[SiteStatus]) -> None:
    print(f"{'SLUG':<16} {'STATUS':<10} {'FILES':>8} {'SIZE (MB)':>10}  URL")
    print("-" * 80)
    for s in statuses:
        label = "done" if s.done else ("partial" if s.file_count else "pending")
        size_mb = s.total_bytes / (1024 * 1024)
        print(f"{s.slug:<16} {label:<10} {s.file_count:>8} {size_mb:>10.2f}  {s.url}")


# --------------------------------------------------------------------------
# The actual mirror run
# --------------------------------------------------------------------------

def repair_percent_encoded_folders(search_root: Path, real_target: Path) -> None:
    """wget2's Windows drive-letter-colon bug (see module docstring, item 1)
    can still leave a 'D%3A...'-prefixed folder behind despite the relative-
    path workaround below, if wget2 ever falls back to an absolute-looking
    path internally. Sweep for it and fold any real content found back into
    the correct destination -- exactly the manual cleanup this session did
    for coceducation.com, just automatic now."""
    for bad in search_root.glob("*%3A*"):
        if not bad.is_dir():
            continue
        moved = 0
        for f in bad.rglob("*"):
            if f.is_file():
                rel = f.relative_to(bad)
                # The garbage folder mirrors the whole absolute path as its
                # own name, so the REAL content sits several levels down,
                # under a repeated copy of this same site's own folder name.
                # Just fold everything found, flattened by its filename's
                # own relative position under the deepest 'site-mirror' (or
                # whatever mirror subfolder) segment we can find.
                parts = rel.parts
                if "site-mirror" in parts:
                    idx = parts.index("site-mirror")
                    dest_rel = Path(*parts[idx + 1:]) if len(parts) > idx + 1 else f.name
                    dest = real_target / dest_rel
                else:
                    dest = real_target / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    shutil.move(str(f), str(dest))
                    moved += 1
        shutil.rmtree(bad, ignore_errors=True)
        if moved:
            print(f"  [repair] recovered {moved} file(s) from a percent-encoded "
                  f"garbage folder ({bad.name}) into {real_target}")


def summarize_external_hosts(log_path: Path) -> list[str]:
    """Pull out every external host wget2 skipped (CDN images, analytics,
    fonts, etc.) so it's visible what a --mirror pass deliberately did NOT
    capture, without automatically going and fetching any of it."""
    if not log_path.exists():
        return []
    hosts = set()
    marker = "not followed (no host-spanning requested)"
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if marker in line and "URL '" in line:
            try:
                url = line.split("URL '", 1)[1].split("'", 1)[0]
                host = urlparse(url).netloc
                if host:
                    hosts.add(host)
            except IndexError:
                continue
    return sorted(hosts)


def run_mirror(url: str, wget2_path: str, wait_seconds: str) -> SiteStatus:
    slug = slug_for(url)
    site_dir = HERE / slug
    mirror_dir = site_dir / "site-mirror"
    site_dir.mkdir(parents=True, exist_ok=True)
    mirror_dir.mkdir(parents=True, exist_ok=True)

    log_path = site_dir / "wget-log.txt"
    status_path = site_dir / "mirror-status.json"

    cmd = [
        wget2_path,
        "--mirror",
        "--page-requisites",
        "--convert-links",
        "--adjust-extension",
        "--no-parent",
        "--no-host-directories",
        "-P", "site-mirror",              # relative -- see module docstring item 1
        "--user-agent", USER_AGENT,
        "--wait", wait_seconds,
        "--random-wait",
        "--tries", TRIES,
        "--timeout", TIMEOUT_SECONDS,
        url,
    ]

    print(f"\n=== Mirroring {url}  ->  {mirror_dir} ===")
    started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()

    with open(log_path, "w", encoding="utf-8", errors="replace") as log_f:
        proc = subprocess.run(
            cmd,
            cwd=site_dir,                 # relative -P resolves under here
            stdout=log_f,
            stderr=subprocess.STDOUT,
        )

    elapsed = time.monotonic() - t0
    finished_at = datetime.now(timezone.utc).isoformat()

    # Auto-repair the known Windows path bug, every run, unconditionally --
    # cheap to check, and silently correct if it happens.
    repair_percent_encoded_folders(site_dir, mirror_dir)
    repair_percent_encoded_folders(HERE, mirror_dir)  # in case it escaped one level up

    file_count = sum(1 for f in mirror_dir.rglob("*") if f.is_file())
    total_bytes = sum(f.stat().st_size for f in mirror_dir.rglob("*") if f.is_file())
    external_hosts = summarize_external_hosts(log_path)

    # wget2 exits non-zero on any individual HTTP error inside a big crawl
    # (e.g. a handful of genuinely-broken links) -- that is NOT the same as
    # "the mirror is empty/useless". Treat "some real files landed" as
    # success; exit code is recorded either way for the honest log.
    result = "success" if file_count > 0 else "failed"

    status = {
        "url": url,
        "slug": slug,
        "started_at": started_at,
        "finished_at": finished_at,
        "elapsed_seconds": round(elapsed, 1),
        "wget2_exit_code": proc.returncode,
        "result": result,
        "file_count": file_count,
        "total_bytes": total_bytes,
        "external_hosts_not_followed": external_hosts,
    }
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    with open(MASTER_LOG, "a", encoding="utf-8") as mlog:
        mlog.write(
            f"{finished_at}  {slug:<16} {result:<8} "
            f"{file_count} files, {total_bytes/1024/1024:.2f} MB, "
            f"exit={proc.returncode}, {elapsed:.0f}s\n"
        )

    print(f"  result: {result}  |  {file_count} files, "
          f"{total_bytes / 1024 / 1024:.2f} MB  |  {elapsed:.0f}s")
    if external_hosts:
        print(f"  NOTE: {len(external_hosts)} external host(s) referenced but "
              f"NOT mirrored (separate CDN/analytics/font domains) -- see "
              f"{status_path.name}'s 'external_hosts_not_followed' for the "
              f"list if a deliberate follow-up pass is ever wanted:")
        for h in external_hosts[:10]:
            print(f"    - {h}")
        if len(external_hosts) > 10:
            print(f"    ... and {len(external_hosts) - 10} more")

    return check_status(url)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true",
                     help="Process every pending site in order, not just the next one.")
    ap.add_argument("--status", action="store_true",
                     help="Show what's done/pending and exit without downloading anything.")
    ap.add_argument("--redo", metavar="SLUG",
                     help="Force a fresh re-download of one site by its folder slug, "
                          "even if it's already marked done.")
    ap.add_argument("--wait", default=DEFAULT_WAIT_SECONDS,
                     help=f"Politeness delay between requests, in seconds "
                          f"(default: {DEFAULT_WAIT_SECONDS}).")
    args = ap.parse_args()

    urls = read_links()
    if not urls:
        print(f"No URLs found in {LINKS_FILE}")
        return 1

    statuses = [check_status(u) for u in urls]

    if args.status:
        print_status_table(statuses)
        return 0

    wget2_path = find_wget2()

    if args.redo:
        target = next((s for s in statuses if s.slug == args.redo), None)
        if not target:
            print(f"No URL in {LINKS_FILE.name} matches slug '{args.redo}'.")
            print("Known slugs:", ", ".join(s.slug for s in statuses))
            return 1
        if target.mirror_dir.exists():
            shutil.rmtree(target.mirror_dir)
        run_mirror(target.url, wget2_path, args.wait)
        return 0

    pending = [s for s in statuses if not s.done]
    if not pending:
        print("All sites already mirrored. Nothing to do.")
        print_status_table(statuses)
        return 0

    if args.all:
        print(f"{len(pending)} site(s) pending: "
              f"{', '.join(s.slug for s in pending)}")
        for s in pending:
            run_mirror(s.url, wget2_path, args.wait)
        print("\nFinal status:")
        print_status_table([check_status(u) for u in urls])
        return 0

    # Default: just the next one.
    next_site = pending[0]
    print(f"Next pending site: {next_site.slug} ({next_site.url})")
    print(f"({len(pending) - 1} more after this one: "
          f"{', '.join(s.slug for s in pending[1:])})" if len(pending) > 1 else
          "(this is the last one)")
    run_mirror(next_site.url, wget2_path, args.wait)
    return 0


if __name__ == "__main__":
    sys.exit(main())
