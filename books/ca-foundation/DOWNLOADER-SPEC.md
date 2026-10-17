# Downloader specification

Preserved from the Google Sheet README tab on 2026-10-17 UTC (2026-10-18 in India). The runnable script is [download_icai_pdfs.py](download_icai_pdfs.py).

## Purpose

Read Downloader Master only. Other tabs retain the detailed source inventory and original folder plan; do not use their filenames or folders for downloads.

## Local root

D:\Local_CACSCMA_RAG_Master

## Input

Download this Google Sheet as Microsoft Excel (.xlsx). Python: pandas.read_excel(workbook_path, sheet_name='Downloader Master') or openpyxl.

## Required columns

download_enabled, download_url, relative_folder, filename. Each row represents one source PDF.

## Enabled flag

Only download TRUE rows. Accept Excel booleans and case-insensitive text TRUE. FALSE means skip; one known 404 is disabled.

## Destination

Windows Path(base_root) / relative_folder / filename. Create the parent folder with parents=True, exist_ok=True. Use the supplied filename exactly; do not derive it from the URL.

## Folders

Only three direct child folders: Study material; Question bank; Reference. No module/chapter/unit subfolders.

## Study naming

CA_L1_P01_M{module}_C{chapter}_U{unit}_{short_topic}_{scheme}_E{YYYYMM}_{language}.pdf

## Study example

CA_L1_P01_M1_C1_U5_AccPolicies_F23_E202605_EN.pdf

## Units and chapters

With a unit: short_topic contains only its unit title. Without a unit: U0 and the abbreviated chapter title. Front matter/annexures use C0_U0 and their document title. M0 means module not specified.

## CA / L1 / P01

CA = Chartered Accountancy; L1 = Foundation level; P01 = Paper 1 Accounting. Historical CPT Accounting is normalized under this archive prefix and identified by CPT in the scheme suffix.

## Edition and scheme

F23 = Foundation 2023 scheme; F17 = Foundation 2017 scheme; CPT = historical CPT. EYYYYMM uses the earliest applicability month stated in Inventory; it is not the publication date. One file may cover multiple exam attempts.

## Language

EN = English, HI = Hindi. Language and edition suffixes prevent overwriting alternate editions/translations. Hindi RTP identified by the official hm source page is marked HI here.

## Question bank naming

CA_L1_P01_{type}_{YYYY}_{MM}_S{set}_{part}_{language}.pdf

## Question bank example

CA_L1_P01_MTP_2025_01_S2_An_EN.pdf

## Question bank types

MTP = Mock Test Paper; RTP = Revision Test Paper; EXAM = Examination Question Paper; SA = Suggested Answers. All go into Question bank.

## Q / An / QnA / Corr

Q = Questions; An = Answers; QnA = combined questions and answers (RTP and Suggested Answers per requested convention); Corr = separate corrigendum, not a question/answer paper.

## Set number

S1/S2 uses a stated Series I/II. S0 means unknown or not applicable; do not invent a set number. RTP, EXAM and SA normally use S0.

## Year and month

RTP uses the attempt in its official source page URL. MTP uses the existing verified date label (PDF mock month where noted, otherwise archive attempt label). EXAM/SA use their exam attempt. 0000_00 means no reliable date; never substitute today's date.

## Reference naming

CA_L1_P01_{SYL|SUM|UPD}_{YYYY}_{MM}_{short_topic}_{scheme}_{language}.pdf. SYL = Syllabus; SUM = Saransh; UPD = Updates/corrigenda.

## Short names

Topic text is abbreviated and capped at 28 characters. Your ambiguous 'more than 0 characters' was treated as a typo; 28 is a practical default. Names are descriptive labels, not authoritative document titles.

## Key abbreviations

Acc = Accounting/Accounts; Reco = Reconciliation; Stat = Statement; Cap = Capital; Rev = Revenue; Exp = Expenditures; Rcpt = Receipts; Cont = Contingent; Liab = Liabilities; Dep = Depreciation; Amort = Amortisation; Part = Partnership; Mfg = Manufacturing; Fin = Financial; Inv = Inventories.

## Other abbreviations

Theory = Theoretical; Frame = Framework; Val = Valuation; Princ = Principles; Est = Estimates; Conv = Conventions; Proc = Procedures; Jrnl = Journal; Rect = Rectification; Err = Errors; Subs = Subsidiary; Prep = Preparation; Prop = Proprietors; Intro = Introduction; Treat = Treatment; Retire = Retirement; Diss = Dissolution; Co = Company; Forfeit = Forfeiture; Org = Organisations; Incomp = Incomplete; Rec = Records; Terms = Terminology; Gloss = Glossary.

## Uniqueness

Case-insensitive relative_folder + filename must be unique. _V2 suffix separates a second distinct PDF with the same date/type/language. This suffix is an inventory discriminator, not proof of an official revision.

## Source lookup

Join Downloader Master.download_url to Inventory.download_url for full titles, applicability, provenance, verification and notes. Preserve this URL relationship when editing.

## HTTP downloading

Use requests.Session with timeout, streaming, limited retries and a modest delay. Follow redirects. Require successful HTTP status and PDF %PDF- signature before accepting the file; never save an HTML error page as PDF.

## Safe saving

Write to filename.pdf.part, validate, then atomically rename to the final filename. Do not overwrite a valid existing PDF. Remove or retry failed partial downloads. Ensure resolved destination stays inside base_root.

## Download log

Keep a local CSV/JSON log with URL, final path, outcome, HTTP status and error. Continue past failures. Show totals for downloaded, already present, skipped and failed.

## Optional resume

Before skipping existing files, check nonzero size and PDF signature. Retry corrupt files. This input tab is a plan, not a live download-status table.

## Known limits

330 enabled PDF URLs, 1 disabled broken link; 331 total rows. Earlier archives and full MTP series remain incomplete; see Coverage. Link verification is from 2026-10-04 and cannot guarantee future availability.

## Manual Drive upload

After local downloading, manually upload the three child folders to your chosen Google Drive destination. No Drive credentials or upload automation are needed.

## AI coding brief

Build a Windows-compatible Python CLI that reads the four-column Downloader Master tab from the downloaded .xlsx; uses the local root above; downloads only enabled URLs; uses exact supplied names and folders; validates PDFs; resumes safely; retries and logs failures. Do not reconstruct filenames from metadata or use the old Inventory folder plan.
