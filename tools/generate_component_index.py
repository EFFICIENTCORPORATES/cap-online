#!/usr/bin/env python3
"""
generate_component_index.py

Reads CA-Inter-Strategy-Book-MASTER.md and regenerates MASTER-component-index.md.

Run after any edit to MASTER.md:
    python tools/generate_component_index.py

Auto-generates:  Reference code system, per-bucket tables (A), non-bucket table (B),
                 global summary (C).
Preserves:       Everything after <!-- MANUAL-SECTIONS-START --> on re-runs.
                 First run inserts default placeholder text for those sections.
"""

import re
import hashlib
from datetime import date
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent
MASTER    = REPO_ROOT / "books/strategy-book/working/CA-Inter-Strategy-Book-MASTER.md"
INDEX_OUT = REPO_ROOT / "books/strategy-book/working/MASTER-component-index.md"

# Everything after this line is preserved across re-runs (manually maintained)
SENTINEL = "<!-- MANUAL-SECTIONS-START -->"

# ── Component detection ────────────────────────────────────────────────────────
COMP_PAT = {
    "IF":  re.compile(r"^> \*\*IMPLEMENTATION FRAMEWORK"),
    "PT":  re.compile(r"^> \*\*PRANAV'S TIP"),
    "HTD": re.compile(r"^> \*\*HOW TO DO THIS"),
    "SL":  re.compile(r"^> \*\*STARTING LATE"),
    "EG":  re.compile(r"^> \*\*END GOAL"),
    "RO":  re.compile(r"^> \*\*RANK ONLY"),
    "FI":  re.compile(r"^> \*\*FILL-IN"),
    "DI":  re.compile(r"^> \*\*DIAGRAM"),
    "EX":  re.compile(r"^> \*\*EXAMPLE"),
    "WA":  re.compile(r"^> \*\*WARNING"),
    "CS":  re.compile(r"^> \*\*CHECKLIST"),
}

# Component columns shown in per-bucket strategy rows (display order)
BUCKET_COLS = ["IF", "PT", "HTD", "SL", "EG", "RO", "WA"]

# ── Structural patterns ────────────────────────────────────────────────────────
RE_BUCKET = re.compile(r"^# BUCKET (\d+)")
RE_TRACK  = re.compile(r"^## TRACK ([AB])\b", re.IGNORECASE)
RE_STRAT  = re.compile(r"^### (?:Strategy|Step) (\d+)\s*[—\-–]+\s*(.+?)(?:\s+\[(ALL|RANK)\])?$")

# ── Data models ───────────────────────────────────────────────────────────────

class Strategy:
    def __init__(self, bkt: str, num: int, title: str, tag: str = "ALL"):
        self.bkt   = bkt        # "0"–"5", "6A", "6B", "E" etc.
        self.num   = num
        self.title = title
        self.tag   = tag.upper()
        self.comps: dict = defaultdict(int)

    @property
    def ref(self) -> str:
        pfx = "RSG" if self.tag == "RANK" else "ASG"
        return f"{pfx}.{self.bkt}.{self.num}"


class Section:
    def __init__(self, sid: str, name: str, is_bucket: bool = False):
        self.sid         = sid
        self.name        = name
        self.is_bucket   = is_bucket
        self.strategies: list = []
        self.intro_comps: dict = defaultdict(int)


# ── Parser ────────────────────────────────────────────────────────────────────

def _sec_id(title: str) -> str:
    t = title.upper()
    for key, sid in [
        ("FRONT MATTER", "FM"), ("ROUTING", "RP"), ("AI SECTION", "AI"),
        ("EMERGENCY",    "E"),  ("PERSONAL PAGES", "PP"), ("AUTHOR", "AJ"),
    ]:
        if key in t:
            return sid
    return t[:4].strip()


def parse(path: Path):
    text  = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    sections = []
    cur       = None
    cur_strat = None
    cur_track = ""

    def push(sid, name, is_bkt):
        nonlocal cur, cur_strat, cur_track
        s = Section(sid, name, is_bkt)
        sections.append(s)
        cur, cur_strat, cur_track = s, None, ""

    for line in lines:
        # Bucket header: # BUCKET N — ...
        m = RE_BUCKET.match(line)
        if m:
            push(m.group(1), line.lstrip("# ").strip(), True)
            continue

        # Other H1 headers
        if line.startswith("# "):
            title = line.lstrip("# ").strip()
            push(_sec_id(title), title, "EMERGENCY" in title.upper())
            continue

        if cur is None:
            continue

        # Track A / B (Bucket 6 only)
        if cur.sid == "6":
            m = RE_TRACK.match(line)
            if m:
                cur_track = m.group(1).upper()
                cur_strat = None
                continue

        # Strategy or Step heading
        m = RE_STRAT.match(line)
        if m:
            num   = int(m.group(1))
            title = m.group(2).strip()
            tag   = (m.group(3) or "ALL").upper()
            bkt   = f"6{cur_track}" if (cur.sid == "6" and cur_track) else cur.sid
            s     = Strategy(bkt, num, title, tag)
            cur.strategies.append(s)
            cur_strat = s
            continue

        # Component markers
        for ctype, pat in COMP_PAT.items():
            if pat.match(line):
                if cur_strat:
                    cur_strat.comps[ctype] += 1
                else:
                    cur.intro_comps[ctype] += 1
                break

    return text, sections


# ── Table renderers ───────────────────────────────────────────────────────────

def _cell(n: int) -> str:
    if n == 0: return "—"
    return "✓" if n == 1 else f"({n})"


def _bucket_table(strats: list) -> str:
    if not strats:
        return "_No strategies detected._\n"
    active = [c for c in BUCKET_COLS if any(s.comps.get(c, 0) for s in strats)]
    hdr = "| Ref | Title |" + "".join(f" {c} |" for c in active)
    sep = "|-----|-------|" + "".join("-----|" for _ in active)
    rows = [
        f"| `{s.ref}` | {s.title} [{s.tag}] |"
        + "".join(f" {_cell(s.comps.get(c, 0))} |" for c in active)
        for s in strats
    ]
    return "\n".join([hdr, sep] + rows) + "\n"


def _non_bucket_table(sections: list) -> str:
    nb = [s for s in sections if not s.is_bucket]
    if not nb:
        return "_None._\n"
    # Which component types appear at all across non-bucket sections?
    active = [
        c for c in COMP_PAT
        if any(
            s.intro_comps.get(c, 0) + sum(st.comps.get(c, 0) for st in s.strategies)
            for s in nb
        )
    ]
    if not active:
        hdr  = "| Section | ID |"
        sep  = "|---------|-----|"
        rows = [f"| {s.name} | `{s.sid}` |" for s in nb]
    else:
        hdr  = "| Section | ID |" + "".join(f" {c} |" for c in active)
        sep  = "|---------|-----|" + "".join("-----|" for _ in active)
        rows = []
        for s in nb:
            tot: dict = defaultdict(int)
            for c, v in s.intro_comps.items(): tot[c] += v
            for st in s.strategies:
                for c, v in st.comps.items(): tot[c] += v
            rows.append(
                f"| {s.name} | `{s.sid}` |"
                + "".join(f" {_cell(tot.get(c, 0))} |" for c in active)
            )
    return "\n".join([hdr, sep] + rows) + "\n"


def _global_summary(sections: list) -> str:
    all_strats = [s for sec in sections for s in sec.strategies]
    totals: dict = defaultdict(int)
    for st in all_strats:
        for c, v in st.comps.items(): totals[c] += v
    for sec in sections:
        for c, v in sec.intro_comps.items(): totals[c] += v

    n_all  = sum(1 for s in all_strats if s.tag == "ALL")
    n_rank = sum(1 for s in all_strats if s.tag == "RANK")
    rank_refs = " · ".join(f"`{s.ref}`" for s in all_strats if s.tag == "RANK")

    def bkt_breakdown(c: str) -> str:
        parts = []
        for sec in sections:
            cnt = sec.intro_comps.get(c, 0) + sum(st.comps.get(c, 0) for st in sec.strategies)
            if cnt:
                parts.append(f"B{sec.sid}:{cnt}")
        return " ".join(parts) if parts else "—"

    rows = [
        "| Component | Total | Breakdown by bucket |",
        "|-----------|-------|---------------------|",
    ]
    for c in COMP_PAT:
        if totals[c]:
            rows.append(f"| **{c}** | {totals[c]} | {bkt_breakdown(c)} |")

    strat_breakdown = " ".join(
        f"B{sec.sid}:{len(sec.strategies)}" for sec in sections if sec.strategies
    )
    rows += [
        "| | | |",
        f"| **Total strategies** | **{n_all + n_rank}** | {strat_breakdown} |",
        f"| \\[ALL] | {n_all} | |",
        f"| \\[RANK] | {n_rank} | {rank_refs} |",
    ]
    return "\n".join(rows) + "\n"


# ── Default manual tail (first run only) ─────────────────────────────────────

DEFAULT_MANUAL = """\
## D. FILL-IN Inventory

*Manually maintained. Auto-count: see FI row in Global Summary.*

| Form Name | Location |
|-----------|----------|
| Why I Am Doing CA | Personal Pages |
| My Vision Board | Personal Pages |
| My Dream Marksheet | Personal Pages |
| Plans to Do After Exams | Personal Pages |
| My Boundary | Personal Pages (one per subject) |

*Inline fill-in references within strategy text are not FI-tagged at the reference point — see NEEDS HUMAN DECISION #9.*

---

## E. DIAGRAM Inventory

*Manually maintained. Auto-count: see DI row in Global Summary.*

| Diagram | Location | Description |
|---------|----------|-------------|
| Routing Flowchart | Routing Page | Decision-tree: A–G routing to bucket or section |
| Posture & Eye Exercise | Bucket 0, Strategy 4 | Line-drawing: neck rolls, shoulder shrugs, wrist rotations, palming |

---

## F. NEEDS HUMAN DECISION

*Items where text could not cleanly fit a component convention. Manually reviewed by Pranav.*

| # | Location | Issue |
|---|----------|-------|
| 1 | Document header | `### Working Master Draft` H3 as doc-level subtitle. Decide: keep or move to metadata block. |
| 2 | Routing Page | Opening blockquote with non-standard bold marker. Candidate for NOTE: or CALLOUT: component. |
| 3 | Bucket 0 intro | Two anonymous blockquotes, no standard marker. Could be PT or a new PREMISE: component. |
| 4 | Bucket 1, Strategy 4 | `> **Note on the example:**` editorial blockquote. Candidate for WARNING or NOTE: type. |
| 5 | Bucket 1, Strategy 5 | 3-question filter blockquote. Candidate for DECISION FILTER: or RULE: component. |
| 6 | Bucket 0, DAILY TICK | Bare `- [ ]` list, no component wrapper. Candidate for FILL-IN or DAILY CHECKLIST:. |
| 7 | Bucket 3 S10; Bucket 5 S17 | PT blockquotes with [STRUCTURE ONLY] — awaiting author writing. |
| 8 | Bucket 5, Strategy 8 | Inline [AUTHOR TO CONFIRM] flag — not in a component. Candidate for PT placeholder. |
| 9 | Bucket 1 S9; Bucket 6A S2 | Strategy text references fill-in forms without FI marker at the reference point. |
| 10 | AI Section, final paragraph | Bold caution about AI misuse — candidate for WARNING component. |

---

## G. UNTAGGED Patterns

*Recurring patterns without a matching component type. For Pranav's decision.*

### 1. Code-fenced structured content (~18 occurrences)
Data tables, format templates, step schedules — all in triple-backtick blocks. Three sub-types:
- **Data table / planning grid** — e.g. B1 S4 reverse-planning calendar, hours table
- **Format template** — e.g. B2 S15 error entry format, register header
- **Step schedule** — e.g. B4 S5 mock-analysis four questions; Emergency 10-day schedule

Candidate: `TEMPLATE:`, `SCHEDULE:`, `FORMAT:` — or one umbrella `STRUCTURE:`.

### 2. Inline [REF: …] tags (2 occurrences)
`[REF: AI Section]` in B0 S2 · `[REF: Bucket 0]` in B4 S9. Candidate: `SEE ALSO:` or inline `→` convention.

### 3. [STRUCTURE ONLY — …] blocks (10+ occurrences)
Placeholders across FRONT MATTER, PT slots, Author's Journey. Parser treats as non-content.
"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if not MASTER.exists():
        print(f"ERROR: MASTER.md not found at {MASTER}")
        raise SystemExit(1)

    text, sections = parse(MASTER)
    today   = date.today().isoformat()
    n_lines = len(text.splitlines())
    md5     = hashlib.md5(text.encode()).hexdigest()[:8]

    # Preserve manually-maintained sections from existing index (if any)
    manual = DEFAULT_MANUAL
    if INDEX_OUT.exists():
        existing = INDEX_OUT.read_text(encoding="utf-8")
        if SENTINEL in existing:
            tail = existing.split(SENTINEL, 1)[1].strip()
            if tail:
                manual = tail

    bucket_secs = [s for s in sections if s.is_bucket]

    out: list = [
        "# MASTER Component Index",
        "## CA-Inter-Strategy-Book-MASTER.md",
        "",
        f"Generated: {today}  ·  `tools/generate_component_index.py`",
        f"Source: `books/strategy-book/working/CA-Inter-Strategy-Book-MASTER.md`",
        f"Lines: {n_lines}  ·  MD5: `{md5}`",
        "",
        "---",
        "",
        "## Reference Code System",
        "",
        "| Code | Meaning | Example |",
        "|------|---------|---------|",
        "| `ASG.B.S` | All Strategy, Bucket B, position S | `ASG.0.4` = Move Your Body |",
        "| `RSG.B.S` | Rank Strategy, Bucket B, position S | `RSG.3.11` = Rate Your Chapters |",
        "| `IF.B.S` | Implementation Framework inside that strategy | `IF.4.1` = Build Layer 3 framework |",
        "| `PT.B.S` | Pranav's Tip inside that strategy | `PT.1.6` = Drive subfolder structure |",
        "| Bucket codes | 0–5, 6A (Track A), 6B (Track B), E (Emergency) | `ASG.6A.3` · `IF.E.2` |",
        "",
        "---",
        "",
        "## A. Bucket + Emergency Sections",
        "",
        "> Key: ✓ = one occurrence · (2) = two · — = absent",
        "> **IF** = IMPLEMENTATION FRAMEWORK · **PT** = PRANAV'S TIP · **HTD** = HOW TO DO THIS",
        "> **SL** = STARTING LATE? BARE MINIMUM · **EG** = END GOAL · **RO** = RANK ONLY · **WA** = WARNING",
        "",
    ]

    for sec in bucket_secs:
        strats = sec.strategies
        n_all  = sum(1 for s in strats if s.tag == "ALL")
        n_rank = sum(1 for s in strats if s.tag == "RANK")
        tag_str = f"{n_all} × [ALL]" + (f", {n_rank} × [RANK]" if n_rank else "")
        out.append(f"### {sec.name}")
        out.append(f"*({tag_str})*")
        out.append("")
        out.append(_bucket_table(strats))

    out += [
        "---",
        "",
        "## B. Non-Bucket Sections",
        "",
        _non_bucket_table(sections),
        "---",
        "",
        "## C. Global Summary",
        "",
        _global_summary(sections),
        "---",
        "",
        SENTINEL,
        "",
        manual,
    ]

    INDEX_OUT.write_text("\n".join(out), encoding="utf-8")

    # Verification printout
    all_strats = [s for sec in sections for s in sec.strategies]
    n_if = sum(s.comps.get("IF", 0) for s in all_strats)
    n_pt = sum(s.comps.get("PT", 0) for s in all_strats)
    n_s  = len(all_strats)
    n_r  = sum(1 for s in all_strats if s.tag == "RANK")
    print(f"OK  {INDEX_OUT.name} regenerated")
    print(f"    Strategies : {n_s}  ({n_s - n_r} × [ALL], {n_r} × [RANK])")
    print(f"    IF blocks  : {n_if}  |  PT blocks : {n_pt}")
    print(f"    Lines      : {n_lines}  |  MD5 : {md5}")


if __name__ == "__main__":
    main()
