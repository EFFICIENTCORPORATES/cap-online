# Important Topics explorer (`/topics/`)

Public page (no login), built 2026-09-25. One page where a student picks paper
type (PYQ / MTP / RTP), year, attempt month, module, chapter and unit, sorts any
way (with a Reverse button), and downloads the result as Excel or CSV.

| File | Role |
|---|---|
| `public/topics/index.html` | Page shell: presets, filters, list, downloads, ID explainer, glossary |
| `public/assets/topics.js` | All behaviour. Ranks in the browser, so any filter mix re-ranks instantly |
| `public/assets/topics.css` | Layout (table becomes cards under 760px) |
| `public/topics/data/topics.json` | 400 topics, 36 units, 35 sittings, 649 question-to-topic rows |
| `public/topics/data/sheets/*.json` | Pranav's six workbook sheets, verbatim, for the Excel downloads |
| `tools/build_topics_explorer_data.py` | Builds all of the above |

## Refresh

```
python tools/build_topics_explorer_data.py
npx wrangler deploy
```

Sources: `descriptive_topic_priority.json` (ranking + question-to-topic mapping),
the canonical topic/page index (`1-ca-inter-adv-accounts-topic-page-index.json`),
and `ca_inter_descriptive_topic_priority_v1.xlsx` (gitignored; only the JSON
copies are committed). The build **refuses to publish** unless the PYQ marks it
recomputes match the workbook's own figure for all 400 topics.

## How ranking works (and why it matches the workbook)

* **Marks** = the sum of `allocated_marks` over the selected papers. A question's
  marks are split equally across the topics it tests; both alternatives of an OR
  question count. Rounded to 2 places (floating-point noise otherwise reorders ties).
* **RTP has no marks** (none are printed), so an RTP-only view ranks by *times asked*.
  Mixed views therefore sum only PYQ and MTP marks; RTP adds to "times asked".
* **Ties** fall back to the workbook's own rank, which is not derivable from the
  counts. Verified: with PYQ selected and no other filter, all 104 topics with PYQ
  marks get exactly the workbook's rank.
* **Rank is global**: it is computed over all 400 topics for the chosen papers/years
  and does not change when you narrow to one chapter. Bands: 1-50 Must know,
  51-100 Important, otherwise Good to know, or Not asked yet when never asked.
* 52 question-topic rows have no Study Material topic (category D) and are left out.
* Only descriptive questions are in the data; MCQs live on the Telegram bot.

## Downloads

Excel is generated in the visitor's browser with SheetJS from cdnjs (loaded only
on the first download click, pinned to version 0.18.5 with a SHA-512 integrity
hash), so no xlsx file is stored in git. "This list" exports exactly the filtered,
sorted view. Ready-made: Top 100 (workbook sheet), MTP-wise / RTP-wise / PYQ-wise
lists (generated from the same data, every topic asked at least once), and the
workbook's Chapter Priority, Topic Attempts, Question Topic Map, A-B-C-D
Questions and Study Topics sheets. There is no "MTP-wise" sheet in the workbook;
that list is new.

Deep links: `/topics/?view=top100|mtp|rtp|all|recent|never` and `/topics/?unit=M2-C5-U2`.

## Reading a topic ID

`M2-C5-U2-T2.6` = Module 2, Chapter 5, Unit 2, topic 6 of Unit 2 (Measurement of
PPE, Study Material page 5.27 = chapter 5, page 27). `U0` = a one-unit chapter,
whose topics are `T1, T2...` without the unit prefix. Hyphens (in the site data) and
underscores (in ICAI file names and the source CSV) are the same ID. The page has a
worked example and a decoder that also explains a wrong ID (for example `M1_C5_...`
does not exist: Module 1 has chapters 1-4).
