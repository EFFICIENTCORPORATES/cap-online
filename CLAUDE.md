# CLAUDE.md — Operating Guide for the cap-online repo

**Read this file first, every session. Then read the context in section 1 BEFORE executing any task.**
This repo is CA **Pranav Pratik Tulshyan**'s CA Inter teaching ecosystem for **VC Gurukul, Noida**.
Git root `D:\EffCorp_Projects\cap-online` · remote `EFFICIENTCORPORATES/cap-online` · branch `main`.

---

## 1. Read order (do this first, every session)

1. **CLAUDE.md** (this file).
2. **README.md** — full repo map, the 6 pillars, and rules.
3. **content/README.md** — creative-studio rules (only if the task touches `content/`).
4. **_claude/memory/** — `project_log.md` (newest entry first) and the memory files there.

Then briefly confirm you understand the structure and rules, and wait for the task. Do not start work before this.

---

## 2. Working rules (non-negotiable)

- **Markdown (`.md`) by default.** HTML for books and slides. **No SVGs/diagrams unless explicitly asked.**
- **No binary files in git.** Audio, video, images, office docs, archives, executables are gitignored — they live locally only. Commit only text (md/py/html/json/csv...).
- **UTF-8 only.** Never write NUL bytes or UTF-16. (Cross-mount edits have corrupted files before — `health_check.py` now catches this.)
- **After ANY structural change** (add / move / rename / delete files or folders): run `python tools/health_check.py` and fix everything it flags, then run `python tools/file_index.py`. If you add a new top-level folder, also document it in this file and in `README.md` — `health_check.py` will fail until you do.
- **End every session** by appending a short dated note to `_claude/memory/project_log.md` (newest on top).
- **Ask first when stuck.** At the first genuine doubt or blocker, ASK Pranav — do not guess or spin on workarounds.
- **Pushing needs Pranav's credentials.** The sandbox cannot push to GitHub. Commit locally; Pranav runs `git push origin main` from his own machine.

---

## 3. What each folder is for

| Folder | Purpose |
|--------|---------|
| `books/strategy-book/` | **Pillar 1** — Exam Strategy book (general + journey + exam-specific). `sources/` (research, skills, external reports), `design/` (spec + HTML build templates), `working/` (MASTER + component-index), `drafts/ final/` |
| `books/concept-book/` | **Pillar 2** — Advanced Accounts **Concept Book** (this IS the Adv-Accounts book): `chapter-zero/ characters/ chapters/ story-vignettes/ revision-material/` |
| `books/about-author/` | Shared author profile + journey (used by both books) |
| `syllabus-engine/` | **Pillar 3** — top-level folder is nearly empty (`data/` = 2 source `.xlsx` only). **The real, working pipeline lives nested at `books/concept-book/syllabus-engine/`** (`scripts/ html-source/ data/` incl. the canonical syllabus JSON) — see section 6. |
| `books/question-bank/` | **Pillar 4** — non-study-material questions (PYQ/MTP/RTP + solutions), currently ~3 yrs' coverage (goal: 7–10 yrs). **Not a top-level folder** — lives under `books/`. Its own `README.md` describes an abandoned `pyq/mtp/rtp/solutions/` layout (those 4 subfolders are empty `.gitkeep` stubs); real content is in `Raw_PDF_Question_Bank_CA_Inter_Accounts/`, `Parsed_PDF_Question_Bank_CA_Inter_Accounts/`, and `metadata-index/` — see section 6 for full pipeline status. |
| `mcq-platform/` | **Pillar 5** — AI MCQs in a DBMS, Cloudflare online tests: `question-generation/ database/ cloudflare-app/` |
| `telegram/` | **Pillar 6** — study bots + their source docs: `bots/ source-docs/` |
| `student-toolkit/` | Standalone student tools (e.g. exam date calculator). A subset of student-facing utilities; the Telegram bots may also surface these. |
| `content/` | Creative studio: `assets/` (raw-footage, intros-outros, green-screen, b-roll, music-sfx, brand-kit, thumbnails, flyers), `social/{personal,vc-gurukul}`, `calendar/`, `scripts/`, `motivation/` (daily-quote media library), `competitor-analysis/`, `ai-content-pipeline/`, `productions/` (one folder per video/content piece). See `content/README.md`. |
| `vc-gurukul/` | Institute side (NOT content brand): `management-discussions/ events/ batch-july-2025/ contracts/` |
| `materials/` | `icai-source/` (study material, PYQ/MTP/RTP — **gitignored/local**) + `reference/` (incl. `samples/`) |
| `obs-setup/` | Recording/streaming setup: `assets/` (OBS wallpapers), `recordings/` (output), `tools/` |
| `photo-gallery/` | `originals/` (gitignored) + `index.md` |
| `planning/` | Future planning: `future-roadmap.md`, `to-purchase.md`, `execution-notes.md` |
| `preparations/` | Personal prep notes, lecture plans |
| `final-deliverables/` | Print-ready teaching documents: teaching method (01), batch planner (02/02A), bridge course skeleton (03/03A), and future student-facing exports. MD only. |
| `tools/` | Admin/processing scripts (see section 5) |
| `_claude/` | Claude's context: `memory/` (incl. `project_log.md`), `artifacts/`, `skills/` |
| `first_run/` | **Workspace proving the Question Bank Book pipeline end-to-end** (added 2026-07-23) before scaling to the full syllabus — `source/` (PDFs only, never MD, for every in-scope sitting — see section 6 for why this is enforced structurally now), `schema/` (single-source-of-truth `book-style.json` + generated `book-style.css` + `HTML-SCHEMA.md`), `prompts/` (the 3 external-AI prompts), `scripts/` (`extract_questions.py`, `generate_chapter_book.py`, `generate_all_chapter_books.py`), `output/parsed-from-pdf/` (sitting HTML, Layer 1), `output/generated-from-script/` (`questions_index.json` + every chapter book, Layers 2–3 — reorganized 2026-07-26, see section 6). See section 6 for full status. Not a permanent pillar — once validated, its lessons fold back into `books/question-bank/`. |

**Only TWO self-drafted books:** the strategy book and the concept book (Advanced Accounts). Everything else is engine/platform/content/ops.

---

## 4. Tools

- `tools/health_check.py` — validates folder structure, README links, UTF-8/NUL encoding, and **CLAUDE.md staleness**. Run after every structural change.
- `tools/file_index.py` — regenerates `_claude/artifacts/file-index.md`.
- `tools/gitignore_audit.py` — flags binaries / large files not covered by `.gitignore`.

---

## 5. Repo-specific gotchas

- **Animation = Excalidraw.** Screen mirroring = **UxPlay** (Windows).
- `content/social/personal/` = **entirely Pranav's own** content. `content/social/vc-gurukul/` = **co-branded** Pranav + VC Gurukul. Two calendars (private vs shared) sync to a Google Sheet via `content/scripts/gsheet_sync.py`.
- The content-side `vc-gurukul` is the *brand*; the top-level `vc-gurukul/` is *institute ops/contracts* — different things.
- Heavy raw media (raw footage especially) is best kept on an external drive/cloud; the repo holds the recipe + finished exports + an index.
- **`tools/health_check.py`'s `EXPECTED_DIRS` list is stale**: it still checks for `question-bank/pyq`, `question-bank/mtp`, etc. at the repo root, which don't exist (real path is `books/question-bank/...`). This produces permanent false-positive MISSING-folder failures until the tool or the layout is reconciled — known, not yet fixed, flagged to Pranav.

---

## 6. Question Bank Book — current focus (as of 2026-07-22)

Pranav has shifted full focus onto **Pillar 4, `books/question-bank/`**. The core task: converge past-exam questions (PYQ/MTP/RTP) with the syllabus chapter/topic taxonomy so every question is tagged to a chapter/topic — this is the main gap, not raw content collection. This session built the tagging schema and machine-tagged 4 sittings end-to-end (see below) — read `books/question-bank/metadata-index/TAGGING-SCHEMA.md` before adding more.

### Where the real content is
- **`Raw_PDF_Question_Bank_CA_Inter_Accounts/`** — raw PDFs, named `CAInter-AdvAcc-{MTP|PYQ|RTP}-{Session}[-SetN]-{Q|Ans}.pdf`, converted to `.md` (originally via MarkItDown; MarkItDown isn't installed in the sandbox, so later conversions in this session used `pypdf` directly — same plain per-page text-extraction contract, logged as such in `conversion_log.txt`). Conversion history: `conversion_log.txt`. QA tracked per-file in `question_bank_index.csv` (sizes/line counts only — no topic data).
  - **PYQ design decision (2026-07-22):** Pranav confirmed PYQ "Suggested Answers" PDFs contain BOTH the question text and the worked answer, and are printed (not scanned) — they convert cleanly every time. The separate PYQ *Question*-only PDFs, by contrast, were consistently blank (scanned/image, no text layer) and add nothing once the Answers doc is used. **PYQ sourcing now targets only the Suggested Answers document per sitting** — same single-document shape as RTP. The 4 existing PYQ Question-only PDF/MD pairs (Jan2025, Jan2026, May2024, May2026) were moved to `Raw_PDF_Question_Bank_CA_Inter_Accounts/deprecated-pyq-question-files/` — don't source or convert PYQ Question papers going forward.
  - **Coverage window extended (2026-07-22):** Pranav sourced 6 more PYQ Answer PDFs — May 2026 (previously missing entirely) plus 5 older sittings never in the repo before: Dec 2021, May 2022, Nov 2022, May 2023, Nov 2023 (the latter two were AES-encrypted; empty-password decrypt worked). All 6 converted cleanly. PYQ now covers **Dec 2021 – May 2026**, a real step toward the README's 7–10 yr goal (MTP/RTP still only May 2023 – May 2026).
  - ~~Stray files~~ `MERGE_PDF.py` and the duplicate leftover `MTP_May-24_Set-1 CA-INTER-ACCOUNTS.md` — both deleted 2026-07-26 (confirmed redundant: the merge script wasn't referenced by any pipeline code, and the MTP file was a pre-rename duplicate of the already-present `CAInter-AdvAcc-MTP-May2024-Set1-*.md/.pdf`).
  - **For a full per-attempt view** (which sittings have PDF/MD/Parsed/JSON, and exactly what's missing) see `books/question-bank/question_bank_index_by_attempt.csv` (new, 2026-07-22) — more useful than `question_bank_index.csv` for pipeline-status questions; that file stays as the per-*file* conversion QA record.
- **`Parsed_PDF_Question_Bank_CA_Inter_Accounts/`** — the clean target format: complex accounting tables (ledgers/BS/working notes) become HTML `<table class="accounting-table">` blocks embedded in the `.md`. **Only 3 of ~55 files parsed so far** (one MTP — May2024 Set1, one PYQ — Jan2026, one RTP — May2026 — explicitly a pilot). All 3 are now fully tagged (see below) — parsing the remaining ~52 raw conversions into this format is the next big lever for growing tagged coverage.
- **`metadata-index/`** — the topic-tagging work:
  - **`TAGGING-SCHEMA.md`** (new, 2026-07-22) — the schema spec: which of the two taxonomies to tag against (`topic-index.json`'s `unitCode`+`subtopicRef`, not the locked master syllabus JSON's IDs), the U0/U1 reconciliation table, and the lean per-question JSON shape (`mdAnchor` pointing into the parsed `.md`, content never duplicated). Read this first before tagging anything else.
  - `topic-index.json` — reference index of ICAI units; now covers **32 of 36** syllabus units (up from 22 this session — added AS16, AS28, AS18, AS5, AS24, AS7, AS22, AS25, AS15, AS17 as stub entries: heading lists only, not yet individually described like the original 22 are). Only **AS 1** (Disclosure of Accounting Policies) and **AS 27** (Joint Ventures) remain genuinely untouched by any tagged question.
  - `MTP_Jan2025.json` — the original pilot (1 sitting), embeds full question/answer HTML inline — left as-is, not worth reprocessing, but no longer the pattern to follow.
  - **`MTP_May2024_Set1.json`, `PYQ_Jan2026.json`, `RTP_May2026.json`** (new, 2026-07-22) — the 3 parsed-pilot sittings, fully tagged question-by-question using the lean schema. That's **4 of ~17 sittings tagged** now (up from 1). Remaining ~13 sittings are blocked on the parsing step above, not tagging.
  - `AS2_Question_Reference.html` — a separate, ad hoc, single-standard (AS 2 only) cross-reference across the whole corpus; useful but not integrated into the systematic per-question scheme above — don't extend this approach to other standards, use the systematic scheme instead.
- **`pyq/ mtp/ rtp/ solutions/`** — dead, empty except `.gitkeep`. An abandoned v1 layout the README still describes; don't populate these, real content lives in the three folders above.

### The chapter/topic taxonomy (for mapping questions → chapters) — updated 2026-07-23

- **`books/concept-book/syllabus-engine/data/0-ca-inter-adv-accounts-subtopics-marks-weightage.json`** — the master syllabus index, marked "locked, never edit." All 36 chapters (teaching-sequence order) + 436 topics + marks-by-attempt back to May-2018, diagnostics confirm no gaps. IDs: `unique_chapter_id` = `M{module}-C{chapter}-U{unit}`; `unique_topic_id` = `{unique_chapter_id}-T{topic_no}`.
- **`books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`** (new, 2026-07-23) — **the canonical topic-number + page-number source**, built from Pranav's `CA INTER ADV ACCOUNTS - For Adarsh.csv` (400 topics, all 36 chapters incl. AS 1 and AS 27 — the two chapters nothing else in the repo had). Cross-joined 1:1 against file 0 by `unique_chapter_id` (verified: zero unmatched either direction) to also carry `teaching_sequence`/`chapter_name_short`/`marks_distinct_attempt_count`, plus new `standard`/`standard_title` (parsed from unit name) and `is_single_unit_chapter`. **Read exact topic numbers/names/page numbers from this file**, not from `topic-index.json`'s hand-built (and less complete) entries.
- `books/question-bank/metadata-index/topic-index.json` tags questions using its **own** scheme (`unitCode` + raw ICAI paragraph `sections[].ref` + prose `description`) — this is the *operative* scheme for the per-question `subtopicRef` tag (more legible than `unique_topic_id` for pointing students at "go read para 5.6–5.8"), but its **chapter IDs and page numbers are secondary to file 1 now** — covers only 32/36 units and 10 of those are still page-number stubs.
- **U0/U1 — reversed 2026-07-23, migration DONE.** Files 0 and 1 both use `U0` for the 7 single-unit chapters (Intro to AS, Applicability, Framework, Buyback, Amalgamation, Internal Reconstruction, Branch Accounting) — e.g. `M1-C1-U0`. **`U0` is now canonical everywhere** (reasoning: it correctly signals "no further units"; also backed 2-sources-to-1). `topic-index.json` (7 `unitCode` fields + their `unit` numeric companions) and all 4 already-tagged sitting JSONs (`MTP_Jan2025.json`, `MTP_May2024_Set1.json`, `PYQ_Jan2026.json`, `RTP_May2026.json` — 28 `unitCode` occurrences total) were migrated in one pass and re-validated as parseable JSON. **No stale `U1` references remain** for these 7 chapters anywhere in tagging data — the only surviving `U1` mentions are `topic-index.json`'s `sourceFile` fields (e.g. `"M1_C1_U1_ Introduction....pdf"`), which are real on-disk filenames under `raw_icai_study_materials/`, not our tagging convention, and were correctly left alone.
- `books/concept-book/chapters/*.md` bracket tags (`[AS2-1.2]`, `[FW-1]`) exist for only 2 of 36 chapters and aren't formatted consistently — don't treat these as a taxonomy source.
- `mcq-platform/` (Pillar 5, empty scaffolding) has already committed in its own README to deferring to syllabus-engine's IDs — no competing scheme there.

### Also relevant, thin/empty so far
- `books/concept-book/chapters/` — only 2 of 36 chapters authored (`seq03-framework`, `seq04-as02`). Most of the syllabus has no concept-book content yet.
- `books/concept-book/revision-material/` — completely empty; no error-register/exam-marking structure exists yet to cross-reference against question topics.

### The ultimate goal: a per-chapter "Question Bank Book" for students (locked in 2026-07-22)

Tagging isn't the end product — it's infrastructure for a **student-facing "go-to book for practice"**, one HTML book per AS/chapter, collecting every question across MTP/RTP/PYQ that tests that chapter, with official answers, topic tags, and (new) authored "Common Student Mistakes." Pranav built a hand-crafted target sample, now 3 files (as of 2026-07-23):
- `books/question-bank/metadata-index/AS10_Question_Book.html` (AS 10, ~58 questions) — **read this file before doing any chapter-book work**; it is the concrete quality bar. Structure: an intro/scope note (question count, explicit inclusions/exclusions with reasons), a flagged-issues note (every low-confidence answer named explicitly), an organisation note (topic ordering + recurring-question policy), then three sections — **I. MCQs, II. Descriptive (pure chapter), III. Integrated (cross-standard)** — each question as a card with source/marks/topic/badges, verbatim question+answer HTML, Common Student Mistakes, and an Extraction-note transparency line.
- `books/question-bank/metadata-index/AS10_Question_Reference.html` — the audit stage that fed the book above (topic-wise weightage summary + per-question source/page/marks table). Confirms this was built by reading raw source PDFs directly, chapter-by-chapter — a separate one-off deep-dive, not through the `topic-index.json` pipeline (references a `_claude/skills/SKILL-question-bank-summary-making.md` that doesn't exist in this repo).
- `books/question-bank/metadata-index/AS10_Question_Bank.json` — **the actual machine-readable schema behind the book**: `findingId, chapter, standard, section (I/II/III), topicRef, topicHeading, sourceLabel, qNoInPaper, marks, questionHtml, answerHtml, commonMistakesHtml, extractionNotes, group, order`. This is the *derived, per-chapter* layer (embeds full content, unlike our lean per-sitting tagging JSONs) — confirms the two-layer architecture: Layer 1 = lean per-sitting tagging (what we build), Layer 2 = derived per-chapter book JSON like this one (what the generator script will produce by querying Layer 1 across all sittings + adding authored fields). Its `group` field is a plain slug (`"mars"`, `null`) with no explicit OP/PP role — predates that rule (file `generated_on: 2026-07-21`), so by Pranav's choice **OP/PP stays a Layer-1-only concept**, not added to the book-level schema.

Also shared: `MTP_Jan2026.json` — a new, cleanly-extracted sitting (both sets, full question+answer HTML) in the old embedded style, **not yet tagged to any chapter** — needs folding into Layer 1 (tag against `topic-index.json`, treat as an already-"Parsed" source since content is already clean).

Still referenced by the sample but not present in this repo: `question-book-implementation-plan.md`, an `icai-practice-extraction/` folder — don't assume these will arrive; the two files above are what we're reconciling against.

**Two strategic decisions locked in (confirmed by Pranav, do not revisit without asking):**
1. **Tag every sitting comprehensively once, for every chapter it touches — never do one-off chapter-by-chapter re-scans of the source PDFs.** This is why `MTP_May2024_Set1.json` etc. tag *all* topics in a sitting, not just one chapter. Once a sitting is tagged, every future chapter-book query is "read the JSON," not "re-read the PDF."
2. **Render chapter books with a reusable generator script**, not hand-assembled HTML per chapter — analogous to `tools/strategy_book_parser.py` for the Strategy Book. One template + one script; a styling/structure fix happens once, not 36 times. Not yet built (`tools/question_book_generator.py` doesn't exist yet) — build it once the schema is reconciled against Pranav's fuller AS10 sample set.

### Two new authored content layers (added 2026-07-22, schema updated in `TAGGING-SCHEMA.md`)

**`commonMistakes`** — did not exist anywhere before this session. Real ICAI **"Examiners' Comments on the Performance of the Examinees"** documents exist for exactly 6 PYQ sittings (Jan 2025, May 2024, Sep 2024, May 2025, Sep 2025, Jan 2026) — Pranav sourced these as new raw PDFs; converted and sliced to their Paper-1-only section at `Raw_PDF_Question_Bank_CA_Inter_Accounts/examiner-comments-paper1/Paper1-ExaminerComments-{Session}.md`. From analysing all 6, wrote `books/question-bank/metadata-index/examiner-comments-writing-skill.md` — a style guide (opening-quantifier vocabulary, failure-mode + standard-citation + consequence-chain pattern, tone rules) for writing believable ICAI-voiced mistake notes for every question **outside** those 6 sittings (MTP/RTP never get real examiner comments; other PYQ sittings don't have a sourced comments doc yet). **Non-negotiable rule: every `commonMistakes` entry is tagged with its `source`** — `"ICAI Examiner's Comment — {Session}, verbatim/paraphrased"` for the real 6, or `"Synthesized per examiner-comments-writing-skill.md — not ICAI-sourced"` for everything else. Never blur the two.

**`recurringGroup` (OP/PP)** — Pranav's rule: strip numbers from question text, compare pairwise, **≥90% similarity ⇒ same recurring group**; within a group, the occurrence from the **chronologically earliest sitting** = **OP** ("Original Concept-testing Question"), every later occurrence = **PP** ("For Practice Question"). All occurrences still get shown in full in the eventual book — this is for cross-referencing/confidence (matching answer keys across occurrences), not de-duplication. Watch for: same numbers/renamed company (should still match) vs same company/different numbers-same-trap (may need judgment beyond the mechanical rule) — flag borderline cases rather than deciding silently. Full detail in `TAGGING-SCHEMA.md`.

### Pipeline reconsidered 2026-07-23: Parsed MD is not a required step; content embeds directly in sitting JSON/HTML

Two follow-on decisions from the same day as the AS10-sample review above:
1. **Parsed MD (`Parsed_PDF_Question_Bank_CA_Inter_Accounts/`) is NOT a mandatory gate.** Tagging already works fine reading Raw MD directly. Cleaning messy OCR'd tables into presentable HTML can happen **once, at first-read time, per question** (embedded directly in that question's record) rather than upfront for an entire sitting whether or not every question in it ever gets used. The 3 existing Parsed files aren't wasted, just no longer something the remaining ~34 sittings need before tagging.
2. **Sitting-level records embed full question+answer content directly** (reversing the original "lean pointer only" schema in `TAGGING-SCHEMA.md`) — because the one careful AI read of a messy source file should never be thrown away and re-done later. Each sitting = **one 100-mark paper = one file** (a bundled two-Set file like the original `MTP_Jan2025.json` pilot is the wrong shape — needs splitting into `_Set1`/`_Set2` for consistency with everything built since).

### First real production run: `first_run/` (started 2026-07-23)

A self-contained pilot workspace proving the whole pipeline end-to-end on 5 real sittings before scaling to the remaining ~30+: MTP May 2026 Set 1, MTP May 2026 Set 2, RTP May 2026, PYQ May 2026, and **PYQ Jan 2026** (deliberately included even though it's out of the "May 2026" batch, because it's the one sitting in this pilot with a *real* ICAI Examiner's Comments document — Jan 2026 lets the pipeline prove it can correctly use a real comment where one exists, not just synthesize one everywhere).

Pipeline for this run: (1) an external, smaller AI model — prompted with a strict schema — reads each raw source PDF/MD directly and writes one self-contained HTML file per sitting (the HTML becomes the **permanent primary record**; the source PDF is never re-read after this) → (2) Pranav + Claude both visually review all 5 → (3) a Python script (BeautifulSoup, no AI) extracts a flexible, multi-sortable JSON from each reviewed HTML → (4) combine all sittings' JSON into one master list, sortable/filterable by chapter, topic, date, paper-type via plain script code → (5) generate chapter-wise HTML books from that JSON via script → (6) merge all chapter HTML into one whole-book HTML via a "sewing" script, reusing every lesson from `tools/strategy_book_merge.py` (see section 7 below). Full detail, schema, and the 3 reusable prompts live under `first_run/` once built (see that folder's own docs).

### First pilot output reviewed, schema revised, all 6 pipeline skills written (2026-07-24)

Pranav ran Prompt 1 and got `first_run/output/MTP_May2026_Set1.html`. Reviewing it against the source **PDF** (not MD, per his explicit instruction) found the schema itself was hiding real defects: zero topic tagging despite the prompt requiring it, Part II answers containing placeholder/meta-descriptive text presented as "verbatim," and — the most serious — one entire printed Part II question (14 marks, the AS 24/Amalgamation-alternative + AS 1 + AS 17 question) silently missing, found only by counting question numbers against the paper's own "answer any four of the remaining five" instruction. Two mark totals were also individually wrong (12 instead of 14, 16 instead of 14) but happened to cancel out in the file's grand total.

Pranav then separately flagged two structural gaps discovered by inspecting the rebuilt file: **the Case Scenario MCQs' shared narratives were never captured at all** (only the questions were, leaving them referencing facts that appear nowhere in the document), and **marks/paper-facets/difficulty need to be independently machine-queryable**, not embedded in display strings. This produced a substantial schema revision, all locked in and applied to `MTP_May2026_Set1.html` as the concrete reference:

- **Paper-level facets** (course/paper-type/month/year/set) live once on `<body>` as `data-*` attributes, never repeated per-question or parsed out of the `"MTP May 2026 Set 1"` display string.
- **`.case-scenario` nodes are mandatory** wherever MCQs share a narrative, referenced by dependent questions via `data-case-ref` — audited as a systemic risk across all future sittings, not just this one.
- **`data-marks` is always a plain integer.** Multi-part questions with independent (unrelated) sub-parts are **split into separate qblock records** rather than carrying an unparseable `"14 (7+7)"` string — this was itself a new locked decision (see below).
- **New "Final Chapter" concept** (`data-final-chapter`): every question/fragment gets one designated home chapter in the assembled Question Bank Book, computed from `teaching_sequence` (canonical file 1) — trivial for single-topic fragments (the norm after splitting), computed as the latest-taught topic for the rare genuinely connected multi-topic question.
- **Independent vs. connected sub-part rule** (Pranav, 2026-07-24): before authoring a multi-part question, classify whether its sub-parts share one continuous fact pattern (connected, stays one record) or are unrelated problems bundled under one question number (independent, becomes separate records, each single-topic, referencing the parent question number + sub-part letter). Independent is the common case for this exam's descriptive questions — every multi-part Part II question in the pilot file turned out to be independent.
- **OR-alternatives** (e.g. "6(a) AS 24 theory OR 6(a) Amalgamation problem") get `data-alt-group`/`data-alt` so both alternatives exist as separate, independently useful records without double-counting marks.
- MCQ options are now structured (`<ol class="options"><li data-opt="A">`) with a machine `data-answer`, not `<br>`-separated text.
- Structured review-flag attributes (`data-confidence`, `data-review-status`, `data-issue`) sit alongside the existing prose `.extraction-note`.
- Easy/Medium/Hard difficulty (by count of distinct topics tagged: ≤2 = Easy, 3–5 = Medium, >5 = Hard) will be **computed in the Python `questions.json`-building step, never hand-authored in HTML** — Pranav's explicit call, so the thresholds/labels can change without touching every sitting file.

An external AI's independent review of the schema was also solicited and evaluated on its merits, not accepted wholesale: its paper-level-facets, case-scenario, structured-options, deterministic-ID, and review-flag recommendations were adopted; its proposal to add a parallel `AS-9.2.8`-style topic-ID namespace was rejected (recreates the ID-scheme-proliferation problem already fixed once — see the U0/U1 migration history above); its proposal to dilute the synthesized examiner-comment voice for misattribution-safety was rejected as reversing a decision already made (voice fidelity + provenance metadata, not voice dilution, was always the intended safeguard) — only its clean `data-comment-source` enum and a call for visible on-page labelling were adopted from that specific point.

**All of this is now documented in six new skill files** at `_claude/skills/SKILL-question-bank-*.md` (`pipeline-overview`, `html-schema`, `topic-tagging`, `question-splitting`, `examiner-comments`, `duplicate-detection`) plus a seventh, `verbatim-extraction`, capturing the failure-mode discipline from this review specifically. `SKILL-question-bank-pipeline-overview.md` is the front-matter index — read it first, from any repo clone, with any AI. `first_run/schema/HTML-SCHEMA.md` and `first_run/prompts/GENERATE-SITTING-HTML-PROMPTS.md` were both revised to match.

### All 5 pilot sittings built and validated (2026-07-24)

Rather than hand the revised prompts to the external AI for the remaining 3 sittings, Pranav asked Claude to build `MTP_May2026_Set2.html`, `PYQ_May2026.html`, and `PYQ_Jan2026.html` directly, against the schema/skills already proven on MTP Set 1 and RTP. All three built from source PDF, tagged, and validated the same way (0 unclosed tags, 0 backticks, 0 placeholders, unique IDs, resolved case-refs, consistent marks arithmetic). PYQ Jan 2026 is the pilot's one sitting with real ICAI Examiner's Comments — 11 of its 12 Part II records got the real matched comment; a self-introduced bug (real-comment blocks initially written with the citation stuffed into `data-comment-source` instead of the clean `icai` enum) was caught by grepping output values, not by the structural validator, and fixed. See `_claude/memory/project_log.md`'s 2026-07-24 (cont'd, 3) entry for full detail.

### Pipeline proven end-to-end (2026-07-25): extraction script + first real chapter book

Pranav asked to see the whole pipeline actually work, not just be designed: "I want to see from you being able to give me a 'Proper well formatted HTML file for the AS02 Chapter' considering the first_run>output 5 HTML files as your base." Two scripts now exist and were both run successfully against the real 5-file pilot:
- **`first_run/scripts/extract_questions.py`** — Layer 1 (sitting HTML) → Layer 2 (`first_run/output/questions_index.json`), BeautifulSoup, purely mechanical (reads what the HTML already says, no re-tagging). Ran clean: **136 rows from the 5 files**. Built-in marks-arithmetic sanity check (Part I / Part II raw / Part II alt-group-deduped, per file).
  - Caught first, via a pre-flight `grep -o 'data-part="[^"]*"' | sort -u` across all 5 files: `MTP_May2026_Set1.html` (built before the `"I"`/`"II"` data-part convention was settled) still had old free-text values. Fixed with a regex pass, re-validated 0 errors. Re-run that same grep check before extracting again after any future file changes — this is exactly the drift the extraction logic depends on being clean.
- **`first_run/scripts/generate_chapter_book.py`** — Layer 2 → Layer 3. Takes a unitcode + labels, queries `questions_index.json`, partitions into Section I MCQs / II Descriptive (pure) / III Integrated, renders inline-CSS HTML matching the `AS10_Question_Book.html` quality bar — including an explicit real-ICAI-vs-synthesized provenance line on every Common-Student-Mistakes box (a discipline this schema tracks losslessly that the AS10 hand-built sample predates).
  - First real run: `first_run/output/AS02_Question_Book.html` (AS 2 / Valuation of Inventories, `M2-C5-U1`) — 6 MCQs + 1 descriptive + 0 integrated = 7 questions, matching the hand-confirmed record set. Validated clean (0 unclosed tags — the HTMLParser's 2 reported "errors" were a validator artifact from self-closing `<br/>` synthetic end-tags, not real defects — 0 NUL bytes, 0 backticks, correct rupee entities, 0 placeholders, 0 duplicate IDs). Case-scenario narratives are correctly embedded inline per MCQ — the exact defect Pranav originally flagged in the external AI's output is confirmed fixed in this generated book.
  - **Expected, honest finding, not a bug**: Section III (Integrated) is genuinely empty for AS 2 in this 5-file pilot — 0 records exist where AS2 is a secondary tag on a connected multi-topic question. The independent-vs-connected splitting design means most multi-topic-looking questions get split into single-topic records at extraction time, so Section III only ever catches the rarer connected case. Future chapter-book runs should expect some chapters to have a legitimately empty Section III and say so plainly in the book's own scope note, rather than treat it as an extraction gap.

Deleted the confirmed-stale `first_run/output/TODO.md` (leftover pre-build RTP planning notes referencing an abandoned unit-code decision).

**Still not built**: OP/PP duplicate detection (`SKILL-question-bank-duplicate-detection.md` — designed, not implemented) and the whole-book merge/"sewing" script (reuse `tools/strategy_book_merge.py` lessons, section 7 below). Scaling `generate_chapter_book.py` to the other 35 chapters is blocked on more sittings existing — still only 5 of ~17+ sittings are built/tagged.

### Accuracy audit and Phase 2 scaling (2026-07-26): 10 sittings, all 34 touched chapters generated

Two locked decisions from 2026-07-26, both still in force — read `_claude/skills/SKILL-question-bank-phase1-definition-of-done.md` for the full checklist:
1. **MCQ arithmetic gets a full independent re-derivation pass** (found and fixed 6 real errors across the first 5 sittings' 67 MCQ rows — see that skill's §1 and the project log's 2026-07-26 entries for detail). **Descriptive answers get a lighter transcription-fidelity check only** — Pranav explicitly relaxed this bar ("first edition... room for errors") after seeing what the MCQ audit alone had already caught.
2. Every chapter book now carries a reader-facing disclaimer (first-edition status, invite to report errors by email) and labels each Common-Student-Mistakes box **"Examiner's Comment"** (real ICAI-sourced) vs. **"Author's Note"** (synthesized, with an explicit "may not apply in every case" caveat) — a rendering change in `generate_chapter_book.py`, not a change to the underlying data model.

Pranav then asked to scale past the single AS 2 proof-of-concept: 5 more sittings built (`MTP_Jan2026_Set1/Set2.html`, `RTP_Jan2026.html`, `PYQ_Sep2025.html`, `RTP_Sep2025.html`), bringing the pilot to **10 sittings, 275 tagged question rows**. A new batch driver, **`first_run/scripts/generate_all_chapter_books.py`**, queries every unique `final_chapter` in `questions_index.json` and generates a book for each — **34 of the syllabus's 36 chapters are now touched** (only AS 1 and AS 27 remain thin, 2 questions each). All 34 books validated structurally clean. Two real cross-tagging bugs were caught and fixed during this build: a `data-part` free-text drift (same class of bug as the 2026-07-25 fix) and a `unitCode` inconsistency where Branch Accounting and Framework were tagged with both `U0` and `U1` variants across different files — both of which are locked-canonical `U0` single-unit chapters per the earlier migration; left uncaught, either would have silently split one chapter's book into two.

**Still not built**: OP/PP duplicate detection and the whole-book merge script, as above — several likely-recurring questions were spotted and flagged in extraction-notes during this build (noted for whenever duplicate detection is implemented) but not acted on.

### Scope expanded to 2023+, folder layout reorganized, MD-not-PDF slip fixed structurally (2026-07-26)

Prompted by discovering that the 5 Phase 2 sittings above were built from `.md` conversions instead of the locked PDF-only rule (a real, self-caught deviation — see `SKILL-question-bank-verbatim-extraction.md` §1 for why that rule exists), Pranav made three decisions:

1. **`first_run/source/` now holds PDFs only, never MD.** The 8 MD files that were there were deleted and replaced with the matching PDFs (58 files: MTP Question+Answer pairs, PYQ Answer-only, RTP's single combined doc, plus all 6 real Examiner-Comments PDFs) for every sitting now in scope. This closes the gap structurally — there's no MD file left in that folder to accidentally reach for.
2. **Scope expanded to "everything from 2023 onwards."** Checked against the actual source library: this excludes only 3 older PYQ sittings (Dec 2021, May 2022, Nov 2022) — no MTP/RTP predates 2023 anyway. **34 sittings are now in scope; 10 are built; 24 remain** (7 MTP sessions × 2 sets, 9 PYQ sessions, 4 RTP sessions — see `_claude/memory/project_log.md` for the exact list). Building the other 24 is substantial future work, explicitly not started in this same pass — flagged as needing batched pacing, not a single continuous push.
3. **`first_run/output/` split into two subfolders**: `parsed-from-pdf/` (the 10 sitting HTML files, Layer 1) and `generated-from-script/` (`questions_index.json` + all 34 chapter books, Layers 2–3) — "so we know whatever is parsed from base scratch is separated from script output," in Pranav's words. `extract_questions.py` and `generate_chapter_book.py` were updated to read/write the new paths (one line each); both re-run clean afterward, all 34 books regenerated with no change in content, only location.

Also deleted two stray files flagged back in the 2026-07-22 session and never cleaned up: `MERGE_PDF.py` (a generic PDF-merge utility, unreferenced by any pipeline script) and `MTP_May-24_Set-1 CA-INTER-ACCOUNTS.md` (confirmed pre-rename duplicate of the already-present `CAInter-AdvAcc-MTP-May2024-Set1-*` files).

**Left deliberately untouched**: `first_run/output/QUESTION-BANK-BOOK.html`, `front-matter.html`, `back-matter.html`, and a `vendor/` folder (paged.js + fonts) of unconfirmed origin — likely a separate, earlier whole-book "sewing" attempt matching the §7 print architecture below, but not something built in any session covered by this log. Don't assume these are stale or fold them into either new subfolder without asking Pranav what they are first.

### Chapter-book reader-experience overhaul (2026-07-26) — MCQs removed, several new student-facing fields added

Following Pranav's review of the rendered book, a 16-point feature/fix list was triaged into "straightforward, do now" vs. "needs more design/input, park" and the first group was implemented directly in `generate_chapter_book.py`, then all 34 chapter books regenerated and re-validated clean (0 unclosed tags/NUL/backticks/placeholders/duplicate IDs):

- **MCQs removed from the book entirely** — they still live in the sitting HTML and `questions_index.json`, just never rendered into a chapter book. Reasoning: MCQs need continuous drilling on a dedicated practice platform, not a slow-read book; also reduces the exposure of the (real, separately-fixed) Integrated-section topic bug below, though that bug affected descriptive rows too and needed its own fix regardless. Sections renumbered to **I. Descriptive, II. Integrated**.
- **Fixed a real rendering bug**: `topic_label()` used to show only the current chapter's tag on an Integrated-section entry, hiding that the question also tests another standard (found via `AS16_Question_Book.html`'s MTP_May2026_Set2 Q8, which showed "AS 16" only despite also testing AS 10). Now renders every tagged topic on the row.
- **Topic tags now render in full**: `M1_C2_U0 : Framework for Preparation and Presentation of Financial Statements / ICAI Study Mat Topic No : 7/9/11` instead of the old compressed `Framework (7/9/11)` — legible to a student who hasn't memorized the shorthand.
- **Examiner's Comment vs. Author's Note now colour-coded distinctly** (tan/orange vs. pale pink, matching `book-style.json`'s `examiner_comment_*`/`synthesized_comment_*` values) — previously both rendered in one flat colour, undermining the front-matter legend's promised distinction.
- **New "Approx Time" field** next to Marks: `ceil(marks × 1.8)` minutes, computed at generation time (never hand-authored); RTP questions with no stated marks show a "10–20 minutes" range instead.
- **Removed from rendered output** (data still exists in `questions_index.json`, just not displayed): the per-question "Extraction note" and the file-level "Build info" footer — both were engineering plumbing, not student-facing content.
- **New per-question fields**: a blank "Student Self Notes" box, a "My Notebook Ref No" fill-in space, a freeform "My Tag" fill-in space, and a "Revision Phase 1/2/3" tick-box line.
- **New chapter-end page**: "Sanjeevani Booti 2: Error Register for {Chapter}" — a dotted-line blank page (40%-opacity rules) with two sections, "Concepts I Forgot" and "Mistakes I Repeated More Than Twice."
- **New header/footer branding** on every chapter book (Pranav Bhaiya / Newton of Accounts / AIR 1-1-5 / Kahaan-Koncept-Karma) — note this is a static per-file header/footer on the standalone chapter HTML, **not** the print running-header-on-every-physical-page mechanism from §7 below, which lives in the other agent's merge scripts and would need its own follow-up to carry this branding into the merged whole-book print output.
- **Title simplified**: `<h1>`/`<title>` now just `{Standard} — {Chapter Title}`, no "Question Book" suffix.
- **New `first_run/output/How-to-Read-this-Book.md`** — a student-facing guide explaining every colour and field above (and why it exists), so the book's design intent is visible to the reader, not just to the pipeline. Every chapter book's "how this book is organised" note now points here instead of re-explaining conventions inline.

**Explicitly parked, not built this pass** (need more design work or Pranav's direct input before they can be implemented):
- **OP/PP (Original/Practice Problem) recurring-question tags** — the ≥90%-similarity duplicate-detection design already exists (`SKILL-question-bank-duplicate-detection.md`) but was never built; this is real, separate script work, not a quick add.
- **Short chapter/unit names** — proposed as a new field on the canonical topic-page-index JSON (file 1 in the taxonomy table below) to keep the topic-tag display short and consistent; needs Pranav's input to actually draft the ~36 short names before it can replace the full titles the topic tag currently uses.
- Both are named honestly as "coming in a future edition" in `How-to-Read-this-Book.md` rather than silently absent.

Full implementation detail lives in `_claude/skills/SKILL-question-bank-chapter-book-rendering.md` §1 (rewritten this date).

---

## 7. HTML/print architecture — single-source-of-truth styling, page-break safety (added 2026-07-23)

Learned from `Claude_V2.md` §8, §13–16 (the Strategy Book's paged.js work, a separate concurrent effort in this same repo) — read that file's sections 13–16 in full before building any HTML generator/merge script; this is only the distilled, actionable summary. Applies to **all** HTML this repo generates going forward, including the Question Bank Book pipeline above.

**1. One JSON file is the only place geometry/typography numbers live.** A generator script reads it and writes the values into every place they're needed at generation time (CSS custom properties, literal `@page` rules, etc.) — never hand-duplicated, never edited in the generated output directly. Question Bank's version of this: `first_run/schema/book-style.json` (or successor) driving a single generated stylesheet every HTML file links to — so a font-size/margin change is one JSON edit + one script re-run, and *already-generated* HTML files pick it up automatically via the shared `<link>`, no regeneration needed.

**2. `@page` does not reliably resolve `var()`.** If/when this book gets full print pagination, geometry values must be substituted as literal numbers into `@page` at generation time, not referenced via CSS custom properties there (though `var()` is fine everywhere else, e.g. `:root` and the rest of the stylesheet).

**3. Page breaks are never a manual concern if `break-inside: avoid` is set on every content component** (tables, question/answer blocks, boxes) — paged.js then guarantees it never slices one mid-box. Content flows continuously in one HTML file; the tool decides where physical pages fall.

**4. Vendor fonts locally, never `@import` from a network font CDN.** Async font loading races pagination — paged.js can measure/lay out text with fallback-font metrics before the real font finishes loading, then swap fonts after layout is already committed, silently corrupting page counts (confirmed: the same merged document produced wildly different page counts across identical runs, purely from this race).

**5. Repeating headers/footers use `position: running()` + `@page` margin boxes** (`@page { @top-center { content: element(name); } }`) — paged.js clones the running element onto every physical page automatically. Anything cloned into a `@page` margin box this way should have its layout-critical CSS (`display`, `flex-direction`, etc.) set with `!important` — margin-box cloning can silently inject a conflicting inline style otherwise (a real bug: a footer row rendered as a stacked column until `!important` was added).

**6. When merging multiple independently-generated HTML files into one book:** verify the shared stylesheet is byte-identical across files before assuming it's safe to consolidate (don't assume — diff them). Namespace any per-file element IDs that restart per file (e.g. `id="s1"`) with a file/section prefix before concatenating, or they collide. Include shared `<script>`/font-loading tags exactly once in the merged output, not once per source file. Keep the book's section order as an explicit list in the merge script, cross-validated against what's actually on disk in both directions (missing file for a listed section = hard error; a file that exists but isn't listed = loud warning).

**7. Never trust a layout/page-break fix by reading the code alone — verify with a headless-Chrome screenshot** (`--screenshot`, not just `--dump-dom`, which confirms DOM structure but not visual layout — a real bug here rendered correctly in the DOM but visually wrong).
