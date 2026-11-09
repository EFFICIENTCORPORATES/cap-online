# Foundation topic master — versioned workbook data

Snapshot read directly from the [live Google Sheet](https://docs.google.com/spreadsheets/d/1a_faP38UZan5QSHDiZeRUnB4TxngHuPdwsAnGCbBMtE/edit) on **2026-10-20**. This is the Foundation topic workbook, not the separate PDF downloader workbook.

| Live tab | Versioned file | Data rows |
|---|---|---:|
| ICAI-SMAT-TOPIC_WISE | [topics.csv](topics.csv) | 229 |
| Unit Index | [units.csv](units.csv) | 33 |
| Chapter Summary | [chapters.csv](chapters.csv) | 11 |
| Resource Index | [resources.csv](resources.csv) | 132 |
| README | [sheet-readme.csv](sheet-readme.csv) | 25 |

[workbook-snapshot.json](workbook-snapshot.json) preserves tab names, column order and typed values from the connector's UNFORMATTED_VALUE read. Each tab has `columns` and a rectangular `rows` array. Missing trailing cells were normalized to empty strings. The CSVs contain the same values with UTF-8/LF and explicit quoting.

## Excel file and live refresh

The native workbook remains in Google Drive; File → Download → Microsoft Excel (.xlsx) exports all five tabs for local use. Per repository policy the binary `.xlsx` is not committed to Git. Agents have the complete tab values in CSV/JSON here, together with the source URL; styling/filter metadata is not reproduced in JSON. If a binary export must be archived in the asset system later, use the repository's R2 workflow and record its real manifest entry rather than inventing an asset key.

For a refresh: read metadata for the **exact Sheet ID above**, use the actual tab names and bounded populated ranges, retain topic/page text values, compare the new data to this snapshot, regenerate the CSV/JSON together and update the snapshot date/counts in one commit. These files are not an automatic synchronization service. Do not write a stale snapshot back over the live Sheet.

## Data contract

- `unique_topic_id` is the join key: e.g. `CA_L1_P01_M1_C1_U1_T1.10`. It includes level/paper/module/chapter/unit and the official numbered topic.
- `topic_no`, `page_number`, source-section start pages and summary/test pages are **strings**, never decimal measurements. `1.10` and `1.1` are different labels. In pandas use `dtype=str, keep_default_na=False`; with the stdlib use `csv.DictReader` and do not cast these fields.
- `chapter_no`, `module_no`, `unit_no` and count columns are numeric in the JSON snapshot. U0 means a standalone chapter with no numbered unit, not missing chapter coverage.
- `source_pdf_url` identifies the unit/chapter PDF. `toc_evidence_link` points to the physical PDF page of the Initial Pages contents; that viewer-page number is not the printed page number.
- The baseline is the **English May 2026-onward edition / August 2025 reprint**, not the separate May 2027 text.
- `importance_status = Not assessed` and blank `importance_evidence` preserve unfinished work. Do not turn blanks into zero historical marks or import the CA Inter reference rankings.
- `coverage_level` is numbered detailed-TOC headings. The next task is body-level concept expansion; the 229 rows are not a claim that all exceptions, examples or sub-concepts are separately represented.

The exact column meanings and original preparation notes are preserved in `sheet-readme.csv`. See [the agent handoff](../AGENT-HANDOFF.md) for pending inputs, suggested output schemas and acceptance criteria.

## Local validation

Run `python books/ca-foundation/topic-master/validate_snapshot.py` from the repo root. It checks all five CSVs against JSON, IDs/counts/page strings and the 41-lecture calendar. `snapshot-manifest.json` records SHA-256 values for the data snapshots; these are snapshot integrity records, not link-availability checks.
