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

### Telegram platform — MIGRATED OUT (2026-09-03)

The whole Telegram platform moved to `EFFICIENTCORPORATES/Main1lavyaAIAgents` (`examstudyhub/`) and runs on a Contabo server. **Everything in this section and in sections 8–11 is historical** — it describes the platform while it lived in this repo. For current truth go to that repo; for what is still kept here and why, read `telegram/MIGRATED.md`. The scale-readiness gaps below were real when written and now belong to that repo, not this one.

### Telegram platform: known scale-readiness gaps (flagged 2026-08-12, not yet resolved)

Pranav's target is **100,000+ students** on the Telegram bot platform (`telegram/`, see §11), currently ~100. An independent PM+CTO-level code review that day found the *feature* layer solid (ledger-based wallet, JSON-source-of-truth configs, audit trails, real smoke tests) but the *infrastructure* layer is still prototype-scale. Anyone picking up `telegram/` work should know these before adding more features on top — fix order matters more than feature count here:

1. **Single point of failure**: every bot process runs hand-managed (`manage_bots.py`, PID files, no auto-restart-on-crash) on one local Windows PC, all writing to one SQLite file. **The "no real off-machine backup" half of this is now fixed (2026-08-16)** — see `telegram/tools/backup_to_cloudflare.py`: a Windows Task Scheduler job runs it nightly at 3:30 AM, pushing SQLite-consistent snapshots of `platform.db`/`myfiles_hub.db`, a full queryable D1 mirror of `platform.db`, Fernet-encrypted `.env`/`creds.txt`, and the live-served asset folders (PDFs/JSON, student-uploaded files) to Cloudflare R2 (ECPL account) — see `telegram/database/README.md`'s "Off-machine backup" section for full detail, retention policy, and the disaster-recovery (`--decrypt-secret`) path. **The "no auto-restart-on-crash" half is still open** — one hardware/power/OS-update failure still takes the live platform itself offline (student data would now survive, but service wouldn't) until a hosted-infra move happens. Still the highest remaining priority below.
2. **DB/concurrency model untested under load**: each bot opens one SQLite connection at process start and reuses it for every concurrent update; sqlite3 calls are synchronous and block the bot's single asyncio event loop (same for the synchronous `open(...).read()` PDF sends). WAL+retry is a stopgap, Postgres is the named eventual target (see `database/schema.sql`'s own comments) but the migration trigger is "gated on real load" that has never actually been measured. Load-test this now, while it's cheap to fail.
3. **No working billing/quota enforcement anywhere in the bot code** — `wallet_ledger`/`payments` tables are schema-only, well-designed, never wired into any bot flow. If monetization is part of what justifies scaling to 100k, this needs to be built and load-tested well before the user base that would make retrofitting it risky.
4. **Long-polling architecture (`run_polling()`), not webhooks** — no horizontal scaling path for a single popular bot; will need to change before any one bot's DAU is large enough to need it.
5. **Content requires a full bot restart to reload** (all MCQ/descriptive JSON loads into memory once at startup) — a one-line content fix currently drops every in-flight session on that bot.
6. **No staging environment** — this session's own routine dev work runs directly against the same `platform.db` file live bots write to.
7. **Callback-data routing has produced the same bug class 3+ times** (regex pattern collisions swallowing another handler's buttons) and a 4th real instance — Telegram's 64-byte `callback_data` limit silently breaking a menu — was found and fixed 2026-08-12 in `exam_hub_bot.py`'s chapter picker. Worth a structural fix (central route registry + an automated collision/length check) rather than continuing to catch instances one at a time.
8. **No rate-limiting/abuse protection** anywhere visible (free-text search, OTP/email sends, leaderboard participation) — worth adding before the platform is that publicly exposed.
9. **Faculty onboarding is fully manual** (new BotFather token + config entries + content pipeline run, no self-serve) — fine for a handful of faculty, a bottleneck if growth depends on onboarding many.
10. **Admin Portal is single-shared-login, no per-faculty self-service** — every faculty's content/config change still goes through Pranav or an AI session.

Full review detail lives in this conversation's history (2026-08-12); this is the durable, brief pointer so any future session sees it. Ask Pranav for current priority before undertaking any of these — they're listed by what blocks 100k first, not in the order he's necessarily chosen to tackle them.

---

## 3. What each folder is for

| Folder | Purpose |
|--------|---------|
| `books/ca-inter/strategy-book/` | **Pillar 1** — Exam Strategy book (general + journey + exam-specific). `sources/` (research, skills, external reports), `design/` (spec + HTML build templates), `working/` (MASTER + component-index), `drafts/ final/` |
| `books/ca-inter/concept-book/` | **Pillar 2** — Advanced Accounts **Concept Book** (this IS the Adv-Accounts book): `chapter-zero/ characters/ chapters/ story-vignettes/ revision-material/` |
| `books/about-author/` | Shared author profile + journey (used by both books) |
| `syllabus-engine/` | **Pillar 3** — top-level folder is nearly empty (`data/` = 2 source `.xlsx` only). **The real, working pipeline lives nested at `books/ca-inter/concept-book/syllabus-engine/`** (`scripts/ html-source/ data/` incl. the canonical syllabus JSON) — see section 6. |
| `books/ca-inter/question-bank/` | **Pillar 4** — non-study-material questions (PYQ/MTP/RTP + solutions), currently ~3 yrs' coverage (goal: 7–10 yrs). **Not a top-level folder** — lives under `books/`. Its own `README.md` describes an abandoned `pyq/mtp/rtp/solutions/` layout (those 4 subfolders have since been deleted); real content is in `Raw_PDF_Question_Bank_CA_Inter_Accounts/`, `Parsed_PDF_Question_Bank_CA_Inter_Accounts/`, and `metadata-index/` — see section 6 for full pipeline status. |
| `mcq-platform/` | **Pillar 5** — AI MCQs in a DBMS, Cloudflare online tests: `question-generation/ database/ cloudflare-app/` |
| `telegram/` | **MIGRATED OUT, 2026-09-03.** The Telegram bot platform now lives in its own repo (`EFFICIENTCORPORATES/Main1lavyaAIAgents`, folder `examstudyhub/`) and runs on a Contabo server — **read `telegram/MIGRATED.md` first**. What remains here is accounts content for CA/CMA/CS (deliberately preserved, this being the accounts repo) plus the old local deployment's runtime logs. Do not edit bot code or platform docs here; they are stale copies. Sections 8–11 below describe that platform as it was when it lived in this repo, and are kept as history only. |
| `student-toolkit/` | Standalone student tools (e.g. exam date calculator). A subset of student-facing utilities; the Telegram bots may also surface these. |
| `content/` | Creative studio: `assets/` (raw-footage, intros-outros, green-screen, b-roll, music-sfx, brand-kit, thumbnails, flyers), `social/{personal,vc-gurukul}`, `calendar/`, `scripts/`, `motivation/` (daily-quote media library), `competitor-analysis/`, `ai-content-pipeline/`, `productions/` (one folder per video/content piece). See `content/README.md`. |
| `vc-gurukul/` | Institute side (NOT content brand): `management-discussions/ events/ batch-july-2025/ contracts/` |
| `materials/` | `icai-source/` (study material, PYQ/MTP/RTP — **gitignored/local**) + `reference/` (incl. `samples/`) |
| `obs-setup/` | Recording/streaming setup: `assets/` (OBS wallpapers), `recordings/` (output), `tools/` |
| `photo-gallery/` | `originals/` (gitignored) + `index.md` |
| `planning/` | Future planning: `future-roadmap.md`, `to-purchase.md`, `execution-notes.md` |
| `preparations/` | Personal prep notes, lecture plans |
| `final-deliverables/` | Print-ready teaching documents: teaching method (01), batch planner (02/02A), bridge course skeleton (03/03A), and future student-facing exports. MD only. |
| `books/ca-foundation/` | CA Foundation material: `icai-smaterials/` + `icai-smaterials-md/`, and `CA_Foundation_Offline_Retrieval_Engine_SMAT/` (the offline retrieval engine restored 2026-09-11). |
| `books/ca-inter/smat-may-27-edition/` | The May-2027-edition CA Inter workspace: `all-modules/`, `summaries/`, and `practice-with-pranav-bhaiya/` (class slides + the `data/` question library, topic-priority JSON and per-unit descriptive sets that feed the website's Must Practice page). |
| `capranav_com_revamped/` | **The live capranav.com** — Cloudflare Worker (`worker/index.js`) + Worker Assets (`public/`), D1 `capranav-platform`, R2 `capranav-vault`. `AGENT-HANDOFF.md` then `PROJECT-LOG.md` are the entry points; `ANATOMY.md` covers the `/anatomy/` explorer; **`MUST-PRACTICE.md` is the runbook for the Must Practice page** (AS 2, AS 10, AS 16 live; corpus-to-live chain, add-a-unit steps, `tools/verify_must_practice_live.py`). Deploy with `npx wrangler deploy` from this folder. |
| `capranav_com/` | Phase A of the website (`capranav-website/`), **superseded and no longer deployed** — kept for reference only. |
| `mentorship/` | Mentorship material for other faculty/institutes: `caclarity/` (CA Inter Taxation and FR question banks, answer keys, weightage), `vcg/`. |
| `tools/` | Admin/processing scripts (see section 5) |
| `_claude/` | Claude's context: `memory/` (incl. `project_log.md`), `artifacts/`, `skills/` |
| `first_run/` | **Workspace proving the Question Bank Book pipeline end-to-end** (added 2026-07-23) before scaling to the full syllabus. **`HOW-TO-BUILD-THE-BOOK.md`** (new 2026-07-27) is the master runbook — read it before running any script below; it has the exact command order, prerequisites, and every fixed-incident gotcha. `source/` (PDFs only, never MD, for every in-scope sitting — see section 6 for why this is enforced structurally now). `schema/` (single-source-of-truth `book-style.json` + generated `book-style.css` + `HTML-SCHEMA.md`). `prompts/` (the 3 external-AI prompts for generating sitting HTML). `scripts/` — Layer 1→2→3 (`extract_questions.py`, `generate_chapter_book.py`, `generate_all_chapter_books.py`), coverage stats (`generate_book_stats.py`), whole-book assembly (`generate_qb_front_back_matter.py`, `generate_qb_toc.py`, `qb_merge.py`, `resolve_qb_toc_pages.py`, `qb_common.py` for shared print/pagination CSS — all built by a concurrent session, see section 2's multi-agent note), and QA round-trip tooling added 2026-08-07 (`extract_book_questions.py`, `diff_book_vs_index.py` — parse the *finished merged book* back into JSON and diff it against `questions_index.json`; see section 6's 2026-08-07 entry). `output/parsed-from-pdf/` (sitting HTML, Layer 1). `output/generated-from-script/` (`questions_index.json`, `book_stats.json`, every chapter book — Layers 2–3). `output/qa/` (added 2026-08-07 — `book_questions_extracted.json`, the finished book re-parsed into JSON, plus `book-vs-index-diff.json`/`.md`, the QA comparison report). `output/` root also holds `front-matter.html`, `table-of-contents.html`, `chapter-coverage-matrix.html`, `back-matter.html`, the final merged `QUESTION-BANK-BOOK.html`, `vendor/` (fonts + paged.js), `final_deliverable/` (already-built, named PDF releases — e.g. `..._V1.pdf`, watermarked `..._V1_protect.pdf` — treat as distributed/ready-to-distribute, never regenerate or overwrite without asking), and the student-facing `How-to-Read-this-Book.md`. See section 6 for full status. Not a permanent pillar — once validated, its lessons fold back into `books/question-bank/`. |

**Path note (2026-09-23):** the books were reorganised under `books/ca-inter/`
(and `books/ca-foundation/`) after most of this file was written. The table above
is correct. **Sections 6 onwards are a historical log and still quote the old
pre-move paths** (`books/concept-book/...`, `books/question-bank/...`,
`books/strategy-book/...`) — read those as `books/ca-inter/<same thing>`. Verify a
path exists before relying on it rather than trusting a quoted path in this file.

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

**Standing rule — log book defects immediately (added 2026-09-24).** The first
edition is printed and distributed; nothing in a student's copy can be quietly
corrected. **Anything found wrong with or missing from the book goes into
`first_run/SECOND-EDITION-CHANGE-REQUESTS.md` the moment it is found — before
fixing it, and whether or not it gets fixed now.** That includes defects you fix
in the pipeline, because the source being right does not make the distributed PDF
right. Rule and entry format: `_claude/skills/SKILL-question-bank-change-log.md`.


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

---

## 11. Telegram Bot Platform — multi-tenant backend + first white-label faculty bots (built 2026-08-09/10)

**Read this section first for anything touching `telegram/`** — it's the entry point;
each subsystem's own doc (linked below) has the full depth. This is the single place
that ties the whole platform together end to end.

### Entity/business context

The Telegram bot platform is owned by **1LAVYA PVT LTD**, a company separate from any
individual faculty — **CA Pranav is faculty #1** on this platform (teaches Advanced
Accounting, CA Inter), not its owner; **CS Arun Chouhan is faculty #2** (teaches Law,
CMA Foundation + Intermediate). This is distinct from this file's own opening framing
("CA Pranav's teaching ecosystem") which correctly describes the books/content pillars
(Strategy Book, Concept Book, Question Bank Book) — that framing does not extend to
the bot platform, which has its own ownership structure. Every faculty pays 1LAVYA a
flat one-time ₹5,000 onboarding fee for (a) a limited, non-exclusive slice of 1LAVYA's
shared content for their students, and (b) the right to publish their own content
through their bot.

### Three pillars, now properly separated

1. **`telegram/config/tenants.json`** — *what does this faculty teach* (content_scope,
   own_content, exam_content). See `tenants.README.md`.
2. **`telegram/config/bots.json`** — *what bot processes exist, which token/script runs
   each one*. Added 2026-08-10 specifically because Pranav asked for **two separate
   bots** (Study + Exam) while Arun has **one unified bot** — the old scheme
   (`tenants.json` carrying `bot_token_env` directly) assumed one tenant = one bot,
   which broke the moment a faculty needed more than one. A tenant can map to 1..N bots
   here; content and bot identity are now independent concerns. See `bots.README.md`.
3. **`telegram/database/`** — *the shared platform database + tooling*. See below.

### The bot scripts

- **`telegram/bots/study_hub_bot.py`** — Category → Course → Level → Subject →
  Chapter/Paper, browse or free-text search. Tenant-aware since 2026-08-09, refactored
  onto `BOT_ID`/`bots.json` 2026-08-10. Auto-skips any picker step that collapses to one
  real option for a narrowly-scoped faculty (e.g. Arun's bot never asks "which course?"
  since he only teaches one). A `_Powered by 1LAVYA_` footer appears **only when
  delivering an actual file/PDF** — never on menus, welcomes, or questions (tightened
  2026-08-10 after first shipping it on every response, per Pranav's correction).
- **`telegram/bots/exam_hub_bot.py`** — Course → Level → Mode (Descriptive/MCQ) →
  Exam Type → Year → Chapter → question. Same `BOT_ID` treatment 2026-08-10, migrated
  off its own separate per-tenant `Exam_Bot.db` onto the shared platform DB. After an
  answer: **Next Question / Back to Chapter List / I'm Done** (was just "Next Question"
  until 2026-08-10). Brand footer only on `send_answer`/`handle_mcq_answer`/`send_pdf`.
- **`telegram/bots/faculty_bot.py`** (new 2026-08-10) — composes both hubs under one
  `/start` picker, for a tenant with only one bot token (Arun). Reuses both other
  scripts' handlers via direct import + one deliberate monkeypatch (see its own
  docstring) — not a rewrite. **Not used for Pranav** — he gets two separate bot
  processes (`study_hub_bot.py` + `exam_hub_bot.py`) instead, per `bots.json`.
- **`telegram/bots/myfiles_hub_bot.py`** — unchanged except a heartbeat-only addition
  (hardcoded `MYFILES_BOT_ID`); its own `users`/`otps`/`files`/`tags`/`activity_log`
  stay in their own separate `myfiles_hub.db` on purpose (primary application data,
  not logs — out of scope for the DB unification below).

**Question/MCQ content lives ONLY in JSON** (`telegram/assets/exam_bot/.../
mcq_questions_extracted.json` + `book_questions_extracted.json`, one pair per tenant
with its own content), loaded into memory once at bot startup and never touched by the
database. **The database stores only interaction/analytics data** (which student was
shown which `mcq_id`, selected what, when) — never question text. Editing a JSON file
needs a bot restart to take effect; the two concerns never overlap. Full detail:
`telegram/database/README.md`.

### Unified database (`telegram/database/schema.sql` + `db.py`)

One shared SQLite file, `telegram/database/platform.db`, replacing each bot's old
separate `.db` file. Tables are shared **per bot kind** with a `bot_id` column
(Pranav's explicit choice over one-table-per-bot-instance) — `bot_heartbeats`, a
generic `bot_interactions` log, `study_hub_events`, `exam_hub_sessions`/
`exam_hub_descriptive_events`/`exam_hub_mcq_attempts`, plus one central `students`
table every bot now writes to. `wallet_ledger`/`payments` exist in the schema
(designed for the ₹5,000 fee / MCQ-credit billing model) but are **not wired into any
bot yet** — no gating, no payment webhook built. Multi-process-safe via WAL mode + a
30s busy_timeout + an application-level retry wrapper (`db.py`'s
`execute_with_retry()`), verified with two connections writing concurrently — not the
originally-planned separate 5-second-snapshot file (see `database/README.md` for why
that was simplified away, and when to revisit it).

### Operating the platform

- **`telegram/tools/manage_bots.py`** (+ `.bat` wrapper) — `start`/`stop`/`restart`/
  `status` for every `active` bot in `bots.json`, at once or by `bot_id`. PID-tracked;
  graceful stop via `CTRL_BREAK_EVENT`, verified actually working on Windows (a test
  process printed its own "exiting cleanly" before terminating, well inside the grace
  period) with a bounded force-terminate fallback.
- **`telegram/tools/generate_dashboard.py`** — regenerate-on-demand local HTML
  dashboard (`telegram/database/dashboard.html`): bot online/offline via heartbeat
  freshness, message volume stacked by bot with date-range presets, true distinct-
  visitor counts per range (a real set union across days, not a sum of daily uniques).
- **`telegram/tools/convert_faculty_mcq_docx.py`** + **`telegram/config/
  FACULTY-MCQ-TEMPLATE.md`** — the deterministic (zero-AI) content-conversion
  pipeline, per Pranav's instruction. Canonical template's key rule: the correct
  answer never lives inline on a question (no "✓ CORRECT ANSWER" marker) — only in
  one separate Answer Key table, because an inline marker is exactly what produced 5
  real defects when Arun's own less-structured file was hand-extracted (see below).
  Verified against synthetic docs covering both real answer-key table shapes and every
  anomaly class (missing/orphan answer-key entry, bad option count, missing
  explanation, stale-figure warning) — nothing is ever silently guessed.

### Current bot roster (as of 2026-08-10 — check `bots.json` for the live truth)

| bot_id | Faculty | Status |
|---|---|---|
| `1lavya-studyhub`, `1lavya-examhub`, `1lavya-myfileshub` | 1LAVYA flagship | Running (pre-existing) |
| `csarunchouhan` | CS Arun Chouhan | Live-ready (unified bot); demo content: 20 MCQs + 5 descriptive out of his ~375-question corpus — see gap below |
| `capranav-study`, `capranav-exam` | CA Pranav | Running — Pranav confirmed he started both himself later the same day (2026-08-10); this row previously said "not yet started by anyone," which was true when first written and is stale now. |
| `1lavya-dashboard` | *(platform, not faculty)* | Running — live analytics dashboard, not a Telegram bot, added 2026-08-10 (see "Reporting & alerting infrastructure" below) |
| `1lavya-platform-watcher` | *(platform, not faculty)* | Built, `status: "inactive"` — down/up DM alerter, added 2026-08-10, waiting on real admin chat IDs before it's turned on (see below) |

### Known gaps, honestly (don't assume these are done)

- **Pranav's own Revision Material** (2 PDFs, AS 2 & AS 10) is `not_ingested` — his
  Study bot serves only the shared pool. Needs the `content_owner` catalog-tagging
  convention (documented in `schema.sql`, not yet applied to
  `build_master_catalog.py`) so his PDFs are attributed to him, not silently merged
  into the anonymous shared catalog.
- **Arun's full MCQ corpus is not wired in.** Only 20 of his ~375 questions are live
  (hand-extracted before the deterministic converter existed). A newer file,
  `telegram/assets/faculty/csarunchouhan-cma-found-law/
  cma_foundation_law_faculty_mcqs.json` (375 questions, `publication_status: "draft"`),
  surfaced 2026-08-10 — different schema than the converter produces, and its
  `answer_html` has no explanations yet. Not converted or wired in as of this writing.
- **OP/PP duplicate detection** — still out of scope, unrelated to this backend work
  (see §10's own history and the Question Bank Book sections above).
- **Billing (wallet/payments) is schema-only** — the ₹5,000 faculty fee and the
  100-free-MCQs/month + ₹-per-100-recharge student model are both designed
  (`schema.sql`) but not built into any bot's actual flow.
- **`myfiles_hub_bot.py`** was not migrated onto `BOT_ID`/the shared DB beyond its
  heartbeat — deliberate, not an oversight (see its own note in `bots.README.md`).

### Real bug found + fixed, and reporting/alerting infrastructure built (2026-08-10, later same day)

Pranav reported a live, reproducible bug on the `csarunchouhan` bot: after
answering an MCQ, "Back to Chapter List" worked but "Next Question" and
"I'm Done" gave no response at all. Verified independently (not just taken
on faith) by reading the actual code path, not assumed: `faculty_bot.py`
registered its exam-hub handler with `pattern=r"^(...|next|mcqopt|restart):"`
— a regex requiring a **trailing colon** — but `exam_hub_bot.py`'s "Next
Question"/"I'm Done" buttons use **bare** `callback_data` values (`"next"`,
`"restart"`, no colon, by design — see `next_step_rows()`). So in the
unified bot specifically, those two taps matched no handler at all;
Telegram never even got `query.answer()` back. Standalone `exam_hub_bot.py`
was never affected (its own handler has no such pattern restriction).
Fixed in `faculty_bot.py` (`(:|$)` instead of a literal `:`), verified
against every real callback shape, and **deployed live** — restarted the
`csarunchouhan` process (its only user at the time was Pranav's own test
session, confirmed via the DB before restarting).

While investigating, found all 6 real bots (including `capranav-study`/
`capranav-exam`) already running — Pranav confirmed he'd started them
himself that day; the "not yet started by anyone" line elsewhere in this
section was accurate when written and is now corrected.

Pranav then asked for "a robust architecture and a perfect reporting
tool" — three concrete asks, all built same-day:

1. **Down/up DM alerts** — `telegram/bots/watcher_bot.py`, sends via the
   1LAVYA MyFiles Hub bot's token (Pranav's choice over a dedicated new
   bot) to `telegram/config/alerts.json`'s `admin_chat_ids` (empty by
   design until Pranav fills in real chat IDs — the watcher runs fine
   either way, just logs instead of sending). Edge-triggered off the same
   heartbeat-freshness signal the dashboard already used, tracked in a new
   `bot_alert_state` table so a restart doesn't re-fire. Both transition
   directions (down→up and up→down) verified against the real live DB in
   this session — not mocked — by temporarily perturbing state for one
   real bot at a time, confirming detection, then letting the watcher
   self-correct back to true state, all through the real code path.
2. **Live, refreshable dashboard** — `telegram/tools/dashboard_server.py`,
   a small local HTTP server (127.0.0.1:8787) with a Refresh button that
   re-queries `platform.db` and re-renders without a page reload (Pranav's
   exact ask). Runs as a managed process like every bot (`bots.json`'s
   `1lavya-dashboard` entry, `kind: "dashboard"`).
3. **On-demand bot-wise usage summary** — delivered as a dashboard view
   (Pranav's choice over a Telegram command): interactions, unique users,
   Study Hub downloads/searches, Exam Hub sessions/MCQ accuracy/
   descriptive views, per bot, all-time.

To avoid two copies of the same queries/page drifting apart, both the live
server and the pre-existing static `generate_dashboard.py` were refactored
onto one shared query layer (`telegram/database/analytics.py`) and one
shared page template (`telegram/database/dashboard_html.py`) — a metric
definition or a rendering fix now happens once, not twice.

**One real bug self-introduced and caught before it shipped**: the
dashboard's `bots.json` entry first used a relative `"../tools/..."`
script path, which would have silently broken `manage_bots.py`'s "already
running" detection (a hand-written `/`-separated string never matches the
OS-native `\`-separated string Python actually launches the process with
on Windows). Fixed properly — `manage_bots.py` gained a `resolve_script_path()`
helper and an optional `script_dir` field (default `"bots"`), used
consistently everywhere a script path is needed, not patched around.
Verified via a real start/status/duplicate-start-attempt cycle.

**Also surfaced, not fixed** (flagged, not acted on without asking): running
`manage_bots.py stop`/`restart` in this session's own sandboxed shell hit
`WinError 87` on the `CTRL_BREAK_EVENT` graceful-stop signal every time,
falling through to the force-terminate fallback (harmless — the bot still
stopped, just after the full grace period). Most likely that shell having
no real attached Windows console, not a code defect — but the
`bots.README.md`/`database/README.md` claim that this was "verified
working on Windows" no longer holds unconditionally; worth Pranav
confirming from his own terminal rather than trusting either claim blindly.

Still open, unchanged by this pass: `alerts.json`'s `admin_chat_ids` is
still empty (needs Pranav's real Telegram chat ID(s) before the watcher can
send anything — see that file's own comment for how to get one), and the
watcher's `bots.json` entry is deliberately `status: "inactive"` until then.

### Roadmap discussed + Content Health validator built (2026-08-10, later still)

Pranav laid out a larger roadmap for this platform and asked for feedback before
committing to it: (1) a formal way to guarantee every faculty's JSON carries the
fields the bot code needs, even as each faculty adds their own extra display
fields; (2) growing `:8787` into a full admin portal; (3) student-wise
performance/usage tracking, not just bot-wise; (4) a faculty-visible,
accuracy-ranked leaderboard with rewards; (5) a PDF performance report, emailed
to a student after 20 practiced questions, branded/watermarked for 1LAVYA.

Feedback given, three points pushed back on rather than accepted as stated:
- **"He won't give a wrong email because he wants the report"** doesn't hold —
  people mistype emails regardless of wanting the thing correctly (autocomplete,
  a stale saved address), and the failure mode here is a *named student's real
  performance data* reaching an unverified stranger, not just a lost email.
  Pranav agreed; the design is now **echo-and-confirm** (bot repeats the typed
  email back with a Confirm/Re-type button) rather than either OTP (too much
  friction for this context) or send-immediately (the original plan).
- **Leaderboard scoring wasn't decided** (raw accuracy rewards never attempting
  hard questions; raw volume rewards guessing fast) — Pranav chose **accuracy
  with a minimum-attempts floor**.
- **PDF report ≠ the existing `watermark_for_print.py`** — that script
  rasterizes every page to a high-DPI image for print/anti-piracy protection on
  the paid Question Bank Book; wrong tool for a light, emailed performance
  report. The right engine is already in this codebase: `exam_hub_bot.py`
  already uses `xhtml2pdf`/`pisa` for on-demand question PDFs (`send_pdf()`) —
  reuse that, not the book's watermarker. **Still open**: no 1LAVYA logo image
  exists anywhere in this repo yet (text wordmark vs. a real logo asset is
  Pranav's call, not yet made).

Also corrected in passing: `students.email` was already designed
(`schema.sql`) to be populated once verified by *any* bot doing email OTP
(MyFiles Hub does this already) — the report-email feature can reuse that
existing SMTP infrastructure rather than building fresh.

Pranav chose to build the smallest, most foundational piece first: **the
content field-consistency validator**, not the leaderboard or reports yet.
Built `telegram/tools/validate_content_json.py` — its `CORE_FIELDS` contract
(`MCQ_REQUIRED`/`MCQ_RECOMMENDED`/`DESC_REQUIRED`/`DESC_RECOMMENDED`) was
derived by grepping every actual `q.get(...)`/`q[...]` field access in
`exam_hub_bot.py`'s `QuestionBank`/`McqBank` and its
`send_question`/`send_answer`/`send_pdf`/`send_mcq`/`handle_mcq_answer`
functions — not guessed. Two severities: ERROR for anything that would crash
or silently corrupt an answer (bad `correct_option`, <2 `options`, a
duplicate `mcq_id`/`book_id` silently shadowing an earlier record via
`get_by_id()`/`get_by_book_id()`'s first-match-wins lookup), WARNING for
anything with a safe fallback but degraded content. **Deliberately never
flags extra, faculty-specific fields** — this checks "does the bot have what
it needs," not "is this file well-formed by some external schema," so a
faculty's own display fields (`submodule_code`, `is_miq`, whatever) never
trip a false alarm. Auto-discovers every content file from `tenants.json`'s
`exam_content` (deduping files two tenants legitimately share, e.g.
`capranav`/`1lavya-examhub` today). Verified both directions before being
trusted: clean run against all 4 real live content files (0 issues), and a
synthetic negative-control file covering all 4 defect classes above (all 4
correctly caught, exit code 1).

Wired into the admin portal per Pranav's ask ("validations... usable through
that admin port"): `analytics.fetch_content_health()` calls the validator
live (no caching — a changed file should show as changed on the very next
Refresh), and both dashboards gained a **Content Health** card — a colored
status badge (all-clear / N warnings / N errors) plus a per-file breakdown
listing every issue with its record id, field, and plain-English
consequence. This is explicitly NOT a content-quality/fact-checking tool
(that deeper concern already exists separately — `first_run/`'s
`extract_book_questions.py`/`diff_book_vs_index.py` for the Question Bank
Book pipeline) — this only guarantees the bot won't break or silently
misbehave on a malformed file.

Still open, by explicit choice (build order Pranav picked, not yet reached):
student-wise analytics view, the leaderboard, and the PDF report/email
pipeline — see this section's own feedback above for the open decisions each
one still needs (logo asset for reports; nothing else blocking student
analytics, most of its raw data already exists in `exam_hub_mcq_attempts`).

### Real admin chat IDs configured + student profile system built (2026-08-11)

Pranav supplied his and CS Arun Chouhan's real Telegram chat IDs
(`5777734732`, `6357621862`) for the down/up alert watcher designed
2026-08-10 above. Filled into `telegram/config/alerts.json`'s
`admin_chat_ids`, flipped `1lavya-platform-watcher`'s `bots.json` status to
`active`, started it as a managed process. Verified real end-to-end
delivery (not just config): perturbed `1lavya-dashboard`'s alert state to a
fake "down" via direct DB update, ran a real check pass, confirmed a
genuine down→up transition alert, then sent an explicit one-time test DM to
each admin chat ID individually — both confirmed delivered via the
Telegram API's own response.

Same day, Pranav asked for students to be able to view/edit a profile by
texting "profile"/"change profile" to any bot — username, display name,
avatar, email, phone, course & level, exam attempt — with confirmation
before editing, and **username permanently locked once set** (must be
stated to the student). Clarifying questions (all "Recommended" answers
accepted): build this now as the **Phase 3 (Leaderboard) identity
foundation**, not a standalone feature to be redone later; avatar pulled
live from the student's own Telegram profile photo (no upload, no new
storage); course & level via a guided picker, not free text; username
Instagram-style (3-20 chars, letters/numbers/underscore, case-insensitive
uniqueness).

Built: `telegram/database/schema.sql`'s new `student_profiles` table
(username as the permanent PK, shared fields: display_name/course/level/
exam_attempt) + `students.lavya_username` link column. **One username can
link multiple `telegram_user_id` chat_ids** — Pranav's own scenario, a
student practicing from several phones shouldn't lose identity/progress
switching between them. Shared fields update everywhere once linked;
email/mobile stay **per-chat-id** on `students` (Pranav's reasoning:
different phones might use different emails) — deliberately not shared.
`telegram/bots/contact_utils.py` (new) extracts the mobile/email validation
`report_flow.py` already had, so both flows share one definition.
`telegram/bots/profile_flow.py` (new) implements the full trigger/state-
machine/menu flow, wired into `exam_hub_bot.py`, `study_hub_bot.py`, and
`faculty_bot.py` with an explicitly-scoped new `profile:`/`profileconfirm:`
callback prefix — guarding against the callback-pattern-collision bug class
already found and fixed 3 times earlier this same day (an unscoped or
mis-scoped `CallbackQueryHandler` silently swallowing another handler's
buttons). Each bot's text router checks profile-flow awaiting-state first,
so an edit in progress is never swallowed by search or the report flow.

`telegram/bots/smoke_test_profile_flow.py` (new): 41 checks against the
real shared DB with synthetic, self-cleaning chat_ids — new-username
creation + permanent lock, case-insensitive duplicate rejection, linking a
second chat_id to an existing username, shared-field propagation across
linked chat_ids, per-chat-id email/mobile isolation, invalid-input
rejection, correct menu behavior (never re-offers username setup once
one's set). All 41 passed. All 5 affected bot processes
(`1lavya-studyhub`, `1lavya-examhub`, `csarunchouhan`, `capranav-study`,
`capranav-exam`) restarted and confirmed running the new code via
`bot_heartbeats.started_at` (not log-grepping, per this section's own
2026-08-10 lesson) plus clean startup logs. Full detail:
`telegram/PROFILE-SYSTEM.md`.

**Known limitations, named honestly**: no profanity/reserved-word filter on
usernames; the exam-attempt quick-pick buttons are relative to today's date
and will read oddly a year or two out (deliberately not hardcoded to a
specific exam cycle, but not auto-updating either); the course/level picker
is a small hand-coded taxonomy (not derived from a live catalog) since that
taxonomy changes rarely — a real curriculum restructuring would need a code
change here.

### Leaderboard system built (Phase 3) + exam-attempt picker redesigned (2026-08-11)

Same day, Pranav asked for two more things: (1) the profile's Target
Attempt field to be a guided **Year → Month** picker instead of free-text
quick-picks — done, replacing `EXAM_ATTEMPT_QUICK_PICKS` with two chained
button steps, years computed relative to "today" at render time; (2) a
full **leaderboard system** — students join up to 5 live leaderboards,
strictly scoped to their own Course+Level (a CA Inter student never sees
a CA Final/CMA Inter/CS Inter board), each mapped to one-or-more Telegram
channels broadcasting nightly at **11:11 PM IST**, ranked by multiple
metrics (accuracy %, questions attempted, time spent) from an extensible
metrics master — plus a faculty-facing student-wise/chapter-wise report.

Given the real architectural forks this implied (leaderboard scope
granularity, config-file vs. admin-UI management, single-vs-multi-metric
display, minimum-attempts-floor scope, faculty-report timing) — and given
the outward-facing, hard-to-reverse nature of auto-broadcasting to public
Telegram channels — asked 6 clarifying questions via AskUserQuestion
before writing any code. All confirmed: **leaderboard eligibility is
fully manual per leaderboard** (hand-specified in a new
`telegram/config/leaderboards.json`, same "JSON is the source of truth"
pattern as `bots.json`/`tenants.json` — this is what lets ONE faculty bot,
e.g. CS Arun Chouhan's unified bot, host multiple SEPARATE leaderboards,
his own CMA Inter Law / CMA Foundation Law example); **multiple metrics on
one leaderboard render as separate mini-rankings**, never a blended
weighted score; **the minimum-attempts floor is a blanket gate across ALL
metrics**, not just accuracy; **the faculty report is built now**, as a
dashboard card, not deferred to Phase 4.

Built: `telegram/config/leaderboards.json` + `.README.md` (2 example CMA
Inter/Foundation Law entries, both `status: "inactive"` with
`chat_id: null` placeholders — nothing broadcasts until Pranav creates the
real channels, adds the posting bot as a channel admin, fills in real
chat_ids, and flips status). `telegram/database/schema.sql`'s new
`leaderboard_participants` (who joined what) + `leaderboard_broadcast_log`
(full audit trail of every nightly send attempt, same "complete trail"
discipline `report_flow_events` already established) tables.
`telegram/database/leaderboard_metrics.py` — config loading, eligibility
matching, the 3-metric registry (`accuracy_pct`, `questions_attempted`,
`time_spent_minutes`), and ranking computation, **every metric aggregated
per username across every linked chat_id/phone** (consistent with the
profile system's multi-device identity model). `profile_flow.py`'s new
"🏆 Leaderboards" menu (join/leave toggle, enforces the 5-board cap with a
real alert on a rejected 6th join). `telegram/bots/leaderboard_broadcaster.py`
— a new standalone managed process (same shape as `watcher_bot.py`),
scheduled against a **fixed UTC+5:30 offset** (no IANA tzdata dependency,
since India has no DST), `--once` for testing, idempotent per leaderboard
per day. `analytics.py`'s new `fetch_faculty_report()` + a new expandable
"Faculty Report — Student-wise & Chapter-wise" card on the `:8787`
dashboard (click a student row to see their chapter breakdown).

`telegram/bots/smoke_test_leaderboards.py` (new): 28 checks against the
real DB with synthetic, self-cleaning data — eligibility matching,
join/leave, the exact 6th-join rejection (with alert), multi-phone metric
aggregation (verified against real seeded MCQ attempts across two
chat_ids), the minimum-attempts floor including the exact-at-floor
boundary case, full per-metric ranking sort order, broadcast message
rendering, and the broadcast-log audit trail (including a real logged
failure when no token resolves). All 28 passed.
`smoke_test_profile_flow.py` re-run clean (43/43) — the new Leaderboards
button didn't disturb existing profile behavior. Faculty Report verified
against **real production data** through the actual `analytics.fetch_all()`
/ `dashboard_html.render_page()` pipeline (correct chapter-wise rows for
`csarunchouhan`'s 15 students and `capranav-exam`'s 3); static dashboard
regenerated, live `:8787` server restarted and confirmed serving
`faculty_report` in its `/api/data` response. All 5 bots that import
`profile_flow.py` restarted, confirmed clean startup logs.

**Nothing is broadcasting live yet, by design** — every `leaderboards.json`
entry and the new `1lavya-leaderboard-broadcaster` `bots.json` entry ship
`status: "inactive"` until Pranav does the Telegram-side setup (create the
channel, add the bot as admin with post rights, get the real chat_id) that
this session cannot do on its own. Full detail:
`telegram/LEADERBOARD-SYSTEM.md`.

### Cloudflare Email Service wired in + on-demand report trigger (2026-08-11)

Same day, Pranav added real `CF_EMAIL_API_TOKEN` to `telegram/.env` and
asked to wire up Cloudflare's Email Service (send-only, no inbox needed)
for the student report pipeline — one dedicated unmonitored email per
bot, all under one domain; a good-branding requirement; support@1lavya.com
referenced for real issues and admin@1lavya.com for "getting your own
Exam or Custom Bot created" (his exact wording) — plus a new on-demand
trigger: typing **"report", "analysis", "email", or "mail"** to any bot
(parallel to "profile"/"change profile") asks whether the student wants
their analysis report, then funnels into the same channel-picker/
delivery flow, not gated on the 20-question milestone.

Researched the actual product first via WebSearch/WebFetch rather than
guessing (Cloudflare Email Service is real, public beta since
2026-04-16, REST endpoint `POST /accounts/{account_id}/email/sending/
send`) — then, since this touches live domain/DNS configuration this
session cannot verify or set up on its own, asked 4 clarifying questions
before writing any integration code: whether 1lavya.com is already
onboarded for Email Sending in the Cloudflare dashboard (confirmed yes),
the Cloudflare Account ID (provided), whether bot addresses should be
literal per-bot subdomains (Pranav's literal ask) or one shared domain
with different local parts (this session's recommendation, given
Cloudflare's onboarding/verification is per-DOMAIN not per-subdomain —
**accepted**), and whether support@/admin@1lavya.com are already real,
monitored mailboxes (confirmed yes).

Built: `telegram/database/cf_email.py` (raw REST client, same
`urllib`-not-`requests` technique `watcher_bot.py`/
`leaderboard_broadcaster.py` already use). Rewrote
`telegram/database/report_delivery.py` — `send_report_email()` now takes
a `bot_id`, resolves that bot's own dedicated `from_email` from
`bots.json` (new field, one shared domain/different local parts:
`studyhub@1lavya.com`, `examhub@1lavya.com`, `csarunchouhan@1lavya.com`,
`capranav-study@1lavya.com`, `capranav-exam@1lavya.com`, graceful
fallback to `reports@1lavya.com` for any bot with none configured), and
sends a **fully 1LAVYA-branded** HTML email regardless of which bot
(including a faculty's own bot) triggered it — matching the existing
precedent that platform-built artifacts (the report PDF's own "Powered
by 1LAVYA" caption) always carry 1LAVYA branding, since 1LAVYA built and
operates the report feature itself, not the faculty. New
`brand_kit.render_email_footer_html()` — every report email's footer
states the mailbox is unmonitored and gives the two real contact
addresses; deliberately **text-based, not the logo `<img>`** the
dashboard/PDF header use, since email clients (Outlook especially) have
much less reliable `data:`-URI image support than a browser or
`xhtml2pdf`. `myfiles_hub_bot.py`'s own OTP email is **unchanged** — still
Gmail SMTP, not migrated (not asked, out of scope).

`report_flow.py`'s entry points (`maybe_trigger_report_milestone()`,
new `start_report_flow_on_demand()`) now take a `bot_id` argument, stashed
in `context.user_data["report_flow_bot_id"]` so `_deliver_report()` —
called much later in the conversation, after several button taps — still
knows which bot's address to send from. The on-demand trigger itself
reuses the milestone flow's ENTIRE existing pipeline
(`_send_channel_picker()`/`_handle_channel_choice()`/`_finalize()`/
`_deliver_report()`, zero duplicated logic) and works even for a student
who's never answered 20 questions — `_finalize()` already tolerated a
missing milestone row (a `WHERE` clause matching zero rows is a harmless
no-op). Wired into `study_hub_bot.py` for the first time in this pass —
it never imported `report_flow.py` before, so Study Hub previously had no
report-related behavior at all.

**Verified with a real send**, not just structurally: after the smoke
test's HTML/address-resolution checks passed, ran one live send through
the *actual* production code path (`report_delivery.build_report_email_html()`
+ `resolve_from_address()` + `cf_email.send_email()`) to Pranav's own
email — confirmed delivered (Cloudflare's response included a real
`message_id` and `"delivered": ["pranavaiversion@gmail.com"]`).
`smoke_test_report_flow.py` itself never fires a real network call by
design (no `load_dotenv()` in that script, so `cf_email.is_configured()`
is deliberately `False` during automated runs) — confirmed the
email-delivery-failure path inside `_deliver_report()` is caught and
logged gracefully rather than crashing, exactly as intended for a
genuinely mis-configured environment. Gained a new Step 7d covering the
full on-demand flow end-to-end (trigger-phrase matching, confirm, channel
picker, delivery with zero prior MCQ activity, and the "declined"
branch). All 5 bots that import `report_flow.py` restarted, confirmed
clean startup logs. Full detail: `telegram/REPORT-PIPELINE.md`'s new
section.

### Major roadmap locked in + Phase 1 (Branding Kit) complete (2026-08-11)

Pranav laid out a much larger roadmap in one message — conversational
upgrades (greetings, free-text intent routing with a confirm-if-≥90%-sure /
top-5-otherwise flow, faculty bots stating their scope limits and pointing
elsewhere), deeper per-student analytics (time per question, chapter-wise
accuracy, time on bot), a 20-question report pipeline (collect email/mobile,
generate a branded HTML→PDF, send by the channels chosen — explicitly no
OTP, his repeated call), a 30-question leaderboard system built on a NEW
globally-unique "1LAVYA username" identity (Instagram-handle-style, separate
from a public display name, one username spanning multiple chat_ids/phones,
consolidated leaderboard scores, unique-chat-ID-count-per-username as an
abuse signal), and turning the admin dashboard into a full sidebar
application (Masters, Settings, downloadable schema templates, tabbed
analytics) — all under **consistent 1LAVYA branding**, distinct from and
never applied to faculty-branded bot output.

**Locked decisions** (asked rather than assumed, since each changes the
architecture):
- Free-text search is scoped to the bot's tenant `content_scope` first
  (never suggests content outside it), narrowing via a Course+Level picker
  and then Subject if the scope is still ambiguous, then querying **both**
  Study Hub and Exam Hub content within that narrowed scope — not literally
  "whichever hub the UI is currently in."
- The 20/30-question milestones are **platform-wide** (matches the existing
  centralized-account model), not per-bot.
- The admin portal moves to **Flask** now that Settings/Masters need writes,
  not just read-only views — the current stdlib `http.server` approach was
  fine for a read-only dashboard, not for this.
- **Build order, strict**: Branding Kit → Report Pipeline → Leaderboard →
  Admin Portal. Each phase: build it, smoke-test it (a real, re-runnable
  `.py` script, not just ad hoc checks), document it, THEN hand off for
  Pranav's manual test — only move to the next phase once that's done.

**Phase 1 (Branding Kit) — done, awaiting Pranav's manual confirmation.**
`telegram/branding/` — see that folder's own `README.md` for full detail.
`build_brand_kit.py` derives everything from `telegram/1LAVYA_LOGO.jpeg`:
a transparent-background PNG (feathered alpha, not a hard cutout — visually
confirmed by compositing onto a navy background before trusting it), three
pre-sized thumbnails, and `brand_colors.json` (navy `#09284b`/gold
`#d0942c`, extracted from the logo's own pixels via hue-bucketing, not
eyeballed). `brand_kit.py` is the reusable module — `colors()`,
`logo_data_uri()`, `render_header_html()`, `render_footer_html()`,
`brand_css_vars()`. Wired into the real dashboard (both
`generate_dashboard.py` and `dashboard_server.py`, via the shared
`dashboard_html.py` template) as the first real proof it works, not left
untested in isolation.

**A real cross-engine bug found and fixed via the smoke test, not by
inspection**: `letter-spacing: 0.02em` rendered fine in a browser but
`xhtml2pdf`/`reportlab` (the engine Phase 2's PDF reports will use, already
proven elsewhere in `exam_hub_bot.py`) can't parse the `em` unit — it
silently dropped the rule rather than erroring, so `pisa`'s own error count
stayed at 0 even though a real rule was being lost. Only caught by actually
rendering through both engines and inspecting the output (a headless-Edge
screenshot for the browser path, a real PDF render read directly via
Claude's own PDF-viewing capability for the xhtml2pdf path) — exactly the
"structural 0-errors isn't enough, check the actual rendered output" lesson
this same session already relearned twice on the content-pipeline side
(see the csarunchouhan entries above). Fixed by dropping the `em`-based
letter-spacing; `smoke_test_brand_kit.py` now has a permanent step guarding
against this exact regression class on every future kit change.

Not yet started: Phase 2 (Report Pipeline) — waiting on Pranav's manual
confirmation of Phase 1 first, per the locked build-order process above.

**Update, same day, minutes later**: Pranav's own manual check found the
branding invisible on the real `:8787` page. Real cause — the live
`1lavya-dashboard` process predated the edit (Python doesn't hot-reload
source; the smoke test had only ever checked the static `dashboard.html`
file, never the actually-running server). Restarted, confirmed live via a
real screenshot of the URL itself, and — more durably — added a Step 7 to
`smoke_test_brand_kit.py` that fetches the live server directly and
compares its recorded start time against the source files' mtimes, so a
stale-process deploy is now an automatic, loud failure instead of something
that has to be remembered. That new check immediately caught a second, real,
pre-existing bug: `db.py`'s `send_heartbeat()` only ever wrote `started_at`
on a bot_id's very first heartbeat row, never on later restarts — fixed
(safe, confirmed nothing else reads that column today). Full detail:
`telegram/branding/README.md`'s operational-gotcha callout at the top.

### Phase 2 (Report Pipeline) built + deployed (2026-08-11)

Pranav confirmed Phase 1 and said to proceed. Full detail:
`telegram/REPORT-PIPELINE.md`. Short version: platform-wide (every bot, not
per-bot), a student's 20th answered MCQ triggers a report offer (Telegram/
email/both), contact info is collected via echo-and-confirm (no OTP,
Pranav's repeated call), and a branded HTML→PDF report (reusing Phase 1's
brand kit) is generated and sent. New: `database/student_analytics.py`,
`tools/generate_student_report.py`, `database/report_delivery.py`,
`bots/report_flow.py`, `bots/smoke_test_report_flow.py`. Schema migrations
for existing tables are idempotent Python (`db.py`'s
`_run_column_migrations()`), not raw SQL — SQLite has no `ADD COLUMN IF NOT
EXISTS`, confirmed by testing directly, not assumed.

Two real design/bugs caught by testing before shipping, not by inspection:
(1) a first draft closed a session's `ended_at` when the next one started,
which would have counted multi-day idle gaps between sessions as active
"time on bot" — reverted; that metric is now computed at query time as
`MAX(activity timestamp) - started_at` per session, never wider than real
recorded activity. (2) The mobile-number regex rejected a realistic input
("+91 98765 43210", the real Indian 5+5 grouping with an internal space) —
fixed by stripping separators before matching, not by trying to encode
every separator position into the pattern.

Deliberately re-guarded against the exact callback-pattern-collision bug
class found twice already this session (2026-08-10's "next"/"restart"
bug): `exam_hub_bot.py`'s `button_router` had NO pattern at all before this
change (harmless only because nothing else claimed any callback_data) —
adding `report_flow`'s own callbacks would have been silently swallowed by
it. Fixed before shipping (explicit pattern now, `report_flow` registered
separately, mirrored in `faculty_bot.py`), with a permanent smoke-test
check verifying every real callback string matches exactly one handler
pattern going forward.

`smoke_test_report_flow.py`: 7 steps, ~40 checks, including a full
conversational-flow simulation against a synthetic test student (cleaned up
after, even on failure) exercising the entire path end to end. Real SMTP
creds aren't configured in this dev environment — proved the email message
builds correctly and a genuine SMTP failure is caught/logged gracefully
(verified for real when mock credentials predictably failed auth mid-test),
not that a real email actually arrives — flagged honestly for Pranav to
verify once real creds are in `.env`.

Restarted `1lavya-examhub`, `capranav-exam`, `csarunchouhan` to deploy;
confirmed clean since restart (checked by timestamp, since old pre-restart
tracebacks remain visible in the same append-only log files).
`health_check.py`: same 16 pre-existing failures. Not yet started: Phase 3
(Leaderboard) — waiting on Pranav's manual confirmation of Phase 2 first,
per the locked build-order process.

### Leaderboard system built (Phase 3) + Cloudflare email + on-demand report trigger (2026-08-11)

Same day: full Phase 3 leaderboard system (students join up to 5 boards,
strictly course+level-scoped, nightly 11:11pm IST broadcasts, multi-metric
rankings via a manual `leaderboards.json` config — see
`telegram/LEADERBOARD-SYSTEM.md`); Cloudflare Email Service replacing
Gmail SMTP for report delivery, one dedicated unmonitored address per bot
on one shared domain, real send verified; and an on-demand "report"/
"analysis"/"email"/"mail" trigger alongside "profile" (see
`telegram/REPORT-PIPELINE.md`'s own detailed entries for both).

### Two real live bugs found + fixed same day: unquoted email From-header, and re-asking for contact info already on file

**Bug 1**: minutes after the Cloudflare email integration went live,
Pranav reported delivery failures on the `csarunchouhan` bot. Root-caused
by reproducing the exact failure and isolating `from`/`to` independently:
`csarunchouhan`'s own `bots.json` `display_name` contains a comma and
parentheses, and the hand-rolled `f"{name} <{email}>"` From-header wasn't
RFC-5322-quoted for that case — Cloudflare rejected it outright (HTTP 400
`email.sending.error.email.invalid`). Fixed with Python's own
`email.utils.formataddr` via a new `cf_email.build_from_header()` helper;
verified with a real send through the exact failing combination; permanent
regression test added. A second, independent issue on the same delivery
(a genuine `telegram.error.TimedOut` on the PDF upload, a one-off network
blip) got a bounded one-retry fix for that transient-error class only.

**Bug 2**: Pranav, separately: "even after sharing the mobile number and
email id once, if I again ask for report than it again asks for my
number/email... does not the bot check with existing database." Confirmed
real — `report_flow.py` never checked `students.mobile_number`/`.email`
before asking, on every single report request. Fixed in three places
(initial channel choice, the "both" mobile→email handoff, and the
post-delivery upsell) via a new `_existing_contact()` helper — each now
skips straight to delivery when the needed value(s) are already on file.

Both fixed same-day, both with new permanent smoke-test coverage, both
deployed to all 5 affected bots. Full detail: `telegram/REPORT-PIPELINE.md`.

### 3 leaderboards activated (config-ready) + Admin Portal (Phase 4) foundation tier built (2026-08-11)

Pranav asked for two things: (1) build the 3 leaderboards he'd been
planning — CS Arun Chouhan's CMA Intermediate + CMA Foundation Law
(already templated from the leaderboard-system build above) plus a new
one for CA Pranav's CA Inter Advanced Accounts — all three ranked by
**Top 10 Most Attempted, Top 10 Most Accurate, and Most Time Spent** (maps
directly onto the existing `questions_attempted`/`accuracy_pct`/
`time_spent_minutes` metrics registry, `top_n: 10` on each); (2) start
building the full **Admin Portal** (Phase 4 of the roadmap) — Flask,
sidebar + sub-tabs, and an extensive module list (analytics, masters
display/editing, bot restart, question summary, question catalog edits,
faculty addition, new bot addition, leaderboard edits, student-profile↔
leaderboard mappings, email analytics, bot-wise logs), plus a later ask
for module-wise RBAC (students/faculty/1LAVYA-manager access levels).
Explicit instruction: *"Any input required from my side, let me know...
don't assume."*

**Leaderboards**: added the 3rd entry to `leaderboards.json`
(`capranav-ca-inter-advanced-accounts`, eligibility `{course: "CA", level:
"Inter"}`, posted via `capranav-exam`'s token) alongside the existing two —
all three now share the identical 3-metric set Pranav specified. All
three remain `status: "inactive"` — still waiting on real Telegram channel
IDs + confirmation the posting bot has been added as channel admin, which
this session cannot do on its own. One honest caveat documented in the new
entry's own `$comment`: eligibility matches on course+level only (no
subject column exists on MCQ attempt records) — safe today since
`capranav`'s tenant serves only Advanced Accounts content, but would need
revisiting if the shared pool ever grows a second CA Inter subject.

**Admin Portal**: given the real architectural stakes (this portal can
restart live bots, will eventually edit faculty tokens, and RBAC is
explicitly coming later), asked 4 clarifying questions via AskUserQuestion
*before* writing any code, all answered with the recommended option:
**single-admin login now, RBAC layered on top later** (not a no-auth
system that would need ripping out under time pressure once real RBAC
arrives); **Question Catalog editor is metadata-only for this build**
(chapter tags/marks/difficulty/flags — not full question/answer content
editing, a meaningfully bigger CMS-like scope parked for later); **build
in this order**: Flask migration + sidebar shell + login + Bot Status/
Restart + Bot-wise Logs first (lowest-risk "ops" tier, and the shell
everything else plugs into) → Analytics tabs → Masters display → Masters
editing/Faculty+Bot addition → Leaderboard edits + Catalog metadata edits
last (the two modules that can most directly affect a live student
experience if done wrong); **explicit confirmation dialog required on
every destructive action** (bot restart today, masters/faculty edits
later), not just a clearly-labeled button.

Built the **foundation tier** exactly per that sequencing —
`telegram/admin_portal/`: `app.py` (Flask, installed fresh into the
project's own `.venv` — wasn't a dependency before), a branded sidebar
shell (`templates/base.html` + `static/style.css`, navy/gold via
`brand_kit.colors()`) listing every one of Pranav's ~12 modules up front,
with the ~10 not-yet-built ones rendering as grayed "Soon" items rather
than being invisible — communicates the full intended shape of the portal
even before every piece exists, matching his "each and everything should
be able to be visible" ask. `auth.py` — single-admin session login,
credentials generated this session (username `pranav`, a random strong
password shown once, only its werkzeug hash + a session secret key stored
in `telegram/.env`, rotatable via new `set_password.py`) — every route
wrapped in `role_required("admin")`, never a bare login check, specifically
so adding real RBAC later is a decorator-argument change per route, not a
redesign of how routes are protected. New `admin_actions` DB table +
`audit.py` — every real action (bot restart today; masters edits/faculty
addition/etc. in later phases) logs who did what, when, same "complete
trail" discipline already established for `report_flow_events`/
`leaderboard_broadcast_log`. **Bot Status & Restart** (`/bots`) calls
`manage_bots.py`'s own `restart_bot()` **directly** (imported, not
subprocessed) — the exact same code path the terminal command already
uses, so the button can never drift from that script's real behavior — and
**Bot-wise Logs** tails the same log files `manage_bots.py` already
writes. A shared JS confirm-modal (`base.html`) implements the
"explicit confirm on every destructive action" requirement once, reused
by every future destructive action rather than rebuilt per module.
Registered as `1lavya-admin-portal` in `bots.json` (port 8788 by default,
`ADMIN_PORTAL_PORT` to override) — runs **alongside** the existing
`:8787` dashboard, not replacing it, until the Analytics tier migrates
that dashboard's content over; nothing Pranav currently relies on breaks
mid-transition.

**One real bug found and fixed during verification**: `NAV_SECTIONS`'
dict key `"items"` collided with Python's own built-in `dict.items()`
method — Jinja2's `section.items` attribute-lookup silently resolved to
the *method* instead of the dict key, 500-erroring every single page.
Renamed the key to `"links"`. Separately (not a code bug, but worth
knowing): two stale dev-server processes were left listening on port 8788
from earlier manual testing, and `pkill -f` could not find them in this
Windows/Git-Bash environment — cleared by PID directly via PowerShell's
`Stop-Process`.

**Verification, multi-layered**: `smoke_test_admin_portal.py` (new) — 26
checks via Flask's own `test_client()` (no real network socket): every
protected route correctly blocks unauthenticated access with zero side
effects (no audit row, no process touched), wrong-password rejection,
correct session state through login/logout, the Bots page renders every
real configured `bot_id`, an unknown-`bot_id` restart is handled without
crashing, and a **mocked** real-bot restart proves the full route→
audit-log wiring safely on every re-run (the real, unmocked path was
separately proven — see next). All 26 passed. **Manually verified against
a real bot** (`1lavya-platform-watcher`, chosen as low-stakes): confirmed
an actual PID change, an actual stop→start sequence through
`manage_bots.py`'s real code, a correct `admin_actions` audit row, and —
tested separately — confirmed an unauthenticated restart attempt is fully
blocked, not just redirected cosmetically. **Visually verified** via
headless-Edge screenshots of the login page, Overview, and the Bot Status
table (showing all 9 other bots' real live PIDs/heartbeat ages/statuses)
— this repo's own established discipline (CLAUDE.md section 7) of never
trusting a layout by reading code alone. `health_check.py`: same 16
pre-existing failures, nothing new introduced by this build.

**Not built yet, by design, per the confirmed sequencing**: Analytics
tabs, Masters display/editing, Faculty/New Bot addition (clarified in the
portal's own README before building anything toward it: this can only
ever *generate config* — BotFather bot registration is a human-in-Telegram
action with no public API to automate, so "New Bot Addition" will always
mean "portal writes the `tenants.json`/`bots.json` entries + shows a
checklist of remaining manual steps," never true end-to-end automation),
Question Catalog metadata editor, Leaderboard edits +
student-profile↔leaderboard mappings, and Users & Access (RBAC) — the
very module this whole auth foundation exists to extend. Each gets its
own build → smoke test → Pranav's confirmation cycle before the next,
same discipline as every phase of this roadmap so far. Full detail:
`telegram/admin_portal/README.md`.

### Admin Portal: Analytics tier built (universal table export, bulk report emails, full Student Master) (2026-08-11)

Same day as the Foundation tier, Pranav asked for: (1) download any DB
table as JSON/CSV/XLSX directly; (2) send the existing performance report
by email to one or many students, from the admin portal itself; (3) full
Student Master visibility, "as per his wish"; (4) pagination + filter
criteria + Excel export on every tabular view; (5) every analytics
dashboard downloadable as CSV, and as HTML or PDF on demand. Also asked to
"begin developing all other modules."

Given real ambiguity in the request (a garbled sentence about sending
reports "to any student or of multiple students, to the faculty" could
mean either bulk student-report sending or a separate new faculty-rollup
report type) and real stakes (which DB tables are exportable given some
carry contact info; how large a batch of modules to build before the next
checkpoint), asked 4 clarifying questions before writing code, all
answered with the recommended option: **send existing per-student
reports, individually or in bulk** (not a new faculty-rollup report
type — that's a separate, bigger ask if wanted later); **only email a
student's own already-confirmed address on file** (never guessed/typed in
for them); **any table, no export scoping** (single-admin login is the
only gate today; RBAC later can scope per-role without a redesign);
**build the shared infrastructure + the Analytics module first, then
continue one module at a time** (not several modules at once) — same
build → smoke test → confirmation discipline as every phase so far.

Built shared infrastructure (`telegram/admin_portal/exporters.py`):
`filter_rows()`/`paginate()` — in-memory free-text filter + pagination
over a list of dicts, deliberately reusing every `analytics.py` function's
already-tested full result set rather than rewriting each as a paginated
SQL query (this platform's real data volumes are dozens to low hundreds
of rows, not millions); `csv_response()`/`xlsx_response()`/
`json_response()` — reused by both the generic table-export page and
every curated Analytics view; `render_printable_table()`/
`html_export_response()`/`pdf_export_response()` — **one** branded HTML
snapshot source reused for both the "download as HTML" button (served
as-is) and "download as PDF" (the same HTML through `xhtml2pdf`), so the
two can never drift apart. New Jinja globals `page_url()`/
`clear_filter_url()` (in `app.py`) preserve every other query arg (filter
text, a bot-selector choice, etc.) across a page change or filter clear.

**Data Export** (`/export`) — every real table in `platform.db`, JSON/CSV/
Excel, genuinely no scoping per Pranav's confirmed choice. **5 Analytics
views**, all paginated/filterable/exportable: **Student Master**
(`/analytics/students`) — full contact/faculty/course visibility per
student, plus checkbox-select + **Send Report to Selected**, which emails
each selected student their own existing report PDF, but only where
`students.email` is already echo-confirmed (skipped, never guessed,
otherwise), sent from the admin portal's own dedicated
`reports@1lavya.com` address (an honest label, not impersonating whichever
bot the student happens to use, since this send is admin-triggered, not
bot-triggered) — new `from_email` added to `1lavya-admin-portal`'s
`bots.json` entry for this. **Bot-wise Usage**, **Faculty Report** (with a
per-student **chapter drill-down** as a real sub-page, not an inline
JS-expand row, so it reuses the same pagination/export primitives as
everything else), **Content Health** (flattened to one row per issue),
and **Email Analytics** (the full `report_deliveries` trail, bot- and
admin-triggered sends together).

**Verified**: `smoke_test_admin_portal.py` grew from 26 to **68 checks**,
all passing — every new route's auth gating, the generic export endpoint
(including a rejected unsupported format and a 404 for an unknown table),
Student Master's filter/pagination/all-4-export-formats, the bulk
report-send (mocked `send_report_email()`, verified called exactly once —
only for the student WITH a confirmed email, with the correct
`1lavya-admin-portal` `bot_id` and the exact real email address, correctly
skipping the emailless student, correct flash message, correct audit
row), Bot-wise Usage, Faculty Report + its bot-selector + chapter
drill-down (a 400 when `bot_id` is missing from an export call, a 404 for
an unknown student), and Content Health/Email Analytics. Every
test-inserted `report_deliveries`/`admin_actions` row is identified
precisely (by `delivery_id` captured before/after, never a guessed string
match) and removed in a `finally` block — confirmed zero residue after a
real run. **Visually verified** via headless-Edge screenshots of Student
Master (real 65-row live data, correctly disabled checkboxes for
emailless students) and Data Export (every real table, real row counts).
`health_check.py`: same 16 pre-existing failures, nothing new.

**Not built yet, by design, per the confirmed one-module-at-a-time
pace**: Masters display/editing, Faculty/New Bot addition (still
honestly scoped to config-generation only — no API exists to automate
BotFather registration), Question Catalog metadata editor, Leaderboard
edits + student-profile↔leaderboard mappings, and Users & Access (RBAC).
Full detail: `telegram/admin_portal/README.md`.

### Course Catalog DB table + human-readable MCQ IDs + year-warning fix (2026-08-11)

Same day, Pranav asked for a Course/Level/Subject-wise Course Catalog
view, that this catalog become the **single DB source of truth** for
every MCQ/descriptive question's chapter/unit tagging (not independently
typed per content file), and a new **additive** human-readable ID per
question — `CA_L2_P01_C3_U4_00876` (course, level number, paper number,
chapter, unit, incremental sequence) — retrofitted onto **all** existing
questions, deterministically, via a catalog-driven script. Separately,
asked to check and resolve a Content Health "Recommended field 'year' is
missing" warning.

Investigated the real current state before writing any code (this touches
every question's identity, genuinely high-stakes) — found **4 different,
mutually inconsistent MCQ ID schemes already in production**
(`CAI-P1-MTP-2025-01-S1-PI-Q1-a`, `CA-FND-QUANTS-C1-Q001`,
`CMAI-P5-M12-FACULTY-2026-Q01-...`, `CMAF-P1-FACULTY-CS-ARUN-CHOUHAN-M1-Q01`).
Also found real, **already-verified** raw material to build the catalog
from — none needed fresh research: `books/concept-book/syllabus-engine/
data/1-ca-inter-adv-accounts-topic-page-index.json` (the canonical,
locked CA Inter Advanced Accounting chapter+unit+topic index);
`telegram/source-docs/CS_CMA_Chapter_Catalog.xlsx`'s "Chapter Catalog"
sheet (647 real CS/CMA chapters including `PaperNo`, read directly off
each subject's own printed Table of Contents in an earlier session);
`telegram/tools/cs_cma_common.py`/`build_study_bot_catalog.py` (paper
numbers, independently read off real cover pages, also earlier session);
`telegram/source-docs/StudyHub_Master_Catalog.xlsx` (CA Foundation
Quantitative Aptitude's 18 real chapters).

Given real open forks (a course-code conflict the request itself
introduced, an unclear CS level-numbering mapping, whether to trust or
re-verify embedded paper numbers, and how large a retrofit to attempt),
asked 4 clarifying questions before touching anything, all resolved:
**course code is `CMA`, not the requested `CO`** (every other reference to
this course across the whole platform already uses `CMA` — introducing a
second abbreviation for the same course was flagged and correctly
avoided); **CS level numbering is CSEET=L1, Executive=L2, Professional=L3**
(same graduated pattern CA/CMA already use); **all 4 paper numbers that
currently matter were cross-checked** against the already-verified
sources above (all 4 confirmed correct — no re-typing, no new research
needed, since the verification work had already happened in an earlier
session and just needed tracing to); **retrofit all ~2,500 existing
questions now**, deterministically, via a catalog-driven Python script
(not just new content going forward) — Pranav's own explicit instruction.

Built: new `course_catalog` DB table (`schema.sql`) — one row per
(course, level, paper, chapter, unit), 701 rows total from the 3 verified
sources; CS/CMA chapters (no real ICSI/ICMAI sub-unit structure) use
`unit_no=0`, the same convention CA's own single-unit chapters already
use. `telegram/tools/populate_course_catalog.py` — full rebuild every run
(never a partial merge), a fatal error on any duplicate key so a real
data conflict can never silently overwrite another, `--dry-run` support.
`telegram/tools/generate_mcq_human_ids.py` — retrofits `human_id` onto
every question across **6 real content files**, with the catalog always
authoritative over the question's own tag. **A real mismatch was found
and correctly resolved this way**: CA Foundation Quantitative Aptitude's
625 MCQs all self-tag `U1` on every chapter, but the real ICAI material
has no sub-unit structure there at all (confirmed against the
independently-sourced StudyHub catalog) — the script used the catalog's
correct `U0` for all 625, reporting the mismatch loudly rather than
silently guessing past it either way. **Idempotent by design and by
verification** — a record that already has a `human_id` is never
re-touched; re-running after new questions are added only assigns IDs to
the new ones, so a previously-communicated ID can never change out from
under a student. **Result: 2,486 questions now carry both their original
internal ID and a new human-readable one** (e.g. `CMA_L2_P05_C12_U0_00001`).
New **Admin Portal → Content → Course Catalog** page
(`/content/course-catalog`) — Course→Level→Subject dropdowns, the
resulting chapters/units filterable/paginated/exportable (CSV/Excel/
HTML/PDF), reusing the exact same shared infrastructure every other
Analytics view already uses.

**Verified, multiple layers**: `smoke_test_course_catalog.py` (new) — 39
checks, including direct cross-checks against independently-known real
facts (CA Inter chapter 7 unit 3 = AS-11; CMA Intermediate paper 5
chapter 12 = Companies Act 2013; CA Foundation Quant Aptitude chapter 1 =
Ratio and Proportion), confirmed dry-run never writes, confirmed every
human_id's format/uniqueness, and — the one that actually matters most —
**ran the real generator a genuine second time and confirmed it assigned
exactly 0 new IDs** — real idempotency proven, not just claimed.
`smoke_test_admin_portal.py` grew to **72 checks** with the new route's
coverage. Content validator re-run clean: **0 errors, 0 warnings**
platform-wide. All affected bots (`1lavya-examhub`, `capranav-exam`,
`csarunchouhan`, `1lavya-admin-portal`) restarted; `health_check.py`:
same 16 pre-existing failures, nothing new.

**The "year" warning, separately fixed**: root cause was
`convert_faculty_mcq_docx.py`'s `--year` argument never being passed when
converting Arun's CMA Foundation Law docx — all 375 records got
`year: null`, while the sibling CMA Intermediate Law file (converted
correctly, same pipeline) already had `"2026"`. Fixed at the actual
source file (`cma_foundation_law_faculty_mcqs.json`), re-ran
`merge_faculty_mcq_sources.py` to propagate into the bot-facing combined
file, re-validated clean. Full detail: `telegram/COURSE-CATALOG.md`.

**What's genuinely left, named honestly**: the catalog only covers the 3
subjects that currently HAVE question content — any new subject's real
chapter/unit numbers need the same verified-source treatment (never
hand-typed) before it can be added to `populate_course_catalog.py`.
Question Catalog *editing* (still metadata-only scope, per the earlier
confirmed decision) remains unbuilt — today's Course Catalog page is
view-only. Every other still-open Admin Portal module (Masters editing,
Faculty/New Bot addition, Leaderboard edits, Users & Access/RBAC) is
unaffected by this work, same order as before.

### Real Course Catalog gap found + fixed; year-warning fix re-confirmed (2026-08-12)

The day after the Course Catalog shipped, Pranav checked the live Admin
Portal himself and caught a real, correct issue: *"I saw many subjects
and chapters missing."* He was right — the first `course_catalog` build
only covered 2 of CA's 17 real subjects (Advanced Accounting +
Quantitative Aptitude); CA Final had **zero** subjects at all. CS/CMA
were always fully covered (their source already lists every subject with
a real `PaperNo`) — the gap was CA-specific, caused by
`rows_from_studyhub_catalog()` being hand-scoped to one subject instead
of importing `telegram/tools/build_study_bot_catalog.py`'s own
already-verified `COURSE_META` dict (all 17 CA subjects, real
cover-page-verified paper numbers) directly.

**Fixing this surfaced two MORE real bugs**, both caught by the
catalog's own duplicate-key collision check doing exactly its job, not
found by inspection: (1) CA Final Advanced Auditing's chapter 14 is
genuinely two units ("Special Features of Audit of Banks" / "...of
NBFCs") sharing one chapter number — an initial "every StudyHub-sourced
subject is single-unit" assumption collapsed them into a fabricated
collision; fixed by parsing each file's real unit number from its own
embedded `M{module}-C{chapter}-U{unit}` filename segment, verified
against all 314 real CA Study Material filenames first (0 unmatched)
before being trusted. (2) CA Inter Financial Management's chapter 9 has
6 real named units ("Unit I" through "Unit VI") plus an Appendix, but
**every one of their filenames says `U0`** — the filename's own unit
segment is simply wrong for this specific subject; fixed by checking each
row's Label text FIRST for an explicit "Unit N" prefix (roman or arabic
numeral), trusted as authoritative over the filename when present. The
Appendix, and two similar chapter-level review files in Financial
Reporting ("Comprehensive Illustrations", "Test Your Knowledge"), are now
correctly excluded entirely — genuine review material, not real syllabus
topics an MCQ would ever be tagged to as its own unit.

**Result**: **957 catalog rows** (up from 701), all 17 real CA subjects
present, CA Final populated for the first time. The human_id generator
re-run confirmed **fully idempotent** against this larger catalog — 0 new
IDs assigned (no new question content was added, only catalog coverage).
5 new permanent regression checks added to `smoke_test_course_catalog.py`
for these exact 3 cases so this bug class can't silently reappear.
Visually re-verified via headless-Edge screenshot: CA Final Financial
Reporting (previously completely empty) now shows its real 46-row
structure, multi-unit chapters intact. Full smoke suite (course catalog,
admin portal, report flow, profile flow, leaderboards) re-run clean;
`health_check.py`: same 16 pre-existing failures, nothing new.

**Separately, Pranav asked to reconfirm the "year" warning fix from the
day before was still holding** — verified fresh, live, in all four places
it could show up (the raw validator, the old `:8787` dashboard's live
API, the new Admin Portal's Content Health page, and every bot's own log
file): 0 errors, 0 warnings everywhere, confirmed right now rather than
just trusted from the earlier fix. Full detail:
`telegram/COURSE-CATALOG.md`'s new section.

### 4 document/question catalogues added to the Admin Portal (2026-08-12)

Pranav asked for the existing Course Catalog page to become the live
**Study Materials** catalogue (reading from `telegram/source-docs/
knowledge_base_documents.json`), plus 3 more catalogues under the same
Course/Level/Subject picker: **Exam Materials**, **Revision Material**,
and a **Question Bank** catalogue (chapter-level MCQ + Descriptive counts
per subject/level/course). Also asked whether 3 PDFs he'd just added to
the Study Materials folder (CA Inter Law's "Other Laws" part — General
Clauses Act, Interpretation of Statutes, FEMA 1999) were showing up.

**They weren't** — `knowledge_base_documents.json` is generated from
`1Lavya_Study_Hub_File_Mapping.xlsx`, not by scanning the folder directly,
and the 3 new PDFs had never been added to that source Excel. Fixed at
the root (verified real chapter titles by reading each PDF's own first
pages, added 3 rows, re-ran the full downstream chain:
`build_master_catalog.py` → `populate_course_catalog.py` →
`build_knowledge_base_catalog.py`). A second real bug surfaced
immediately via `populate_course_catalog.py`'s own duplicate-key check:
CA Inter Corporate and Other Laws' printed chapter numbering genuinely
restarts at Module 4 (Chapter 1/2/3, "Other Laws"), colliding with Module
1's own Chapter 1/2/3. Verified this is the ONLY CA subject with this
pattern (checked all 17), then added a small, explicit, documented offset
(`CHAPTER_NO_MODULE_OFFSET`) so Module 4's chapters continue the
subject's sequence as 13/14/15 instead of colliding. `course_catalog`
grew from 957 to 960 rows.

Built `telegram/admin_portal/document_catalog.py` — the query layer for
Study/Exam/Revision Material (documents from `knowledge_base_documents.json`
joined to `course_catalog`'s chapter taxonomy at chapter granularity) and
Question Bank (MCQ/Descriptive counts computed directly from every
question's own `human_id`, 100% accurate by construction). Wired into the
Admin Portal as a 5-tab strip on `/content/course-catalog` (the 4 new
tabs plus the original Chapter Taxonomy view, kept not replaced), sharing
one Course→Level→Subject picker via a `catalogue` query param, each tab
with the same pagination/filter/CSV/Excel/HTML/PDF export every other
Admin Portal table has. Exam Materials only has CA Inter Advanced
Accounting content (58 files) — sourcing official CS/CMA exam papers from
ICAI/ICSI/ICMAI's own websites was raised and explicitly deferred to its
own separate task (asked via AskUserQuestion, Pranav's choice); every
other course/level/subject shows an honest "not sourced yet" row, not a
silent gap. Revision Material is honestly empty everywhere too (the
folder has no files yet).

A third real bug was found testing Pranav's own example URL
(`?course=CA&level=Inter&subject=Accounting` — the real CA Inter subject
is "Advanced Accounting"): an invalid subject in the URL silently queried
zero matching rows and rendered an unexplained empty table. Fixed — an
unrecognized course/level/subject now falls back to the first real
option instead.

**Verified**: `smoke_test_course_catalog.py` gained 2 new regression
checks (all passing, including the original 39). `smoke_test_admin_portal.py`
grew to 87 checks (from 72) covering the 4 new tabs, the collision fix,
honest-empty states, and the invalid-subject fallback. Content validator
still 0 errors/0 warnings. Visually verified via headless-Edge
screenshots. `1lavya-admin-portal` and `1lavya-studyhub` (the bot that
actually serves these files to students) both restarted and confirmed
loading the updated catalog live. `health_check.py`: same 16 pre-existing
failures, nothing new. Full detail: `telegram/COURSE-CATALOG.md`.

### CA Foundation Accounting: 4 missing chapters found + real ICAI PDFs sourced (2026-08-12, later same day)

While reviewing 2 newly-added MCQ content sets (CA Foundation Accounting
and Business Economics) for chapter-name accuracy against the master
syllabus, found a real gap: the new Accounting MCQ set correctly tests
Chapters 8–11 (Financial Statements of NPO / Accounts from Incomplete
Records / Partnership and LLP Accounts / Company Accounts) — real ICAI
syllabus content — but `course_catalog` had no rows for any of them (it
stopped at Chapter 7), and no Study Material PDFs existed either. Rather
than guess, asked Pranav for the official syllabus link
(https://www.icai.org/post/19138), confirmed all 11 chapters (including
the exact 6-unit split for both Ch.10 and Ch.11) match ICAI's own
published syllabus exactly — the new content was more complete than our
data, not deviating from it.

Found and downloaded all 15 real PDFs directly from ICAI's own CDN
(linked on that same syllabus page), verified each (correct page counts,
first-page title text matches), added to Study Materials using the
existing naming convention, added 15 rows to `1Lavya_Study_Hub_File_
Mapping.xlsx`, re-ran the full downstream chain. No collision this time —
`course_catalog` grew cleanly 960→975 rows. 3 new permanent regression
checks added; full suite passing; content validator 0/0; `1lavya-studyhub`
and `1lavya-admin-portal` restarted, confirmed loading 1102 total catalog
rows live. `health_check.py`: same 16 pre-existing failures, nothing new.
Full detail: `telegram/COURSE-CATALOG.md`.

### CA Foundation Accounting + Business Economics MCQs: fixed, normalized, and made live (2026-08-12, later still)

Finished the job on the 2 new MCQ content sets: built `telegram/tools/
ingest_ca_foundation_accounting_economics_mcqs.py`, which repaired the 3
invalid-JSON files (including a real `":="` typo found only once repair
was attempted), merged both subjects' many scattered per-chapter/unit
files into 2 clean subject-level files (1,595 Accounting + 918 Economics
MCQs) per the confirmed one-MCQ-plus-one-Descriptive-per-subject
convention, and resolved every question's real chapter/unit via a single
regex against the source's own (inconsistently-formatted but always
present) unit indicators — no fuzzy topic matching needed.

4 more real defects found and fixed via preflight checks failing loudly,
not inspection: a Python falsy-zero bug that silently dropped a valid
`correct_answer: 0`; 3 different per-chapter answer formats (option
text, a letter, a 0-indexed integer) all needing separate handling; a
`mc_id`/`mcq_id` key typo; and a `Options`/`options` capitalization typo.
Also corrected the source data's own inaccurate `exam_type: "MTP"` label
(these are self-authored practice MCQs, not from a real ICAI paper) to
`"PRACTICE"`, matching the existing CA Foundation Quant Aptitude
convention.

Extended `generate_mcq_human_ids.py` with a new `_resolve_by_chapter_
slug()` resolver — all 2,513 records got a real human_id, idempotent on
a second run. Added both files to `1lavya-examhub`'s `tenants.json`
scope and restarted it — confirmed loading both cleanly in its own
startup log. Admin Portal's Question Bank tab now shows real per-chapter
counts for both subjects (verified summing to 1,595/918 exactly, plus a
live screenshot). Content validator 0/0, both course-catalog and
admin-portal smoke suites still fully passing, `health_check.py`: same
16 pre-existing failures. Still open: faculty attribution (null, needs
Pranav's input), duplicate-question detection, and "student tags" — all
named honestly, not silently dropped. Full detail:
`telegram/COURSE-CATALOG.md`.

### MCQ_PROMPT.md: AI-model prompt for generating MCQ JSON correctly (2026-08-12)

Pranav asked for a "Skill plus prompt" file to hand to AI models
generating MCQ JSON from PDFs, so future batches don't need the
repair/normalize pass the CA Foundation Accounting/Economics batches
just needed. Built `telegram/base_formats/MCQ_PROMPT.md` — a paste-ready
system prompt directly encoding every real defect found and fixed this
session (invalid JSON escaping, inconsistent answer-key formats across
chapters, field-name typos, and a confirmed case of a chapter_slug
copy-pasted from `base_formats/mcq_input_example.json`'s own AS-1
example into an unrelated Economics chapter and never updated). Built on
`generate_base_formats.py`'s already-existing authoritative field
contract rather than re-deriving field names. Includes a worked example,
a JSON validity checklist, content-fidelity rules, and a mandatory
8-point self-check. Documents that any resulting batch still needs the
same ingestion-script preflight (duplicate IDs, correct_option validity,
course_catalog cross-check) — the prompt reduces defects, doesn't
replace verification. `health_check.py`: same 16 pre-existing issues.

### PM+CTO scale review (100k-student target) + real production bug found and fixed in exam_hub_bot.py (2026-08-12)

Pranav asked for an independent PM+CTO-level review of the whole Telegram
platform against his real target — 100,000+ students, currently ~100 —
and separately reported a live bug: MCQ practice silently did nothing
after selecting Year.

**Review findings** (the feature layer is solid — ledger-based wallet,
JSON-source-of-truth configs, audit trails, real smoke tests; the
*infrastructure* layer is still prototype-scale): single local-Windows-PC
deployment with no auto-restart-on-crash and no real off-machine backups
(highest-priority gap); every bot opens one SQLite connection at startup
and reuses it for every concurrent update, blocking its single asyncio
event loop under contention — untested at any real load; no working
billing/quota enforcement despite a well-designed `wallet_ledger` schema;
long-polling (`run_polling()`), no horizontal-scaling path for a single
popular bot; content requires a full bot restart to reload; dev work
happens directly against the same `platform.db` file live bots write to
(no staging environment); the same callback_data-collision bug class has
now recurred 3+ times; no rate-limiting anywhere; faculty onboarding is
fully manual (new BotFather token + config + content pipeline run, no
self-serve). Logged as a durable, brief callout right after §2 of this
file (**"Telegram platform: known scale-readiness gaps"**) so any future
session sees it before adding more features on top — full narrative
review lived only in that session's conversation, not reproduced here in
full; the callout is the lasting artifact.

**The reported bug, root-caused via the real logs** (not guessed):
`1lavya-examhub.log` showed `telegram.error.BadRequest: Button_data_invalid`
firing on `edit_message_text` inside the "year" action's chapter-picker
build — some content sources (the newly-ingested CA Foundation
Accounting/Business Economics banks) slugify a full chapter/unit name
into `chapter_slug` (one over 100 bytes on its own), and putting that raw
string straight into `callback_data=f"chapter:{slug}"` blew past
Telegram's hard 64-byte `callback_data` limit — **one bad button broke
the ENTIRE keyboard for that Year**, not just the long one, so a student
who picked Year saw the loading spinner clear and then nothing. Fixed by
carrying a small integer INDEX in callback_data instead (same pattern
already used for Study Hub's own past fix of this exact bug class — see
§8) and resolving it back via `context.user_data["chapter_slugs"]`, never
the raw slug. A second, related bug found in the same logs
(`KeyError: 'exam_type'`, from `capranav-exam.log`/`csarunchouhan.log`) —
the `year`/`chapter` actions read prior-step state via raw dict indexing;
a stale keyboard tapped after a bot restart (in-memory `context.user_data`
doesn't survive one) crashed silently after `query.answer()` already
fired. Fixed with a new `_require_state()` helper used everywhere a
handler reads a prior step's value — shows "session expired, start over"
instead of crashing. Verified against the real offending data (confirmed
3 of 71 CA Foundation chapters would have broken the old code; all now
resolve at 10 bytes) before deploying to `1lavya-examhub`, `capranav-exam`,
`csarunchouhan` — confirmed clean restarts, 0 new tracebacks.

### Exam Hub rebuilt Mode-first; real Subject-picker gap closed (2026-08-12, same day)

While investigating the callback bug above, confirmed a second real gap
Pranav suspected: Exam Hub had **no Subject-level picker at all**
(Course→Level→Mode→ExamType→Year→Chapter, nothing narrowed by Subject) —
at CA Foundation this already merged 3 separate subjects'
(Accounting/Business Economics/Quantitative Aptitude) chapters into one
flat, undifferentiated Chapter list. Asked Pranav which flow order he
wanted — Subject-before-Mode (minimal change) vs. Mode-first with every
Course/Level/Subject list derived live from real content (bigger rework,
never shows a dead end) — he chose **Mode-first**.

Rebuilt `exam_hub_bot.py`'s entire flow as **Mode → Course → Level →
Subject → Exam Type → Year → Chapter → question**, every step
auto-skipped when exactly one real option exists, every option list
derived live from actual loaded content intersected with the tenant's
`content_scope` (never a hand-maintained "show every course even the
empty ones, gate later" list — the explicit UX choice behind Pranav's
pick: a student never taps into a dead end). Two structural pieces:

- **`_resolve_course_level_subject()`** (new) — every question record now
  resolves to a real `(course, level, subject)` triple, derived from
  `human_id` (`{COURSE}_L{n}_P{paper}_C{c}_U{u}_{seq}`, already present on
  nearly every record) joined against the platform's own `course_catalog`
  DB table — the SAME single-source-of-truth mechanism already used for
  chapter/unit naming (§ COURSE-CATALOG.md), just applied one level up.
  This fixed a real correctness gap along the way, not just added a new
  step: 2 of 3 CA Foundation content files had no `subject` field at all;
  the flagship's descriptive bank (`book_questions_extracted.json`) had
  no `course`/`level` field on ANY record at all — a "no course/level
  field always matches" hack that was only ever correct because exactly
  one course/level/subject existed in scope when it was written, and
  would have been silently wrong the moment a second one did. Validated
  against every real record across every tenant before shipping: 0
  unresolved ("Unknown").
- **`resolve_entry()`** (replaces `entry_screen_and_updates()`) — one
  cascade function reused for BOTH the initial `/start` screen and every
  mid-flow button tap, removing the pre-existing code's duplicated
  auto-skip logic between the two (a real simplification, not just a
  rename). The old hand-maintained `AVAILABLE_DATA`/`COURSES` globals are
  gone entirely.

`faculty_bot.py` updated to match (calls `eh.resolve_entry(context)`,
callback-pattern registration gained `subject`). New
`exam_hub_sessions.subject` DB column (via `db.py`'s `_COLUMN_MIGRATIONS`
list) for the same drop-off analytics `course`/`level`/`mode` already
had. Verified via 3 full simulated click-journeys driving the real
`button_router` against real data (multi-subject CA Foundation MCQ with
an actual queued question, full-auto-skip CA Inter Descriptive matching
the pre-rewrite zero-extra-taps behavior exactly, csarunchouhan's CMA
Foundation/Intermediate subject differentiation) before deploying — all
passed. Deployed to `1lavya-examhub`, `capranav-exam`, `csarunchouhan`;
confirmed clean restarts. `README_Bot2_ExamHub.md` rewritten to match the
new flow.

### Chapter-label duplication fixed, CMA Law MCQs merged into the flagship bot, "Report Issue in MCQ" + a real "I'm Done" summary built (2026-08-13)

Pranav flagged 3 more things after using the rebuilt Exam Hub: (1)
chapter names showing without Unit distinction, so many chapters looked
repeated in the picker; (2) CMA Foundation/Intermediate Law MCQs
(csarunchouhan's content) missing from the flagship `1lavya-examhub` bot,
since — his stated position — 1LAVYA gave Arun ACCESS to this content for
his own bot, it isn't his exclusively; (3) wanted a "Report Issue in
MCQ" 4th button (category + free text, stored for later resolution) and
a real "I'm Done" summary (today's stats, then the existing report
offer) instead of "I'm Done" silently resetting.

**Chapter duplication, root-caused via a real data audit, not assumed**:
CA Foundation Accounting/Business Economics were ingested with a bare
"Chapt N"/"Chapt. N" `chapter_label` carrying no Unit distinction — e.g.
literally 7 different real units all labeled "Chapt 1", 4 different units
all labeled "Chapt 7". The underlying grouping (`chapter_slug`) was
always correct; only the DISPLAYED label collided. Fixed with a new
`_disambiguate_chapter_labels()` post-load pass in `exam_hub_bot.py`:
within each (course, level, subject) scope, detects labels shared by more
than one distinct `chapter_slug` and appends the real unit/chapter name
(via the SAME `course_catalog` join mechanism, extended to also capture
chapter_no/unit_no from `human_id`) — falling back to a title-cased slug
if even that lookup fails, so nothing is ever left silently ambiguous.
Deliberately surgical: a label that's already unique (the flagship's
"AS 11: ..." style) is never touched. Verified: 0 duplicate labels
remaining in both affected subjects; flagship labels confirmed unchanged.

**CMA Foundation + Intermediate Law MCQs (1,025 questions) added as a
5th `mcq_json` entry** in `tenants.json`'s `1lavya-examhub` tenant —
csarunchouhan's own bot is unaffected (still scoped to just his
`content_scope`). MCQ only in this first pass, per Pranav's literal ask
that day (descriptive followed later the same day — see below).

**"Report Issue in MCQ" built**: new `telegram/bots/mcq_issue_flow.py`
(same shape as `profile_flow.py`/`report_flow.py` — the host script owns
callback registration and `text_router` priority-checking; this module
never imports `exam_hub_bot.py`/`McqBank` at all, every field it needs is
passed in by the caller at call time, by deliberate design for reuse and
zero circular-import risk). New `mcq_issue_reports` DB table (bot_id,
telegram_user_id, mcq_id, course/level/subject/chapter, `category` —
wrong_question/wrong_answer/typo_error/wrong_mapping/other — description,
status, created_at). New 4th button on the MCQ answer screen; category →
free-text → stored → "Thanks for your report... you may also mail us at
support@1lavya.com" confirmation, restoring the exact Next/Chapter-List/
I'm-Done keyboard the student was already looking at. Cancel path
verified too, same restore behavior.

**"I'm Done" — found a real bug while building the requested feature,
not just a missing feature**: it was wired to the IDENTICAL bare
`restart` callback_data as "Start Over" — tapping it silently reset
straight to the Mode picker, zero summary, ever; not a design choice.
Fixed: new `imdone` action, new `student_analytics.fetch_today_summary()`
(platform-wide, UTC calendar day — MCQs attempted/answered/correct,
descriptive questions viewed, a deliberately simpler "time spent today"
metric than the full report's all-time session-span number, documented
as such), shown before offering the SAME existing on-demand report flow
via `report_flow.py`'s already-built `report:ondemand_yes`/`_no` buttons
directly — zero new report-delivery code, just setting
`report_flow_bot_id` the same way that flow's other two entry points
already do.

All 4 pieces verified end-to-end against real data/the real database
before deploying (full click-journey simulations, including a real
category-report round trip confirmed stored correctly with every field,
the cancel path, and "I'm Done" reading real today's-DB-rows) — not just
structurally. Deployed to `1lavya-examhub`, `capranav-exam`,
`csarunchouhan`; confirmed clean restarts, 0 new tracebacks.
`README_Bot2_ExamHub.md` and `telegram/FIRST_PROMPT.md` updated to match.

### Standing "everything joins the flagship" rule locked in; human_id made genuinely live; MCQ Issue Reports added to the Admin Portal (2026-08-13, later same day)

Pranav extended the CMA-merge decision above into a standing platform
rule: **every question on the platform — MCQ or descriptive, 1LAVYA-
authored or faculty-sourced — becomes part of the flagship
`1lavya-examhub` bot's pool, full stop.** Provenance is tracked via
tagging, never via withholding content from that pool; a faculty's own
bot stays narrowly scoped to their own `content_scope`, unaffected. He
also asked for issue reports to get a real place in the Admin Portal, and
flagged that the human-readable MCQ ID work from 2026-08-11
(`generate_mcq_human_ids.py`, see COURSE-CATALOG.md) never actually went
live — computed, but never shown to anyone or used anywhere.

**csarunchouhan's 47-question descriptive Companies Act bank merged into
the flagship** — `tenants.json`'s `descriptive_json` became a list (same
pattern `mcq_json` already used since 2026-08-11). Investigating first
(never assumed) surfaced a real data-sync bug: the bot-facing file had
been copied from its raw, already-human-id'd source *before* the
2026-08-11 human_id retrofit ran — a full field-diff confirmed every
OTHER field was byte-identical between raw and bot-facing, human_id was
the ONLY gap, 0 of 47 records had it. Patched directly from the
already-correct raw source; verified 47/47 correct afterward, 0 NUL
bytes, valid UTF-8/JSON.

**`_content_owner` provenance tagging built** (`exam_hub_bot.py`) —
inferred purely from each source file's own path convention
(`.../faculty/<tenant_id>/...` → that tenant_id; everything else →
`"1lavya"`) — no per-record field or content-file schema change needed
anywhere. This is exactly the "content-ownership tagging convention"
`schema.sql` had documented back on 2026-08-09 but left unwired — now
wired. Persisted into 2 new DB columns, `content_owner` and `human_id`,
on both `exam_hub_mcq_attempts` and `exam_hub_descriptive_events` (via
`db.py`'s migration list, since both tables already had live rows),
enabling future usage/accuracy breakdowns by content source, not just by
which bot logged the row. Verified: exactly 3,472 "1lavya" + 1,025
"csarunchouhan" MCQs, 455 + 47 descriptive — matching expected counts
precisely, 0 missing `human_id` anywhere in the merged pool.

**`human_id` made genuinely live**: already 100%-covered and globally
unique across the whole merged pool (verified by direct audit before
touching anything — 0 duplicates, 0 missing), the gap was purely that it
was never surfaced. Added as the first line (🆔) of every question's meta
text, both Descriptive and MCQ. Threaded through the issue-report flow
too — `mcq_issue_reports` gained its own `human_id` column (added via
`db.py`'s migration list, since that table had been created earlier the
SAME day by the CREATE TABLE in schema.sql, and `CREATE TABLE IF NOT
EXISTS` doesn't retroactively ALTER an already-existing table — a real,
easy-to-miss gotcha worth remembering for any future same-day
table-then-column addition), shown on the category-picker screen and the
thank-you confirmation, so a filed report is always traceable to one
exact, citable question.

**"MCQ Issue Reports" — new Admin Portal Analytics page**
(`/analytics/issue-reports`), same paginated/filterable/exportable
(CSV/Excel/HTML/PDF) shape as every other Analytics view, joined to
`students` for a display name. Read-only for now — no status-editing UI,
not asked for (the generic "Data Export" page and direct SQL already
cover marking a report resolved if needed sooner). Verified with a
synthetic DB row through Flask's real `test_client()` (login, render, all
4 export formats, cleanup confirmed), then added as a permanent new step
in `smoke_test_admin_portal.py` (same insert-verify-cleanup discipline
the rest of that suite already uses) — full suite re-run clean at
**110 checks, 0 failures**. **Real-world confirmation, found while
verifying**: Pranav had
already filed a genuine issue report through the live bot right after
the feature's first deploy that same day (a Factories Act MCQ,
`telegram_user_id` = his own real admin chat ID) — left untouched (real
user data, not test residue), now visible in this new page.

All 3 pieces verified end-to-end against real data/the real database
before deploying. Restarted `1lavya-examhub`, `capranav-exam`,
`csarunchouhan`, `1lavya-admin-portal`; confirmed 0 tracebacks since
restart in every log (checked from each process's actual restart-marker
log line, not a naive timestamp-string comparison — the first attempt at
that check gave a false positive from exactly that mistake).
`README_Bot2_ExamHub.md`, `database/README.md`, and
`admin_portal/README.md` updated to match. Full session-by-session detail
for everything in this and the 3 entries above:
`_claude/memory/project_log.md`'s 2026-08-12/2026-08-13 entries.

### External-contributor CA Inter Cost & Management Accounting MCQs reviewed + wired live (2026-08-13, later still)

An external contributor (govinjee@gmail.com) submitted MCQ batches for CA
Inter Cost & Management Accounting into a new `telegram/assets/exam_bot/
ca-inter-cost-accounting/` folder, in 3 rounds — an initial 75-question
file with real format gaps (missing `human_id`/`subject`, wrong `level`
value, an invented `unitcode`), flagged back via a drafted email; a
corrected 200-question resubmission reviewed clean (including
independently re-deriving every "Hard" question's arithmetic); then 5
more chapters (500 more MCQs, 700 total) submitted the same way and wired
directly per Pranav's instruction. All 700 validated (0 errors, 0
ID/`human_id` collisions against ~4,500 already-live questions), wired
into `1lavya-examhub`'s `mcq_json` list in `tenants.json`, dry-run
verified against the real loading logic before the live bot was touched,
then deployed with a clean restart and 0 regressions elsewhere. Platform
MCQ pool: 4,497 → 5,197. Full detail: `_claude/memory/project_log.md`'s
2026-08-13 (cont'd, 2) entry.

### Admin Portal Overview rebuilt into a real analytics dashboard (2026-08-13, later still)

Pranav asked for the Overview page (previously a 3-tile placeholder) to
become a full executive dashboard: student onboarding trends, content
growth, top performers, time spent, questions attempted, and a faculty
roster — date-ranged, filterable, and exportable (CSV/Excel/HTML/PDF,
charts included), sub-tab organized, with content-catalog drill-down.
Asked 4 clarifying questions before building (all his recommended
choices): Overview is a **summary layer** linking into the already-built
detailed Analytics pages, not a duplicate of them; **new-questions
tracking starts today forward only** (a new `content_ingestion_log` DB
table — no historical ingestion-date data exists anywhere to backfill
from); **charts are self-built inline SVG**, no new JS dependency;
**"Top Performing Students" reuses the exact student-facing leaderboard
definition** (accuracy % + minimum-attempts floor), not a new ranking.

Built 4 sub-tabs (Students / Content / Performance / Faculty) with a
shared date-range picker, `telegram/admin_portal/charts.py` (inline SVG)
+ `charts_pdf.py` (reportlab-native PDF chart rendering — found and
worked around before shipping that `xhtml2pdf` can't reliably render
inline `<svg>`, so PDF chart export needed its own code path, no new
dependency since reportlab is already vendored). Faculty roster correctly
counts "questions contributed" only from a faculty's own `faculty/
<tenant_id>/` content files, never a shared/flagship file their tenant
also references — verified against real data (`capranav` correctly shows
0 contributed, matching his `own_content.status == "not_ingested"`).
`smoke_test_admin_portal.py` grew from 110 to 182 checks, all passing;
visually verified via headless-Edge screenshots of all 4 tabs against
real data on a throwaway diagnostic instance before deploying to the real
process. Full detail: `telegram/admin_portal/README.md`'s "Overview
rebuild" section.

### Faculty Comprehensive Report built (2026-08-14)

Pranav asked for a full, deterministic, per-faculty report for any date
range: which subjects/levels are live for that faculty and how many MCQ/
Descriptive questions exist, which chapters are most accessed/practiced
(MCQ attempted/correct/time spent), student-wise performance, a last-7-
days student-wise trend, which chapters each student practices most, and
a question-wise difficulty analysis (which MCQs are most often wrong, and
what students chose instead of the right answer) — downloadable as PDF/
XLSX/HTML by button and emailable straight to the faculty, with **no
commentary, just raw facts in properly-headed tables** (his explicit
wording).

Built as a new **Analytics → Faculty Comprehensive Report** page
(`/reports/faculty`), distinct from and alongside the existing per-bot
"Faculty Report" page. New `telegram/admin_portal/faculty_report.py` (the
query/render/email layer, six sections, all pooling activity across every
bot a tenant has — e.g. Pranav's `capranav-study` + `capranav-exam`
together, not one bot's slice), a new `faculty_report_deliveries` audit
table, and three new routes wired into `app.py`. Reused every existing
pattern rather than inventing new ones: `document_catalog.question_bank_
rows()` for the human_id-derived question counts, `brand_kit.py` for the
branded PDF/HTML/email look, the same Cloudflare Email Service backend
`report_delivery.py` already uses for student reports.

**Real bug found and fixed via actually running it against the live DB**
(not by inspection): the student "last active" tracker tried `max()`
across a mix of `None` and real timestamp strings on a student's first
row, crashing every call — fixed by filtering `None`s out first, then
re-verified clean against all 4 real tenants with real data.
`smoke_test_admin_portal.py` grew from 182 to 205 checks, all passing;
`health_check.py`: same 16 pre-existing failures, nothing new;
`1lavya-admin-portal` restarted, confirmed live with a clean startup log
immediately after. Full detail: `telegram/admin_portal/README.md`'s
"Faculty Comprehensive Report" section.

### Faculty Master DB table + Masters → Faculty Details built (2026-08-14, later same day)

Pranav asked directly whether faculty contact/admin details should live
in a DB table or a JSON file — confirmed via AskUserQuestion: **DB
table**. New `faculty_master` table (`schema.sql`) holds `contact_email`/
`contact_phone`/`notes` only — deliberately not duplicating anything
`tenants.json` already owns (`content_scope`/`kind`/`onboarding_fee`
etc. stay there, read directly by the bot scripts at startup). New
`telegram/admin_portal/faculty_master.py` (list/get/upsert) and a new
**Masters → Faculty Details** page (`/masters/faculty`, list + per-
tenant edit form), audit-logged like every other portal write. The
Faculty Comprehensive Report's email box now pre-fills from this table
instead of the `tenants.json` field the earlier entry above added (that
field was removed the same day, before anything depended on it).

**Real mid-build issue caught and fixed**: since the live
`1lavya-admin-portal` process re-runs `init_schema()` (`CREATE TABLE IF
NOT EXISTS`) on every request, a live request landed between this
table's first draft and its trimmed final column set, creating the real
table with the wrong (draft) columns before the file settled — caught by
checking `PRAGMA table_info`, confirmed 0 rows existed yet, fixed with a
`DROP TABLE` + re-`init_schema()`. Worth remembering: a table's *shape*
isn't safely re-editable mid-session once any live process may have
already created it from an earlier draft of the same file.

`smoke_test_admin_portal.py` grew from 205 to **220 checks** — including
one that captures and restores whatever real row already exists for the
tenant it exercises (rather than blindly overwriting-then-deleting,
which would have destroyed real admin-entered data on a re-run).
`health_check.py`: same 16 pre-existing failures, nothing new;
`1lavya-admin-portal` restarted, confirmed live. Full detail:
`telegram/admin_portal/README.md`'s "Faculty Master DB table" section.

### Whole platform found down + Windows autostart/health-check automation built (2026-08-15)

Asked to check whether the bots were working — found **every single one**
down, heartbeats stale by ~4.7 hours (the exact "no auto-restart-on-crash"
gap already flagged right after §2). Restarted all 9 via `manage_bots.py
start`. Pranav then asked for two standing safeguards: a script that
auto-runs at Windows startup, and a Task Scheduler job every 30 minutes
that restarts anything found down.

Added a new `ensure-running` action to `manage_bots.py` — starts any
`active` bot that isn't running, and (new) **restarts** any bot that IS
running but whose heartbeat has gone stale (a hung process, not just a
dead one). New `telegram/tools/ensure_bots_running.bat`, the actual
unattended entry point, using the repo's `.venv` interpreter explicitly
and a `ping`-based delay (`timeout.exe` hard-refuses to run with no real
console attached — confirmed by testing). Wired into **both** requested
places: a Startup-folder shortcut (`shell:startup`, points at the
canonical repo `.bat`, not a copy) and a new Task Scheduler job,
**"1LAVYA Bots - Health Check"**, every 30 minutes indefinitely. A true
pre-login "at system boot" trigger needs elevated rights this session's
shell doesn't have — not created; documented as a known gap with the
exact elevated command to run if Pranav wants it too (the Startup
shortcut + 30-min recurring task already bound any real outage to ≤30
min regardless).

**A real bug found and fixed along the way**: an earlier manual test left
a timezone-naive heartbeat timestamp in the DB for one bot, which crashed
`analytics.fetch_heartbeats()` — outside its existing `try/except`, which
only guarded the parse step, not the later naive-minus-aware subtraction
— silently dropping *every* bot's heartbeat, not just the bad row's, and
put the platform watcher into a real 60s crash loop. Fixed the bad value
and hardened `fetch_heartbeats()`/`_parse_iso()` so one malformed row can
never take the whole function down again. All 9 bots restarted to pick up
the fix (imports don't hot-reload).

**Also investigated and ruled out**: every bot briefly showing as *two*
OS processes (one `.venv` path, one the machine's global Python, the
global one a child of the venv one) looked exactly like a duplicate
instance/Telegram-polling-conflict risk — chased with a live-monitored
kill-and-watch test before `.venv\pyvenv.cfg` settled it: this is Python
3.11+'s normal Windows venv-launcher stub-plus-worker behavior, not a
bug, not a second bot instance. Worth knowing so a future session doesn't
re-chase the same ghost. Full detail, all of the above:
`telegram/database/README.md`'s "Self-healing autostart" section.

### Off-machine backup built: Cloudflare R2 + D1, nightly (2026-08-16)

Directly follows from the scale-readiness gap #1 callout right after §2
("no real off-machine backup") — this closes that half of the gap (the
"no auto-restart-on-crash" half is still open). Pranav asked what to back
up and how, given the platform runs off one standalone PC; after a real
inventory (not guesswork) confirmed the exposure — `database/platform.db`
(880KB then, live student/wallet/MCQ data), the separate
`assets/myfiles_bot/myfiles_hub.db` + its `uploads/` (real student-
uploaded files), and 1,803 sourced PDFs (~1.4GB actually served) are
**100% local-only** (gitignored by design: `**/*.db`, `**/*.pdf`, `*.env`,
`creds.txt`) — while Python code + question-bank JSON + config JSON are
already safe via `git push` — the plan was scoped to exactly the
git-uncovered set, R2 for blob storage + a D1 mirror for a queryable
off-site copy (Pranav's confirmed choice over R2-only).

**Account decision, corrected mid-flow**: initially set up against a new,
separate 1LAVYA Cloudflare account Pranav created — he then confirmed
staying on the existing **EfficientCorporates (ECPL) account** instead
(same one `CF_EMAIL_*` already uses), since `1lavya.com`'s domain
currently lives there; the 1LAVYA account id is kept on file in
`telegram/.env`'s comments for whenever the domain itself migrates. Pranav
created one Custom API Token himself (`Account > Workers R2 Storage >
Edit` + `Account > D1 > Edit`) and pasted the raw value into chat — Claude
then derived the R2 S3-compatible Access Key ID/Secret Access Key
**without any extra dashboard step**, per Cloudflare's own documented
mechanism (Access Key ID = the token's `id`, Secret = SHA-256 of the token
value), and verified this for real (not just computed) with an actual
signed `ListBuckets` S3 call before trusting it.

**Built**: `telegram/tools/backup_to_cloudflare.py` — SQLite-consistent
snapshots (via `sqlite3`'s own `.backup()` API, never a raw file copy, so
it's safe even while WAL-mode writers are live) of both DBs, gzipped,
60-day retention; a full D1 mirror of `platform.db` refreshed (wipe +
reinsert) every run, table order derived at runtime from
`PRAGMA foreign_key_list` (never a hand-maintained list that could drift
from `schema.sql`); Fernet-encrypted `.env`/`creds.txt` (PBKDF2-derived
key from a new `CF_BACKUP_ENCRYPTION_PASSPHRASE`, generated this session
and handed to Pranav to also save in a password manager — if only stored
next to the files it encrypts, it protects nothing once this PC is the
thing that's gone) with a real `--decrypt-secret` CLI path for actual
disaster recovery, not just one-way upload; and an MD5-vs-R2-ETag asset
sync for the live-served folders (`study_bot/`, `faculty/`, `exam_bot/`,
`myfiles_bot/uploads/`) that only uploads new/changed files and never
deletes a remote object based on local state. `assets/backup pdfs/`
(1.5GB, already documented elsewhere in this file as unused) is
deliberately excluded. On any phase failure, sends a DM via the same
`watcher_bot.py` sender/alerts.json plumbing already used for bot down/up
alerts — reused directly, not reimplemented. Deliberately NOT registered
in `bots.json`/`manage_bots.py` (a run-to-completion batch job, not a
long-running heartbeat process) — instead runs via a new Windows Task
Scheduler job, **"1LAVYA Platform Backup"**, nightly at 3:30 AM.

**Verified for real before trusting any of it**: bucket + D1 database
auto-created on first run; D1 mirror row counts cross-checked against
live `platform.db` query results (matched, including catching real
platform growth between two checks minutes apart — `course_catalog`,
static reference data, matched exactly at 975 both times, confirming the
mirror isn't just coincidentally close); the encrypted-secrets path proven
with an actual download-decrypt-read round trip (not just "upload
succeeded") via the script's own `--decrypt-secret` flag. Full first real
run: DB snapshots + secrets + D1 mirror in ~200s, asset sync separately.
Full detail, retention policy, and the disaster-recovery procedure:
`telegram/database/README.md`'s "Off-machine backup" section.
