# CLAUDE.md — Operating Guide for the cap-online repo

**Read this file first, every session. Then read the context in section 1 BEFORE executing any task.**
This repo is CA **Pranav Pratik Tulshyan**'s CA Inter teaching ecosystem for **VC Gurukul, Noida**.
Git root `D:\EffCorp_Projects\cap-online` · remote `EFFICIENTCORPORATES/cap-online` · branch `main`.

---

## 1. Read order (do this first, every session)

1. **CLAUDE.md** (this file) — repo-wide rules and context for every pillar.
2. **README.md** — full repo map, the 6 pillars, and rules.
3. **Claude_V2.md** — deep context for the Strategy Book (Pillar 1) only; read it if the task touches `books/strategy-book/`. It does not cover any other pillar and is never a substitute for this file.
4. **content/README.md** — creative-studio rules (only if the task touches `content/`).
5. **_claude/memory/** — `project_log.md` (newest entry first) and the memory files there.

Then briefly confirm you understand the structure and rules, and wait for the task. Do not start work before this.

---

## 2. Working rules (non-negotiable)

- **Markdown (`.md`) by default.** HTML for books and slides. **No SVGs/diagrams unless explicitly asked.**
- **No binary files in git.** Audio, video, images, office docs, archives, executables are gitignored — they live locally only. Commit only text (md/py/html/json/csv...).
- **UTF-8 only.** Never write NUL bytes or UTF-16. (Cross-mount edits have corrupted files before — `health_check.py` now catches this.)
- **After ANY structural change** (add / move / rename / delete files or folders): run `python tools/health_check.py` and fix everything it flags, then run `python tools/file_index.py`. If you add a new top-level folder, also document it in this file and in `README.md` — `health_check.py` will fail until you do.
- **End every session** by appending a short dated note to `_claude/memory/project_log.md` (newest on top).
- **Ask first when stuck.** At the first genuine doubt or blocker, ASK Pranav — do not guess or spin on workarounds.
- **Pushing:** previously documented as impossible from this sandbox ("needs Pranav's credentials, commit locally, Pranav pushes from his own machine"). **Correction, 2026-07-29**: `git push origin main` succeeded directly from this sandbox when tried — some credential (cached helper, PAT, or similar) is evidently configured in at least this environment. Don't assume this is permanent or true in every clone/session — verify with a real push attempt (or ask) rather than trusting either this note or the old one blindly. If a push fails, fall back to committing locally and telling Pranav to push from his own machine, per the original rule.
- **This repo is worked on by more than one AI session concurrently** (at minimum: Claude Code sessions like this one, and a separate "Codex"-based session — both have directly authored files under `first_run/`, both have committed to `main`, sometimes without the other's clone knowing). **Never assume you're the only author of recent changes.** Before assuming a file is stale, unfinished, or "of unconfirmed origin," check its mtime and actually read it — it may have been built or fixed by the other session since you last looked. A real git-history divergence (the other session pushed straight to `origin/main` while this clone worked from an older commit) already happened once and needed a manual merge — see `_claude/memory/project_log.md`'s 2026-07-27 entries for exactly how it was reconciled if it recurs.

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
| `telegram/` | **Pillar 6** — study bots + their source docs: `bots/` (the bot scripts + their READMEs + `creds.txt`, gitignored), `source-docs/` (generated Excel catalogs — `StudyHub_Master_Catalog.xlsx` is the one the bot actually reads), `assets/study_bot/{Study Materials, Exam Materials, Revision Material}/` (the Study Hub bot's 3 flat, generated category folders, covering CA+CS+CMA together — see section 10), `assets/backup pdfs/` (pre-restructuring backup, not read by anything), `assets/exam_bot/ myfiles_bot/` (the other two bots' content), `tools/` (all the catalog-generation scripts — see sections 8–10) |
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
| `first_run/` | **Workspace proving the Question Bank Book pipeline end-to-end** (added 2026-07-23) before scaling to the full syllabus. **`HOW-TO-BUILD-THE-BOOK.md`** (new 2026-07-27) is the master runbook — read it before running any script below; it has the exact command order, prerequisites, and every fixed-incident gotcha. `source/` (PDFs only, never MD, for every in-scope sitting — see section 6 for why this is enforced structurally now). `schema/` (single-source-of-truth `book-style.json` + generated `book-style.css` + `HTML-SCHEMA.md`). `prompts/` (the 3 external-AI prompts for generating sitting HTML). `scripts/` — Layer 1→2→3 (`extract_questions.py`, `generate_chapter_book.py`, `generate_all_chapter_books.py`), coverage stats (`generate_book_stats.py`), whole-book assembly (`generate_qb_front_back_matter.py`, `generate_qb_toc.py`, `qb_merge.py`, `resolve_qb_toc_pages.py`, `qb_common.py` for shared print/pagination CSS — all built by a concurrent session, see section 2's multi-agent note), and QA round-trip tooling added 2026-08-07 (`extract_book_questions.py`, `diff_book_vs_index.py` — parse the *finished merged book* back into JSON and diff it against `questions_index.json`; see section 6's 2026-08-07 entry). `output/parsed-from-pdf/` (sitting HTML, Layer 1). `output/generated-from-script/` (`questions_index.json`, `book_stats.json`, every chapter book — Layers 2–3). `output/qa/` (added 2026-08-07 — `book_questions_extracted.json`, the finished book re-parsed into JSON, plus `book-vs-index-diff.json`/`.md`, the QA comparison report). `output/` root also holds `front-matter.html`, `table-of-contents.html`, `chapter-coverage-matrix.html`, `back-matter.html`, the final merged `QUESTION-BANK-BOOK.html`, `vendor/` (fonts + paged.js), `final_deliverable/` (already-built, named PDF releases — e.g. `..._V1.pdf`, watermarked `..._V1_protect.pdf` — treat as distributed/ready-to-distribute, never regenerate or overwrite without asking), and the student-facing `How-to-Read-this-Book.md`. See section 6 for full status. Not a permanent pillar — once validated, its lessons fold back into `books/question-bank/`. |

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

## 6. Question Bank Book — current focus (chronological log, 2026-07-22 through 2026-08-08 — read to the end for current state)

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

**Still not built at this point in the timeline**: OP/PP duplicate detection (`SKILL-question-bank-duplicate-detection.md` — designed, not implemented, still true today) and the whole-book merge/"sewing" script (reuse `tools/strategy_book_merge.py` lessons, section 7 below — **the merge script was built and proven end-to-end by 2026-07-27, see that entry below; this note is historical**). Scaling `generate_chapter_book.py` to the other 35 chapters is blocked on more sittings existing — still only 5 of ~17+ sittings are built/tagged.

### Accuracy audit and Phase 2 scaling (2026-07-26): 10 sittings, all 34 touched chapters generated

Two locked decisions from 2026-07-26, both still in force — read `_claude/skills/SKILL-question-bank-phase1-definition-of-done.md` for the full checklist:
1. **MCQ arithmetic gets a full independent re-derivation pass** (found and fixed 6 real errors across the first 5 sittings' 67 MCQ rows — see that skill's §1 and the project log's 2026-07-26 entries for detail). **Descriptive answers get a lighter transcription-fidelity check only** — Pranav explicitly relaxed this bar ("first edition... room for errors") after seeing what the MCQ audit alone had already caught.
2. Every chapter book now carries a reader-facing disclaimer (first-edition status, invite to report errors by email) and labels each Common-Student-Mistakes box **"Examiner's Comment"** (real ICAI-sourced) vs. **"Author's Note"** (synthesized, with an explicit "may not apply in every case" caveat) — a rendering change in `generate_chapter_book.py`, not a change to the underlying data model.

Pranav then asked to scale past the single AS 2 proof-of-concept: 5 more sittings built (`MTP_Jan2026_Set1/Set2.html`, `RTP_Jan2026.html`, `PYQ_Sep2025.html`, `RTP_Sep2025.html`), bringing the pilot to **10 sittings, 275 tagged question rows**. A new batch driver, **`first_run/scripts/generate_all_chapter_books.py`**, queries every unique `final_chapter` in `questions_index.json` and generates a book for each — **34 of the syllabus's 36 chapters are now touched** (only AS 1 and AS 27 remain thin, 2 questions each). All 34 books validated structurally clean. Two real cross-tagging bugs were caught and fixed during this build: a `data-part` free-text drift (same class of bug as the 2026-07-25 fix) and a `unitCode` inconsistency where Branch Accounting and Framework were tagged with both `U0` and `U1` variants across different files — both of which are locked-canonical `U0` single-unit chapters per the earlier migration; left uncaught, either would have silently split one chapter's book into two.

**Still not built at this point in the timeline**: OP/PP duplicate detection and the whole-book merge script, as above (**the merge script is done — see the 2026-07-27 entry below; OP/PP is still genuinely not built**) — several likely-recurring questions were spotted and flagged in extraction-notes during this build (noted for whenever duplicate detection is implemented) but not acted on.

### Scope expanded to 2023+, folder layout reorganized, MD-not-PDF slip fixed structurally (2026-07-26)

Prompted by discovering that the 5 Phase 2 sittings above were built from `.md` conversions instead of the locked PDF-only rule (a real, self-caught deviation — see `SKILL-question-bank-verbatim-extraction.md` §1 for why that rule exists), Pranav made three decisions:

1. **`first_run/source/` now holds PDFs only, never MD.** The 8 MD files that were there were deleted and replaced with the matching PDFs (58 files: MTP Question+Answer pairs, PYQ Answer-only, RTP's single combined doc, plus all 6 real Examiner-Comments PDFs) for every sitting now in scope. This closes the gap structurally — there's no MD file left in that folder to accidentally reach for.
2. **Scope expanded to "everything from 2023 onwards."** Checked against the actual source library: this excludes only 3 older PYQ sittings (Dec 2021, May 2022, Nov 2022) — no MTP/RTP predates 2023 anyway. **34 sittings are now in scope; 10 are built; 24 remain** (7 MTP sessions × 2 sets, 9 PYQ sessions, 4 RTP sessions — see `_claude/memory/project_log.md` for the exact list). Building the other 24 is substantial future work, explicitly not started in this same pass — flagged as needing batched pacing, not a single continuous push.
3. **`first_run/output/` split into two subfolders**: `parsed-from-pdf/` (the 10 sitting HTML files, Layer 1) and `generated-from-script/` (`questions_index.json` + all 34 chapter books, Layers 2–3) — "so we know whatever is parsed from base scratch is separated from script output," in Pranav's words. `extract_questions.py` and `generate_chapter_book.py` were updated to read/write the new paths (one line each); both re-run clean afterward, all 34 books regenerated with no change in content, only location.

Also deleted two stray files flagged back in the 2026-07-22 session and never cleaned up: `MERGE_PDF.py` (a generic PDF-merge utility, unreferenced by any pipeline script) and `MTP_May-24_Set-1 CA-INTER-ACCOUNTS.md` (confirmed pre-rename duplicate of the already-present `CAInter-AdvAcc-MTP-May2024-Set1-*` files).

**At the time, left deliberately untouched** (origin unconfirmed): `first_run/output/QUESTION-BANK-BOOK.html`, `front-matter.html`, `back-matter.html`, and a `vendor/` folder (paged.js + fonts). **Origin since confirmed**: these are a concurrent "Codex" session's whole-book "sewing" pipeline — see the 2026-07-27 entry below for the full, now-complete picture. No longer mystery files.

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

### Whole-book assembly built and proven end-to-end (2026-07-27)

A concurrent "Codex" session (see section 2's multi-agent note) built the entire remaining
half of the pipeline — the pieces the 2026-07-26 entries above still called "not built" —
while this Claude session was focused on the chapter-book UX overhaul: `qb_common.py`
(shared print/pagination CSS, single source of truth per section 7 below),
`generate_qb_front_back_matter.py` (title/copyright/dedication/How-to-Read pages),
`generate_qb_toc.py` (a fully script-owned, always-fresh-rewrite Table of Contents —
fixing a real duplication bug an earlier version had), `qb_merge.py` (the whole-book
"sewing" script, stitching front matter + ToC + all 34 chapters + back matter into one
document), and `resolve_qb_toc_pages.py` (drives headless Chrome over the DevTools
Protocol to read real page numbers post-pagination, since `target-counter()` is a
confirmed-broken CSS feature in the vendored paged.js version — same finding
`Claude_V2.md` §16 already made for the Strategy Book, independently rediscovered here).

This Claude session then took full ownership of that pipeline on Pranav's instruction
("take full control of the entire book and entire flow... go through every file of
another AI"), audited every one of those files, and ran the complete pipeline
end-to-end in one pass. Findings:
- **No major issues.** The one duplication risk flagged in the prior session (this
  script's own richer per-question Student Self Notes/Notebook Ref/Tag/Revision Phase
  block vs. `qb_common.py`'s older, merge-time-injected "Your Notes" strip) had **already
  been found and fixed by the Codex session** before this audit even started —
  `page_shell()` no longer calls `inject_student_notes()`; confirmed by grepping the
  merged output (zero occurrences of the old strip, all new fields present correctly).
- **Two small, real bugs found and fixed directly** (per Pranav's "resolve small bugs
  yourself" instruction): (1) `.qb-howto`/`.qb-legend-*` CSS existed in `qb_common.py`
  but no page anywhere actually used it — a "How to Read This Book" legend page was
  designed but never written; added it to `generate_qb_front_back_matter.py`, condensed
  from `first_run/output/How-to-Read-this-Book.md`, plus 3 more legend swatches so all
  five colour-coded box types (not just two) are explained. (2) `resolve_qb_toc_pages.py`
  passed an unencoded `file://` URL into an HTTP request to Chrome's DevTools endpoint —
  crashed on any repo path containing a space (this clone's does: `.../Other
  computers/...`). Fixed with `urllib.parse.quote()`.
- **Full pipeline run, validated**: `generate_all_chapter_books.py` →
  `generate_book_stats.py` → `generate_qb_front_back_matter.py` → `generate_qb_toc.py` →
  `qb_merge.py` → `resolve_qb_toc_pages.py --remerge`. Final `QUESTION-BANK-BOOK.html`:
  **307 pages**, all 34 chapters' ToC page numbers correctly resolved and baked in,
  validated clean (0 unclosed tags, 0 duplicate ids, 0 NUL bytes, 0 leftover
  build-info/extraction-note text, 0 duplicate notes strips).

**New file**: `first_run/HOW-TO-BUILD-THE-BOOK.md` — the master end-to-end build
runbook (architecture, folder map, prerequisites, exact command sequence, a
what-needs-re-running-after-X-changes table, and every fixed-incident gotcha above in
full detail). Read it before running any script in `first_run/scripts/`.

**Still genuinely not built** (confirmed current as of this date): OP/PP duplicate
detection and short chapter/unit names — both as described earlier in this section,
both still named honestly as "coming in a future edition" in the book's own front matter.

### Scaling to all 34 sittings + two new locked decisions (2026-07-28)

Pranav asked to scale the pipeline past the 10-sitting pilot to all 24 remaining
in-scope sittings, using the `first_run/pending/` PDFs + `first_run/output/
pending-pdf-parsed-clean/` cleaned-MD aids (see that folder's own docstring in
`clean_pending_md.py`) as the batch's source material — **PDF is still the accuracy
source of truth per sitting; the cleaned MD is a typing aid only**, same rule as
before. Built via parallel background agents, one per sitting, each independently
self-validating (structural HTML checks + independent MCQ arithmetic re-derivation
per `SKILL-question-bank-phase1-definition-of-done.md` §1) and then spot-verified a
second time by the orchestrating session before being trusted — batched ~3-5 at a time
with a checkpoint after each, per the pacing this section already recommended. **Done
as of 2026-07-28**: all 24 remaining sittings built, all 34 in-scope sittings now
exist, full pipeline (extraction → 34 chapter books → stats → front/back matter → ToC
→ merge → page-number resolution) rebuilt end-to-end: **796-page `QUESTION-BANK-
BOOK.html`**, 437 distinct questions, 3,096 total marks, 68 real ICAI Examiner's
Comments matched. Full detail in `_claude/memory/project_log.md`'s 2026-07-28 entries.
Two mid-build account spend-limit hits were absorbed without data loss because every
sitting-build agent is instructed to write to disk as early as it has a solid draft
and refine in place — worth keeping that instruction in any future batch of this kind.

**New finding during this batch, now a locked handling rule**: several of the older
(2023) MTP/PYQ sittings test topics from **before a syllabus change** that don't exist
anywhere in the current 36-chapter taxonomy at all (Hire Purchase, Departmental
Accounts, Incomplete Records, Insurance Claims for Loss of Stock, Redemption of
Debentures/Preference Shares, Profit Prior to Incorporation, Bonus Shares, Managerial
Remuneration — found across `PYQ_May2023.html`, `MTP_May2023_Set1.html`,
`MTP_May2023_Set2.html`). **Pranav's decision**: tag these `data-unitcode`/
`data-final-chapter="LEGACY-{TOPIC-SLUG}"` + `data-issue="topic-legacy-not-in-current-
syllabus"` — the sitting HTML stays a complete, accurate record, but these records are
**excluded from the generated chapter books** (no chapter exists for a LEGACY code) as
the book is scoped to the current syllabus. No appendix for them in this edition. This
is distinct from `topic-unindexed` (AS 1/AS 27 — genuinely *in* the current syllabus,
just not yet in `topic-index.json`).

**OP/PP explicitly out of scope for this (first) edition** — not just "still not
built" as stated above, but a deliberate scope decision: Pranav's call, 2026-07-28,
is to publish the first edition without it and revisit OP/PP as a dedicated
post-launch effort once the full 34-sitting corpus exists (the ≥90%-similarity
comparison is O(n²) over the whole corpus — running it against a partial corpus now
would mean redoing it later for no benefit anyway). Don't build this for edition 1
even if it looks like a quick win partway through.

**Two new features locked in for this edition, not yet built** (Pranav, 2026-07-28) —
both are pure derivations from `questions_index.json`, no new tagging work needed:

1. **Chapter-wise Sitting Summary** — a marks-coverage matrix (rows = 36 chapters,
   columns = sittings, cell = marks tested), placed near the front matter/ToC. Full
   34-column width doesn't fit A4 print, so: **one column per exam session, not per
   individual paper/set** (an MTP session's Set 1 + Set 2 collapse into one column —
   brings MTP to ~7 columns, matching RTP's 7 and PYQ's 9), split into **three
   separate tables, one page each: MTP, RTP, PYQ** (Pranav's proposed fix for the
   width problem), each with a row-summed **Total** column at the end — that total,
   sorted descending, doubles as a "which chapters actually matter most" ranking.
2. **Topic-wise Summary at the start of each chapter book** — same idea one level
   deeper: rows = that chapter's subtopics, columns = sittings, cell = marks. This
   formalizes and automates what Pranav already built by hand for the AS10 pilot
   sample (`books/question-bank/metadata-index/AS10_Question_Reference.html`'s
   "topic-wise weightage summary" — this is that same table, generated, for every
   chapter). Usually narrow enough (a chapter typically has a handful of subtopics)
   to need only one table, not the three-way MTP/RTP/PYQ split — fall back to that
   split only for the busiest chapters (AS 2, AS 10, Framework) if row width becomes
   a real problem in practice, don't split by default.

**Both built 2026-07-28**, same session the 34-sitting corpus was completed. Chapter-
wise Sitting Summary: `first_run/scripts/generate_qb_coverage_matrix.py` →
`chapter-coverage-matrix.html`, merged into the book right after the ToC. Per-chapter
Topic-wise Summary: built into `generate_chapter_book.py`, one per chapter, right
after each chapter's intro notes. **Real mid-build finding**: a single busy chapter's
combined MTP+PYQ+RTP session table hit 22 columns (AS 2, tested in nearly every
sitting) — the identical print-width problem the whole-book matrix was designed to
avoid, rediscovered one level deeper. Fixed by applying the same MTP/PYQ/RTP split at
chapter granularity too. Full detail: `first_run/HOW-TO-BUILD-THE-BOOK.md` §5/§6.

### Print-cost reduction pass (2026-07-28) — 819 → 688 pages

Pranav reviewed the merged book for print cost and sent a punch list, all implemented:
empty Descriptive/Integrated sections now omitted entirely (not printed with a "no
questions" placeholder); the repeated per-box Author's Note/Examiner's Comment
provenance sentence removed (stated once in front matter instead); the 3-line student
fields (Notebook Ref/My Tag/Revision Phase) collapsed into 1 line, renamed "My NB Page
No"; the Error Register changed from 34 per-chapter full pages to ONE shared 6-page
appendix at the back; the per-question topic line no longer repeats the chapter name
(shows only the specific topic, via a new `qb_common.abbreviated_topic_label()`); the
coverage matrix's chapter column uses file 1's `chapter_name_short` plus CSS wrapping.
**Real bug found and fixed in the same pass**: the Topic-wise Marks Mapping table was
showing the same chapter-level title on every row instead of each row's actual topic
name — `extract_questions.py` never captured `data-subtopictitle` (present on the
source tags all along); Pranav also added a new `topic_name_abbvtd` field to file 1
specifically for this. Margins checked but left unchanged (already at a documented
6mm print-safety floor). **Result: 688 pages**, all from removing genuine repetition,
no content cut. Full detail: `first_run/HOW-TO-BUILD-THE-BOOK.md`'s "Print-cost
reduction pass" entry and its two new gotchas.

### Current state as of 2026-08-07 (read this if you're new to the session)

`QUESTION-BANK-BOOK.html` is **688 pages, 455 questions, 34 chapters**, built from
the full 34-sitting corpus (2023–2026, per the 2026-07-26 scope decision above).
Verified clean — see the QA tooling below. Two things still genuinely open:
**OP/PP duplicate detection** and **short chapter/unit names** (both explicitly
deferred to a future edition, see the 2026-07-28 entries above) — don't build either
without asking, per the locked scope decision. `first_run/output/final_deliverable/`
holds already-built "V1"/"_protect" (watermarked) PDF releases dated 2026-07-28/30 —
**these predate the 2026-08-07 fix below and are now stale**; treat that folder as a
distributed/ready-to-distribute deliverable and never regenerate or overwrite it
without asking — if a corrected PDF is wanted, that's an explicit separate ask.

### QA round-trip tooling built, and a real cross-taxonomy bug found + fixed (2026-08-07)

Pranav asked for a script converting the finished `QUESTION-BANK-BOOK.html` back into
JSON. Clarified first: scope = questions only, purpose = QA/round-trip verification
against `questions_index.json`, not a new data source — this shaped everything below.

**Two new scripts, `first_run/scripts/extract_book_questions.py` and
`diff_book_vs_index.py`** (companion pair to `extract_questions.py`, but for the
*output* end of the pipeline instead of the input end):
- `extract_book_questions.py` parses the real merged book (all 34 `.qb-section`
  chapters, `.qblock` by `.qblock` — no `data-*` attributes at this stage, everything
  is baked into rendered display text) into `first_run/output/qa/
  book_questions_extracted.json`. Exports `parse_qblock()` for reuse.
- `diff_book_vs_index.py` is the actual QA tool: for every `questions_index.json` row
  that `generate_chapter_book.select_chapter_rows()` (new — factored out of
  `build_book()`, behavior-preserving, verified byte-identical output before/after)
  says belongs in the book, it **regenerates that row's exact qblock HTML via the
  real `render_qblock()`**, parses it with the same `parse_qblock()`, and diffs
  field-by-field against what's actually in the book. Both sides call the real
  pipeline functions — no label/selection logic re-derived — so a diff is real drift,
  not two parsers disagreeing. Validated with a positive control (real row, byte-
  identical) and a negative control (corrupted fields, correctly flagged) before
  trusting a clean run. Output: `first_run/output/qa/book-vs-index-diff.json`/`.md`.
- Re-run either any time after a full pipeline rebuild — they always parse the book
  fresh, no stale intermediate state possible.

**First real run found a genuine bug**: 27 of 455 questions came back "orphan" (in
the book, no matching expected row) — all 27, no exceptions, were the Cash Flow
Statement chapter. Root cause: `qb_merge.py`'s `CHAPTERS` tuple listed
`study_ref = "M1-C4-U2"` for that chapter, but every one of its 27 tagged questions in
`questions_index.json` — and `generate_all_chapter_books.py`'s own
`NON_AS_SLUGS`/`TITLE_OVERRIDES` table, which is what actually pulls the chapter's
content — uses `"M3-C11-U2"` instead. **Both codes are real, distinct entries** in
`1-ca-inter-adv-accounts-topic-page-index.json` (`M1-C4-U2` = the standalone AS 3
chapter under Module 1, 11 topics; `M3-C11-U2` = the Cash Flow unit inside Module 3's
"Financial Statements of Companies" chapter, 7 topics) — a real duplicate-chapter
situation like the U0/U1 one earlier in this section, not a typo, and one **already
flagged and resolved toward `M3-C11-U2` elsewhere** (`books/question-bank/mcq_bank/
tag_batch01.py`'s tagging notes, `topic-index.json`'s `lastUpdated` note) — this was
the one place that decision had never propagated to. Consequence in the *published*
book before the fix: the chapter's "Study Material Reference" banner, its ToC
cross-reference, **and** its row in the Chapter-wise Sitting Summary all pointed at
`M1-C4-U2` — the coverage-matrix row showed **zero marks in every sitting** for Cash
Flow Statement as a result (real questions existed, just tagged under a different
code than the matrix was reading numbers from).

Pranav confirmed: point everything at `M3-C11-U2`. Fixed the one `CHAPTERS` tuple
entry in `qb_merge.py` (comment there explains the history), then re-ran exactly what
`HOW-TO-BUILD-THE-BOOK.md`'s "what needs re-running" table calls for on a `CHAPTERS`
change: `generate_qb_coverage_matrix.py` → `generate_qb_toc.py` → `qb_merge.py` →
`resolve_qb_toc_pages.py --remerge` (real headless-Chrome pagination). Result: still
688 pages, Cash Flow Statement still lands on page 393 (content length unchanged,
only the reference code and matrix numbers changed). All of Step 7's validation
assertions pass. Re-ran the new QA tool: **455/455 matched, 0 missing, 0 drifted, 0
orphan** — confirmed clean, and this is now the expected steady state after any
future full pipeline rebuild too.

Grepped the whole repo for every `M1-C4-U2` occurrence to check for other drift
(Pranav explicitly asked for full consistency, not just the banner): confirmed
`generate_qb_toc.py` and `generate_qb_coverage_matrix.py` both import `CHAPTERS`
directly from `qb_merge.py` (single source of truth, nothing else to fix). Every
other `M1-C4-U2` occurrence in the repo is legitimate — the real Module 1 AS 3
chapter entry in files 0/1, and the `mcq_bank/` pipeline's own already-correct notes
about this same duplicate.

### Marketing one-pager built for the launch video (2026-08-08)

Pranav asked Claude to independently review the finished book and list what's
genuinely worth marketing, then drafted his own feature pitch and asked for feedback,
then asked for it built as an HTML one-pager for a launch video he's making. Built
`content/productions/question-bank-launch/deck/question-bank-onepager.html` — see
that folder's own `README.md` for full detail (design intent, hero line, why the MCQ
mention is placed last and names `1Lavya.com` only as one neutral non-endorsed
example per Pranav's explicit instruction not to be seen as associated with it).

Deliberately reuses the *book's own* CSS colour language (tan/pink/green
Examiner's-Comment/Author's-Note/Answer coding, the `Marks · Approx Time · Topic`
line, the dotted-line Error Register) rather than inventing a separate marketing look
— so the promo page reads as a page out of the book itself. The two facsimile
"exhibits" on the page are genuine excerpts (the AS 10 Preet Ltd. PPE question and its
real Author's Note), not invented examples. Fonts (Fraunces + IBM Plex Sans + IBM Plex
Mono) are embedded as base64 data URIs so the file is fully self-contained.

**Not yet done — needs Pranav's input before this goes live**: no purchase link, no
price, and no contact address are wired in yet (left as visible placeholders, not
invented). Also published as a Claude Artifact (URL in that folder's README) — the
repo copy in `deck/` is the persistent source of truth; redeploy the Artifact from
that file if it's edited further.

---

## 7. HTML/print architecture — single-source-of-truth styling, page-break safety (added 2026-07-23)

Learned from `Claude_V2.md` §8, §13–16 (the Strategy Book's paged.js work, a separate concurrent effort in this same repo) — read that file's sections 13–16 in full before building any HTML generator/merge script; this is only the distilled, actionable summary. Applies to **all** HTML this repo generates going forward, including the Question Bank Book pipeline above. For the Question Bank Book's own concrete instances of every principle below (which files, which bug, which fix) see `first_run/HOW-TO-BUILD-THE-BOOK.md` §5 rather than re-deriving them — several of the same root causes (CORS-blocked font `<link>`s, flex-fragmentation across page breaks, `target-counter()` being broken) were independently rediscovered there and are already written up in full.

**1. One JSON file is the only place geometry/typography numbers live.** A generator script reads it and writes the values into every place they're needed at generation time (CSS custom properties, literal `@page` rules, etc.) — never hand-duplicated, never edited in the generated output directly. Question Bank's version of this: `first_run/schema/book-style.json` (or successor) driving a single generated stylesheet every HTML file links to — so a font-size/margin change is one JSON edit + one script re-run, and *already-generated* HTML files pick it up automatically via the shared `<link>`, no regeneration needed.

**2. `@page` does not reliably resolve `var()`.** If/when this book gets full print pagination, geometry values must be substituted as literal numbers into `@page` at generation time, not referenced via CSS custom properties there (though `var()` is fine everywhere else, e.g. `:root` and the rest of the stylesheet).

**3. Page breaks are never a manual concern if `break-inside: avoid` is set on every content component** (tables, question/answer blocks, boxes) — paged.js then guarantees it never slices one mid-box. Content flows continuously in one HTML file; the tool decides where physical pages fall.

**4. Vendor fonts locally, never `@import` from a network font CDN.** Async font loading races pagination — paged.js can measure/lay out text with fallback-font metrics before the real font finishes loading, then swap fonts after layout is already committed, silently corrupting page counts (confirmed: the same merged document produced wildly different page counts across identical runs, purely from this race).

**5. Repeating headers/footers use `position: running()` + `@page` margin boxes** (`@page { @top-center { content: element(name); } }`) — paged.js clones the running element onto every physical page automatically. Anything cloned into a `@page` margin box this way should have its layout-critical CSS (`display`, `flex-direction`, etc.) set with `!important` — margin-box cloning can silently inject a conflicting inline style otherwise (a real bug: a footer row rendered as a stacked column until `!important` was added).

**6. When merging multiple independently-generated HTML files into one book:** verify the shared stylesheet is byte-identical across files before assuming it's safe to consolidate (don't assume — diff them). Namespace any per-file element IDs that restart per file (e.g. `id="s1"`) with a file/section prefix before concatenating, or they collide. Include shared `<script>`/font-loading tags exactly once in the merged output, not once per source file. Keep the book's section order as an explicit list in the merge script, cross-validated against what's actually on disk in both directions (missing file for a listed section = hard error; a file that exists but isn't listed = loud warning).

**7. Never trust a layout/page-break fix by reading the code alone — verify with a headless-Chrome screenshot** (`--screenshot`, not just `--dump-dom`, which confirms DOM structure but not visual layout — a real bug here rendered correctly in the DOM but visually wrong).

---

## 8. Telegram Study Hub Bot — catalog pipeline (built 2026-08-07)

Pillar 6's `telegram/bots/study_hub_bot.py` sends CA study-material PDFs to students via a
Course→Level→Subject→Chapter menu or free-text fuzzy search. It has no database — an
Excel file (`telegram/source-docs/1Lavya_Study_Hub_File_Mapping.xlsx`) is its whole
catalog/search index, and it serves PDFs from one flat folder
(`telegram/assets/study_bot_flat/`). Both are **generated**, not hand-built — full detail,
including why every design decision was made, is in
`_claude/skills/SKILL-study-bot-catalog-pipeline.md`; this is the short version.

**What existed before this date**: 380 real ICAI study-material PDFs (CA Foundation ×4
subjects, CA Inter ×8 paper-sections, CA Final ×5 subjects) sitting in a *nested*
`telegram/assets/study_bot/<course-slug>/Module N/*.pdf` tree with `.md` siblings from an
earlier conversion pass, plus a completely blank Excel template (3 example rows). The
bot's own code assumes one flat folder with globally-unique filenames — but ICAI's own
naming collides badly (`M1_C0_U1_ Initial Pages.pdf` alone repeats 12× across courses),
so flattening naively would have silently overwritten files.

**What was built**: two scripts under `telegram/tools/` —
`scan_study_bot_source.py` (read-only: extracts real page-1 text from every PDF via
`pypdf` and fuzzy-scores it against the filename's stated title, so nothing is trusted
without being checked against actual content — Pranav's explicit instruction, "this will
be the last time we will be checking it... accuracy shall be required") and
`build_study_bot_catalog.py` (writes: copies every PDF into the flat folder under a new
name — `{Course}{Level}-{SubjectShort}-{Session}_M{n}-C{n}-U{n}_{ShortTitle}.pdf`, e.g.
`CAInter-AdvAcc-May26_M1-C4-U2_AS3CashFlowStatement.pdf` — and generates the Excel
catalog from scratch). Both are idempotent and safe to re-run; **never hand-edit the flat
folder or the Excel directly**, they will drift out of sync with each other.

The verification pass caught three real filename defects (not hypothetical) by reading
actual PDF content: a corrigendum file with no parseable naming pattern at all, two CA
Final Advanced Auditing chapters whose title field was literally the word "Untitled" (real
content: Chapter 14 Units 1–2, "Special Features of Audit of Banks" / "...of NBFCs"), and
two CA Foundation Quantitative Aptitude files filed under chapter/module `0` that are
actually real Chapters 13 and 14 (confirmed via the printed chapter number on each PDF's
own first page). All three are documented, with reasoning, in the script's
`TITLE_OVERRIDES` table — never silently corrected with no trace. All 17 subjects'
official paper names/numbers were likewise read off each subject's own "Initial Pages"
cover PDF rather than assumed.

Per Pranav's explicit choice: the nested source tree (both the 380 PDFs and their 216
`.md` siblings) was **deleted** after the flat copy was verified complete (380 source
PDFs == 380 flat PDFs == 380 Excel rows, zero filename collisions) — "delete the older
version to avoid duplication." If this pipeline needs to run again from scratch (a new
session's PDFs, a new subject), re-source a same-shaped nested tree first.

Also fixed in the same pass: `study_hub_bot.py` no longer hardcodes a live bot token as
its env-var fallback (a real exposure — the token was sitting in plaintext in the script
*and* in `telegram/creds.txt`, neither gitignored) — it now reads its token from
`telegram/creds.txt` at runtime (parsed, never hardcoded) or `TELEGRAM_STUDY_BOT_TOKEN`.
`.gitignore` gained a "Secrets / credentials" section (`telegram/creds.txt`, `**/creds.txt`,
`*.env`) plus a blanket `desktop.ini` rule (54 stray Windows metadata files were sitting
untracked in the old nested tree alone). `EXCEL_PATH`/`FILES_FOLDER` in the bot script are
now resolved repo-relative from `Path(__file__)` instead of hardcoded to a `D:\Eklavvia\...`
path outside this repo entirely — the bot now actually runs against this repo's own data,
smoke-tested end to end (catalog loads, browse flow, free-text search, file-on-disk
resolution all verified working against the real 380-row catalog).

One expected (not a bug) finding surfaced by testing free-text search: some topics
legitimately return two results because ICAI's own study material repeats them under two
different chapters (e.g. "cash flow statement" matches both `M1-C4-U2` — the standalone
AS-3 chapter — and `M3-C11-U2` — Cash Flow Statement inside "Financial Statements of
Companies") — the exact same duplicate-chapter-code situation already documented in
section 6's 2026-08-07 QA entry for the Question Bank pipeline, independently
rediscovered here in a different corpus.

**Not done, deliberately**: CS/CMA content (the bot's README has always described
CA/CS/CMA; only CA material has ever existed on disk — adding CS/CMA later is just new
`COURSE_META` entries in `build_study_bot_catalog.py` once those PDFs exist in the same
nested-tree shape).

**Post-deployment bug found and fixed (same day):** Pranav live-tested the bot and hit
`telegram.error.BadRequest: Button_data_invalid` searching "Inventories". Cause: Telegram
inline-button `callback_data` has its own 64-byte limit, unrelated to filesystem/path
limits — the bot embedded the (sometimes 80+ char) `FileName` directly into
`callback_data`, which overflows for 192 of the 380 files, plus the Subject-picker step
had the same bug via long subject names (23 rows). Fixed in `study_hub_bot.py`: every
callback now carries a small integer catalog-row-id (or a subject-list index) instead of
the literal string, resolved back via `Catalog.get_row_by_id()`. Verified by generating
every possible callback string across the full browse tree + several free-text queries —
max is now 23 bytes. Full writeup: `SKILL-study-bot-catalog-pipeline.md` §6.

**CS/CMA content sourced the next day (2026-08-08)** — the "not done" note above is now
in progress: see section 9.

---

## 9. CS / CMA Chapter Catalog — ToC extraction pipeline (built 2026-08-08)

Pranav added CS (Company Secretary) and CMA (Cost & Management Accountant) study
material — 50 PDFs across `telegram/assets/{CS Exce, CS Prof, CS EET, CMA Final, CMA
Found Study mat, CMA Inter Study Mat}/`. Unlike ICAI's CA material, ICSI/ICMAI ship **one
consolidated PDF per subject** (every chapter in one file, no per-chapter split, no
usable embedded bookmarks). Full detail, including every parsing bug found and fixed, is
in `_claude/skills/SKILL-cs-cma-toc-pipeline.md`; this is the short version.

Pranav's instruction: use each PDF's own printed Table of Contents to work out
chapter-wise page ranges, capturing **both** the printed page range and the actual PDF
page range (since "our Python code will only understand the page of the PDF and not the
printed page"), plus a full and an abbreviated (button-width) chapter name and the
planned final split-PDF filename — all in one Excel catalog, generated by script, **as a
first stage before any actual PDF splitting** ("make this complete Excel file first").

**Built**: `telegram/tools/cs_cma_common.py` (per-file Course/Level/Subject metadata,
read from each PDF's own cover page, not guessed — including catching that CMA
Intermediate's "Paper 7" is one syllabus paper split across two study-note volumes,
Direct/Indirect Taxation, kept as `7A`/`7B` the same way CA Inter's GST/Income-tax split
already is); `telegram/tools/scan_cs_cma_toc.py` (Stage 1 — two ToC parsers, one per
publisher format, plus a content-matching offset detector and per-chapter verification,
same discipline as the CA pipeline); `telegram/tools/build_cs_cma_catalog.py` (Stage 2 —
short titles, final filenames, the Excel itself:
`telegram/source-docs/CS_CMA_Chapter_Catalog.xlsx`).

**Result**: 647 chapters extracted across all 50 files. A random 12-row independent
spot-check (re-reading the actual PDF pages fresh, not trusting the pipeline's own
self-reported scores) confirmed every one correct. Two rows needed an explicit,
documented correction rather than trusting the source verbatim: two genuine typos in
ICMAI's own printed ToC ("Operatinal"/"Diefferent", corrected against the real chapter
page) and one ICSI lesson that its own book states was merged into an earlier lesson
(listed with a Notes explanation, no fabricated page range). Both are named honestly in
the catalog's `Notes` column, never silently applied.

**Not built yet, deliberately** (scope locked to "Excel catalog first" — don't build
without asking): actually splitting the 50 consolidated PDFs into per-chapter files using
this catalog's page ranges, and wiring the result into `study_hub_bot.py` (which
currently only serves CA content).

**Both of those "not built yet" items are done as of the next day — see section 10.**

---

## 10. Study Hub Bot unified for CA + CS + CMA, 3 material categories (built 2026-08-08/09)

Pranav split the PDF-splitting work in §9 into its own step: asked for (and reviewed
before running) a `telegram/tools/split_cs_cma_pdfs.py` script that reads
`CS_CMA_Chapter_Catalog.xlsx`'s page ranges and actually writes one PDF per chapter —
built with a safe dry-run default (prints the plan, writes nothing) and an explicit
`--execute` flag, wipes-and-rebuilds its output folder idempotently, skips/logs any bad
row instead of crashing the batch. Pranav ran it himself; output matched the catalog
exactly (646 files, byte-for-byte the naming this script predicted).

He then **restructured `telegram/assets/` entirely**: replaced the separate per-course
flat folders with `telegram/assets/study_bot/{Study Materials, Exam Materials, Revision
Material}/` and populated them — 1,026 Study Materials files (380 CA + 646 CS/CMA, i.e.
his own split-script output merged with the CA bot's existing flat folder) and 58 Exam
Materials files (CA Inter Advanced Accounting MTP/PYQ/RTP papers, filenames already
self-describing: `{CourseLevel}-{Subject}-{PaperType}-{Session}[-SetN]-{Q|Ans}.pdf`).
Asked for `study_hub_bot.py` to be rewritten to match the new folder layout and serve
all three courses (CA/CS/CMA), not just CA.

**Built `telegram/tools/build_master_catalog.py`**: the one catalog the bot now actually
reads (`StudyHub_Master_Catalog.xlsx`), merging the CA catalog + the CS/CMA catalog (both
remapped into one unified schema) with Exam Materials parsed directly from its
already-self-describing filenames (a small 9-entry table splits `CAInter`-style prefixes
back into Course+Level; Subject full names are resolved by matching filename prefixes
against the already-loaded Study Materials rows, no separate table needed). Self-cross-
checks against disk every run, both directions (every catalog row ↔ a real file) — clean
on the first run: 1,084 total rows, zero mismatches.

**Rewrote `study_hub_bot.py`**: new browse tree Category → Course → Level → Subject →
(Chapter, or Paper Type → file for Exam Materials) — every level computed dynamically
from the catalog (no hardcoded course/level lists), so new courses/subjects/sessions
just appear once catalogued, no bot code changes needed. An empty category (Revision
Material today) shows "not available yet" instead of a broken empty menu. Extended the
already-learned 64-byte `callback_data` lesson (§8) one level deeper — Category and the
new Paper-Type step both follow the same index-not-literal-string rule. Verified for
real: generated every possible `callback_data` string across the entire current browse
tree (1,172 of them) — max 25 bytes. Smoke-tested against the real catalog + real files
on disk: full tree traversal, free-text search across all 3 courses and Exam Materials,
and a 15-row random sample of `send_file()`'s path resolution — all correct.
