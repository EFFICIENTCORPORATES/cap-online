# Teaching notes (for Pranav's classes, not student-facing)

Chapter-by-chapter aids an AI session wrote for Pranav while he prepares to teach: the main trap in each ICAI illustration, what is new in Test Your Knowledge, and short answers to his concept questions. Produced with the `chapter-illustration-traps` skill (`.claude/skills/`). The repo-wide state and to-do list for this work: `docs/BACKLOG.md` group **T** and `docs/sessions/2026-11-09-teaching-material-handover.md`.

| File | Covers | State |
|---|---|---|
| `ch14-internal-reconstruction-traps.md` | Illustrations 1-8 and TYK (new items only) of Ch 14 | Done |
| `ch11-12-dividend-vs-buyback.md` | Pages, the dividend-vs-buy-back difference, Ch 12 Illustrations 1-6 and Ch 11 Illustration 1, the CRR rule | Illustrations done; **TYK new-items list not done** |
| `ch09u2-ch13-amalgamation-traps.md` | AS 14 (Ch 9 Unit 2) and Ch 13: main trap per illustration, new points in TYK | Done |
| `concept-clarifications.md` | Purchase-method reserves, subsidiary bonus shares, cross-holding / Sec 19, overdraft in Ill. 3, pointer to the AS 26 review, amalgamation why-answers (net assets chart, statutory reserves, AAR) | Done (sections 1-8) |
| `CONCEPT-BOOK-DESIGN-BRIEF.md` | **Read first when building the concept book:** what the book is, the building block per concept, Error Register Points, visuals, linkages, rules for the agent | Done |
| `diagrams/` | HTML sources of the CRR formula and Simple Ltd diagrams (render with headless Chromium; PNGs are gitignored) | Done |

Rules for adding a file: one chapter per file named `chNN-<slug>-traps.md`; header with source file, edition and "page numbers not checked against the PDF"; recompute every figure with a script; mark every inference ("my reconstruction", "ICAI's solution does not say").
