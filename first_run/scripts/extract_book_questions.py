"""
QA extraction: final QUESTION-BANK-BOOK.html -> JSON.

Companion to extract_questions.py, but for the OTHER end of the pipeline.
extract_questions.py reads Layer 1 (per-sitting HTML, still carrying clean
data-* attributes) and produces questions_index.json (Layer 2). This script
reads the finished, MERGED book (first_run/output/QUESTION-BANK-BOOK.html --
the actual published deliverable, after generate_chapter_book.py has already
stripped MCQs, baked marks/topic/approx-time into display text, and qb_merge.py
has stitched all 34 chapters + front/back matter + ToC + coverage matrix into
one file) and extracts every rendered .qblock back into JSON.

Purpose: NOT a replacement data source for questions_index.json -- this is a
round-trip QA tool. Pair it with diff_book_vs_index.py, which regenerates the
expected HTML for every questions_index.json row via
generate_chapter_book.render_qblock() and compares it field-by-field against
what this script actually found in the merged book, to catch drift (a stale
regeneration, a silently dropped question, a hand-edit that never made it back
to the source data) between "what the data says should be in the book" and
"what actually got printed."

The final book's qblocks carry NO data-* attributes (unlike Layer 1) -- every
field is baked into rendered display text by generate_chapter_book.render_qblock().
So this is unavoidably light HTML-structure parsing, not attribute reading.
parse_qblock() is factored out specifically so diff_book_vs_index.py can run
the exact same parsing logic against freshly-regenerated qblock HTML, instead
of re-deriving a second, possibly-drifting notion of "what a qblock's fields
look like."

Usage:  python extract_book_questions.py
Output: first_run/output/qa/book_questions_extracted.json
"""
import json
import os
import re
import sys
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.normpath(os.path.join(HERE, "..", "output"))
BOOK_PATH = os.path.join(OUTPUT_DIR, "QUESTION-BANK-BOOK.html")
QA_DIR = os.path.join(OUTPUT_DIR, "qa")
EXTRACTED_PATH = os.path.join(QA_DIR, "book_questions_extracted.json")

sys.path.insert(0, HERE)
from qb_merge import CHAPTERS  # noqa: E402  (slug, filename, chapter_label, study_ref)

_SECTION_ROLE_RE = re.compile(r"^\s*(I|II)\.\s")


def _text(tag):
    return tag.get_text(strip=True) if tag is not None else None


def _first_inner_div_html(wrapper):
    """wrapper is e.g. <div class="question"><strong>Question:</strong>
    <div>...content...</div></div> or the answer-block equivalent (with an
    optional <p><em>Correct option...</em></p> in between for the rare
    non-MCQ row that still carries an answer_letter). The content lives in
    the first nested <div> -- BeautifulSoup's document-order traversal
    returns that wrapper div itself before any of ITS children, so a plain
    .find("div") is safe here, not a risk of grabbing a deeper descendant."""
    inner = wrapper.find("div") if wrapper is not None else None
    if inner is None:
        return ""
    return inner.decode_contents().strip()


def parse_qblock(qblock):
    """Extract one rendered .qblock <div> into a plain dict. Shared by this
    script (parsing the real merged book) and diff_book_vs_index.py (parsing
    freshly-regenerated qblock HTML for comparison) -- keep this the single
    place that knows the qblock markup shape."""
    classes = qblock.get("class") or []
    qmeta = qblock.find("div", class_="qmeta")
    marks_spans = qmeta.find_all("span", class_="marks") if qmeta else []
    badges = qmeta.find_all("span", class_="badge") if qmeta else []

    question_wrap = qblock.find("div", class_="question")
    answer_wrap = qblock.find("div", class_="answer-block")

    answer_letter = None
    if answer_wrap is not None:
        m = re.search(r"Correct option:\s*([A-Za-z0-9]+)", answer_wrap.get_text())
        if m:
            answer_letter = m.group(1)

    mistakes_div = qblock.find("div", class_=re.compile(r"\bmistakes\b"))
    mistake_type = None
    if mistakes_div is not None:
        m_classes = mistakes_div.get("class") or []
        if "icai" in m_classes:
            mistake_type = "icai"
        elif "synth" in m_classes:
            mistake_type = "synth"

    return {
        "book_id": qblock.get("id"),
        "flagged": "flagged" in classes,
        "src_text": _text(qmeta.find("span", class_="src")) if qmeta else None,
        "qno_text": _text(qmeta.find("span", class_="qno")) if qmeta else None,
        "marks_text": _text(marks_spans[0]) if len(marks_spans) > 0 else None,
        "approx_time_text": _text(marks_spans[1]) if len(marks_spans) > 1 else None,
        "topic_text": _text(qmeta.find("span", class_="topic")) if qmeta else None,
        "badges": [b.get_text(strip=True) for b in badges],
        "question_html": _first_inner_div_html(question_wrap),
        "answer_html": _first_inner_div_html(answer_wrap),
        "answer_letter": answer_letter,
        "mistake_type": mistake_type,
        "mistake_text": _mistake_text(mistakes_div),
    }


def _mistake_text(mistakes_div):
    """get_text(strip=True) with no separator glues the <strong>Author's
    Note:</strong> label straight onto the following text node with no space
    ("Note:A common error...") -- separator=" " fixes that at every tag
    boundary; the whitespace collapse afterward absorbs the extra spaces that
    introduces elsewhere (e.g. around nested inline tags)."""
    if mistakes_div is None:
        return None
    return re.sub(r"\s+", " ", mistakes_div.get_text(separator=" ", strip=True)).strip()


def extract_chapter_section(section_tag, slug, chapter_label, study_ref):
    """Walk one <div class="qb-section" id="{slug}">'s content in document
    order, tracking which of the two <h2> subsections ("I. Descriptive..." /
    "II. Integrated...") each .qblock falls under."""
    study_ref_tag = section_tag.find("div", class_="qb-study-ref")
    study_ref_seen = None
    if study_ref_tag is not None:
        strong = study_ref_tag.find("strong")
        study_ref_seen = _text(strong)
    if study_ref_seen and study_ref_seen != study_ref:
        print(f"  WARNING [{slug}]: qb-study-ref shows '{study_ref_seen}', "
              f"expected '{study_ref}' (CHAPTERS table drifted from the book?)")

    role = "descriptive"  # a section with no MCQs-excluded Section II heading defaults here
    rows = []
    for tag in section_tag.find_all(lambda t: t.name == "h2" or (
            t.name == "div" and "qblock" in (t.get("class") or []))):
        if tag.name == "h2":
            m = _SECTION_ROLE_RE.match(tag.get_text())
            if m:
                role = "descriptive" if m.group(1) == "I" else "integrated"
            continue
        row = parse_qblock(tag)
        row["chapter_slug"] = slug
        row["unitcode"] = study_ref
        row["chapter_label"] = chapter_label
        row["section"] = role
        rows.append(row)
    return rows


def extract_book(book_path=BOOK_PATH, verbose=True):
    """Parse the merged book and return (all_rows, per_chapter_counts,
    missing_sections). Factored out of main() so diff_book_vs_index.py can
    call this directly instead of shelling out to this script first and
    re-reading its JSON output -- always parses the book fresh."""
    with open(book_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    all_rows = []
    missing_sections = []
    per_chapter_counts = {}
    for slug, _filename, chapter_label, study_ref in CHAPTERS:
        section_tag = soup.find("div", class_="qb-section", id=slug)
        if section_tag is None:
            missing_sections.append(slug)
            continue
        rows = extract_chapter_section(section_tag, slug, chapter_label, study_ref)
        per_chapter_counts[slug] = len(rows)
        all_rows.extend(rows)

    if verbose and missing_sections:
        print(f"WARNING: {len(missing_sections)} chapter section(s) from qb_merge.CHAPTERS "
              f"were not found in the book at all: {missing_sections}")

    return all_rows, per_chapter_counts, missing_sections


def main():
    all_rows, per_chapter_counts, missing_sections = extract_book()

    os.makedirs(QA_DIR, exist_ok=True)
    with open(EXTRACTED_PATH, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(all_rows)} qblock rows from {len(CHAPTERS)} chapter sections "
          f"in {os.path.relpath(BOOK_PATH, OUTPUT_DIR)}:")
    for slug, _filename, chapter_label, _ref in CHAPTERS:
        print(f"  {slug}: {per_chapter_counts.get(slug, 0)}")
    if missing_sections:
        print(f"\n(see WARNING above)")
    print(f"\nWrote {EXTRACTED_PATH}")


if __name__ == "__main__":
    main()
