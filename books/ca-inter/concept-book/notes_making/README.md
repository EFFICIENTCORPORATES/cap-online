# P01-NB-01B CONCEPT BOOK — Conversion & Reconstruction Log

## 1. What this package contains

This package is a reconstruction of the supplied CollaNote file:

`P01-NB-01B CONCEPT BOOK.cnote`

The goal was to preserve the original handwritten material while also producing editable, human-readable and media-friendly representations.

### Main outputs

- `pdf/01_Original_Handwritten.pdf` — 21-page PDF rendering of the notebook pages. The original page geometry and handwriting are retained as closely as possible.
- `pdf/02_Easy_Read_Notes.pdf` — a clean study-oriented summary arranged page-by-page.
- `excalidraw/notebook_all_pages.excalidraw.json` — non-binary JSON containing the recovered handwriting as Excalidraw-style `freedraw` vector elements.
- `excalidraw/page-XX.excalidraw.json` — one editable JSON file per notebook page.
- `excalidraw/notebook_editable_source.json` — a more explicit source representation containing page dimensions, strokes, points, widths and colours.
- `excalidraw/font_and_ocr_settings.json` — editable font/OCR/layout settings.
- `audio/01_Original_Audio.m4a` — audio extracted from the CollaNote package.
- `audio/01_Original_Audio.mp3` — MP3 version of the extracted recording.
- `audio/02_CollaNote_Transcript.json` — the timestamped transcript supplied inside the CollaNote metadata.
- `audio/03_Transcript_Timestamped.md` — human-readable transcript with timestamps.
- `video/03_Karaoke_Synced_Page_17.mp4` — audio + the relevant handwritten page with word-level karaoke highlighting.
- `ocr/raw_tesseract_output.txt` — diagnostic OCR output. It is intentionally not treated as authoritative because handwriting OCR is imperfect.
- `source/P01-NB-01B CONCEPT BOOK.cnote` — the original input file, retained for reproducibility.

---

## 2. Initial inspection of the `.cnote`

The uploaded file was inspected directly rather than treating `.cnote` as an ordinary PDF.

The file is a ZIP-style CollaNote package. Its contents included:

- `note without pdf.cnote` — JSON metadata.
- `0.cpage` through `20.cpage` — 21 page records.

Each `.cpage` is itself JSON. The handwriting is primarily stored in the `_dkDrawing` field as Base64-encoded binary drawing records.

The metadata also contained:

- notebook size: approximately `1050 × 1485` page units;
- 21 page records;
- one embedded audio recording;
- audio duration: approximately `132.7 seconds`;
- an embedded word-level transcript.

The CollaNote package therefore contained substantially more structure than a screenshot or flat PDF would preserve.

---

## 3. Important discovery: the handwriting is recoverable as vectors

A major part of the conversion was understanding `_dkDrawing`.

The drawing data is not plain JSON points. It is a Base64 representation of a protobuf-like binary structure. Each drawing record contains stroke records, and the stroke records contain points, style information, widths and colours.

A public open-source CollaNote-to-PDF converter was consulted as a format reference. Its documentation states that it supports newer CollaNote strokes stored in `_dkDrawing`, legacy strokes, embedded audio and attachments. The repository was used only as a technical reference for understanding the proprietary structure; the output files in this package were generated locally from the supplied notebook.

Reference project:
`alarsama/collanote_cnote_to_pdf_converter`

The important design decision was **not to flatten the handwriting immediately into raster images**. Instead, the stroke records were decoded into ordinary JSON objects containing point coordinates and style information.

---

## 4. Page reconstruction

The page sequence was reconstructed from the numbered `.cpage` files.

There are 21 page records:

- Pages 1–17 contain visible handwritten material.
- Pages 18–21 contain no meaningful strokes in the source package and are therefore essentially blank.

The first 16 populated pages are mainly accounting / financial-statement notes and worked examples. Page 17 introduces the DPDP Act and digital personal data. The embedded audio corresponds to that latter section.

The page geometry is retained at `1050 × 1485` units so that table lines, arrows, underlines, annotations and handwritten placement remain spatially faithful.

---

## 5. Excalidraw / non-binary JSON conversion

The requested approach was to use Excalidraw or an equivalent editable JSON representation instead of another opaque binary format.

The generated files use Excalidraw-compatible JSON concepts, particularly `freedraw` elements.

Each stroke contains information such as:

- `x`, `y`
- `width`, `height`
- `strokeColor`
- `strokeWidth`
- `opacity`
- `points`
- `angle`
- `roughness`
- element ID and version fields

This means the recovered handwriting is represented as ordinary JSON rather than as the original CollaNote binary drawing payload.

### Why Excalidraw was suitable

The original material is fundamentally vector handwriting. Excalidraw's freehand representation is therefore a natural interchange target: the handwriting can remain geometrically editable without requiring the original CollaNote binary encoder.

### Font handling

The original handwriting font cannot be reproduced as a normal font because it is not font glyph text — it is drawn strokes.

Therefore the package separates the concepts:

1. **Original handwriting:** preserved as vector freehand strokes.
2. **Editable text/font settings:** represented as JSON settings for future OCR/text reconstruction.

`font_and_ocr_settings.json` contains a changeable font family and font size rather than baking those choices into the source data.

---

## 6. Tables and diagrams

The notebook contains several tables and accounting T-accounts.

Rather than attempting to infer every table cell and immediately rebuilding it as a new typeset table, the original stroke coordinates were preserved. This is important because the vertical/horizontal lines, arrows, circled figures and annotations are part of the author's reasoning structure.

Consequently:

- table geometry is preserved in the Excalidraw vector data;
- the original PDF remains the authoritative visual copy;
- the Easy-Read PDF converts the conceptual material into normal text;
- exact numerical workings should be checked against the original handwritten PDF rather than against OCR.

This avoids a common conversion error where an OCR engine reads a number correctly but places it in the wrong row or column.

---

## 7. OCR processing

Tesseract OCR was run as a diagnostic step using a sparse-text configuration.

The result is included in:

`ocr/raw_tesseract_output.txt`

The OCR output contains recognizable words and many useful fragments, but handwritten accounting notation, abbreviations, arrows and numbers are not consistently recognized.

Therefore the OCR was **not** used as the sole source for reconstructing the final handwritten PDF or the vector representation.

The workflow deliberately treats OCR as an assistive layer rather than a source of truth.

---

## 8. Easy-to-read notes

A separate study PDF was produced from the visual contents of the notebook.

The notes are organized by source page and cover the major concepts appearing in the notebook, including:

- framework for financial statements;
- balance sheet;
- statement of profit and loss;
- cash flow statement;
- users of financial statements;
- fundamental accounting assumptions;
- going concern;
- comparative going-concern / non-going-concern treatment;
- worked accounting adjustments;
- accrual concept;
- consistency;
- qualitative characteristics;
- elements of financial statements;
- assets;
- liabilities and provisions;
- the DPDP Act / digital personal data.

The exact numerical tables remain in the original PDF because the handwriting contains dense accounting calculations where a false OCR correction would be worse than preserving the original.

---

## 9. Audio extraction

The notebook metadata contained an audio object with:

- duration: approximately 132.7 seconds;
- language code: `en-IN`;
- timestamped transcript segments;
- Base64-encoded audio data.

The Base64 audio payload was decoded into an `.m4a` file.

An MP3 derivative was also created for easier playback on systems that do not handle M4A as conveniently.

The transcript itself was preserved without replacing it with a newly invented transcript.

---

## 10. Karaoke-style synchronized video

The transcript includes timestamps for individual words/phrases. These timings were used to create an ASS subtitle track with karaoke timing tags.

The video therefore contains:

1. the relevant handwritten page;
2. the original recorded audio;
3. a transcript overlay;
4. word-level progressive highlighting following the embedded CollaNote timestamps.

The current audio is associated with the DPDP page, so the video uses that page as the visual background rather than pretending that the audio describes all 21 pages.

The resulting file is:

`video/03_Karaoke_Synced_Page_17.mp4`

An intermediate `karaoke.ass` subtitle file is also retained so the timing can be edited independently of the video.

---

## 11. Hurdles encountered

### Hurdle 1 — `.cnote` is not a PDF

The first conceptual trap was assuming that a CollaNote file could simply be renamed or opened as a PDF. It cannot. It is a structured package containing JSON, page records and encoded drawing data.

**Resolution:** inspect the ZIP structure first and parse the `.cpage` JSON records.

### Hurdle 2 — handwriting was inside `_dkDrawing`

The visible handwriting was not stored as normal text. It was encoded in Base64 binary drawing records.

**Resolution:** decode the Base64 data and parse the protobuf-like fields to recover strokes, points, colours, widths and highlighter information.

### Hurdle 3 — preserving tables

OCR alone cannot reliably preserve accounting tables because a number can be recognized but assigned to the wrong row or column.

**Resolution:** preserve the original vector geometry and create Excalidraw-style freedraw JSON. This retains table lines and spatial relationships.

### Hurdle 4 — OCR errors

Handwritten characters such as `P&L`, `PPE`, `P&L a/c`, `B/S`, numbers and arrows were frequently misread by OCR.

**Resolution:** keep OCR as a diagnostic layer and use the vector rendering as the authoritative page representation.

### Hurdle 5 — blank pages

There are 21 `.cpage` records but only 17 pages contain meaningful strokes.

**Resolution:** retain all 21 pages in the PDF and JSON package so page numbering stays faithful to the source.

### Hurdle 6 — audio does not cover the entire notebook

The embedded recording is only about 2 minutes 13 seconds and its transcript discusses the DPDP Act page rather than the complete accounting notebook.

**Resolution:** synchronize the video specifically to the page and transcript that the recording describes instead of artificially attaching the recording to unrelated pages.

### Hurdle 7 — proprietary format uncertainty

CollaNote's internal drawing representation is proprietary and can change between versions.

**Resolution:** use a best-effort decoder, retain the original `.cnote`, and preserve decoded intermediate JSON so the conversion can be re-run or improved later.

---

## 12. What was intentionally NOT changed

- The original `.cnote` was retained unchanged.
- The handwritten PDF is not an OCR-retyped replacement for the original.
- Original stroke positions were not rearranged.
- Numerical calculations were not silently “corrected”.
- The audio was not re-recorded or regenerated.
- The supplied CollaNote transcript timestamps were retained.

---

## 13. Reproducibility

The conversion was performed locally using standard command-line / Python tooling and the supplied file.

Major tools used:

- ZIP extraction / archive inspection
- Python
- JSON parsing
- custom binary/protobuf-like stroke decoding
- Pillow for page rendering
- ReportLab for PDF generation
- Tesseract OCR for diagnostic text extraction
- FFmpeg for audio conversion and MP4 generation

The original `.cnote` and decoded JSON are included so future conversion code can be applied without losing the source data.

---

## 14. Important limitation

This is a **best-effort reconstruction**, not an official CollaNote export.

The original CollaNote application remains the final authority for exact rendering behaviour. In particular, very subtle brush dynamics, pressure curves, proprietary blending behaviour and future-version DrawingKit records may not be reproduced pixel-for-pixel.

For normal study, however, the package preserves the important information in three complementary forms:

**Original visual appearance → editable vector JSON → easy-to-read study notes.**

---

## 15. Suggested use

For exact handwriting: use `01_Original_Handwritten.pdf`.

For studying: use `02_Easy_Read_Notes.pdf`.

For editing/reusing the handwriting: use the `excalidraw/` JSON files.

For listening: use either M4A or MP3.

For synchronized revision: use the karaoke MP4.

For auditing or improving the conversion: read this README, inspect `source/`, and use the JSON/OCR intermediates.
