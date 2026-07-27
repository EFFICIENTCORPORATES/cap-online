# Reusable prompt: tag one exam sitting to syllabus chapters/topics

Copy everything in the code block below into another AI model that has repo
access. **Only one thing changes between runs: the `SOURCE FILENAME` line** —
everything else (which sitting this is, paper type, the matching answer file,
the output filename) is derived automatically from that one filename, per the
repo's established naming conventions. Written 2026-07-23 for the `cap-online`
repo (CA Inter Advanced Accounting question bank).

---

```
You are tagging every question in one CA Inter Advanced Accounting exam paper
("sitting") to the syllabus chapter(s)/topic(s) it actually tests. This is one
sitting out of ~37 in a larger question bank; your output must match an exact,
already-established format so it can be combined with the others later.

SOURCE FILENAME (the only thing that changes between runs): {{e.g.
  "CAInter-AdvAcc-MTP-Nov2023-Set1-Q.md"}}

STEP 0 - WORK OUT EVERYTHING ELSE YOURSELF FROM THAT ONE FILENAME:
- First check whether a cleaned version already exists in
  `books/question-bank/Parsed_PDF_Question_Bank_CA_Inter_Accounts/` (named
  `parsed-{MTP|PYQ|RTP}-{Session}[-SetN].md`) - if it does, read that instead,
  it's cleaner (HTML tables already fixed up). Only 3 sittings have one so far
  (MTP May2024 Set1, PYQ Jan2026, RTP May2026) - for everything else you'll be
  reading directly from `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/`.
- Parse the filename: `CAInter-AdvAcc-{MTP|PYQ|RTP}-{Session}[-SetN]-{Q|Ans}.md`
  tells you paperType, session, and set. E.g.
  `CAInter-AdvAcc-MTP-Nov2023-Set1-Q.md` = MTP, session "Nov 2023", Set 1.
- Find the matching file in the SAME folder as the one you were given, and
  ALWAYS read both question and answer content - never tag from one side alone:
  - **MTP**: separate `-Q.` and `-Ans.` files - both REQUIRED, they are not
    redundant. Verified: the `-Q.` file has only question text; the `-Ans.` file
    has only answers/option-letters, it does NOT repeat the question at all. Your
    `mdAnchor` (see schema below) should point into the `-Q.` file, since that's
    where the actual question wording lives.
  - **PYQ**: most sittings now only have an `-Ans.` file (the `-Q.` file was
    deprecated - it converted blank/scanned in every case). Verified: this
    `-Ans.` file DOES embed the full question text before each answer (look for
    "Question 1", "Question 2" etc. plain-text markers followed by the full
    question, then the answer) - so one file has everything here. If you were
    given a PYQ filename and there's no matching `-Q.` file, that's expected -
    proceed with just the `-Ans.` file, your `mdAnchor` points into it.
  - **RTP**: single combined file (named with `-Q.` even though it has
    announcements + questions + suggested answers all together) - nothing else
    to find, your `mdAnchor` points into that one file.
- Output filename: `{PaperType}_{Session}[_SetN].json` with no spaces, e.g.
  `MTP_Nov2023_Set1.json`, `PYQ_Sep2024.json`, `RTP_Jan2025.json` - save it to
  `books/question-bank/metadata-index/`.

BEFORE YOU START, READ THESE FILES IN THIS ORDER (all in the same repo):
1. `books/question-bank/metadata-index/TAGGING-SCHEMA.md` - the full schema spec,
   field-by-field rules, and the U0/U1 convention (use U0 for single-unit chapters
   - this was migrated from U1 on 2026-07-23, U0 is now correct everywhere).
2. `books/concept-book/syllabus-engine/data/1-ca-inter-adv-accounts-topic-page-index.json`
   - THE canonical list of all 36 chapters and 400 topics, with exact topic numbers,
   topic names, and ICAI study-material page numbers. Use THIS file's `unique_chapter_id`
   and `topic_no` values - do not invent your own numbering.
3. `books/question-bank/metadata-index/topic-index.json` - the working reference
   index questions are actually tagged against. It has richer per-topic descriptions
   for the ~32 chapters already documented there, but is missing some chapters
   (compare against file 2 above to check) and some of its page numbers are stubs.
4. One already-completed example for the exact output shape you must produce:
   `books/question-bank/metadata-index/MTP_May2024_Set1.json`
5. Check `books/question-bank/question_bank_index_by_attempt.csv` to confirm the
   sitting you were given isn't already tagged (skip it if it is).

WHAT "TAGGING A QUESTION" MEANS:
For every question in the sitting, read it and its official answer, decide which
syllabus chapter(s) it is genuinely testing (NOT just what section header the paper
prints above it - papers sometimes mislabel this), and record a short JSON entry
pointing at that chapter/topic. You are NOT copying the question text into your
output - the question stays in the source file; your output only points at it.

EXACT OUTPUT SCHEMA (one JSON file per sitting):

{
  "_readme": "<one line: which source file(s) you read, any caveats>",
  "examSession": "<e.g. Nov 2023, Set 1>",
  "paperType": "Mock Test Paper (MTP)" | "Past Year Question (PYQ)" | "Revision Test Paper (RTP)",
  "course": "CA Intermediate - Group I - Paper 1",
  "subject": "Advanced Accounting",
  "sourceParsedFile": "<relative path to the source file(s) you read>",
  "totalMarks": <int, or null if not printed>,
  "questions": [
    {
      "id": "<PaperType-Session[-SetN]-Part-QN, e.g. MTP-Nov2023-S1-PartI-Q1>",
      "mdAnchor": "<a short, EXACT, copy-pasted snippet of text (5-10 words) from
                    right where this question begins in the QUESTION file (the
                    file that actually has the question wording - see note below)
                    - so it can be located later by a plain text search. DO NOT
                    assume markdown headings like '### Question 1' exist - they
                    only exist in the 3 already-Parsed files
                    (Parsed_PDF_Question_Bank_CA_Inter_Accounts/parsed-*.md).
                    Raw .md conversions have NO markdown headings at all, just
                    plain numbered text (e.g. '1.  Fly Ltd. made a sale of...') -
                    if that's what you're reading, your mdAnchor is that exact
                    plain-text snippet, verbatim, not an invented heading.>",
      "part": "<section/part label as printed, e.g. 'Part I - Case Scenario MCQs'>",
      "questionNumber": "<as printed, e.g. '1' or '6-9'>",
      "marks": <int>,
      "marksNote": "<optional, e.g. '4 MCQs of 2 marks each' - omit if not needed>",
      "topics": [
        {
          "unitCode": "<from file 2 above, e.g. M2-C5-U2>",
          "standard": "<e.g. AS 10, or null if the chapter has no AS number
                        (Buyback/Amalgamation/Internal Reconstruction/Branch
                        Accounting/Preparation of Financial Statements/Framework/
                        Applicability/Introduction to AS are all standard: null)>",
          "title": "<chapter title, from file 2>",
          "subtopicRef": "<the specific topic number(s) within that chapter being
                           tested, e.g. '2.7/2.8' - from file 2's topic_no, or
                           file 3's sections[].ref if the question needs finer
                           paragraph-level precision than file 2 has>",
          "subtopicTitle": "<one sentence: what specifically about this topic is
                             being tested in THIS question, not a generic chapter
                             description>"
        }
      ]
    }
  ]
}

A question with parts testing different chapters gets MULTIPLE entries in its
`topics[]` array - one per distinct chapter tested (see MTP_May2024_Set1.json's
Question 1 for a real 5-topic example, a case-scenario MCQ blending AS 9, AS 11,
AS 5, AS 21, and AS 23 across its four sub-parts).

CRITICAL RULES - DO NOT SKIP THESE:
1. Read the actual question and its answer before tagging. Do not tag from the
   paper's own section heading alone - these are sometimes wrong (one RTP question
   in this question bank was printed under an "AS 7 Construction Contracts" header
   but was actually pure AS 10 + AS 16 content).
2. Only use `unitCode` values that exist in file 2
   (`1-ca-inter-adv-accounts-topic-page-index.json`). Never invent a chapter ID.
3. If you are genuinely uncertain which chapter a question tests, or a question's
   sub-part is ambiguous between two standards, SAY SO explicitly in that topic's
   `subtopicTitle` (e.g. "uncertain - could also be AS 4, flagging for review") -
   never silently guess and present it as confident.
4. Do NOT invent or write a `commonMistakes` or `recurringGroup` field unless you
   have actually done that specific work (see TAGGING-SCHEMA.md if asked to do
   these too) - for a first-pass tagging run, omit both fields entirely rather
   than leaving empty placeholders.
5. Do not copy the question or answer text into your output JSON. Only the fields
   listed in the schema above. Content stays in the source file; `mdAnchor` is
   the link back to it.
6. Marks: use exactly what's printed in the source. If the source paper doesn't
   print marks at all (this happens in some RTPs), set `"marks": null` and say so
   in `marksNote` rather than guessing a number.
7. If a question tests a chapter not yet in `topic-index.json` (check against
   file 2 to see if it's missing there), add a stub entry to `topic-index.json`
   first (module/chapter/unit/standard/title/sourceFile, a plain heading list is
   fine, marked `"_note": "stub - headings only, not yet described"`) rather than
   tagging against a chapter that isn't indexed anywhere queryable.

WHEN YOU FINISH:
1. Validate your output is syntactically correct JSON (no trailing commas, all
   strings properly quoted/escaped, especially the rupee sign "₹" and any quote
   marks inside question text if you're referencing them).
2. Double check every `unitCode` you used actually appears in file 2.
3. Report back: which sitting you processed, the output filename you used, how
   many questions you tagged, how many topics total, and a short list of anything
   you flagged as uncertain per rule 3 above.
```

---

## Notes for whoever is running this (not part of the prompt above)

- Run this once per remaining sitting (33 as of 2026-07-23 — see
  `books/question-bank/question_bank_index_by_attempt.csv` for the full list of
  what's tagged vs not). Only the `SOURCE FILENAME` line changes each time.
- **Review the first few outputs closely before trusting a batch of them** —
  verify a `unitCode` or two against file 2 by hand, and skim for any question
  tagged with suspiciously generic `subtopicTitle` text (a sign the model tagged
  from the section header without actually reading the question). Also check
  it actually validated its own JSON (rule "when you finish" #1) rather than just
  claiming to.
