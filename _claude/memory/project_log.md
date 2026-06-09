# Project Log — cap-online

A running status note. Newest entries at the top. One short block per session.

---

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