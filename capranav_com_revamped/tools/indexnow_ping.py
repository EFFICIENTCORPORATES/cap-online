"""Tell IndexNow search engines (Bing, Yandex and others; Google does not use it) that the site's public URLs
are new or changed. Bing's index also feeds several AI assistants. Safe to re-run after each content change.

    python tools/indexnow_ping.py           # sends every URL in public/sitemap.txt

Needs public/<key>.txt, written by build_discovery_files.py. Only public URLs are sent.
"""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
key = (ROOT / "tools/.indexnow-key").read_text(encoding="utf-8").strip()
urls = [u for u in (ROOT / "public/sitemap.txt").read_text(encoding="utf-8").split() if u]
body = json.dumps({"host": "capranav.com", "key": key, "keyLocation": f"https://capranav.com/{key}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("IndexNow accepted", len(urls), "URLs: HTTP", r.status)
except urllib.error.HTTPError as e:
    print("IndexNow replied HTTP", e.code, e.read()[:200])
    sys.exit(1)
