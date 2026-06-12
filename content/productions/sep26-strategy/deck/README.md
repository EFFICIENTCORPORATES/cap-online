# Sep-26 Strategy Video — HTML Slide Deck

HTML/CSS/JS presentation for the YouTube video **"CA Inter Sep 2026: Exactly What To Do In The Next 40 Days"**.
Built from `books/strategy-book/working/video-brief-sep26-strategy.md` (run-of-show + slide treatments).

**Status:** COMPLETE — all 27 slides built (Phases 1–4). Pending: Pranav's full wording review (all on-screen text is editable in the `js/slides*.js` files).

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
| **R** | reset the Subject Slider Board markers to start positions |

On the **Subject Slider Board** (slide 7): drag any marker with the mouse, or tap anywhere on a bar to jump the marker there. When all 6 subjects cross the B4 line, the **LEVEL 1 CLEARED** badge pops.

## Files

| File | What it is |
|---|---|
| `index.html` | Shell — loads fonts, CSS, JS |
| `css/theme.css` | Design tokens: brand blue/green (DISC), bucket colours, dark/light themes, slide chrome (bilingual header, footer journey strip, watermark), reveal animations |
| `css/slides.css` | Layouts for slides 0–5 (Shlok → Bucket Analysis) |
| `css/parts.css` | Layouts for slides 6–26 (slider board → CTA) + booti tracker |
| `js/slides.js` | **Slide content, part 1** (slides 0–5) + `EXAM_DATE` / `B4_DATE` constants |
| `js/slides-part2.js` | Content: Slider Board · Mission · Roadmap (6–8) |
| `js/slides-part3.js` | Content: Bucket 3 — North Star → 15 July deadline (9–21) |
| `js/slides-part4.js` | Content: Bucket 4 · Bucket 0 · CTA (22–26) |
| `js/engine.js` | Slide engine — navigation, reveals, chrome, themes |
| `js/engine-extras.js` | Interactivity — draggable sliders, booti footer tracker, mock-deadline date |

**To change any on-screen wording:** edit the `js/slides*.js` files — plain text inside each slide's `html` block. Never need to touch engine or CSS for wording.

## Notes

- **All dates are live-computed** from `EXAM_DATE = '2026-09-01'`: the hook number (days to exam), the header chip, days-to-15-July on the Mission slide, and the mock deadline (exam − 10 days = 22 AUG). Record any day — everything stays correct.
- Fonts (Archivo, Source Sans 3, Noto Serif Devanagari) load from Google Fonts — needs internet on first load.
- Dark theme = emotional moments (Shlok, hook, North Star, Bootis, 15 July, CTA); light = content slides.
- Brand: blue (logical) + green (friendly) chrome per DISC; bucket colours match `design/design-spec.md`; gold reserved for Bootis.
