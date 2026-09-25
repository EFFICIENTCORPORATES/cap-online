"""Write crawler-readable HTML into the pages that are otherwise built in the browser.

Most AI crawlers do not run JavaScript, so /topics/, /videos/ and Must Practice used
to look empty to them ("Loading..."). This script renders the same public information
as plain HTML between ``ssr:start`` / ``ssr:end`` markers on each page:

* /topics/                  the Top 100 topics by past-exam marks (table)
* /videos/                  every video and Short, grouped, with links
* Must Practice             each published unit's questions: source, marks, topic,
                            why it was chosen, and the question text. NOT the answers.

Visitors with JavaScript never see these blocks: an inline script adds ``js`` to <html>
and ``.js .ssr {display:none}`` hides them, because the interactive page shows the same
information. Visitors and crawlers without JavaScript see the plain version.

Re-run after the data changes (it reads the same JSON the pages use)::

    python tools/build_topics_explorer_data.py    # if the topic data changed
    python tools/build_must_practice_data.py      # if the practice lists changed
    python tools/build_seo_static.py
    npx wrangler deploy
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
START, END = "<!-- ssr:start -->", "<!-- ssr:end -->"
JS_FLAG = "<script>document.documentElement.classList.add('js')</script>"

e = lambda s: html.escape(str(s), quote=True)


def plain(text_html: str, limit: int) -> str:
    text = re.sub(r"<[^>]+>", " ", text_html)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut + "…"


def topics_block() -> str:
    d = json.loads((PUBLIC / "topics/data/topics.json").read_text(encoding="utf-8"))
    units, topics, sittings = d["units"], d["topics"], d["sittings"]
    marks, count, papers = {}, {}, {}
    for ti, si, m, _ in d["rows"]:
        if sittings[si]["type"] != "PYQ":
            continue
        marks[ti] = marks.get(ti, 0) + m
        count[ti] = count.get(ti, 0) + 1
        papers.setdefault(ti, set()).add(si)
    ranked = sorted((i for i, t in enumerate(topics) if t["officialRank"] and t["officialRank"] <= 100),
                    key=lambda i: topics[i]["officialRank"])
    pyq = [s for s in sittings if s["type"] == "PYQ"]
    span = f"{min(pyq, key=lambda s: (s['year'], s['monthNo']))['label'].replace('PYQ ', '')} to " \
           f"{max(pyq, key=lambda s: (s['year'], s['monthNo']))['label'].replace('PYQ ', '')}"
    rows = []
    for i in ranked:
        t, u = topics[i], units[topics[i]["unit"]]
        path = u["chapter"] + ("" if u["single"] else f" › {u['unit']}")
        rows.append(
            f"<tr><td>{t['officialRank']}</td><td>{e(t['name'])}</td><td>{e(path)}</td>"
            f"<td>{round(marks.get(i, 0), 1):g}</td><td>{len(papers.get(i, ()))}</td>"
            f"<td>{e(t['page'])}</td><td>{e(t['id'])}</td></tr>"
        )
    return f"""{START}
<section class="panel ssr" id="ssr-topics">
  <h2>The 100 most important CA Inter Advanced Accounting topics</h2>
  <p>These 100 topics of the 400 in the ICAI Study Material have carried the most marks in ICAI's past exam papers (PYQs, {e(span)}). A question's marks are split equally across the topics it tests. Turn on JavaScript to filter by paper type (PYQ, MTP, RTP), year, module, chapter and unit, and to download the list as Excel.</p>
  <table class="ssr-table">
    <thead><tr><th>Rank</th><th>Topic</th><th>Chapter and unit</th><th>PYQ marks</th><th>Papers</th><th>Study Material page</th><th>Topic ID</th></tr></thead>
    <tbody>
{chr(10).join(rows)}
    </tbody>
  </table>
</section>
{END}"""


def videos_block() -> str:
    d = json.loads((PUBLIC / "videos/videos.json").read_text(encoding="utf-8"))
    parts = [START, '<section class="panel ssr" id="ssr-videos">',
             "<h2>CA Pranav's videos and Shorts</h2>",
             "<p>Study-plan videos, Advanced Accounting chapter revision and short exam-technique tips. Turn on JavaScript to watch them on this page.</p>"]
    for g in d["groups"]:
        vids = [v for v in d["videos"] if v["group"] == g["id"]]
        if not vids:
            continue
        kind = "Short" if g["type"] == "short" else "Video"
        parts.append(f"<h3>{e(g['title'])} ({kind}s)</h3><p>{e(g.get('blurb', ''))}</p><ul>")
        for v in vids:
            url = f"https://www.youtube.com/{'shorts/' if v['type'] == 'short' else 'watch?v='}{v['id']}"
            parts.append(f'<li><a href="{url}" rel="noopener">{e(v["title"])}</a></li>')
        parts.append("</ul>")
    parts += ["</section>", END]
    return "\n".join(parts)


def practice_block() -> str:
    parts = [START, '<section class="ssr" id="ssr-questions">']
    for f in sorted((PUBLIC / "practice-with-pranav-bhaiya/must-practice/data").glob("M*-C*-U*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if not d.get("published"):
            continue
        parts.append(f"<h2>{e(d['standard'])} — {e(d['unit_title'])}: {len(d['questions'])} must-practice questions</h2>")
        parts.append(f"<p>{e(d['chapter'])}, {e(d['module'].title())}. Chosen from every MTP, RTP and PYQ, ranked by how heavily the topic has been examined. Answers are on the interactive page.</p><ol>")
        for q in d["questions"]:
            topics = "; ".join(t["topic_name"] for t in q["topics"][:3])
            parts.append(
                f"<li><strong>{e(q['source_label'])}, {e(q['question_no'])}</strong> &middot; {e(q['marks_text'])} &middot; Topic: {e(topics)}."
                f" Why practise it: {e(q['why'])}<br>{e(plain(q['question_html'], 650))}</li>"
            )
        parts.append("</ol>")
    parts += ["</section>", END]
    return "\n".join(parts)


def inject(rel: str, block: str, anchor_pattern: str, after: bool) -> None:
    p = PUBLIC / rel
    s = p.read_text(encoding="utf-8")
    s = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", s, flags=re.S)
    m = re.search(anchor_pattern, s, flags=re.S)
    assert m, f"{rel}: anchor not found"
    pos = m.end() if after else m.start()
    s = s[:pos] + "\n" + block + "\n" + s[pos:]
    if JS_FLAG not in s:
        s = s.replace("<body>", "<body>\n" + JS_FLAG, 1)
    p.write_text(s, encoding="utf-8")
    print(f"  {rel}")


def main() -> None:
    inject("topics/index.html", topics_block(), r'<div class="notice" id="status"[^>]*>.*?</div>', after=True)
    inject("videos/index.html", videos_block(), r'<section id="pane-video"', after=False)
    inject("practice-with-pranav-bhaiya/must-practice/index.html", practice_block(), r'<section class="picker"', after=False)
    print("Wrote crawler-readable blocks")


if __name__ == "__main__":
    main()
