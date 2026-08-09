"""
Stage 1 of the CS/CMA ToC-extraction pipeline: parse each consolidated
subject PDF's own printed Table of Contents into (chapter, printed page
range) records, then work out which actual PDF page each printed page
number corresponds to, and verify every chapter's computed PDF start
page really does open with that chapter's title.

Unlike ICAI's per-chapter PDFs (see the Study Hub pipeline), CS and CMA
ship one consolidated PDF per subject with no per-chapter split and no
usable embedded bookmarks (checked: 47 of 50 have zero PDF outline
entries). So chapter boundaries have to be derived from each PDF's own
printed ToC, and "printed page N" has to be reverse-engineered to "PDF
page M" by content-matching, not assumed.

Two publisher formats, both handled here (see cs_cma_common.py / the
skill doc for detail):
  - ICMAI (CMA Final/Foundation/Intermediate): "Contents as per Syllabus"
    page(s) give explicit printed page RANGES per Module and Section --
    no inference needed for chapter end pages.
  - ICSI (CS Executive/Professional/CSEET): "CONTENTS" section gives each
    LESSON's first printed page only; a lesson's end = the next lesson's
    start - 1 (or a "TEST PAPERS" sentinel / end-of-book for the last one).

Read-only against telegram/assets/<folder>/*.pdf. Writes a report to
telegram/tools/_reports/cs_cma_toc_scan.json for review -- this is Stage
1 output; Stage 2 (build_cs_cma_catalog.py) turns it into the Excel
catalog.

Run: python telegram/tools/scan_cs_cma_toc.py
"""

import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader
from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cs_cma_common import ASSETS_ROOT, all_source_files, get_file_meta, normalize_ws, publisher_of

REPORT_DIR = Path(__file__).resolve().parent / "_reports"
REPORT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# ICMAI parser -- "Contents as per Syllabus"
# ---------------------------------------------------------------------------
NUM = r"\d(?:\s?\d){0,3}"  # 1-4 digits, tolerating a single stray embedded
                            # space (a real OCR/font-kerning artifact seen in
                            # these PDFs) without over-matching adjacent
                            # unrelated numbers (e.g. a cited Act's year).
ICMAI_SECTION_RE = re.compile(
    rf"^SECTION[\s\-]*([A-Z0-9]+)\s*[:\-–]\s*(.+?)\s+({NUM})\s*[-–]\s*({NUM})\s*$",
    re.IGNORECASE,
)
ICMAI_MODULE_RE = re.compile(
    # "Module N. Title" is the common style, but at least one file uses
    # "Module N : Title" (colon) -- accept either separator, or none.
    rf"^Module\.?\s+(\d+)\s*[.:]?\s*(.+?)\s+({NUM})\s*[-–]\s*({NUM})\s*$",
    re.IGNORECASE,
)


def _clean_num(s: str) -> int:
    return int(re.sub(r"\s+", "", s))


def parse_icmai_toc(pages_text):
    """Returns (sections, modules) -- modules is the chapter-equivalent list."""
    sections, modules = [], []
    for text in pages_text:
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            m = ICMAI_MODULE_RE.match(line)
            if m:
                modules.append({
                    "number": int(m.group(1)),
                    "title": normalize_ws(m.group(2)),
                    "printed_start": _clean_num(m.group(3)),
                    "printed_end": _clean_num(m.group(4)),
                })
                continue
            m = ICMAI_SECTION_RE.match(line)
            if m:
                sections.append({
                    "label": m.group(1),
                    "title": normalize_ws(m.group(2)),
                    "printed_start": _clean_num(m.group(3)),
                    "printed_end": _clean_num(m.group(4)),
                })
    return sections, modules


SECTION_HDR_ONLY_RE = re.compile(r"^SECTION[\s\-]*([A-Z0-9]+)\s*[:\-–]\s*(.+?)\s*$", re.IGNORECASE)
MODULE_HDR_ONLY_RE = re.compile(r"^Module\.?\s+(\d+)\s*[.:]?\s*(.+?)\s*$", re.IGNORECASE)
RANGE_ONLY_RE = re.compile(rf"^({NUM})\s*[-–]\s*({NUM})\s*$")


def parse_icmai_toc_grouped_ranges(pages_text):
    """Fallback for a handful of ICMAI files where pypdf extracts the ToC
    table column-by-column instead of row-by-row: every Section/Module
    heading line on a page (no trailing page range) is followed by ALL of
    that page's page-range values dumped together at the end, in the same
    order the headings appeared. Only used when the normal inline-range
    parser finds zero modules -- see SKILL-cs-cma-toc-pipeline.md §3."""
    headings = []  # list of ('section'|'module', number_or_label, title)
    ranges = []    # list of (start, end)
    for text in pages_text:
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            rm = RANGE_ONLY_RE.match(line)
            if rm:
                ranges.append((_clean_num(rm.group(1)), _clean_num(rm.group(2))))
                continue
            mm = MODULE_HDR_ONLY_RE.match(line)
            if mm:
                headings.append(("module", mm.group(1), normalize_ws(mm.group(2))))
                continue
            sm = SECTION_HDR_ONLY_RE.match(line)
            if sm:
                headings.append(("section", sm.group(1), normalize_ws(sm.group(2))))
                continue

    sections, modules = [], []
    for (kind, num_or_label, title), rng in zip(headings, ranges):
        entry = {"title": title, "printed_start": rng[0], "printed_end": rng[1]}
        if kind == "module":
            entry["number"] = int(num_or_label)
            modules.append(entry)
        else:
            entry["label"] = num_or_label
            sections.append(entry)
    return sections, modules, len(headings) == len(ranges)


def find_icmai_toc_pages(reader):
    start = None
    for i in range(min(20, len(reader.pages))):
        t = reader.pages[i].extract_text() or ""
        if "Contents as per Syllabus" in t:
            start = i
            break
    if start is None:
        return None
    pages = []
    stall = 0
    i = start
    while i < len(reader.pages) and i < start + 15:
        t = reader.pages[i].extract_text() or ""
        _, mods = parse_icmai_toc([t])
        # also recognize the "grouped ranges" layout (see
        # parse_icmai_toc_grouped_ranges) as still-in-the-ToC, since its
        # heading lines carry no inline page range for parse_icmai_toc to
        # find. Per-line match, not .search() on the whole page -- ^/$
        # without re.MULTILINE only anchor to the whole string.
        has_heading_only = any(
            MODULE_HDR_ONLY_RE.match(ln.strip()) or SECTION_HDR_ONLY_RE.match(ln.strip())
            for ln in t.split("\n") if ln.strip()
        )
        pages.append(i)
        if mods or has_heading_only:
            stall = 0
        else:
            stall += 1
            if stall >= 2 and len(pages) > 1:
                pages.pop()
                break
        i += 1
    return pages


# ---------------------------------------------------------------------------
# ICSI parser -- "CONTENTS" section, LESSON N headers
# ---------------------------------------------------------------------------
LESSON_HDR_RE = re.compile(r"^LESSON\s+(\d+)\s*$", re.IGNORECASE)
SUBSECTION_RE = re.compile(r"^SECTION\s+[IVXLCM]+\s*:", re.IGNORECASE)
PAGENUM_TRAIL_RE = re.compile(r"^(.*\S)\s+(\d{1,4})\s*$")
ARRANGEMENT_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
TEST_PAPERS_RE = re.compile(r"^TEST\s+PAPERS\s+(\d{1,4})\s*$", re.IGNORECASE)


def parse_arrangement(pages_text):
    items, in_block = [], False
    for text in pages_text:
        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if "ARRANGEMENT OF STUDY LESSONS" in line.upper():
                in_block = True
                continue
            if in_block:
                m = ARRANGEMENT_ITEM_RE.match(line)
                if m:
                    items.append((int(m.group(1)), normalize_ws(m.group(2))))
                elif line.upper().startswith("LESSON WISE SUMMARY") or line.upper().startswith("CONTENTS"):
                    in_block = False
    return items


def find_icsi_contents_start(reader):
    arrangement_pages = []
    for i in range(min(25, len(reader.pages))):
        t = reader.pages[i].extract_text() or ""
        if re.search(r"ARRANGEMENT OF STUDY LESSONS", t, re.IGNORECASE):
            arrangement_pages.append(i)
        if re.search(r"^\s*CONTENTS\s*$", t, re.MULTILINE):
            if not arrangement_pages:
                arrangement_pages.append(max(0, i - 1))
            return i, arrangement_pages
    return None, arrangement_pages


def find_icsi_toc_window(reader, contents_start, target):
    toc_pages = []
    seen = set()
    stall = 0
    i = contents_start
    while i < len(reader.pages) and i < contents_start + 90:
        t = reader.pages[i].extract_text() or ""
        # per-line match (not .findall on the whole page) -- ^/$ without
        # re.MULTILINE only anchor to the whole string, not each line.
        nums_here = {int(m.group(1)) for raw in t.split("\n") if (m := LESSON_HDR_RE.match(raw.strip()))}
        new_nums = nums_here - seen
        toc_pages.append(i)
        if new_nums:
            seen |= new_nums
            stall = 0
        else:
            stall += 1
        if target and seen >= set(range(1, target + 1)):
            if i + 1 < len(reader.pages):
                toc_pages.append(i + 1)
            break
        if stall >= 15 and seen:
            # a content-heavy lesson's detailed subtopic list can span many
            # ToC pages with no new "LESSON N" header in between -- don't
            # bail out early just because of a long stretch of those.
            break
        i += 1
    return toc_pages


def parse_icsi_toc(pages_text, target=None):
    lessons = []
    current = None
    expect_title = False
    seen_numbers = set()
    test_papers_start = None
    for text in pages_text:
        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            tm = TEST_PAPERS_RE.match(line)
            if tm:
                test_papers_start = int(tm.group(1))
                continue
            hm = LESSON_HDR_RE.match(line)
            if hm:
                num = int(hm.group(1))
                if num in seen_numbers:
                    continue  # body-content bleed-through past the real ToC
                current = {"number": num, "title": None, "printed_start": None}
                lessons.append(current)
                seen_numbers.add(num)
                expect_title = True
                continue
            if expect_title and current is not None:
                current["title"] = normalize_ws(line)
                expect_title = False
                continue
            if current is not None and current["printed_start"] is None:
                if SUBSECTION_RE.match(line):
                    continue
                pm = PAGENUM_TRAIL_RE.match(line)
                if pm:
                    if pm.group(1).rstrip().endswith(","):
                        continue
                    current["printed_start"] = int(pm.group(2))
            if target and len(lessons) >= target and all(l["printed_start"] is not None for l in lessons):
                return lessons, test_papers_start
    return lessons, test_papers_start


def icsi_chapters_with_end(lessons, test_papers_start, total_pdf_pages, offset_guess):
    """Fill in printed_end for each lesson: next lesson's start - 1, or the
    TEST PAPERS sentinel - 1 for the last one, or an offset-adjusted
    estimate of the book's last printed page if neither is available.
    A lesson whose own printed_start couldn't be parsed (rare -- e.g. an
    unusual sub-heading right after its title that neither regex handles)
    gets printed_end=None and is left for scan_file() to flag rather than
    guessed at here."""
    chapters = []
    for idx, l in enumerate(lessons):
        start = l["printed_start"]
        end = None
        if start is not None:
            next_start = lessons[idx + 1]["printed_start"] if idx + 1 < len(lessons) else None
            if next_start is not None:
                end = next_start - 1
            elif test_papers_start:
                end = test_papers_start - 1
            else:
                end = total_pdf_pages - offset_guess  # best-effort fallback
        chapters.append({
            "number": l["number"],
            "title": l["title"],
            "printed_start": start,
            "printed_end": end,
        })
    return chapters


# ---------------------------------------------------------------------------
# Offset detection: which PDF page is "printed page 1"?
# ---------------------------------------------------------------------------
def page_text(reader, idx, chars=350):
    if idx < 0 or idx >= len(reader.pages):
        return ""
    return (reader.pages[idx].extract_text() or "")[:chars]


def title_match_score(title, text):
    return fuzz.partial_ratio(title.lower(), (text or "").lower())


def find_offset_for_chapter(reader, title, printed_start, search_from, search_to, threshold=78):
    """Search pdf pages [search_from, search_to) for one whose text opens
    with `title`. Returns (pdf_idx, score) of the best match, or (None, 0)."""
    best_idx, best_score = None, 0
    for idx in range(max(0, search_from), min(len(reader.pages), search_to)):
        score = title_match_score(title, page_text(reader, idx))
        if score > best_score:
            best_score, best_idx = score, idx
            if best_score >= 95:  # confident enough, stop scanning the rest of the window
                break
    if best_score >= threshold:
        return best_idx, best_score
    return None, best_score


def detect_offset(reader, chapters, toc_end_page):
    """Try first / middle / last chapter to find a consistent
    pdf_idx - printed_start offset. Returns (offset, confidence_notes)."""
    if not chapters:
        return None, ["no chapters to anchor on"]

    usable = [i for i, ch in enumerate(chapters) if ch.get("printed_start") is not None]
    if not usable:
        return None, ["no chapter has a parsed printed_start to anchor on"]
    candidates_idx = sorted({usable[0], usable[len(usable) // 2], usable[-1]})
    found_offsets = []
    notes = []
    for ci in candidates_idx:
        ch = chapters[ci]
        idx, score = find_offset_for_chapter(
            reader, ch["title"], ch["printed_start"],
            search_from=toc_end_page, search_to=min(len(reader.pages), toc_end_page + 60),
        )
        if idx is not None:
            offset = idx - ch["printed_start"]
            found_offsets.append(offset)
            notes.append(f"ch{ch['number']} '{ch['title'][:40]}' -> pdf_idx={idx} score={score:.0f} offset={offset}")
        else:
            notes.append(f"ch{ch['number']} '{ch['title'][:40]}' -> NOT FOUND (best score={score:.0f})")

    if not found_offsets:
        return None, notes
    # majority offset
    from collections import Counter
    offset, count = Counter(found_offsets).most_common(1)[0]
    if count < len(found_offsets):
        notes.append(f"INCONSISTENT offsets found: {found_offsets} -- using majority {offset}")
    return offset, notes


# ---------------------------------------------------------------------------
# Main per-file pipeline
# ---------------------------------------------------------------------------
def scan_file(folder, pdf_path):
    meta = get_file_meta(folder, pdf_path.name)
    reader = PdfReader(str(pdf_path))
    n_pages = len(reader.pages)
    publisher = publisher_of(folder)

    record = {
        "folder": folder,
        "filename": pdf_path.name,
        "n_pdf_pages": n_pages,
        "publisher": publisher,
        **meta,
        "sections": [],
        "chapters": [],
        "offset": None,
        "offset_notes": [],
        "toc_pages": [],
        "issues": [],
    }

    if publisher == "icmai":
        toc_pages = find_icmai_toc_pages(reader)
        if not toc_pages:
            record["issues"].append("ICMAI ToC ('Contents as per Syllabus') not found in first 20 pages")
            return record
        record["toc_pages"] = toc_pages
        full_text = [reader.pages[i].extract_text() or "" for i in toc_pages]
        sections, modules = parse_icmai_toc(full_text)
        if not modules:
            # fallback: this file's ToC table extracted column-by-column
            # (all headings, then all page ranges dumped together) instead
            # of row-by-row -- see parse_icmai_toc_grouped_ranges.
            g_sections, g_modules, clean_pairing = parse_icmai_toc_grouped_ranges(full_text)
            if g_modules:
                sections, modules = g_sections, g_modules
                record["used_grouped_ranges_fallback"] = True
                if not clean_pairing:
                    record["issues"].append("grouped-ranges fallback: heading count != range count, pairing may be off")
        record["sections"] = sections
        record["chapters"] = [
            {"number": m["number"], "title": m["title"], "printed_start": m["printed_start"], "printed_end": m["printed_end"]}
            for m in modules
        ]
        toc_end = toc_pages[-1] + 1
    else:
        contents_start, arrangement_pages = find_icsi_contents_start(reader)
        if contents_start is None:
            record["issues"].append("ICSI 'CONTENTS' section not found in first 25 pages")
            return record
        arrangement = parse_arrangement([reader.pages[i].extract_text() or "" for i in arrangement_pages])
        target = len(arrangement) if arrangement else None
        toc_pages = find_icsi_toc_window(reader, contents_start, target)
        record["toc_pages"] = toc_pages
        full_text = [reader.pages[i].extract_text() or "" for i in toc_pages]
        lessons, test_papers_start = parse_icsi_toc(full_text, target)
        if target and len(lessons) != target:
            record["issues"].append(f"expected {target} lessons per 'ARRANGEMENT OF STUDY LESSONS', parsed {len(lessons)}")
        chapters = icsi_chapters_with_end(lessons, test_papers_start, n_pages, offset_guess=8)
        record["chapters"] = chapters
        record["test_papers_printed_start"] = test_papers_start
        toc_end = toc_pages[-1] + 1

    if not record["chapters"]:
        record["issues"].append("zero chapters parsed")
        return record

    offset, notes = detect_offset(reader, record["chapters"], toc_end)
    record["offset"] = offset
    record["offset_notes"] = notes
    if offset is None:
        record["issues"].append("could not determine printed-page -> pdf-page offset")
        return record

    # compute + verify every chapter's pdf page range
    for ch in record["chapters"]:
        if ch.get("printed_start") is None or ch.get("printed_end") is None:
            ch["needs_review"] = True
            ch["verify_score"] = 0.0
            record["issues"].append(f"ch{ch['number']} '{ch['title'][:40]}' has no printed page range parsed")
            continue
        ch["pdf_start"] = ch["printed_start"] + offset
        ch["pdf_end"] = min(ch["printed_end"] + offset, n_pages - 1)
        score = title_match_score(ch["title"], page_text(reader, ch["pdf_start"]))
        if score < 70:
            # local search +/- 3 pages in case of a divider/blank page shift
            best_idx, best_score = find_offset_for_chapter(
                reader, ch["title"], 0, ch["pdf_start"] - 3, ch["pdf_start"] + 4, threshold=70
            )
            if best_idx is not None:
                shift = best_idx - ch["pdf_start"]
                ch["pdf_start"] += shift
                ch["pdf_end"] = max(ch["pdf_end"], ch["pdf_start"])
                score = best_score
                ch["local_shift"] = shift
        ch["verify_score"] = round(score, 1)
        if score < 70:
            ch["needs_review"] = True

    return record


def main():
    results = []
    for folder, pdf_path in all_source_files():
        print(f"Scanning {folder}/{pdf_path.name} ...")
        try:
            rec = scan_file(folder, pdf_path)
        except Exception as e:
            print(f"  !! CRASHED: {e!r} -- recorded as a hard issue, continuing with the rest of the batch")
            meta = get_file_meta(folder, pdf_path.name)
            rec = {
                "folder": folder, "filename": pdf_path.name, "publisher": publisher_of(folder),
                **meta, "sections": [], "chapters": [], "offset": None, "offset_notes": [],
                "toc_pages": [], "issues": [f"CRASHED: {e!r}"],
            }
        results.append(rec)

    out_path = REPORT_DIR / "cs_cma_toc_scan.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    total_chapters = sum(len(r["chapters"]) for r in results)
    needs_review = [
        (r["folder"], r["filename"], ch["number"], ch["title"], ch.get("verify_score"))
        for r in results for ch in r["chapters"] if ch.get("needs_review")
    ]
    hard_issues = [(r["folder"], r["filename"], r["issues"]) for r in results if r["issues"]]

    print(f"\n{len(results)} files scanned, {total_chapters} chapters parsed total.")
    print(f"Chapters needing manual review (verify_score < 70): {len(needs_review)}")
    for f, fn, num, title, score in needs_review:
        print(f"  [{score}] {f}/{fn} ch{num} {title!r}")
    print(f"\nFiles with hard issues (ToC not found / zero chapters / no offset): {len(hard_issues)}")
    for f, fn, issues in hard_issues:
        print(f"  {f}/{fn}: {issues}")

    print(f"\nFull report: {out_path}")


if __name__ == "__main__":
    main()
