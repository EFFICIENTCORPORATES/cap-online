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
  - Stray files still to clean up: `MERGE_PDF.py` (utility script, not content) and a duplicate leftover `MTP_May-24_Set-1 CA-INTER-ACCOUNTS.md` (pre-rename artifact).
  - **For a full per-attempt view** (which sittings have PDF/MD/Parsed/JSON, and exactly what's missing) see `books/question-bank/question_bank_index_by_attempt.csv` (new, 2026-07-22) — more useful than `question_bank_index.csv` for pipeline-status questions; that file stays as the per-*file* conversion QA record.
- **`Parsed_PDF_Question_Bank_CA_Inter_Accounts/`** — the clean target format: complex accounting tables (ledgers/BS/working notes) become HTML `<table class="accounting-table">` blocks embedded in the `.md`. **Only 3 of ~55 files parsed so far** (one MTP — May2024 Set1, one PYQ — Jan2026, one RTP — May2026 — explicitly a pilot). All 3 are now fully tagged (see below) — parsing the remaining ~52 raw conversions into this format is the next big lever for growing tagged coverage.
- **`metadata-index/`** — the topic-tagging work:
  - **`TAGGING-SCHEMA.md`** (new, 2026-07-22) — the schema spec: which of the two taxonomies to tag against (`topic-index.json`'s `unitCode`+`subtopicRef`, not the locked master syllabus JSON's IDs), the U0/U1 reconciliation table, and the lean per-question JSON shape (`mdAnchor` pointing into the parsed `.md`, content never duplicated). Read this first before tagging anything else.
  - `topic-index.json` — reference index of ICAI units; now covers **32 of 36** syllabus units (up from 22 this session — added AS16, AS28, AS18, AS5, AS24, AS7, AS22, AS25, AS15, AS17 as stub entries: heading lists only, not yet individually described like the original 22 are). Only **AS 1** (Disclosure of Accounting Policies) and **AS 27** (Joint Ventures) remain genuinely untouched by any tagged question.
  - `MTP_Jan2025.json` — the original pilot (1 sitting), embeds full question/answer HTML inline — left as-is, not worth reprocessing, but no longer the pattern to follow.
  - **`MTP_May2024_Set1.json`, `PYQ_Jan2026.json`, `RTP_May2026.json`** (new, 2026-07-22) — the 3 parsed-pilot sittings, fully tagged question-by-question using the lean schema. That's **4 of ~17 sittings tagged** now (up from 1). Remaining ~13 sittings are blocked on the parsing step above, not tagging.
  - `AS2_Question_Reference.html` — a separate, ad hoc, single-standard (AS 2 only) cross-reference across the whole corpus; useful but not integrated into the systematic per-question scheme above — don't extend this approach to other standards, use the systematic scheme instead.
- **`pyq/ mtp/ rtp/ solutions/`** — dead, empty except `.gitkeep`. An abandoned v1 layout the README still describes; don't populate these, real content lives in the three folders above.

### The chapter/topic taxonomy (for mapping questions → chapters)
- **Canonical source: `books/concept-book/syllabus-engine/data/0-ca-inter-adv-accounts-subtopics-marks-weightage.json`** — marked "locked, never edit." All 36 chapters (teaching-sequence order) + 436 topics + marks-by-attempt back to May-2018, diagnostics confirm no gaps. IDs: `unique_chapter_id` = `M{module}-C{chapter}-U{unit}` (e.g. `M2-C5-U1` = AS 2 Valuation of Inventories); `unique_topic_id` = `{unique_chapter_id}-T{topic_no}` (e.g. `M2-C5-U1-T1.3`).
- `books/question-bank/metadata-index/topic-index.json` already tags questions using its **own** scheme (`unitCode` + raw ICAI paragraph `sections[].ref`) — this is the *operative* scheme in use today, but covers only 22/36 units and doesn't reuse `unique_topic_id`.
- **Mismatch to reconcile before joining the two:** for the 7 single-unit chapters (Intro to AS, Applicability, Framework, Buyback, Internal Reconstruction, Branch Accounting, Amalgamation-of-Cos), the master JSON uses `U0` (e.g. `M1-C1-U0`) while `topic-index.json` and the raw ICAI source filenames use `U1` (`M1-C1-U1`) for the same chapter. Normalize this before any automated join between the two files.
- `books/concept-book/chapters/*.md` bracket tags (`[AS2-1.2]`, `[FW-1]`) exist for only 2 of 36 chapters and aren't formatted consistently with each other — don't treat these as a taxonomy source.
- `mcq-platform/` (Pillar 5, currently empty scaffolding) has already committed in its own README to deferring to syllabus-engine's IDs — no competing scheme to reconcile there.
- **Recommended default:** tag each question with `unique_chapter_id` (always) and `unique_topic_id` (where determinable) from the master syllabus JSON — it's the one taxonomy with full 36-chapter coverage and no known gaps.

### Also relevant, thin/empty so far
- `books/concept-book/chapters/` — only 2 of 36 chapters authored (`seq03-framework`, `seq04-as02`). Most of the syllabus has no concept-book content yet.
- `books/concept-book/revision-material/` — completely empty; no error-register/exam-marking structure exists yet to cross-reference against question topics.

### The ultimate goal: a per-chapter "Question Bank Book" for students (locked in 2026-07-22)

Tagging isn't the end product — it's infrastructure for a **student-facing "go-to book for practice"**, one HTML book per AS/chapter, collecting every question across MTP/RTP/PYQ that tests that chapter, with official answers, topic tags, and (new) authored "Common Student Mistakes." Pranav built a hand-crafted target sample at
`books/question-bank/metadata-index/AS10_Question_Book.html` (AS 10, ~58 questions) — **read this file before doing any chapter-book work**; it is the concrete quality bar. Structure: an intro/scope note (question count, explicit inclusions/exclusions with reasons), a flagged-issues note (every low-confidence answer named explicitly), an organisation note (topic ordering + recurring-question policy), then three sections — **I. MCQs, II. Descriptive (pure chapter), III. Integrated (cross-standard)** — each question as a card with source/marks/topic/badges, verbatim question+answer HTML, Common Student Mistakes, and an Extraction-note transparency line. Note: the AS10 sample references files that don't exist in this repo yet (`AS10_Question_Reference.html`, `question-book-implementation-plan.md`, `AS10_Question_Bank.json`, an `icai-practice-extraction/` folder) — it was built as a separate one-off deep-dive, not through the `topic-index.json` pipeline below. **Pranav is going to share more AS10 sample files later** — reconcile our schema against them when they arrive, don't assume our schema is final yet.

**Two strategic decisions locked in (confirmed by Pranav, do not revisit without asking):**
1. **Tag every sitting comprehensively once, for every chapter it touches — never do one-off chapter-by-chapter re-scans of the source PDFs.** This is why `MTP_May2024_Set1.json` etc. tag *all* topics in a sitting, not just one chapter. Once a sitting is tagged, every future chapter-book query is "read the JSON," not "re-read the PDF."
2. **Render chapter books with a reusable generator script**, not hand-assembled HTML per chapter — analogous to `tools/strategy_book_parser.py` for the Strategy Book. One template + one script; a styling/structure fix happens once, not 36 times. Not yet built (`tools/question_book_generator.py` doesn't exist yet) — build it once the schema is reconciled against Pranav's fuller AS10 sample set.

### Two new authored content layers (added 2026-07-22, schema updated in `TAGGING-SCHEMA.md`)

**`commonMistakes`** — did not exist anywhere before this session. Real ICAI **"Examiners' Comments on the Performance of the Examinees"** documents exist for exactly 6 PYQ sittings (Jan 2025, May 2024, Sep 2024, May 2025, Sep 2025, Jan 2026) — Pranav sourced these as new raw PDFs; converted and sliced to their Paper-1-only section at `Raw_PDF_Question_Bank_CA_Inter_Accounts/examiner-comments-paper1/Paper1-ExaminerComments-{Session}.md`. From analysing all 6, wrote `books/question-bank/metadata-index/examiner-comments-writing-skill.md` — a style guide (opening-quantifier vocabulary, failure-mode + standard-citation + consequence-chain pattern, tone rules) for writing believable ICAI-voiced mistake notes for every question **outside** those 6 sittings (MTP/RTP never get real examiner comments; other PYQ sittings don't have a sourced comments doc yet). **Non-negotiable rule: every `commonMistakes` entry is tagged with its `source`** — `"ICAI Examiner's Comment — {Session}, verbatim/paraphrased"` for the real 6, or `"Synthesized per examiner-comments-writing-skill.md — not ICAI-sourced"` for everything else. Never blur the two.

**`recurringGroup` (OP/PP)** — Pranav's rule: strip numbers from question text, compare pairwise, **≥90% similarity ⇒ same recurring group**; within a group, the occurrence from the **chronologically earliest sitting** = **OP** ("Original Concept-testing Question"), every later occurrence = **PP** ("For Practice Question"). All occurrences still get shown in full in the eventual book — this is for cross-referencing/confidence (matching answer keys across occurrences), not de-duplication. Watch for: same numbers/renamed company (should still match) vs same company/different numbers-same-trap (may need judgment beyond the mechanical rule) — flag borderline cases rather than deciding silently. Full detail in `TAGGING-SCHEMA.md`.

### Immediate next step (as of 2026-07-22, session end)

Schema is updated (`TAGGING-SCHEMA.md` + `examiner-comments-writing-skill.md`); **not yet retrofitted into the 4 already-tagged JSONs** (intentional — Pranav wants the new shape used going forward, not retrofitted backward). Waiting on Pranav to share more `AS10_*` sample files before reconciling the schema fully and building the generator script. Once that lands, resume Phase 1 at scale: parse (3 of ~37 done) + tag (4 of ~37 done) the remaining sittings, now using the full schema (topics + commonMistakes + recurringGroup) from the start on every new sitting.
