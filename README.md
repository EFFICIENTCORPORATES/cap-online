# cap-online — CA Inter Teaching Journey (VC Gurukul)

Master repository for **CA Pranav Pratik Tulshyan**'s CA Inter Advanced Accounting teaching ecosystem at VC Gurukul, Noida — books, syllabus-engine pipeline, class materials, content, and recording setup.

> **Git root:** `D:\EffCorp_Projects\cap-online` · **Remote:** `EFFICIENTCORPORATES/cap-online` · **Branch:** `main`

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
│   ├── strategy-book/         ← 7-bucket exam strategy book   (drafts/ working/ final/)
│   ├── concept-book/          ← Chapter 0, Arjun/Pranav Bhaiya (chapter-zero/ characters/)
│   └── adv-accounts-book/     ← CA Inter Advanced Accounting textbook
│                                 (chapters/ story-vignettes/ revision-material/)
│
├── syllabus-engine/           ← JSON pipeline + Python extraction
│   ├── data/                  ← syllabus JSON + Excel weightage source
│   ├── scripts/               ← extract_json_from_html.py
│   └── html-source/           ← ICAI Base HTML chapters (e.g. AS2_Inventories.html)
│
├── vc-gurukul/                ← management-discussions/ events/ batch-july-2025/
│
├── content/
│   ├── reels/                 ← scripts, ideas, references (no video files)
│   ├── motivation/            ← content bank, quotes, story ideas, images
│   └── competitor-analysis/   ← research on other CA educators/platforms
│
├── telegram/                  ← bots/ source-docs/
├── obs-setup/                 ← OBS config, scene notes, recording setup
├── photo-gallery/             ← originals/ (gitignored) + index.md
├── materials/                 ← icai-source/ (gitignored) + reference/
├── preparations/              ← personal prep notes, lecture plans
│
└── tools/                     ← Python admin scripts + processing utilities
    ├── health_check.py        ← validates folder structure & README links
    ├── file_index.py          ← auto-generates a file listing
    ├── gitignore_audit.py     ← flags large/binary files not in .gitignore
    ├── split_pdf.py · count-line-pdf.py · sarvamai.py · translate_chapter0.py
```

---

## Where things are

| You want… | Look in |
|---|---|
| Exam strategy book (7 buckets) | `books/strategy-book/` |
| Concept book — Chapter 0, characters | `books/concept-book/` |
| Advanced Accounting textbook chapters | `books/adv-accounts-book/` |
| Syllabus JSON / extraction scripts | `syllabus-engine/` |
| ICAI study material, PYQ/MTP/RTP | `materials/icai-source/` *(local only)* |
| Motivation images & content bank | `content/motivation/` |
| Recovered Claude project docs & skills | `_claude/artifacts/`, `_claude/skills/` |
| Session history | `_claude/memory/project_log.md` |

---

## ⚠️ Pending review (not yet migrated)

These hold mixed content and were left in place pending your call:

- **`book/`** — mixed: a Law chapter (Nature of Contracts, *out of Adv-Accounts scope*), `about-author/`, `chap-0/` (concept-book Chapter 0 + Hindi), `strategy-all-in-one/`, concept bank, TOC, writing skill. → likely splits across `books/concept-book/`, `books/strategy-book/`, `_claude/skills/`.
- **`preparation-materials/animation-generate/`** — character bible, story flow, content pipeline. → `books/adv-accounts-book/` or `content/`.
- **`preparation-materials/all in one exam strategy for all/`** — Audit Decoder Question Bank. → `materials/reference/` or `books/strategy-book/`.
- **`recording/`** — ApowerMirror binaries + live-batch MP4s (large). → keep local, decide home.
- **`content/motivation/OBS Background IPCC.*`** — may belong in `obs-setup/`.

---

*Maintained with Claude (Cowork). Run `python tools/health_check.py` after structural changes.*
