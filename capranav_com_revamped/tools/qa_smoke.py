"""Smoke test for capranav.com: run after every deploy.

    python tools/qa_smoke.py                       # checks https://capranav.com (no browser needed)
    python tools/qa_smoke.py --base http://localhost:8799
    python tools/qa_smoke.py --browser             # also: no sideways scroll at phone/tablet/desktop widths
                                                   # (needs: pip install playwright, and Microsoft Edge installed)

What it checks (each line prints PASS or FAIL; the exit code is 1 if anything failed):
  * Search and AI crawler user-agents get 200 on the public pages (nobody is blocked by mistake).
  * The bulk data files and the anatomy API are refused to a bare request (403) and served to a same-site
    request (200). Uses a cache-busting query string, because Cloudflare may serve an old cached copy.
  * Every URL in sitemap.xml returns 200, and robots.txt, llms.txt, llms-full.txt, sitemap.txt exist.
  * A crawl of internal links finds no redirects or 404s (internal links must use clean URLs such as /about-us,
    not about-us.html, which 307-redirects).
  * (--browser) no page scrolls sideways at 320, 390, 768 and 1440 px.

Note: Cloudflare returns 403 to the Python-urllib user-agent, so this script sends a browser user-agent.
"""

from __future__ import annotations

import argparse
import random
import re
import sys
import urllib.error
import urllib.request

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
CRAWLERS = ["GPTBot/1.2", "OAI-SearchBot/1.0", "ChatGPT-User/1.0", "ClaudeBot/1.0", "Claude-SearchBot", "Claude-User",
            "PerplexityBot/1.0", "Googlebot/2.1", "Bingbot/2.0", "Applebot/0.1", "DuckDuckBot/1.1"]
PAGES = ["/", "/faq/", "/topics/", "/videos/", "/about-us", "/practice-with-pranav-bhaiya/must-practice/", "/llms.txt"]
DATA_FILES = ["/topics/data/topics.json", "/practice-with-pranav-bhaiya/must-practice/data/M2-C5-U1.json"]
FILES = ["/robots.txt", "/sitemap.xml", "/sitemap.txt", "/llms.txt", "/llms-full.txt", "/humans.txt"]
WIDTHS = [320, 390, 768, 1440]

failures = 0


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # report redirects instead of following them
        return None


opener = urllib.request.build_opener(NoRedirect)


def fetch(url: str, ua: str = BROWSER_UA, headers: dict | None = None) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": ua, **(headers or {})})
    try:
        with opener.open(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""


def check(ok: bool, label: str) -> None:
    global failures
    print(("PASS  " if ok else "FAIL  ") + label)
    if not ok:
        failures += 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://capranav.com")
    ap.add_argument("--browser", action="store_true")
    a = ap.parse_args()
    base = a.base.rstrip("/")

    print("== crawlers get the public pages")
    for ua in CRAWLERS:
        codes = {fetch(base + p, ua)[0] for p in PAGES}
        check(codes == {200}, f"{ua}: {sorted(codes)}")

    print("== data guard")
    for f in DATA_FILES:
        bust = f"?qa={random.randint(1, 10**9)}"
        check(fetch(base + f + bust)[0] == 403, f"bare request refused: {f}")
        check(fetch(base + f + bust, headers={"Sec-Fetch-Site": "same-origin"})[0] == 200, f"same-site request served: {f}")
    check(fetch(base + "/api/anatomy/topics")[0] == 403, "bare /api/anatomy/topics refused")

    print("== discovery files")
    for f in FILES:
        check(fetch(base + f)[0] == 200, f)
    sm = fetch(base + "/sitemap.xml")[1]
    urls = re.findall(r"<loc>([^<]+)</loc>", sm)
    bad = [u for u in urls if fetch(u)[0] != 200]
    check(bool(urls) and not bad, f"sitemap.xml: {len(urls)} URLs all 200" + (f" (bad: {bad})" if bad else ""))

    print("== internal links (no redirects, no 404s)")
    seen: dict[str, int] = {}
    queue = ["/"]
    while queue:
        path = queue.pop()
        if path in seen:
            continue
        status, body = fetch(base + path)
        seen[path] = status
        if status == 200:
            for h in re.findall(r'href="(/[^"#?]*)', body):
                if not h.startswith(("/assets", "/api")) and re.fullmatch(r"/[\w/-]*", h) and h not in seen:
                    queue.append(h)
    broken = {p: s for p, s in seen.items() if s != 200}
    check(not broken, f"{len(seen)} internal pages crawled; non-200: {broken or 'none'}")

    if a.browser:
        print("== no sideways scroll")
        from playwright.sync_api import sync_playwright  # imported late: optional dependency
        with sync_playwright() as p:
            b = p.chromium.launch(channel="msedge")
            for w in WIDTHS:
                ctx = b.new_context(viewport={"width": w, "height": 800}, is_mobile=w < 700)
                page = ctx.new_page()
                for path in sorted(seen):
                    page.goto(base + path, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(300)
                    sw, vw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
                    check(sw <= vw + 1, f"{w}px {path} (scrollWidth {sw}, viewport {vw})")
                ctx.close()
            b.close()

    print(f"\n{'ALL PASSED' if not failures else str(failures) + ' FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
