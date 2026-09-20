# Strategy Book — Design Specification (v1)

**Status:** Locked decisions from Pranav (2026-06-10): full-colour interior · B5 (7"×10") trim · diagram ownership decided per-diagram later · spec first, sample chapter later.
**Scope:** Visual design system for *The Comprehensive CA Intermediate Exam Preparation Guide* (Pillar 1). Content lives in `working/CA-Inter-Strategy-Book-MASTER.md`; this file governs only how it looks on the page.

---

## 1. Design intent

One question answered on every page: **"Where am I in the journey, and what do I do here?"**

- The reader is 17–19, short attention span, possibly in panic mode. The book must be navigable in seconds with the book *closed*.
- The book is a **workbook the student writes in** — fill-in forms, tick-boxes, margin space. A written-in book gets re-opened.
- Visual grammar is fixed: every recurring component has exactly ONE look, learned once, recognised forever.
- Tone of the design matches the voice: clean, confident, warm — not corporate, not childish, no clip-art.

---

## 2. Page geometry (B5, 7"×10")

| Property | Value |
|---|---|
| Trim size | 177.8 × 254 mm (7" × 10") |
| Bleed | 3 mm all sides (required for edge tabs) |
| Inner (binding) margin | 22 mm |
| Outer margin | 25 mm (room for bleed tabs + student pencil notes) |
| Top margin | 20 mm (header sits at 12 mm) |
| Bottom margin | 24 mm (footer + journey strip at 14 mm) |
| Text column | single column, ≈ 130 mm wide |
| Body type | 10.5 pt / 16 pt leading |
| Max paragraph length | ~6 lines — break or box anything longer |

---

## 3. Section colour system

Calm → intense as exams approach; calm again after. Emergency is signal-red and findable with the book shut.

| Section | Colour | Hex | Logic |
|---|---|---|---|
| Bucket 0 — Foundation | Slate | `#5C6B7A` | Neutral base; runs beneath everything |
| Bucket 1 — Before the Journey | Teal | `#0E7C7B` | Fresh start |
| Bucket 2 — While Taking Classes | Green | `#2E8B57` | Growth |
| Bucket 3 — Revision Phase | Mustard | `#E8A13D` | Heat building |
| Bucket 4 — 45 Days Before | Orange | `#E07A2F` | Urgency |
| Bucket 5 — The 15 Exam Days | Maroon | `#8E2C3A` | Peak intensity |
| Bucket 6 — After Exam → Result | Sky blue | `#4A90C4` | Exhale |
| AI Section | Violet | `#6C4FB8` | Different species of content |
| Emergency — 10 Days Left | Signal red | `#E03131` | Panic-findable |
| RANK accent (global) | Gold | `#C9A227` | Used ONLY for ranker content |
| Ink / body text | Near-black | `#1F2933` | Softer than pure black |
| Grey box fill | Light grey | `#EEF1F4` | Bare-Minimum boxes |

Each section colour is used at three tints: 100% (tabs, headings, edge strip), ~15% (box fills), ~40% (rules/borders).

---

## 4. Edge tabs + "you are here" system

**Stepped bleed tabs (right-hand pages, outer edge).**
- Tab: 10 mm wide × 22 mm tall, section colour at 100%, bleeds 3 mm off-trim. White label: bucket number (large) + short name (small, rotated 90°).
- Nine vertical slots (B0, B1, B2, B3, B4, B5, B6, AI, EMG) stepped top-to-bottom between 40 mm and 225 mm from trim top. Every page of a section carries its tab in its slot → the closed book shows a stepped fore-edge index.
- **Emergency section additionally gets a full-height red edge strip** (not just the tab) — the panic reader finds it instantly.

**Running header.**
- Verso (left page): book title, small caps, grey.
- Recto (right page): current bucket name in section colour · current strategy title in ink.
- Hairline rule beneath, in section colour at 40%.

**Footer with journey strip (every page).**
- Centre: a mini timeline — nine small segments `0 1 2 3 4 5 6 AI EMG`; the current section's segment is filled in its colour, the rest are 15% grey. This is the persistent "you are here" map.
- Page number outside-aligned, in section colour.
- Bucket 0's "runs beneath everything" nature: inside Buckets 1–6, the `0` segment of the strip stays half-filled slate — a quiet reminder the foundation never switches off.

---

## 5. Section opener (2-page spread, every bucket)

| Left page (verso) | Right page (recto) |
|---|---|
| Full-bleed section colour. Huge bucket number (≈ 300 pt, white). Bucket name + timeframe line ("45 days before exam"). Journey timeline diagram with this bucket highlighted. | **End Goal of This Bucket** box (top). **Ranker version** line with gold ★. **Grey box:** "Starting Late or Falling Behind? Bare Minimum to Continue" — same position in every opener. Mini-TOC of the bucket's strategies with page numbers. |

One glance at the spread = full briefing for the phase.

---

## 6. Component library (fixed identity — never improvise)

| # | Component | Visual treatment |
|---|---|---|
| 1 | **Strategy heading** | Number in a section-colour circle + title + scope badge `[ALL]` (ink outline pill) or `[RANK ★]` (gold pill). |
| 2 | **How to Do This** | The book's signature block. White box, 2 pt section-colour left border, gear/checklist icon, numbered steps with printed tick-boxes ☐ the student can tick. Every strategy has one — if it can't, the strategy is gyaan and shouldn't be in the book. |
| 3 | **Author Says** | Section-colour 15% tinted box, rounded corners, small circular author avatar top-left, text set in the handwritten accent font. Reads like a voice note, not a quotation. |
| 4 | **RANK insert** | Inline paragraph/box with thin gold left border + ★. Gold is reserved exclusively for this. |
| 5 | **Bare Minimum (late-starter)** | Grey box `#EEF1F4`, dashed border, clock icon. Openers only + Emergency section. |
| 6 | **Warning / common mistake** | Red-tint strip, ⚠ icon, 1–3 lines max (mnemonic conflicts, OMR domino, etc.). |
| 7 | **Closing checklist** ("By the end of this bucket…") | Full page, large tick-boxes, rank items starred gold. Designed to be physically ticked. |
| 8 | **Fill-in forms** | Ruled lines / tables printed as real stationery: 1 boundary page per subject, Dream Marksheet, Vision Board page, reverse-planning calendars, Personal Pages, exam-kit checklist. Generous box sizes — pen-friendly, not decorative. |
| 9 | **Routing page** | Full-page flowchart (see diagrams). Answer 2–3 questions → arrow to your bucket + page number. |
| 10 | **Track A / Track B (Bucket 6)** | Two parallel colour-coded columns/lanes; reader follows one lane only. |
| 11 | **Pull-quote** | Rare. One per bucket max, section colour, large, used to break long runs of strategies. |

**Icon set:** one consistent line-icon family (single stroke weight, rounded). No emoji in print, no mixed icon styles.

**Legend page:** "How to Read This Book" (front matter) gets a half-page visual legend showing components 1–8 at small scale — teaches the grammar once.

---

## 7. Typography

| Role | Face | Notes |
|---|---|---|
| Headings / tabs / numbers | **Archivo** (or Manrope) | Confident, geometric, free (Google Fonts), heavy weights available |
| Body | **Source Sans 3** | Highly readable at 10.5 pt, handles Hinglish-in-Latin naturally |
| Author Says + photo captions | **Kalam** | Handwritten feel, supports Latin AND Devanagari |
| Gita shloka / Devanagari passages | **Noto Serif Devanagari** | Dignified, pairs with the above |

Rules: sentence case for headings (no SHOUTING except bucket numbers); bold for emphasis, never underline; em-dash and box, not parentheses, for asides.

---

## 8. Diagram inventory (Excalidraw; ownership decided per-diagram later)

`.excalidraw` source files = JSON text → **committed** to `design/diagrams/`. PNG/exports = binary → local only (gitignored), consistent with repo rules.

| Pri | Diagram | Lives in |
|---|---|---|
| 1 | Routing flowchart — "Where are you right now?" → your bucket | Routing page |
| 2 | 3-Layer Study Architecture — compression funnel L1→L2→L3 | Bucket 2 intro |
| 3 | Journey timeline — Buckets 1–6 on a line, Bucket 0 as ribbon beneath | How to Read + every opener (small) |
| 4 | Boundary diagram — MIN / MAX / RANKER nested zones | Bucket 1, Fix Your Boundary |
| 5 | Reverse-planning calendars — RANK + PASS timelines back from exam day | Bucket 1, Strategy 4 |
| 6 | Notebook numbering — spines P01-001, P01-002, insertions 1A/1B | Bucket 1, Strategy 7 |
| 7 | Sample filled Error Register entry (handwritten look) | Bucket 2, Strategy 15 |
| 8 | Second Space phone — before/after home screens | Bucket 0, Strategy 1 |
| 9 | Mock test + analysis cycle loop | Bucket 4, Strategy 5 |
| 10 | A4 sheet taping method — cello tape one side only | Bucket 3, Paste It Where You Live |
| 11 | Exam-hall mechanics — supplement "1+2" count, tick-attempted-box | Bucket 5, Inside the Hall |

No other diagrams without explicit decision (repo rule: no diagrams unless asked).

---

## 9. Production pipeline

1. Content stays canonical in `working/CA-Inter-Strategy-Book-MASTER.md`.
2. Book is built as **HTML + print CSS** (repo rule: HTML for books) in `design/templates/` → one HTML per section, shared stylesheet implementing this spec.
3. **Paged.js** renders headers, footers, journey strip, bleed tabs, page numbers → print-ready PDF (B5 + 3 mm bleed, fonts embedded; final press PDF conversion to CMYK at print stage).
4. Build order (when triggered): design tokens/CSS → one sample section → Pranav review on the *printed* page (tabs and tints behave differently on paper) → lock → roll out all sections → diagrams merged as they're approved.
5. Fonts: all Google Fonts (free for commercial print embedding).

## 10. Folder layout (this directory)

```
design/
├── design-spec.md        ← this file (source of truth)
├── diagrams/             ← .excalidraw JSON sources (committed); exports local-only
└── templates/            ← HTML/CSS book templates (when build phase starts)
```

## 11. Open items

- Cover design — separate brief, not covered here.
- Photo gallery treatment (real photos = binary, local-only) — layout spec when photos are selected.
- Print vendor constraints (paper GSM, binding, tab bleed tolerance) may force tab-width tweaks — revisit after a vendor quote.
- Per-diagram ownership (Claude-drafts vs Pranav-draws) — decide when each diagram is started.
