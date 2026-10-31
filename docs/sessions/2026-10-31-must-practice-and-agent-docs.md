# Session note: Must Practice for all units, and making the repo self-explanatory for agents

Sessions of 2026-10-06, 10-18, 10-21 and 10-31 (one Claude Code conversation). Owner: Pranav.

## Goal

Publish the Must Practice question lists for every syllabus unit on capranav.com, document the method
and the data behind it so any agent can repeat or extend it, and make the repo's entry points
(`CLAUDE.md`, `AGENTS.md`, `CONTEXT.md`) and a pending-work index reliable.

## Decisions (Pranav)

- **2026-10-18, short units:** combine the Question Bank with Study Material Illustrations and Test Your
  Knowledge questions, keep unique ones only, publish even if fewer than ten.
- **AS 25 pilot:** Illustration 1 kept, Illustration 4 dropped as the same problem with other figures,
  Illustration 1 still unique next to PYQ May 2025 Q3(b). Label: "ICAI Study Material, Illustration N, p. <printed page>".
- **AS 3 and AS 14:** pointer units to the Module 3 units. **Answers stay public** for now.
- **2026-10-31:** keep `CLAUDE.md` and `AGENTS.md` both; track pending work in one file first
  (`docs/BACKLOG.md`), GitHub issues after Pranav decides where they live.

## What was done

- Published AS 16 (2026-10-06), then AS 25 (short unit, one Study Material item), AS 3 and AS 14
  (pointers), then the remaining 30 units in one pass (2026-10-18): 36 units, 274 questions, every
  Question Bank page number traced. Live check passes for all 36 (`capranav_com_revamped/tools/verify_must_practice_live.py`).
- Wrote the method and data provenance: `_claude/skills/SKILL-must-practice-questions.md`, the runbook
  `capranav_com_revamped/MUST-PRACTICE.md`, and `first_run/scripts/build_study_material_pool.py`.
- Generated a Study Material topic to questions map (400 topics, 175 with questions):
  `books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/data/must_practice_topic_map.json` and `.csv`.
- Logged first-edition defect CR-008 (PYQ November 2023 Q4 prints as "QNone").
- 2026-10-31: added `CONTEXT.md`, `docs/BACKLOG.md`, this note; fixed stale statements in `AGENTS.md`
  (pushing is possible, old paths, thin read order); added a drift guard to `tools/health_check.py`.

## A correction

On 2026-10-18 the unit counts were reported as "20 standard, 14 short, 13 lacking Study Material".
The true figures are **18 standard, 16 short (AS 20 and Buyback were miscounted), 2 pointer; 15 short units
lack Study Material items; 16 standard units are unreviewed**. Fixed in the living documents; the two
dated log entries carry a correction line.

## Findings worth knowing

- The GitHub repo is **public** although the operating guide says private (backlog BL-R01).
- `AGENTS.md` had drifted into an abridged, stale copy of `CLAUDE.md` (114 lines against 2,414, missing
  62 sections, still saying the sandbox cannot push).
- Google Drive writes `desktop.ini` files into `.git/refs`, which breaks `git fetch` (recipe in `CONTEXT.md`).
- The lexical similarity in the pool script understates overlap between a Study Material illustration and
  the exam question built on it, and cannot see the same problem with different figures.

## Commands that matter

`python capranav_com_revamped/tools/build_must_practice_data.py`, `python capranav_com_revamped/tools/build_seo_static.py`,
`npx wrangler deploy` (from `capranav_com_revamped/`), `python capranav_com_revamped/tools/verify_must_practice_live.py`,
`python first_run/scripts/build_study_material_pool.py`, `python tools/health_check.py`, `python tools/file_index.py`.

## Open items and next step

All open items are indexed in `docs/BACKLOG.md`. Highest value next: BL-R01 (public repo, Pranav decides),
BL-R02 (where issues live), then BL-M01 (repeat review of 16 standard units) and BL-M02 (Study Material
items for 11 short units).
