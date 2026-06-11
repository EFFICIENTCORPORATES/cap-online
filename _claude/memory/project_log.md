# Project Log — cap-online

A running status note. Newest entries at the top. One short block per session.

---

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
- **Layer 3 corrected** to one thin BOUND notebook per subject (spiral-bound A4 ok) — updated the sources-copy memory; **canonical `_claude/memory/summary-strategy-book-memory.md` is LOCKED/read-only this session (EPERM) — its Layer-3 line still says 'loose sheets' and needs the same one-line fix.**
- health_check green (46/46, encoding clean, CLAUDE.md current); file_index 71 files. Commit locally; Pranav pushes.

## 2026-06-09 — Strategy Book (Pillar 1) materials consolidated into books/strategy-book/

- The `books/strategy-book/` folder was empty (only .gitkeep); all real Strategy Book material lived scattered in `_claude/`. Exported (copied, originals kept) into the folder so it's now self-contained.
- `working/`: `CA-Inter-Strategy-Book-MASTER.md` (lead working draft) + `CA-Inter-Book-Full-Structure.md` (fullest content collection).
- `sources/` (new subfolder): `CA-Inter-General-Exam-Systems.md` (original topic-based source), `Blueprint-CA-Inter-Exam-Strategy-Guide.md` (decision log), `SKILL-strategy-book-structural-method.md`, `SKILL-strategy-book-voice-and-tone.md`, `summary-strategy-book-memory.md`.
- Author profile NOT duplicated — stays shared in `books/about-author/`. Added `books/strategy-book/README.md` mapping every file + the lineage.
- health_check: 46/46 dirs, encoding clean, CLAUDE.md current — all green. file_index regenerated (65 files). Commit locally; Pranav pushes.

## 2026-06-09 — CLAUDE.md entry point + staleness guard (Session: setup, cont.)

- Added **`CLAUDE.md`** at repo root — the session entry point. Pranav starts new chats with "Read CLAUDE.md ...". It encodes: the read order (CLAUDE.md → README → content/README → _claude/memory), the working rules, the full folder-purpose map, the tools, and the gotchas (Excalidraw, UxPlay, brand split, UTF-8, no binaries, ask-first, sandbox-can't-push).
- Added **`check_claude_md()`** to `health_check.py`: fails if CLAUDE.md is missing or if any live top-level folder isn't documented in it — so structural changes can't leave CLAUDE.md stale. Verified with a negative test (temp folder → check failed → removed → clean).
- Health check now reports: dirs 46/46 + README links + encoding + CLAUDE.md current — all green.
- Prior 5 commits already pushed to origin/main by Pranav. This adds CLAUDE.md + guard (commit locally; Pranav pushes).

## 2026-06-09 — content/ studio + encoding guard (Session: setup, cont.)

- Built `content/` creative studio: `assets/{raw-footage,intros-outros,green-screen,b-roll,music-sfx,brand-kit,thumbnails,flyers}`, `social/{personal,vc-gurukul}`, `calendar/{personal-private,vc-gurukul-shared}.md`, `scripts/gsheet_sync.py` (stub), `content/README.md`. Base clip → `assets/b-roll/`. Retired empty `reels/`.
- Brand rule: `social/personal` = entirely Pranav's; `social/vc-gurukul` = co-branded Pranav + VCG. Two calendars (private vs shared) sync to a Google Sheet via gsheet_sync.py for editor collaboration.
- Converted law-faculty sample `.md` (was UTF-16) → clean UTF-8. Fixed stray NULs in README.md; about-author `.md` files were empty UTF-16 stubs (real content in their PDFs) → replaced with proper UTF-8 placeholder stubs.
- **Added encoding guard to `tools/health_check.py`:** new `check_encoding()` flags any tracked text file with NUL bytes or invalid UTF-8 (skips gitignored binaries via `git check-ignore`). Run it after edits — it caught the corruption this session. Health check now: dirs 46/46 + links + encoding, all clean.

## 2026-06-09 — animation/recording cleanup + new spaces (Session: setup, cont.)

- **animation-generate/ dissolved:** character bible → `books/concept-book/characters/`; story flow (story first-draft) → `books/concept-book/story-vignettes/`; AI content pipeline + tool stack → `content/ai-content-pipeline/`.
- **Animation tool locked = Excalidraw** (noted in both ai-content-pipeline docs). Screen mirroring now via **UxPlay** on Windows; ApowerMirror retired (Pranav deleted those files).
- **recording/ dissolved:** 3 test MP4s → `obs-setup/recordings/test/` (OBS output). recording/ removed; leftover empty `preparation-materials/` tree fully removed.
- **OBS wallpapers:** explicit `OBS Background IPCC.*` → `obs-setup/assets/`. OPEN: confirm if any other `content/motivation/` wallpapers are OBS-linked (would break scene refs; Pranav fine redoing scene collection, or grant OBS config access for auto path-rewrite).
- **New spaces:** `vc-gurukul/contracts/` (legal agreements w/ VC Gurukul); `planning/` (future-roadmap.md, to-purchase.md, execution-notes.md) for dumping execution/purchase thoughts.
- Audit Decoder Question Bank PDF → `materials/reference/` (Audit subject, not Adv-Accounts).
- **New strict rule:** at first real blocker/doubt, ASK Pranav first — don't spin on workarounds. Saved to Claude memory.

---

## 2026-06-09 — book/ bifurcation + scope lock-in (Session: setup, cont.)

**Scope clarified by Pranav — six pillars (only 2 self-drafted books):**
1. Exam Strategy Book (general + journey + exam-specific) → `books/strategy-book/`
2. Concept Book for **Advanced Accounts** (concepts all chapters + stories + error register + exam markings) → `books/concept-book/` — **this IS the Advanced Accounts book**, so the earlier separate `adv-accounts-book/` was merged into `concept-book/`.
3. Syllabus Engine (ICAI → JSON/MD) → `syllabus-engine/`
4. Question Bank (PYQ/MTP/RTP + solutions, **not** in study material, last 7–10 yrs) → `question-bank/` (new)
5. AI MCQ / online test platform (DBMS + Cloudflare, students test online & get results) → `mcq-platform/` (new)
6. Telegram study bots → `telegram/`

**book/ folder bifurcated & removed:**
- Law-faculty chapter sample (docx+md, *Nature of Contracts*) → `materials/reference/samples/` (kept as a style/inference sample only; out of Adv-Accounts scope).
- `chap-0/` → `books/concept-book/chapter-zero/` (EN + Hindi drafts).
- `about-author/` → `books/about-author/` (shared by both books — profile + journey).
- Deleted as confirmed byte-identical duplicates of `_claude/` copies: `write-like-the-ca-inter-teacher-skill.md`, `chapter-zero-concept-bank.md`, `strategy-all-in-one/CA-Inter-General-Exam-Systems.md`. Deleted empty `table-of-contents.md` and `__pycache__/`.

**Added pillars:** `question-bank/{pyq,mtp,rtp,solutions}` + README; `mcq-platform/{question-generation,database,cloudflare-app}` + README. Updated README, health_check EXPECTED_DIRS.

**Still pending review:** `preparation-materials/animation-generate/`, `preparation-materials/all in one exam strategy for all/`, `recording/`, and the `OBS Background IPCC.*` images in `content/motivation/`.

---

## 2026-06-09 — Repo restructure (Session: setup)

- Connected root folder `D:\EffCorp_Projects\cap-online` (git root, remote: EFFICIENTCORPORATES/cap-online, branch `main`).
- Built the full agreed folder skeleton (books, syllabus-engine, vc-gurukul, content, telegram, obs-setup, photo-gallery, materials, preparations, tools, _claude).
- Migrated unambiguous folders:
  - `motivation/` → `content/motivation/`
  - `scripts/` → `tools/` (count-line-pdf, sarvama
