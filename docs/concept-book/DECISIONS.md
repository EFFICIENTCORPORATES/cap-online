# Concept Book: decision log

_Every decision about the Concept Book, with the date, who made it and why, so a newcomer can see how the book was shaped. Decisions by Pranav are in his words as closely as they can be summarised; agent proposals are marked as such until he accepts them. Newest section last. The working plan is `books/ca-inter/concept-book/CONCEPT-BOOK-BUILD-PLAN.md`; this file is the record of what was decided, the plan is the record of how to do it._

## 2026-11-13: what the book is

| # | Decision | Made by |
|---|---|---|
| 1 | The book is **complementary** to the ICAI study material, never a replacement. It is the single place for every concept of the CA Inter Advanced Accounting syllabus, with exam-friendly handling of illustrations and Test Your Knowledge (MCQ, theory, scenario) | Pranav |
| 2 | Use case: read all concepts and traps in a few hours on the day before the exam | Pranav |
| 3 | **Edition rule:** later editions add more questions and better stories and linkages; new concepts are added only when ICAI changes the syllabus | Pranav |
| 4 | References use **module-chapter-unit-topic IDs and no page numbers** (page numbers are hard to keep current). Illustrations are cited by **number plus entity name** | Pranav |
| 5 | Stories come from his **real class stories** (notebooks and lecture transcripts). Stories can run across chapters and across topics | Pranav |
| 6 | Language: **English**, except stories and "things to remember" (memory lines, mnemonics), which are Roman-script **Hinglish** | Pranav |

## 2026-11-13: structure and the unit of work

| # | Decision | Made by |
|---|---|---|
| 7 | The unit of work is **one file per syllabus unit (36)**, not one file per topic (400), so one agent holds the whole chapter in mind. Related units are grouped into **families** for story continuity | Pranav |
| 8 | **Pilots:** Internal Reconstruction, **AS 10** and AS 29 (three very different shapes) | Pranav |
| 9 | **Chapter order is Pranav's real teaching and revision sequence** (`books/ca-inter/concept-book/BOOK-SEQUENCE.csv`): Part A Rules of Swimming (17 units), Part B Actual Swimming (12), Part C Group Companies and Branches (7). Intro to AS and Ch 11 Unit 1 are taught in two parts. File 1's `teaching_sequence` is a different order and is not changed | Pranav |
| 10 | Intro to AS: topics 1 to 3 in part 1 (Lecture 1), topics 4 to 14 in part 2. Ch 11 Unit 1: the distributable-profit part is topic 1.6 up to Illustration 1 (agent reading, awaiting confirmation) | Pranav; reading by agent |
| 11 | The Part A / B / C "swimming" framing is the **intro to the subject, told once at the start**, not a running thread | Pranav |

## 2026-11-13: how an illustration is written

| # | Decision | Made by |
|---|---|---|
| 12 | Framework: **Goal of the question → Concepts triggered → Given → Approach → Exam points → Tricky points**; tricky points are the Error Register (Sanjeevani Booti) | Pranav |
| 13 | **Keep it short.** No number-by-number working; steps only where the order is the point; figures only for a tough calculation or when the figure is the exam point. A first sample with the full working was rejected as too verbose | Pranav |
| 14 | Each illustration has a difficulty: **Easy / Medium / Hard**; "Hard" may later be renamed **LDR** (last-day revision) | Pranav |
| 15 | Every unit ends with a **Most Common Errors** page: 4 to 14 points, with the rest of the page left blank for the student's own | Pranav |
| 16 | The **one-page summary** of each chapter is a **separate PDF** (A3 for big units), not part of the book | Pranav |
| 17 | MCQs get one line each (concept and trap); theory questions get the heading points and keywords; scenario questions get full cards (agent proposal, not yet confirmed) | Agent |

## 2026-11-13: look and feel

| # | Decision | Made by |
|---|---|---|
| 18 | **Handwritten style** (not typed), like Excalidraw. Body font Patrick Hand or Kalam, to be switched if needed | Pranav |
| 19 | **Ruled lines where there is text, plain where there is a diagram.** (A mock-up showed ruled lines running through diagrams look pasted on; so diagrams, tables and boxes sit on plain panels and the lines are used only inside text blocks, aligned to the text) | Pranav; condition from agent's test |
| 20 | **A box for each topic**, so topics are visibly separate and the page is more attractive, and **colour legends** that say what each box type means | Pranav (agent's design rules in the plan) |
| 21 | Pictures: HTML/CSS diagrams, and **SVG is allowed** for pictures; real photos can be searched later (copyright to be checked) | Pranav |

## 2026-11-13: tools and how the work is run

| # | Decision | Made by |
|---|---|---|
| 22 | The repository is **public** and that is acceptable | Pranav |
| 23 | No spending cap; work within the weekly and monthly usage limits. Parallel sessions are approved | Pranav |
| 24 | **GitHub issues are created by the agent after the pilot**, not before. Other AI models then work on those issues within the guardrails and raise pull requests; **the agent reviews them and merges those that pass** | Pranav |
| 25 | Everything about how the book is made is to be stored so others can understand the process; the same method will be **replicated for other subjects after about a month** | Pranav |
| 26 | The handwritten notes and annotated ICAI chapters are in **public** Drive folders, so their PDFs can be downloaded by anyone. A deterministic inventory (pages, sizes, what is missing) is made first (`tools/drive_notes_inventory.py`); any model can then read them with its own OCR | Pranav |

## 2026-11-13: Question Bank second edition (separate book)

Eight change requests were logged in `first_run/SECOND-EDITION-CHANGE-REQUESTS.md` (CR-009 to CR-016): chapter order, Must Practice highlighting, Sep 2026 and Jan 2027 MTP and RTP, trial balance and typo audit, remove repeated disclaimers, header and footer on every page, OP/PP tags. See that file; they are not Concept Book decisions.

## 2026-11-13 (later): writing style, Internal Reconstruction, next units

| # | Decision | Made by |
|---|---|---|
| 27 | **The book carries concepts, not examples.** ICAI already has the examples. Keep each point to the shortcut an exam needs: short fragments that still make sense, not full sentences or long paragraphs | Pranav |
| 28 | The exam-routine (numbered steps) and the linkages format are right as they are, but written as short fragments. Keep the linkages | Pranav |
| 29 | Capital Reduction A/c in Pranav's words: **credit all sacrifices (balidaan), debit what they were used for, the balancing figure is Capital Reserve.** P&L debit is written off first with the sacrifices; if still short, General Reserve. A preference dividend that was waived and never recorded needs **no entry**; if anything is issued in lieu, **debit Capital Reduction A/c** | Pranav |
| 30 | Internal Reconstruction is an easy chapter with few stories. Its stories: the Kahaani deck (slides s01 and s02), the "all stakeholders make a balidaan to save the company" framing, Sections 230 and 233 of the Companies Act, and Tata Finance into Tata Capital. Nothing else | Pranav |
| 31 | **Next units: AS 2, AS 10 and AS 29**, each with several stories to be read from his notebooks | Pranav |
| 32 | The Question Bank topic-number collision (marks on the wrong topic) is logged as CR-017; not to be fixed now | Pranav asked for a quick look only |

## Still open (as of 2026-11-13)

- Confirm the Ch 11 Unit 1 split (decision 10).
- Which untaught stories and what the "swimming" intro story says (Pranav to tell it).
- Whether LDR is Hard renamed or a separate flag.
- Photos: licensing.
- Who sets up branch protection and CODEOWNERS (needs repository-admin rights).
