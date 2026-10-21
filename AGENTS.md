# AGENTS.md — Operating Guide for the cap-online repo

<!-- EC-STANDARD:START (managed by EFFICIENTCORPORATES/ec-asset-index tools/gen_docs.py - edit there, not here) -->
## EC operating guide (read this before doing anything in this repo)

_Generated 2026-10-20 from `EFFICIENTCORPORATES/ec-asset-index`. If anything here is wrong, fix `products.json` / the generator there, then re-run `tools/gen_docs.py`._

### 1. What this repo is
- **Repo:** `EFFICIENTCORPORATES/cap-online` (default branch `main`), private GitHub.
- **Product:** `capranav` - CA Pranav - teaching persona
- **Entity:** PRANAV PRATIK TULSHYAN (proprietorship)
- **Domain list (Google Tasks):** 5 - CA Pranav - VCG & Advanced Accounts | **Manager designation:** `capranav-product-manager` (principal NOT created yet - ask Pranav to create it before you need credentials) | **Owner:** pranav (interim)
- **Domains (Cloudflare):** `capranav.com`
- **Detected stack:** Python (requirements.txt); static HTML
- **Top-level layout:** `.claude/`, `.tmp_artifact/`, `AGENTS.md`, `CLAUDE.md`, `Claude_V2.md`, `R2_MANIFEST.md`, `README.md`, `TELEGRAM-TEST-MODE-SYSTEM.md`, `_claude/`, `books/`, `capranav_com/`, `capranav_com_revamped/`, `content/`, `final-deliverables/`, `first_run/`, `index.html`, `materials/`, `mcq-platform/`, `obs-setup/`, `planning/`, `preparations/`, `requirements.txt`, `scratch_new_batches.txt`, `student-toolkit/`, `telegram/`

### 2. Other repos you may need (clone what the task touches)
- Registry and tools (always useful): `gh repo clone EFFICIENTCORPORATES/ec-asset-index` -> `ASSET_INDEX.json` (repo -> R2), `products.json` (all products/entities), `ENTITIES.md`, `DOMAINS.md`, `GOVERNANCE.md`, `ASSET_WORKFLOW.md`, `tools/ec_assets.py`.
- Tech shared services: `EFFICIENTCORPORATES/credential-agent` (tokens/secrets), `EFFICIENTCORPORATES/task-hub` (GitHub issues/delivery), `EFFICIENTCORPORATES/personal-assistant` (Google Tasks/Calendar, brand-entity map).
- Other repos of this product (`capranav`):
  - `EFFICIENTCORPORATES/CAPranav_Website`
  - `EFFICIENTCORPORATES/cap-offline`
- Clone everything of a product in one go: see `ec-asset-index/ASSET_WORKFLOW.md` (`ec_assets.py pull <repo>` clones a repo and downloads its R2 files).

### 3. Large and binary files (Cloudflare R2) - do not say a file is "missing" before checking
- Bucket **`ec-cap-online-assets`** (private; Cloudflare account `68e19e5bed11326478a23d6e2ad31453`): 63 indexed files, 2.68 GB, plus 1 AES-256 encrypted archive(s) of local-only small files.
- Full list with key, size and sha256: **`R2_MANIFEST.md`** in this repo, and `ec-asset-index/ASSET_INDEX.json`.
- Download everything for this repo, sha256-verified (from a clone of `ec-asset-index`):
  ```bash
  pip install boto3
  python ec-asset-index/tools/ec_assets.py --agent pull cap-online --dest <this-repo-folder-or-its-parent>
  ```
  (`--agent` needs a principal allowed to issue Cloudflare tokens; otherwise set `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` issued for you by Pranav. Never paste keys into chat or commit them.)
- New or changed file >= 5 MB: never commit it. `ec_assets.py scan <repo-path>` then `ec_assets.py --agent push <repo-path> --all`, commit the updated `R2_MANIFEST.md`. Install the guard once per clone: copy `ec-asset-index/tools/pre-push-large-files.sh` to `.git/hooks/pre-push`.
- Local-only small files (ignored/untracked): `ec_assets.py --agent backup-local <repo-path>` / `restore-local`. Passphrase is in Bitwarden (`EC_BACKUP__PROD__ARCHIVE_PASSPHRASE`).

### 4. Secrets - how you get them (never from chat, never into git)
- Secrets live in **Bitwarden Secrets Manager**, named `<REPO>__<ENV>__<VARIABLE>` (this repo's prefix: `CAP_ONLINE__`, ENV = `PROD`/`DEV`/`LOCAL`/`SHARED`). Only secret **names** are in `ec-asset-index/secrets_map.csv`; values never are.
- Known secrets for this repo (6): `CAP_ONLINE__LOCAL__CAPRANAV_COM_CAPRANAV_WEBSITE_RAZORPAY_KEY_ID`, `CAP_ONLINE__LOCAL__CAPRANAV_COM_CAPRANAV_WEBSITE_RAZORPAY_KEY_SECRET`, `CAP_ONLINE__DEV__CAPRANAV_COM_REVAMPED_RAZORPAY_KEY_ID`, `CAP_ONLINE__DEV__CAPRANAV_COM_REVAMPED_RAZORPAY_KEY_SECRET`, `CAP_ONLINE__DEV__CAPRANAV_COM_REVAMPED_CF_EMAIL_API_TOKEN`, `CAP_ONLINE__DEV__CAPRANAV_COM_REVAMPED_RAZORPAY_WEBHOOK_SECRET`
- You receive a value only through the **ECTPL credential agent** (`EFFICIENTCORPORATES/credential-agent`, `python ectpl_creds.py ...`), using **your own principal** (the designation of your role, e.g. the product manager above once it exists; today only `cloudflare-manager`, `github-manager` and `1lavya-product-manager` exist besides Pranav's admin), never another agent's or Pranav's identity unless Pranav explicitly authorises it for that task. Pipe the value straight into the command that needs it, e.g. `X=$(python ectpl_creds.py --as <you> get static:<NAME>) command`. Do not print, log, echo or commit it.
- If your principal cannot read a secret you need, **stop and ask Pranav** to grant it; do not look for it in `.env` files, chat history or other repos.
- Create `.env` locally from the secret names (see `.env.example` if present); `.env` is always gitignored.

### 5. How agents work here (agentic workflow)
- **Identity and scope:** act only as your designated role (see `ec-asset-index/GOVERNANCE.md`): Platform Manager (one platform), Product Manager (this product), or Process Owner (an approved n8n process). Stay inside this repo and the repos/platforms your task names. Humans and agents have separate identities.
- **Start of session:** read this file, `README.md`, the repo's own docs below, and the latest notes in `docs/sessions/` (if present). **End of session:** write `docs/sessions/YYYY-MM-DD-<topic>.md` (goal, decisions, commands run, files changed, open items, next step) and add anything lasting to `CONTEXT.md` / `docs/adr/` / `docs/runbooks/`. No secrets in notes.
- **Git:** work on a branch, small commits, open a PR; never force-push or rewrite history, never delete branches/repos, never commit files >= 5 MB or secrets. Destructive or irreversible actions (delete, force-push, drop data, change permissions) need Pranav's explicit approval in the session.
- **Ask, do not guess:** if ownership, a placement or a requirement is unclear, ask Pranav one concise question. Report outcomes faithfully (what ran, what failed).
- **Cost discipline:** use the cheapest model tier that does the job (open-source/small models for checks and routine edits; top models only for planning/hard reasoning), keep context small, cap loops/retries, and stop at your budget.
- **Commands:** run only commands needed for the task; project code, build scripts and git hooks are untrusted until reviewed. Do not install software or change system settings without approval.
<!-- EC-STANDARD:END -->


**Read this file first, every session. Then read the context in section 1 BEFORE executing any task.**
This repo is CA **Pranav Pratik Tulshyan**'s CA Inter teaching ecosystem for **VC Gurukul, Noida**.
Git root `D:\EffCorp_Projects\cap-online` · remote `EFFICIENTCORPORATES/cap-online` · branch `main`.

---

## 1. Read order (do this first, every session)

1. **AGENTS.md** (this file).
2. **README.md** — full repo map, the 6 pillars, and rules.
3. **content/README.md** — creative-studio rules (only if the task touches `content/`).
4. **_claude/memory/** — `project_log.md` (newest entry first) and the memory files there.

Large/binary files are in R2: see section 2b and `R2_MANIFEST.md` before concluding any file is missing.

Then briefly confirm you understand the structure and rules, and wait for the task. Do not start work before this.

---

## 2. Working rules (non-negotiable)

- **Markdown (`.md`) by default.** HTML for books and slides. **No SVGs/diagrams unless explicitly asked.**
- **No binary files in git.** Audio, video, images, office docs, archives, executables are gitignored — they live in private Cloudflare R2 (see section 2b and `R2_MANIFEST.md`), never only on one machine. Commit only text (md/py/html/json/csv...).
- **UTF-8 only.** Never write NUL bytes or UTF-16. (Cross-mount edits have corrupted files before — `health_check.py` now catches this.)
- **After ANY structural change** (add / move / rename / delete files or folders): run `python tools/health_check.py` and fix everything it flags, then run `python tools/file_index.py`. If you add a new top-level folder, also document it in this file and in `README.md` — `health_check.py` will fail until you do.
- **End every session** by appending a short dated note to `_claude/memory/project_log.md` (newest on top).
- **Ask first when stuck.** At the first genuine doubt or blocker, ASK Pranav — do not guess or spin on workarounds.
- **Pushing needs Pranav's credentials.** The sandbox cannot push to GitHub. Commit locally; Pranav runs `git push origin main` from his own machine.

---

## 2b. Large and binary files live in Cloudflare R2 (do NOT say they are missing or "only on the old disk")

Binary/large files (PDFs, videos, zips, installers...) are gitignored, **but they are not local-only**. Since 2026-10-20 every large file of this repo is stored in a private Cloudflare R2 bucket and indexed:

- **Bucket:** `ec-cap-online-assets` (Cloudflare account `68e19e5bed11326478a23d6e2ad31453`), private.
- **What is there:** 63 files, 2.68 GB (CA Inter question banks, strategy-book and study-material PDFs, b-roll video, zips...). The full list with R2 key, size and sha256 is in **`R2_MANIFEST.md`** (repo root).
- **Local-only small files** (ignored/untracked, incl. local config) are in one AES-256-encrypted archive: `local-only-archives/2026-10-20-cap-online.tar.gz.enc` (2105 files). Passphrase: Bitwarden Secrets Manager `EC_BACKUP__PROD__ARCHIVE_PASSPHRASE` (readable via the ECTPL credential agent).
- **Master index for all repos:** `EFFICIENTCORPORATES/ec-asset-index` (`ASSET_INDEX.json`, `tools/ec_assets.py`, `ASSET_WORKFLOW.md`).

### How to get a file that is in `R2_MANIFEST.md` but not on this machine
Do this yourself. Do not ask Pranav to find the file.
```bash
git clone https://github.com/EFFICIENTCORPORATES/ec-asset-index      # once, next to this repo
pip install boto3
# downloads every manifest file into place, verifying sha256 (use the parent folder of this repo as --dest):
python ec-asset-index/tools/ec_assets.py --agent pull cap-online --dest <parent-folder-of-cap-online>
```
Credentials: `--agent` asks the ECTPL credential agent for a short-lived Cloudflare token, or set `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY`. **Never ask for keys in chat and never commit them.** To fetch one file only, use boto3 `download_file(bucket, key, path)` with the key from the manifest.

Restore the encrypted local-only archive:
```bash
export EC_ARCHIVE_PASSPHRASE=...   # from Bitwarden, never printed or committed
python ec-asset-index/tools/ec_assets.py --agent restore-local cap-online local-only-archives/2026-10-20-cap-online.tar.gz.enc --dest <parent-folder-of-cap-online>
```

### When you create or change a big file
1. `python ec-asset-index/tools/ec_assets.py scan <path-to-cap-online>` lists big files not yet in R2.
2. `python ec-asset-index/tools/ec_assets.py --agent push <path-to-cap-online> --all` uploads, verifies, updates the index and `R2_MANIFEST.md`.
3. Keep the file gitignored; commit `R2_MANIFEST.md` and push (`ec-asset-index` gets `ASSET_INDEX.json` committed too). Install the guard once per clone: copy `ec-asset-index/tools/pre-push-large-files.sh` to `.git/hooks/pre-push`.
4. Before ending a session, run `scan` (nothing should be listed) and `backup-local`. Full guide: `ec-asset-index/ASSET_WORKFLOW.md`.

---

## 3. What each folder is for

| Folder | Purpose |
|--------|---------|
| `books/strategy-book/` | **Pillar 1** — Exam Strategy book (general + journey + exam-specific). `sources/` (research, skills, external reports), `design/` (spec + HTML build templates), `working/` (MASTER + component-index), `drafts/ final/` |
| `books/concept-book/` | **Pillar 2** — Advanced Accounts **Concept Book** (this IS the Adv-Accounts book): `chapter-zero/ characters/ chapters/ story-vignettes/ revision-material/` |
| `books/about-author/` | Shared author profile + journey (used by both books) |
| `syllabus-engine/` | **Pillar 3** — ICAI material → JSON/MD. `data/ scripts/ html-source/` |
| `question-bank/` | **Pillar 4** — non-study-material questions (7–10 yrs): `pyq/ mtp/ rtp/ solutions/` |
| `mcq-platform/` | **Pillar 5** — AI MCQs in a DBMS, Cloudflare online tests: `question-generation/ database/ cloudflare-app/` |
| `telegram/` | **Pillar 6** — study bots + their source docs: `bots/ source-docs/` |
| `student-toolkit/` | Standalone student tools (e.g. exam date calculator). A subset of student-facing utilities; the Telegram bots may also surface these. |
| `content/` | Creative studio: `assets/` (raw-footage, intros-outros, green-screen, b-roll, music-sfx, brand-kit, thumbnails, flyers), `social/{personal,vc-gurukul}`, `calendar/`, `scripts/`, `motivation/` (daily-quote media library), `competitor-analysis/`, `ai-content-pipeline/`, `productions/` (one folder per video/content piece). See `content/README.md`. |
| `vc-gurukul/` | Institute side (NOT content brand): `management-discussions/ events/ batch-july-2025/ contracts/` |
| `materials/` | `icai-source/` (study material, PYQ/MTP/RTP — **gitignored/local**) + `reference/` (incl. `samples/`) |
| `obs-setup/` | Recording/streaming setup: `assets/` (OBS wallpapers), `recordings/` (output), `tools/` |
| `photo-gallery/` | `originals/` (gitignored) + `index.md` |
| `planning/` | Future planning: `future-roadmap.md`, `to-purchase.md`, `execution-notes.md` |
| `preparations/` | Personal prep notes, lecture plans |
| `final-deliverables/` | Print-ready teaching documents: teaching method (01), batch planner (02/02A), bridge course skeleton (03/03A), and future student-facing exports. MD only. |
| `tools/` | Admin/processing scripts (see section 5) |
| `_claude/` | Codex's context: `memory/` (incl. `project_log.md`), `artifacts/`, `skills/` |

**Only TWO self-drafted books:** the strategy book and the concept book (Advanced Accounts). Everything else is engine/platform/content/ops.

---

## 4. Tools

- `tools/health_check.py` — validates folder structure, README links, UTF-8/NUL encoding, and **AGENTS.md staleness**. Run after every structural change.
- `tools/file_index.py` — regenerates `_claude/artifacts/file-index.md`.
- `tools/gitignore_audit.py` — flags binaries / large files not covered by `.gitignore`.

---

## 5. Repo-specific gotchas

- **Animation = Excalidraw.** Screen mirroring = **UxPlay** (Windows).
- `content/social/personal/` = **entirely Pranav's own** content. `content/social/vc-gurukul/` = **co-branded** Pranav + VC Gurukul. Two calendars (private vs shared) sync to a Google Sheet via `content/scripts/gsheet_sync.py`.
- The content-side `vc-gurukul` is the *brand*; the top-level `vc-gurukul/` is *institute ops/contracts* — different things.
- Heavy raw media (raw footage especially) is best kept on an external drive/cloud; the repo holds the recipe + finished exports + an index.

## Imported Claude Cowork project instructions

This project is created for finalizing the content around the bridge course and the Demo lecture on ind AS 02 - valuation of Inventories
