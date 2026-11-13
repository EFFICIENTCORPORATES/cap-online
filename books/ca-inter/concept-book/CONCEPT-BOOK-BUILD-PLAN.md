# Concept Book: build plan (framework, structure, AI split, multi-agent workflow)

_Draft for Pranav's review, written 2026-11-13. **Nothing in this plan is built yet.** It replaces nothing: it sits on top of `teaching-notes/CONCEPT-BOOK-DESIGN-BRIEF.md` and the two older runbooks in this folder, and changes them only where section 12 says so. Decisions marked **(Pranav)** are his own words from the 2026-11-13 session; everything else is my proposal and is marked **(proposal)**._

---

## 1. What the book is (Pranav's brief, 2026-11-13)

- A **story-and-picture book of concepts**, complementary to the ICAI study material, never a replacement. **(Pranav)**
- Each topic carries the story or picture Pranav uses in class to make the concept memorable. The stories come from his **class notebooks and lecture transcripts**; the job is to document them. **(Pranav)**
- A student who wants detail follows a **reference to the ICAI topic**, any day, in any edition. **No page numbers** (they change every edition). References use **module, chapter, unit, topic** numbers, which do not change. Illustrations are cited by **illustration number plus the entity name** ("Illustration 5, Best (Jammu branch)"). **(Pranav)**
- For every referenced illustration or question: **what concept it tests, the tricky points, the exam points**, highlighted. **(Pranav)**
- Use case: one day before the exam, read every concept and every trap in a few hours. **(Pranav)**
- It must carry the qualities of the **Strategy Book**: how Pranav speaks, his examples, the ICAI referencing, how to rank, how to revise on the last day. **(Pranav)**
- Built with AI, but **not the top model for everything**: small models for routine work, many independent agents contributing to the Git repo in parallel. **(Pranav)**

## 2. What the Question Book teaches us

I read the build runbooks (`first_run/HOW-TO-BUILD-THE-BOOK.md`, the `SKILL-question-bank-*` set), looked at a rendered chapter book (`InternalReconstruction_Question_Book.html`), and read `How-to-Read-this-Book.md`. The lessons that carry over:

| Question Book lesson | Concept Book use |
|---|---|
| **Layers.** Layer 1 hand-reviewed records (sitting HTML) → Layer 2 machine index (JSON, mechanical, no AI judgment) → Layer 3 generated chapter books → Layer 4 merged whole book. HTML/records authored once; anything recomputable lives in code. | Layer 1 = **topic cards** (authored). Layer 2 = indexes (ICAI reference registry, importance data). Layer 3 = generated chapter HTML. Layer 4 = merged book. |
| **One taxonomy key**, never a new ID scheme (the U0/U1 fight). | Join everything on the canonical `unique_topic_id` of `syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json` (e.g. `M3-C15-U0-T5`). The website, the Must Practice map and the anatomy pages already use it. |
| **Strict schema + validators.** Unique IDs, every reference must resolve, coverage checked in both directions, fail loudly. | Same for cards: every topic has a card or a stated exclusion; every ICAI illustration and TYK question appears in some card; every reference resolves. |
| **Verbatim / flag, never guess.** A flagged item is better than a confident wrong one. | A story is either "Pranav said this" (with its source) or "agent draft" (visibly labelled). Never blurred. |
| **Provenance labels** (tan "Examiner's Comment" vs pink "Author's Note"). | Same idea: ICAI rule, Pranav's class, agent addition, each shown differently (section 6). |
| **One style source** (`book-style.json` → CSS), `break-inside: avoid`, vendored fonts, headless-Chrome page numbers. | Reuse the whole print chain (`qb_common.py`, `qb_merge.py` pattern, `resolve_qb_toc_pages.py`). Do not re-derive it. |
| **Round-trip QA**: parse the finished book back to JSON and diff against the source index. | Same: extract the finished Concept Book and diff against the card set and the ICAI registry. |
| **Pilot first** (AS 2), then scale to 34 sittings with parallel agents, each self-validating, each spot-checked by the orchestrator, writing to disk early (two spend-limit stops cost nothing because of that). | Same recipe for chapters. |
| **Generated files are never hand-edited. A defect found in a distributed book goes into a change log first.** | Same; add a `SECOND-EDITION-CHANGE-REQUESTS` equivalent from day one. |
| **Known slip to avoid:** the rendered chapter title reads "Internal Reconstruction — Internal Reconstruction" (standard and chapter name repeated for non-AS chapters). | Title logic must handle chapters that have no AS number. |

**Two taxonomies exist and must not be mixed.** The Question Bank tags questions with `topic-index.json` references (`unitCode` + `subtopicRef`); the Concept Book uses file 1's `unique_topic_id`. `questions_index.json` carries `final_chapter` in file 1's chapter format (`M3-C15-U0`), so chapter-level joins work today. **Topic-level** joins already exist through `must_practice_topic_map.json/.csv`, which maps `unique_topic_id` to questions and also carries `overall_rank`, `priority_band` ("Top 50" etc.) and `pyq_allocated_marks` for every topic. That is a ready-made, deterministic **importance signal** per topic (section 6).

## 3. References without page numbers (**Pranav's rule**; format is my proposal)

**Topic reference** = file 1's ID: `M3-C15-U0-T5` ("Branch Accounts, topic 5, Accounting for Dependent Branches"). Where ICAI numbers a paragraph inside a topic, add it: `M3-C15-U0-T5 §5.2` (ICAI's own para number, stable across editions).

**Illustration / question reference** = number + entity name:

| ICAI item | Written in the book | Machine key |
|---|---|---|
| Illustration 5 (Best, New Delhi, Jammu branch) | Illustration 5, Best (Jammu branch) | `M3-C15-U0:ILL-5` |
| Illustration 1(b) | Illustration 1(b), Buckingham Bros (Nagpur) | `M3-C15-U0:ILL-1-2` (the registry key ICAI's converted file uses) |
| Example 3 | Example 3 (unnamed, XP-style data) | `…:EX-3` |
| TYK scenario Q14 | TYK Q14, Green Ltd | `…:TYK-SBQ-14` |
| TYK MCQ 5 | TYK MCQ 5 (no entity) | `…:TYK-MCQ-5` |

- **Edition stamp.** Every chapter says which ICAI edition its references follow (now: July 2026, May 2027 attempt). If ICAI renumbers, the registry is rebuilt and the validator lists every reference that no longer resolves.
- **Entity names are not unique** (many "A Ltd"). The number is the primary key; the name is the human check. Items with no entity get the first few words of the question as a label.
- **Page numbers inside the pipeline only.** To place an illustration under a topic I need a join. File 1 gives each topic's start page and the converted ICAI file gives each illustration's page, but they disagree by about one page in places (Branch Accounts: T7 is 15.44 in file 1 and 15.43 in the converted file; T10 is 15.67 vs 15.66). So the join uses page ranges **plus heading text**, and anything ambiguous is flagged for a human. Pages never appear in the book.
- ICAI topics are finer than file 1's topics in places (Branch T5 contains ICAI paras 5.1 cost, 5.2 selling price, 5.3 wholesale, and Illustrations 1 to 8). So one **topic card holds several concept blocks**, each anchored to an ICAI para.

## 4. The topic card (the building block)

One card per `unique_topic_id` (400 in total), as a small Markdown file with YAML front matter. Reader-facing sections, in this order (extends the design brief's block order; **(proposal)**):

1. **Header line:** `M3-C15-U0-T5 · Accounting for Dependent Branches · ICAI Ch 15, Edition Jul-2026` plus the importance chips (section 6).
2. **Kahaani / picture:** Pranav's class story or drawing for this concept. Provenance-tagged. Optional per card; the skeleton pass leaves it blank.
3. **In plain words:** 3 to 6 lines.
4. **Why boxes:** the doubts students actually raise, answered with the underlying identity (the brief's examples: CRR formula, net assets under merger vs purchase).
5. **Exam algorithm:** a numbered flow a student can run in the hall; a small round-number example next to any new method.
6. **Exam points (highlighted):** the lines that carry marks.
7. **Where ICAI tests it:** for each illustration/TYK item: reference (section 3), **what it tests**, **the tricky point**, **what is new** (only if new). No question text, no solution (brief; see open decision 2).
8. **Error Register Points:** wrong move → right move → why; "most common" flagged; each backed by an ICAI reference or a script-checked figure. ICAI's own inconsistencies are labelled as such.
9. **Linkages:** "You will also see this in <chapter/standard, topic ID>: one line." Verified in both places.
10. **Last-day line:** one line the student can recall in the hall (the Layer 3 idea).

Chapter level: an opening **chapter map**, the **topic-wise importance table** (reuse the Question Book's Topic-wise Marks Mapping), and a closing **last-day page**.

## 5. Source authority (unchanged from the runbooks; restated because it is the core rule)

| Decides | Source |
|---|---|
| Rules, definitions, numbers, "what ICAI says", references | **ICAI** (edition-stamped) |
| Story, analogy, example, emphasis, order he teaches in | **Pranav's lecture and notebook** (only when actually read; otherwise "needs Pranav") |
| What is examined, how often, with how many marks | **Question Bank data** (computed, never authored) |
| Strategy framing (boundary, error register, rank vs pass, last day) | **Strategy Book** (`Claude_V2.md`, `SKILL-strategy-book-*`) |
| Anything an agent proposes | Labelled **agent draft** until Pranav approves |

## 6. Highlight system and the Strategy Book's qualities

Box types, each with one colour and one label (single source: `book-style.json`, never per-file CSS):

| Box | Meaning |
|---|---|
| **Exam Point** | a rule or step that carries marks |
| **Error Register Point** (with "most common" flag) | the wrong move students make; copyable into their own register (this is the Strategy Book's "favourite strategy", Sanjeevani Booti 2) |
| **Why** | the doubt behind the rule |
| **Kahaani / Picture** | Pranav's class story or drawing, source-tagged |
| **Kaam Ki Baat** | his real professional example (existing callout type) |
| **Linkage** | where else the concept appears |
| **Agent draft** | visibly marked, removed before release |

**Importance chips are computed, not authored:** from the Must Practice topic map (`priority_band`, `overall_rank`, `pyq_allocated_marks`) and the Question Bank marks mapping ("asked in N of 15 attempts"). The reader sees at a glance what the boundary should include (the Strategy Book's MIN / MAX / RANKER idea).

**Mapping the Strategy Book onto the Concept Book** (**proposal**):
- **"Gyaan test":** every Exam Point and Error Register Point needs a *how* (a step, a formula, a worked mini-example). If it only says "be careful", it is cut.
- **"Author Says":** short first-person aside by Pranav where he has one; only from his own words.
- **[RANK] markers:** a star on the extra depth a ranker adds (edge cases, cross-chapter linkages); skippable for a pass-minded student.
- **"Starting late" box per chapter:** the bare minimum to read if time is short (the 30-minute route).
- **Front matter:** three reading routes: 30 minutes (Exam Points and last-day lines only), 3 hours (+ Error Register), full read. Plus the same Chapter-wise coverage matrix the Question Book already generates.
- **Mnemonics** always appear with their trigger question (Strategy Book rule).
- Voice: Pranav's class voice. The Strategy Book is blunt and direct; the Concept Book is conversational and story-led. They share the "older brother" warmth but not the format (`SKILL-strategy-book-voice-and-tone.md` says so explicitly).

## 7. Data model and folders (**proposal**; inspect before creating, per the production guide)

```
books/ca-inter/concept-book/
  content/
    M3-C15-U0/                     # one folder per chapter (file 1 chapter id)
      _chapter.yaml                # id, title, sequence, edition, status, story spine
      _evidence.md                 # which sources exist for this chapter, and what could not be read
      T5.md                        # one topic card each (front matter + fixed headings)
      ...
  generated/                       # never hand-edited
    icai_refs.json                 # every ILL/EX/TYK item: key, entity, topic, edition
    importance.json                # chips, from the topic map + question index
    M3-C15-U0.html                 # chapter book
  agent-prompts/                   # one prompt file per role (like first_run/prompts)
  CONCEPT-BOOK-CHANGE-REQUESTS.md  # defect register from day one
```

Card front matter (sketch): `topic_id`, `edition`, `status` (`skeleton | story-drafted | agent-checked | pranav-approved | locked`), `sources` (list: ICAI ref / lecture file + timestamp / notebook page / agent), `open_questions`, `last_agent`. **One file per card** keeps parallel agents from editing the same lines.

## 8. Pipeline (reuses the Question Book chain)

1. **`build_icai_refs.py`** (script, no AI): reads the `_BEAUTIFIED.md` files → `icai_refs.json` (ILL/EX/TYK ids, entity name, edition, owning topic by page range + heading match, ambiguities flagged). Entity extraction is heuristic; a small model checks the output.
2. **`build_importance.py`** (script): chips from the topic map and question index.
3. **Cards** (authored; sections 9–10).
4. **`validate_cards.py`** (script): unique IDs; every topic has a card or exclusion; every ICAI reference in `icai_refs.json` appears in at least one card and every reference in a card resolves; every Exam Point has a "how"; no number without a source; no `agent draft` in a release; provenance present; HTML well-formed.
5. **`generate_chapter_book.py`** (script) → chapter HTML (style from `book-style.json`).
6. Front matter, ToC, coverage matrix, merge, page numbers, round-trip QA: adapt the existing Question Book scripts.

## 9. Build phases

| Phase | What | Why this order |
|---|---|---|
| **0. Decide** (this week) | Answer the open decisions (section 12); freeze the card template and reference format; build steps 1–2 and the validator skeleton | Cheap to change now, expensive after 400 cards |
| **1. Pilot one chapter end to end** | One chapter, full depth: skeleton → story → render → Pranav review → print preview | Surfaces template flaws on 8 to 12 cards, not 400. Recommended pilot: **Internal Reconstruction** (8 topics, 8 illustrations, trap notes already done) unless you want another |
| **2. Skeleton pass, all 36 chapters, in parallel** | Every topic: plain words, exam points, "where ICAI tests it" (what tested, tricky point), error-register points, linkages. **No stories yet.** | The book becomes complete and useful on its own (the one-day-before use) even if time runs short. Stories need Pranav's transcripts and notebooks, which are the slowest dependency; they must not block completeness |
| **3. Story pass, in priority order** | Add Pranav's real stories and pictures from transcripts/notebooks, highest-frequency chapters first (the story bank lists exam frequency: AS 21 15×, AS 14 14×, AS 3 13×, Branch 13×, AS 13 13×, Buyback 12×) | Spend his review time where marks are |
| **4. Linkages and whole-book pages** | Cross-chapter links, coverage matrix, three routes, last-day pages | Needs most chapters to exist |
| **5. QA and print** | Round-trip diff, visual check of every layout, page-number resolution | Same as Question Book |

The skeleton-first order is a trade-off against "storybook first". If you would rather see the story layer first in the pilot, say so; the structure supports both.

## 10. Which AI does what (cheapest tier that does the job; EC rule)

**Scripts first.** Anything deterministic is code, not a model: the ICAI registry, importance chips, validators, rendering, merge, coverage matrix, ID checks, and **every number** (recomputed in a script, never by a model's mental arithmetic).

| Tier | Examples of work | Notes |
|---|---|---|
| **Small / cheap** (Haiku-class or an open model) | Check extracted entity names; cross-check IDs and links; format transcript chunks; build per-chapter `_evidence.md` inventories; spelling and house-style lint; fill front-matter fields from data; produce lint reports | Mechanical, checkable by a script or a second look |
| **Mid** (Sonnet-class) | Read a transcript or notebook page and extract teaching beats (story, example, emphasis, timestamp); write skeleton cards from ICAI text; per-illustration "what is tested / tricky point" drafts; Error Register candidates from the teaching notes; linkage candidates | The bulk of the volume. Output always lands as `agent draft` and goes through the checks below |
| **Top** (Opus-class) | Template and schema decisions; chapter story spines and cross-chapter linkage design; the traps pass on hard chapters (consolidation, amalgamation, cash flow, foreign branches); settling conflicts between ICAI and the lecture; final review before a card goes to Pranav | Few calls, high stakes |
| **Pranav** | Chooses chapters; approves stories and voice; decides what counts as an exam point; flips status to `pranav-approved` | His time is the scarcest resource, so cards reach him in a batched review page (section 11) |

**Verification rules** (**proposal**, from the Question Book's failures):
1. The agent that writes a card never signs it off; a different agent (or a script) checks it.
2. Numbers: recomputed by a script in the scratchpad; the script's output is attached to the card's sources.
3. Anything read from a scan or transcript carries its locator (page or timestamp). Unclear → `needs_pranav`, never guessed.
4. Every agent writes partial work to disk early (the Question Book survived two spend-limit stops because of this).
5. Orchestrator spot-checks a sample of each agent's output before it is trusted; the first batch of any new lane is checked in full.

## 11. Working in parallel on GitHub

**Why it can work:** one file per card, a fixed template, scripts that check, and clear ownership. **Where it breaks:** shared files and the known `project_log.md` conflict.

- **Lanes, by path:** an agent writes only inside its assigned `content/<chapter>/` folder. Shared files (schema, template, style, indexes, scripts) are read-only to lane agents; only the integrator changes them.
- **Work packets:** a generated list (`tools/concept_book_status.py`) of cards by status per chapter, so claiming work needs no hand-kept board. A packet is "chapter X, stage Y, N cards".
- **Branches:** one branch per lane, `cb/<chapter>/<stage>`, small commits. Never force-push, never delete branches (existing rules).
- **Done = validator passes** for that chapter and the lane's session note is written. Lane agents commit **sources only**; the integrator regenerates `generated/`.
- **Session notes:** each lane writes `docs/sessions/YYYY-MM-DD-<chapter>-<stage>.md`; the integrator rolls the one-line summaries into `_claude/memory/project_log.md`. This avoids the log merge conflict every parallel session hits.
- **Prompts as files:** one per role in `agent-prompts/` (inputs, outputs, the checks to run, the "do not" list, how to report what could not be read), modelled on `first_run/prompts/`.
- **Review queue for Pranav:** a generated HTML page per chapter listing cards by status with what changed and what is unsure, so he reviews many cards fast (a phone is enough).
- **Starting agents:** I can start parallel cloud sessions, each with one lane prompt, once you approve the cost. Each starts cold, which is why the prompts must be complete.
- **Landing work:** the repo says "branch + PR" but you decide on PRs and merges yourself. Open decision 6.

## 12. Differences from earlier documents (to be settled)

| Earlier document | Said | Now |
|---|---|---|
| Design brief §1, §2 | Cite chapter, number **and printed page**; no answers | Pranav: **no page numbers**; the module-chapter-unit-topic key plus illustration number and entity name. (Proposal: update the brief.) |
| Production guide §1, §5 | Selected question **with stepwise solution** after each concept | Brief says no solutions; Pranav's message mentions "questions and answers" with tricky and exam points (open decision 2) |
| Production guide / pipeline | Handwritten-style HTML, Excalidraw vectors, vector illustrations | `CLAUDE.md`: no SVG unless asked; HTML/CSS diagrams are fine (open decision 5) |
| Existing chapters `seq03`, `seq04` | Story first, then notes, then illustration guide, then one-liners | The topic card puts the story *inside* each topic and adds references, error register and linkages. They would be rebuilt as cards (open decision 7) |
| Pipeline §11 | Colour roles for handwritten notes (blue, red, green) | Replaced by the box types in section 6 (single style file) |

## 13. Known gaps and risks

- **No transcripts exist** in the repo (the bulk-transcription workflow never succeeded; the gate needs Pranav's quality approval). **NB01/NB02 have no text layer**, and the only OCR is garbled Tesseract output of one CollaNote notebook (Framework). So stories cannot be documented until these are provided or produced. That is the critical path for phase 3.
- **I cannot read R2 from a cloud session** (no credentials), and Drive returns nothing for scanned notebooks.
- **ICAI page numbers are unchecked** against the PDFs; topic joins can be off by one page.
- **Topic granularity:** ICAI paras are finer than file 1's topics; Branch Accounts is the example. Cards need sub-anchors.
- **Duplicate chapter code:** Cash Flow exists as `M1-C4-U2` (AS 3) and `M3-C11-U2`; cards must cross-link rather than duplicate (as Must Practice does with pointer units).
- **Edition change** (ICAI renumbers) breaks references; mitigated by edition stamp plus registry rebuild plus validator.
- **Timeline:** about 400 topics. The skeleton-first order protects completeness; stories are the part at risk.

## 14. Open decisions for Pranav

1. **Pilot chapter.** Internal Reconstruction (recommended: notes ready), or Branch Accounts, or another?
2. **Answers.** Per illustration: only "what it tests + tricky point + exam point", or also the final figure as a self-check (e.g. "profit 15,000")? Final answers copy ICAI; I recommend tricky points only.
3. **Reference format** in section 3 (number + entity, `§` para anchors, edition stamp): approved?
4. **Transcripts and notebooks.** Where are they, and in what format? Approve the transcription QA gate? May an AI read notebook scans visually (page images)? Can R2 credentials be given to a session, or will you attach files?
5. **Pictures.** Your notebook drawings, new drawings, or generated images? Stored in R2 with an asset manifest (no binaries in git); HTML/CSS diagrams only unless you approve SVG.
6. **Landing work.** Branch per lane plus pull requests that you merge, or direct commits to `main` with path ownership? Should task tracking use public GitHub issues (the repo is public) or only the generated status list?
7. **Existing drafts** (`seq03`, `seq04`, AS 26 sheet): rebuild as cards, or keep as a separate story layer?
8. **Stories.** Real class stories (from transcripts) first, with the fictional universe (Rolly, Sethji, Arjun, Gurpreet Sir, Diya) only where no class story exists?
9. **Language.** English with Hinglish lines as in class, or English only?
10. **Agents and budget.** May I start parallel cloud sessions (cost), and is there a spending cap?
