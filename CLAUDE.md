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
| `books/strategy-book/` | **Pillar 1** — Exam Strategy book (general prep + author journey + exam-specific strategy). `drafts/ working/ final/` |
| `books/concept-book/` | **Pillar 2** — Advanced Accounts **Concept Book** (this IS the Adv-Accounts book): `chapter-zero/ characters/ chapters/ story-vignettes/ revision-material/` |
| `books/about-author/` | Shared author profile + journey (used by both books) |
| `syllabus-engine/` | **Pillar 3** — ICAI material → JSON/MD. `data/ scripts/ html-source/` |
| `question-bank/` | **Pillar 4** — non-study-material questions (7–10 yrs): `pyq/ mtp/ rtp/ solutions/` |
| `mcq-platform/` | **Pillar 5** — AI MCQs in a DBMS, Cloudflare online tests: `question-generation/ database/ cloudflare-app/` |
| `telegram/` | **Pillar 6** — study bots + their source docs: `bots/ source-docs/` |
| `content/` | Creative studio: `assets/` (raw-footage, intros-outros, green-screen, b-roll, music-sfx, brand-kit, thumbnails, flyers), `social/{personal,vc-gurukul}`, `calendar/`, `scripts/`, `motivation/`, `competitor-analysis/`, `ai-content-pipeline/`. See `content/README.md`. |
| `vc-gurukul/` | Institute side (NOT content brand): `management-discussions/ events/ batch-july-2025/ contracts/` |
| `materials/` | `icai-source/` (study material, PYQ/MTP/RTP — **gitignored/local**) + `reference/` (incl. `samples/`) |
| `obs-setup/` | Recording/streaming setup: `assets/` (OBS wallpapers), `recordings/` (output), `tools/` |
| `photo-gallery/` | `originals/` (gitignored) + `index.md` |
| `planning/` | Future planning: `future-roadmap.md`, `to-purchase.md`, `execution-notes.md` |
| `preparations/` | Personal prep notes, lecture plans |
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
