# First prompt for the Concept Book agent (paste this as the first message of a new session)

_Written 2026-11-11. Maintained by whoever last changed the reading list: keep the paths current._

---

You are joining CA Pranav Pratik Tulshyan's CA Inter teaching ecosystem (`EFFICIENTCORPORATES/cap-online`) to help build the **Concept Book for all chapters of CA Inter Advanced Accounting**, using three kinds of source: the ICAI study material, Pranav's **lecture transcriptions**, and his **class notebooks**. Do not start writing any chapter yet. First read everything below in one go, then report back and ask.

## Step 0: get the right files
Everything is on `main` (merged 2026-11-11; the other branches are being deleted). Run `git pull origin main` first. If `books/ca-inter/teaching-notes/CONCEPT-BOOK-DESIGN-BRIEF.md` is missing, tell Pranav before going on. Never delete branches.

## Step 1: read, in this order (batch the reads, then summarise)
1. `CONTEXT.md`, then `CLAUDE.md` sections 1, 2, 2b and 7, then `docs/sessions/2026-11-09-teaching-material-handover.md` (Pranav's standing preferences are in its section 3), then `docs/BACKLOG.md` group **T** (especially BL-T14).
2. **`books/ca-inter/teaching-notes/CONCEPT-BOOK-DESIGN-BRIEF.md`** (the design decisions for this book: complementary to ICAI, no solved questions, question references after each concept with "what we learnt / what is new", **Error Register Points**, visual and step-wise algorithms, **linkages between concepts** as the main focus) and `books/ca-inter/teaching-notes/README.md`.
3. The Concept Book runbooks: `books/ca-inter/concept-book/CONCEPT_BOOK_NOTES_PIPELINE.md`, `NEWTON_CONCEPT_BOOK_PRODUCTION_GUIDE.md`, and `books/ca-inter/concept-book/notes_making/README.md` with its `conversion_manifest.json`.
4. Lecture transcription: `_claude/skills/SKILL-ca-lecture-transcription.md` (where the transcripts and audio live in R2, what is settled, what not to redo).
5. The quality bar already produced: `books/ca-inter/concept-book/chapters/` (`seq03-framework.md`, `seq04-as02-valuation-of-inventories.md` and `.html`), and the teaching notes `ch14-internal-reconstruction-traps.md`, `ch11-12-dividend-vs-buyback.md`, `ch09u2-ch13-amalgamation-traps.md`, `concept-clarifications.md`, plus the two diagrams in `books/ca-inter/teaching-notes/diagrams/`.
6. The skills `.claude/skills/chapter-illustration-traps/SKILL.md` and `concept-material-review/SKILL.md` (new project skills load only in a fresh session; if they do not appear, read the files directly).
7. The chapter map and topic/page index: `books/ca-inter/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json` (canonical topic numbers, names and pages for all 36 chapters) and `R2_MANIFEST.md` (large files are in R2, not missing).
8. The ICAI study material as Markdown with page markers: `books/ca-inter/smat-may-27-edition/all-modules/*_BEAUTIFIED.md` (July 2026 edition, May 2027 attempt). Page numbers are printed pages from the converted files, **not checked against the PDFs**.

## Step 2: facts you must not rediscover
- The **class notebooks NB01/NB02** are scanned handwriting with no text layer; the Drive connector returns an empty string. Never claim the teaching sequence is verified from them; use whatever OCR exists under `notes_making/ocr`, and otherwise ask Pranav for the order.
- Lecture audio and video are in R2 (see the transcription skill); a cloud session may lack R2 credentials. Say plainly what you could not read.
- Do not deploy, open a pull request or merge unless Pranav asks. The repo is public: no secrets or personal data in files or issues.
- Recompute every figure with a script in the scratchpad; mark every inference ("my reconstruction", "ICAI does not say"); do not invent what Pranav said in class.
- Rules from `CLAUDE.md`: no binary files in git, UTF-8 only, no SVG diagrams unless asked, run `python tools/health_check.py` after structural changes, and add a note to `_claude/memory/project_log.md` at the end.

## Step 3: what to report back (and nothing more yet)
1. **Inventory:** for each of the 36 chapters, what exists today (ICAI Markdown, lecture transcript, OCR of notes, teaching notes, existing concept-book draft) and what is missing. Mark anything you could not open.
2. **Your understanding in about ten lines:** what the Concept Book is and is not, the building block per concept, how Error Register Points and linkages work.
3. **A proposed build order and per-chapter workflow** (evidence gathering → teaching-note pass with `chapter-illustration-traps` → draft → review), and how you will combine the transcript, the notebook and ICAI without mixing their authority (ICAI is the source for rules and pages; the lecture and notebook give Pranav's sequence, examples and emphasis).
4. **Your questions for Pranav, one concise list:** which chapter to start with; where exactly the transcripts and notebook scans are and in what format; the chapter teaching order (NB01); the output format (Markdown first, then HTML?); and anything in the design brief that conflicts with the older production guide.

Then wait for Pranav's answers.
