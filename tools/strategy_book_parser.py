#!/usr/bin/env python3
"""
md_to_html.py — CA Inter Strategy Book  MD → HTML converter

Parses CA-Inter-Strategy-Book-MASTER.md (the 10-component markdown format)
and renders one or all sections as print-ready B5 HTML using the visual system
defined in design-spec.md.

Usage:
    python md_to_html.py                              # render Bucket 0 → build/bucket-0.html
    python md_to_html.py --section "BUCKET 0"
    python md_to_html.py --section all
    python md_to_html.py --list-sections
    python md_to_html.py --section "BUCKET 2" --output my.html
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

# ── Design tokens ─────────────────────────────────────────────────────────────

SECTION_META = {
    "BUCKET 0":          {"color": "#5C6B7A", "label": "Foundation",         "slug": "bucket-0",       "index": 0},
    "BUCKET 1":          {"color": "#0E7C7B", "label": "Before the Journey", "slug": "bucket-1",       "index": 1},
    "BUCKET 2":          {"color": "#2E8B57", "label": "While in Classes",   "slug": "bucket-2",       "index": 2},
    "BUCKET 3":          {"color": "#E8A13D", "label": "Revision Phase",     "slug": "bucket-3",       "index": 3},
    "BUCKET 4":          {"color": "#E07A2F", "label": "45 Days Before",     "slug": "bucket-4",       "index": 4},
    "BUCKET 5":          {"color": "#8E2C3A", "label": "The Exam Days",      "slug": "bucket-5",       "index": 5},
    "BUCKET 6":          {"color": "#4A90C4", "label": "After Exam",         "slug": "bucket-6",       "index": 6},
    "THE AI SECTION":    {"color": "#6C4FB8", "label": "AI Section",         "slug": "ai-section",     "index": 7},
    "AI SECTION":        {"color": "#6C4FB8", "label": "AI Section",         "slug": "ai-section",     "index": 7},
    "EMERGENCY SECTION": {"color": "#E03131", "label": "Emergency",          "slug": "emergency",      "index": 8},
    "ROUTING PAGE":      {"color": "#1F2933", "label": "Routing",            "slug": "routing",        "index": -1},
    "FRONT MATTER":      {"color": "#1F2933", "label": "Front Matter",       "slug": "front-matter",   "index": -2},
    "PERSONAL PAGES":    {"color": "#1F2933", "label": "Personal Pages",     "slug": "personal-pages", "index": 9},
    "THE COMPREHENSIVE": {"color": "#1F2933", "label": "Cover",              "slug": "cover",          "index": -3},
    "THE AUTHOR'S JOURNEY": {"color": "#1F2933", "label": "The Author's Journey", "slug": "authors-journey", "index": 10},
}

GOLD   = "#C9A227"
INK    = "#1F2933"
GREY   = "#EEF1F4"

# ── Page geometry ──────────────────────────────────────────────────────────────
# Single source of truth: design/page-geometry.json. get_css() templates BOTH
# the :root CSS variables and the literal @page rule from this same dict, so
# there is exactly one place to ever change page size/margins.

def load_geometry() -> dict:
    here = Path(__file__).resolve().parent
    geo_path = here.parent / 'books' / 'strategy-book' / 'design' / 'page-geometry.json'
    with geo_path.open(encoding='utf-8') as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith('_')}

# Known component markers (all-caps, may contain space / ? / — / -)
COMPONENT_MARKERS = {
    "HOW TO DO THIS",
    "STARTING LATE? BARE MINIMUM",
    "END GOAL",
    "RANK ONLY",
    "FILL-IN",
    "DIAGRAM",
    "WARNING",
    "EXAMPLE",
    "CHECKLIST — END OF BUCKET",
    "PRANAV'S TIP",
}

JOURNEY_LABELS  = ["0", "1", "2", "3", "4", "5", "6", "AI", "EMG"]
JOURNEY_IDX_MAP = {
    "bucket-0": 0, "bucket-1": 1, "bucket-2": 2, "bucket-3": 3,
    "bucket-4": 4, "bucket-5": 5, "bucket-6": 6, "ai-section": 7, "emergency": 8,
}


# ── Inline markdown ───────────────────────────────────────────────────────────

def inline_md(text: str) -> str:
    """Convert inline markdown to safe HTML spans."""
    text = html.escape(text, quote=False)
    # Bold-italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # ★ star
    text = text.replace('★', '<span class="star">★</span>')
    # [REF: ...]
    text = re.sub(r'\[REF:\s*(.+?)\]', r'<span class="ref-tag">→ \1</span>', text)
    # [STRUCTURE ONLY ...]
    text = re.sub(r'\[STRUCTURE ONLY[^\]]*\]', r'<span class="placeholder structure-only">[STRUCTURE ONLY]</span>', text)
    # [AUTHOR TO CONFIRM ...]
    text = re.sub(r'\[AUTHOR TO CONFIRM[^\]]*\]', r'<span class="placeholder author-confirm">[AUTHOR TO CONFIRM]</span>', text)
    # [AUTO-GENERATED]
    text = re.sub(r'\[AUTO-GENERATED\]', r'<span class="placeholder">[AUTO-GENERATED]</span>', text)
    return text


# ── Tokenizer ─────────────────────────────────────────────────────────────────

def tokenize(lines: list) -> list:
    """Convert a list of raw text lines into block tokens."""
    tokens = []
    i, n = 0, len(lines)

    while i < n:
        raw = lines[i] if isinstance(lines[i], str) else lines[i]
        stripped = raw.rstrip() if isinstance(raw, str) else raw

        # Empty line
        if not stripped:
            i += 1
            continue

        # Double HR ── section separator
        if stripped == '---' and i + 1 < n and _rstrip(lines[i + 1]) == '---':
            tokens.append({'type': 'section_break'})
            i += 2
            continue

        # Single HR
        if stripped == '---':
            tokens.append({'type': 'hr'})
            i += 1
            continue

        # H1
        if re.match(r'^# [^#]', stripped):
            tokens.append({'type': 'h1', 'text': stripped[2:].strip()})
            i += 1
            continue

        # H2
        if re.match(r'^## [^#]', stripped):
            tokens.append({'type': 'h2', 'text': stripped[3:].strip()})
            i += 1
            continue

        # H3
        if re.match(r'^### [^#]', stripped):
            text = stripped[4:].strip()
            m = re.match(r'^Strategy\s+(\d+)\s+[—\-]\s+(.+?)\s+\[(ALL|RANK)\]$', text)
            if m:
                tokens.append({
                    'type': 'strategy_heading',
                    'number': m.group(1),
                    'title': m.group(2),
                    'tag': m.group(3),
                })
            else:
                tokens.append({'type': 'h3', 'text': text})
            i += 1
            continue

        # Fenced code block
        if stripped.startswith('```'):
            lang = stripped[3:].strip()
            body = []
            i += 1
            while i < n and not _rstrip(lines[i]).startswith('```'):
                line = lines[i]
                body.append(line.rstrip('\n').rstrip('\r') if isinstance(line, str) else line)
                i += 1
            i += 1  # closing ```
            tokens.append({'type': 'code_block', 'lang': lang, 'content': '\n'.join(body)})
            continue

        # Blockquote
        if stripped.startswith('> ') or stripped == '>':
            bq = []
            while i < n and (_rstrip(lines[i]).startswith('> ') or _rstrip(lines[i]) == '>'):
                s = _rstrip(lines[i])
                bq.append(s[2:] if s.startswith('> ') else '')
                i += 1
            _emit_blockquote(bq, tokens)
            continue

        # Checklist  (- [ ] / - [x] / ★ mixed list)
        if stripped.startswith('- [ ] ') or stripped.startswith('- [x] '):
            items = []
            while i < n:
                s = _rstrip(lines[i])
                if s.startswith('- [ ] '):
                    items.append({'checked': False, 'rank': False, 'text': s[6:]})
                elif s.startswith('- [x] '):
                    items.append({'checked': True,  'rank': False, 'text': s[6:]})
                elif s.startswith('★ '):
                    items.append({'checked': False, 'rank': True,  'text': s[2:]})
                else:
                    break
                i += 1
            tokens.append({'type': 'checklist', 'items': items})
            continue

        # Markdown table  (line starts with |)
        if stripped.startswith('|'):
            rows = []
            while i < n and _rstrip(lines[i]).startswith('|'):
                rows.append(_rstrip(lines[i]))
                i += 1
            def _parse_row(r):
                r = r.strip().strip('|')
                return [c.strip() for c in r.split('|')]
            if len(rows) >= 2:
                headers  = _parse_row(rows[0])
                data     = [_parse_row(r) for r in rows[2:]]  # skip separator row
                tokens.append({'type': 'table', 'headers': headers, 'rows': data})
            continue

        # Unordered list
        if stripped.startswith('- '):
            items = []
            while i < n and _rstrip(lines[i]).startswith('- '):
                items.append(_rstrip(lines[i])[2:])
                i += 1
            tokens.append({'type': 'ul', 'items': items})
            continue

        # Ordered list
        if re.match(r'^\d+\.\s', stripped):
            items = []
            while i < n and re.match(r'^\d+\.\s', _rstrip(lines[i])):
                items.append(re.sub(r'^\d+\.\s+', '', _rstrip(lines[i])))
                i += 1
            tokens.append({'type': 'ol', 'items': items})
            continue

        # Standalone ★ rank item (outside checklist)
        if stripped.startswith('★ '):
            tokens.append({'type': 'rank_item', 'text': stripped[2:]})
            i += 1
            continue

        # Paragraph (collect consecutive non-special lines)
        para = []
        while i < n:
            s = _rstrip(lines[i])
            if not s:
                break
            if (s.startswith('#') or s.startswith('> ') or s == '>'
                    or s.startswith('```') or s.startswith('- ')
                    or s == '---' or s.startswith('★ ')
                    or re.match(r'^\d+\.\s', s)):
                break
            para.append(s)
            i += 1
        if para:
            tokens.append({'type': 'paragraph', 'text': ' '.join(para)})
        continue

    return tokens


def _rstrip(line) -> str:
    return line.rstrip() if isinstance(line, str) else str(line)


def _emit_blockquote(bq_lines: list, tokens: list):
    """Classify a collected blockquote as a component or plain blockquote."""
    if not bq_lines:
        return
    first = bq_lines[0]

    # Match **MARKER:** or **MARKER: Title** patterns
    # Character class for marker body: uppercase, digits, space, ?, —, -
    m = re.match(r'^\*\*([A-Z][A-Z0-9 ?—\-]+?)(?::\s*([^*]*?))?\*\*\s*(.*)', first)
    if m:
        marker    = m.group(1).strip()
        title     = (m.group(2) or '').strip()
        rest_line = (m.group(3) or '').strip()

        is_known = (marker in COMPONENT_MARKERS
                    or marker.split(':')[0].strip() in COMPONENT_MARKERS
                    or any(marker.startswith(k) for k in COMPONENT_MARKERS))
        if is_known:
            content = []
            if rest_line:
                content.append(rest_line)
            content.extend(bq_lines[1:])
            tokens.append({
                'type':          'component',
                'marker':        marker,
                'title':         title,
                'content_lines': content,
            })
            return

    # Plain / anonymous blockquote
    tokens.append({'type': 'blockquote', 'lines': bq_lines})


# ── Section extractor ─────────────────────────────────────────────────────────

def extract_sections(text: str) -> dict:
    """Split MASTER.md text by H1 headings → {HEADING_UPPER: [lines]}."""
    sections   = {}
    current_k  = None
    current_ls = []

    for line in text.splitlines(keepends=True):
        m = re.match(r'^# ([^#].+)', line.rstrip())
        if m:
            if current_k is not None:
                sections[current_k] = current_ls
            current_k  = m.group(1).strip().upper()
            current_ls = [line]
        elif current_k is not None:
            current_ls.append(line)

    if current_k is not None:
        sections[current_k] = current_ls

    return sections


def find_section_key(sections: dict, query: str) -> str | None:
    q = query.upper().strip()
    for key in sections:
        if key == q or key.startswith(q) or q in key:
            return key
    return None


def get_section_meta(section_key: str) -> dict:
    ku = section_key.upper()
    for k, v in SECTION_META.items():
        if ku == k or ku.startswith(k):
            return v
    return {'color': INK, 'label': section_key.title(), 'slug': 'section', 'index': -1}


# ── HTML Renderer ─────────────────────────────────────────────────────────────

def _tint(hex_color: str, opacity: float) -> str:
    """Blend hex colour with white at given opacity → rgb() string."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r2 = int(r * opacity + 255 * (1 - opacity))
    g2 = int(g * opacity + 255 * (1 - opacity))
    b2 = int(b * opacity + 255 * (1 - opacity))
    return f'rgb({r2},{g2},{b2})'


class Renderer:
    def __init__(self, color: str, slug: str):
        self.color    = color
        self.slug     = slug
        self.color_15 = _tint(color, 0.15)
        self.color_40 = _tint(color, 0.40)

    def render(self, tokens: list) -> str:
        return '\n'.join(filter(None, (self._tok(t) for t in tokens)))

    def _tok(self, t: dict) -> str:
        kind = t['type']
        if kind == 'h1':              return self._h1(t['text'])
        if kind == 'h2':              return f'<h2 class="section-subtitle">{inline_md(t["text"])}</h2>'
        if kind == 'h3':              return f'<h3 class="subsection-heading">{html.escape(t["text"])}</h3>'
        if kind == 'strategy_heading': return self._strat(t)
        if kind == 'paragraph':       return f'<p>{inline_md(t["text"])}</p>'
        if kind == 'code_block':      return self._code(t)
        if kind == 'ul':
            li = ''.join(f'<li>{inline_md(x)}</li>' for x in t['items'])
            return f'<ul class="body-list">{li}</ul>'
        if kind == 'ol':
            li = ''.join(f'<li>{inline_md(x)}</li>' for x in t['items'])
            return f'<ol class="body-list">{li}</ol>'
        if kind == 'checklist':       return self._checklist(t['items'])
        if kind == 'rank_item':
            return f'<p class="rank-line"><span class="star">★</span> {inline_md(t["text"])}</p>'
        if kind == 'table':            return self._table(t)
        if kind == 'blockquote':      return self._plain_bq(t['lines'])
        if kind == 'component':       return self._component(t)
        if kind == 'hr':              return '<hr class="strat-rule">'
        return ''  # section_break, etc.

    # ── H1 banner ──

    def _h1(self, text: str) -> str:
        m = re.match(r'^BUCKET\s+(\d+)\s+[—\-]\s+(.+)', text)
        if m:
            num, name = m.group(1), m.group(2)
            return (
                f'<div class="bucket-banner" style="background:{self.color}">'
                f'<span class="bucket-num">{num}</span>'
                f'<div class="bucket-nameblock">'
                f'<span class="bucket-label">BUCKET {num}</span>'
                f'<span class="bucket-name">{html.escape(name)}</span>'
                f'</div></div>'
            )
        return f'<h1 class="section-h1">{inline_md(text)}</h1>'

    # ── Strategy heading ──

    def _strat(self, t: dict) -> str:
        num, title, tag = t['number'], t['title'], t['tag']
        if tag == 'RANK':
            badge = f'<span class="badge badge-rank">★ RANK</span>'
        else:
            badge = f'<span class="badge badge-all">ALL</span>'
        return (
            f'<div class="strat-head" id="s{num}">'
            f'<span class="strat-circle" style="background:{self.color}">{num}</span>'
            f'<span class="strat-title">{html.escape(title)}</span>'
            f'{badge}</div>'
        )

    # ── Code block ──

    def _code(self, t: dict) -> str:
        return f'<pre class="tmpl-block"><code>{html.escape(t["content"])}</code></pre>'

    # ── Checklist ──

    def _checklist(self, items: list) -> str:
        rows = []
        for item in items:
            if item['rank']:
                text = re.sub(r'^\[RANK\]\s*', '', item['text'])
                rows.append(
                    f'<li class="cl-item cl-rank">'
                    f'<span class="star">★</span>'
                    f'<span class="cl-text">{inline_md(text)}</span></li>'
                )
            else:
                sym = '☑' if item['checked'] else '☐'
                rows.append(
                    f'<li class="cl-item">'
                    f'<span class="cl-box">{sym}</span>'
                    f'<span class="cl-text">{inline_md(item["text"])}</span></li>'
                )
        return '<ul class="checklist">' + ''.join(rows) + '</ul>'

    # ── Markdown table ──

    def _table(self, t: dict) -> str:
        th = ''.join(f'<th>{inline_md(h)}</th>' for h in t['headers'])
        body = ''
        for row in t['rows']:
            cells = ''.join(f'<td>{inline_md(c)}</td>' for c in row)
            body += f'<tr>{cells}</tr>'
        return (
            f'<div class="table-wrap">'
            f'<table class="content-table">'
            f'<thead><tr>{th}</tr></thead>'
            f'<tbody>{body}</tbody>'
            f'</table>'
            f'</div>'
        )

    # ── Plain blockquote ──

    def _plain_bq(self, lines: list) -> str:
        parts = []
        buf = []
        for ln in lines:
            if ln.strip():
                buf.append(ln)
            else:
                if buf:
                    parts.append(f'<p>{inline_md(" ".join(buf))}</p>')
                    buf = []
        if buf:
            parts.append(f'<p>{inline_md(" ".join(buf))}</p>')
        inner = ''.join(parts) or ''
        return f'<blockquote class="anon-bq">{inner}</blockquote>'

    # ── Component rendering ──

    def _component(self, t: dict) -> str:
        marker  = t['marker']
        title   = t.get('title', '')
        content = self._component_body(t.get('content_lines', []))

        if marker == 'HOW TO DO THIS':
            return (
                f'<div class="comp how-to" style="border-left:4px solid {self.color}">'
                f'<div class="comp-head">'
                f'<span class="comp-icon">⚙</span>'
                f'<span class="comp-label" style="color:{self.color}">HOW TO DO THIS</span>'
                f'</div>'
                f'<div class="comp-body">{content}</div>'
                f'</div>'
            )

        if marker == 'END GOAL':
            return (
                f'<div class="comp end-goal" style="border:2px solid {self.color}">'
                f'<div class="comp-head end-goal-head" style="background:{self.color}">'
                f'<span class="comp-label" style="color:white">END GOAL</span>'
                f'</div>'
                f'<div class="comp-body">{content}</div>'
                f'</div>'
            )

        if marker == 'RANK ONLY':
            return (
                f'<div class="comp rank-only" style="border-left:4px solid {GOLD}">'
                f'<div class="comp-head">'
                f'<span class="star">★</span>'
                f'<span class="comp-label" style="color:{GOLD}">RANK ONLY</span>'
                f'</div>'
                f'<div class="comp-body">{content}</div>'
                f'</div>'
            )

        if marker == 'STARTING LATE? BARE MINIMUM':
            return (
                f'<div class="comp bare-min" style="background:{GREY};border:2px dashed #8a9bac">'
                f'<div class="comp-head">'
                f'<span class="comp-icon">⏱</span>'
                f'<span class="comp-label">STARTING LATE? BARE MINIMUM</span>'
                f'</div>'
                f'<div class="comp-body">{content}</div>'
                f'</div>'
            )

        if marker == 'WARNING':
            return (
                f'<div class="comp warning" style="background:#fff0f0;border-left:4px solid #E03131">'
                f'<div class="comp-head">'
                f'<span class="comp-icon">⚠</span>'
                f'<span class="comp-label" style="color:#E03131">WARNING</span>'
                f'</div>'
                f'<div class="comp-body">{content}</div>'
                f'</div>'
            )

        if marker == 'DIAGRAM':
            diag_name = title or ''
            return (
                f'<div class="comp diagram-ph">'
                f'<div class="diag-icon">📐</div>'
                f'<div class="diag-label">DIAGRAM: {html.escape(diag_name)}</div>'
                f'<div class="diag-desc">{content}</div>'
                f'</div>'
            )

        if marker == 'FILL-IN':
            form_name = title or ''
            return (
                f'<div class="comp fill-in">'
                f'<div class="fill-head" style="background:{self.color_15};'
                f'border:1px solid {self.color_40}">'
                f'<span class="comp-icon">✏</span>'
                f'<span class="comp-label" style="color:{self.color}">'
                f'FILL-IN: {html.escape(form_name)}</span>'
                f'</div>'
                f'<div class="comp-body">{content}</div>'
                f'</div>'
            )

        if marker == 'CHECKLIST — END OF BUCKET':
            return (
                f'<div class="comp end-checklist" style="border:2px solid {self.color}">'
                f'<div class="comp-head" style="background:{self.color}">'
                f'<span class="comp-label" style="color:white">CHECKLIST — END OF BUCKET</span>'
                f'</div>'
                f'<div class="comp-body">{content}</div>'
                f'</div>'
            )

        if marker == "PRANAV'S TIP":
            return (
                f'<div class="comp pran-tip" style="background:#fffdf5;'
                f'border-left:4px solid {self.color}">'
                f'<div class="comp-head">'
                f'<span class="comp-icon">💡</span>'
                f'<span class="comp-label" style="color:{self.color}">PRANAV\'S TIP</span>'
                f'</div>'
                f'<div class="comp-body handwritten">{content}</div>'
                f'</div>'
            )

        # Generic fallback (NEEDS HUMAN DECISION items, NOTE:, FILTER: etc.)
        return (
            f'<div class="comp generic-callout" style="border-left:3px solid {self.color_40}">'
            f'<div class="comp-head">'
            f'<span class="comp-label">{html.escape(marker)}'
            + (f': {html.escape(title)}' if title else '')
            + f'</span></div>'
            f'<div class="comp-body">{content}</div>'
            f'</div>'
        )

    def _component_body(self, lines: list) -> str:
        """Re-tokenize and render the inner lines of a component blockquote."""
        sub = tokenize(lines)
        parts = []
        for t in sub:
            k = t['type']
            if k == 'paragraph':
                parts.append(f'<p>{inline_md(t["text"])}</p>')
            elif k == 'ul':
                li = ''.join(f'<li>{inline_md(x)}</li>' for x in t['items'])
                parts.append(f'<ul class="comp-list">{li}</ul>')
            elif k == 'ol':
                li = ''.join(f'<li>{inline_md(x)}</li>' for x in t['items'])
                parts.append(f'<ol class="comp-list">{li}</ol>')
            elif k == 'checklist':
                parts.append(self._checklist(t['items']))
            elif k == 'code_block':
                parts.append(self._code(t))
            elif k == 'table':
                parts.append(self._table(t))
            elif k == 'rank_item':
                parts.append(f'<p class="rank-line"><span class="star">★</span> {inline_md(t["text"])}</p>')
            elif k == 'blockquote':
                parts.append(self._plain_bq(t['lines']))
            # h1/h2/h3/hr/strategy_heading inside components: skip
        if not parts:
            all_text = ' '.join(ln for ln in lines if isinstance(ln, str) and ln.strip())
            if all_text:
                return f'<p>{inline_md(all_text)}</p>'
        return '\n'.join(parts)


# ── CSS ───────────────────────────────────────────────────────────────────────

def get_css(geo: dict) -> str:
    css = """
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800;900&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&family=Kalam:wght@300;400;700&display=swap');

/* ── Reset ── */
*, *::before, *::after {
  box-sizing: border-box; margin: 0; padding: 0;
  print-color-adjust: exact;
  -webkit-print-color-adjust: exact;
}

:root {
  --ink:       #1F2933;
  --gold:      #C9A227;
  --grey:      #EEF1F4;
  --body-f:    'Source Sans 3', sans-serif;
  --head-f:    'Archivo', sans-serif;
  --hand-f:    'Kalam', cursive;
  --pg-w:      __PG_W__;
  --pg-h:      __PG_H__;
  --m-inner:   __M_INNER__;
  --m-outer:   __M_OUTER__;
  --m-top:     __M_TOP__;
  --m-bottom:  __M_BOTTOM__;
}

body {
  font-family: var(--body-f);
  font-size: 10.5pt;
  line-height: 1.6;
  color: var(--ink);
}

/* ── Book content flow ──
   One continuous flow, no manual page division. paged.js slices this into
   as many physical pages as the content needs, at whatever size @page below
   declares. Resize the page by editing design/page-geometry.json only —
   nothing in this file or in the content HTML ever needs to change. */
.book-content { }

/* ── Running header (paged.js repeats this on every page via @page @top-center) ── */
.running-header {
  position: running(bookHeader);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-family: var(--head-f);
  font-size: 7pt;
  letter-spacing: 0.04em;
  padding-bottom: 1.5mm;
  border-bottom: 0.5pt solid #d5dae0;
}
.r-book-title {
  color: #8a9bac;
  text-transform: lowercase;
  font-variant: small-caps;
}
.r-section {
  font-weight: 700;
}

/* ── Edge tab (paged.js repeats this on every right-hand page: @page :right / @right-middle) ── */
.edge-tab {
  position: running(bookEdgeTab);
  width: 12mm;
  height: 22mm;
  border-radius: 4px 0 0 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tab-label {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  transform: rotate(180deg);
  font-family: var(--head-f);
  font-size: 6pt;
  font-weight: 800;
  color: white;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  line-height: 1;
}

/* ── Journey strip footer (paged.js repeats this on every page via @page @bottom-center) ──
   display/flex-direction/flex-wrap are !important here because paged.js has a known
   quirk: content cloned into a @page margin box via content:element() can pick up an
   inline style during that clone that silently forces block layout, which otherwise
   beats a plain (non-!important) class rule and stacks the segments into a vertical
   column instead of a row (confirmed visually via headless-Chrome screenshot,
   2026-07-22 — see project_log.md). !important on the stylesheet rule is the only
   thing that reliably wins against an inline style. */
.journey-strip {
  position: running(bookFooter);
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  align-items: center;
  gap: 2.5pt;
  padding-top: 1.5mm;
  border-top: 0.5pt solid #d5dae0;
}
.j-seg {
  width: 14pt;
  height: 8pt;
  border-radius: 2pt;
  background: #dde3e8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--head-f);
  font-size: 5pt;
  font-weight: 800;
  color: #8a9bac;
  flex-shrink: 0;
}
.j-seg.active { color: white; }
.j-seg.past   { opacity: 0.6; }

/* ── Section banner (bucket opener) ──
   NOTE: contained within the normal content column, not full-bleed to the
   trim edge — true edge-to-edge colour under @page-margin pagination needs
   a dedicated zero-margin named page (see project_log for this open item). */
.bucket-banner {
  margin: 0 0 7mm 0;
  padding: 9mm 6mm 7mm 6mm;
  display: flex;
  align-items: center;
  gap: 7mm;
  color: white;
}
.bucket-num {
  font-family: var(--head-f);
  font-size: 80pt;
  font-weight: 900;
  line-height: 1;
  opacity: 0.22;
  letter-spacing: -3pt;
  flex-shrink: 0;
}
.bucket-nameblock {
  display: flex;
  flex-direction: column;
  gap: 1mm;
}
.bucket-label {
  font-family: var(--head-f);
  font-size: 7.5pt;
  font-weight: 700;
  letter-spacing: 0.18em;
  opacity: 0.7;
}
.bucket-name {
  font-family: var(--head-f);
  font-size: 22pt;
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.3pt;
}

/* ── Generic H1 (non-bucket) ── */
.section-h1 {
  font-family: var(--head-f);
  font-size: 18pt;
  font-weight: 800;
  margin-bottom: 5mm;
}

/* ── H2 subtitle ── */
.section-subtitle {
  font-family: var(--head-f);
  font-size: 11pt;
  font-weight: 400;
  color: #607080;
  margin-top: -3mm;
  margin-bottom: 6mm;
}

/* ── H3 non-strategy ── */
.subsection-heading {
  font-family: var(--head-f);
  font-size: 7.5pt;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #8a9bac;
  margin: 6mm 0 3mm;
  padding-bottom: 1.5mm;
  border-bottom: 1px solid #dde3e8;
}

/* ── Strategy heading ── */
.strat-head {
  display: flex;
  align-items: center;
  gap: 3mm;
  margin: 5mm 0 3.5mm;
  flex-wrap: nowrap;
}
.strat-circle {
  flex-shrink: 0;
  width: 8mm;
  height: 8mm;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--head-f);
  font-size: 9pt;
  font-weight: 800;
  color: white;
  line-height: 1;
}
.strat-title {
  flex: 1;
  font-family: var(--head-f);
  font-size: 11.5pt;
  font-weight: 700;
  line-height: 1.25;
}
.badge {
  flex-shrink: 0;
  font-family: var(--head-f);
  font-size: 7pt;
  font-weight: 700;
  padding: 1pt 5pt;
  border-radius: 10pt;
  letter-spacing: 0.04em;
}
.badge-all  { border: 1.5pt solid var(--ink); color: var(--ink); }
.badge-rank { background: var(--gold); color: white; }

/* ── Strategy rule ── */
.strat-rule {
  border: none;
  border-top: 1px solid #e0e5ea;
  margin: 5mm 0;
}

/* ── Body text ── */
p { margin-bottom: 3mm; }
p:last-child { margin-bottom: 0; }
strong { font-weight: 600; }
em     { font-style: italic; }
code {
  font-family: 'Courier New', monospace;
  font-size: 8.5pt;
  background: #f0f2f4;
  padding: 1pt 3pt;
  border-radius: 2pt;
}

/* ── Lists ── */
ul.body-list, ol.body-list {
  margin: 2mm 0 3mm 5mm;
  padding-left: 4mm;
}
ul.body-list li, ol.body-list li {
  margin-bottom: 1.5mm;
}

/* ── Markdown table ── */
.table-wrap { overflow-x: auto; margin: 3mm 0; }
.content-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9.5pt;
}
.content-table th {
  background: #eef1f4;
  font-family: var(--head-f);
  font-weight: 700;
  font-size: 8pt;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 2mm 3mm;
  text-align: left;
  border: 1px solid #c8d0da;
}
.content-table td {
  padding: 2mm 3mm;
  border: 1px solid #dde3e8;
  vertical-align: top;
  line-height: 1.5;
}
.content-table tbody tr:nth-child(even) { background: #f7f8fa; }

/* ── Checklist ── */
ul.checklist {
  list-style: none;
  margin: 3mm 0;
  padding: 0;
}
.cl-item {
  display: flex;
  align-items: flex-start;
  gap: 3mm;
  margin-bottom: 2.5mm;
  line-height: 1.45;
}
.cl-box {
  flex-shrink: 0;
  font-size: 12pt;
  line-height: 1.1;
  color: #8a9bac;
}
.cl-rank .star {
  flex-shrink: 0;
  color: var(--gold);
  font-size: 11pt;
  line-height: 1.3;
}
.cl-text { flex: 1; }

/* ── Code / template block ── */
.tmpl-block {
  background: #f7f8fa;
  border: 1px solid #dde3e8;
  border-left: 3px solid #b0bcc8;
  border-radius: 3pt;
  padding: 3mm 4mm;
  font-family: 'Courier New', monospace;
  font-size: 8.5pt;
  line-height: 1.5;
  white-space: pre;
  overflow-x: auto;
  margin: 3mm 0;
  color: #2d3a45;
}

/* ── Anonymous blockquote ── */
blockquote.anon-bq {
  border-left: 3px solid #c5cdd5;
  padding: 2mm 4mm;
  margin: 3mm 0;
  color: #4a5568;
  font-style: italic;
}
blockquote.anon-bq p { margin-bottom: 1.5mm; }

/* ── Components: shared ── */
.comp {
  margin: 5mm 0;
  border-radius: 5pt;
  overflow: hidden;
}
.comp-head {
  display: flex;
  align-items: center;
  gap: 2.5mm;
  padding: 2.5mm 4mm;
  border-bottom: 1px solid rgba(0,0,0,0.07);
}
.end-goal-head { border-bottom: none; }
.comp-label {
  font-family: var(--head-f);
  font-size: 7.5pt;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.comp-icon { font-size: 11pt; line-height: 1; }
.avatar {
  width: 7mm; height: 7mm;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--head-f);
  font-size: 8pt;
  font-weight: 800;
  color: white;
  flex-shrink: 0;
}
.comp-body {
  padding: 3mm 4mm;
}
.comp-body p { margin-bottom: 2mm; }
.comp-body p:last-child { margin-bottom: 0; }
ul.comp-list, ol.comp-list {
  margin: 1.5mm 0 2mm 4mm;
  padding-left: 3mm;
}
.comp-list li { margin-bottom: 1.5mm; }

/* ── Pranav's Tip (handwritten style, formerly Author Says) ── */
.author-says { border-radius: 6pt; }
.handwritten, .handwritten p {
  font-family: var(--hand-f) !important;
  font-size: 11pt;
  line-height: 1.65;
  color: #2a3a47;
}

/* ── HOW TO DO THIS ── */
.how-to { background: #fbfcfd; }

/* ── RANK ONLY ── */
.rank-only { background: #fffbee; }

/* ── Rank inline ── */
.rank-line {
  padding-left: 3mm;
  border-left: 2.5pt solid var(--gold);
  margin: 2mm 0;
}
.star { color: var(--gold); font-weight: 700; }

/* ── END GOAL ── */
.end-goal { }
.end-goal .comp-body { padding-top: 4mm; }

/* ── DIAGRAM placeholder ── */
.diagram-ph {
  background: #f7f8fa;
  border: 2px dashed #b5c0ca;
  border-radius: 5pt;
  padding: 7mm;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2mm;
  min-height: 32mm;
  justify-content: center;
}
.diag-icon { font-size: 24pt; opacity: 0.35; }
.diag-label {
  font-family: var(--head-f);
  font-size: 7.5pt;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #8a9bac;
}
.diag-desc { font-size: 8.5pt; color: #8a9bac; max-width: 80%; }
.diag-desc p { margin: 0; }

/* ── FILL-IN ── */
.fill-in { overflow: visible; }
.fill-head {
  display: flex; align-items: center; gap: 2.5mm;
  padding: 2.5mm 4mm;
  border-radius: 5pt 5pt 0 0;
}

/* ── PRANAV'S TIP ── */
.pran-tip { border-radius: 4pt; }

/* ── Generic callout ── */
.generic-callout {
  background: #f9fafb;
  padding: 3mm 4mm 3mm 5mm;
  border-radius: 0 4pt 4pt 0;
}

/* ── Inline tags ── */
.ref-tag      { font-size: 8.5pt; color: #8a9bac; font-style: italic; }
.placeholder  { font-size: 8.5pt; font-style: italic; padding: 1pt 4pt; border-radius: 2pt; }
.structure-only { background: #fff8e1; color: #a0522d; border: 1px dashed #f5c518; }
.author-confirm { background: #ffe0e0; color: #c0392b; border: 1px dashed #e74c3c; }

/* ── Overflow-proofing: never slice these across a page break ── */
.comp, .strat-head, .bucket-banner, .diagram-ph, .content-table, table,
blockquote.anon-bq, .tmpl-block {
  break-inside: avoid;
}
h1, h2, h3, .section-h1, .section-subtitle, .subsection-heading, .strat-head {
  break-after: avoid;
}

@media print {
  .placeholder { display: none; }
}

/* ── Page geometry + running elements (paged.js) ──
   size/margin are literal values templated from design/page-geometry.json.
   @page does not reliably resolve var(), so the generator substitutes the
   same source numbers here AND into the :root block above — edit the JSON,
   never these lines directly. */
@page {
  size: __PG_W__ __PG_H__;
  margin: __M_TOP__ __M_OUTER__ __M_BOTTOM__ __M_INNER__;

  @top-center    { content: element(bookHeader); }
  @bottom-center { content: element(bookFooter); width: 55mm; }
  @bottom-right  {
    content: counter(page);
    font-family: var(--head-f);
    font-size: 8pt;
    font-weight: 700;
    color: var(--ink);
  }
}

@page :right {
  @right-middle { content: element(bookEdgeTab); }
}
"""
    return (css
            .replace('__PG_W__', geo['page_width'])
            .replace('__PG_H__', geo['page_height'])
            .replace('__M_TOP__', geo['margin_top'])
            .replace('__M_BOTTOM__', geo['margin_bottom'])
            .replace('__M_INNER__', geo['margin_inner'])
            .replace('__M_OUTER__', geo['margin_outer']))


# ── Page builder ──────────────────────────────────────────────────────────────

def build_journey_strip(slug: str, color: str) -> str:
    active = JOURNEY_IDX_MAP.get(slug, -1)
    segs = []
    for i, lbl in enumerate(JOURNEY_LABELS):
        if i == active:
            segs.append(f'<span class="j-seg active" style="background:{color}">{lbl}</span>')
        elif i < active:
            segs.append(f'<span class="j-seg past" style="background:{color};opacity:0.35;color:white">{lbl}</span>')
        else:
            segs.append(f'<span class="j-seg">{lbl}</span>')
    return '<div class="journey-strip">' + ''.join(segs) + '</div>'


def build_page(body_html: str, slug: str, color: str, label: str) -> str:
    # Vertical "slot" for this section's edge tab, stepped down the fore-edge
    # (B0 near the top, EMG near the bottom) — same value as before, just
    # applied as an offset inside its own running margin box instead of a
    # position tied to one giant per-file page div.
    tab_top = 40 + max(0, JOURNEY_IDX_MAP.get(slug, 0)) * 22
    journey = build_journey_strip(slug, color)
    geo = load_geometry()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(label)} — CA Inter Strategy Book</title>
  <style>{get_css(geo)}</style>
</head>
<body>

  <!-- Running header: repeated on every physical page by paged.js (@page @top-center) -->
  <div class="running-header">
    <span class="r-book-title">CA Inter Strategy Guide</span>
    <span class="r-section" style="color:{color}">{html.escape(label)}</span>
  </div>

  <!-- Edge tab: repeated on every right-hand page by paged.js (@page :right / @right-middle) -->
  <div class="edge-tab" style="background:{color};margin-top:{tab_top}mm">
    <span class="tab-label">{html.escape(label[:8])}</span>
  </div>

  <!-- Journey strip footer: repeated on every physical page by paged.js (@page @bottom-center) -->
  {journey}

  <!-- Section content: one continuous flow, paginated automatically -->
  <div class="book-content">
{body_html}
  </div>

<script src="../vendor/paged.polyfill.js"></script>
</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def convert_section(lines: list, section_key: str) -> str:
    meta     = get_section_meta(section_key)
    renderer = Renderer(meta['color'], meta['slug'])
    tokens   = tokenize(lines)
    body     = renderer.render(tokens)
    return build_page(body, meta['slug'], meta['color'], meta['label'])


def main():
    ap = argparse.ArgumentParser(description='Strategy Book MD → HTML')
    ap.add_argument('input', nargs='?',
                    default='books/strategy-book/working/CA-Inter-Strategy-Book-MASTER.md',
                    help='Path to MASTER.md (default: relative from repo root)')
    ap.add_argument('--section', '-s', default='BUCKET 0',
                    help='"BUCKET 0", "BUCKET 3", "ROUTING PAGE", "all"')
    ap.add_argument('--output',  '-o', default=None,
                    help='Output HTML path (default: auto in design/templates/build/)')
    ap.add_argument('--list-sections', '-l', action='store_true',
                    help='List all H1 sections found and exit')
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        # Try resolving relative to this script's repo root
        here = Path(__file__).resolve().parent
        candidate = here.parent.parent.parent / 'working' / 'CA-Inter-Strategy-Book-MASTER.md'
        if candidate.exists():
            src = candidate
        else:
            print(f'ERROR: cannot find {args.input}', file=sys.stderr)
            sys.exit(1)

    text     = src.read_text(encoding='utf-8')
    sections = extract_sections(text)

    if args.list_sections:
        print('Sections found in', src)
        for k in sections:
            meta = get_section_meta(k)
            print(f'  {k}  (slug: {meta["slug"]})')
        return

    if args.section.lower() == 'all':
        out_dir = Path(args.output) if args.output else src.parent.parent / 'design' / 'templates' / 'build'
        out_dir.mkdir(parents=True, exist_ok=True)
        for key, ls in sections.items():
            m        = get_section_meta(key)
            out_path = out_dir / f'{m["slug"]}.html'
            out_path.write_text(convert_section(ls, key), encoding='utf-8')
            print(f'  {out_path}')
        print(f'Built {len(sections)} sections.')
        return

    key = find_section_key(sections, args.section)
    if not key:
        print(f'ERROR: section "{args.section}" not found.', file=sys.stderr)
        print('Run with --list-sections to see available sections.', file=sys.stderr)
        sys.exit(1)

    meta = get_section_meta(key)
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = src.parent.parent / 'design' / 'templates' / 'build' / f'{meta["slug"]}.html'

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(convert_section(sections[key], key), encoding='utf-8')
    print(f'Written: {out_path}')


if __name__ == '__main__':
    main()
