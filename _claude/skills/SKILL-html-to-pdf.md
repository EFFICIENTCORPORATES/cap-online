# SKILL — HTML to PDF Conversion

> **Scope:** Converting any HTML file to a multi-page PDF on this machine (Windows 11).
> Use this skill whenever a task requires generating a PDF from an HTML source — presentations,
> reports, books, or any structured document. This skill covers both the automated path
> (Chrome headless) and the manual fallback, along with what the source HTML must look like
> to produce a clean PDF.

---

## 1. The Two-Stage Workflow

Every HTML-to-PDF job has two stages:

**Stage A — Prepare the print HTML.**
The source HTML must be adapted (or purpose-built) for print. Interactive features
(JavaScript click-advance, animations, hover states, hidden elements) do not work in
headless rendering. All content must be fully visible in the static DOM.

**Stage B — Render to PDF.**
Use Chrome headless to render the print HTML and output a PDF file. Chrome is the only
reliable tool on this machine that correctly handles dark backgrounds, gradients, CSS Grid,
CSS variables, and modern layout — alternatives like wkhtmltopdf or WeasyPrint drop a lot
of these.

Do both stages. Skipping Stage A and feeding the interactive HTML directly to Chrome
will produce a PDF with most content invisible (because `.beat { opacity: 0 }` and similar
hidden-state rules are not cleared by headless rendering).

---

## 2. Stage A — Preparing the Print HTML

### 2.1 Create a separate print file

Always create a **separate static HTML file** for printing. Do not modify the interactive
source. Naming convention used in this project:

```
source file:  filename.html           ← interactive (presentations, etc.)
print file:   filename-print.html     ← static, PDF-ready
output PDF:   filename.pdf            ← final output
```

Place all three in the same folder.

### 2.2 Required CSS — must be present in the `<head>` of the print file

```css
/* 1. Force all backgrounds, gradients, and colours to print exactly as specified */
*, *::before, *::after {
  print-color-adjust: exact !important;
  -webkit-print-color-adjust: exact !important;
  box-sizing: border-box;
}

/* 2. Set page dimensions and remove browser margins */
@page {
  size: A4 landscape;   /* or: A4 portrait | A3 landscape | 297mm 167mm (16:9) etc. */
  margin: 0;
}

html, body {
  margin: 0;
  padding: 0;
  background: <your-background-colour>;
  font-family: <your-font-stack>;
}
```

### 2.3 Slide/page sizing — one page per `div`

Each page of the PDF corresponds to one HTML element (a slide, a section, a chapter).
Use **mm-based dimensions** to match the `@page` size exactly:

```css
/* For A4 landscape (297mm × 210mm) */
.slide {
  width: 297mm;
  height: 210mm;
  padding: 16mm 26mm;       /* adjust to taste */
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;

  /* PAGE BREAK — both rules for cross-browser compatibility */
  break-after: page;
  page-break-after: always;
}

/* Prevent an empty blank page after the last slide */
.slide:last-child {
  break-after: avoid;
  page-break-after: avoid;
}
```

Common `@page` size values:
```
A4 portrait:    size: A4;                   → 210mm × 297mm
A4 landscape:   size: A4 landscape;         → 297mm × 210mm
16:9 slide:     size: 338mm 190mm;          → matches 16:9 widescreen
Custom:         size: 297mm 167mm;          → 16:9 at A4 width
```

### 2.4 Typography — use pt (points) not px for print

Pixel sizes are screen-relative and can produce inconsistent results across print
resolutions. Use `pt` for all font sizes in a print HTML:

```
Rough conversion guide:
  px  →  pt
  6   →  4.5
  8   →  6
  10  →  7.5
  12  →  9
  14  →  10.5
  16  →  12
  18  →  13.5
  20  →  15
  24  →  18
  32  →  24
  48  →  36
  64  →  48
```

### 2.5 Make all content visible — clear interactive states

If adapting from an animated/interactive HTML (presentations, slides with beat reveals):

```css
/* Make every hidden/animated element fully visible */
.beat, .hidden, [data-hidden], .slide:not(.active) {
  opacity: 1 !important;
  transform: none !important;
  visibility: visible !important;
  display: flex !important;   /* or block / grid — match the original display type */
}

/* Show ALL slides, not just the active one */
.slide {
  display: flex !important;   /* override JS-set display:none */
}
```

Remove all JavaScript from the print file. It is not needed and can interfere with
headless rendering timing.

### 2.6 Gradients, shadows, and backgrounds

These all work correctly in Chrome headless when `print-color-adjust: exact` is set.
No special treatment needed. Background colours on `<body>`, `<div>`, `<section>` all print.

`text-shadow`, `box-shadow`, `border-radius`, CSS Grid, Flexbox, CSS variables (`var(--x)`) —
all supported correctly.

### 2.7 Images and embedded fonts

- **Images** must be local files or data URIs. Remote URLs (http/https) will not load in
  headless mode unless the machine has internet access at generation time.
- **Web fonts** (Google Fonts etc.) similarly require internet. Use system fonts for
  offline-safe output: `'Segoe UI', system-ui, -apple-system, sans-serif`.
- **SVGs** inline in HTML render correctly.

---

## 3. Stage B — Generating the PDF with Chrome Headless

### 3.1 Chrome paths on this machine (Windows 11)

Both have been confirmed present:
```
C:\Program Files (x86)\Google\Chrome\Application\chrome.exe   ← PRIMARY (use this first)
C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe  ← FALLBACK
```

If neither exists at those paths, search:
```powershell
Get-ChildItem "C:\Program Files*" -Recurse -Filter "chrome.exe" -ErrorAction SilentlyContinue |
  Select-Object -First 3 -ExpandProperty FullName
```

### 3.2 The exact PowerShell command

```powershell
$chrome  = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
$htmlIn  = "file:///D:/path/to/your-file-print.html"   # must be file:/// URL, not a path
$pdfOut  = "D:\path\to\your-file.pdf"                  # absolute Windows path is fine

& $chrome `
  --headless=new `
  --disable-gpu `
  --no-sandbox `
  --no-first-run `
  --disable-extensions `
  --print-to-pdf="$pdfOut" `
  --no-margins `
  --print-to-pdf-no-header `
  $htmlIn

Start-Sleep -Seconds 4   # wait for Chrome to finish writing the file
```

**Flag reference:**

| Flag | Why |
|------|-----|
| `--headless=new` | Modern headless renderer (Chrome 112+). More accurate CSS rendering than old headless. |
| `--disable-gpu` | Prevents GPU-related crashes in headless mode. |
| `--no-sandbox` | Required in some Windows environments to prevent sandbox init errors. |
| `--no-first-run` | Skips the "welcome to Chrome" setup that can block headless execution. |
| `--disable-extensions` | Prevents any installed extensions from interfering. |
| `--print-to-pdf="path"` | The absolute path to write the PDF. Use double quotes around path. |
| `--no-margins` | Overrides any OS-level print margin defaults. The `@page { margin: 0; }` CSS handles margins. |
| `--print-to-pdf-no-header` | Removes Chrome's default "filename + URL + date + page number" header/footer. |

### 3.3 Converting the HTML path to a `file:///` URL

```powershell
# Input: Windows path
$winPath = "D:\EffCorp_Projects\cap-online\books\strategy-book\working\file-print.html"

# Convert to file:/// URL (replace backslashes with forward slashes)
$fileUrl = "file:///" + $winPath.Replace("\", "/")
# Result: file:///D:/EffCorp_Projects/cap-online/books/strategy-book/working/file-print.html
```

### 3.4 Using Edge as fallback

Same flags work identically with Edge:
```powershell
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
& $edge --headless=new --disable-gpu --no-sandbox --no-first-run --disable-extensions `
  --print-to-pdf="$pdfOut" --no-margins --print-to-pdf-no-header $htmlIn
```

### 3.5 Page size control

The PDF page size is controlled entirely by the `@page { size: ... }` CSS rule in the HTML.
Chrome headless respects it. You do **not** need to pass a page size flag to Chrome.

If you need a specific size not set in the HTML, you cannot override it from the CLI —
you must edit the CSS.

---

## 4. Verification

### 4.1 Check the PDF was created and is non-empty

```powershell
if (Test-Path $pdfOut) {
  $bytes = (Get-Item $pdfOut).Length
  Write-Host "PDF created: $bytes bytes"
  if ($bytes -lt 5000) { Write-Host "WARNING: file is suspiciously small — may be empty/corrupt" }
} else {
  Write-Host "ERROR: PDF not found — Chrome may have failed silently"
}
```

### 4.2 Count the pages using Python

```powershell
python -c "
import re, sys
path = r'$pdfOut'
with open(path, 'rb') as f:
    data = f.read().decode('latin-1', errors='replace')
pages = len(re.findall(r'/Type\s*/Page[^s]', data))
print(f'Page count: {pages}')
"
```

Expected output: `Page count: 7` (or however many slides/sections are in the HTML).

If the page count is wrong (e.g., 1 instead of 7), the most common cause is that the
`break-after: page` CSS was not applied — see section 2.3.

### 4.3 Open the PDF to visually confirm

```powershell
Start-Process $pdfOut
```

This opens the PDF in the system default viewer (usually Edge PDF or Adobe Reader on Windows).

---

## 5. Common Problems and Fixes

### Problem: PDF is created but has 1 page instead of N

**Cause:** `break-after: page` is not triggering. Usually one of:
- The `.slide` elements have `display: none` (from the interactive JS) — fix: set
  `display: flex !important` in the print CSS.
- The height is set in `vh` units — these don't work in headless. Fix: convert to `mm`.
- The `@page` rule is missing — without it, Chrome uses its default A4 sizing, and
  your `height: 210mm` elements may overflow or be clipped.

### Problem: Backgrounds are white / dark backgrounds missing

**Cause:** `print-color-adjust: exact` is missing or not inherited.

**Fix:** Add this to the top of `<style>`:
```css
*, *::before, *::after {
  print-color-adjust: exact !important;
  -webkit-print-color-adjust: exact !important;
}
```

### Problem: Content is cut off / overflows the page

**Cause:** Font sizes or element dimensions are too large for the mm-based page.
The `overflow: hidden` on `.slide` hides the overflow in the PDF cleanly, but the content
is simply not visible.

**Fix:** Reduce font sizes (use `pt` units, see conversion table in 2.4), reduce padding,
or check that no child element has a fixed height larger than the slide height.

### Problem: Chrome hangs / no output

**Cause:** Chrome process started but did not complete before the script checked for output.

**Fix:** Increase the sleep duration from 4 to 8 seconds:
```powershell
Start-Sleep -Seconds 8
```

Or check if a stale Chrome process is blocking:
```powershell
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Problem: `--headless=new` gives an error

**Cause:** Older Chrome version (pre-112) does not support the `--headless=new` flag.

**Fix:** Use `--headless` (old form) instead:
```powershell
# Replace --headless=new with:
--headless
```

### Problem: Emoji or special characters missing in PDF

**Cause:** System fonts may not have the full emoji range.

**Fix:** For critical text, replace emoji with Unicode symbols or text labels.
Emoji in decorative contexts (slide titles, etc.) usually render fine on Windows 11.

### Problem: File path has spaces — Chrome gives an error

**Fix:** Always wrap the `--print-to-pdf` value in double quotes:
```powershell
--print-to-pdf="C:\path with spaces\output.pdf"
```

---

## 6. Full Worked Example

Below is the complete PowerShell block used successfully in this project
(June 2026, Windows 11, Chrome 126):

```powershell
$chrome = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
$htmlIn = "file:///D:/EffCorp_Projects/cap-online/books/strategy-book/working/exam-strategyFoundation-print.html"
$pdfOut = "D:\EffCorp_Projects\cap-online\books\strategy-book\working\exam-strategyFoundation.pdf"

& $chrome `
  --headless=new `
  --disable-gpu `
  --no-sandbox `
  --no-first-run `
  --disable-extensions `
  --print-to-pdf="$pdfOut" `
  --no-margins `
  --print-to-pdf-no-header `
  $htmlIn

Start-Sleep -Seconds 4

if (Test-Path $pdfOut) {
  $bytes = (Get-Item $pdfOut).Length
  Write-Host "PDF created: $bytes bytes"
} else {
  Write-Host "PDF generation failed"
}

# Verify page count
python -c "
import re
with open(r'$pdfOut', 'rb') as f:
    data = f.read().decode('latin-1', errors='replace')
pages = len(re.findall(r'/Type\s*/Page[^s]', data))
print(f'Pages: {pages}')
"
```

**Result:** `exam-strategyFoundation.pdf` — 7 pages, 150 KB, A4 landscape,
dark background fully preserved, all slide content visible.

---

## 7. Print HTML Checklist — Before Running Chrome

Use this checklist before running Chrome headless. Every item must be true.

- [ ] Separate `*-print.html` file created (not the interactive source)
- [ ] All `.beat`, `.hidden`, `.slide:not(.active)` overridden to `display` and `opacity: 1`
- [ ] All JavaScript removed or confirmed harmless in static context
- [ ] `@page { size: ...; margin: 0; }` present
- [ ] `print-color-adjust: exact !important` on `*`
- [ ] Slide dimensions in `mm` matching the `@page` size
- [ ] `break-after: page` and `page-break-after: always` on each slide element
- [ ] `break-after: avoid` on the last slide element only
- [ ] No remote image or font URLs (or confirmed internet access is available)
- [ ] File path converted to `file:///` URL format for the Chrome command

---

## 8. Manual Fallback (No CLI Access)

If Chrome headless is not accessible via the command line, the PDF can be generated
manually:

1. Open `filename-print.html` in Chrome (double-click the file, or drag into Chrome).
2. Press `Ctrl + P` to open the Print dialog.
3. Set **Destination** to: `Save as PDF`.
4. Set **Layout** to: `Landscape` (if the slides are landscape).
5. Set **Paper size** to: `A4` (or match the `@page` size in the CSS).
6. Set **Margins** to: `None`.
7. Expand **More settings** and enable: `Background graphics` ✓
   (This is the critical step — without it, dark backgrounds print white.)
8. Click **Save** and choose the output path.

This produces an identical PDF to the headless method.

---

*Skill written: 2026-06-21. Verified on: Windows 11 Pro, Chrome 126, Python 3.x.*
*Source: exam-strategyFoundation workflow — June 2026.*
