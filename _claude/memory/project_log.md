# Project Log — cap-online

A running status note. Newest entries at the top. One short block per session.

---

## 2026-06-09 — Repo restructure (Session: setup)

- Connected root folder `D:\EffCorp_Projects\cap-online` (git root, remote: EFFICIENTCORPORATES/cap-online, branch `main`).
- Built the full agreed folder skeleton (books, syllabus-engine, vc-gurukul, content, telegram, obs-setup, photo-gallery, materials, preparations, tools, _claude).
- Migrated unambiguous folders:
  - `motivation/` → `content/motivation/`
  - `scripts/` → `tools/` (count-line-pdf, sarvamai, split_pdf, translate_chapter0)
  - `preparation-materials/book-syllabus-engine/` → split into `syllabus-engine/` (scripts, data, html-source, architecture docs) and `materials/icai-source/` (ICAI study materials, AS2 source PDF, PYQ/MTP/RTP).
- Copied Claude project artifacts into `_claude/` (memory ×2, 5 SKILL files + writing skill → skills/, 7 docs → artifacts/).
- Wrote master `README.md`, extended `.gitignore` (video/audio/archives/executables/large binaries), created `tools/` admin scripts.
- Committed locally (not pushed).

**Left in place for review (mixed content — needs your call):**
- `book/` — contains a Law chapter (Nature of Contracts, out of Adv-Accounts scope), `about-author/`, `chap-0/` (concept-book Chapter 0 + Hindi), `strategy-all-in-one/`, `chapter-zero-concept-bank.md`, `table-of-contents.md`, `write-like...skill.md`.
- `preparation-materials/animation-generate/` — character bible, story flow, content pipeline, tool stack (could go to books/adv-accounts-book or content/).
- `preparation-materials/all in one exam strategy for all/` — Audit Decoder Question Bank PDF.
- `recording/` — ApowerMirror app binaries + live-batch MP4s (large binaries; suggest gitignore + decide home: obs-setup or external).
- `content/motivation/` includes `OBS Background IPCC.*` — may belong in `obs-setup/`.
