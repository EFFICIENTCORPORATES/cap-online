# Sep-26 Strategy Video — HTML Slide Deck

HTML/CSS/JS presentation for the YouTube video **"CA Inter Sep 2026: Exactly What To Do In The Next 40 Days"**.
Built from `books/strategy-book/working/video-brief-sep26-strategy.md` (run-of-show + slide treatments).

**Status:** First 3 slides built (Hook · Pain Mirror · Positioning) — awaiting Pranav's look-and-feel approval before the remaining 15 slides.

## How to present

1. Open `index.html` in Chrome (double-click — no server needed).
2. Press **F** (or F11) for fullscreen.
3. Advance with **→ / Space / click**. One press = one reveal.

For OBS: add a **Browser Source**, point it at `index.html`, set 1920×1080.

| Key | Action |
|---|---|
| → / Space / click | next reveal step, then next slide |
| ← | undo step, then previous slide |
| Home / End | first / last slide |
| F | fullscreen |
| H | hide/show the corner HUD (slide + step counter) |

## Files

| File | What it is |
|---|---|
| `index.html` | Shell — loads fonts, CSS, JS |
| `css/theme.css` | Design tokens (B3 amber `#E8A13D`, B4 orange `#E07A2F`, dark/light themes), stage scaling, reveal animations |
| `css/slides.css` | Per-slide layouts |
| `js/slides.js` | **All slide content — edit text here** |
| `js/engine.js` | Slide engine — navigation, reveals, theme switching (don't edit for content changes) |

## Notes

- **The "83" is live** — `js/slides.js` sets `EXAM_DATE = '2026-09-01'`; the hook number is computed on load, so it's correct on whichever day the video is recorded.
- Fonts (Archivo, Source Sans 3) load from Google Fonts — needs internet on first load.
- Dark theme = emotional moments (hook, Booti reveals, 25th July, CTA); light theme = content slides.
