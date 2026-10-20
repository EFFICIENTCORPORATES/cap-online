# CA Foundation Paper 1 — ICAI materials workflow

Download official ICAI Accounting PDFs into a shallow local archive, preserve their source links, and optionally convert them to Markdown using the repository's existing offline converter.

## Start here

- **Other agents: start with [AGENT-HANDOFF.md](AGENT-HANDOFF.md).** It records the concept-book goal, live sources, completed work, limits and next required inputs.
- [Foundation topic master snapshots](topic-master/README.md): all five live Sheet tabs, topic/page IDs, CSV and typed JSON (read 2026-10-20).
- [Teaching flow and time allocations](TEACHING-PLAN.md) and [date-wise proposal](teaching-plan.csv): 41 lectures / 61.5 hours; not a locked beginner-course promise.

- [Live inventory and downloader plan](https://docs.google.com/spreadsheets/d/1FxNpBF5_CI2FVw2lQ7a3w8r8AchIFzcJdlVOB7Gjy7A/edit#gid=104001): download the **entire workbook** through File → Download → Microsoft Excel (.xlsx). Keep the tab named `Downloader Master` unchanged.
- [Python downloader](download_icai_pdfs.py): Python 3.10+, with `openpyxl` as its only third-party dependency.
- [Full downloader specification](DOWNLOADER-SPEC.md): naming, dates, languages, resume/logging behavior and instructions for future AI agents.
- [PDF-to-Markdown converter](../../tools/icai_pdf_to_md_converter.py): existing shared tool; operates locally after dependencies are installed.

The scope is CA Foundation / historical CPT **Accounting only**, including study material, syllabus, Saransh, RTP, MTP, examination questions, suggested answers and relevant updates. Official ICAI sources only; no material older than the original 15-year cutoff of 2011-10-04 was requested. Source entry points:

- https://www.icai.org/post/new-scheme-of-education-and-training
- https://www.icai.org/post/sm-foundation-paper1

## 1. Install and validate the plan

From the repository root in Windows PowerShell:

```powershell
py -m pip install -r books/ca-foundation/requirements-downloader.txt
py books/ca-foundation/download_icai_pdfs.py --excel "C:\Users\YourName\Downloads\inventory.xlsx" --output "D:\Local_CACSCMA_RAG_Master" --dry-run
```

Replace `YourName` and the Excel filename with the actual downloaded path. `inventory.xlsx` is a convenient local name, not a different online file. The destination is configurable; the supplied path is Pranav's preferred root.

## 2. Download and rename

```powershell
py books/ca-foundation/download_icai_pdfs.py --excel "C:\Users\YourName\Downloads\inventory.xlsx" --output "D:\Local_CACSCMA_RAG_Master"
```

Alternatively run `py books/ca-foundation/download_icai_pdfs.py` without arguments and enter the two paths at the prompts. No Google credentials are needed: the script reads the exported Excel file.

The input tab has exactly four required columns:

| Column | Meaning |
|---|---|
| `download_enabled` | Download TRUE rows; skip FALSE rows. |
| `download_url` | Direct source PDF URL. |
| `relative_folder` | Child folder under the selected local root. |
| `filename` | Exact final filename, including `.pdf`. |

Only three direct child folders are used: `Study material`, `Question bank`, and `Reference`. Modules/chapters/units are represented in filenames rather than deeper folders. All MTP, RTP, exam papers and suggested answers share `Question bank`.

The downloader validates unique destinations, rejects unsafe paths, streams each file to `.pdf.part`, checks its PDF signature, then renames it. It retries up to three attempts by default, skips existing PDFs with a recognizable signature, and appends outcomes to `download_log.csv` in the output root. This is a signature check, not a full PDF integrity or content audit. Run only one downloader per destination at a time.

Rerun the same command to resume. Exit codes: `0` = no download failures (or successful dry run), `1` = at least one download failed, `2` = input/setup error, `130` = interrupted. Optional flags: `--attempts 3`, `--timeout 60`, `--delay 0.5`, `--dry-run`. Stop with Ctrl+C; completed PDFs remain available.

## Short filename rules

Study example: `CA_L1_P01_M1_C1_U5_AccPolicies_F23_E202605_EN.pdf`.

| Token | Meaning |
|---|---|
| `CA_L1_P01` | Chartered Accountancy, Foundation level, Paper 1 Accounting |
| `M1_C1_U5` | Module 1, Chapter 1, Unit 5 |
| `U0` | No unit: use the chapter title instead of a unit title |
| `C0`, `M0` | Chapter/module not specified, e.g. front matter |
| `F23`, `F17`, `CPT` | Scheme identifier |
| `E202605` | Earliest stated applicability, May 2026; not publication date |
| `EN`, `HI` | English / Hindi |

When a unit exists, the topic suffix includes only the abbreviated unit name. Topics are capped at 28 characters. Examples: `Acc` = Accounting, `Reco` = Reconciliation, `Stat` = Statement. Edition and language suffixes prevent different versions from overwriting each other.

Question-bank example: `CA_L1_P01_MTP_2025_01_S2_An_EN.pdf`.

- Types: `MTP`, `RTP`, `EXAM`, `SA` (Suggested Answers).
- Parts: `Q` = Questions; `An` = Answers; `QnA` = both (RTP and Suggested Answers by the requested convention); `Corr` = separate corrigendum.
- `S1`/`S2` = stated series/set; `S0` = unknown or not applicable. Do not invent a set number.
- `0000_00` = date unknown. `_V2` distinguishes distinct PDFs with otherwise identical names; it does not claim an official revision.
- MTP dates follow the recorded PDF mock month or archive label, not an inferred exam attempt. See the full specification for details.

## 3. Optional PDF → Markdown conversion

The existing [converter](../../tools/icai_pdf_to_md_converter.py) needs a separate dependency:

```powershell
py -m pip install "markitdown[pdf]"
py tools/icai_pdf_to_md_converter.py
```

In its GUI, choose `D:\Local_CACSCMA_RAG_Master` and start conversion. It recursively discovers PDFs and writes `.md` **beside each PDF with the same base name**, with UTF-8/LF normalization. Existing Markdown is skipped by default. Tkinter is required for the GUI (normally included with standard Windows Python).

For a headless run from the repository root:

```powershell
py -c "from tools.icai_pdf_to_md_converter import run_batch; print(run_batch(r'D:\Local_CACSCMA_RAG_Master'))"
```

Inspect the conversion log as well as the return counts: missing dependencies produce a FATAL message and zero counts. Conversion uses local MarkItDown/pdfminer text extraction; scanned pages may need OCR, and tables, formulas and reading order need manual review. This step does not produce the structured retrieval corpus automatically. Existing `icai-smaterials-md/` and `CA_Foundation_Offline_Retrieval_Engine_SMAT/` remain separate downstream workspaces; do not overwrite their curated files with raw conversions.

## 4. Manual upload and Git boundaries

Review `download_log.csv`, retry failures, and upload the three local folders to Google Drive manually. Downloading does not upload anything or trigger conversion. This repository stores code, documentation and text inventories; Excel/PDF files stay local or in Drive under the repository's no-binary policy. No credentials are stored here.

## Inventory snapshot and coverage

The `inventory/` CSVs were read from the live Google Sheet on **2026-10-17 UTC (2026-10-18 India)**:

- [downloader-master.csv](inventory/downloader-master.csv): 331 rows, 330 enabled, one disabled broken link; exact four-column downloader plan.
- [source-inventory.csv](inventory/source-inventory.csv): full titles, provenance URLs, original metadata and verification notes. Join to the downloader plan on `download_url`.
- [coverage.csv](inventory/coverage.csv): known archive gaps and exclusions.

These are versioned text snapshots, not a live sync. **The Python script accepts `.xlsx`, not CSV.** Use the current Google Sheet export for execution. Its `Downloader Master` tab overrides the old paths in `Inventory` and `Folder Map`; those older columns are preserved for provenance only. Do not use them for downloads.

The original link checks were on **2026-10-04** (330 PDF-signature checks; one 404 disabled), not on the snapshot date. Availability can change. The archive is not exhaustive: older CPT/Foundation editions and full MTP series remain partly unlocated. Combined multi-subject model papers/weightage files were excluded from Accounting-only automatic downloads.

## Status and next steps

Completed: inventory, short naming plan, shallow folder plan, runnable downloader, local downloader tests and documentation linking the existing converter. The downloader already existed here when this documentation was added. A completed full download/manual Drive upload for this 331-row plan has not been confirmed in this session. Existing curated Markdown/retrieval work is not evidence that every inventory row was downloaded.

Next: export the workbook, dry-run, download locally, review failures, manually upload; optionally convert and inspect PDFs. Later work can fill documented archive gaps. Do not expand this archive to other papers/levels without an explicit scope change.
