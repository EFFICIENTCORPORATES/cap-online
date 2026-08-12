# `telegram/branding/` — the 1LAVYA brand kit

**Phase 1** of the 2026-08-10 roadmap: **Branding Kit → Report Pipeline →
Leaderboard → Admin Portal**. Each phase is built, smoke-tested, documented,
then handed off for manual confirmation before the next one starts — this
phase is done and ready for that manual check.

> **Operational gotcha, learned the hard way (2026-08-11):** editing
> `dashboard_html.py` or `brand_kit.py` does **not** take effect on the live
> dashboard until `1lavya-dashboard` is restarted — Python doesn't hot-reload
> changed source, and the first time this happened, Pranav saw no branding
> at all on `http://127.0.0.1:8787/` because the running process predated
> the edit. **After any change to either file, always run:**
> `python telegram/tools/manage_bots.py restart 1lavya-dashboard`
> `smoke_test_brand_kit.py`'s Step 7 now catches this automatically (checks
> the LIVE `:8787` endpoint, not just the static file, and compares the
> process's own start time against both files' mtimes) — but don't rely on
> remembering to run the smoke test either; just restart after every edit.

## What this is for

**Every 1LAVYA-authored, student/admin-facing HTML page or PDF this
platform generates should look consistently branded** — the admin
dashboard, and (starting Phase 2) reports sent to students. **Never** used
on faculty-branded bot output — per Pranav's existing, explicit rule (see
`study_hub_bot.py`/`exam_hub_bot.py`'s own "Powered by 1LAVYA" footer scope
notes), a faculty's bot carries no 1LAVYA branding at all. This kit is for
1LAVYA's *own* surfaces only.

## Files

| File | What it is |
|---|---|
| `build_brand_kit.py` | Generator script. Reads `telegram/1LAVYA_LOGO.jpeg` and produces everything below. **Re-run this if the source logo ever changes** — never hand-edit an output file. |
| `assets/1lavya_logo_transparent.png` | Full-res (1254×1254), white background removed via a feathered alpha ramp (not a hard cutout — see the script's own comment). ~800KB — one-per-document use only (a cover page), never embedded in a repeating header/footer. |
| `assets/1lavya_logo_header_128.png` | 128px pre-sized thumbnail, ~13KB. Default for page headers. |
| `assets/1lavya_logo_footer_48.png` | 48px pre-sized thumbnail, ~3KB. For small footer marks. |
| `assets/1lavya_logo_original.jpg` | Plain copy of the source JPEG, kept alongside the derived assets. |
| `brand_colors.json` | The two dominant brand colors, **extracted from the logo's own pixels** (hue-bucketed, not eyeballed) — `navy` (`#09284b`) and `gold` (`#d0942c`), plus two fixed light tints and an `ink` body-text color. Single source of truth — a color changes here once. |
| `brand_kit.py` | The module everything else imports. `colors()`, `logo_data_uri(variant)`, `render_header_html(title, subtitle=None)`, `render_footer_html()`, `brand_css_vars()`. |
| `smoke_test_brand_kit.py` | Re-run any time the kit changes, before trusting it again. See below. |

## Why the markup looks the way it does

`render_header_html()`/`render_footer_html()` use **table-based, inline-style
markup only — no flexbox, no grid, no CSS gradients, no `em`-unit
letter-spacing**. This isn't a stylistic choice, it's a hard constraint:
the exact same markup has to render correctly in **two different engines**
with very different CSS support —

1. A real browser (the admin dashboard).
2. `xhtml2pdf`/`reportlab` (Phase 2's report PDFs, and already the engine
   `exam_hub_bot.py`'s `html_to_pdf_bytes()` uses for question PDFs today).

The smoke test caught a real instance of this during Phase 1:
`letter-spacing: 0.02em` rendered fine in a browser, but reportlab's
`getSize()` can't parse the `em` unit — it silently *dropped* the rule
(not a crash, `pisa`'s own error count stayed at 0) rather than raising.
Only an actual render-and-inspect pass caught it, not a "did it throw"
check. Fixed by removing `em`-based letter-spacing; `smoke_test_brand_kit.py`
now has a permanent step guarding against this exact regression class.

## Running the smoke test

```
python telegram/branding/smoke_test_brand_kit.py
```

Seven steps, each printing PASS/FAIL per check, non-zero exit on any failure:

1. Every asset file `build_brand_kit.py` is supposed to produce exists.
2. `brand_colors.json` parses and every color is valid `#rrggbb` hex.
3. Every `logo_data_uri()` variant round-trips through base64 back into a
   real, valid PNG (not corrupt).
4. `render_header_html()`/`render_footer_html()`/`brand_css_vars()` all
   produce non-empty markup containing the expected brand elements.
5. Regenerates the **real** `dashboard.html` (the actual live surface this
   phase wired branding into), confirms the wordmark and an embedded logo
   data URI are present, and takes a real screenshot via headless Edge
   (`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`) —
   written to `assets/_smoke_test_screenshot.png`. Per CLAUDE.md section 7's
   own rule ("never trust a layout fix by reading the code alone — verify
   with a screenshot"), **open that screenshot** (or have Claude's `Read`
   tool view it) before calling this visually confirmed — passing
   structural checks alone isn't enough, a lesson relearned the hard way
   more than once in this same session on the content-pipeline side.
6. Renders the same header/footer markup through the real `xhtml2pdf`
   engine and checks for `pisa`'s own error count AND any silently-dropped
   CSS values (the `letter-spacing` class of bug above) — a structural
   "0 errors" from `pisa` alone is not sufficient, same lesson as step 5.
7. **Fetches the actual live `:8787` server** (not just the static file)
   and confirms branding is really being served, THEN compares the live
   process's own recorded start time against `dashboard_html.py`/
   `brand_kit.py`'s mtimes — a process older than the source is flagged as
   needing a restart. Added 2026-08-11 after exactly that gap let a real
   deployment miss slip past every other check (see the operational-gotcha
   note at the top of this file).

## Using the kit in new code

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[N] / "telegram" / "branding"))
import brand_kit

html = f"""<html><body>
{brand_kit.render_header_html("My Report", "Optional subtitle")}
... your content ...
{brand_kit.render_footer_html()}
</body></html>"""
```

For a page that wants CSS custom properties instead (a real-browser-only
context, e.g. more of the dashboard's own styling), use
`brand_kit.brand_css_vars()` and reference `var(--1lavya-navy)` etc. — but
never inside `render_header_html()`/`render_footer_html()` themselves,
which must stay `xhtml2pdf`-safe.

## What's deliberately not built yet

- A dark-background/reversed (light wordmark) logo variant — the current
  transparent PNG is suited to light backgrounds only (the dashboard and
  planned reports are both light-background by convention). Add one only
  if a real dark-themed surface actually needs it later.
- SVG output — the source logo is a raster JPEG with photographic-style
  gradients/shading (not flat vector shapes), so a faithful SVG would need
  actual vector redrawing, not a mechanical raster→SVG trace. Not
  attempted; the PNG-based kit above covers every real use case identified
  so far (embed as `<img>`/data URI, works in both target rendering
  engines). Revisit only if a genuine need for true vector output appears.
