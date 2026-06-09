**Purpose & context**

Pranav Pratik Tulshyan is a CA with AIR 1 in CPT & IPCC and AIR 5 in Finals, working at IOCL and the Ministry of Petroleum while teaching at VC Gurukul, Noida. He is building a comprehensive CA Inter Advanced Accounting content ecosystem with three interlocking outputs:

1. **An advanced accounting textbook** for CA Inter students that blends rigorous technical content with motivational/life philosophy inserts woven throughout chapters
2. **A video course** (with an animation team) using a recurring cast of fictional characters to anchor difficult concepts
3. **A Syllabus Intelligence Engine** — a machine-readable data pipeline converting ICAI source materials into structured, queryable formats

Success means students can recall correct accounting treatment under exam pressure, not just recite definitions — and that the content system is reusable and scalable across all 36 chapters of the Advanced Accounting syllabus.

**Key people & assets:**
- Recurring character cast: Sethji, Rolly, Diya, Pranav, CFO Sir, Gurpreet Sir (each with defined personalities and roles)
- A custom JSON syllabus file covering 36 chapters in a specific teaching sequence, ~436 topic rows, exam frequency data across 15 historical attempts
- A long-running narrative spine: ECPL preparing for a funding round/acquisition, BCPL being cleaned up for a bank loan — teased in Chapter 1, paying off at Chapter 30

**Current state**

- **Content bank chat** established separately for all non-accounting (motivational/philosophical) book material; ten named content sections defined, with raw-to-polished workflow in place
- **HTML extraction pipeline** operational: AS 2 (Inventories) fully extracted into semantic HTML using a strict class taxonomy and M[x].C[x].U[x].S[x].B[x] sequence ID convention
- **Python scripts built and verified:**
  - `extract_json_from_html.py` — converts verified ICAI Base HTML chapters to structured JSON (77 blocks on test run, 0 errors)
  - `build_syllabus_json.py` — processes Excel exam weightage/topic data into unified `ca_inter_syllabus.json` (36 chapters, 436 topic rows, 0 unmatched IDs)
- **AS 2 story content** developed as a working example: joint product/by-product costing vignette featuring Sethji's naphthalene factory, with verified numbers, worked table, formal AS 2 rule, and Pranav's Margin Note

**On the horizon**

- Extending the HTML extraction and story-vignette treatment to remaining chapters (35+ chapters remaining beyond AS 2)
- Building out Excalidraw-style revision summaries for exam use (high-detail-density, examiner-trap-focused)
- Developing the full season-long narrative arc across all 36 chapters using the character cast
- Expanding the non-accounting content bank across all ten motivational/philosophical theme sections

**Key learnings & principles**

- **Story placement rule:** Stories must live at the exact point where a confident student writes the wrong answer — at exceptions, misapplications, and counter-intuitive cases — never at the definition level. Basic, well-known rules (e.g., "lower of cost or NRV") are not worth animating.
- **Book vignette structure:** Boxed narrative showing the error → rigorous technical treatment → Pranav's Margin Note (exam warnings + cross-chapter linkages)
- **Animation threshold:** Reserve for concepts where sequential logic is genuinely hard to grasp from text (e.g., the two-step subtract-then-allocate in joint products); don't animate what text handles well
- **Revision material principle:** Carry every sub-point and worked example; functional density for exam use, not elegance
- **Data integrity matters:** The Excel attempt column headers encode year in the day field (e.g., `May 18, 2026` = May 2018 attempt) — custom decoding required; marks strings like `"5+5"` and `"14 (With AS 23)"` preserved as exact strings

**Approach & patterns**

- Pranav shares raw thoughts, stories, or source material in any form; Claude shapes into polished, book-ready output
- Non-accounting content (motivational/philosophical) is kept strictly separate from technical subject matter in its own dedicated chat
- HTML extraction follows exact replication rules — no paraphrasing, no omissions, with verification checklists embedded as HTML comments and extraction flags for missing content
- Numbers in story vignettes are computationally verified before writing to ensure clean ratios and exact allocations
- Communication style is direct and instruction-heavy; domain terminology used fluently throughout

**Tools & resources**

- BeautifulSoup4 (HTML parsing in Python pipeline)
- Excalidraw (revision visual planning)
- ICAI CA Inter Advanced Accounting Study Material (PDF source)
- Custom Excel file: `CA_Inter_Topic_Wise_Bifurcation_and_Chapter_wise_weightage.xlsx`
- Custom JSON: `ca_inter_syllabus.json`

**Output format defaults**

- Default to **.MD format** for all documents (not .docx)
- Default to **.HTML for books or slides** unless told otherwise
- **Never create diagrams or SVGs** unless specifically requested