"""
render_capture.py -- Headless-browser capture for JavaScript-rendered sites.

mirror_sites.py (wget2-based) only works on traditional server-rendered
sites, where the real page content is already present in the raw HTML the
server sends. It CANNOT capture a modern JS single-page app (React/Next.js/
Vue/etc.) -- the server sends an almost-empty HTML shell plus a pile of
<script> tags, and the real content only exists after a browser downloads
and RUNS those scripts. wget2 has no JavaScript engine, so on a site built
this way it correctly, unavoidably captures nothing but that empty shell.

This is exactly what happened mirroring vcgurukul.com: 2 files, 0.11 MB --
just index.html's empty shell + favicon.ico. Not a bug, not a missed
setting; a fundamentally different kind of site needing a fundamentally
different tool. See this session's own explanation for the full mechanics.

This script uses Playwright (a real, automatable headless Chromium browser)
to actually load each page, let its JavaScript run, wait for the real
content to render, then save what a human visitor would actually see --
both the rendered HTML and its plain visible text (the text file is what
you actually want for RAG ingestion; the HTML is kept for reference/re-
extraction later).

It crawls same-domain links discovered in the rendered DOM (since a
client-rendered site's real navigation only appears after rendering, not
in the raw HTML wget2 can see), breadth-first, with a page-count and depth
cap by default -- deliberately conservative, since a SPA with dynamic
catch-all routes (seen on vcgurukul.com: ".../project-internal/[projectId]/
[...url_slug]/...") can easily have far more distinct URLs than a normal
brochure site, and this should never turn into an accidental unbounded
crawl.

robots.txt handling: uses Python's own urllib.robotparser, which -- per
RFC and per Python's own stdlib implementation -- treats a 401/403 on the
robots.txt fetch itself as "disallow everything" (the conservative, safe-
by-default reading). vcgurukul.com's own robots.txt returned exactly that
403 when mirror_sites.py fetched it. If you're confident that's a hosting/
WAF quirk rather than a deliberate block (reasonable to judge for your own
site; a third party's site deserves more caution) pass --ignore-robots
explicitly -- this is a visible opt-out, never a silent default.

Requires:  pip install playwright   then   playwright install chromium
(both already run for this repo's .venv as of 2026-08-24).

Usage:
    python render_capture.py vcgurukul                 # by slug (looked up in website_links.txt)
    python render_capture.py https://example.com/       # or a raw URL directly
    python render_capture.py vcgurukul --max-pages 60 --max-depth 4
    python render_capture.py vcgurukul --screenshot      # also save a PNG per page (visual QA)
    python render_capture.py vcgurukul --ignore-robots   # explicit override, see above
    python render_capture.py vcgurukul --headed          # watch it work, for debugging
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.robotparser
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

from mirror_sites import HERE, MASTER_LOG, read_links, slug_for  # reuse, don't duplicate

DEFAULT_MAX_PAGES = 40
DEFAULT_MAX_DEPTH = 3
DEFAULT_WAIT_MS = 1500          # extra settle time after networkidle, for late client-side renders
DEFAULT_DELAY_SECONDS = 1.0     # politeness delay between page loads
NAV_TIMEOUT_MS = 30_000

# Extensions that are clearly not a page to render (skip from the crawl queue,
# but still noted so nothing silently vanishes from the picture).
SKIP_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".zip", ".rar", ".7z", ".mp4", ".mp3", ".doc", ".docx", ".xls", ".xlsx",
    ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
}
SKIP_SCHEMES = {"mailto", "tel", "javascript", "data"}


def normalize_url(url: str) -> str:
    """Strip fragment, strip trailing slash (except bare root), for dedup."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, ""))


def same_site(url: str, base_netloc: str) -> bool:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    base = base_netloc.lower()
    if base.startswith("www."):
        base = base[4:]
    return host == base


def is_capturable(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    ext = Path(parsed.path).suffix.lower()
    return ext not in SKIP_EXTENSIONS


def path_to_filename(url: str) -> str:
    """Turn a URL path into a filesystem-safe base filename."""
    path = urlparse(url).path.strip("/")
    if not path:
        return "index"
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", path)
    return safe[:150]  # keep filenames sane on Windows


def discover_dropdown_links(page, base_netloc: str) -> list[str]:
    """Some sites hide real navigation links inside a hover/click-revealed
    mega-menu -- they have no <a href> at all until you interact with the
    trigger element, so the plain a[href] scan never sees them. Found on
    vcgurukul.com's own "Free Courses" menu: the trigger itself has no href
    (it's a styled <div>, not a link), and "CA Foundation" underneath it
    only exists in the page's embedded nav config, revealed in the DOM only
    once the trigger is hovered.

    This hovers (never clicks -- see below) every plausible trigger inside
    <header>/<nav>, re-scans for newly-visible a[href] elements after each
    one, then moves the mouse away before trying the next trigger so open
    panels don't stack and confuse the next hover.

    Hover-only, deliberately: a click on the wrong element (a real button
    mis-identified as a menu trigger -- "Add to Cart", "Submit", a modal
    trigger) could cause a real, unwanted side effect on a live site.
    Hovering a CSS-driven dropdown open carries essentially none of that
    risk, which is why this doesn't just click everything that looks
    clickable.

    Two real bugs found and fixed while building this, both worth knowing
    about since either could recur on a different site:

    1. **Visibility.** vcgurukul.com renders a DUPLICATE, hidden copy of its
       whole nav (almost certainly a mobile-drawer variant). The hidden copy
       has a perfectly normal non-zero bounding box -- a hand-rolled raw-JS
       visibility check (`getBoundingClientRect`/`offsetParent`) picked the
       WRONG duplicate with no error at all, just silently found nothing.
       Fixed by using Playwright's own `ElementHandle.is_visible()` -- real
       actionability logic, not a reimplementation -- which correctly told
       the two apart where the raw-JS check couldn't.
    2. **Staleness across hovers.** The first fix still didn't work end to
       end. Root cause: this function used to tag every candidate ONCE up
       front (a `data-rc-trigger` attribute), then loop through the tags.
       React re-renders the menu DOM on hover-driven state changes, and can
       silently replace/remount nodes -- which drops any attribute added
       from outside React's own render, invalidating tags for elements not
       yet reached in the loop. Fixed by re-querying the DOM **fresh, by
       position, on every single iteration** (see the JS below) instead of
       trusting attributes to survive N rounds of hover-triggered
       re-rendering.
    """
    ELIGIBLE_COUNT_JS = """
        () => Array.from(document.querySelectorAll('header *, nav *')).filter(el => {
            if (el.tagName === 'A' && el.hasAttribute('href')) return false;
            const style = window.getComputedStyle(el);
            const looksClickable = style.cursor === 'pointer';
            const hasIconChild = el.querySelector('svg, i[class*="chevron"], i[class*="arrow"]') !== null;
            return looksClickable || hasIconChild;
        }).length
    """
    try:
        trigger_count = page.evaluate(ELIGIBLE_COUNT_JS)
    except Exception:  # noqa: BLE001
        return []

    discovered: set[str] = set()
    # NOT capped low -- a real site can genuinely have 100+ eligible elements
    # once every phone/email link, icon button, and duplicate hidden nav copy
    # is counted (vcgurukul.com's own homepage has 107). An earlier version
    # of this function capped at 40 "to be safe," which silently truncated
    # the loop before it ever reached the correct "Free Courses" trigger
    # (sitting around index 67-75 here) -- the bug hid completely, no error,
    # just a quietly incomplete result. MAX_TRIGGERS is a genuine safety
    # ceiling only, not a tuned-for-this-site number.
    MAX_TRIGGERS = 300
    for i in range(min(trigger_count, MAX_TRIGGERS)):
        try:
            handle = page.evaluate_handle(
                f"""
                () => Array.from(document.querySelectorAll('header *, nav *')).filter(el => {{
                    if (el.tagName === 'A' && el.hasAttribute('href')) return false;
                    const style = window.getComputedStyle(el);
                    const looksClickable = style.cursor === 'pointer';
                    const hasIconChild = el.querySelector('svg, i[class*="chevron"], i[class*="arrow"]') !== null;
                    return looksClickable || hasIconChild;
                }})[{i}]
                """
            )
            trigger = handle.as_element()
            if trigger is None or not trigger.is_visible():
                continue
            trigger.hover(timeout=2000)
            page.wait_for_timeout(300)  # let a CSS/JS-driven panel finish opening
            hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
            for href in hrefs:
                if same_site(href, base_netloc):
                    discovered.add(href)
            page.mouse.move(0, 0)  # close whatever just opened before the next hover
            page.wait_for_timeout(150)
        except Exception:  # noqa: BLE001 -- one bad trigger must not abort discovery
            continue

    return sorted(discovered)


def load_robots(base_url: str, ignore_robots: bool) -> urllib.robotparser.RobotFileParser | None:
    if ignore_robots:
        print("  [robots] --ignore-robots passed -- skipping robots.txt entirely.")
        return None
    robots_url = urljoin(base_url, "/robots.txt")
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception as exc:  # noqa: BLE001 -- any fetch failure -> proceed, matches rp's own "allow all" fallback
        print(f"  [robots] could not fetch {robots_url} ({exc}) -- proceeding without restriction.")
        return None
    if not rp.default_entry and not getattr(rp, "disallow_all", False):
        print(f"  [robots] {robots_url} fetched but has no applicable rules.")
    if getattr(rp, "disallow_all", False):
        print(f"  [robots] {robots_url} returned 401/403 on fetch -- Python's robotparser "
              f"treats this as 'disallow everything' per RFC. This IS what happened on "
              f"vcgurukul.com. If you're confident this is a hosting/WAF quirk rather than "
              f"a deliberate block, re-run with --ignore-robots to override explicitly.")
    return rp


def robots_allows(rp: urllib.robotparser.RobotFileParser | None, url: str) -> bool:
    if rp is None:
        return True
    return rp.can_fetch("*", url)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="A slug from website_links.txt, or a raw URL.")
    ap.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    ap.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    ap.add_argument("--wait-ms", type=int, default=DEFAULT_WAIT_MS,
                     help="Extra settle time (ms) after each page reports network-idle.")
    ap.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS,
                     help="Politeness delay (seconds) between page loads.")
    ap.add_argument("--screenshot", action="store_true",
                     help="Also save a full-page PNG screenshot per page (visual QA).")
    ap.add_argument("--headed", action="store_true",
                     help="Run with a visible browser window instead of headless (debugging).")
    ap.add_argument("--ignore-robots", action="store_true",
                     help="Explicit override -- see module docstring's robots.txt section.")
    ap.add_argument("--no-dropdown-discovery", action="store_true",
                     help="Skip hovering nav/header elements to reveal dropdown-menu links "
                          "(see discover_dropdown_links). On by default -- it's what catches "
                          "links like vcgurukul.com's 'Free Courses' mega-menu that a plain "
                          "a[href] scan misses; turn it off only if it's slowing a run down "
                          "on a site that doesn't need it.")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright isn't installed in this Python environment.\n"
              "Install it with:\n"
              "    pip install playwright\n"
              "    playwright install chromium")
        return 1

    # Resolve target: slug from website_links.txt, or a raw URL.
    if args.target.startswith("http://") or args.target.startswith("https://"):
        base_url = args.target
        slug = slug_for(base_url)
    else:
        slug = args.target
        urls = read_links()
        match = next((u for u in urls if slug_for(u) == slug), None)
        if not match:
            print(f"No URL in website_links.txt matches slug '{slug}'.")
            print("Known slugs:", ", ".join(slug_for(u) for u in urls))
            return 1
        base_url = match

    base_netloc = urlparse(base_url).netloc
    site_dir = HERE / slug
    out_dir = site_dir / "rendered-pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = site_dir / "render-capture-log.txt"
    status_path = site_dir / "render-capture-status.json"

    rp = load_robots(base_url, args.ignore_robots)
    if not robots_allows(rp, base_url):
        print(f"robots.txt disallows fetching {base_url} at all -- stopping. "
              f"Use --ignore-robots to override (see the note above about why "
              f"this triggered).")
        return 1

    print(f"\n=== Rendering {base_url}  ->  {out_dir}  "
          f"(max {args.max_pages} pages, depth {args.max_depth}) ===")

    started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()

    visited: set[str] = set()
    skipped_offsite: set[str] = set()
    skipped_robots: set[str] = set()
    errors: list[dict] = []
    pages_captured: list[dict] = []

    queue: deque[tuple[str, int]] = deque([(normalize_url(base_url), 0)])
    seen_in_queue = {normalize_url(base_url)}

    with open(log_path, "w", encoding="utf-8") as log_f:
        def log(msg: str) -> None:
            print(f"  {msg}")
            log_f.write(msg + "\n")

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=not args.headed)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()
            page.set_default_navigation_timeout(NAV_TIMEOUT_MS)

            while queue and len(pages_captured) < args.max_pages:
                url, depth = queue.popleft()

                if not robots_allows(rp, url):
                    skipped_robots.add(url)
                    log(f"[skip: robots.txt] {url}")
                    continue

                log(f"[{len(pages_captured) + 1}/{args.max_pages}] "
                    f"(depth {depth}) GET {url}")
                try:
                    page.goto(url, wait_until="networkidle")
                    page.wait_for_timeout(args.wait_ms)
                except Exception as exc:  # noqa: BLE001 -- one bad page must not abort the crawl
                    errors.append({"url": url, "error": str(exc)})
                    log(f"  ERROR: {exc}")
                    continue

                html = page.content()
                try:
                    text = page.inner_text("body")
                except Exception:  # noqa: BLE001
                    text = ""

                base_name = path_to_filename(url)
                html_path = out_dir / f"{base_name}.html"
                text_path = out_dir / f"{base_name}.txt"
                # Guard against two different URLs slugging to the same filename.
                n = 1
                while html_path.exists() and str(html_path) not in {p["html_file"] for p in pages_captured}:
                    n += 1
                    html_path = out_dir / f"{base_name}-{n}.html"
                    text_path = out_dir / f"{base_name}-{n}.txt"

                html_path.write_text(html, encoding="utf-8", errors="replace")
                text_path.write_text(text, encoding="utf-8", errors="replace")

                shot_path = None
                if args.screenshot:
                    shot_path = out_dir / f"{base_name}.png"
                    try:
                        page.screenshot(path=str(shot_path), full_page=True)
                    except Exception as exc:  # noqa: BLE001
                        log(f"  screenshot failed: {exc}")
                        shot_path = None

                visited.add(url)
                pages_captured.append({
                    "url": url,
                    "depth": depth,
                    "html_file": str(html_path.relative_to(site_dir)),
                    "text_file": str(text_path.relative_to(site_dir)),
                    "text_chars": len(text),
                    "screenshot": str(shot_path.relative_to(site_dir)) if shot_path else None,
                })

                # Discover same-site links from the RENDERED DOM (this is the
                # whole point -- these links don't exist in the raw HTML at all
                # on a client-rendered site).
                if depth < args.max_depth:
                    try:
                        hrefs = page.eval_on_selector_all(
                            "a[href]", "els => els.map(e => e.href)"
                        )
                    except Exception:  # noqa: BLE001
                        hrefs = []
                    if not args.no_dropdown_discovery:
                        dropdown_hrefs = discover_dropdown_links(page, base_netloc)
                        if dropdown_hrefs:
                            log(f"  found {len(dropdown_hrefs)} link(s) inside hover/dropdown "
                                f"menus not present in the plain DOM scan")
                        hrefs = list(hrefs) + dropdown_hrefs
                    for href in hrefs:
                        if urlparse(href).scheme in SKIP_SCHEMES:
                            continue
                        if not is_capturable(href):
                            continue
                        if not same_site(href, base_netloc):
                            skipped_offsite.add(href)
                            continue
                        norm = normalize_url(href)
                        if norm not in seen_in_queue:
                            seen_in_queue.add(norm)
                            queue.append((norm, depth + 1))

                time.sleep(args.delay)

            browser.close()

    elapsed = time.monotonic() - t0
    finished_at = datetime.now(timezone.utc).isoformat()

    offsite_hosts = sorted({urlparse(u).netloc for u in skipped_offsite})

    status = {
        "url": base_url,
        "slug": slug,
        "started_at": started_at,
        "finished_at": finished_at,
        "elapsed_seconds": round(elapsed, 1),
        "pages_captured": len(pages_captured),
        "max_pages_reached": len(pages_captured) >= args.max_pages,
        "errors": errors,
        "robots_ignored": args.ignore_robots,
        "pages_skipped_by_robots": len(skipped_robots),
        "offsite_hosts_not_followed": offsite_hosts,
        "pages": pages_captured,
    }
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    with open(MASTER_LOG, "a", encoding="utf-8") as mlog:
        mlog.write(
            f"{finished_at}  {slug:<16} render   "
            f"{len(pages_captured)} pages, {len(errors)} errors, {elapsed:.0f}s\n"
        )

    print(f"\n  result: {len(pages_captured)} page(s) rendered and captured  |  "
          f"{len(errors)} error(s)  |  {elapsed:.0f}s")
    print(f"  saved to: {out_dir}")
    if len(pages_captured) >= args.max_pages:
        print(f"  NOTE: hit the --max-pages cap ({args.max_pages}) -- there may be more "
              f"pages on this site than were captured. Re-run with a higher --max-pages "
              f"if you want more, once you've reviewed what's here.")
    if offsite_hosts:
        print(f"  NOTE: {len(offsite_hosts)} other-domain host(s) linked from this site "
              f"were not followed (by design -- only same-site pages are crawled): "
              f"{', '.join(offsite_hosts[:10])}")
    if errors:
        print(f"  NOTE: {len(errors)} page(s) failed to load -- see {status_path.name} "
              f"for details.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
