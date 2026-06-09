# content/ — Creative Studio

Everything related to **creatives and brand-building** — for Pranav's personal brand and for VC Gurukul — that is *not* book or syllabus content. This is the marketing/content side of the project.

## Structure

```
content/
├── assets/              ← shared raw ingredients (reused across everything)
│   ├── raw-footage/     ← phone shoots dropped here for the editing team
│   ├── intros-outros/
│   ├── green-screen/
│   ├── b-roll/          ← base clips, e.g. "Claude Cowork in Action.mp4"
│   ├── music-sfx/
│   ├── brand-kit/       ← logos, fonts, colours, templates (personal + VCG)
│   ├── thumbnails/      ← YouTube thumbnails
│   └── flyers/          ← YouTube / promo flyers
├── social/              ← finished / in-progress output, split by brand
│   ├── personal/        ← Pranav's ENTIRELY personal reels (NOT collaborated with VC Gurukul)
│   └── vc-gurukul/      ← posts shared by Pranav + VC Gurukul (co-branded / collaborative)
├── calendar/            ← content calendars (planning + progress)
│   ├── personal-private.md   ← private; personal brand only
│   └── vc-gurukul-shared.md  ← shared with the institute/editing team
├── scripts/
│   └── gsheet_sync.py   ← pull/push the calendar to/from a shared Google Sheet
├── motivation/          ← student-motivation creatives (quotes, wallpapers, reels, articles)
├── competitor-analysis/ ← research on other CA educators / platforms
└── ai-content-pipeline/ ← AI content-generation method + tool stack (animation = Excalidraw)
```

## Conventions

**The pipeline.** Shoot on phone → footage drops into `assets/raw-footage/` (organised by shoot date or name) → editing team cuts it → the finished reel lands in `social/personal/` or `social/vc-gurukul/`. Reusable polished pieces (intros, outros, green-screen, b-roll, music, brand kit, thumbnail/flyer templates) live in `assets/` and get pulled into many edits.

**Brand split (important).**
- `social/personal/` — content that is *entirely Pranav's own*, with no VC Gurukul collaboration. Planned in `calendar/personal-private.md` (private).
- `social/vc-gurukul/` — posts that are *shared by Pranav + VC Gurukul* (co-branded). Planned in `calendar/vc-gurukul-shared.md` (shared with the team). Note this is the content brand; institute operations, events, and legal contracts live in the top-level `vc-gurukul/` folder, which is a different thing.

**Calendars & collaboration.** The two calendars track what content is in the pipeline and its progress (`idea → scripting → shot → editing → scheduled → posted`). `scripts/gsheet_sync.py` keeps them in sync with a shared Google Sheet so the editing team can collaborate, while the repo keeps a versioned Markdown copy.

**Git & storage.** All media here is binary (video/images) and is gitignored — git tracks only the *scripts, calendars, ideas, and indexes* you write alongside the media, never the media itself. Keep an `ideas.md` (or `index.md`) in each output folder so planning stays in version control while the files stay local. Raw footage is the heaviest and most disposable; strongly consider keeping it on an external drive / cloud and letting the repo hold only the recipe and finished compressed exports.
