# Concept Book: build plan (revision 4, 2026-11-13)

_Draft for Pranav's review. **Nothing is built yet.** Revision 2 replaces revision 1 after Pranav's second message of 2026-11-13: the unit of work is the **unit file (36 of them), not the topic card (400)**; three pilot chapters; a new illustration framework; handwritten style. It sits on top of `teaching-notes/CONCEPT-BOOK-DESIGN-BRIEF.md` and the two older runbooks in this folder. Decisions marked **(Pranav)** are his own words; everything else is **(proposal)**._

---

## 1. Decisions already made (Pranav, 2026-11-13)

| Topic | Decision |
|---|---|
| What the book is | A story-and-picture book of concepts, **complementary** to ICAI, never a replacement; readable in a few hours on the day before the exam |
| References | Module-chapter-unit-topic IDs, **no page numbers**; illustrations cited by **number + entity name** |
| Unit of work | **One file per unit/chapter entry of the index (36)**, not 400 cards. A story may span topics and a big topic may hold several stories, so stories are not tied to topics |
| Grouping | Related units are grouped into **families** (e.g. the asset-based standards) because their stories link |
| Pilots | **Internal Reconstruction**, **AS 2 or AS 10** (big, many stories), and **AS 29** (very different; a test of how an agent copes) |
| Illustration framework | Goal → Concepts triggered → Given → Approach (short; no number-by-number working) → Exam points → Tricky points (the **Error Register / Sanjeevani Booti**); figures where they matter, wording where the concept is the wording |
| Difficulty | **Easy / Medium / Hard** per illustration; "Hard" may later be renamed **LDR** (last-day-revision) |
| Stories | **Real class stories first** |
| Language | **English** everywhere, **except stories and "things to remember" (memory lines, mnemonics), which are Roman-script Hinglish** (revised 2026-11-13, third message) |
| Look | **Handwritten style**, like Excalidraw; not typed |
| Pictures | Real photos found later (e.g. an office building); **HTML/CSS diagrams**; **SVG is allowed** for pictures, judged by effort |
| Repo | Public is acceptable (it is public; see section 11) |
| Agents | Parallel sessions approved. No spending cap; the weekly and monthly usage limits apply, and Pranav can ask for a reset |

## 2. What the Question Book teaches us (unchanged from revision 1)

| Lesson | Use here |
|---|---|
| Layers: authored records → mechanical index → generated chapter → merged book; generated files never hand-edited | Layer 1 = **unit files** (authored); Layer 2 = indexes (`icai_refs.json`, `importance.json`); Layer 3 = generated chapter HTML; Layer 4 = merged book |
| One taxonomy key; never invent a second ID scheme | Join on `unique_topic_id` of `syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json` (e.g. `M3-C14-U0-T3`) |
| Strict schema, validators, coverage checked both ways | Every ICAI illustration and TYK item must appear in its unit file; every reference must resolve |
| Provenance labels (Examiner's Comment vs Author's Note) | Every block says whose it is: ICAI, Pranav's class, or agent draft |
| One style file (`book-style.json`), `break-inside: avoid`, vendored fonts, headless-Chrome page numbers | Reuse the print chain (`qb_common.py`, `qb_merge.py`, `resolve_qb_toc_pages.py`) |
| Round-trip QA; pilot first; parallel agents that self-validate and are spot-checked; write to disk early | Same |
| A defect found in a distributed book is logged first | `CONCEPT-BOOK-CHANGE-REQUESTS.md` from day one |
| Known slip | Chapter title repeats ("Internal Reconstruction — Internal Reconstruction") when a chapter has no AS number |

**Two taxonomies exist.** The Question Bank tags with `topic-index.json` references; the Concept Book uses file 1's IDs. `questions_index.json` carries `final_chapter` in file 1's chapter format (`M3-C15-U0`), so chapter-level joins work now. Topic-level joins go through `must_practice_topic_map.json`, which already holds `overall_rank`, `priority_band` and `pyq_allocated_marks` per topic (the importance signal, section 6).

## 3. The 36 units and their families (**proposal**)

The index has **36** entries (34 teaching-sequence numbers; sequences 23 and 30 each split into A and B). Topic counts are from file 1 (they sum to 400).

| Family | Units | Topics |
|---|---|---|
| A. Foundations | Intro to AS, Applicability, Framework | 27 |
| B. Asset-based | AS 2, AS 10, AS 26, AS 16, AS 19, AS 28, AS 13 | 103 |
| C. Liability-based | AS 29, AS 15 | 32 |
| D. Items impacting financial statements | AS 4, AS 5, AS 11, AS 22 | 34 |
| E. Income-side | AS 9, AS 7, AS 12 | 31 |
| F. Presentation and disclosure | AS 20, AS 1, AS 3, AS 17, AS 18, AS 24, AS 25 | 75 |
| G. Company financial statements | Ch 11 Unit 1, Ch 11 Unit 2 (Cash Flow; cross-linked with AS 3, which is a separate unit) | 13 |
| H. Group accounts | AS 21, AS 23, AS 27 | 41 |
| I. Restructuring | Ch 13 Amalgamation, AS 14, Ch 12 Buyback, Ch 14 Internal Reconstruction | 31 |
| J. Branches | Ch 15 | 13 |

- **One agent per unit file at a time.** A family has a short **family spine** (`_families/<family>.md`, written first by a strong model): the running thread, recurring real class stories, and the cross-unit linkages, so units in a family feel like one story.
- Pilots come from families I, B and C, so they test three different shapes (calculation-heavy, long and story-rich, judgement/theory-heavy).

## 4. References without page numbers (format is my proposal)

**Topic reference:** the file-1 ID, plus ICAI's own para number where the topic is large: `M3-C15-U0-T5 §5.2`.

**Item reference:** number + entity name. What ICAI actually has (counted across all 36 converted files): 218 illustrations (including (a)/(b) parts), 88 examples, 89 notes, and in Test Your Knowledge 250 MCQs, 99 theory questions and 162 scenario questions.

| ICAI item | Written in the book | Machine key |
|---|---|---|
| Illustration 5 | Illustration 5, Best (Jammu branch) | `M3-C15-U0:ILL-5` |
| Illustration 1(b) | Illustration 1(b), Buckingham Bros (Nagpur) | `…:ILL-1-2` |
| Example 3 | Example 3, XP Ltd | `…:EX-3` |
| TYK scenario Q14 | TYK Q14, Green Ltd | `…:TYK-SBQ-14` |
| TYK MCQ / theory | TYK MCQ 5, "debt-equity test" | `…:TYK-MCQ-5` |

- **The number is the key; the entity name is a human check.** A naive pattern finds a company name in only about **65%** of illustrations, examples and scenario questions; the rest name a person ("Mr. Mehul") or nothing. When there is no company, use the person, otherwise a 3 to 5 word label marked as a label.
- **Edition stamp** on every unit (now July 2026, May 2027 attempt). If ICAI renumbers, the registry is rebuilt and the validator lists every reference that stopped resolving.
- **Pages are used only inside the scripts** to place an item under a topic. File 1 and the converted ICAI files disagree by about one page in places (Branch Accounts: topic 7 starts 15.44 in file 1 and 15.43 in the converted file), so the join uses page ranges plus heading text and flags anything ambiguous.
- ICAI topics are sometimes finer than file 1's (Branch topic 5 contains ICAI paras 5.1 cost, 5.2 selling price, 5.3 wholesale). The unit file anchors to the ICAI para inside the topic.

## 5. The unit file (the unit of work)

One Markdown file per unit, named by the file-1 chapter ID: `content/M3-C14-U0.md`. A fixed set of sections (**proposal**):

1. **Front matter (YAML):** unit ID, title, family, edition, status (`skeleton | story-drafted | agent-checked | pranav-approved | locked`), sources used and sources **not** available, open questions.
2. **Unit map:** the topics (T1…Tn) with generated importance chips.
3. **Stories:** `S1…Sn` blocks. Each has: the source (lecture file + timestamp, or notebook page, or `agent-draft`), which topics it covers (many-to-many), the text, and an optional picture reference. A topic may reference several stories; a story may cover several topics.
4. **Concepts, by topic (anchored by topic ID):** in plain words; **Why** boxes (the doubt and the underlying identity); the exam algorithm; **Exam points**; **Linkages** ("You will also see this in <topic ID>: one line"); the **last-day line**.
5. **Illustration and TYK cards** in the framework below.
6. **Most Common Errors page (end of every unit; Pranav, 2026-11-13):** the 4 to 14 Error Register points flagged "most common", collected by a script from the topics and cards (each point is written once), followed by **the rest of the page left blank for the student's own entries** (Sanjeevani Booti 2). Ruled lines belong only on this writing area.
7. **Last-day page:** generated from the last-day lines.

### Illustration card (Pranav's framework)

Fields, in this order: **Reference** · **Difficulty** (computed) · **Goal of the question** · **Concepts triggered** (topic IDs) · **Given** (only the facts that matter, in words) · **Approach** (the concepts in a few short lines; numbered steps **only** where the order of steps is the point, and figures **only** where a calculation is genuinely tough or the figure is the exam point) · **Exam points** · **Tricky points** (the Error Register entries: wrong move → right move → why).

**Writing rule (Pranav, 2026-11-13): no number-by-number working.** The card says what to do and what to watch, not the whole solution. A sample with the earlier long working was rejected as too verbose.

**Sample, revised (illustrative only; Branch Accounts is not a pilot chapter):**

> **Illustration 5, Best (Jammu branch)** · `M3-C15-U0:ILL-5` · Medium
> **Goal:** the branch's profit for the year, and the stock reserve for unrealised profit.
> **Concepts triggered:** goods invoiced at cost plus loading; closing stock valued at invoice price; stock reserve (`T5 §5.2`).
> **Given:** three prices (cost, invoice = cost + 20%, sale = cost + 50%); opening stock and goods sent at invoice price; sales and expenses.
> **Approach:** bring sales down to invoice price to find the goods sold; closing stock follows from opening stock plus goods sent less goods sold; the reserve is the loading portion of closing stock.
> **Exam point:** the loading is 20/120 of invoice price.
> **Tricky points:** *Wrong:* 20% of closing stock. *Right:* 20/120. *Why:* the 20 is inside the 120. ICAI's profit is the branch's profit at invoice price; the business's own profit also includes the loading realised on goods sold (ICAI does not say this; my reconstruction).

**Difficulty is computed**, not authored: by the Question Bank's rule (up to 2 concepts triggered = Easy, 3 to 5 = Medium, over 5 = Hard), with the labels in the style file so renaming "Hard" to "LDR" is one edit. (**Open:** is LDR just Hard renamed, or a separate "solve this on the last day" flag chosen from all difficulties?)

## 6. Highlights, importance and the Strategy Book

Box types, one colour and one label each, defined once in the style file:
**Exam Point · Error Register Point (with "most common") · Why · Story / Picture · Kaam Ki Baat · Linkage · Agent draft (removed before release).**

- **Importance chips are computed:** from the Must Practice topic map and the Question Bank marks mapping ("asked in N of 15 attempts"), so a student sees at a glance what a boundary should include (MIN / MAX / RANKER).
- **Strategy Book qualities (proposal):** every Exam Point and Error Register Point needs a *how* (a step, formula or mini-example) or it is cut ("gyaan test"); "Author Says" asides only from Pranav's own words; [RANK] stars on extra depth; a "starting late: bare minimum" box per unit; three reading routes in the front matter (30 minutes, 3 hours, full read); mnemonics always with their trigger question.
- **Source authority:** ICAI decides rules, definitions, numbers and references. Pranav's lecture and notebook decide story, example, emphasis and order. Question Bank data decides what is examined and how often. Anything an agent invents is labelled agent draft.

## 7. Handwritten style (**proposal**, to be proven in the pilot)

- **Look:** a hand-drawn feel like Excalidraw: handwriting font, wobbly boxes, arrows, underlines, circled exam points, on a **plain background** (see section 21; ruled paper rejected for reading pages). Real text, not images, so it stays searchable and editable.
- **How:** HTML and CSS, with a small vendored library for sketchy borders if CSS alone is not enough. The existing AS 26 prototype already has the ruled-paper idea, but its font (Comic Neue) is named and **not shipped inside the file**, so it falls back unpredictably on other machines.
- **Fonts:** vendored locally (the repo rule; binaries not in git, fetched by a script like `tools/fetch_local_fonts.py`). Excalidraw's own font is open source. Candidates to compare in a one-page **font bake-off** before the pilots start: Excalifont, Kalam, Patrick Hand, Caveat.
- **Readability caution:** long paragraphs in a handwriting font tire the eye in print. Option: the handwriting font everywhere at 16px or larger, with a very legible handwriting face for body text and tables. The bake-off will show it on a real page.
- **Pictures:** HTML/CSS diagrams first; SVG for pictures that need it (small, hand-drawn style, inline text, not photos); photos stored outside git (R2 plus an asset manifest).
- **Photos found on Google:** they are third-party copyright. For a distributed book we need a licence, your own photo, or an openly licensed one (e.g. Wikimedia Commons with attribution). Otherwise draw it. (**Open decision**, see section 12.)

## 8. Pipeline (reuses the Question Book chain)

1. **`build_icai_refs.py`** (script): reads the `_BEAUTIFIED.md` files → `icai_refs.json` (item ID, entity, edition, owning topic, ambiguities flagged). A small model checks entity names.
2. **`build_importance.py`** (script): chips from the topic map and question index.
3. **Unit files** (authored).
4. **`validate_units.py`** (script): unique IDs; every topic covered or explicitly excluded; every ICAI item in the registry appears in its unit and every reference resolves; every Exam Point has a "how"; no figure without a source; every story has a source tag; no `agent-draft` in a release; HTML well-formed.
5. **`generate_unit_book.py`** (script) → chapter HTML, handwritten theme, from `book-style.json`.
6. Front matter, ToC, coverage matrix, merge, page numbers, round-trip QA: adapt the Question Book scripts.

## 9. Phases

| Phase | What |
|---|---|
| **0. Prepare** | Settle the open decisions; font bake-off; build steps 1, 2 and a validator skeleton; make the notebook pages readable to a session (section 10) |
| **1. Three pilots in parallel** (Internal Reconstruction, AS 10, AS 29) | Each pilot produces the whole unit file: skeleton (concepts, cards, error register, linkages) **plus** stories from whichever of notebook or transcript can be read. Record per pilot: tokens and time used, defects found, what a cheaper tier could have done. These numbers decide how to scale within the weekly and monthly limits |
| **2. Review and fix the template** | Pranav reviews the three units; the template, validator and prompts are corrected before scaling |
| **3. Scale by family** | Family spine first, then the unit agents in parallel, in priority order (exam frequency from the story bank: AS 21 15×, AS 14 14×, AS 3 13×, Branch 13×, AS 13 13×, Buyback 12×) |
| **4. Linkages and whole-book pages** | Cross-unit links, coverage matrix, reading routes, last-day pages |
| **5. QA and print** | Round-trip diff, visual check of every layout, page numbers |

Stories depend on notebooks and transcripts, the slowest dependency, so **a unit can be released in skeleton form and gain stories later**; stories never block completeness.

## 10. Sources for the pilots: what exists and what is blocked

**Drive** (class-notes folder, found by search):

| Pilot | NB01 | NB02 |
|---|---|---|
| Internal Reconstruction | `P01 NB01C Ch 14 Internal Reconctruction.pdf` (about 15 MB, modified 2026-11-11) | not found |
| AS 10 | `P01 NB 01 AS 10 Property Plant & Equipments` (about 42 MB) | `P01 NB 02 AS 10 …` (about 9 MB) |
| AS 29 | `P01 NB 01 AS 29 PROVISIONS CONTIGENCIES` (about 12 MB) | `P01 NB 02 AS 29 …` (about 4 MB) |
| AS 2 (if chosen) | `P01 NB 01 AS02 Inventories` (about 27 MB) | `P01 NB 02 AS 02 Inventories` (about 13 MB) |

These are scanned handwriting with no text layer (earlier finding). A session cannot save a Drive file to disk, only receive its content in chat, so the practical routes are: **(1) you attach the PDFs (or page ranges) in chat** and I read the pages visually; or **(2)** a one-time GitHub Action (the Drive and R2 secrets already exist for the archive workflows) renders the pilot notebooks to page images in R2, and a session gets read access. Route 1 is enough for three pilots.

**Transcripts:** the repo's record says lecture video and audio are in R2 but **bulk transcription was never run** (the transcription workflow has 3 runs, none successful), and it was gated on your quality approval of a 5-minute test. If transcripts have since been made, tell me the R2 path; a session also needs R2 read access.

**ICAI text and the existing teaching notes** are in the repo (Internal Reconstruction's trap notes are done; AS 10 and AS 29 need the traps pass).

## 11. Working in parallel on GitHub

- **Lane = one unit file.** An agent writes only its own unit file (and its session note). Shared files (schema, template, style, indexes, scripts, family spines) are changed only by the integrator.
- **Branch per lane** (`cb/<unit>`), small commits, never force-push, never delete branches. **Done = `validate_units.py` passes for that unit** and the session note is written.
- **Session notes:** each lane writes `docs/sessions/YYYY-MM-DD-<unit>.md`; the integrator adds one line per lane to `_claude/memory/project_log.md` (avoids the log merge conflict).
- **Prompts as files** in `agent-prompts/`, one per role, complete enough for a cold start.
- **Review queue for Pranav:** a generated page per unit listing what is stable, what is unsure, and what needs his story or his decision.
- **Status without a hand-kept board:** a script reads each unit's front matter (`status`) and prints the table.
- **Who runs what:** I can start the sessions once the pilot prompts are ready. Costs are governed by your weekly and monthly limits; pilot measurements (section 9) set the batch size.
- **The repo is public** (confirmed: the unauthenticated GitHub API returns it). Everything committed is world-readable, including draft stories. Pranav has said this is acceptable.

## 12. Which AI does what (cheapest tier that does the job)

**Scripts first:** the registry, importance, validators, rendering, merge, matrices, ID checks, and **every number** (recomputed in a script).

| Tier | Work |
|---|---|
| Small / cheap (Haiku-class or an open model) | Check entity names, IDs and links; format notebook-reading output; build source inventories; house-style lint |
| Mid (Sonnet-class) | Read a notebook page or transcript and extract story beats (with page or timestamp); write unit skeletons from ICAI text; draft illustration cards; propose linkages. Output lands as `agent-draft` |
| Top (Opus-class) | Template and schema; family spines; the traps pass on hard units; resolving ICAI-vs-lecture conflicts; final review before a unit goes to Pranav |
| Pranav | Approves stories and voice; says what counts as an exam point; flips status to `pranav-approved` |

**Verification:** the agent that wrote a unit never signs it off; numbers come from a script; anything read from a scan or transcript carries its locator; unclear means `needs_pranav`, never a guess; agents write to disk early; the orchestrator checks the first batch of any new lane in full.

## 13. Existing drafts

`chapters/seq03-framework.md` and `seq04-as02-valuation-of-inventories.md`: the file names carry the **teaching-sequence number** (sequence 3 = Framework, sequence 4 = AS 2), not "chapters 2 and 3". Both are story-first drafts with an invented cast (Rolly, Sethji, Gurpreet Sir and others) and a fixed Story / Concept notes / Illustration guide / TYK guide / One-liners layout. With "real class stories first", the invented stories become a fallback only; their concept notes can be mined. AS 2 is why I would pick AS 10 as the second pilot (no draft, 16 illustrations, a clean test) and rebuild AS 2 later as the "convert an existing draft" case.

## 14. Known gaps and risks

- No transcripts in the repo and no readable notebook text (section 10).
- ICAI page numbers are unchecked against the PDFs; topic joins can be off by one page.
- About 35% of ICAI items have no company name, so references fall back to a person or label.
- Duplicate chapter code: Cash Flow is both `M1-C4-U2` (AS 3) and `M3-C11-U2`; they are separate units that must cross-link.
- Edition change breaks references (mitigated by the edition stamp and validator).
- Handwriting fonts hurt long-text readability in print (bake-off).
- Usage limits, not money, are the real constraint on how many parallel sessions run.

## 15. Open decisions

1. **Second pilot:** AS 10 (my pick) or AS 2?
2. **Notebooks:** will you attach the pilot NB PDFs in chat (or page ranges), or shall we set up the Action and R2 access? Where is the NB02 for Internal Reconstruction, if one exists?
3. **Transcripts:** have they been generated? Where in R2? If not, approve the transcription QA step so it can start.
4. **Photos:** use only licensed, own, or openly licensed photos, and draw the rest, or accept the copyright risk of Google images?
5. **LDR:** is it Hard renamed, or a separate last-day flag?
6. **Sample card:** is the framework and layout in section 5 what you meant?
7. **Landing work:** branches plus pull requests that you merge, or direct commits to `main` with one-file-per-agent ownership?

## 16. Chapter sequence (superseded by Pranav's real sequence, below)

This is `teaching_sequence` from file 1, which is the order the repo already uses. Pranav's own notes may differ; **the book will follow whatever order he confirms.** The last column is only a hint: the date the notebook PDF was uploaded to the Drive class-notes folder (not a teaching date; my search was partial, and "not seen" means I did not find one).

| Seq | Unit | Unit ID | Topics | Drive notebook date (hint) |
|---|---|---|---|---|
| 1 | Introduction to Accounting Standards | `M1-C1-U0` | 14 | - |
| 2 | Applicability of Accounting Standards | `M1-C3-U0` | 2 | Oct 22 (notes) |
| 3 | Framework | `M1-C2-U0` | 11 | Sep 26 |
| 4 | AS 2 | `M2-C5-U1` | 15 | Jul 20 |
| 5 | AS 10 | `M2-C5-U2` | 10 | Jul 28 |
| 6 | AS 26 | `M2-C5-U6` | 27 | Jul 31 |
| 7 | AS 16 | `M2-C5-U4` | 12 | Aug 4 (NB02) |
| 8 | AS 19 | `M2-C5-U5` | 10 | not seen |
| 9 | AS 28 | `M2-C5-U7` | 19 | Aug 8 |
| 10 | AS 13 | `M2-C5-U3` | 10 | not seen |
| 11 | AS 29 | `M2-C6-U2` | 20 | Aug 25 |
| 12 | AS 15 | `M2-C6-U1` | 12 | Aug 29 |
| 13 | AS 4 | `M2-C7-U1` | 6 | Aug 31 |
| 14 | AS 5 | `M2-C7-U2` | 5 | Sep 1 |
| 15 | AS 11 | `M2-C7-U3` | 13 | Sep 12 |
| 16 | AS 9 | `M2-C8-U2` | 10 | Sep 3 |
| 17 | AS 7 | `M2-C8-U1` | 11 | Sep 7 |
| 18 | AS 12 | `M2-C9-U1` | 10 | Sep 8 |
| 19 | AS 22 | `M2-C7-U4` | 10 | Sep 16 |
| 20 | AS 20 | `M1-C4-U5` | 12 | Sep 23 |
| 21 | AS 1 | `M1-C4-U1` | 6 | Oct 23 (notes) |
| 22 | Ch 11 Unit 1, Preparation of Financial Statements | `M3-C11-U1` | 6 | Oct 2; Nov 9 (divisible profit) |
| 23A | Ch 11 Unit 2, Cash Flow Statement | `M3-C11-U2` | 7 | Oct 7 |
| 23B | AS 3, Cash Flow Statement | `M1-C4-U2` | 11 | Oct 6 |
| 24 | AS 17 | `M1-C4-U3` | 13 | Nov 1 |
| 25 | AS 18 | `M1-C4-U4` | 8 | Nov 5 |
| 26 | AS 24 | `M1-C4-U6` | 10 | Nov 6 |
| 27 | AS 21 | `M2-C10-U1` | 18 | Nov 9 (slides) |
| 28 | AS 23 | `M2-C10-U2` | 10 | not seen |
| 29 | AS 27 | `M2-C10-U3` | 13 | not seen |
| 30A | Ch 13 Amalgamation of Companies | `M3-C13-U0` | 7 | Nov 11 (one notebook with 30B) |
| 30B | AS 14 | `M2-C9-U2` | 14 | Nov 11 |
| 31 | AS 25 | `M1-C4-U7` | 15 | Nov 9 |
| 32 | Ch 12 Buyback | `M3-C12-U0` | 2 | Nov 11 |
| 33 | Ch 14 Internal Reconstruction | `M3-C14-U0` | 8 | Nov 9, updated Nov 11 |
| 34 | Ch 15 Branches incl. Foreign Branches | `M3-C15-U0` | 13 | not seen |

Things the Drive dates suggest, for checking (not conclusions): AS 11 was uploaded after AS 9, AS 7 and AS 12 though the index puts it before them; the AS 3 notebook (Oct 6) is before Ch 11 Unit 2 (Oct 7) though the index lists Cash Flow Ch 11 first as 23A; AS 25 (Nov 9) is before Ch 13 / AS 14 (Nov 11) though the index puts it after; Ch 13 and AS 14 share **one** notebook.

## 17. Stories that run across chapters (**proposal**)

A story is not owned by a chapter. Three objects:
- **Thread:** a story that runs through several units (e.g. Arjun Ltd and Bhim Ltd across the restructuring and consolidation units). One file per thread in `content/_threads/`, written first by a strong model: the cast, the arc, and **which unit carries which beat**, with forward and back links ("continued in M2-C10-U1").
- **Beat:** the part of a thread that lives inside one unit file, written by that unit's agent. Each beat names its thread, its position, and the beats before and after.
- **Standalone story:** a story used in one unit only.

Because each unit still has one agent, threads are planned up front and each unit writes only its own beats. The validator checks that every beat listed in a thread exists in its unit, that links resolve both ways, and that every story or beat carries a source tag (lecture, notebook, or agent draft). Real class stories come first; where the thread file proposes a beat that Pranav did not tell in class, it is marked agent draft.

## 18. One-page summary per chapter (**proposal**; separate PDFs, not part of the book: Pranav, 2026-11-13)

**Goal (Pranav):** every concept of the unit on literally one page, in one single-page PDF; A3 for big units; maximum use of space; creative layout.

- **Content rule:** every topic ID of the unit must appear on the page (the validator checks it), with its exam points, the key formula or flow, and the memory line. It is a summary of the unit file, not new content.
- **Authoring:** a strong model writes a one-page **spec** from the unit file (blocks, each with topic IDs, priority and a type: flowchart, comparison table, timeline, formula strip, memory line, mini-diagram, trap box). Pranav reviews the spec and the result.
- **Layout and fitting (script):** HTML/CSS grid in the handwritten theme, rendered in headless Chrome. The script **measures** the page: it scales the type to fill the printable area (target at least 92% used), enforces a **minimum type size**, and checks the PDF has **exactly one page**. If it cannot fit above the minimum, it moves from A4 to **A3**, and if even A3 fails it lists what must be cut or merged. I will not shrink type below a readable size to meet the one-page rule.
- **Likely A3 units** (my forecast from topic count; the script decides): AS 26 (27 topics), AS 29 (20), AS 28 (19), AS 21 (18), AS 25 (15), AS 2 (15), AS 14 (14), Intro to AS (14).
- **Files:** **separate PDFs handed out on their own; they are not merged into the book** (the book may point to them). HTML source in git; the PDFs are binaries, so they go to R2 with an entry in the manifest (repo rule), one per unit. A split unit (Intro to AS, Ch 11 Unit 1) gets one one-pager, not two.
- **Honest limit:** handwriting fonts are less legible at small sizes. Dense one-pagers may need a more legible handwriting face than the body text; the font comparison covers this.

## 19. One ecosystem with the website (**proposal**)

**What already lines up:** Must Practice data files are named by the same unit IDs (`M1-C1-U0.json` … `M3-C15-U0.json`), the topic map is keyed by `unique_topic_id`, the Question Bank uses `final_chapter` in the same format, and the Anatomy pages use the same index. So the join key already exists: **unit ID and topic ID**.

**Proposal: a generated registry, `ecosystem_links.json`**, one entry per unit with: concept-book page, one-page PDF, Must Practice unit, Question Bank chapter book, Anatomy page, slides. Both builds read it, so neither hand-writes a link.
- **Concept book → website:** each unit shows "Must Practice: N questions" (count computed from the Must Practice data) with a link; each topic carries computed chips ("asked in N attempts", priority band). A small QR or short link on the one-pager points to the unit's Must Practice list.
- **Website → concept book:** the Must Practice unit page gets "Read the concept sheet" and "Download the one-pager"; the topic table links each topic to its concept section. My search found **no URL-based unit selection** in `must-practice.js`, so deep links need a small change there, and **you deploy** (a cloud session cannot).
- **Questions grow, concepts stay.** The question corpus stays the single source of questions. When you or an AI add questions, the Must Practice build and the concept book's computed counts and chips update by rebuild; **no concept text is touched**. Generated questions must carry their own provenance label (the topic map already has a `source_kind` column), kept apart from ICAI questions as the Question Book keeps examiner comments apart from author notes.
- **Edition rule (Pranav):** a new edition adds more questions, better stories and linkages. New concepts are added only when ICAI changes the syllabus. The concept book's illustration and TYK cards belong to an ICAI edition and are rebuilt only then; the practice set around them is the part that grows.

## 20. What the book covers from ICAI's practice material (**proposal**)

The aim is one place for every concept of the CA Inter syllabus, with exam-friendly handling of illustrations and Test Your Knowledge:
- **Illustrations, examples and scenario (SBQ) questions:** a full card in the framework of section 5.
- **MCQs (250):** one line each in a per-topic table: reference, the concept it tests, the trap. A full card for each would add little.
- **Theory questions (99):** what the examiner expects: the heading points to write and the keywords that carry marks, with the topic ID.
- Same rule for all: no final answers copied from ICAI; figures only where they prove the point.

### 16a. The real sequence (Pranav, 2026-11-13): `BOOK-SEQUENCE.csv`

This is the order Pranav teaches in class and recommends to students for reading **and** for revision, so it is the order of the book. It is stored in `books/ca-inter/concept-book/BOOK-SEQUENCE.csv` (38 rows, 36 units). **File 1's `teaching_sequence` is a different order and is left untouched** because the Question Bank's "Final Chapter" logic depends on it; the Concept Book reads its own order from the CSV.

- **Part A, Rules of Swimming (17 units):** AS 2, 10, 26, 16, 28, 19, 13, 29, 15, 4, 5, 9, 7, 12, 11, 22, 20.
- **Part B, Actual Swimming (12 units):** Intro to AS, Framework, Ch 11 Unit 1, Ch 11 Unit 2 (Cash Flow), AS 3, Applicability, AS 1, AS 17, 18, 24, 25, Ch 12 Buyback.
- **Part C, Group Companies and Branches (7 units):** Ch 15 Branches, Ch 14 Internal Reconstruction, AS 14, Ch 13 Amalgamation, AS 21, 23, 27.
- **Two units are taught in two parts:** Intro to AS (position 1, then position 23) and Ch 11 Unit 1 (position 20 without the divisible-profit concept, then position 30 for divisible profits and books of accounts). **One unit file, two parts**, each part placed at its slot in the book and cross-linked. The one-pager is per unit.
- **The swimming metaphor looks like a book-level thread** (rules, then actually swimming, then the group). It is Pranav's class framing; I will not write it until he tells me the story. (Open.)

## 21. Paper style and font: tested (2026-11-13)

Pranav asked whether ruled paper is a good idea because figures can look inauthentic. I built one test page with identical content on four backgrounds and four fonts and looked at it (the image was sent to Pranav in the session).

| Option | Result |
|---|---|
| Plain white | Cleanest and cheapest to print. Best for reading pages |
| Cream, no lines | Equally clean; looks friendlier on screen. In print it spends ink on a full-page tint, so use it on screen and print it white |
| **Ruled notebook** | **Rejected for reading pages.** The lines run through boxes, arrows and tables and are not aligned to the text, so figures look pasted onto the paper. This confirms Pranav's worry |
| Faint dot grid | Better than ruled, but still adds noise behind text and boxes |

**Decision (proposal):** plain white (cream on screen only); the handwritten feel comes from the **font, wobbly borders, arrows and underlines**, not from the paper. **Ruled lines only on the writing area of the Most Common Errors page.**

**Fonts:** Kalam and Patrick Hand are both easy to read at body size; **Patrick Hand is the most compact and most legible for numbers and tables**; Caveat is too tall and curly for body text but good for headings and annotations. Proposal: Patrick Hand (or Kalam) for body and tables, Caveat for headings and margin notes. All are Google fonts (open licence); vendor them locally by script (binaries are not committed).

## 22. Reading the notebooks: options evaluated (**proposal**)

Task: turn scanned handwriting (dense, tables, arrows) into text, with page references, flagged where unclear. The repo's own history shows plain OCR (Tesseract) is useless here.

| Option | Verdict |
|---|---|
| Cloudflare Workers AI | Good fit for plumbing (the pages and results can live in R2 on the same account). Its vision models are open models of modest size; **their handwriting quality on accounting notes is unproven here and I expect it to be weaker** than a frontier model. A wrong reading is worse than a flagged one. Use only if it passes the bake-off |
| GitHub Actions | **Good as the pipeline, not as the reader.** It can fetch the PDFs from Drive (the Drive and R2 secrets already exist for the archive workflows), render each page to an image, count pages, store images in R2, call a vision model, and commit only the resulting **text JSON** (never the images) to a branch. Jobs can run per notebook in parallel and resume per page |
| A frontier vision model as the reader | Best expected quality. In a Claude session it uses your usage limits; through an API it is billed separately and needs a key stored as a repo secret. Check the provider's data-retention terms for your own notes |

**Recommendation:** Actions for plumbing plus a frontier vision model for reading, decided by a **three-page bake-off** (the same pages through Workers AI, a frontier model and Tesseract, scored by Pranav). For the three pilots, attaching the PDFs in chat is enough. The Action first reports page counts so cost can be estimated before any batch.

## 23. Other AI models and GitHub features (**proposal**)

**Other models (Kimi, ChatGPT and so on) on independent tasks: yes, with conditions.**
- **Why it works:** the repo is public, so any agent can **fork and open a pull request without write access**. Each gets a role prompt, `AGENT-GUARDRAILS.md`, and one unit or one task.
- **Suitable (checkable by script):** skeleton drafts from ICAI text for one unit, entity-name and reference checks, transcript clean-up, one-pager specs, lint. **Not suitable:** anything needing Pranav's stories, family spines and threads, final review, and settling conflicts between ICAI and the lecture.
- **Guardrails:** one branch and one unit per agent; shared files off limits; no story without a source tag; no figure without a script; no invented page numbers; must run `validate_units.py` and attach the result; output is labelled `agent-draft` with the model's name.
- **Review:** every output is reviewed by a **different** model or by the validator, and by Pranav before a status flips to `pranav-approved`.
- **Calibration first:** I cannot test other vendors' models from here. Give each the same small reference task (a short unit such as Ch 12 Buyback or Applicability) and compare against the checks before assigning more.

**GitHub features:**
- **Issues** as work packets: one per unit and stage, with a checklist (sources available, steps, definition of done); labels such as `unit`, `family:B`, `stage:skeleton`, `agent:codex`, `needs-pranav`; milestones for the phases. The repo is public, so issues are public (Pranav accepts this). The existing `tools/backlog_to_issues.py` is a dry-run and BL-R02 (where issues live) is still marked undecided in `CONTEXT.md`, so I will **not create issues until Pranav says go**.
- **Pull requests** with a template (sources used and not available, provenance, scripts attached) and **Actions running `validate_units.py` and the health check on every PR** (red or green).
- **CODEOWNERS** so Pranav must approve anything under `content/`, and **branch protection** so nobody (including me) pushes to `main` directly. These settings, and Projects boards, need repo-admin rights in the GitHub UI; my GitHub tools can read and write issues and comments but not change these settings.
- **Review comments** from a second agent on the PR; Pranav's approval is the gate.

## 24. Recording how the book was made (**proposal**)

Nothing should live only in chat or in issue threads.
- **`docs/concept-book/DECISIONS.md`:** a dated decision log with Pranav's decisions in his words and the reason (what is in this plan's first table, kept up to date).
- **`docs/concept-book/PROCESS.md`:** how the book is made, in plain steps, so a newcomer can follow the pipeline end to end.
- **Per-unit `build record`** (in the unit's front matter): each stage, the agent and model tier, the prompt version, the date, the validator result, the reviewer, and the sources used and not available.
- **`agent-prompts/`:** every prompt versioned in git, with a version stamp copied into the build record.
- **Reproducibility:** generated files carry a hash of their inputs; the session notes in `docs/sessions/` are kept.
- **Issue and PR history** is useful but not the record; important decisions are copied into `DECISIONS.md`.

## 25. Replicating this for other subjects (after about a month)

Design for it now, so the pilots produce a reusable kit and not an Accounts-only build.
- **Separate the engine from the content.** The scripts, template, validator and prompts read a **`subject.yaml`** (index file, ICAI source folder, edition, unit-naming pattern, card types, the style file) instead of hard-coding Advanced Accounting.
- **Card types are configurable per subject.** Accounts has illustrations and scenario questions; Law has sections and case laws; Taxation has computations. The Accounts card framework is the first configuration, not the only one.
- **Harvest after the pilots:** a replication kit (template, prompts, guardrails, validator, checklist, the lessons) written once the three pilots are reviewed.
- **Open:** which subject is next, and whether each has a topic index of the same shape as file 1.

## 26. Questions still open

1. For the two split units, which topics belong to part 1 and which to part 2 (Intro to AS, Ch 11 Unit 1)?
2. Is the swimming framing (Part A, B, C) a class story you tell? If so, tell it to me; I will not invent it.
3. Plain white (cream on screen) with Patrick Hand or Kalam: accepted?
4. Notebooks: attach the pilot PDFs, or build the Action? Bake-off pages, and an API key if the Action is chosen.
5. Approve creating GitHub issues (public) for the units, and who sets up branch protection and CODEOWNERS.
6. Which other AI models do you have access to, and should I draft the guardrails and one calibration task for them?
