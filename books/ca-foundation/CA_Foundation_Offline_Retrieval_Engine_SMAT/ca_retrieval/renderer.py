from __future__ import annotations
import re
from collections import defaultdict
from datetime import datetime
from .models import Block, QuerySpec
from .query import QUESTION_TYPES, ANSWER_TYPES

INTERNAL_COMMENT_RE = re.compile(r"^\s*<!--\s*(?:ICAI_SOURCE_PAGE(?:_RANGE)?|SOURCE_STRUCTURE)\b.*?-->\s*$", re.M)
HEADING_RE = re.compile(r"^#{1,6}\s+", re.M)

TYPE_LABELS = {
    "tyk_mcq_question": "MCQ",
    "answer_mcq": "MCQ Answer",
    "tyk_true_false_question": "True/False",
    "answer_true_false": "True/False Answer",
    "tyk_theory_question": "Theoretical Question",
    "answer_theory": "Theoretical Answer",
    "tyk_practical_question": "Practical Question",
    "answer_practical": "Practical Answer",
    "tyk_scenario_question": "Scenario-Based Question",
    "answer_scenario": "Scenario Answer",
    "illustration_question": "Illustration Question",
    "illustration_solution": "Illustration Solution",
    "example": "Example",
    "example_question": "Example Question",
    "example_solution": "Example Solution",
    "topic": "Topic",
    "subtopic": "Sub-topic",
    "summary": "Summary",
    "learning_outcomes": "Learning Outcomes",
    "overview": "Overview",
}


def clean_content(content: str, keep_internal_comments: bool = False) -> str:
    text = content.strip()
    if not keep_internal_comments:
        text = INTERNAL_COMMENT_RE.sub("", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def page_label(b: Block) -> str:
    if b.page_start is None:
        physical = "not recorded"
    elif b.page_end is None or b.page_end == b.page_start:
        physical = str(b.page_start)
    else:
        physical = f"{b.page_start}–{b.page_end}"
    if b.printed_page_start:
        if b.printed_page_end and b.printed_page_end != b.printed_page_start:
            printed = f"{b.printed_page_start}–{b.printed_page_end}"
        else:
            printed = b.printed_page_start
        return f"PDF page {physical}; ICAI printed page {printed}"
    return f"PDF page {physical}"


def block_heading(b: Block) -> str:
    label = TYPE_LABELS.get(b.type, b.type.replace("_", " ").title())
    number = b.number
    if number not in (None, ""):
        return f"{label} {number}"
    seq = b.meta.get("sequence")
    if seq and b.type.startswith("example_"):
        return f"{label} (sequence {seq})"
    topic = b.meta.get("topic_number")
    if b.type == "topic" and topic:
        title = b.meta.get("topic_title") or ""
        return f"Topic {topic}: {title}".rstrip(": ")
    return label


def render(blocks: list[Block], spec: QuerySpec, keep_internal_comments: bool = False) -> str:
    lines: list[str] = []
    lines.append(f"# {spec.title}")
    lines.append("")
    lines.append("> Generated offline from explicitly classified `ICAI_BLOCK` metadata. No AI/API used for retrieval.")
    if spec.original_query:
        lines.append(f"> Query: {spec.original_query}")
    if not spec.everything:
        primary_count = sum(1 for b in blocks if b.type not in ANSWER_TYPES)
        lines.append(f"> Source items matched: {primary_count}")
    lines.append(f"> Returned blocks: {len(blocks)}")
    lines.append("")

    if not blocks:
        lines.append("_No matching blocks were found for this query/filter._")
        lines.append("")
        return "\n".join(lines)

    current_paper = current_chapter = object()
    current_unit_key = object()

    for b in blocks:
        paper = b.paper
        chapter = b.chapter
        unit = b.unit
        unit_key = (chapter, unit, b.document.path.name)

        if paper != current_paper:
            current_paper = paper
            current_chapter = object()
            current_unit_key = object()
            ptitle = b.document.paper_title
            lines += [f"## Paper {paper:02d}" + (f": {ptitle}" if ptitle else ""), ""]
        if chapter != current_chapter:
            current_chapter = chapter
            current_unit_key = object()
            ctitle = b.document.chapter_title
            lines += [f"### Chapter {chapter}" + (f": {ctitle}" if ctitle else ""), ""]
        if unit_key != current_unit_key:
            current_unit_key = unit_key
            if unit is None:
                label = f"Chapter Scope: {b.document.unit_title or b.document.chapter_title}"
            else:
                label = f"Unit {unit}: {b.document.unit_title or 'Untitled'}"
            lines += [f"#### {label}", ""]

        lines += [f"##### {block_heading(b)}", ""]
        text = clean_content(b.content, keep_internal_comments=keep_internal_comments)
        # Keep source text intact; only remove leading Markdown heading if it duplicates our generated heading.
        if text:
            first, *rest = text.splitlines()
            if first.lstrip().startswith("#") and block_heading(b).lower().split()[0] in first.lower():
                text = "\n".join(rest).lstrip()
            lines.append(text)
            lines.append("")
        lines.append(f"> **Source:** `{b.source_pdf}` — {page_label(b)} — Block `{b.id}`")
        if b.pair_key:
            lines.append(f"> **Pair key:** `{b.pair_key}`")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
