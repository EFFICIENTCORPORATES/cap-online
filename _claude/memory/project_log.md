# Project Log — cap-online

A running status note. Newest entries at the top. One short block per session.

---

## 2026-06-22 — CA Foundation strategy slides + HTML-to-PDF skill

Created `books/strategy-book/working/exam-strategyFoundation.html` (7-slide interactive dark-background presentation with beat-wise JS animation engine for CA Foundation Sep 2026 batch). Generated `exam-strategyFoundation-print.html` (static print copy, mm/pt sizing, all content visible) and `exam-strategyFoundation.pdf` (7 pages, 150 KB, A4 landscape) via Chrome headless.

Converted `books/concept-book/chapters/seq04-as02-valuation-of-inventories.html` to PDF (16 pages, 595 KB, A4 portrait). Added `print-color-adjust: exact` to source `*` rule; used Edge + `--virtual-time-budget=15000` because Chrome headless failed silently on Google Fonts.

Created `_claude/skills/SKILL-html-to-pdf.md` — full 8-section skill with two worked examples (slides vs. chapter), documenting the Chrome-vs-Edge decision, `--virtual-time-budget` flag, `--no-margins` usage, and the "no separate print file needed when source already has @media print" pattern.

---

## 2026-06-22 - Parsed question-bank pilot created

Created ooks/question-bank/Parsed_PDF_Question_Bank_CA_Inter_Accounts/ with one parsed MTP, one parsed RTP, one parsed PYQ, and a README. Outputs remain .md files with HTML table blocks for ruled accounting layouts. Ran python tools/health_check.py (17 pre-existing failures remain) and python tools/file_index.py (417 files indexed).

---

## 2026-06-22 - Question-bank markdown parseability sampling

Inspected ooks/question-bank/README.md, question_bank_index.csv, and sampled MTP/RTP/PYQ markdown files under ooks/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/. Confirmed raw OCR markdown is parseable with a custom rule-based parser, but needs cleanup rules for page numbers, table fragments, front-matter announcements, and embedded suggested answers in RTP files.

---

## 2026-06-22 - Orientation read: CLAUDE.md + project context reviewed

Read AGENTS.md, README.md, CLAUDE.md, and the _claude/memory/ context to understand the cap-online ecosystem. Ran python tools/health_check.py; it reported existing missing expected folders, NUL-byte text files in bridge-course/question-bank sources, and undocumented top-level capranav_com/. No content files changed beyond this log note.

---

## 2026-06-19 — AS02.dc.html animation: 4 fixes applied + local React bundled

Applied all 4 agreed fixes to `books/concept-book/characters/animations/AS02.dc.html`:

1. **Narrator position**: `top:332` → `bottom:90` (subtitle band, no longer overlaps characters)
2. **Pranav walk animation**: Added `asEnter` keyframe (slide in from right); changed his Scene 4 beat pose from `'walk'` (bounce) to `'enter'`
3. **Jump-to-scene menu**: `≡` button top-left opens an overlay listing all 12 scenes; click to jump; ESC or click-away to close; click-to-advance blocked while menu is open
4. **Local React**: Downloaded React 18.3.1 UMD as `react.min.js` + `react-dom.min.js` into animations folder; added `<script>` tags before `support.js` in all 3 `.dc.html` files (AS02, universe-intro, Character Universe) — zero CDN dependency at runtime

All changes committed locally. Pranav to `git push origin main` from his machine.

---

## 2026-06-17 — AS 2 Concept Book chapter: HTML print version complete

Created `books/concept-book/chapters/seq04-as02-valuation-of-inventories.html` — print-ready A4 HTML for the AS 2 Concept Book chapter. Self-contained file (Google Fonts CDN, all CSS inline).

Design: 7 pages — (1) cover (navy gradient, watermark AS2, gold-orange accent bar, badges), (2) story "Godown Ka Hisaab", (3–5) Layer 2 concept notes [AS2-1.2] to [AS2-1.15], (6) Illustration Guide, (7) TYK Guide + Layer 3. Color system: Story = orange border on warm cream; Kaam Ki Baat = green border on mint; Story Reference = purple border on lavender; Exam Note = red border on light red; Layer 3 = dark navy background with orange numbered circles. Print: @page A4, position:fixed header/footer repeating on each printed page. Fonts: Poppins (headings/badges), Merriweather (story prose), Lato (body).

All 4 Kaam Ki Baat boxes, 3 Story References, and Exam Notes from the MD chapter are fully reproduced in the HTML.

---

## 2026-06-17 — final-deliverables: 02A and 03A light versions created

Continuation session (context exhausted in previous turn). Tasks from previous session pending were:

1. `final-deliverables/02A-batch-day-wise-planner-light.md` — lighter version of 02. Stripped Kahaani/Koncept/Karma narrative from Day Focus column; removed Notes column. Kept all 97 rows, 6 phase headers, chapter tests, ITD tests, holiday markers. Day Focus is now just topic/subtopic name (e.g. "Why AS exist; ASB formation; 8-step standard setting; benefits and limitations"). Phase summary table retained at bottom.

2. `final-deliverables/03A-bridge-course-skeleton-light.md` — lighter version of 03. Removed all Kahaani narration (story beats, dialogues, Arjun/bus scenes). Kept: time budget tables for both sessions, Kahaani slot with just the anchor concept (blood report metaphor / why rules exist), full Koncept topic list in sequence, all Karma items (MCQ topics + illustration details), Layer 3 one-liners, vision close content list. 1.5 hrs × 2 session format maintained.

3. `final-deliverables/` folder documented in CLAUDE.md section 3 and README.md (folder map + Where things are table). This was overdue from when the folder was created last session.

4. `file_index.py` run: 326 files. `generate_component_index.py` run (regenerated). `health_check.py`: 22 pre-existing failures — 12 missing gitignored/local folders, 9 NUL-byte OCR files from last session's base-studymaterials, 1 component-index CRLF/LF hash mismatch (systematic tooling bug — generator hashes text, health_check hashes raw bytes on Windows). No new failures from this session's work.

---

## 2026-06-15 — teaching_sequence.md: ALL 10 chapters complete

Multi-session task concluded. Built `books/bridge-course/teaching_sequence.md` — 7-column table (CA Level | Chapter No. | Unit No. + Unit Name | Topic/SubTopic ID | Topic Name | Page No. | One-Line Summary) from all 10 base-studymaterial OCR files.

This session (continuation): CA Inter Chapter 2 (24 rows) + CA Inter Chapter 3 (9 rows) appended.

- Ch3 sections: 1 (Status of AS), 2 (Applicability intro), 2.1 (MSME/Large criteria, effective 1 Apr 2024), 2.1-Illus (Example 1), 2.3 (Companies), 2.3.1 (20 AS in entirety), 2.3.2 (SMC exemptions), UNTSMRY, TYK (ranking: 2.1 \ 1)
- Full file: header + Foundation Units 1–7 + Inter Ch1 (16 rows) + Inter Ch2 (24 rows) + Inter Ch3 (9 rows)
- `file_index.py` run (116 files); `health_check.py` 15 pre-existing failures only (same as before — not caused by this work)

---

## 2026-06-15 — Bridge Course Topics to cover.md — full final rewrite completed

Continuation session (prior context was exhausted mid-task). Wrote the complete final version of `books/bridge-course/Topics to cover.md` covering ALL source chapters:
- Foundation Ch1 Units 1–7: every numbered sub-topic, all illustrations with concept-test note, Summary, TYK with sub-topic IDs
- Inter Ch1 (Intro to AS): all 14 sections including 8-step process, IFRS components, carve outs/ins, Ind AS roadmap for all 4 entity categories
- Inter Ch2 (Framework): all 11 sections — 8 elements of the Framework, 7 user groups, 3 fundamental assumptions, 4 qualitative characteristics + sub-qualities, 5 elements (formal definitions), 4 measurement bases, all 3 capital maintenance concepts; all illustrations/examples with concept-test notes
- Inter Ch3 (Applicability): Status, 3-question test, ICDS (10 standards), MSME vs Large entity revised criteria (Aug 2024), SMC vs Non-SMC exemptions; all MCQs with sub-topic IDs, case scenarios
- Ran `file_index.py` (116 files); `health_check.py` shows 15 pre-existing failures only (no new issues)

---

## 2026-06-15 — Bridge Course Layer 2 revision map written

Created `books/bridge-course/Topics to cover.md` — point-wise, topic-wise raw concept summary of all source chapters:

- **CA Foundation Ch1 Units 1, 2, 5, 6, 7:** 6-step accounting cycle, evolution (Egypt → Pacioli), objectives, functions, book-keeping vs accounting, sub-fields, users, disciplines; all 12 GAAPs with key pointer each; 3 Fundamental Assumptions; Accounting Policies (selection + change); 4 Valuation Bases + Accounting Estimates; AS objectives, benefits, limitations, ASB process (8 steps), 3 sets of standards, AS 1-29 full list, key Ind AS list
- **CA Inter Ch1:** GAAP at Inter depth, IFRS/IASB, Convergence vs Adoption, Ind AS, Carve-outs, Phase-wise Roadmap
- **CA Inter Ch2:** Framework (objectives, users, 4 qualitative characteristics with sub-qualities), 5 elements with formal definitions, 2 recognition criteria, 4 measurement bases, Financial vs Physical Capital Maintenance
- **CA Inter Ch3:** Status of AS, 3-question applicability test, Companies Act Sec 129/133/143, non-corporate applicability, CA's professional responsibility
- Purpose: "Layer 2 skeleton" — Pranav Sir will insert story anchors and concept teaching between these raw topics
- `file_index.py` run (116 files: 106 text, 10 local); `health_check.py` has 15 pre-existing failures (9 NUL-byte files in base-studymaterials, 5 missing gitignored folders, component-index stale) — none caused by today's work

---

## 2026-06-15 — Bridge Course master teaching document complete

Rewrote `books/bridge-course/bridge-story.md` into a full structured teaching guide:

- **3-class × 1-hour structure** with story, chapter maps, cliffhangers
- **Class 1 (Foundation):** Going Concern, Money Measurement, Matching, Consistency, Conservatism, Materiality, Accounting Policies, Valuation Bases, Why AS exist — all with blood-report / Byju's / Arjun story thread
- **Class 2 (Inter Ch 1):** GAAP, AS-setting process (ASB), IFRS/IASB, Convergence vs Adoption, Ind AS, Carve-outs, Roadmap
- **Class 3 (Inter Ch 2 + 3):** Framework (4 qualitative characteristics), Elements (formal definitions), Recognition criteria, Capital Maintenance, 3-Question Test, Companies Act Sec 129/133/143, CA's responsibility
- Every class ends with a story cliffhanger except Class 3 (which is a resolution)
- AI fear not resolved — one paragraph: focus on studies, conversation for later
- Ran `file_index.py` (updated); `generate_component_index.py` (regenerated)
- `health_check.py` has 13 pre-existing failures (NUL bytes in base-studymaterials files from cross-mount edit, 5 missing gitignored folders, component-index stale) — none caused by today's work

---

## 2026-06-14 — Bridge course story written

Created `books/bridge-course/bridge-story.md` — a Chapter 0-style Hinglish dialogue story bridging CA Foundation → CA Inter. Same characters (Arjun + Pranav Bhaiya), same narrative style. Covers:

- Foundation concept recap (Entity, Dual Aspect, Accrual, Matching, Going Concern, Consistency, Conservatism)
- Why Accounting Standards exist (the 5-accountants-5-profits problem)
- What Accounting Standards are and how ICAI formulates them
- AS vs Ind AS vs IFRS — India's convergence journey
- Framework for financial statements (Reliable, Relevant, Comparable, Understandable)

Setting: Arjun receives his Foundation result (passed), calls Pranav Bhaiya, conversation bridges him into the Inter level. Content is ICAI curriculum-accurate throughout.

---

## 2026-06-13 — Working tree cleanup: 4-block atomic commit plan completed

Resumed from previous context (session ran out). Committed remaining 2 blocks:

- **Block 3** (`a6b3e18`): CLAUDE.md + content/README.md — documented `productions/` folder in both files
- **Block 4** (this entry): file-index regeneration + project log

**Sep26-strategy relocation** (done in prior session, committed as Block 1):
All 14 old paths under `books/strategy-book/video-presentations/sep26-strategy/` moved to `content/productions/sep26-strategy/deck/`. Git detected renames correctly.

**Pending decision (Pranav):** `content/assets/green-screen/book-cover-image-base-64.txt` — 573KB base64-encoded PNG. Used by `book-promo.html` for self-containment. Per "no binary files in git" rule, recommend adding to `.gitignore`. If Pranav wants it committed, can do so explicitly.

**Pending tasks:**
- Add `--input` flag to `tools/strategy_book_parser.py` so it can process `CA-Inter-90-Days-Strategy.md` (currently defaults to MASTER.md only)
- Generate 90-day book HTML → PDF once `--input` flag added

---

## 2026-06-11 — AI section expanded + parser table support added

**MASTER.md — THE AI SECTION:** Added 3 new sub-sections after the existing 7 use-cases:
- **TOOL PICKER** — markdown table: 10 rows mapping task → best tool → why (NotebookLM, Claude, Perplexity, ChatGPT, Sarvam/Gemini, KIMI)
- **OUTPUT FORMAT** — HTML vs MD vs PDF guidance with ready-to-use prompts; explains token cost of scanned PDFs
- **TOKEN MINIMIZATION** — 6 numbered habits for free-plan users + PRANAV'S TIP (compact MD summary habit)

**Parser (`tools/strategy_book_parser.py`) — markdown table support added:**
- Tokenizer: detects `|`-prefixed lines, parses header/separator/data rows → `{'type': 'table'}` token
- Renderer: `_table()` method → `<table class="content-table">` with thead/tbody
- `_component_body()`: table token wired in (tables inside components work too)
- CSS: `.content-table` / `.table-wrap` — zebra-striped, uppercase headers, border-collapse

Verified: parser renders AI section cleanly; all 7 checks pass (content-table, NotebookLM, headings, HOW TO DO THIS, PRANAV'S TIP, handwritten class, file size 20KB). health_check green (47/47, MD5: 5805c527).

---

## 2026-06-11 — CA-Inter-90-Days-Strategy.md fully rewritten, HTML-synced

Complete rewrite of `books/strategy-book/working/CA-Inter-90-Days-Strategy.md`.
Now fully in sync with the sep26-strategy HTML slide deck and standalone as an
independent book.

**Structure:** FRONT MATTER (Title, Copyright, Dedication, Socrates Story, About
the Author, About This Book, How to Read) → ROUTING PAGE → BUCKET 3 (Phase 1:
Build Your Arsenal, 18 strategies) → BUCKET 4 (Phase 2: Delivery Mode, 10
strategies) → BUCKET 5 (The 15 Days, 17 strategies) → BUCKET 0 (Daily
Foundation, 13 strategies + Discipline Bridge) → PERSONAL PAGES → AUTHOR'S STORY.

**Sync gaps closed vs slides:**
- Booti 3: "Paste It Where You Live" → "The Visual Vault" (Flowcharts / Tables
  & Formats / Skeletons / Dates·Rates·Limits / Mnemonics); paste-it is now the
  usage rule, not the name
- Level 1 gate: 3-check system (Boundary written + Layer 1&2 documented + 3
  Bootis) → LEVEL 1 CLEARED → NO NEW MATERIAL
- Mock Analysis Protocol: routing decision tree (recall-fail → Visual Vault;
  didn't-know-in-Boundary → Golden Nuggets; outside Boundary → decide)
- Discipline Bridge: before Bucket 0 — "CA is game of PREPARATION not talent"
  + Atomic Habits framing
- Student Toolkit promise (20+ tools, comment guarantee)
- "ON GROUND Strategies" / "No Gyaan Baazi" language in About This Book
- North Star escalates to 3× per day in Bucket 4
- Layer 3 size: "10–40 pages per subject"
- Gamify frame: Level 1 / Final Boss (tied to Level 1 CLEARED milestone)

**Parser compliance:** Section headings map to existing SECTION_META keys
(BUCKET 3/4/5/0, FRONT MATTER, ROUTING PAGE, PERSONAL PAGES). 58 strategy
headings. 48 component markers. Health check clean.

**Stats:** ~1520 lines. Gallery skipped (per Pranav). About Author added.

---

## 2026-06-11 — Book-promo silent slide (book-promo.html) + CTA bug confirmed fixed

- **CTA stray `</div>` bug**: confirmed already fixed on disk (Pranav's edit); his local `node --check slides-part4.js` passes. Deck is now **29 slides** — Pranav added Mock Analysis Protocol (24B), Discipline Bridge (24C), and a Manifest line on the CTA; deck README still says 27 (update pending).
- **New: `books/strategy-book/video-presentations/sep26-strategy/book-promo.html`** — standalone silent promo slide for the Complete Strategy Book PDF (end of Sep-26 video, no voiceover). Floating 3D A4 book cover (dark, brand blue/green edge, gold accents, shine sweep, float + floor-shadow animation) with Pranav's photo **chroma-keyed from green-screen** (`content/assets/green-screen/Book-cover-green.png` → transparent cutout, embedded base64 — file ~386 KB, fully self-contained). Right panel: LAUNCHING SOON badge, facts (90+ strategies, **20+ frameworks** — actual count 23, Pranav chose the safe number, 30+ Pranav's Tips, 7 buckets, 3 Bootis, 17 exam-day strategies, fill-in pages), CTA "For **Jan 27 & May 27** attempts" (Pranav confirmed; original brief said Jan 26) + PRE-BOOK NOW / Early Bird / UP TO 30% OFF / link in description. 1920×1080 stage, auto-scales to window.
- **Note**: the base64-embedded image makes this HTML a ~386 KB blob in git — Pranav to decide: commit as-is or gitignore it.
- Sandbox health_check: known stale-mount false flags (slides.js, parser, video-brief) + **component-index STALE (MASTER.md changed: 86bb07d8 → efdc37ad)** — Pranav to run `python tools/generate_component_index.py` + health_check locally. file_index regenerated (200 files).

## 2026-06-09 — reconcile Pranav's edits + new spaces (Session: setup, cont.)

- Confirmed Pranav's build-out: strategy-book `sources/ design/ working/ video-presentations/`, new tools (`generate_component_index.py`, `strategy_book_parser.py`), component-index MD5 check in health_check, segment-library + standup material in `preparations/`, all motivation images moved to `obs-setup/assets/` (content/motivation now a daily-quote media library, kept).
- Fixed typo `sources/extermal` → `sources/external`; added `.txt` to Report 4 & 5 (external strategy research from YouTube etc.).
- New top-level **`student-toolkit/`** (separate from telegram bots) — moved `Exam Preparation date calculator.xlsx` there.
- Dedupe: removed 6 redundant strategy copies from `_claude/` (book is single source of truth); concept-book material stays in `_claude/` until it gets its own home.
- Placed syllabus master `CA-Inter-Adv-Accounts-Syllabus-TEACHER-COPY.xlsx` → `syllabus-engine/data/` (4 sheets: chapter categorize, topics+subtopics w/ unique topic IDs, combined syllabus, ICAI topics).
- Registered `student-toolkit` in CLAUDE.md + health_check EXPECTED_DIRS.
- health_check encoding guard flagged sandbox-corrupted reads of `strategy_book_parser.py` (NULs) and `slides.js` (truncated) — disk copies intact; commit from Pranav's machine. Component-index stale → run `generate_component_index.py`.

## 2026-06-11 — Deck: Mock Analysis Protocol + Discipline bridge slides (Pranav's 2nd pass)

- **New slide "Mock Analysis Protocol"** (after Mock Window): analysis TURANT mock ke baad (khud ya siblings/friend se checkwao) + routing — knew-but-no-recall → Visual Vault · didn't-know-but-in-Boundary → Golden Nuggets · chapter-not-in-Boundary → decide; if added → must also go in Layer 3 + revision material.
- **New slide "Discipline bridge"** (cushion before Bucket 0, was abrupt): "Tough? Impossible?" → "CA is a game of PREPARATION, not talent" → discipline ≠ quick motivation / week's josh / Monday flame → unwavering commitment → ATOMIC HABITS, 21 din = habit, "buffer aaj bhi hai. Go."
- Deck now 29 slides. Fixed stray `</div>` in CTA (from Pranav's manual edit; wording kept). Pranav's wording edits this pass retained: "This entire PPT discussion — FREE PDF", manifest line, "Exam ke 15 days ki strategy".
- Clarified for Pranav: "Error Register ka ek full pass" = one complete start-to-finish sweep of every logged error before exams.
- Commit still Pranav-side (sandbox stale-view issue).

---

## 2026-06-11 — Deck review tweaks (Pranav's pass) + commit deferred to Pranav

- Pranav reviewed full deck. Changes: visible **"↺ RESET" button** on Subject Slider Board (R key kept as backup); **Booti 3 renamed "The Visual Vault"** (Pranav picked from options) — contents now Flowcharts / Tables & Formats / Skeletons / Dates·Rates·Limits / Mnemonics, paste-it-where-you-live kept as the usage rule; AI slide synced ("printable visual sheets — Visual Vault ke liye"); **15 JULY slide now gates LEVEL 1 CLEARED on 3 checks** — Boundary written (har subject/chapter) + Anchor Material & Layer 1–2 ready/documented (physical ya digital) + 3 Bootis — then "Tab — aur sirf tab — LEVEL 1 CLEARED".
- Pranav edits this session: "ON GROUND Strategies" wording, Layer 3 "Around 10-40 pages", toolkit line "This is where I'll help".
- **OPEN: Booti 3 rename in `CA-Inter-90-Days-Strategy.md`** (book still says "Paste It Where You Live") — Pranav to decide.
- **Git: NOT committed from sandbox** — sandbox mount serves stale/truncated views of files edited this session; a sandbox commit would store corrupted blobs. Pranav commits from his machine (`git add -A && git commit`). His local health_check is the authoritative check this session.

## 2026-06-11 — Fixes: .handwritten class + 90-day book AUTHOR SAYS rename + MASTER trailing space

**Fix 1:** `tools/strategy_book_parser.py` PRANAV'S TIP renderer — `comp-body` → `comp-body handwritten` (`.handwritten` CSS was orphaned after AUTHOR SAYS removal; this wires it back in).
**Fix 2:** `CA-Inter-90-Days-Strategy.md` — all 10 `> **AUTHOR SAYS:**` → `> **PRANAV'S TIP:**` (90-day guide had not been updated in the earlier rename pass).
**Cleanup:** MASTER.md line 1 trailing space (test artifact from staleness-test) removed. Component index regenerated (clean MD5: `86bb07d8`). All health checks green (46/46, encodings OK, index in sync).

---

## 2026-06-11 — AUTHOR SAYS → PRANAV'S TIP rename + component index automation

**MASTER.md:** All 30 occurrences of `> **AUTHOR SAYS:**` renamed to `> **PRANAV'S TIP:**` (branding — student reads Pranav's name on every tip block). PT total now 33 (30 former AS + 3 original PT), IF = 22.

**Reference code system designed and implemented:**
- `ASG.B.S` = All Strategy, Bucket B, strategy S (e.g., `ASG.0.4` = Move Your Body)
- `RSG.B.S` = Rank Strategy (e.g., `RSG.3.11` = Rate Your Chapters; only 2 RANK strategies exist, both in B3)
- `IF.B.S` / `PT.B.S` = component inside that strategy
- Bucket 6 → `6A` (Track A, passed) and `6B` (Track B, failed/retaking)
- Emergency → `E`

**New tool: `tools/generate_component_index.py`** — auto-generates MASTER-component-index.md from MASTER.md. Writes MD5 of MASTER.md into index header. Run after any MASTER.md edit.

**health_check.py updated:** Check 5 added — compares stored MD5 in index to current MASTER.md; fails with regeneration instructions if stale.

**strategy_book_parser.py updated:** Removed `AUTHOR SAYS` from COMPONENT_MARKERS; `PRANAV'S TIP` handler (`.pran-tip` CSS class) already existed and handles all PT blocks.

All checks green (46/46 folders, encodings clean, component index in sync, MD5: `86bb07d8`).

---

## 2026-06-11 — Sep-26 video slide deck COMPLETE: all 27 slides (Phases 1–4)

- Major restructure per Pranav after first-3-slides review: **15th July** (not 25th) = B4 start/Level-Up/No-New-Material date (Pranav's buffer choice; exact 45-days-before-1-Sep is 18 Jul — flagged, he chose 15th; slides say "45+ days"). Exams 1–12 Sep. Bilingual headings everywhere (EN + Devanagari). Brand chrome = DISC blue/green; bucket colours from design-spec; gold = Bootis only.
- **Phase 1**: slide chrome in engine (bilingual header + live days chip, footer journey strip w/ proportional buckets + B0 band, watermark "CA Pranav P Tulshyan"), Gita Shlok opener (2.47), Reality Check title, Bucket Analysis proportional timeline (B1 8% / B2 34% / B3 22% / B4 16% / B5 7% / B6 13%; markers AAJ · 15 JULY pulsing · 1 SEP · 12 SEP; B0 band beneath). Approved by Pranav.
- **Phases 2–4** (new files, additive architecture): `js/slides-part2/3/4.js` (SLIDES.push), `js/engine-extras.js`, `css/parts.css`. Slides: interactive **Subject Slider Board** (6 draggable markers on bucket-gradient tracks, B4 goal line at 64%, LEVEL 1 CLEARED badge when all ≥ B4, R = reset, tap-to-jump), Mission (live days-to-15-July), Roadmap TOC, North Star (21 hours, 1×/day), Boundary + 3-question filter + NOTHING ELSE stamp, **Implementation Framework + STUDENT TOOLKIT badge** (20+ tools, comment promise), 3-Layer Architecture (fixes layers-before-explained hiccup), Drive setup, Physical vs Digital (red flash), Booti intro + 3 Booti slides (gold, field-by-field; footer booti-tracker slots fill ①②③), AI (violet, memory-machine framing), Group Decision (comfort-first formula), 15 JULY deadline (LEVEL 1 CLEARED + NO NEW MATERIAL flash), Bucket 4 rules (North Star 3×/day), Layer 3 A/B/C (60/30/10), Mock Window (min 1/max 2, deadline live-computed = exam−10 = 22 AUG), Bucket 0 tick-list, CTA ("No Gyaan Baazi. ON GROUND Strategies." — Pranav's wording).
- Verified: node --check all new JS, 27 slides, all step sequences sequential, mock date computes 22 AUG. **Known sandbox issue:** the Cowork sandbox mount pins stale sizes for re-written files (slides.js etc.) → health_check run in-sandbox false-flags UTF-8 on them; files verified complete/valid on Windows side and Pranav's local health_check runs green. New-file architecture (part files) chosen partly for this reason.
- README (deck) updated: full file map, R key, wording-edit guide. Commit locally; Pranav pushes.

---

## 2026-06-11 — Sep-26 video slide deck: engine + first 3 slides

- New folder `books/strategy-book/video-presentations/sep26-strategy/` — HTML/CSS/JS deck for the Sep-26 strategy video (per `working/video-brief-sep26-strategy.md`). Multi-file: `index.html`, `css/theme.css` (B3 #E8A13D / B4 #E07A2F tokens, dark/light themes, 1920×1080 scaled stage, reveal animations), `css/slides.css`, `js/engine.js` (vanilla-JS: →/Space/click step reveals, ←, F fullscreen, H HUD), `js/slides.js` (content-as-data, edit text without touching engine), `README.md`.
- Built slides 1–3 for Pranav's look-and-feel approval: Hook ("83 days" — **live-computed** from EXAM_DATE 2026-09-01), Pain Mirror (NEW slide approved by Pranav — 4 Hinglish pain lines + closer), Positioning ("Yeh video kya NAHI hai"). 15 slides remain (18 total).
- Decisions locked with Pranav: pain-mirror slide added; days counter auto-calculated; folder location under strategy-book. **Slide 4 redesigned per Pranav**: timeline Today → 25th July → 1st Sep; first half = fix boundary + finalize 3 Bootis, second half = pure revision & practice (to build next).
- `books/strategy-book/README.md` updated (video-presentations/ in layout + file table). Verified: node --check clean, 3 slides / 12 reveal steps, days calc = 83. health_check green (46/46); file_index 91 files. Commit locally; Pranav pushes.

---

## 2026-06-10 — Staleness check + component index corrected

Checked 6 files for staleness and contradictions: CLAUDE.md (current), README.md (current), content/README.md (current), project_log.md (current), MASTER-component-index.md (stale — fixed), CA-Inter-Book-Full-Structure.md (superseded — marked archived).

**MASTER-component-index.md corrections:**
- Added `IF = IMPLEMENTATION FRAMEWORK` to key + IF column to per-section table (B0:3, B1:2, B2:6, B3:4, B4:3, B5:3, B6:1 = 22 content blocks)
- AS counts corrected: B0 6→7, B2 9→10, B3 5→6, B4 0→2, B5 2→3 (total 20→30)
- WA counts corrected: B1 2→1, B2 1→0 (total 1 WARNING at B1 S10)
- B3 tag notation corrected: "10×[ALL], 1×[RANK], 1×[ALL], 1×[RANK]" → "11×[ALL], 2×[RANK]"
- PRANAV'S TIP corrected: 4→3 (B1 S6, B1 S10, B4 S1)
- Total strategies corrected: 94→91; [ALL] 90→89; [RANK] 4→2 (B3 S11, B3 S13)

**CA-Inter-Book-Full-Structure.md:** Added ARCHIVED DRAFT header — this file diverged from MASTER.md before the 2026-06-10 normalization pass. It is reference-only; all active work is in MASTER.md.

---

## 2026-06-10 — New file: CA-Inter-90-Days-Strategy.md (website PDF mini-book)

Created `books/strategy-book/working/CA-Inter-90-Days-Strategy.md` — complete standalone 90-day strategy book for the website PDF. Parser-compatible with `tools/strategy_book_parser.py`.

Structure: Socrates Story (STRUCTURE ONLY) → About This Book (STRUCTURE ONLY) → Routing Page → First 45 Days (Strategies 1–17: boundary, Physical vs Digital, 3 Layers, 3 Sanjeevani Bootis, revision strategies) → Next 45 Days (Strategies 1–10: Layer 3 build, No New Material, mocks, error register) → Exam: The 15 Days (Strategies 1–17: kit/logistics, reading time, hall mechanics, between-papers) → Bucket 0 — The Daily Foundation (all 13 strategies, at end) → Personal Pages (Why I Am Doing CA, Dream Marksheet, Vision Board, My Boundary, My Notes) → Author's Journey + Gallery (STRUCTURE ONLY).

Key: "21 Hours Before Exam" throughout · PRANAV'S TIP components included in Physical vs Digital and Layer 2/Layer 3 strategies · cross-refs to MASTER.md noted via [REF: …] tags · parser note at end flagging new SECTION_META slugs required (FIRST 45 DAYS, NEXT 45 DAYS, EXAM: THE 15 DAYS, THE SOCRATES STORY).

health_check green (46/46); file_index 85 files.

---

## 2026-06-10 — MASTER.md: 23 Implementation Frameworks added across all 7 Buckets

Major session — comprehensive framework layer added to the Strategy Book:

- **New parser tag `IMPLEMENTATION FRAMEWORK`** added to file header (front-cover countable element).
- **About This Book** updated: added differentiator line about implementation plans for each strategy.
- **Bucket 0**: Wake Anchor Rule (sleep), 2-Minute Park Protocol (emotions + "scientifically proven" note without names), 4-Part Target Rule (daily targets).
- **Bucket 1**: Full 2-Role Rule rewrite in Pranav's plain-language style (Understanding vs Boundary); A/B/C Classification Formula (W = avg marks, ≥5=A, ≥2=B, else C) with VC Gurukul channel reference; 3-Condition Removal Rule for boundary.
- **Bucket 2**: Layer Lock Rule (zero Layer 2 during classes); 3-Question Class Filter (what to write); 25-5 Rhythm (active recall — no scientist names); 3-Item Buddy Agenda (study buddy calls); full Sanjeevani Booti 2 Error Register format (3 entry types + 5-field error format); MCQ Quota by Category (30/15/8 with VC Gurukul platform reference).
- **Bucket 3**: Compression Time Test (Layer 2 quality check); 3-Gate Revision Standard (Notes + Test + Error); Author Says on 7-subject IPCC spacing; 3-Day Triage Protocol (recovery); Action Matrix (chapter rating → action trigger).
- **Bucket 4**: 4-Type Layer 3 Filter (only 4 content types allowed); Author Says on mnemonic pairing (Audit disaster story); Layer 3 reading time updated to 30–40 min; Decision Tree (new material vs boundary gap); Mock Sequence Rule + Author Says (sister checking immediately).
- **Bucket 5**: 4-Step Reading Time Protocol (15-min sequence); MCQ-first rationale rewritten in Pranav's style + Author Says (watch on desk); Every-5 OMR cross-check; 4-Line Fallback Protocol (never leave blank); CA Inter Time Budget (1.8 min/mark table).
- **Between Papers**: COMPLETELY REWRITTEN — Pranav's 20–22 hr study approach: 2 hrs same day + 16 hrs next day + 4 hrs exam morning. Remove completed subject materials immediately after exam.
- **Bucket 6**: 3-Column Look-Back Table (honest review after exams).
- Memory saved: `project_ca_inter_basics.md` + `feedback_ca_inter_book_rules.md`.
- Total: 23 IMPLEMENTATION FRAMEWORK blocks, 30 AUTHOR SAYS blocks, 91 strategies.
- health_check green (46/46); file_index 84 files.

---

## 2026-06-10 — MASTER.md: 7 new concepts added + PRANAV'S TIP parser component

- Added **Strategy 13 — Make It a Game** to Bucket 0 (gamify concept: learning as levels, exam as Final Boss, Princess ko bachana hai).
- Added **PRANAV'S TIP for Google Drive subfolder structure** to B1 S6 (Layer 1 / Layer 2 / Layer 3 subfolders per subject).
- Added **Strategy 10 — Physical vs Digital** to Bucket 1: what must be physical (Layer 3 always physical), what is digital, WARNING for never-digital-as-primary, PRANAV'S TIP for cloud backup + YouTube Unlisted for heavy files.
- Enhanced **Error Register format** in B2 S15 with new PRANAV'S TIP block (5 specific fields: where is Q, where is solution, what was asked, where messed up, why messed up).
- Added **Strategy 18 — The Golden Nuggets Register** to Bucket 2 (distinct from Error Register; collects per-chapter: important concepts + exam tips + examiner tricks while watching revision videos).
- Added **North Star Question framing** ("21 Hours Before Exam") to Bucket 4 intro, before Strategy 1.
- Added **Layer 3 default A→B→C sequence** as PRANAV'S TIP inside B4 Strategy 1 Build Layer 3.
- Added **PRANAV'S TIP** to `COMPONENT_MARKERS` in `tools/strategy_book_parser.py` + renderer + CSS class `.pran-tip`.
- Updated `MASTER-component-index.md`: new key PT, updated strategy counts (B0:13, B1:10, B2:18), added new strategy rows.
- health_check green (46/46); file_index 83 files.

---

## 2026-06-10 — Video planning: Sep 2026 strategy video brief

- Planning discussion for a YouTube video targeting CA Inter Sep 2026 students ("exactly what to do in the next 40 days").
- Decided format: face-to-camera primary, slides only for data-heavy blocks (timelines, templates, checklists).
- Content scope: Bucket 3-to-4 transition. Core: Boundary fixation, 3-Layer material framework, three "Sanjeevani Bootis" (Golden Nuggets register, Error Register, Paste-It-Where-You-Live), AI usage for memory, post-25th-July phase. Bucket 0 compressed to 90 seconds at end. Bucket 5 deferred to separate video.
- Positioning: "Big Brother, not topper, not faculty" — no planners, no motivation, raw strategies only.
- Created `books/strategy-book/working/video-brief-sep26-strategy.md` — full run-of-show + 6 critical flags + open decisions table for Pranav.
- health_check green (46/46); file_index 83 files.

---

## 2026-06-10 — Strategy Book: md_to_html.py converter + Bucket 0 HTML output

- Built `books/strategy-book/design/templates/md_to_html.py` — state-machine line-by-line parser that converts MASTER.md → print-ready B5 HTML implementing design-spec.md visual system. Self-contained CSS (Archivo/Source Sans 3/Kalam, Google Fonts), embedded in output HTML.
- Handles all 10 component types (AUTHOR SAYS, HOW TO DO THIS, RANK ONLY, END GOAL, STARTING LATE? BARE MINIMUM, WARNING, DIAGRAM, FILL-IN, CHECKLIST — END OF BUCKET, EXAMPLE), strategy headings (number circle + title + ALL/RANK badge), non-strategy H3s, code/template blocks, checklists (`- [ ]` + ★), anonymous blockquotes, inline REF/STRUCTURE ONLY/AUTHOR TO CONFIRM tags.
- Generated `books/strategy-book/design/templates/build/bucket-0.html` (B5 Slate theme, 26KB, 564 lines). Component counts verified against MASTER-component-index: 5 Author Says, 3 HOW TO, 1 RANK ONLY, 1 DIAGRAM, 12 strategy headings. `build/` is gitignored per existing .gitignore rule.
- Known limitation: indented continuation lines of list items (e.g., `>   move on...` below a `> - list item`) are rendered as a separate `<p>` rather than joined to the list item. Text content is preserved; only visual grouping differs.
- CLI flags: `--section "BUCKET 0"`, `--section all`, `--list-sections`, `--output <path>`.
- health_check green (46/46); file_index regenerated (76 files). Commit locally; Pranav pushes.

---

## 2026-06-10 — Strategy Book MASTER: formatting normalization pass + component index

- **Normalization pass** on `books/strategy-book/working/CA-Inter-Strategy-Book-MASTER.md` (FORMATTING ONLY — zero content/wording changed). Objective: make every recurring component machine-parseable for the HTML build pipeline.
- Key changes made (counts): 20 AUTHOR SAYS → blockquotes · 12 HOW TO DO THIS → blockquotes (inline variants had text moved below marker) · 4 STARTING LATE? BARE MINIMUM → convention-compliant blockquotes · 6 END GOAL → blockquotes with `- [ ]` checkbox items (replacing □ in code blocks) · 8 RANK ONLY → blockquotes (inline ★ [RANK] within [ALL] strategies) · 2 DIAGRAM markers added (Routing Flowchart, Posture & Eye Exercise) · 5 FILL-IN markers added in Personal Pages section.
- **Heading fixes:** `# ROUTING PAGE — WHERE ARE YOU...` split into H1 + H2 · `### Priorities from today...` and `### Your Bucket 0 Daily Tick` and `### Understand this before any class strategy.` all converted to ALL-CAPS non-strategy H3 (no tag) · All Bucket 5 and Bucket 6 `**Strategy N — ...**` bold headings promoted to `### Strategy N — ...` with `---` after each · Added missing `---` after Bucket 2 Strategies 6, 7, 8.
- **Created** `books/strategy-book/working/MASTER-component-index.md` — per-section table, global summary (88 strategies total: 84 × [ALL], 4 × [RANK]), FILL-IN inventory, DIAGRAM inventory, 10 NEEDS HUMAN DECISION items, 3 UNTAGGED recurring patterns (code-fenced structured content, inline REF tags, STRUCTURE ONLY blocks).
- health_check green (46/46); file_index regenerated (74 files). Commit locally; Pranav pushes.

---

## 2026-06-10 — Strategy Book: subject-wise routing, repeat-attempt check, tick-list end-goals

- MASTER edits (`working/CA-Inter-Strategy-Book-MASTER.md`): Routing page now leads with the **subject-by-subject** principle (run buckets per subject, even for both-groups students) + a **repeat/multiple-attempt self-check** (per subject: 70%+ → Bucket 3, 50–70% → Bucket 2, <50% → fresh start Bucket 1/0).
- **All bucket "End Goals" converted to tick-lists** (□/★); folded the old separate end-of-bucket checklists in (one checklist per bucket). **Bucket 0** got a **Daily Tick** habit-tracker instead. Bucket 1 list includes a **FIXED (not new) single Gmail + phone number** for all study/digital activity.
- Bucket 0 also: "better late than never" line + Indian pure-veg budget diet examples. Voice kept to the Raj-Shamani/older-brother spec throughout.
- **Consistency pass:** reconciled `sources/summary-strategy-book-memory.md` — fixed the two stale lines (separate-closing-checklist format; "feedback-collection / no further changes" status) and appended a dated **UPDATE — current state (2026-06-10)** section cataloguing everything added across recent sessions. README is a file-manifest, still accurate (design/ entry already present). No contradictions found across the doc set.
- health_check green; file_index regenerated. Commit locally; Pranav pushes. (Sandbox git index keeps corrupting on this mount — rebuild with `git reset` before committing; one Cowork session at a time.)

## 2026-06-10 — Strategy Book design system: spec v1 locked

- Created `books/strategy-book/design/design-spec.md` — the visual design source of truth. Decisions locked by Pranav: **full-colour interior, B5 (7"×10") trim, diagram ownership decided per-diagram later, spec-only for now (no sample chapter yet)**.
- Spec covers: bucket colour system (B0 slate → B5 maroon, B6 sky, AI violet, Emergency signal-red with full red edge strip; gold reserved for RANK); **stepped right-edge bleed tabs** (9 slots → closed-book fore-edge index, Pranav's idea); footer **journey strip** ("you are here" mini-timeline on every page, B0 segment always half-filled); 2-page bucket-opener spread (End Goal + ranker line + grey Bare-Minimum box + mini-TOC); fixed component library (How to Do This checklist box = signature, Author Says in Kalam handwritten font with avatar, RANK gold border, warning strips, fill-in workbook forms); typography (Archivo/Source Sans 3/Kalam/Noto Serif Devanagari); **11-diagram Excalidraw inventory** prioritised (routing flowchart #1, 3-layer funnel #2…) — .excalidraw JSON committed, PNG exports local-only; production = HTML + paged.js → B5+bleed PDF.
- `books/strategy-book/README.md` updated (design/ in folder map + file table). health_check green (46/46, encodings clean, CLAUDE.md current); file_index 73 files. Commit locally; Pranav pushes.
- Next step when Pranav triggers build: CSS tokens + one sample section (Bucket 5 recommended) → print review → roll out.

## 2026-06-09 — Verification pass + git recovery

- Ran `tools/health_check.py` (green: 46/46 dirs, README links resolve, UTF-8/NUL clean, CLAUDE.md current) and `tools/file_index.py` (regenerated `_claude/artifacts/file-index.md`, 72 files). No structural fixes needed.
- Strategy Book confirmed fully committed on Pranav's machine (MASTER, Full-Structure, README, all sources — verified against HEAD).
- **Git incident logged for future-proofing:** two concurrent Cowork sessions/app hitting `.git` at once corrupted the index (stale `.git/index.lock`, "bad signature/index corrupt", and a sandbox view that showed the whole repo staged as deleted). No data lost — fixed by removing the lock + `git reset` to rebuild the index from HEAD. **Rule going forward: one Cowork session at a time on this repo.**

## 2026-06-09 — Strategy Book MASTER: harvested from 5 external ranker/faculty reports

- Reviewed the 5 `books/strategy-book/sources/extermal/` reports (YouTube ranker + faculty compilations). ~70% was CA Final (articleship/IBS/CFA/placement) — filtered as out-of-scope; deduped heavy repetition. Harvested 5 Inter-relevant items into `working/CA-Inter-Strategy-Book-MASTER.md`:
  - **Bucket 5 — new Strategy 1 "Your Exam Kit & Logistics"** (scout centre; TWO identical calculators; 3–4 same-brand black pens; 3–4 hall-ticket copies; stapler/scale/pencils; night-before pack; reach 1hr early; loose clothing; light meal + nimbu-paani/glucose). Renumbered Bucket 5 → 1–17. Folded submission mechanics (tick attempted-question boxes, OMR domino alignment, "1+2" supplement count, pen-cap-off, last-10-min review) into "Presentation & Submission" (Strat 11).
  - **Bucket 2** — Pause-and-Solve (Undivided-Attention, esp. recorded lectures); study-buddy fixed-call + Author Says (Teach-a-Friend → "and Keep a Study Buddy"); own-the-technical-keywords (theory mnemonics strat).
  - **Bucket 3** — Hinglish/Hindi revision notes (Build Layer 2); exam answer stays English.
- **Resolved morning-theory-vs-practical conflict** per Pranav: flipped Bucket 3 "Match Subject to Your Energy" → theory in your most productive window (morning OR night), practical sums when low/sleepy.
- **Excluded:** all CA-Final content; "lucky break" chapter-gambling; "reject notes/master from source"; rigid 12–14h & Pomodoro mandates; pure motivation/anecdote.
- health_check green; file_index 72. NOTE: project_log + summary-memory show signs of a **concurrent session/app** (a "Batch Operations" entry appeared that this session didn't write; summary-memory locked EPERM). Layer-3 fix still pending in canonical summary-memory. Commit locally; Pranav pushes.

## 2026-06-09 — Batch Operations system rebuilt + Standup Teaching philosophy doc

- Created `preparations/standup-teaching.md` — working philosophy doc for "Standup Teaching" (Pranav's named teaching style blending deep concept teaching with clean, anchored comedy). Not in books yet; flagged for future `books/about-author/` entry.
- Rebuilt `preparations/cainter-batch-operations.html` (replacing old `cainter-batch_operations_daily.html` which had a fixed daily quote+verse+insta routine). Key changes:
  - **Segment Library** (19 types): 6 Opening segments (Motivational Quote, Gita Shlok, Mahabharata/Epic Story, Personal IPCC Story, Standup Moment, Exam War Story) + 13 Mid-class segments (Insta Comedy Feed, Insta Motivation, Spiritual Reels, AI Tool Update, ICAI Updates, Financial News Brief, Mental Side of CA, CV & Career Reality, Famous CA/Finance Stories, Accounting in the News, Myth vs Reality in CA, YT Shorts Comment React, Student Doubt Discussion). Replaces the previous fixed daily routine.
  - **Week Planner tab**: Sun planning — pick Opening + Mid-class segment per day for 6 days. Saved to localStorage.
  - **Daily Ops tab**: Simplified checklist (fewer items, segment-aware). localStorage persistence per date — resets daily, survives refresh.
  - **Quote/Verse banks**: Added "Mark used" toggle per item, saved to localStorage — prevents repetition.
  - **Class structure**: Updated to 2.5 hr / 150 min flow, batch stats card (100 classes, 240 hrs, 4 months).
  - Removed: Sunday prep load for 6 separate daily items (now weekly Segment Library planning instead).
- README.md updated: preparations/ folder map expanded, "Where things are" table updated.
- Commit locally; Pranav pushes.

## 2026-06-09 — Strategy Book MASTER: harvested missing strategies + reverse-planning

- Compared MASTER vs Full-Structure vs original General-Exam-Systems; harvested everything missing into **MASTER** (the canonical working draft). All edits in `books/strategy-book/working/CA-Inter-Strategy-Book-MASTER.md`.
- **Bucket 1 restructured:** new Strategy 3 *Pick Your Anchor Book*; new Strategy 4 *Plan Backward From Exam Day* (industry hours + reverse-planning calendar for RANK and a separate PASS/exemption chart + one-group-or-two decision merged in); 3-Question Filter + Golden Rule box added to *Fix Your Boundary*. Renumbered to 1–9 (old standalone Both-Groups removed, folded into Strat 4).
- **Reverse-planning dates:** kept Pranav's round-number durations (4/21/45; 185/231/308/461) but **recomputed the calendar dates** — his table didn't tie out (second-rev start is 24-02-2027 not 17-03; Scenario A start 23-08-2026 not 28-10). PASS chart: exam-anchored back end fixed, second revision 45→39 days, classes+first-rev −30% (≈1295h) → starts 23-10-2026/21-09/29-07/12-04. **Flagged to Pranav** in case his dates used a different assumption (e.g. study-days only).
- **Other harvests:** Chapter Rating [RANK] (Exam-Relevant A/B/C + Recall + Simulation, Hinglish, Bucket 3); Paste-It-Where-You-Live (Bucket 3, GST-in-hallway Author Says); Amalgamation 5-times rule [RANK] (Bucket 3, exception only); 15-min Reading-Time strategy (Bucket 5 Strat 6, anecdote softened — dropped the 'not allowed' claim); Revision Marathons (Bucket 4); Dual-coding tip + Write-by-hand 'worse to worst' Author Says (Bucket 2); target-driven-not-hours + Pain Choice + diet (Bucket 0); AI teacher-first caution (AI Section); 'no motivation, gamified journey, warna time chala jayega' positioning (About This Book).
- **Dropped per Pranav:** Five-Year Rule, Articleship Discipline.
- **Layer 3 corrected** to one thin BOUND notebook per subject (spiral-bound A4 ok) — u