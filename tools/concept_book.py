#!/usr/bin/env python3
"""
concept_book.py - deterministic helpers for the Concept Book unit files.

Subcommands (all take a unit id such as M3-C14-U0):
  refs <unit>                     read the ICAI chapter Markdown and write the registry of every illustration,
                                  example and Test Your Knowledge item (key, label, entity name, marks of care):
                                  books/ca-inter/concept-book/content/generated/<unit>.refs.json
  chips <unit> [--write]          computed importance data for the unit (topic rank/band/marks from the Must
                                  Practice topic map, Question Bank counts, Must Practice question count);
                                  with --write, refreshes the GENERATED block inside the unit file
  validate <unit> [--fix-difficulty]
                                  check the unit file against the rules in CONCEPT-BOOK-BUILD-PLAN.md:
                                  every topic and every ICAI item covered, card fields present, difficulty
                                  computed from the number of concepts, Most Common Errors count, no page
                                  numbers, no leftover [verify] tags, no model names

Nothing here is AI judgement: everything is parsed or counted. Page numbers are read from the ICAI file only to
place an item; they must never appear in the unit file (Pranav's rule, 2026-11-13).
"""
import csv, glob, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CB = os.path.join(REPO, "books", "ca-inter", "concept-book")
ALL = os.path.join(REPO, "books", "ca-inter", "smat-may-27-edition", "all-modules")
INDEX = os.path.join(CB, "syllabus-engine", "data", "1-ca-inter-adv-accounts-topic-page-index.json")
TOPIC_MAP = os.path.join(REPO, "books", "ca-inter", "smat-may-27-edition", "practice-with-pranav-bhaiya", "data", "must_practice_topic_map.csv")
QINDEX = os.path.join(REPO, "first_run", "output", "generated-from-script", "questions_index.json")
MP_DIR = os.path.join(REPO, "capranav_com_revamped", "public", "practice-with-pranav-bhaiya", "must-practice", "data")
GEN = os.path.join(CB, "content", "generated")
ENTITY = re.compile(r"\b((?:Mr\.|Mrs\.|Ms\.)\s[A-Z][a-z]+|[A-Z][A-Za-z&\.\-]*(?:\s[A-Z&][A-Za-z&\.\-]*){0,3}\s(?:Ltd\.?|Limited|Co\.?|Bros\.?|Company|Corporation|Industries|Enterprises|& Co\.?))")


def icai_file(unit):
    m, c, u = re.match(r"M(\d)-C(\d+)-U(\d)", unit).groups()
    hits = [f for f in glob.glob(os.path.join(ALL, f"M{m}_C{c}_U{u}[_ ]*_BEAUTIFIED.md")) if "Initial" not in f and "Annexure" not in f]
    if not hits: sys.exit(f"no ICAI file for {unit}")
    return hits[0]


def unit_meta(unit):
    d = json.load(open(INDEX, encoding="utf-8"))
    return next(c for c in d["chapters"] if c["unique_chapter_id"] == unit)


def entity_in(text):
    m = ENTITY.search(text)
    return m.group(1).strip().rstrip(".,") if m else ""


def build_refs(unit):
    lines = open(icai_file(unit), encoding="utf-8").read().split("\n")
    items, page, in_scen, qnum, last_n = [], None, False, None, 0
    for i, l in enumerate(lines):
        pm = re.search(r'printed_page="([\d\.]+)"', l)
        if pm: page = pm.group(1)
        h = re.match(r"#### (ILL|EX)-(\d+)(-\d+)?\s+[—-]\s+(.*)", l)
        if h:
            kind, n, sub = h.group(1), h.group(2), h.group(3) or ""
            body = " ".join(x.strip() for x in lines[i + 1:i + 14] if x.strip() and not x.startswith("<!--"))
            label = ("Illustration " if kind == "ILL" else "Example ") + n + ("(b)" if sub else "")
            items.append(dict(key=f"{kind}-{n}{sub}", label=label, entity=entity_in(body), page=page))
            continue
        h = re.match(r"#### TYK-(MCQ|TQ)-(\d+)", l)
        if h:
            last_n = max(last_n, int(h.group(2)))
            items.append(dict(key=f"TYK-{h.group(1)}-{h.group(2)}", label=("TYK MCQ " if h.group(1) == "MCQ" else "TYK Theory Q") + h.group(2), entity="", page=page))
            continue
        if re.match(r"\s*Scenario[ -]based Questions", l, re.I): in_scen = True
        if in_scen:
            q = re.match(r"^(\d{1,2})\.?\s+(.*)", l)
            if q and int(q.group(1)) > last_n and (qnum is None or int(q.group(1)) == qnum + 1) and (qnum is not None or int(q.group(1)) == last_n + 1):
                qnum = int(q.group(1))
                body = " ".join(x.strip() for x in lines[i:i + 6])
                items.append(dict(key=f"TYK-Q{qnum}", label=f"TYK Q{qnum}", entity=entity_in(body), page=page))
            if re.match(r"ANSWERS/HINTS", l): in_scen = False
    os.makedirs(GEN, exist_ok=True)
    out = os.path.join(GEN, f"{unit}.refs.json")
    json.dump(dict(unit=unit, edition="ICAI July 2026 edition (May 2027 attempt)", source=os.path.basename(icai_file(unit)),
                   note="pages are for placement only and never appear in the book; unchecked against the PDF", items=items),
              open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"wrote {out}: {len(items)} items")
    for it in items: print(f"  {it['key']:<12} {it['label']:<16} {it['entity']}")


def chips(unit, write=False):
    meta = unit_meta(unit)
    rows = list(csv.DictReader(open(TOPIC_MAP, encoding="utf-8-sig")))
    out = {}
    for r in rows:
        if r["unit_id"] == unit and r["topic_id"] not in out:
            out[r["topic_id"]] = dict(topic=r["topic_name"], rank=r["overall_rank"], band=r["priority_band"],
                                      pyq_marks=r["pyq_allocated_marks"], must_practice=r["must_practice_question_count"])
    q = [r for r in json.load(open(QINDEX, encoding="utf-8")) if r.get("final_chapter") == unit]
    sittings = sorted({r["session_key"] for r in q})
    mp = ""
    mpf = os.path.join(MP_DIR, f"{unit}.json")
    if os.path.exists(mpf):
        d = json.load(open(mpf, encoding="utf-8"))
        lst = d if isinstance(d, list) else next((v for v in d.values() if isinstance(v, list) and v and isinstance(v[0], dict)), [])
        mp = len(lst)
    lines = [f"Asked in {meta['marks_distinct_attempt_count']} attempts (topic index); {len(q)} Question Bank records across {len(sittings)} sittings; Must Practice questions on the website: {mp or 'n/a'}.", "",
             "| Topic | Rank (of 400) | Band | PYQ marks allocated | Must Practice questions |", "|---|---|---|---|---|"]
    for t in meta["topics"]:
        c = out.get(t["unique_topic_id"], {})
        lines.append(f"| {t['unique_topic_id'].split('-')[-1]} {t['topic_name']} | {c.get('rank','-')} | {c.get('band','-')} | {c.get('pyq_marks','-')} | {c.get('must_practice','-')} |")
    block = "\n".join(lines)
    print(block)
    os.makedirs(GEN, exist_ok=True)
    json.dump(dict(unit=unit, topics=out, qb_records=len(q), sittings=sittings, must_practice=mp), open(os.path.join(GEN, f"{unit}.chips.json"), "w", encoding="utf-8"), indent=1)
    if write:
        p = os.path.join(CB, "content", f"{unit}.md")
        t = open(p, encoding="utf-8").read()
        new = "<!-- GENERATED:CHIPS (tools/concept_book.py chips --write; do not edit by hand) -->\n" + block + "\n<!-- /GENERATED:CHIPS -->"
        t = re.sub(r"<!-- GENERATED:CHIPS.*?<!-- /GENERATED:CHIPS -->", lambda m: new, t, flags=re.S)
        open(p, "w", encoding="utf-8").write(t)
        print("refreshed generated block in", p)


def difficulty(n):
    return "Easy" if n <= 2 else ("Medium" if n <= 5 else "Hard")


def validate(unit, fix=False):
    p = os.path.join(CB, "content", f"{unit}.md")
    text = open(p, encoding="utf-8").read()
    meta = unit_meta(unit)
    refs = json.load(open(os.path.join(GEN, f"{unit}.refs.json"), encoding="utf-8"))["items"]
    errs, warns = [], []
    # topics
    for t in meta["topics"]:
        tid = t["unique_topic_id"].split("-")[-1]
        if not re.search(rf"^## {tid}\b", text, re.M): errs.append(f"topic section missing: {tid} {t['topic_name']}")
    # cards
    cards = {m.group(1): m.start() for m in re.finditer(r"^### ((?:ILL|EX|TYK)-[A-Za-z0-9\-]+) ", text, re.M)}
    mcq_rows = set(re.findall(r"^\| (TYK-MCQ-\d+) \|", text, re.M))
    tq_rows = set(re.findall(r"^\| (TYK-TQ-\d+) \|", text, re.M))
    covered = set(cards) | mcq_rows | tq_rows | set(re.findall(r"^- (TYK-Q\d+) is the same as", text, re.M))
    for it in refs:
        if it["key"] not in covered: errs.append(f"ICAI item not covered: {it['key']} ({it['label']} {it['entity']})")
    for k in covered - {it["key"] for it in refs}: errs.append(f"card refers to an ICAI item that does not exist: {k}")
    # card fields and computed difficulty
    names = {it["key"]: it for it in refs}
    for k, pos in cards.items():
        end = min([v for v in cards.values() if v > pos] + [len(text)])
        body = text[pos:end]
        for f in ("Goal", "Concepts", "Given", "Approach", "Exam points", "Tricky points"):
            if f"**{f}:**" not in body: errs.append(f"{k}: field missing: {f}")
        m = re.search(r"\*\*Concepts:\*\*\s*(.+)", body)
        n = len([x for x in re.split(r";\s*", m.group(1)) if x.strip()]) if m else 0
        exp = difficulty(n)
        d = re.search(r"\*\*Difficulty:\*\*\s*(\w+)[^\n]*", body)
        line = f"**Difficulty:** {exp} (computed from {n} concepts)"
        if not d:
            if fix: text = text.replace(body, re.sub(r"(^### [^\n]*\n)", lambda mm: mm.group(1) + line + "\n", body, count=1), 1)
            else: errs.append(f"{k}: Difficulty line missing (expected {exp})")
        elif d.group(1) != exp or f"{n} concepts" not in d.group(0):
            if fix: text = text.replace(d.group(0), line, 1)
            else: errs.append(f"{k}: Difficulty is {d.group(1)}, expected {exp} ({n} concepts)")
        ent = names.get(k, {}).get("entity", "")
        head = re.match(r"### [^\n]*", body).group(0)
        if ent and ent.split()[0] not in head: warns.append(f"{k}: heading does not show entity name '{ent}'")
    if fix: open(p, "w", encoding="utf-8").write(text)
    # global rules
    common = len(re.findall(r"\*\*Error Register \(most common\):\*\*", text))
    if not 4 <= common <= 14: errs.append(f"Most Common Errors page needs 4 to 14 flagged points, found {common}")
    for m in re.finditer(r"\bp\.?\s?\d{1,2}\.\d{1,3}\b", text): errs.append(f"page number found ({m.group(0)}): the book carries no page numbers")
    for m in re.finditer(r"\[verify[^\]]*\]", text): warns.append(f"unresolved {m.group(0)}")
    for w in ("TODO", "TBD", "claude-", "sonnet", "opus", "haiku"):
        if re.search(w, text, re.I) and not (w in ("sonnet", "opus", "haiku") and False): errs.append(f"forbidden or placeholder text: {w}")
    print(f"{unit}: {len(cards)} cards, {len(mcq_rows)} MCQ rows, {common} most-common error points")
    for w in warns: print("  WARN ", w)
    for e in errs: print("  ERROR", e)
    print("RESULT:", "PASS" if not errs else f"FAIL ({len(errs)} errors)")
    return not errs


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    cmd, unit = a[0], a[1]
    if cmd == "refs": build_refs(unit)
    elif cmd == "chips": chips(unit, "--write" in a)
    elif cmd == "validate": sys.exit(0 if validate(unit, "--fix-difficulty" in a) else 1)
    else: sys.exit(__doc__)
