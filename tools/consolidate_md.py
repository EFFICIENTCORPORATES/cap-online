#!/usr/bin/env python3
"""
consolidate_md.py
─────────────────────────────────────────────────────────────────────────────
Reads all 40 MD files from:
    books/concept-book/raw_icai_study_materials/

Merges them in Module → Chapter → Unit order into a single combined MD file:
    books/concept-book/syllabus-engine/combined_all_chapters.md

CONTENT IS NEVER MODIFIED.
Only <!-- HTML comment --> tags are INSERTED as parser anchors.

Tags added:
  MODULE-START / MODULE-END              — Module boundary (M1, M2, M3)
  CHAPTER-START / CHAPTER-END           — Chapter boundary (C1–C15)
  UNIT-START / UNIT-END                 — One per content file
  INITIAL-PAGES-START / END             — Module cover/disclaimer pages
  ANNEXURE-START / ANNEXURE-END         — Annexure file
  LEARNING-OUTCOMES-START / END         — Learning outcomes block
  OVERVIEW-START / OVERVIEW-END         — Unit/Chapter overview block
  SUBTOPIC-START id="x.y.z" / END       — Every numbered sub-topic heading
  ILLUSTRATION-START id="N" / END       — Every Illustration block
  SOLUTION-START for="N" / END          — Solution to Illustration N
  EXAMPLE-START id="N" / END            — Every Example block
  NOTE-START / NOTE-END                 — Every "Note:" block
  SUMMARY-START / SUMMARY-END           — Summary section
  TYK-START / TYK-END                   — Test Your Knowledge section

Run from repo root:
    python tools/consolidate_md.py
─────────────────────────────────────────────────────────────────────────────
"""

import re
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
INPUT_DIR   = Path("books/concept-book/raw_icai_study_materials")
OUTPUT_FILE = Path("books/concept-book/syllabus-engine/combined_all_chapters.md")

# ── DETECTION PATTERNS ────────────────────────────────────────────────────────
# All patterns are matched against the STRIPPED (no leading/trailing whitespace) line.

# L1 structural blocks (mutually exclusive, sequential within a unit)
RE_LEARNING_OUTCOMES = re.compile(r'^LEARNING\s+OUTCOMES$', re.IGNORECASE)
RE_OVERVIEW          = re.compile(r'^(UNIT|CHAPTER)\s+OVERVIEW$', re.IGNORECASE)
RE_SUMMARY           = re.compile(r'^SUMMARY$', re.IGNORECASE)
RE_TYK               = re.compile(r'^TEST\s+YOUR\s+KNOWLEDGE$', re.IGNORECASE)

# Sub-topic: "x.y" or "x.y.z" (one or more spaces) Title starting with uppercase
# Requires title to start with A-Z and have at least one more character.
# Strict enough to avoid matching page-number artifacts like "4.2" or "5.2 1".
RE_SUBTOPIC = re.compile(
    r'^(\d+\.\d+(?:\.\d+)*)\s+([A-Z][A-Za-z0-9\s\(\)\-\,\.\/\:\?\&]{1,})$'
)

# L2 content blocks (can appear within any L1 section)
# Illustration: entire line is "Illustration N" or "Illustration N:" (standalone heading)
RE_ILLUSTRATION = re.compile(
    r'^Illustration\s+(\d+)\s*[\:\-]?\s*$', re.IGNORECASE
)

# Solution: entire line is "Solution", "Solution N", "Solution to Illustration N"
RE_SOLUTION = re.compile(
    r'^Solution(\s+\d+|\s+to\s+Illustration\s+\d+)?\s*[\:\-]?\s*$', re.IGNORECASE
)

# Example: entire line is "Example N" or "Example N:" (standalone heading)
RE_EXAMPLE = re.compile(
    r'^Example\s+(\d+)\s*[\:\-]?\s*$', re.IGNORECASE
)

# Note: line starts with "Note:" or "Notes:" (may have content after on the same line)
RE_NOTE = re.compile(r'^Notes?\s*:', re.IGNORECASE)


# ── TAG BUILDER ───────────────────────────────────────────────────────────────
def htag(name, **attrs):
    """Return an HTML comment tag string: <!-- NAME key="val" ... -->"""
    attr_str = ''.join(f' {k}="{v}"' for k, v in attrs.items())
    return f'<!-- {name}{attr_str} -->'


# ── FILENAME PARSER ───────────────────────────────────────────────────────────
def parse_filename(path):
    """
    Parse filename like:  M1_C4_U2_ Accounting Standard 3 Cash Flow Statement.md
    Returns dict: {module, chapter, unit, title, path}  or  None if unrecognised.
    """
    m = re.match(r'^(M\d+)_(C\d+)_(U\d+)_\s*(.*)', path.stem)
    if not m:
        return None
    return {
        'module' : m.group(1),
        'chapter': m.group(2),
        'unit'   : m.group(3),
        'title'  : m.group(4).strip(),
        'path'   : path,
    }


def sort_key(info):
    """Sort by Module → Chapter → Unit → (Initial Pages first, Annexure second, content last)."""
    mod  = int(re.search(r'\d+', info['module']).group())
    chap = int(re.search(r'\d+', info['chapter']).group())
    unit = int(re.search(r'\d+', info['unit']).group())
    title = info['title']
    # Within the same M/C/U, ensure Initial Pages → Annexure → content
    order = 0 if 'Initial Pages' in title else (1 if 'Annexure' in title else 2)
    return (mod, chap, unit, order)


# ── PER-FILE PROCESSOR ────────────────────────────────────────────────────────
def process_file(info):
    """
    Read one MD file. Return a list of output lines with HTML comment tags inserted.
    The original content lines are NEVER changed — only tags are added between them.
    NUL bytes (OCR artifacts) are stripped before processing.
    """
    path    = info['path']
    module  = info['module']
    chapter = info['chapter']
    unit    = info['unit']
    title   = info['title']

    is_initial  = 'Initial Pages' in title
    is_annexure = 'Annexure'      in title

    # Read file — strip NUL bytes (OCR artefacts that are not real content)
    try:
        raw_bytes = path.read_bytes()
        raw_text  = raw_bytes.replace(b'\x00', b'').decode('utf-8', errors='replace')
    except Exception as e:
        print(f'      [ERROR] Cannot read {path.name}: {e}')
        return []

    lines = raw_text.splitlines()
    out   = []

    # Determine wrapper tag type
    block = ('INITIAL-PAGES' if is_initial else
             'ANNEXURE'      if is_annexure else
             'UNIT')

    # ── Open unit-level wrapper ───────────────────────────────────────────────
    out.append(htag(f'{block}-START',
                    module=module, chapter=chapter, unit=unit, title=title))
    out.append('')

    # Initial Pages and Annexure: no structural parsing, pass through verbatim
    if is_initial or is_annexure:
        out.extend(lines)
        out.append('')
        out.append(htag(f'{block}-END'))
        return out

    # ── State tracking for structural parsing ─────────────────────────────────
    # open_l1: which L1 block is currently open (None if none)
    #   values: 'LEARNING-OUTCOMES' | 'OVERVIEW' | 'SUBTOPIC' | 'SUMMARY' | 'TYK'
    open_l1 = None

    # open_l2: which L2 content block is currently open (None if none)
    #   values: 'ILLUSTRATION' | 'SOLUTION' | 'EXAMPLE'
    open_l2 = None

    # in_note: True when inside a Note block (closed by blank line)
    in_note = False

    # Counters and linkage for Illustrations / Examples
    illus_count   = 0   # running counter — becomes the illustration id
    example_count = 0   # running counter — becomes the example id
    current_illus = 0   # id of the ILLUSTRATION currently open (for SOLUTION linking)

    # ── Helper: close NOTE block ──────────────────────────────────────────────
    def close_note():
        nonlocal in_note
        if in_note:
            out.append(htag('NOTE-END'))
            in_note = False

    # ── Helper: close L2 block ────────────────────────────────────────────────
    def close_l2():
        nonlocal open_l2, current_illus
        close_note()
        if open_l2:
            out.append(htag(f'{open_l2}-END'))
            out.append('')
            # Reset illustration linkage only when closing non-SOLUTION blocks
            if open_l2 != 'SOLUTION':
                current_illus = 0
            open_l2 = None

    # ── Helper: close L1 block ────────────────────────────────────────────────
    def close_l1():
        nonlocal open_l1
        close_l2()
        if open_l1:
            out.append(htag(f'{open_l1}-END'))
            out.append('')
            open_l1 = None

    # ── Line-by-line pass ─────────────────────────────────────────────────────
    for raw_line in lines:
        stripped = raw_line.strip()

        # ── LEARNING OUTCOMES ─────────────────────────────────────────────────
        if RE_LEARNING_OUTCOMES.match(stripped):
            close_l1()
            open_l1 = 'LEARNING-OUTCOMES'
            out.append(htag('LEARNING-OUTCOMES-START'))
            out.append(raw_line)
            continue

        # ── UNIT / CHAPTER OVERVIEW ───────────────────────────────────────────
        if RE_OVERVIEW.match(stripped):
            close_l1()
            open_l1 = 'OVERVIEW'
            out.append(htag('OVERVIEW-START'))
            out.append(raw_line)
            continue

        # ── SUMMARY ───────────────────────────────────────────────────────────
        if RE_SUMMARY.match(stripped):
            close_l1()
            open_l1 = 'SUMMARY'
            out.append(htag('SUMMARY-START'))
            out.append(raw_line)
            continue

        # ── TEST YOUR KNOWLEDGE ───────────────────────────────────────────────
        if RE_TYK.match(stripped):
            close_l1()
            open_l1 = 'TYK'
            out.append(htag('TYK-START'))
            out.append(raw_line)
            continue

        # ── SUBTOPIC (x.y or x.y.z headings) ─────────────────────────────────
        # Skip subtopic detection inside SUMMARY and TYK to avoid false matches
        if open_l1 not in ('SUMMARY', 'TYK'):
            m = RE_SUBTOPIC.match(stripped)
            if m:
                sub_id    = m.group(1)
                sub_title = m.group(2).strip()
                close_l2()
                # Close previous subtopic or L1 section before opening new subtopic
                if open_l1 == 'SUBTOPIC':
                    out.append(htag('SUBTOPIC-END'))
                    out.append('')
                elif open_l1 in ('LEARNING-OUTCOMES', 'OVERVIEW'):
                    out.append(htag(f'{open_l1}-END'))
                    out.append('')
                open_l1 = 'SUBTOPIC'
                out.append(htag('SUBTOPIC-START', id=sub_id, title=sub_title))
                out.append(raw_line)
                continue

        # ── ILLUSTRATION ──────────────────────────────────────────────────────
        if RE_ILLUSTRATION.match(stripped):
            close_l2()
            illus_count  += 1
            current_illus = illus_count
            open_l2 = 'ILLUSTRATION'
            out.append(htag('ILLUSTRATION-START', id=str(illus_count)))
            out.append(raw_line)
            continue

        # ── SOLUTION (closes the preceding ILLUSTRATION before opening) ────────
        if RE_SOLUTION.match(stripped):
            close_note()
            if open_l2 == 'ILLUSTRATION':
                # Close illustration explicitly before solution
                out.append(htag('ILLUSTRATION-END'))
                out.append('')
                open_l2 = None
            elif open_l2 == 'SOLUTION':
                # Back-to-back solutions (rare) — close previous
                close_l2()
            sol_attrs = {'for': str(current_illus)} if current_illus > 0 else {}
            open_l2 = 'SOLUTION'
            out.append(htag('SOLUTION-START', **sol_attrs))
            out.append(raw_line)
            continue

        # ── EXAMPLE ───────────────────────────────────────────────────────────
        if RE_EXAMPLE.match(stripped):
            close_l2()
            example_count += 1
            open_l2 = 'EXAMPLE'
            out.append(htag('EXAMPLE-START', id=str(example_count)))
            out.append(raw_line)
            continue

        # ── NOTE (multi-line block; closed by first blank line) ───────────────
        if RE_NOTE.match(stripped):
            close_note()          # close any previous note
            in_note = True
            out.append(htag('NOTE-START'))
            out.append(raw_line)
            continue

        # ── BLANK LINE — closes a NOTE block if one is open ───────────────────
        if stripped == '' and in_note:
            close_note()
            out.append(raw_line)
            continue

        # ── DEFAULT: content line — passed through UNCHANGED ──────────────────
        out.append(raw_line)

    # ── Close anything still open at end of file ──────────────────────────────
    close_l1()

    out.append('')
    out.append(htag(f'{block}-END'))
    return out


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    SEP  = '═' * 68
    SEP2 = '─' * 68

    print(SEP)
    print('  consolidate_md.py — CA Inter Advanced Accounting')
    print('  Merging all MD files into one parser-tagged combined file')
    print(SEP)
    print(f'  Input  : {INPUT_DIR}')
    print(f'  Output : {OUTPUT_FILE}')
    print()

    # ── STEP 1: Discover and sort all MD files ────────────────────────────────
    print('[1/4] Discovering MD files...')
    all_paths = sorted(INPUT_DIR.glob('*.md'))
    total_found = len(all_paths)
    print(f'      Total .md files found : {total_found}')

    parsed, skipped = [], []
    for p in all_paths:
        info = parse_filename(p)
        if info:
            parsed.append(info)
        else:
            skipped.append(p.name)
            print(f'      [WARN] Cannot parse filename — skipped: {p.name}')

    parsed.sort(key=sort_key)
    print(f'      Successfully parsed   : {len(parsed)} files')
    if skipped:
        print(f'      Skipped (bad names)   : {len(skipped)} files')
    print()
    print('      Processing order:')
    print(f'      {"#":<4} {"Module/Ch/Unit":<18} {"Title"}')
    print(f'      {SEP2}')
    for i, info in enumerate(parsed, 1):
        flag = (' [INITIAL-PAGES]' if 'Initial Pages' in info['title'] else
                ' [ANNEXURE]'      if 'Annexure'      in info['title'] else '')
        print(f'      {i:02d}.  '
              f'{info["module"]}/{info["chapter"]}/{info["unit"]:<8}  '
              f'{info["title"]}{flag}')
    print()

    # ── STEP 2: Process each file, insert tags ────────────────────────────────
    print('[2/4] Processing and tagging content...')
    print()

    combined_lines = [
        '# COMBINED — CA Inter Advanced Accounting — All Chapters',
        '<!-- AUTO-GENERATED by tools/consolidate_md.py — DO NOT EDIT MANUALLY -->',
        '<!-- Source: books/concept-book/raw_icai_study_materials/ -->',
        '',
    ]

    prev_module  = None
    prev_chapter = None

    for info in parsed:
        mod   = info['module']
        chap  = info['chapter']
        unit  = info['unit']
        title = info['title']

        # Module boundary
        if mod != prev_module:
            if prev_module is not None:
                combined_lines.append(f'<!-- MODULE-END module="{prev_module}" -->')
                combined_lines.append('')
            combined_lines.append(f'<!-- MODULE-START module="{mod}" -->')
            combined_lines.append('')
            prev_module  = mod
            prev_chapter = None
            print(f'  ── {mod} {"─" * 55}')

        # Chapter boundary
        if chap != prev_chapter:
            if prev_chapter is not None:
                combined_lines.append(f'<!-- CHAPTER-END chapter="{prev_chapter}" -->')
                combined_lines.append('')
            combined_lines.append(
                f'<!-- CHAPTER-START module="{mod}" chapter="{chap}" -->'
            )
            combined_lines.append('')
            prev_chapter = chap

        # Process the file
        flag = (' [INITIAL-PAGES]' if 'Initial Pages' in title else
                ' [ANNEXURE]'      if 'Annexure'      in title else '')
        print(f'      [{mod}/{chap}/{unit}] {title}{flag}')

        file_lines = process_file(info)
        combined_lines.extend(file_lines)
        combined_lines.append('')

    # Close last chapter and module
    if prev_chapter:
        combined_lines.append(f'<!-- CHAPTER-END chapter="{prev_chapter}" -->')
        combined_lines.append('')
    if prev_module:
        combined_lines.append(f'<!-- MODULE-END module="{prev_module}" -->')
        combined_lines.append('')

    print()

    # ── STEP 3: Write output file ─────────────────────────────────────────────
    print('[3/4] Writing combined output file...')
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output_text = '\n'.join(combined_lines)
    OUTPUT_FILE.write_text(output_text, encoding='utf-8')
    size_kb    = OUTPUT_FILE.stat().st_size // 1024
    line_count = len(combined_lines)
    print(f'      Written to : {OUTPUT_FILE}')
    print(f'      Total lines: {line_count:,}')
    print(f'      File size  : {size_kb:,} KB')
    print()

    # ── STEP 4: Verification — count all inserted tags ────────────────────────
    print('[4/4] Verification — tag counts in output:')
    print(f'      {SEP2}')
    tag_names = [
        ('MODULE-START',           'Modules'),
        ('CHAPTER-START',          'Chapters'),
        ('UNIT-START',             'Content units'),
        ('INITIAL-PAGES-START',    'Initial-Pages files'),
        ('ANNEXURE-START',         'Annexure files'),
        ('LEARNING-OUTCOMES-START','Learning Outcomes blocks'),
        ('OVERVIEW-START',         'Overview blocks'),
        ('SUBTOPIC-START',         'Sub-topic headings'),
        ('ILLUSTRATION-START',     'Illustrations'),
        ('SOLUTION-START',         'Solutions'),
        ('EXAMPLE-START',          'Examples'),
        ('NOTE-START',             'Note blocks'),
        ('SUMMARY-START',          'Summary sections'),
        ('TYK-START',              'Test Your Knowledge sections'),
    ]
    for tag_str, label in tag_names:
        count = output_text.count(f'<!-- {tag_str}')
        print(f'      {label:<32}: {count:>5}')
    print(f'      {SEP2}')

    # Sanity checks
    print()
    print('      Sanity checks:')
    # Every START should have a matching END
    issues = 0
    for tag_str, label in tag_names:
        start_count = output_text.count(f'<!-- {tag_str}')
        end_name    = tag_str.replace('-START', '-END')
        end_count   = output_text.count(f'<!-- {end_name}')
        if start_count != end_count:
            print(f'      [WARN] {label}: {start_count} START vs {end_count} END — mismatch!')
            issues += 1
    if issues == 0:
        print('      All START/END tag pairs are balanced.')
    else:
        print(f'      {issues} mismatche(s) found — review output manually.')

    print()
    print(SEP)
    print('  DONE — Consolidation complete.')
    print(SEP)


if __name__ == '__main__':
    main()
