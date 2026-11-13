#!/usr/bin/env python3
"""
drive_notes_inventory.py - deterministic inventory of Pranav's public Google Drive PDFs.

WHAT IT DOES
  For each of two PUBLIC ("anyone with the link") Drive folders it lists the files, downloads each PDF
  one at a time to a temporary folder, records size, SHA-256, page count, page size and how much text
  the PDF carries (a scanned handwritten notebook has none), then DELETES the download. Only the
  statistics are written to the repo; no PDF is ever committed (repo rule: no binaries in git).

WHY
  The concept book needs to know, per unit, which handwritten notes and which annotated ICAI chapters
  exist, how many pages each has, and what is missing. Anyone (a person or any AI model) can re-run this
  to get the same table, and a PDF whose checksum changed shows up as changed.

OUTPUT (default folder: books/ca-inter/concept-book/sources/)
  handwritten-notes-inventory.csv   one row per Drive file
  handwritten-notes-by-unit.md      one row per syllabus unit: what exists, pages, what is missing

USAGE
  python tools/drive_notes_inventory.py                # run everything
  python tools/drive_notes_inventory.py --list-only    # list the folders, download nothing
  python tools/drive_notes_inventory.py --summary-only # rebuild the markdown from the CSV

Downloaded PDFs are untrusted input: they are only parsed with pypdf, never opened or executed. Run this
script with `python -I` if you want the interpreter isolated from the current directory.
"""
import argparse, csv, hashlib, html, json, os, re, shutil, sys, tempfile, time, urllib.request

CLASS_NOTES = "1fHgz8ktYI8_kF5oQaUKVHcP43KE9bTNb"      # class annotated notes (NB01 / NB02 and others)
ICAI_ANNOTATED = "1xmSOYMmtv8HehJNOwtQ6_WYO2WIKlHxH"   # teacher-annotated ICAI study material
FOLDERS = (("class_notes", CLASS_NOTES), ("icai_annotated", ICAI_ANNOTATED))

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_DIR = os.path.join(REPO, "books", "ca-inter", "concept-book", "sources")
INDEX = os.path.join(REPO, "books", "ca-inter", "concept-book", "syllabus-engine", "data",
                     "1-ca-inter-adv-accounts-topic-page-index.json")
SEQ = os.path.join(REPO, "books", "ca-inter", "concept-book", "BOOK-SEQUENCE.csv")
UA = {"User-Agent": "Mozilla/5.0"}

# keyword (matched case-insensitively against the file name) -> unit id. First match wins; a file may
# map to more than one unit (Ch 13 and AS 14 share one notebook).
KEYWORDS = [
    (r"AS\s*0?2\b|inventor", ["M2-C5-U1"]), (r"AS\s*10\b|property plant", ["M2-C5-U2"]),
    (r"AS\s*26|intangible", ["M2-C5-U6"]), (r"AS\s*16|borrowing", ["M2-C5-U4"]),
    (r"AS\s*19|leases", ["M2-C5-U5"]), (r"AS\s*28|impairment", ["M2-C5-U7"]),
    (r"AS\s*13\b|accounting for investments", ["M2-C5-U3"]), (r"AS\s*29|provisions", ["M2-C6-U2"]),
    (r"AS\s*15|employee", ["M2-C6-U1"]), (r"AS\s*4\b|events after", ["M2-C7-U1"]),
    (r"AS\s*5\b|prior period", ["M2-C7-U2"]), (r"AS\s*11\b|forex|foreign exchange", ["M2-C7-U3"]),
    (r"AS\s*9\b|revenue recognition", ["M2-C8-U2"]), (r"AS\s*0?7\b|construction", ["M2-C8-U1"]),
    (r"AS\s*12\b|government grants", ["M2-C9-U1"]), (r"AS\s*22|taxes on income", ["M2-C7-U4"]),
    (r"AS\s*20|earnings per share", ["M1-C4-U5"]), (r"AS\s*1\b|disclosure of accounting policies", ["M1-C4-U1"]),
    (r"AS\s*3\b", ["M1-C4-U2"]), (r"AS\s*17|segment", ["M1-C4-U3"]), (r"AS\s*18|related party", ["M1-C4-U4"]),
    (r"AS\s*24|discontinuing", ["M1-C4-U6"]), (r"AS\s*25|interim", ["M1-C4-U7"]),
    (r"Ch\s*11\s*Unit\s*2|ch 11 u2", ["M3-C11-U2"]),
    (r"Ch\s*11|divisible|financial statements", ["M3-C11-U1"]),
    (r"Ch\s*12|buy\s*-?back", ["M3-C12-U0"]),
    (r"Ch\s*13.*AS\s*14|AS\s*14.*Ch\s*13", ["M3-C13-U0", "M2-C9-U2"]),
    (r"Ch\s*13|amalgamation of companies", ["M3-C13-U0"]), (r"AS\s*14", ["M2-C9-U2"]),
    (r"Ch\s*14|reconstruction|reconctruction", ["M3-C14-U0"]), (r"Ch\s*15|branch", ["M3-C15-U0"]),
    (r"AS\s*21|consolidat", ["M2-C10-U1"]), (r"AS\s*23|associates", ["M2-C10-U2"]),
    (r"AS\s*27|joint ventures", ["M2-C10-U3"]),
    (r"framework|Ch\s*3\b", ["M1-C2-U0"]), (r"applicability", ["M1-C3-U0"]),
    (r"introduction to accounting standards|initial pages", ["M1-C1-U0"]),
]
SINGLE_UNIT_CHAPTERS = {(1, 1), (1, 2), (1, 3), (3, 12), (3, 13), (3, 14), (3, 15)}


def http(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)


def list_folder(folder_id):
    page = http(f"https://drive.google.com/embeddedfolderview?id={folder_id}").read().decode("utf-8", "replace")
    items = re.findall(r'<div class="flip-entry" id="entry-([A-Za-z0-9_-]+)".*?<div class="flip-entry-title">(.*?)</div>', page, re.S)
    return [(i, html.unescape(re.sub(r"<[^>]+>", "", n)).strip()) for i, n in items]


def classify(name):
    n = name.lower()
    m = re.search(r"nb\s*-?\s*0?(1|2)", n)
    if m: return "NB0" + m.group(1)
    if "rough" in n: return "rough"
    if "slide" in n: return "slides"
    if "revision" in n or "descriptive notes" in n: return "revision-notes"
    if "concept" in n: return "concept"
    return "other"


def units_for(name):
    m = re.match(r"M(\d)_C(\d+)_U(\d)", name)
    if m:
        mod, ch, u = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if (mod, ch) in SINGLE_UNIT_CHAPTERS: u = 0
        return [f"M{mod}-C{ch}-U{u}"]
    for pat, units in KEYWORDS:
        if re.search(pat, name, re.I): return units
    return []


def download(file_id, dest):
    url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
    h = hashlib.sha256(); size = 0
    with http(url, timeout=120) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk: break
            f.write(chunk); h.update(chunk); size += len(chunk)
    return size, h.hexdigest()


def pdf_stats(path):
    from pypdf import PdfReader
    r = PdfReader(path)
    n = len(r.pages)
    w = h = None
    if n:
        box = r.pages[0].mediabox; w, h = round(float(box.width)), round(float(box.height))
    text = 0
    for p in r.pages[:3]:
        try: text += len((p.extract_text() or "").strip())
        except Exception: pass
    return n, w, h, text


def run(list_only):
    os.makedirs(OUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUT_DIR, "handwritten-notes-inventory.csv")
    cols = ["folder", "file_name", "drive_id", "kind", "unit_ids", "size_bytes", "sha256", "pages",
            "page_w_pt", "page_h_pt", "text_chars_first3", "status"]
    rows = []
    tmp = tempfile.mkdtemp(prefix="drive_inv_")
    try:
        for label, fid in FOLDERS:
            entries = list_folder(fid)
            print(f"{label}: {len(entries)} entries listed", flush=True)
            for i, (file_id, name) in enumerate(entries, 1):
                row = dict(folder=label, file_name=name, drive_id=file_id, kind=classify(name),
                           unit_ids=";".join(units_for(name)), size_bytes="", sha256="", pages="",
                           page_w_pt="", page_h_pt="", text_chars_first3="", status="listed")
                if not list_only and name.lower().endswith(".pdf") or (not list_only and "." not in name):
                    dest = os.path.join(tmp, "x.pdf")
                    try:
                        size, sha = download(file_id, dest)
                        row.update(size_bytes=size, sha256=sha)
                        n, w, h, text = pdf_stats(dest)
                        row.update(pages=n, page_w_pt=w, page_h_pt=h, text_chars_first3=text, status="ok")
                    except Exception as e:
                        row["status"] = "error: " + str(e)[:120]
                    finally:
                        if os.path.exists(dest): os.remove(dest)
                elif not list_only:
                    row["status"] = "skipped (not a PDF)"
                rows.append(row)
                print(f"  [{label} {i}/{len(entries)}] {name[:60]} -> {row['status']} {row['pages']}p", flush=True)
                time.sleep(0.2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print("wrote", csv_path)


def summary():
    csv_path = os.path.join(OUT_DIR, "handwritten-notes-inventory.csv")
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    idx = {c["unique_chapter_id"]: c for c in json.load(open(INDEX, encoding="utf-8"))["chapters"]}
    order = []
    for r in csv.DictReader(open(SEQ, encoding="utf-8")):
        if r["unit_id"] not in [o[0] for o in order]: order.append((r["unit_id"], r["unit"]))

    def cell(unit, folder, kind):
        hits = [r for r in rows if r["folder"] == folder and unit in r["unit_ids"].split(";") and r["kind"] == kind]
        if not hits: return "missing"
        return "; ".join(f"{r['pages'] or '?'} p / {int(r['size_bytes'] or 0)/1e6:.1f} MB" for r in hits)

    lines = ["# Handwritten notes and annotated ICAI: what exists, by unit\n",
             "_Generated by `tools/drive_notes_inventory.py` from the two public Drive folders. Do not edit by hand; re-run the script. "
             "Pages and sizes are measured, not estimated. \"missing\" means no file in the folder matched the unit (check the "
             "unmapped list below before concluding it does not exist)._\n",
             "| # | Unit | Unit ID | NB01 | NB02 | Other class notes | ICAI annotated |", "|---|---|---|---|---|---|---|"]
    for i, (uid, uname) in enumerate(order, 1):
        other = [r for r in rows if r["folder"] == "class_notes" and uid in r["unit_ids"].split(";") and r["kind"] not in ("NB01", "NB02")]
        o = "; ".join(f"{r['kind']}: {r['pages'] or '?'} p" for r in other) or "-"
        ica = [r for r in rows if r["folder"] == "icai_annotated" and uid in r["unit_ids"].split(";")]
        a = "; ".join(f"{r['pages'] or '?'} p / {int(r['size_bytes'] or 0)/1e6:.1f} MB" for r in ica) or "missing"
        lines.append(f"| {i} | {uname} | `{uid}` | {cell(uid,'class_notes','NB01')} | {cell(uid,'class_notes','NB02')} | {o} | {a} |")
    un = [r for r in rows if not r["unit_ids"]]
    lines += ["", "## Files not matched to any unit (check these)", ""]
    lines += [f"- {r['folder']}: `{r['file_name']}` ({r['pages'] or '?'} p)" for r in un] or ["- none"]
    scanned = [r for r in rows if r["status"] == "ok" and int(r["text_chars_first3"] or 0) < 50]
    lines += ["", f"## Text layer", "", f"{len(scanned)} of {sum(1 for r in rows if r['status']=='ok')} downloaded PDFs have (almost) no text in their first three pages, i.e. they are scans needing OCR/vision reading."]
    bad = [r for r in rows if r["status"].startswith("error")]
    if bad: lines += ["", "## Download errors", ""] + [f"- `{r['file_name']}`: {r['status']}" for r in bad]
    open(os.path.join(OUT_DIR, "handwritten-notes-by-unit.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote summary")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-only", action="store_true"); ap.add_argument("--summary-only", action="store_true")
    a = ap.parse_args()
    if not a.summary_only: run(a.list_only)
    summary()
