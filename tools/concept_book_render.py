#!/usr/bin/env python3
"""
concept_book_render.py - render one Concept Book unit file to a self-contained HTML preview.

  python3 tools/concept_book_render.py M3-C14-U0

Reads  books/ca-inter/concept-book/content/<unit>.md
Writes books/ca-inter/concept-book/content/generated/<unit>.preview.html   (generated: never hand-edit)

Design (Pranav, 2026-11-13):
  * handwritten look from the FONT (Patrick Hand body, Caveat headings), wobbly borders, arrows; plain white paper
  * a box for each topic, with a header tab; coloured callouts for each box type, with a colour legend
  * ruled lines ONLY inside text blocks (line height equals the rule pitch so writing sits on the lines) and on the
    student's writing area; diagrams, steps, tables and callouts sit on plain panels
Fonts are downloaded once from Google Fonts (open licence) into content/vendor/ (git-ignored: no binaries in git) and
embedded in the HTML as base64 text so the preview is one file. If the download fails the page falls back to a system
handwriting-style font.
"""
import base64, html, json, os, re, sys, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CB = os.path.join(REPO, "books", "ca-inter", "concept-book")
VENDOR = os.path.join(CB, "content", "vendor")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
FONTS = (("Patrick Hand", "400", "PatrickHand-400.woff2"), ("Caveat", "700", "Caveat-700.woff2"))


def font_css():
    os.makedirs(VENDOR, exist_ok=True)
    out = []
    for fam, wt, fn in FONTS:
        path = os.path.join(VENDOR, fn)
        if not os.path.exists(path):
            try:
                url = "https://fonts.googleapis.com/css2?family=" + fam.replace(" ", "+") + ("" if fam == "Patrick Hand" else ":wght@" + wt) + "&display=swap"
                css = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode()
                block = re.search(r"/\* latin \*/\s*@font-face\s*\{[^}]*?url\((https://[^)]+)\)", css, re.S)
                open(path, "wb").write(urllib.request.urlopen(urllib.request.Request(block.group(1), headers=UA), timeout=30).read())
            except Exception as e:
                print("font download failed:", fam, e); continue
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-weight:{wt};font-style:normal;src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
    return "\n".join(out)


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"\[(T[\d\.]+)\]", r'<span class="tag">\1</span>', s)
    s = re.sub(r"\b(Wrong:)", r'<span class="wrong">\1</span>', s)
    s = re.sub(r"\b(Right:)", r'<span class="right">\1</span>', s)
    s = re.sub(r"\b(Why:)", r'<span class="why">\1</span>', s)
    s = s.replace("→", '<span class="arr">→</span>')
    return s


def lists(lines, steps=False):
    """render a block of list/paragraph lines to HTML (nested bullets by indentation)."""
    out, stack = [], []   # stack of (indent, tag)
    def close_to(ind):
        while stack and stack[-1][0] >= ind:
            out.append(f"</{stack.pop()[1]}>")
    for raw in lines:
        if not raw.strip(): continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", raw)
        if m:
            ind, mark, txt = len(m.group(1)), m.group(2), m.group(3)
            tag = "ol" if mark[0].isdigit() else "ul"
            if not stack or ind > stack[-1][0]:
                out.append(f'<{tag}{" class=steps" if (steps and tag=="ol" and not stack) else ""}>'); stack.append((ind, tag))
            else:
                close_to(ind + 1)
                if stack and stack[-1][0] == ind and stack[-1][1] != tag:
                    out.append(f"</{stack.pop()[1]}>"); out.append(f"<{tag}>"); stack.append((ind, tag))
            out.append(f"<li>{inline(txt)}")
        else:
            close_to(0); out.append(f"<p>{inline(raw.strip())}</p>")
        # li closed lazily
    close_to(0)
    # close <li> tags: simple approach, add </li> before next <li> / closing tags
    h = "".join(out)
    h = re.sub(r"(<li>.*?)(?=<li>|</ul>|</ol>|<ul|<ol)", r"\1</li>", h, flags=re.S)
    return h


def table(lines):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines if not re.match(r"^\s*\|[\s\-:|]+\|\s*$", l)]
    if rows and rows[0][0] == "Key": rows = [r[1:] for r in rows]   # the key column repeats the reference column
    h = "<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr></thead><tbody>"
    for r in rows[1:]: h += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
    return h + "</tbody></table>"


def blocks(lines):
    """split a run of lines into table / list-or-paragraph chunks and render."""
    out, buf, tb = [], [], []
    def flush():
        nonlocal buf, tb
        if tb: out.append(f'<div class="panel">{table(tb)}</div>'); tb = []
        if buf: out.append(lists(buf)); buf = []
    for l in lines:
        if l.strip().startswith("|"):
            if buf: out.append(lists(buf)); buf = []
            tb.append(l)
        else:
            if tb: out.append(f'<div class="panel">{table(tb)}</div>'); tb = []
            buf.append(l)
    flush()
    return "".join(out)


LABELS = ("Concept", "Exam algorithm", "Exam points", "Stories", "Linkages", "Linkages:", "Remember", "Where ICAI tests it")


def split_labelled(lines):
    """split topic lines into [(label, inline_rest, [lines])] by lines that start with **Label."""
    parts, cur = [], None
    for l in lines:
        m = re.match(r"^\*\*(Concept|Exam algorithm|Exam points|Stories:\*\*|Linkages|Remember)(.*)$", l)
        if m:
            cur = [m.group(1).rstrip(":*"), l, []]; parts.append(cur)
        elif cur is not None: cur[2].append(l)
    return parts


def callout(kind, label, body_html, extra=""):
    sym = dict(concept="●", algo="①", point="!", err="✗", link="↔", rem="♥", story="✎").get(kind, "")
    return f'<div class="co {kind}{extra}"><div class="lab"><span class="sym">{sym}</span> {label}</div>{body_html}</div>'


def error_bullets(items):
    out = []
    for t in items:
        common = "(most common)" in t
        t2 = re.sub(r"^\*\*Error Register( \(most common\))?:\*\*\s*", "", t)
        out.append(callout("err", "Error Register" + (' <span class="star">★ most common</span>' if common else ""), f"<p>{inline(t2)}</p>"))
    return "".join(out)


def render(unit):
    p = os.path.join(CB, "content", f"{unit}.md")
    text = open(p, encoding="utf-8").read()
    fm = {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    for l in m.group(1).split("\n"):
        k = re.match(r"^(\w+):\s*(.*)$", l)
        if k: fm[k.group(1)] = k.group(2).strip().strip('"')
    body = text[m.end():]
    secs = re.split(r"^## ", body, flags=re.M)
    head, secs = secs[0], secs[1:]
    theme = re.search(r"^> (.*)$", head, re.M)
    common_errors = []
    html_parts = []
    for sec in secs:
        title, _, rest = sec.partition("\n")
        lines = [l for l in rest.split("\n") if l.strip() and not l.startswith("<!--") and l.strip() != "---"]
        if title.startswith("Unit map"):
            html_parts.append(f'<section class="plain"><h2>Unit map</h2>{blocks(lines)}</section>')
        elif title.startswith("Stories"):
            items = [l[2:] for l in lines if l.startswith("- ")]
            boxes = []
            for it in items:
                mm = re.match(r"\*\*(S\d+) · (.*?)\*\*\s*(.*)", it)
                if mm: boxes.append(callout("story", f"Story {mm.group(1)}: {inline(mm.group(2).rstrip('.'))}", f"<p>{inline(mm.group(3))}</p>"))
            html_parts.append(f'<section class="plain"><h2>Stories</h2>{"".join(boxes) or "<p>None yet.</p>"}</section>')
        elif re.match(r"T[\d\.]+ ", title):
            tid, _, tname = title.partition(" · "); tname = re.sub(r"\s*\{#.*\}", "", tname)
            inner = []
            for label, first, rest_l in split_labelled(lines):
                content = [re.sub(r"^\*\*[^*]+\*\*:?\s*", "", first)] if label in ("Remember", "Stories") else []
                content = [c for c in content if c.strip()]
                if label == "Concept":
                    inner.append(callout("concept", "Concept", f'<div class="ruled">{lists(rest_l)}</div>'))
                elif label == "Exam algorithm":
                    note = re.search(r"\*(.*?)\*", first); sub = f'<p class="note">{inline(note.group(1))}</p>' if note else ""
                    inner.append(callout("algo", "Exam algorithm", sub + lists(rest_l, steps=True)))
                elif label == "Exam points":
                    inner.append(callout("point", "Exam points", lists(rest_l)))
                elif label == "Stories":
                    inner.append(f'<div class="meta">{inline(first)}</div>')
                elif label == "Linkages":
                    inner.append(callout("link", "Linkages", lists(rest_l)))
                elif label == "Remember":
                    inner.append(callout("rem", "Remember", f"<p>{inline(first[len('**Remember**'):].strip())}</p>"))
            html_parts.append(f'<section class="topic" id="{tid.lower()}"><div class="tab">{html.escape(tid)} · {inline(tname)}</div>{"".join(inner)}</section>')
        elif title.startswith("Illustration cards") or title.startswith("Test Your Knowledge"):
            cards = re.split(r"^### ", rest, flags=re.M)
            intro, cards = cards[0], cards[1:]
            out = [f"<h2>{html.escape(title)}</h2>"]
            for c in cards:
                ctitle, _, crest = c.partition("\n")
                clines = [l for l in crest.split("\n") if l.strip() and l.strip() != "---"]
                if ctitle.startswith("MCQs"):
                    out.append(f"<h3>{html.escape(ctitle)}</h3>{blocks(clines)}"); continue
                if ctitle.startswith("Same as"):
                    out.append(f'<div class="co algo"><div class="lab">{html.escape(ctitle)}</div>{lists(clines)}</div>'); continue
                key, _, name = ctitle.partition(" · ")
                fields, cur, errs = [], None, []
                for l in clines:
                    f = re.match(r"^\*\*(Difficulty|Goal|Concepts|Given|Approach|Exam points|Tricky points):\*\*\s*(.*)$", l)
                    if f: cur = [f.group(1), f.group(2), []]; fields.append(cur)
                    elif cur is not None: cur[2].append(l)
                rows, diff, pts, tricky = [], "", "", ""
                for fname, val, extra in fields:
                    if fname == "Difficulty":
                        d = re.match(r"(\w+) \(computed from (\d+) concepts\)", val); diff = f'<span class="diff {d.group(1).lower()}">{d.group(1)}</span> <span class="dn">{d.group(2)} concepts</span>' if d else ""
                    elif fname == "Exam points": pts = callout("point", "Exam points", f"<p>{inline(val)}</p>")
                    elif fname == "Tricky points":
                        items = [x.strip()[2:] for x in extra if x.strip().startswith("- ")]
                        for t in items:
                            if "(most common)" in t: common_errors.append((key, t))
                        tricky = error_bullets(items)
                    else:
                        rows.append(f'<div class="row"><div class="k">{fname}</div><div class="v">{inline(val)}</div></div>')
                out.append(f'<article class="card"><div class="chead"><span class="key">{html.escape(key)}</span> <span class="cname">{inline(name)}</span> {diff}</div><div class="panel rows">{"".join(rows)}</div>{pts}{tricky}</article>')
            html_parts.append(f'<section class="plain">{"".join(out)}</section>')
    # most common errors page
    items = []
    for key, t in common_errors:
        t2 = re.sub(r"^\*\*Error Register \(most common\):\*\*\s*", "", t)
        items.append(f"<li><span class=\"from\">{html.escape(key)}</span> {inline(t2)}</li>")
    mce = f'<section class="mce"><h2>Most Common Errors</h2><p class="note">Collected by script from the cards flagged “most common”. Sanjeevani Booti 2: now add your own.</p><ol class="errs">{"".join(items)}</ol><h3>My own errors</h3><div class="writing"></div></section>'
    legend = "".join(f'<span class="lg {k}"><span class="sym">{s}</span> {n}</span>' for k, s, n in (
        ("story", "✎", "Story"), ("concept", "●", "Concept"), ("algo", "①", "Exam algorithm"), ("point", "!", "Exam point"),
        ("err", "✗", "Error Register"), ("link", "↔", "Linkage"), ("rem", "♥", "Remember")))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(fm.get('title','Unit'))}: Concept Book preview</title><style>{font_css()}{CSS}</style></head><body>
<main><header><div class="eyebrow">{html.escape(fm.get('part_of_syllabus',''))} · {html.escape(fm.get('unit_id',''))}</div>
<h1>{html.escape(fm.get('title',''))}</h1><div class="sub">{html.escape(fm.get('icai_chapter',''))} · {html.escape(fm.get('edition',''))}</div>
{f'<div class="theme">{inline(theme.group(1))}</div>' if theme else ''}<div class="legend"><b>Colour key:</b> {legend}</div>
<div class="draft">Preview of a skeleton draft. Layout and look only; content awaits Pranav's review.</div></header>
{''.join(html_parts)}{mce}</main></body></html>"""
    out = os.path.join(CB, "content", "generated", f"{unit}.preview.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    print("wrote", out, f"({len(page)//1024} KB)")


CSS = """
:root{--ink:#1b2a4a;--muted:#5d6b82;--rule:#cfdaea;--hand:'Patrick Hand','Comic Neue','Segoe Print','Bradley Hand',cursive;--head:'Caveat','Patrick Hand',cursive}
*{box-sizing:border-box}
body{margin:0;background:#f1efe9;color:var(--ink);font-family:var(--hand);font-size:18px;line-height:28px}
main{max-width:860px;margin:0 auto;background:#fff;padding:20px 22px 60px;min-height:100vh}
header{border-bottom:3px double var(--ink);padding-bottom:10px;margin-bottom:18px}
.eyebrow{font-family:var(--head);font-size:22px;color:#c62828}
h1{font-family:var(--head);font-size:50px;line-height:52px;margin:0}
h2{font-family:var(--head);font-size:34px;line-height:40px;margin:26px 0 8px}
h3{font-family:var(--head);font-size:26px;margin:16px 0 6px}
.sub{color:var(--muted)}
.theme{margin:10px 0;padding:6px 12px;border:2px solid #2f9e6b;background:#eaf7ee;border-radius:12px 16px 10px 15px/15px 10px 16px 12px}
.legend{display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center;margin-top:10px;font-size:16px}
.lg{border:2px solid;border-radius:10px 14px 9px 13px/13px 9px 14px 10px;padding:0 9px;line-height:24px;white-space:nowrap}
.draft{margin-top:10px;font-size:15px;color:var(--muted)}
.story{background:#fff3c4;border-color:#d9a200}.concept{background:#fff;border-color:#4a6fa5}.algo{background:#e8f6ee;border-color:#2f9e6b}
.point{background:#ffeedd;border-color:#e8731a}.err{background:#fde8e8;border-color:#c62828}.link{background:#e6eefc;border-color:#2f6fdb}.rem{background:#f1e7fb;border-color:#7b3fb0}
.co{border:2px solid;border-left-width:8px;border-radius:12px 16px 10px 15px/15px 10px 16px 12px;padding:6px 12px 8px;margin:10px 0;break-inside:avoid}
.co .lab{font-family:var(--head);font-size:23px;line-height:28px;color:var(--ink)}
.co .sym{display:inline-block;min-width:1em}
.co.concept{break-inside:auto}
.ruled{line-height:28px;background-image:repeating-linear-gradient(to bottom,transparent 0,transparent 27px,var(--rule) 27px,var(--rule) 28px)}
.ruled p,.ruled ul,.ruled ol,.ruled li{margin:0}
.ruled ul,.ruled ol{padding-left:24px}
.topic{border:3px solid var(--ink);border-radius:16px 22px 14px 24px/22px 14px 24px 16px;margin:34px 0 26px;padding:30px 14px 8px;position:relative;background:#fff}
.tab{position:absolute;top:-20px;left:16px;background:var(--ink);color:#fff;font-family:var(--head);font-size:26px;line-height:34px;padding:0 16px;border-radius:10px 14px 8px 12px/12px 8px 14px 10px;max-width:92%}
.meta{font-size:16px;color:var(--muted);margin:2px 0 4px}
.co p{margin:0}.co ul,.co ol{margin:4px 0;padding-left:24px}.co li{margin:0}
ol.steps{list-style:none;counter-reset:s;padding-left:0}
ol.steps>li{counter-increment:s;position:relative;padding-left:40px;margin:4px 0;min-height:30px}
ol.steps>li:before{content:counter(s);position:absolute;left:4px;top:1px;width:28px;height:28px;border:2px solid #2f9e6b;border-radius:50% 46% 52% 48%;text-align:center;line-height:24px;background:#fff;font-family:var(--head);font-size:20px}
.note{font-size:15px;color:var(--muted);margin:0 0 2px}
.panel{background:#fff;border:2px solid var(--ink);border-radius:10px 14px 9px 13px/13px 9px 14px 10px;padding:6px 10px;margin:10px 0;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:16px;line-height:22px}
th,td{border:1px solid #9aa7bd;padding:3px 7px;text-align:left;vertical-align:top}th{background:#eef2f9;font-family:var(--head);font-size:20px}
.tag{display:inline-block;border:1.5px solid var(--ink);border-radius:8px;padding:0 6px;font-size:14px;line-height:19px;background:#fff;vertical-align:1px}
.wrong{color:#c62828;font-weight:bold}.right{color:#1f7a4f;font-weight:bold}.why{color:#5d6b82;font-weight:bold}
.star{font-size:17px;color:#b34700}
.card{border:3px solid var(--ink);border-radius:14px 20px 12px 22px/20px 12px 22px 14px;padding:10px 12px;margin:22px 0;background:#fff}
.chead{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline;font-family:var(--head);font-size:27px;line-height:34px}
.key{background:var(--ink);color:#fff;padding:0 10px;border-radius:8px 12px 7px 11px}
.diff{font-size:20px;padding:0 10px;border-radius:12px;border:2px solid}.diff.easy{background:#e8f6ee;border-color:#2f9e6b}.diff.medium{background:#fff3c4;border-color:#d9a200}.diff.hard{background:#fde8e8;border-color:#c62828}
.dn{font-family:var(--hand);font-size:15px;color:var(--muted)}
.rows .row{display:grid;grid-template-columns:110px 1fr;gap:8px;padding:2px 0;border-bottom:1px dashed #c9d2e2}.rows .row:last-child{border:0}
.rows .k{font-family:var(--head);font-size:21px;color:#4a6fa5}
.mce{margin-top:40px;break-before:page}
ol.errs li{margin:6px 0}.from{font-family:var(--head);background:var(--ink);color:#fff;border-radius:7px;padding:0 7px;font-size:17px}
.writing{height:420px;border:2px solid var(--ink);border-radius:12px 16px 10px 15px/15px 10px 16px 12px;line-height:28px;background-image:repeating-linear-gradient(to bottom,transparent 0,transparent 27px,var(--rule) 27px,var(--rule) 28px)}
code{font-family:inherit;background:#eef2f9;padding:0 4px;border-radius:4px}
@media (max-width:560px){body{font-size:17px}.rows .row{grid-template-columns:1fr}h1{font-size:40px}main{padding:14px 12px}}
@media print{body{background:#fff}main{padding:0;max-width:none}.topic,.card{break-inside:auto}.co{break-inside:avoid}@page{size:A4;margin:12mm}}
"""

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    render(sys.argv[1])
