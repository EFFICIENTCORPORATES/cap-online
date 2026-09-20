#!/usr/bin/env python3
"""
extract_json_from_html.py
=========================

Syllabus Intelligence Engine — Step 3
Converts a verified ICAI Base HTML chapter file into the structured
ICAI Base JSON format defined in the architecture document.

Design principles
-----------------
1. HTML is the human-verifiable source of truth. JSON is machine-generated.
2. Every top-level block under <div class="chapter"> becomes one entry in
   blocks[], keyed by its data-sequence-id (unique).
3. NOTHING is lost. Every block carries:
     - structured fields specific to its block_type (per the schema), AND
     - raw_html  : the full inner HTML of the block, byte-for-byte
     - plain_text: clean text for search / queries / diffing
   So even if a future block type needs richer parsing, the source is
   already in the JSON and the script can be re-run.
4. Tables embedded inside illustrations / examples / answer-hints are
   extracted as {caption, headers, rows} per the schema, but ALSO retained
   inside raw_html on the parent block.
5. The `extraction-flag` blocks are preserved as their own block_type so
   the merge engine can detect & route them.
6. No content is paraphrased, removed, or reordered. Sequence order in the
   JSON exactly mirrors document order in the HTML.

Usage
-----
    python extract_json_from_html.py <input.html> <output.json>
    python extract_json_from_html.py <input.html> <output.json> --verified-by "Reviewer Name"

Requires: beautifulsoup4
    pip install beautifulsoup4
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from typing import Any

try:
    from bs4 import BeautifulSoup, NavigableString, Tag
except ImportError:
    sys.stderr.write(
        "ERROR: beautifulsoup4 is required.\n"
        "Install with:  pip install beautifulsoup4\n"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_text(s: str) -> str:
    """Collapse internal whitespace, strip ends. Keep unicode (₹, etc.) intact."""
    if s is None:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def _inner_html(tag: Tag) -> str:
    """Return the inner HTML of a tag (children concatenated as strings)."""
    return "".join(str(c) for c in tag.children).strip()


def _plain_text(tag: Tag) -> str:
    """All text content of a tag, whitespace-normalised."""
    return _clean_text(tag.get_text(separator=" ", strip=True))


def _list_items(tag: Tag) -> list[str]:
    """Return cleaned text of every <li> at any depth inside `tag`."""
    return [_clean_text(li.get_text(separator=" ", strip=True))
            for li in tag.find_all("li")]


def _first_heading_text(tag: Tag) -> str | None:
    """Return text of the first h1-h6 child, if any."""
    h = tag.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    return _clean_text(h.get_text(separator=" ", strip=True)) if h else None


def _extract_table(table: Tag) -> dict[str, Any]:
    """Extract a <table> into {caption, table_class, headers, rows}."""
    caption_tag = table.find("caption")
    caption = _clean_text(caption_tag.get_text(separator=" ", strip=True)) \
        if caption_tag else ""

    table_class = " ".join(table.get("class", [])) or None

    headers: list[str] = []
    thead = table.find("thead")
    if thead:
        # Use the LAST header row (handles multi-row headers gracefully)
        header_rows = thead.find_all("tr")
        if header_rows:
            headers = [_clean_text(th.get_text(separator=" ", strip=True))
                       for th in header_rows[-1].find_all(["th", "td"])]

    body_rows: list[list[str]] = []
    body_scope = table.find("tbody") or table
    for tr in body_scope.find_all("tr"):
        # Skip rows that live inside <thead>
        if tr.find_parent("thead"):
            continue
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        body_rows.append(
            [_clean_text(c.get_text(separator=" ", strip=True)) for c in cells]
        )

    # If there was no <thead>, the first row might be header-like — but we
    # don't second-guess. We respect the HTML structure as authored.
    return {
        "caption": caption,
        "table_class": table_class,
        "headers": headers,
        "rows": body_rows,
    }


def _extract_all_tables(tag: Tag) -> list[dict[str, Any]]:
    """Extract every <table> descendant in document order."""
    return [_extract_table(t) for t in tag.find_all("table")]


def _strip_leading_number_label(text: str) -> tuple[str | None, str]:
    """
    Many question/MCQ/answer blocks begin with '<strong>N.</strong> ...'
    Extract that leading number if present.
    Returns (number_as_str_or_None, remaining_text).
    """
    m = re.match(r"^\s*(\d+)\.\s+(.*)$", text)
    if m:
        return m.group(1), m.group(2).strip()
    return None, text


# ---------------------------------------------------------------------------
# Block-type-specific extractors
#
# Each receives the block <div> tag and returns a dict of fields to MERGE
# into the universal block dict. Universal fields (sequence_id, block_type,
# visibility, raw_html, plain_text) are added by the caller.
# ---------------------------------------------------------------------------

def _extract_chapter_heading(tag: Tag) -> dict[str, Any]:
    headings = tag.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    return {
        "headings": [_clean_text(h.get_text(separator=" ", strip=True))
                     for h in headings],
    }


def _extract_section_heading(tag: Tag) -> dict[str, Any]:
    headings = tag.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    return {
        "heading_text": _clean_text(headings[0].get_text(separator=" ", strip=True))
        if headings else _plain_text(tag),
        "heading_level": headings[0].name if headings else None,
    }


def _extract_learning_outcomes(tag: Tag) -> dict[str, Any]:
    heading = _first_heading_text(tag)
    intro_parts = []
    for child in tag.children:
        if isinstance(child, Tag):
            if child.name == "p":
                intro_parts.append(_clean_text(child.get_text(separator=" ", strip=True)))
            elif child.name in ("ul", "ol"):
                break  # stop intro at first list
    return {
        "heading": heading,
        "intro": " ".join(p for p in intro_parts if p) or None,
        "outcomes": _list_items(tag),
    }


def _extract_definition(tag: Tag) -> dict[str, Any]:
    # Try to detect a defined term — typically a <strong> at the start or
    # the structure "<TERM> defines/means ..."
    term = None
    first_strong = tag.find("strong")
    if first_strong:
        term = _clean_text(first_strong.get_text(separator=" ", strip=True))
    paragraphs = [_clean_text(p.get_text(separator=" ", strip=True))
                  for p in tag.find_all("p")]
    items = _list_items(tag)
    return {
        "term": term,
        "paragraphs": paragraphs,
        "list_items": items,
    }


def _extract_theory(tag: Tag) -> dict[str, Any]:
    heading = _first_heading_text(tag)
    paragraphs = [_clean_text(p.get_text(separator=" ", strip=True))
                  for p in tag.find_all("p")]
    return {
        "heading": heading,
        "paragraphs": paragraphs,
        "list_items": _list_items(tag),
        "tables": _extract_all_tables(tag),
    }


def _extract_concept_note(tag: Tag) -> dict[str, Any]:
    return _extract_theory(tag)  # same shape


def _extract_standard_provision(tag: Tag) -> dict[str, Any]:
    return _extract_theory(tag)


def _extract_exception(tag: Tag) -> dict[str, Any]:
    return _extract_theory(tag)


def _extract_flowchart_text(tag: Tag) -> dict[str, Any]:
    """
    Flowcharts have nested <div class="flowchart-text"> children that
    represent branches. We capture the structure recursively.
    """
    def _walk(t: Tag) -> dict[str, Any]:
        node_paragraphs = []
        children_nodes = []
        for c in t.children:
            if isinstance(c, Tag):
                if c.name == "div" and "flowchart-text" in (c.get("class") or []):
                    children_nodes.append(_walk(c))
                elif c.name in ("p", "h4", "h5", "h6"):
                    node_paragraphs.append(_clean_text(c.get_text(separator=" ", strip=True)))
                elif c.name in ("ul", "ol"):
                    node_paragraphs.extend(
                        f"• {item}" for item in _list_items(c)
                    )
        return {
            "text": node_paragraphs,
            "branches": children_nodes,
        }

    heading = _first_heading_text(tag)
    structure = _walk(tag)
    return {
        "heading": heading,
        "structure": structure,
    }


def _extract_solution_block(sol_tag: Tag, parent_seq_id: str) -> dict[str, Any]:
    """Extract a <div class='solution'> nested inside an illustration/example."""
    paragraphs = [_clean_text(p.get_text(separator=" ", strip=True))
                  for p in sol_tag.find_all("p", recursive=True)
                  if p.find_parent("div", class_="working-note") is None
                  and p.find_parent("div", class_="journal-entry") is None]

    # Working notes nested inside the solution
    working_notes = []
    for wn in sol_tag.find_all("div", class_="working-note"):
        working_notes.append({
            "paragraphs": [_clean_text(p.get_text(separator=" ", strip=True))
                           for p in wn.find_all("p")],
            "tables": _extract_all_tables(wn),
            "raw_html": _inner_html(wn),
        })

    # Journal entries (if any)
    journal_entries = []
    for je in sol_tag.find_all("div", class_="journal-entry"):
        journal_entries.append({
            "paragraphs": [_clean_text(p.get_text(separator=" ", strip=True))
                           for p in je.find_all("p")],
            "tables": _extract_all_tables(je),
            "raw_html": _inner_html(je),
        })

    # Accounting statements (P&L / BS / CFS) — tables tagged accordingly
    accounting_statements = []
    for tbl in sol_tag.find_all("table"):
        classes = tbl.get("class") or []
        if "accounting-statement-table" in classes:
            accounting_statements.append(_extract_table(tbl))

    # Tables that are NOT inside working-note / journal-entry / accounting-statement
    solution_tables = []
    for tbl in sol_tag.find_all("table"):
        if tbl.find_parent("div", class_="working-note"):
            continue
        if tbl.find_parent("div", class_="journal-entry"):
            continue
        if "accounting-statement-table" in (tbl.get("class") or []):
            continue
        solution_tables.append(_extract_table(tbl))

    return {
        "sequence_id": f"{parent_seq_id}.SOL",
        "block_type": "solution",
        "content_paragraphs": paragraphs,
        "tables": solution_tables,
        "accounting_statements": accounting_statements,
        "working_notes": working_notes,
        "journal_entries": journal_entries,
        "raw_html": _inner_html(sol_tag),
    }


def _extract_illustration(tag: Tag) -> dict[str, Any]:
    heading = _first_heading_text(tag) or ""
    # Illustration number — e.g. "Illustration 1", "Illustration 12"
    illustration_number = heading if heading else None

    # Question text = all <p> tags that are direct children before the
    # solution div, plus any tables shown as part of the question.
    question_paragraphs = []
    question_tables = []
    for child in tag.children:
        if isinstance(child, Tag):
            if child.name == "div" and "solution" in (child.get("class") or []):
                break
            if child.name == "p":
                question_paragraphs.append(_clean_text(child.get_text(separator=" ", strip=True)))
            elif child.name == "table":
                question_tables.append(_extract_table(child))

    # Solution
    seq_id = tag.get("data-sequence-id", "")
    sol_tag = tag.find("div", class_="solution", recursive=False)
    if sol_tag is None:
        # Fallback — sometimes nesting depth varies
        sol_tag = tag.find("div", class_="solution")
    solution = _extract_solution_block(sol_tag, seq_id) if sol_tag else None

    return {
        "illustration_number": illustration_number,
        "question_text": " ".join(question_paragraphs),
        "question_paragraphs": question_paragraphs,
        "question_tables": question_tables,
        "solution": solution,
        # Empty skeleton — to be filled by teacher customisation layer per schema
        "practical_solution_summary": {
            "given_directly": [],
            "given_indirectly": [],
            "what_was_asked": "",
            "approach_used": "",
            "formula_used": "",
            "common_mistakes": [],
            "exam_watchout": "",
        },
    }


def _extract_example(tag: Tag) -> dict[str, Any]:
    """Examples are like illustrations but usually shorter, no nested solution div."""
    heading = _first_heading_text(tag) or ""
    paragraphs = []
    for child in tag.children:
        if isinstance(child, Tag) and child.name == "p":
            paragraphs.append(_clean_text(child.get_text(separator=" ", strip=True)))
    return {
        "example_number": heading if heading else None,
        "paragraphs": paragraphs,
        "tables": _extract_all_tables(tag),
        "list_items": _list_items(tag),
    }


def _extract_mcq(tag: Tag) -> dict[str, Any]:
    # Question text — usually first <p> with leading "<strong>N.</strong>"
    question_p = tag.find("p")
    raw_q = _clean_text(question_p.get_text(separator=" ", strip=True)) if question_p else ""
    mcq_number, question_text = _strip_leading_number_label(raw_q)

    options: dict[str, str] = {}
    for opt in tag.find_all("div", class_="mcq-option"):
        opt_text = _clean_text(opt.get_text(separator=" ", strip=True))
        # Match leading "(a)", "(b)", ... possibly with optional spacing
        m = re.match(r"^\(\s*([a-zA-Z])\s*\)\s*(.*)$", opt_text)
        if m:
            options[m.group(1).lower()] = m.group(2).strip()
        else:
            # Fallback — store under the next available key
            next_key = chr(ord('a') + len(options))
            options[next_key] = opt_text

    return {
        "mcq_number": int(mcq_number) if mcq_number and mcq_number.isdigit() else None,
        "question_text": question_text,
        "options": options,
        # Answer + explanation populated by the matching mcq-answer block
        # in a downstream merge step. We leave placeholders per schema.
        "correct_answer": None,
        "mcq_solution_explanation": "",
        "one_day_revision": False,
    }


def _extract_mcq_answer(tag: Tag) -> dict[str, Any]:
    """
    MCQ answer blocks in this material are typically a single table laid out
    as: [Q#] [Ans] [Q#] [Ans] [Q#] [Ans] ...
    We parse them into a dict {question_number_str: option_letter}.
    """
    answers: dict[str, str] = {}
    tables = tag.find_all("table")
    for tbl in tables:
        for tr in tbl.find_all("tr"):
            cells = [_clean_text(td.get_text(separator=" ", strip=True))
                     for td in tr.find_all(["td", "th"])]
            # walk pairs (q_label, answer)
            i = 0
            while i < len(cells) - 1:
                q_match = re.match(r"^(\d+)\.?$", cells[i])
                a_match = re.match(r"^\(\s*([a-zA-Z])\s*\)\s*$", cells[i + 1])
                if q_match and a_match:
                    answers[q_match.group(1)] = a_match.group(1).lower()
                    i += 2
                else:
                    i += 1

    # Fallback — if no table found, parse paragraphs like "1. (a)"
    if not answers:
        for p in tag.find_all("p"):
            text = _clean_text(p.get_text(separator=" ", strip=True))
            for m in re.finditer(r"(\d+)\.\s*\(\s*([a-zA-Z])\s*\)", text):
                answers[m.group(1)] = m.group(2).lower()

    return {
        "answers": answers,  # e.g. {"1": "b", "2": "a", ...}
    }


def _extract_theoretical_question(tag: Tag) -> dict[str, Any]:
    raw = _clean_text(tag.get_text(separator=" ", strip=True))
    qnum, qtext = _strip_leading_number_label(raw)
    return {
        "question_number": int(qnum) if qnum and qnum.isdigit() else None,
        "question_text": qtext,
        "paragraphs": [_clean_text(p.get_text(separator=" ", strip=True))
                       for p in tag.find_all("p")],
    }


def _extract_scenario_question(tag: Tag) -> dict[str, Any]:
    first_p = tag.find("p")
    raw_first = _clean_text(first_p.get_text(separator=" ", strip=True)) if first_p else ""
    qnum, _ = _strip_leading_number_label(raw_first)
    paragraphs = [_clean_text(p.get_text(separator=" ", strip=True))
                  for p in tag.find_all("p")]
    return {
        "question_number": int(qnum) if qnum and qnum.isdigit() else None,
        "paragraphs": paragraphs,
        "list_items": _list_items(tag),
        "tables": _extract_all_tables(tag),
    }


def _extract_case_scenario(tag: Tag) -> dict[str, Any]:
    return _extract_scenario_question(tag)


def _extract_answer_hint(tag: Tag) -> dict[str, Any]:
    first_p = tag.find("p")
    raw_first = _clean_text(first_p.get_text(separator=" ", strip=True)) if first_p else ""
    qnum, _ = _strip_leading_number_label(raw_first)

    # Paragraphs that are NOT inside a working-note (those go separately)
    paragraphs = []
    for p in tag.find_all("p"):
        if p.find_parent("div", class_="working-note"):
            continue
        paragraphs.append(_clean_text(p.get_text(separator=" ", strip=True)))

    list_items = []
    for lst in tag.find_all(["ul", "ol"]):
        if lst.find_parent("div", class_="working-note"):
            continue
        list_items.extend(_list_items(lst))

    # Top-level tables (not inside working-note)
    top_tables = []
    for tbl in tag.find_all("table"):
        if tbl.find_parent("div", class_="working-note"):
            continue
        top_tables.append(_extract_table(tbl))

    # Working notes
    working_notes = []
    for wn in tag.find_all("div", class_="working-note"):
        working_notes.append({
            "paragraphs": [_clean_text(p.get_text(separator=" ", strip=True))
                           for p in wn.find_all("p")],
            "tables": _extract_all_tables(wn),
            "raw_html": _inner_html(wn),
        })

    return {
        "answer_number": int(qnum) if qnum and qnum.isdigit() else None,
        "paragraphs": paragraphs,
        "list_items": list_items,
        "tables": top_tables,
        "working_notes": working_notes,
    }


def _extract_extraction_flag(tag: Tag) -> dict[str, Any]:
    return {
        "reason": tag.get("data-reason", ""),
        "page": tag.get("data-page", ""),
        "description": tag.get("data-description", ""),
        "placeholder_text": _clean_text(tag.get_text(separator=" ", strip=True)),
        "needs_manual_entry": True,
    }


# ---------------------------------------------------------------------------
# Base Syllabus JSON topic-lookup helpers
# ---------------------------------------------------------------------------

def _load_base_chapter(base_json_path: str, chapter_id: str) -> dict[str, Any] | None:
    """Return the chapter entry whose unique_chapter_id matches chapter_id."""
    try:
        with open(base_json_path, "r", encoding="utf-8") as f:
            base = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"WARNING: could not load base JSON '{base_json_path}': {exc}\n")
        return None
    for ch in base.get("chapters", []):
        if ch.get("unique_chapter_id") == chapter_id:
            return ch
    sys.stderr.write(
        f"WARNING: chapter '{chapter_id}' not found in {base_json_path}\n"
        f"  Available IDs: "
        + ", ".join(c.get("unique_chapter_id", "?") for c in base.get("chapters", []))
        + "\n"
    )
    return None


def _build_topic_lookup(chapter_entry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Returns a dict keyed by topic_no (e.g. '1.1', '2.3') plus the special
    key '__header__' for the chapter-level header row (is_chapter_header_row=true).
    """
    lookup: dict[str, dict[str, Any]] = {}
    for topic in chapter_entry.get("topics", []):
        if topic.get("is_chapter_header_row"):
            lookup["__header__"] = topic
        else:
            tn = topic.get("topic_no")
            if tn is not None:
                lookup[str(tn)] = topic
    return lookup


def _extract_topic_no_from_heading(heading_text: str) -> str | None:
    """
    Extract a leading topic number from a section-heading text.
    Handles '1.1 INTRODUCTION', '4.10 SUSPENSION OF CAPITALISATION', '3 SCOPE' etc.
    Returns the matched string (e.g. '1.1') or None if no numeric prefix found.
    """
    m = re.match(r"^(\d+(?:\.\d+)*)\s", heading_text.strip())
    return m.group(1) if m else None


# Registry mapping block_type → extractor function
EXTRACTORS = {
    "chapter-heading": _extract_chapter_heading,
    "section-heading": _extract_section_heading,
    "learning-outcomes": _extract_learning_outcomes,
    "definition": _extract_definition,
    "theory": _extract_theory,
    "concept-note": _extract_concept_note,
    "standard-provision": _extract_standard_provision,
    "exception": _extract_exception,
    "flowchart-text": _extract_flowchart_text,
    "illustration": _extract_illustration,
    "example": _extract_example,
    "mcq": _extract_mcq,
    "mcq-answer": _extract_mcq_answer,
    "theoretical-question": _extract_theoretical_question,
    "scenario-question": _extract_scenario_question,
    "case-scenario": _extract_case_scenario,
    "answer-hint": _extract_answer_hint,
    "extraction-flag": _extract_extraction_flag,
}


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def _detect_block_type(tag: Tag) -> str | None:
    """Determine the block_type. Prefer data-block-type; fall back to class."""
    bt = tag.get("data-block-type")
    if bt:
        return bt.strip()
    classes = tag.get("class") or []
    if "extraction-flag" in classes:
        return "extraction-flag"
    # Pick the first class that we know how to handle
    for c in classes:
        if c in EXTRACTORS:
            return c
    return classes[0] if classes else None


def convert_html_to_json(
    html_path: str,
    *,
    verified_by: str = "",
    verified_on: str = "",
    generated_on: str | None = None,
    base_json_path: str = "",
    chapter_id: str = "",
) -> dict[str, Any]:
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    chapter_root = soup.find("div", class_="chapter")
    if chapter_root is None:
        raise ValueError(
            f"No <div class='chapter'> root found in {html_path}. "
            "The HTML must follow the ICAI Base HTML schema."
        )

    # ---- META --------------------------------------------------------------
    meta: dict[str, Any] = {
        "module": _coerce_int(chapter_root.get("data-module")),
        "chapter": _coerce_int(chapter_root.get("data-chapter")),
        "unit": _coerce_int(chapter_root.get("data-unit")),
        "icai_version": chapter_root.get("data-icai-version", ""),
        "exam_applicable": chapter_root.get("data-exam", ""),
        "generated_on": generated_on or date.today().isoformat(),
        "source_html": os.path.basename(html_path),
        "verified_by": verified_by,
        "verified_on": verified_on,
        "title": _infer_title(chapter_root),
    }

    # ---- BASE SYLLABUS JSON LOOKUP -----------------------------------------
    # When --base-json and --chapter-id are supplied, IDs are derived from the
    # pre-verified Base Syllabus JSON (unique_topic_id + incremental block counter).
    # Without them, the script falls back to reading data-sequence-id from HTML.
    topic_lookup: dict[str, dict[str, Any]] = {}
    chapter_syllabus: dict[str, Any] | None = None
    if base_json_path and chapter_id:
        chapter_entry = _load_base_chapter(base_json_path, chapter_id)
        if chapter_entry:
            topic_lookup = _build_topic_lookup(chapter_entry)
            chapter_syllabus = {
                "unique_chapter_id": chapter_entry.get("unique_chapter_id"),
                "teaching_sequence": chapter_entry.get("teaching_sequence"),
                "icai_chapter_ref": chapter_entry.get("icai_chapter_ref"),
                "chapter_name_icai": chapter_entry.get("chapter_name_icai"),
                "chapter_name_short": chapter_entry.get("chapter_name_short"),
                "marks_distinct_attempt_count": chapter_entry.get("marks_distinct_attempt_count"),
                "sn_alternate_order": chapter_entry.get("sn_alternate_order"),
                "marks_by_attempt": chapter_entry.get("marks_by_attempt"),
            }

    # ---- BLOCKS ------------------------------------------------------------
    blocks: list[dict[str, Any]] = []
    seen_seq_ids: set[str] = set()
    duplicate_seq_ids: list[str] = []
    unknown_block_types: set[str] = set()
    unmatched_headings: list[str] = []

    # Topic tracking state (used only when topic_lookup is active)
    current_topic: dict[str, Any] | None = topic_lookup.get("__header__") if topic_lookup else None
    block_counter: int = 0

    for child in chapter_root.children:
        if not isinstance(child, Tag):
            continue
        block_type = _detect_block_type(child)
        if block_type is None:
            continue

        visibility = child.get("data-visibility", "both")

        # --- Topic advancement (base JSON mode) ---
        # A section-heading whose text starts with a known topic_no advances
        # the current topic and resets the per-topic block counter.
        if topic_lookup and block_type == "section-heading":
            raw_heading = _plain_text(child)
            topic_no = _extract_topic_no_from_heading(raw_heading)
            if topic_no and topic_no in topic_lookup:
                current_topic = topic_lookup[topic_no]
                block_counter = 0
            elif topic_no:
                # Heading has a numeric prefix but it's not in the base JSON
                unmatched_headings.append(raw_heading)

        # --- Sequence ID assignment ---
        if topic_lookup and current_topic:
            block_counter += 1
            seq_id = f"{current_topic['unique_topic_id']}.B{block_counter}"
        else:
            # Fallback: use data-sequence-id from HTML (legacy / no base JSON)
            seq_id = child.get("data-sequence-id", "")

        block: dict[str, Any] = {
            "sequence_id": seq_id,
            "block_type": block_type,
            "visibility": visibility,
            "plain_text": _plain_text(child),
            "raw_html": _inner_html(child),
        }

        # Embed per-block syllabus context fields when base JSON is active
        if topic_lookup and current_topic:
            block["syllabus_topic_id"] = current_topic.get("unique_topic_id")
            block["syllabus_topics_id_name"] = current_topic.get("topics_id_name")
            block["syllabus_topic_sequence"] = current_topic.get("topic_sequence_in_chapter")
            block["syllabus_page_ref"] = current_topic.get("page_number_label")
            block["syllabus_icai_unit_label"] = current_topic.get("icai_unit_no_label")

        extractor = EXTRACTORS.get(block_type)
        if extractor is not None:
            block.update(extractor(child))
        else:
            unknown_block_types.add(block_type)
            # Even unknown types are kept — raw_html + plain_text cover them.

        # Fix solution sequence_id now that the parent seq_id is known
        if block_type == "illustration" and isinstance(block.get("solution"), dict):
            block["solution"]["sequence_id"] = f"{seq_id}.SOL"

        if seq_id:
            if seq_id in seen_seq_ids:
                duplicate_seq_ids.append(seq_id)
            seen_seq_ids.add(seq_id)

        blocks.append(block)

    # ---- DIAGNOSTICS -------------------------------------------------------
    extraction_flag_count = sum(1 for b in blocks
                                if b["block_type"] == "extraction-flag")

    diagnostics = {
        "total_blocks": len(blocks),
        "blocks_by_type": _count_by_type(blocks),
        "extraction_flags_present": extraction_flag_count,
        "duplicate_sequence_ids": duplicate_seq_ids,
        "unknown_block_types": sorted(unknown_block_types),
        "blocks_without_sequence_id": [
            i for i, b in enumerate(blocks) if not b["sequence_id"]
        ],
        "unmatched_topic_headings": unmatched_headings,
    }

    result: dict[str, Any] = {
        "meta": meta,
        "diagnostics": diagnostics,
        "blocks": blocks,
    }
    if chapter_syllabus:
        result["syllabus_meta"] = chapter_syllabus
    return result


def _coerce_int(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _count_by_type(blocks: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for b in blocks:
        counts[b["block_type"]] = counts.get(b["block_type"], 0) + 1
    return dict(sorted(counts.items()))


def _infer_title(chapter_root: Tag) -> str:
    """Best-effort title derived from the first chapter-heading block."""
    ch = chapter_root.find("div", class_="chapter-heading")
    if ch is None:
        return ""
    headings = ch.find_all(["h1", "h2", "h3"])
    parts = [_clean_text(h.get_text(separator=" ", strip=True)) for h in headings]
    return " — ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert ICAI Base HTML chapter to ICAI Base JSON."
    )
    parser.add_argument("input_html", help="Path to the verified ICAI Base HTML file.")
    parser.add_argument("output_json", help="Path to write the generated JSON file.")
    parser.add_argument("--verified-by", default="",
                        help="Name of human reviewer who verified the HTML.")
    parser.add_argument("--verified-on", default="",
                        help="Date HTML was verified (YYYY-MM-DD).")
    parser.add_argument("--generated-on", default=None,
                        help="Override the generated_on date (YYYY-MM-DD). "
                             "Defaults to today.")
    parser.add_argument("--base-json", default="",
                        help="Path to the Base Syllabus JSON "
                             "(0-ca-inter-adv-accounts-subtopics-marks-weightage.json). "
                             "When provided together with --chapter-id, block IDs are "
                             "derived from the base JSON instead of data-sequence-id in HTML.")
    parser.add_argument("--chapter-id", default="",
                        help="unique_chapter_id from the Base Syllabus JSON for this chapter "
                             "(e.g. 'M2-C5-U1'). Required when --base-json is supplied.")
    parser.add_argument("--indent", type=int, default=2,
                        help="JSON indentation (default: 2).")
    args = parser.parse_args()

    if not os.path.isfile(args.input_html):
        sys.stderr.write(f"ERROR: input HTML not found: {args.input_html}\n")
        sys.exit(1)

    result = convert_html_to_json(
        args.input_html,
        verified_by=args.verified_by,
        verified_on=args.verified_on,
        generated_on=args.generated_on,
        base_json_path=args.base_json,
        chapter_id=args.chapter_id,
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.output_json)) or ".",
                exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=args.indent, ensure_ascii=False)

    # Print summary to stderr
    diag = result["diagnostics"]
    sys.stderr.write(
        f"OK — wrote {args.output_json}\n"
        f"  Total blocks: {diag['total_blocks']}\n"
        f"  Extraction flags: {diag['extraction_flags_present']}\n"
        f"  Duplicate sequence IDs: {len(diag['duplicate_sequence_ids'])}\n"
        f"  Unknown block types: {diag['unknown_block_types'] or 'none'}\n"
    )
    if result.get("syllabus_meta"):
        sm = result["syllabus_meta"]
        sys.stderr.write(
            f"  Syllabus chapter: {sm['unique_chapter_id']} "
            f"(teaching seq #{sm['teaching_sequence']})\n"
        )
    unmatched = diag.get("unmatched_topic_headings", [])
    if unmatched:
        sys.stderr.write(
            f"  WARNING — {len(unmatched)} heading(s) had topic numbers not found "
            f"in the base JSON (kept under last matched topic):\n"
        )
        for h in unmatched:
            sys.stderr.write(f"    • {h}\n")


if __name__ == "__main__":
    main()
