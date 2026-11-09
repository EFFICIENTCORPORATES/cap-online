#!/usr/bin/env python3
"""Assemble src/ (CSS + JS + slide fragments) into one self-contained HTML deck.

Usage:  python3 build_deck.py
Output: kahaani-restructuring-map.html  (no network needed) and slides-manifest.json
Every slide gets the same brand label + CApranav.com mark injected here.
"""
import glob, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
OUT = os.path.join(HERE, "kahaani-restructuring-map.html")

css = "\n".join(open(f, encoding="utf-8").read() for f in sorted(glob.glob(os.path.join(SRC, "style*.css"))))
js = open(os.path.join(SRC, "app.js"), encoding="utf-8").read()
slides = "\n".join(open(f, encoding="utf-8").read() for f in sorted(glob.glob(os.path.join(SRC, "slides-*.html"))))

inject = '<div class="brand">Kahaani · CA Inter Advanced Accounts</div><div class="mark">CApranav.com</div>\n</section>'
slides = slides.replace("</section>", inject)
# wrap each slide's content in .pad so container units (cqw) are measured against the full slide
slides = re.sub(r'(<section class="slide"[^>]*>)(.*?)(<div class="brand">)', lambda m: m.group(1) + '<div class="pad">' + m.group(2) + '</div>' + m.group(3), slides, flags=re.S)

manifest = []
for m in re.finditer(r'<section class="slide" id="([^"]+)" data-sec="([^"]*)" data-title="([^"]*)">(.*?)</section>', slides, re.S):
    sid, sec, title, body = m.groups()
    nums = [int(n) for n in re.findall(r'data-(?:at|until)="(\d+)"', body)]
    for attr in re.findall(r'data-(?:st|txt)="([^"]*)"', body):
        nums += [int(k) for k in re.findall(r'(?:^|\|)(\d+):', attr)]
    used = set(nums)
    dead = [n for n in range(1, (max(nums) if nums else 0) + 1) if n not in used]
    if dead:
        print(f"WARNING: slide {sid} has dead steps (no effect on click): {dead}")
    manifest.append({"id": sid, "section": sec, "title": title, "steps": max(nums) if nums else 0})

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kahaani: Reconstruction, Amalgamation and Consolidation | CA Pranav</title>
<meta name="description" content="The map before the maths: how internal reconstruction, amalgamation and consolidation connect. CA Inter Advanced Accounting.">
<style>
{css}
</style>
</head>
<body>
<main id="deck" aria-label="Kahaani: Reconstruction, Amalgamation and Consolidation">
<button id="tocbtn" title="Contents (T)">☰ Contents</button>
<nav id="toc" aria-label="Contents"></nav>
{slides}
<div id="toast"></div>
<div id="progress"></div>
<div id="controls">
  <button id="prev" title="Back" aria-label="Back">‹</button>
  <span id="counter"></span>
  <button id="next" title="Next" aria-label="Next">›</button>
  <button id="printbtn" class="wide" title="Print or save as PDF (P)">Print / Save PDF</button>
</div>
</main>
<script>
{js}
</script>
</body>
</html>
"""
open(OUT, "w", encoding="utf-8").write(html)
json.dump(manifest, open(os.path.join(HERE, "slides-manifest.json"), "w", encoding="utf-8"), indent=1)
print(f"built {OUT}  ({len(html)//1024} KB, {len(manifest)} slides)")
for s in manifest: print(f"  {s['id']:6} steps={s['steps']:2}  {s['section']}  |  {s['title']}")
