# Backlog — everything not done yet

_Last updated 2026-11-09. This is an **index**: each item says what is pending, who has to act,
and where the detail lives. Do not copy detail here; point to it. Update this file in the same commit
as the work._

## How to use this file

- **Id** is stable. Never reuse or renumber one. Prefixes: `R` repo and governance, `M` Must Practice,
  `S` website (ids are the ones in `capranav_com_revamped/AGENT-HANDOFF.md` §4), `Q` Question Bank
  Book second edition (ids are the `CR-` ids in the change register), `T` teaching material and Kahaani lectures (added 2026-11-09), `O` other workstreams.
- **Who**: `Pranav` = needs his decision, account or action. `Agent` = an AI session can do it now.
  `Both` = an agent prepares, Pranav confirms.
- **Priority**: `P1` act soon, `P2` normal, `P3` small or later.
- **Issue** is the GitHub issue number once one exists, recorded in `docs/backlog-issues.json` by
  `tools/backlog_to_issues.py` (dry-run by default; see `CONTEXT.md` §2). Where issues live is itself
  undecided (BL-R02). Until then this file is the tracker.
- To add an item: pick the next id in its group, fill every column, and link the detail document.

## R. Repo and governance

| Id | Item | Pri | Who | Status | Detail |
|---|---|---|---|---|---|
| BL-R01 | **The repo is public on GitHub**, but the EC operating guide in `CLAUDE.md`/`AGENTS.md` says private. Decide: make it private, or confirm public is intended. If it stays public, remove personal identifiers from the docs (two Telegram admin chat IDs and an external contributor's email appear in `CLAUDE.md`, `_claude/memory/project_log.md` and `_claude/artifacts/telegram-prune-manifest.txt`; Cloudflare account ids appear in the EC block and `R2_MANIFEST.md`). Git history keeps old versions. A bounded scan on 2026-10-31 found no tokens or private keys in the working tree or history, but it was not an exhaustive audit. | P1 | Pranav (setting), Agent (redaction) | Decision needed | this file |
| BL-R02 | Decide where issues live: this repo's GitHub Issues (public today, only default labels, none open) or `EFFICIENTCORPORATES/task-hub`. Then run `python tools/backlog_to_issues.py --execute` (43 rows would become issues; the dry-run shows each). | P1 | Pranav | Decision needed | `CONTEXT.md` §2 |
| BL-R03 | Document the background job that commits "auto: N file(s) updated": what runs it, where, how often, whether it pushes, and what it covers. It commits other sessions' unfinished files. | P2 | Pranav (tell us), Agent (document) | Open | `CONTEXT.md` §4 |
| BL-R04 | Stop Google Drive from writing `desktop.ini` files into `.git/refs`; they break `git fetch`. Exclude `.git` from Drive sync. Workaround is in `CONTEXT.md` §4. | P2 | Pranav | Open | `CONTEXT.md` §4 |
| BL-R05 | `CLAUDE.md` is about 2,460 lines, mostly dated history (sections 6 to 11), too long for an agent to read first. Proposal: move those sections to `docs/history/`, keep `CLAUDE.md` and `AGENTS.md` short and pointing to `CONTEXT.md`. Needs Pranav's go-ahead because another session also edits these files. | P2 | Both | Proposed | `CLAUDE.md` |
| BL-R06 | The `capranav-product-manager` principal in the credential agent is not created yet; secrets and R2 pulls through the credential agent need it. | P2 | Pranav | Open | EC block in `CLAUDE.md` §1 |

## M. Must Practice (`/practice-with-pranav-bhaiya/must-practice/`)

State: all 36 units live. 18 standard units, 16 short units, 2 pointer units, 274 questions.

| Id | Item | Pri | Who | Status | Detail |
|---|---|---|---|---|---|
| BL-M01 | **Same-idea repeat review** for the 16 standard units not yet reviewed (all except AS 2 and AS 10): AS 4, 5, 9, 11, 12, 13, 16, 19, 21, 29, Framework, Financial Statements of Companies, Cash Flow Statement, Amalgamation, Internal Reconstruction, Branch Accounting. Look for parts of one question reissued alone and the same idea under different topic tags; add `force_exclude` with a reason. | P2 | Both | Ready | `capranav_com_revamped/MUST-PRACTICE.md` step 4; `MUST-PRACTICE-RULES.md` |
| BL-M02 | **Study Material items for short units.** 11 short units have Study Material candidates and no items yet: AS 7, 15, 17, 18, 20, 22, 23, 26, 27, 28 and Buyback. Per unit: read the ICAI PDF pages, transcribe question and answer, re-derive arithmetic, tag topics, add to `data/study-material-items/<unit>.json`. AS 25 is done and is the worked example. Basics, Applicability and AS 24 have no Study Material items; AS 1's three are all already covered by past questions. | P2 | Agent (Pranav answers real judgment calls) | Ready | `_claude/skills/SKILL-must-practice-questions.md` §6.6 |
| BL-M03 | Five AS 1 questions on the live list (six in the library) have no syllabus topic mapped, so they appear under no topic in the topic map. Needs tagging in the Question Bank source, which is also a first-edition book matter. | P3 | Both | Open | `must_practice_topic_map.json` caveats |
| BL-M04 | Revisit gating answers behind login once the passkey login exists. Decision on 2026-10-18 was: public for now. | P3 | Pranav | Waiting on S-B1 | `CONTEXT.md` §3 |
| BL-M05 | The "QNone" display override for PYQ November 2023 Q4 (`M3C11U1-024`) is temporary until the sitting HTML is fixed in the second edition. | P3 | Agent | Waiting on Q-CR-008 | `first_run/SECOND-EDITION-CHANGE-REQUESTS.md` CR-008 |
| BL-M06 | Run `verify_must_practice_live.py` automatically (add to `qa_smoke.py`) instead of by hand after each deploy. | P3 | Agent | Open | `capranav_com_revamped/tools/` |
| BL-M07 | The Must Practice page HTML is about 224 KB because of the crawler-readable list for 36 units. Consider trimming the text per question. | P3 | Agent | Open | `tools/build_seo_static.py` |

## S. Website capranav.com

Authoritative text, acceptance tests and file paths are in `capranav_com_revamped/AGENT-HANDOFF.md` §4.
The owner-facing short list is `capranav_com_revamped/PENDING.md`. One line each here.

| Id | Item | Pri | Who | Status |
|---|---|---|---|---|
| S-A1 | Cloudflare Access on `/admin*` and `/api/admin/*` (needs the email to allow); the other protections were applied by API 2026-09-27 | P1 | Pranav | Blocked |
| S-A3 | Submit `sitemap.xml` in Google Search Console and Bing Webmaster Tools | P2 | Pranav | Blocked |
| S-A4 | Backlinks to capranav.com from the VC Gurukul site, YouTube, LinkedIn, Instagram, Telegram | P2 | Pranav (Agent drafts text) | Blocked |
| S-A5 | Keep the Razorpay and email-token secrets in a password manager; download a DNS zone export | P1 | Pranav | Blocked |
| S-A6 | Decide which AI training crawlers stay allowed | P3 | Pranav | Decision needed |
| S-A7 | Passkey login design (Pranav said he will describe it); blocks B1 | P2 | Pranav | Decision needed |
| S-A8 | Review the 4 Shorts chosen from titles; send more video links | P3 | Pranav | Blocked |
| S-A9 | Question Bank e-book checkout: bring back to this site or keep VC Gurukul's store | P2 | Pranav | Decision needed |
| S-A10 | Unanswered profile questions ("1% at all levels", school marks, proof link, Newton of Accounts URL) | P2 | Pranav | Decision needed |
| S-A11 | Where the 1lavya.com site's repo lives | P3 | Pranav | Blocked |
| S-A12 | Read the Terms clause once (legal wording) | P2 | Pranav | Blocked |
| S-A13 | Real-phone check of Videos, Topics, Must Practice, FAQ | P2 | Pranav (Agent writes the checklist) | Blocked |
| S-A14 | September batch: add the product and price when it opens | P2 | Both | Waiting on the batch |
| S-B1 | Free login without personal data, then gate answers and bulk data | P2 | Both | Waiting on S-A7 |
| S-B2 | One public page per topic (400) and per question (no answers), in the sitemap | P2 | Agent | Ready |
| S-B4 | Canary entries and per-account watermarks | P3 | Agent | Ready |
| S-B6 | Videos in D1 with an admin form, upload dates, transcripts | P3 | Agent | Ready |
| S-B7 | Content-Security-Policy, report-only first | P3 | Agent | Ready |
| S-B8 | Small items: 1200x630 share image, Anatomy tick-many filters, Cloudflare Web Analytics | P3 | Agent | Ready |
| S-B9 | The 1lavya.com landing for the UTM links | P3 | Both | Waiting on S-A11 |
| S-B10 | Backups second pass: exercise the failure-alert email, off-site copy beyond Cloudflare, quarterly restore drill | P2 | Both | Ready |
| S-B11 | Tune and watch the rate-limit guards | P3 | Agent | Ready |

## Q. Question Bank Book, second edition

The register `first_run/SECOND-EDITION-CHANGE-REQUESTS.md` is authoritative (status, severity, reasoning).
The first edition is printed and distributed; nothing here changes a student's copy.

| Id | Item | Pri | Who | Status |
|---|---|---|---|---|
| Q-CR-001 | OP/PP recurring-question tags not built (out of scope for edition one) | P3 | Both | Open |
| Q-CR-002 | Short chapter and unit names not drafted | P3 | Both | Open |
| Q-CR-003 | Distributed V1 PDFs predate the Cash Flow chapter fix; a corrected PDF needs Pranav's explicit ask | P2 | Pranav | Fixed in source, PDF stale |
| Q-CR-004 | Legacy pre-syllabus-change topics excluded with no appendix | P3 | Both | Open |
| Q-CR-005 | Descriptive answers were not independently re-derived (risk, not a confirmed defect) | P2 | Agent | Open |
| Q-CR-006 | Reader-reported errors have no intake path into the register | P2 | Both | Open |
| Q-CR-007 | Some questions are printed twice (home chapter and Integrated section) | P3 | Both | Open |
| Q-CR-008 | PYQ November 2023 Q4 prints as "QNone" | P2 | Agent | Open |
| Q-CR-009 | Chapter order should follow Pranav's real sequence (`BOOK-SEQUENCE.csv`); decide how the two split units are handled | P2 | Both | Open |
| Q-CR-010 | Highlight the Must Practice questions separately in each chapter | P2 | Agent | Open |
| Q-CR-011 | Add MTP and RTP for September 2026 and January 2027 (Jan 2027 availability not verified) | P1 | Both | Open |
| Q-CR-012 | Typos and trial balances not rendered correctly: audit the 26 trial-balance questions against the PDFs (8 have no table) | P1 | Agent | Open |
| Q-CR-013 | Remove the repeated accuracy, scope and organisation notes from every chapter; keep them once in the front matter | P2 | Agent | Open |
| Q-CR-014 | Running header with chapter and unit on every page (cause of the missing header not yet found) | P1 | Agent | Open |
| Q-CR-015 | Footer on every page: #Newton of Accounts, AIR 1-1-5, Pranav Bhaiya | P2 | Agent | Open |
| Q-CR-016 | OP/PP tags confirmed for the second edition; run once after the new sittings are added | P2 | Both | Open |

## T. Teaching material, Kahaani lectures and chapter notes

State (2026-11-09): Kahaani lecture 1 deck built and reviewed; website pages prepared but **not deployed**; two reusable skills written; chapter notes for Ch 14 done, Ch 11/12 partly done. All of it was **merged into `main` on 2026-11-09** (BL-T01 done); the feature branch can be deleted. Full handover and standing preferences: `docs/sessions/2026-11-09-teaching-material-handover.md`. Notes: `books/ca-inter/teaching-notes/`.

| Id | Item | Pri | Who | Status | Detail |
|---|---|---|---|---|---|
| BL-T00 | Tracking issue for this group (umbrella to-do list): **GitHub issue #4** (https://github.com/EFFICIENTCORPORATES/cap-online/issues/4), created by hand on Pranav's request, not by `tools/backlog_to_issues.py`; it is not recorded in `docs/backlog-issues.json`. | P2 | Agent | Open | `docs/sessions/2026-11-09-teaching-material-handover.md` §6 |
| BL-T01 | Merge branch `claude/sweet-brahmagupta-5yu98q` (and the two other unmerged remote branches) into `main`, one trunk, then delete the other branches. | P1 | Pranav | **Done 2026-11-09** (merged by an agent on Pranav's explicit instruction; branches not deleted by the agent) | handover §8 |
| BL-T02 | Deploy the Kahaani area (index + deck) to capranav.com from the checkout that has the site's gitignored images (never from a fresh clone), then `qa_smoke.py --browser` and `indexnow_ping.py`. | P1 | Pranav | Prepared, waiting | `capranav_com_revamped/PROJECT-LOG.md` (2026-11-06) |
| BL-T03 | Decide whether the site navigation gets a Kahaani link (none was added). | P3 | Pranav | Decision needed | `capranav_com_revamped/public/kahaani/` |
| BL-T04 | "What is new in TYK" lists for the **Chapter 12 TYK** and the dividend-related **Chapter 11 TYK** (MCQ 5, 8, 9; Q15 Z Ltd); append to the Ch 11/12 note. Use `/chapter-illustration-traps`. | P2 | Agent | **Chapter 12 TYK done 2026-11-09** (note section 6). **Chapter 11 TYK (MCQ 5, 8, 9; Q15 Z Ltd) NOT DONE YET** | `books/ca-inter/teaching-notes/ch11-12-dividend-vs-buyback.md` |
| BL-T05 | Buyback and Dividend teaching deliverable. Ask Pranav which format: Kahaani-style deck (two calculations animated side by side), Markdown teaching note, or traps only. Content already written. | P1 | Both | Waiting on Pranav's choice | same note |
| BL-T14 | Concept book build: follow `books/ca-inter/teaching-notes/CONCEPT-BOOK-DESIGN-BRIEF.md` (complementary book, no Q&A, question references after each concept, Error Register Points, visuals, linkages). Teaching notes done for Ch 14, Ch 11/12 (TYK pending) and AS 14 + Ch 13. | P2 | Both | Start with the chapter Pranav picks; run `chapter-illustration-traps` first for any chapter not yet covered |
| BL-T06 | AS 26 revision sheet: fix the revaluation error, add the missing items, improve layout; decide which Drive version is current. The sheet is unchanged. | P2 | Both | Waiting on Pranav's go-ahead | `_claude/skills/SKILL-chapter-review-skills.md` §4 |
| BL-T07 | NB01/NB02 class notes are scanned (no text layer): Pranav to give the chapter order as a short list for any sheet whose teaching sequence must be checked. | P3 | Pranav | Open | `.claude/skills/concept-material-review/SKILL.md` §4 |
| BL-T08 | Next Kahaani decks (e.g. Internal Reconstruction, Amalgamation) following the `content/productions/restructuring-lecture-1/` pattern. Ask which chapter first. | P2 | Agent | Waiting on Pranav's choice | that folder's `deck/README.md` |
| BL-T09 | Verify every real-world example before use in a deck (Vistara merged into Air India Nov 2024; check Titan, SBI, Walmart-Flipkart, Tata Digital-BigBasket, Tata Motors-JLR). | P3 | Agent | Open | `content/productions/restructuring-lecture-1/outline/SPEAKER-NOTES.md` |
| BL-T10 | In a fresh session confirm the two skills load (`/chapter-illustration-traps`, `/concept-material-review`). | P2 | Agent | Open | `.claude/skills/` |
| BL-T11 | Source-material oddities (list in handover §5): register them if Pranav wants them tracked. | P3 | Agent | Open | handover §5 |
| BL-T12 | Committed `capranav_com_revamped/public/faq/index.html` lacks the SEO head block; re-run `tools/apply_seo_meta.py` before the next deploy. | P3 | Agent | Open | `capranav_com_revamped/PROJECT-LOG.md` (2026-11-06) |
| BL-T13 | Pranav's local branch `docs/concept-book-storylines` was not visible to cloud sessions; push or merge it if it holds concept-book work. | P2 | Pranav | Open | `CONTEXT.md` §1 |

## O. Other workstreams (owned by another session)

Their open items are not recorded in one place, so none are listed. Their entry documents:
`books/ca-inter/concept-book/CONCEPT_BOOK_NOTES_PIPELINE.md`, `NEWTON_CONCEPT_BOOK_PRODUCTION_GUIDE.md`,
`books/ca-foundation/README.md` and `DOWNLOADER-SPEC.md`, the Google Drive to R2 workflows in
`.github/workflows/`, and the AS 26 revision HTML. **BL-O01** (P2, Pranav or that session): add their open
items to this file so the picture is complete.
