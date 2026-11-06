# Kahaani deck: Reconstruction, Amalgamation and Consolidation

`kahaani-restructuring-map.html` is the finished, self-contained deck (no network needed). It is **generated**: edit `src/` and rebuild.

```bash
python3 deck/build_deck.py          # builds the HTML and slides-manifest.json; warns about any click that does nothing
python3 deck/check_notes_sync.py    # checks ../outline/SPEAKER-NOTES.md against the deck (slide ids and step counts)
```

| Path | What |
|---|---|
| `src/style.css`, `src/style-2.css` | Brand tokens, components, print stylesheet (CApranav.com watermark) |
| `src/app.js` | Step engine, contents panel, keyboard, Print / Save PDF |
| `src/slides-1.html` ... `slides-5.html` | The 31 slides |
| `build_deck.py` | Joins the parts, adds the brand label to every slide, writes the manifest |

**Step engine.** An element with `data-at="n"` appears at click n (`data-until="m"` hides it again at m). `data-st="n:state|m:state2"` sets a `data-state` attribute (CSS reacts), `data-txt="n:text|m:text2"` swaps the text. Separator is `|`.

**Speaker notes are never in the HTML.** They live in `../outline/SPEAKER-NOTES.md`.

**Keys:** Space / → next, ← back, T contents, P print, F full screen. **Print:** Print / Save PDF button, "Background graphics" on, Landscape, Margins None.

A PDF is not committed (binary files stay out of git); make one with the Print button when needed.
