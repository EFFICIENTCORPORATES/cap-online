# cap-online — CA Inter Teaching Journey (VC Gurukul)

Master repository for **CA Pranav Pratik Tulshyan**'s CA Inter Advanced Accounting teaching ecosystem at VC Gurukul, Noida — books, syllabus engine, question bank, online practice platform, content, and recording setup.

> **Git root:** `D:\EffCorp_Projects\cap-online` · **Remote:** `EFFICIENTCORPORATES/cap-online` · **Branch:** `main`

---

## What we're building

| # | Pillar | Folder | What it is |
|---|--------|--------|-----------|
| 1 | **Exam Strategy Book** *(self-drafted)* | `books/strategy-book/` | General prep book + author's journey + exam-specific strategy. |
| 2 | **Concept Book — Advanced Accounts** *(self-drafted)* | `books/concept-book/` | All concepts for all chapters, with stories, characters, and space for error register + exam markings. *(This is the Advanced Accounts book.)* |
| 3 | **Syllabus Engine** | `syllabus-engine/` | Structural breakdown of the entire ICAI study material into JSON/MD so AI agents can navigate it and pull insights via scripts. |
| 4 | **Question Bank** | `question-bank/` | Curated collection of questions **not** in the ICAI study material — PYQ, MTP, RTP + solutions. Scope: last 7–10 years (depending on book size). |
| 5 | **AI MCQ / Online Test Platform** | `mcq-platform/` | AI-generated MCQ bank in a DBMS, hosted as a Cloudflare project. Students take tests online and get results. |
| 6 | **Telegram Bots** | `telegram/` | Study-centric bots and tools students use to augment study, practice, and exam prep. |

Supporting: `vc-gurukul/` (institute ops), `content/` (reels, motivation, competitor analysis), `obs-setup/`, `photo-gallery/`, `materials/` (ICAI source + reference), `preparations/`, `tools/`, and `_claude/` (Claude memory & context).

---

## How we work together

Each session:

1. Claude reads **`README.md`** + everything in **`_claude/memory/`** first — full context in seconds.
2. You say what we're working on.
3. Claude executes, updates files, and updates this README if the structure changes.
4. Session ends with a brief status note appended to **`_claude/memory/project_log.md`** (newest on top).

## Rules

- **Markdown (`.md`) by default** for all content and docs.
- **HTML** for books and slides.
- **No SVGs / diagrams** unless explicitly asked.
- **No binary files in git** — audio, video, images, office docs, archives, and executables are gitignored (see `.gitignore`). They live locally only.

---

## Folder map

```
cap-online/
├── README.md                  ← this file (master ToC + rules + how-to)
├── .gitignore                 ← excludes binaries (audio/video/images/docs/archives)
│
├── _claude/                   ← Claude session memory & recovered context
│   ├── memory/                ← memory files + project_log.md (session history)
│   ├── artifacts/             ← MD docs recovered from Claude projects
│   └── skills/                ← writing/voice skill files worth preserving
│
├── books/
│   ├── strategy-book/         ← Pillar 1: exam strategy (drafts/ working/ final/)
│   ├── concept-book/          ← Pillar 2: Advanced Accounts concept book
│   │   ├── chapter-zero/      ← Chapter 0 (Arjun / Pranav Bhaiya); EN + Hindi drafts
│   │   ├── characters/        ← recurring cast (Sethji, Rolly, Diya, CFO Sir…)
│   │   ├── chapters/          ← concept chapters
│   │   ├── story-vignettes/   ← error-point stories
│   │   └── revision-material/ ← revision + error-register / exam-marking space
│   └── about-author/          ← shared: author profile + journey (used by both books)
│
├── syllabus-engine/           ← Pillar 3: JSON/MD pipeline + extraction
│   ├── data/                  ← syllabus JSON + Excel weightage source
│   ├── scripts/               ← extract_json_from_html.py
│   └── html-source/           ← ICAI Base HTML chapters
│
├── question-bank/             ← Pillar 4: non-study-material questions (7–10 yr)
│   ├── pyq/  mtp/  rtp/        ← by source
│   └── solutions/
│
├── mcq-platform/              ← Pillar 5: AI MCQs in DBMS, Cloudflare online tests
│   ├── question-generation/   ← AI generation pipeline
│   ├── database/              ← schema, seed data
│   └── cloudflare-app/        ← hosted test app
│
├── telegram/                  ← Pillar 6: bots/ source-docs/
│
├── vc-gurukul/                ← management-discussions/ events/ batch-july-2025/
├── content/                   ← reels/ motivation/ competitor-analysis/
├── obs-setup/                 ← OBS config, scene notes, recording setup
├── photo-gallery/             ← originals/ (gitignored) + index.md
├── materials/                 ← icai-source/ (gitignored) + reference/ (incl. samples/)
├── preparations/              ← personal prep notes, lecture plans
│
└── tools/                     ← admin scripts + processing utilities
    ├── health_check.py · file_index.py · gitignore_audit.py
    └── split_pdf.py · count-line-pdf.py · sarvamai.py · translate_chapter0.py
```

---

## Where things are

| You want… | Look in |
|---|---|
| Exam strategy book | `books/strategy-book/` |
| Advanced Accounts concept book (Ch.0, characters, stories) | `books/concept-book/` |
| Author profile & journey | `books/about-author/` |
| Syllabus JSON / extraction scripts | `syllabus-engine/` |
| PYQ / MTP / RTP question bank + solutions | `question-bank/` |
| Online MCQ test platform | `mcq-platform/` |
| ICAI study material, raw PYQ/MTP/RTP PDFs | `materials/icai-source/` *(local only)* |
| Reference samples (e.g. law-faculty chapter sample) | `materials/reference/samples/` |
| Motivation images & content bank | `content/motivation/` |
| Recovered Claude project docs & skills | `_claude/artifacts/`, `_claude/skills/` |
| Session history | `_claude/memory/project_log.md` |

---

## ⚠️ Pending review (not yet migrated)

Mixed-content folders left in place pending your call:

- **`preparation-materials/animation-generate/`** — character bible, story flow, content pipeline. → likely `books/concept-book/` (characters/story-vignettes) and/or `content/`.
- **`preparation-materials/all in one exam strategy for all/`** — Audit Decoder Question Bank PDF. → `question-bank/` or `materials/reference/`.
- **`recording/`** — ApowerMirror binaries + live-batch MP4s (large, gitignored). → keep local, decide home (`obs-setup/`?).
- **`content/motivation/OBS Background IPCC.*`** — may belong in `obs-setup/`.

---

*Maintained with Claude (Cowork). Run `python tools/health_check.py` after structural changes.*
