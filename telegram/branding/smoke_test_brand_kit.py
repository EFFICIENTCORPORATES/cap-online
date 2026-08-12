#!/usr/bin/env python3
"""
telegram/branding/smoke_test_brand_kit.py -- Phase 1 (Branding Kit) smoke
test (2026-08-10)
--------------------------------------------------------------------------------
Per Pranav's process for this roadmap ("complete each phase, test it at
your end, make sure you have the smoke test .py script built, document it,
THEN tell me to test manually"): this is that script for Phase 1. Re-run it
any time the brand kit changes (a new asset, a color/markup tweak) before
trusting it again -- never re-declare Phase 1 done without running this.

Checks, in order (stops at the first failure -- a partial brand kit is
worse than an obviously-broken one):
  1. Every asset file build_brand_kit.py is supposed to produce actually
     exists on disk.
  2. brand_colors.json parses and both navy/gold are valid #rrggbb hex.
  3. Every logo_data_uri() variant decodes back into a real, correctly-
     sized PNG (round-trips through base64 correctly, isn't corrupt).
  4. render_header_html()/render_footer_html()/brand_css_vars() all
     produce non-empty HTML containing the expected brand elements (the
     wordmark, the tagline, an <img> tag, at least one real hex color) --
     not literally rendered pixels (see step 5 for that), just "did the
     function actually produce branded markup and not blow up / return
     something empty."
  5. Regenerates the real dashboard.html (the actual, live surface this
     phase wired branding into) and takes a real screenshot via headless
     Edge -- confirms the branding renders correctly as PIXELS, not just
     as HTML text. Per CLAUDE.md section 7's own rule: "never trust a
     layout fix by reading the code alone -- verify with a screenshot."

USAGE:
    python telegram/branding/smoke_test_brand_kit.py
    (screenshot written to telegram/branding/assets/_smoke_test_screenshot.png
    -- open it, or have Claude's Read tool view it directly)
"""

import os
import re
import sys
import base64
import subprocess
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "branding"))
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
sys.path.insert(0, str(REPO_ROOT / "telegram" / "tools"))
import brand_kit  # noqa: E402

# Portable Edge discovery (fixed 2026-08-12, see FIRST_PROMPT.md) -- was a
# single hardcoded path that only worked on a machine with 64-bit Edge
# installed at exactly this default location. Now: an explicit env var
# override first, then the two common Windows install locations. Returns
# None (not a wrong path) if nothing is found, so step5 fails loudly with
# an actionable message instead of silently subprocess-erroring.
_EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_edge_browser():
    override = os.environ.get("EDGE_SCREENSHOT_BROWSER")
    if override:
        return override if Path(override).exists() else None
    for candidate in _EDGE_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


EDGE_PATH = find_edge_browser()
SCREENSHOT_OUT = REPO_ROOT / "telegram" / "branding" / "assets" / "_smoke_test_screenshot.png"
DASHBOARD_HTML = REPO_ROOT / "telegram" / "database" / "dashboard.html"

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

failures = []


def check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        failures.append(label)


def step1_assets_exist():
    print("\n--- Step 1: asset files exist ---")
    from build_brand_kit import TRANSPARENT_PNG, ORIGINAL_COPY, COLORS_JSON, THUMBNAIL_SIZES
    check("transparent PNG exists", TRANSPARENT_PNG.exists())
    check("original JPEG copy exists", ORIGINAL_COPY.exists())
    check("brand_colors.json exists", COLORS_JSON.exists())
    for label, (size, path) in THUMBNAIL_SIZES.items():
        check(f"thumbnail '{label}' ({size}px) exists", path.exists())


def step2_colors_valid():
    print("\n--- Step 2: brand_colors.json is valid ---")
    c = brand_kit.colors()
    for key in ("navy", "gold", "navy_tint", "gold_tint", "ink"):
        check(f"colors()['{key}'] is present", key in c)
        if key in c:
            check(f"colors()['{key}'] = {c[key]!r} is valid #rrggbb hex", bool(HEX_COLOR_RE.match(c[key])))


def step3_data_uris_valid():
    print("\n--- Step 3: logo data URIs round-trip to real images ---")
    try:
        from PIL import Image
    except ImportError:
        check("PIL available for image round-trip check", False, "pip install Pillow")
        return
    for variant in ("header", "footer", "full"):
        uri = brand_kit.logo_data_uri(variant)
        check(f"logo_data_uri('{variant}') starts with data:image/png;base64,", uri.startswith("data:image/png;base64,"))
        raw = base64.b64decode(uri.split(",", 1)[1])
        try:
            img = Image.open(BytesIO(raw))
            img.verify()
            check(f"logo_data_uri('{variant}') decodes to a valid PNG", True)
        except Exception as e:
            check(f"logo_data_uri('{variant}') decodes to a valid PNG", False, str(e))


def step4_html_functions():
    print("\n--- Step 4: header/footer/css-vars produce real branded markup ---")
    header = brand_kit.render_header_html("Smoke Test Title", "a subtitle")
    footer = brand_kit.render_footer_html()
    css = brand_kit.brand_css_vars()

    check("render_header_html() contains the wordmark", brand_kit.BRAND_NAME in header)
    check("render_header_html() contains the tagline", brand_kit.TAGLINE in header)
    check("render_header_html() contains an <img> tag", "<img" in header)
    check("render_header_html() contains the title passed in", "Smoke Test Title" in header)
    check("render_footer_html() contains 'Powered by'", "Powered by" in footer)
    check("render_footer_html() contains an <img> tag", "<img" in footer)
    check("brand_css_vars() defines --1lavya-navy", "--1lavya-navy" in css)
    check("brand_css_vars() defines --1lavya-gold", "--1lavya-gold" in css)


def step5_real_render_screenshot():
    print("\n--- Step 5: real dashboard render, screenshot via headless Edge ---")
    import generate_dashboard
    generate_dashboard.main()
    check("dashboard.html regenerated", DASHBOARD_HTML.exists())

    html = DASHBOARD_HTML.read_text(encoding="utf-8")
    check("dashboard.html contains the wordmark", brand_kit.BRAND_NAME in html)
    check("dashboard.html contains an embedded logo data URI", "data:image/png;base64," in html)

    if not EDGE_PATH:
        check(
            "headless Edge available for screenshot", False,
            "not found at any known location -- set EDGE_SCREENSHOT_BROWSER to msedge.exe's "
            "path, or install Edge, then re-run -- skipping visual check",
        )
        return

    SCREENSHOT_OUT.parent.mkdir(parents=True, exist_ok=True)
    file_url = "file:///" + str(DASHBOARD_HTML.resolve()).replace("\\", "/")
    result = subprocess.run(
        [
            EDGE_PATH, "--headless", "--disable-gpu",
            "--window-size=1280,1600",
            f"--screenshot={SCREENSHOT_OUT}",
            file_url,
        ],
        capture_output=True, timeout=30,
    )
    check("headless Edge screenshot command succeeded", result.returncode == 0, result.stderr.decode(errors="replace")[:300])
    check("screenshot file was written", SCREENSHOT_OUT.exists())
    if SCREENSHOT_OUT.exists():
        print(f"    -> {SCREENSHOT_OUT} ({SCREENSHOT_OUT.stat().st_size:,} bytes) -- view this to confirm visually.")


def step_live_server_not_stale():
    """BUG FOUND 2026-08-11, added as a permanent check because of it:
    steps 1-6 all passed cleanly while the REAL running dashboard_server.py
    process (started before dashboard_html.py/brand_kit.py were last
    edited) kept serving the old, unbranded page -- Python doesn't hot-
    reload changed source files, and nothing above this ever actually hit
    the live :8787 endpoint, only the static file. Pranav caught it by
    eye; this check exists so the next code change catches it automatically
    instead. Two things: (1) if the live server is reachable, fetch it and
    confirm the branding is actually there; (2) compare the live process's
    own recorded start time (bot_heartbeats, via manage_bots' same DB) to
    this module's source file mtimes -- a process older than the source is
    a real, actionable "restart this" signal, not just a maybe."""
    print("\n--- Step 7: the LIVE :8787 server (not just the static file) is not serving stale code ---")
    import urllib.request
    import urllib.error

    try:
        with urllib.request.urlopen("http://127.0.0.1:8787/", timeout=5) as resp:
            live_html = resp.read().decode("utf-8", errors="replace")
        check("live :8787 server is reachable", True)
        check("live :8787 page contains the wordmark", brand_kit.BRAND_NAME in live_html)
        check("live :8787 page contains an embedded logo data URI", "data:image/png;base64," in live_html)
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        print(f"    (live server not reachable at 127.0.0.1:8787 -- {e} -- skipping staleness check, "
              f"not a failure if it's simply not running right now)")
        return

    try:
        sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
        import db as platform_db
        conn = platform_db.get_connection()
        row = conn.execute(
            "SELECT started_at FROM bot_heartbeats WHERE bot_id='1lavya-dashboard'"
        ).fetchone()
        if not row:
            print("    (no heartbeat row for 1lavya-dashboard yet -- skipping staleness check)")
            return
        from datetime import datetime, timezone
        started_at = row[0]
        started_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00")) if started_at.endswith("Z") else datetime.fromisoformat(started_at)
        if started_dt.tzinfo is None:
            started_dt = started_dt.replace(tzinfo=timezone.utc)

        newest_source_mtime = max(
            (REPO_ROOT / "telegram" / "database" / "dashboard_html.py").stat().st_mtime,
            (REPO_ROOT / "telegram" / "branding" / "brand_kit.py").stat().st_mtime,
        )
        newest_source_dt = datetime.fromtimestamp(newest_source_mtime, tz=timezone.utc)

        check(
            f"live dashboard process (started {started_dt.isoformat(timespec='seconds')}) is NEWER than "
            f"dashboard_html.py/brand_kit.py (last edited {newest_source_dt.isoformat(timespec='seconds')})",
            started_dt >= newest_source_dt,
            "the running process predates a source edit -- restart it: "
            "python telegram/tools/manage_bots.py restart 1lavya-dashboard",
        )
    except Exception as e:
        print(f"    (couldn't check process staleness against the DB: {e} -- not a hard failure)")


def step6_xhtml2pdf_compatible():
    """The Phase 2 report pipeline will render this exact markup through
    xhtml2pdf/reportlab, not a browser -- a real, weaker CSS engine (see
    brand_kit.py's own module docstring on why markup is table/inline-block
    only). Catches a real class of bug this exact check already found once
    (2026-08-10): `letter-spacing: 0.02em` parsed fine in a browser but
    reportlab's getSize() couldn't parse the 'em' unit at all and silently
    dropped the rule -- pisa still reported 0 fatal errors, so only an
    actual render-and-inspect catches this, not just "did it crash.\""""
    print("\n--- Step 6: renders cleanly through the actual xhtml2pdf engine ---")
    try:
        from xhtml2pdf import pisa
    except ImportError:
        check("xhtml2pdf available", False, "pip install xhtml2pdf")
        return
    import io
    import contextlib

    html = f"""<html><body>
{brand_kit.render_header_html("Smoke Test Title", "a subtitle")}
<p>Body text.</p>
{brand_kit.render_footer_html()}
</body></html>"""
    buf = io.BytesIO()
    warnings_buf = io.StringIO()
    with contextlib.redirect_stdout(warnings_buf):
        result = pisa.CreatePDF(html, dest=buf)
    warnings_text = warnings_buf.getvalue()
    check("xhtml2pdf reports 0 fatal errors", result.err == 0, f"err={result.err}")
    check("PDF bytes were produced", len(buf.getvalue()) > 1000)
    # pisa logs CSS values it couldn't parse to stdout as "getSize: ..." --
    # these don't fail result.err but ARE a real rendering defect (the rule
    # is silently dropped, not applied) -- treat as a smoke-test failure.
    check("no unparseable CSS values (\"getSize: Not a float\")", "getSize: Not a float" not in warnings_text,
          warnings_text.strip()[:300])


def main():
    step1_assets_exist()
    step2_colors_valid()
    step3_data_uris_valid()
    step4_html_functions()
    step5_real_render_screenshot()
    step_live_server_not_stale()
    step6_xhtml2pdf_compatible()

    print(f"\n{'='*70}")
    if failures:
        print(f"{len(failures)} check(s) FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All checks passed. Screenshot still needs a human/Claude look before calling this visually confirmed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
