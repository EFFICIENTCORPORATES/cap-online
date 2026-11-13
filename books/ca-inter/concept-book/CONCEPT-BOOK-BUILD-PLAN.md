# Concept Book: build plan (revision 2, 2026-11-13)

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
| Illustration framework | Goal → Concepts triggered → Given → How it is solved → Exam points → Tricky points (the **Error Register / Sanjeevani Booti**); figures where they matter, wording where the concept is the wording |
| Difficulty | **Easy / Medium / Hard** per illustration; "Hard" may later be renamed **LDR** (last-day-revision) |
| Stories | **Real class stories first** |
| Language | **English only** (tips too) |
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
6. **Error Register:** written inside topics and cards; **collected by a script** into one page per unit (Sanjeevani Booti 2), so each point is written once.
7. **Last-day page:** generated from the last-day lines.

### Illustration card (Pranav's framework)

Fields, in this order: **Reference** · **Difficulty** (computed) · **Goal of the question** · **Concepts triggered** (topic IDs) · **Given** · **How it is solved** (the approach in a few steps, with figures where they prove the point) · **Exam points** · **Tricky points** (these are the Error Register entries: wrong move → right move → why).

**Sample (illustrative only; recomputed with a script; Branch Accounts is not a pilot chapter):**

> **Illustration 5, Best (Jammu branch)** · `M3-C15-U0:ILL-5` · Medium (3 concepts)
> **Goal:** the branch's profit for the year, and the stock reserve for unrealised profit.
> **Concepts triggered:** goods invoiced at cost + loading (`T5 §5.2`); stock reserve on closing stock (`T5 §5.2`); branch Trading A/c at invoice price (`T5 §5.1`).
> **Given:** invoice price = cost + 20%; sale price = cost + 50%; opening stock ₹2,20,000 and goods sent ₹11,00,000 (both at invoice price); sales ₹12,00,000; expenses ₹45,000.
> **How it is solved:** (1) three prices per ₹100 of cost: cost 100, invoice 120, sale 150. (2) Goods sold at invoice price = 12,00,000 × 120/150 = 9,60,000. (3) Closing stock at invoice price = 2,20,000 + 11,00,000 − 9,60,000 = 3,60,000. (4) Branch trading at invoice price gives profit 1,95,000. (5) Reserve = 3,60,000 × 20/120 = 60,000.
> **Exam points:** the loading fraction is margin ÷ invoice price (20/120), not the 20% markup; closing stock is derived, not given.
> **Tricky points (Error Register):** *Wrong:* reserve = 20% × 3,60,000 = 72,000. *Right:* 20/120 → 60,000. *Why:* the 20 is inside the 120. — *ICAI's 1,95,000 is the branch's profit at invoice price; the business's profit adds the loading realised on goods sold (1,60,000) to make 3,55,000. ICAI does not say this; my reconstruction.*

**Difficulty is computed**, not authored: by the Question Bank's rule (up to 2 concepts triggered = Easy, 3 to 5 = Medium, over 5 = Hard), with the labels in the style file so renaming "Hard" to "LDR" is one edit. (**Open:** is LDR just Hard renamed, or a separate "solve this on the last day" flag chosen from all difficulties?)

## 6. Highlights, importance and the Strategy Book

Box types, one colour and one label each, defined once in the style file:
**Exam Point · Error Register Point (with "most common") · Why · Story / Picture · Kaam Ki Baat · Linkage · Agent draft (removed before release).**

- **Importance chips are computed:** from the Must Practice topic map and the Question Bank marks mapping ("asked in N of 15 attempts"), so a student sees at a glance what a boundary should include (MIN / MAX / RANKER).
- **Strategy Book qualities (proposal):** every Exam Point and Error Register Point needs a *how* (a step, formula or mini-example) or it is cut ("gyaan test"); "Author Says" asides only from Pranav's own words; [RANK] stars on extra depth; a "starting late: bare minimum" box per unit; three reading routes in the front matter (30 minutes, 3 hours, full read); mnemonics always with their trigger question.
- **Source authority:** ICAI decides rules, definitions, numbers and references. Pranav's lecture and notebook decide story, example, emphasis and order. Question Bank data decides what is examined and how often. Anything an agent invents is labelled agent draft.

## 7. Handwritten style (**proposal**, to be proven in the pilot)

- **Look:** a hand-drawn feel like Excalidraw: handwriting font, ruled-paper background, wobbly boxes, arrows, underlines, circled exam points. Real text, not images, so it stays searchable and editable.
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
