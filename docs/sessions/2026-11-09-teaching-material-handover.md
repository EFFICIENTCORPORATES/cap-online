# 2026-11-09 Handover: teaching material, Kahaani decks, chapter aids

**Read this first if you are a new AI agent asked to continue Pranav's teaching-material work.** Start at `CONTEXT.md`, then this file, then `docs/BACKLOG.md` group **T** (the to-do list with ids). The tracking issue is **GitHub issue #4** (https://github.com/EFFICIENTCORPORATES/cap-online/issues/4), also backlog row BL-T00.

**All of this work is on `main`** (merged 2026-11-09 on Pranav's instruction; `main` is the single trunk and the other branches are being deleted). If a file is missing, `git pull origin main` first.

## 1. Who and what

Pranav (CA Pranav Pratik Tulshyan) teaches CA Inter Advanced Accounting. In this stretch he is preparing lectures for the **Reconstruction, Amalgamation, Consolidation block** and then the **Buyback and Dividend** topics. He asks short, concrete questions and expects short, concrete answers grounded in the ICAI study material. He decides scope and wording.

## 2. What was built or written (all committed on the branch)

| What | Where | State |
|---|---|---|
| **Kahaani lecture 1 deck** ("Reconstruction, Amalgamation and Consolidation: the map before the maths"): 31 slides, one self-contained HTML | `content/productions/restructuring-lecture-1/deck/` (sources in `src/`, `build_deck.py`, `check_notes_sync.py`, `README.md`) | Built, reviewed by Pranav (all 31 slides "perfectly fine"). A zip was given to him. |
| Speaker notes (separate from the HTML, never embedded), ICAI references, design record | `content/productions/restructuring-lecture-1/outline/` (`SPEAKER-NOTES.md`, `REFERENCES.md`, `FLOW.md`) | Done; notes checked against the deck by `check_notes_sync.py` |
| **Kahaani area for capranav.com** (index + deck page), sync tool, SEO and legal registration, sitemap | `capranav_com_revamped/public/kahaani/`, `tools/sync_kahaani.py`, `PROJECT-LOG.md` (2026-11-06 entry) | **Prepared, NOT deployed** |
| Two reusable skills | `.claude/skills/chapter-illustration-traps/`, `.claude/skills/concept-material-review/`, index `_claude/skills/SKILL-chapter-review-skills.md` | Written; helper scripts tested; skills not yet invoked through the Skill tool |
| Teaching notes (illustration traps, TYK new items, concept answers) | `books/ca-inter/teaching-notes/` | Ch 14 done; Ch 11/12 illustrations done, TYK pending |
| AS 26 revision sheet review | `_claude/skills/SKILL-chapter-review-skills.md` §4 | Review only; the sheet is **unchanged** |

## 3. How Pranav likes the work done (standing preferences, learned this session)

- **Ask, do not assume.** One concise question when something is unclear; otherwise proceed with a stated default. His message may be cut off (one ended at "Please give"): say so and ask.
- **Intro lectures are concept-level:** what it is, where it sits, how it relates; no journal entries or solving. Every major concept at least mentioned.
- **Decks:** HTML, click-through animation, **capranav.com look** (tokens from `capranav_com_revamped/public/practice-with-pranav-bhaiya/slides/*.html`); **speaker notes in a separate Markdown file, never in the HTML**; Print / Save PDF with a **CApranav.com** watermark; he reviews every slide.
- **Balance sheet in T-format: Equity & Liabilities on the LEFT, Assets on the RIGHT.**
- **Timing examples: always 9 : 3, never 6 : 6** (acquisition on 1 January in a 1 April - 31 March year).
- **One running story:** Arjun's company (net assets), then **Arjun Ltd (target) and Bhim Ltd (investor)** for associate, subsidiary, minority interest.
- **Consolidated cash flow statement is outside the syllabus.**
- **When he teaches a chapter by solving illustrations:** he wants, per illustration, the **main tricky point**; for TYK, only questions and adjustments that are **new** (not in any illustration). The `chapter-illustration-traps` skill encodes this.
- **Page numbers:** he confirmed the Kahaani references against the PDFs; other chapters' page numbers come from the converted Markdown and are unchecked.
- **Deployment is his, later.** Never deploy or open a pull request unless he asks.

## 4. Facts about sources and tools (so you do not rediscover them)

- **ICAI study material (July 2026 edition, May 2027 attempt)** as Markdown with per-page markers: `books/ca-inter/smat-may-27-edition/all-modules/*_BEAUTIFIED.md` (machine-structured, not visually validated). A rawer copy: `books/ca-inter/concept-book/raw_icai_study_materials/`. The PDFs are not in the repo (R2 needs credentials a cloud session lacks; Pranav can attach PDFs in chat and the Read tool can open them by page range).
- **Teacher class notes NB01 / NB02** are in Google Drive as **scanned handwriting with no text layer**; reading NB01 through the Drive connector returns an empty string. Never claim the teaching order was verified; ask Pranav for it.
- **A cloud session cannot deploy** capranav.com (no Cloudflare credentials). **Never deploy from a fresh clone or worktree**: images and binaries are gitignored, so Worker Assets would replace the live files without them. Deploy from the checkout that has them (`capranav_com_revamped/PROJECT-LOG.md`, 2026-11-06).
- **Skills are read at session start**; new project skills appear only in a new session that has the files.
- **The repo is public** (BL-R01): put no secrets or personal data in files or issues.
- Playwright and headless Chromium are pre-installed in cloud sessions; use them to check any layout from screenshots, not from code.
- Shell quirk seen this session: long heredocs with Python in a single command were sometimes blocked by a safety check; write scripts to files and run them.

## 5. Defects and oddities found in the source material (not fixed; for teaching awareness or a later register)

- Pranav's roadmap PDFs (v4/v5): AS 21 topic numbers 1.15 - 1.17 are sub-sections of ICAI topic 1.14 (pages are right). See `content/productions/restructuring-lecture-1/outline/REFERENCES.md` §D.
- Ch 12 text p12.3 words the share-outstanding test as 25% of "paid-up capital and free reserves"; summary and illustrations use shares outstanding / equity capital.
- Ch 12 Illustration 5 labels rupee figures "crores". Illustration 4 leaves revenue reserve at (1.80).
- Ch 11 TYK Q15 answer prints "/5" for a three-year average.
- Ch 14 MCQ 5 answer says "Court"; the text says "Tribunal". Illustration 3 nets the bank overdraft with no explanation; Illustration 8 does not.
- Committed `capranav_com_revamped/public/faq/index.html` lacks the SEO head block that `tools/apply_seo_meta.py` adds.
- Pranav's local branch `docs/concept-book-storylines` was not visible to cloud sessions; if it holds concept-book work it needs pushing.
- Drive holds an older `as-26.html` (Sept) next to the repo's October `AS26_Intangible_Assets_15min_Revision_Handwritten.html`.

## 6. To-do list (ids are in `docs/BACKLOG.md` group T; the issue mirrors this list)

**P1**
- [ ] **BL-T01 (Pranav)** Merge branch `claude/sweet-brahmagupta-5yu98q` into `main` (open a pull request when he asks) so `CONTEXT.md`, the skills, notes and deck are visible to every new session.
- [ ] **BL-T02 (Pranav)** Deploy the Kahaani area to capranav.com from the checkout that has the site images; then `qa_smoke.py --browser` and `indexnow_ping.py`.
- [ ] **BL-T05 (Both)** Buyback and Dividend teaching deliverable: ask Pranav which format (Kahaani-style deck with the two calculations animated side by side / Markdown teaching note / traps only). Content already exists in `books/ca-inter/teaching-notes/ch11-12-dividend-vs-buyback.md`.

**P2**
- [ ] **BL-T04 (Agent)** Run `/chapter-illustration-traps` for the **Chapter 12 TYK** and the dividend-related **Chapter 11 TYK** (MCQ 5, 8, 9; Q15 Z Ltd): list only what is new; append to `ch11-12-dividend-vs-buyback.md`.
- [ ] **BL-T06 (Both)** AS 26 revision sheet: fix the revaluation error and add the missing items (list in the skill index §4), if Pranav says go; decide which Drive version is current.
- [ ] **BL-T08 (Agent)** Next Kahaani decks (e.g. Internal Reconstruction, Amalgamation) following the `restructuring-lecture-1` pattern (sources, build script, notes-sync check, references, sync tool). Ask first which chapter.
- [ ] **BL-T10 (Agent)** In a fresh session, confirm the two skills load (`/chapter-illustration-traps`, `/concept-material-review`); if not, check `.claude/skills/<name>/SKILL.md` frontmatter.
- [ ] **BL-T13 (Pranav)** Push or merge the local branch `docs/concept-book-storylines` if it holds concept-book work.

**P3**
- [ ] **BL-T03 (Pranav)** Decide whether the site navigation gets a Kahaani link.
- [ ] **BL-T07 (Pranav)** Give the chapter order from NB01 for any chapter whose concept sheet must be checked for teaching sequence.
- [ ] **BL-T09 (Agent)** Verify every real-world example before it is used in a deck (Vistara merged into Air India in Nov 2024; check Titan, SBI, Walmart-Flipkart, Tata Digital-BigBasket, Tata Motors-JLR).
- [ ] **BL-T11 (Agent)** Turn the source-material oddities in §5 into a register if Pranav wants them tracked.
- [ ] **BL-T12 (Agent)** Decide about the FAQ page's missing SEO block (re-run the SEO tool before the next deploy).

## 7. First message to give a new agent

> Read `CONTEXT.md`, then `docs/sessions/2026-11-09-teaching-material-handover.md`, then `docs/BACKLOG.md` group T. Everything is on `main`. Ask me which item to do next; do not deploy or open a pull request unless I say so.

## 8. The single-trunk merge (2026-11-09)

Pranav asked that everything go into `main` so he can delete every other branch. Result:

| Branch | What it held | Outcome |
|---|---|---|
| `claude/sweet-brahmagupta-5yu98q` | Kahaani deck, website pages, skills, notes, handover (6 commits) | Merged into `main` |
| `docs/foundation-topic-master-handoff-20261020` | CA Foundation topic-master workbook snapshot and agent handoff (18 files) | Merged into `main` (one conflict, `_claude/memory/project_log.md`: both sets of entries kept) |
| `chore/r2-manifest-2026-10-18` | An early 10-line `R2_MANIFEST.md` | Recorded as merged but its content not taken: `main`'s `R2_MANIFEST.md` is newer and already lists both of its entries |
| `docs/as26-revision-html`, `docs/concept-book-notes-pipeline` | Nothing beyond `main` (already merged) | Nothing to do |
| **Pranav's LOCAL branch `docs/concept-book-storylines`** | Unknown. It was **never on GitHub**, so no agent could see or merge it | **Not merged.** Before deleting it, check `git log main..docs/concept-book-storylines` on his machine and push or merge anything it has (BL-T13) |
