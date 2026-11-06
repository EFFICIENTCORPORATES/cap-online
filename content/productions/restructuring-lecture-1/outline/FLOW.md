# Lecture 1 — Flow & Storyboard (Draft 2)
## "Reconstruction, Amalgamation and Consolidation: the map before the maths"

**Course:** CA Inter, Advanced Accounting (May 2027 attempt, July 2026 edition of the study material)
**Place in sequence:** straight after *Buyback of Securities* (Ch 12), before *Internal Reconstruction* (Ch 14), *Amalgamation of Companies* (Ch 13), AS 14 (Ch 9 U2) and AS 21 / 23 / 27 (Ch 10 U1-U3).
**Status:** DRAFT 2, after Pranav's review of Draft 1. No slides built yet.

**Companion files (kept separate on purpose):**
- `SPEAKER-NOTES.md` — your talking points, scene by scene. **Never part of the HTML.**
- `REFERENCES.md` — ICAI topic number and printed page for every item, with how each was checked.

**What changed from Draft 1:**
1. Brand now follows capranav.com and the "Practice with Pranav Bhaiya" slides (section 1).
2. Print / Save-as-PDF with a **CApranav.com** watermark is a built-in feature (section 1).
3. T-format is now **Equity & Liabilities on the LEFT, Assets on the RIGHT** (Schedule III order).
4. Net assets is taught with the **Arjun story** (Scene 6), and the same company becomes the target in the consolidation example.
5. Pre/post acquisition uses a **9 : 3 split**, never 6 : 6 (section 3).
6. Scene 1 is re-ordered to "rescue before winding up".
7. The reserves split (pre/post, parent/minority) is a full animation (Scene 9).
8. Associate scene now compares AS 13 with the equity method, using ICAI's own illustration (Scene 13).
9. Cross-holding corrected (REFERENCES.md section B).

---

## 0. What this lecture is, and is not

**Purpose.** Give the student the whole map of the block in one sitting, so that every later chapter feels like zooming into a box they have already seen.

**The rule for this lecture:** explain the **WHAT**, the **WHERE** it sits (financial statements and syllabus) and **how it relates** to its neighbours. **No journal entries and no solving.** Running examples are used only so a term has a number behind it.

**Every major concept gets at least a mention** (coverage checklist in section 9).

**The eight target terms:** net assets, net results of operations, acquisition (holding - subsidiary), control, cost of control, pre- and post-acquisition, statutory reserves, minority interest.

---

## 1. Format and brand

### 1.1 Format: HTML slide deck, step-by-step animation (not a video)
- You control the pacing and can stop to answer "wait, why?".
- The concepts are *movements* (shares changing hands, a company fading, an investment line splitting, a reserve being divided between two shareholders). Static slides cannot show these.
- One self-contained `.html` file; no internet needed while recording; can later be dropped into the website.

### 1.2 Brand: match capranav.com
Read from the site's own source files (`capranav_com_revamped/public/assets/site.css`, `whiteboard-theme.css`, and the two existing slide pages `day-01-opening` and `day-01-syllabus-flow`).

| Element | Used on your slides today | Plan for this deck |
|---|---|---|
| Stage | 16:9 stage, centred, dark navy surround | Same |
| Ink / text | `#10233f` | Same |
| Paper | `#f7f2e8` with a soft gold glow top right | Same |
| Accent red | `#e5484d` (eyebrows, strike-throughs, progress bar) | Same; **red = "problem / the dying side / eliminated"** |
| Gold | `#f2b84b` (hard offset shadow on cards) | Same; **gold = "the answer / the key term"** |
| Green | `#0f8a70` | **green = "survives / goodwill / income"** |
| Blue | `#1f62d0` | **blue = "the parent's share"**; minority interest gets its own colour (a light orange from the site's `--orange #e8733f`) |
| Type | Aptos / Segoe UI on slides; Manrope headings, DM Sans body, Caveat / Patrick Hand handwriting on the site | Slides: same as existing slides. Handwriting font only for **hand-drawn style asides** (a small note in the margin), as the site's whiteboard theme does |
| Pattern | Red caps "eyebrow" above a heavy headline; dark card with **hard gold shadow**, tilted about 1 degree; red strike-through; items that **reveal one per click**; thin red progress bar; round prev/next buttons; "n / N" counter; small grey brand label top-right | All kept |
| Wordmark and tagline | "P CA PRANAV" wordmark; "AIR 1. AIR 1. AIR 5." | Wordmark top-left of the TOC panel; tagline on the closing slide |
| Fonts offline | Slides use system fonts, no web-font download | Same: so it works offline and drops into the website unchanged |

Blend rule: it should look like **another episode of the "Practice with Pranav Bhaiya" slides**, not a new product.

### 1.3 Navigation
- **Table of contents:** a collapsible panel (hamburger button) with every section as a clickable link, the current section highlighted. Collapsed by default so the stage stays clean when recording; works with a keyboard (`T` toggles).
- **Steps:** `Space`, `->`, `Enter` or a click = next step; `<-`, `Backspace` = back. Nothing appears before you click it (same behaviour as your existing slides).
- Phone: panel becomes a full-width menu; stage scales.

### 1.4 Print / Save as PDF, with watermark
- A **Print / Save PDF** button (also `P`) on the control bar.
- Print view: **one slide per landscape A4 page**, **every step already revealed**, animations off, controls and TOC hidden.
- **Watermark "CApranav.com"** on every page: large, diagonal, low opacity (about 8 to 10 percent) so text stays readable; repeats on each printed page.
- The browser's "Save as PDF" then gives a proper PDF. I will also **generate a sample PDF at build time with headless Chromium and check that the watermark is on every page** before handing over. (Browser print dialogs differ; "Background graphics" must be on, and the button will remind you.)
- **Not** in the PDF: the speaker notes (they live only in `SPEAKER-NOTES.md`).

### 1.5 SVG: why the repo says "no SVGs/diagrams unless explicitly asked"
That line is in this repo's CLAUDE.md section 2 ("Working rules"), under "Markdown by default; HTML for books and slides". **The file does not give a reason**, so I do not know why it was written and will not guess. What I can say technically:
- An SVG is **not heavy to run or to load**: a few kilobytes, loads instantly, scales cleanly.
- It costs **more to author** than a Markdown table: a drawing needs coordinates for every shape, so it takes more tokens and more review time, and it is harder to edit by hand afterwards.
- **For this deck:** the T-format balance sheets and cards will be plain HTML and CSS boxes (easy to animate and edit), and I would use SVG only for arrows and curved connectors. You have now asked explicitly for the T-format and the animations, so both are in scope. No change to the rule is needed.

---

## 2. Table of contents (what the panel will show)

| # | Section | The student can answer afterwards |
|---|---|---|
| 1 | Rescue before winding up | Why do we have so many chapters? |
| 2 | Internal reconstruction | How can a sick company be saved without closing it? |
| 3 | **The big fork: does the target die?** | Which chapter / standard applies? |
| 4 | Target dies: reconstruction, amalgamation, absorption | Merger or purchase, and what decides it? |
| 5 | Target lives: the ownership ladder | AS 13, AS 23, AS 21 or AS 27? |
| 6 | **Net assets** (Arjun's story) | What is a company worth, and what changes it? |
| 7 | **Control** and what it triggers | Why does line-by-line consolidation exist? |
| 8 | **Cost of control** | Goodwill or capital reserve? |
| 9 | **Pre- and post-acquisition** (and net results of operations) | Why split reserves and profits? Who gets what? |
| 10 | **Minority interest** | What changes when it is not wholly owned? |
| 11 | **Statutory reserves** | Where do they matter? |
| 12 | Intra-group adjustments | Why can't a group profit from itself? |
| 13 | Associates (AS 13 vs equity method) and joint ventures | What if control is partial or shared? |
| 14 | Also in this block (mention cards, with ICAI pages) | What else will I meet? |
| 15 | Master map and word-bank | Can I place every term? |

---

## 3. The running examples

### 3.1 Arjun's company (Scene 6): net assets and what changes it
Units: ₹ thousand unless stated. **Equity & Liabilities on the left, Assets on the right.**

**Step 1 - Arjun starts the company**
| Equity & Liabilities (left) | ₹'000 | Assets (right) | ₹'000 |
|---|---|---|---|
| Capital | 50 | Cash | 5 |
| | | Inventory | 10 |
| | | Investment | 15 |
| | | PPE | 20 |
| **Total** | **50** | **Total** | **50** |

Net assets = 50 = Capital 50.

**Step 2 - one year of business: profit ₹50 (this is the "net results of operations")**
| Equity & Liabilities (left) | ₹'000 | Assets (right) | ₹'000 |
|---|---|---|---|
| Capital | 50 | Cash | 10 |
| Reserves & Surplus (profit for the year) | 50 | Inventory | 20 |
| **Equity** | **100** | Trade receivables | 20 |
| Trade payables | 20 | Investments | 30 |
| | | PPE | 40 |
| **Total** | **120** | **Total** | **120** |

Net assets = Assets 120 - Liabilities 20 = **100 = Equity**. A profit of 50 raised net assets by 50.

**Step 3 - Arjun borrows ₹10 lakh (= 1,000 thousand) and spends it half on PPE, half kept as cash** *(following your figures: PPE 540, cash 510)*
| Equity & Liabilities (left) | ₹'000 | Assets (right) | ₹'000 |
|---|---|---|---|
| Capital | 50 | Cash | 510 |
| Reserves & Surplus | 50 | Inventory | 20 |
| **Equity** | **100** | Trade receivables | 20 |
| Trade payables | 20 | Investments | 30 |
| Loan | 1,000 | PPE | 540 |
| **Total** | **1,120** | **Total** | **1,120** |

Net assets = 1,120 - (20 + 1,000) = **100**. Unchanged.

**The lesson (shown in gold):** *Net assets rise only when net worth rises. Assets and liabilities growing together change the size of the balance sheet, not what the owners own.*

### 3.2 Arjun Ltd becomes the target "S Ltd" (Scenes 7 - 11), 9 : 3 timing
We go back to Arjun's balance sheet at the end of Step 2: net assets **100** (capital 50 + reserves 50). The reserves are now shown in parts: **statutory reserve 10, general reserve 15, profit and loss surplus 25**.

**Timing (always 9 : 3):** financial year 1 April to 31 March. P Ltd buys on **1 January**, so **9 months are pre-acquisition and 3 months are post-acquisition**. *(Assumes profits accrue evenly, which is what ICAI says to assume when nothing else is given: AS 21 p10.32.)*

Year 2 profit of S Ltd is ₹40 for the full year, accruing evenly: **30 in the first 9 months, 10 in the last 3.**

**S Ltd on the acquisition date (1 January)** (no dividend paid in the year):
| Equity & Liabilities (left) | ₹'000 | Assets (right) | ₹'000 |
|---|---|---|---|
| Capital | 50 | Cash | 15 |
| Reserves: statutory 10, general 15, P&L 55 (25 + 30) | 80 | Inventory | 25 |
| **Equity** | **130** | Trade receivables | 25 |
| Trade payables | 20 | Investments | 35 |
| | | PPE | 50 |
| **Total** | **150** | **Total** | **150** |

**Net assets at acquisition = 150 - 20 = 130 = capital 50 + reserves 80.** Note that the 30 earned *this year before 1 January* is already part of the 130: P effectively pays for it.

| | **Case A: P buys 80% for 120** | **Case B: P buys 100% for 150** |
|---|---|---|
| Parent's share of net assets | 80% x 130 = **104** | **130** |
| Cost of control | 120 - 104 = **16 goodwill** | 150 - 130 = **20 goodwill** |
| Minority interest at acquisition | 20% x 130 = **26** | nil |
| Post-acquisition profit (last 3 months) | 10: P's 8 to consolidated reserves; minority's 2 to MI | 10: all to consolidated reserves |
| Minority interest at 31 March | 26 + 2 = **28** (= 20% x S's equity of 140) | nil |

Checks: Case A: 120 = 104 + 16; net assets 130 = 104 (P) + 26 (minority). Year-end equity of S = 50 + 90 = 140; 20% = 28; P's 80% = 112 = 104 (pre) + 8 (post).

*Numbers are illustrative and chosen to be clean whole numbers; they are not from the ICAI text.*

### 3.3 Associate example (Scene 13): ICAI's own illustration
AS 23 Illustration 1 (p10.114 - p10.115): A Ltd holds **45%** of B Ltd. Cost **₹15,00,000**; B's net assets ₹16,00,000, so goodwill **₹7,80,000** (cost less 45% x 16,00,000 = 7,20,000). B earns profit ₹3,00,000 and pays dividend ₹1,00,000.
- Equity method carrying amount: 15,00,000 **+ 1,35,000** (45% of profit) **- 45,000** (45% of dividend) = **₹15,90,000**.
- AS 13 treatment: investment stays at **₹15,00,000**; profit ignored; the **₹45,000 dividend is income** (it comes out of post-acquisition profit).

---

## 4. Scene-by-scene storyboard

Format per scene: **Goal / On screen / Click steps / Cues / Links**. Full talking points are in `SPEAKER-NOTES.md`; "Cues" here are only what the *slide* must contain.

### Scene 1 - Rescue before winding up
- **Goal:** the student sees why this block exists: a company in trouble should be **saved first**; winding up is the last resort.
- **On screen:** a health bar running from *Healthy* to *Dying*, with a big red button labelled **WIND UP / DISSOLVE** sitting at the far right, greyed out.
- **Steps:**
  1. **Healthy company:** "normal business". **Buyback (Sec 68)** appears as the example of a *happy* company using cash to return capital. Real cash flows *out*.
  2. The company starts to decline. The red **WIND UP** button flashes, then a stamp appears over it: **"Not the first thing we try."**
  3. **Rescue 1: Internal reconstruction.** Same company, same entity; sacrifices by shareholders, debenture holders and creditors; no cash leaves.
  4. **Rescue 2: External reconstruction.** The business moves to a *new* company; the old one closes.
  5. **If the business cannot be saved at all:** the WIND UP button finally lights up. It is the **last** box, not the first.
  6. A second arrow appears from the *Healthy* end, going the other way: **growth**: amalgamation, absorption, acquisition (the rest of the block).
- **Cues:** "Winding-up is the *process*; dissolution is the *outcome*" (from Foundation). Today's block = everything we can do *before* that last box, and everything a growing company does *instead*.
- **Links:** Buyback (Sec 68, Ch 12); Internal reconstruction (Sec 61, 66; Ch 14).

### Scene 2 - Internal reconstruction (mention-level)
- **Goal:** what it is and where it sits; no entries.
- **On screen:** a T-format balance sheet of a sick company (Equity & Liabilities left, Assets right): a large P&L debit balance and overvalued assets on the Assets side.
- **Steps:** 1 Show the sick balance sheet. 2 Arrows from shareholders, debenture holders and creditors labelled "sacrifice / waive". 3 All arrows flow into one box: **Capital Reduction (Reconstruction) Account**. 4 The box empties onto the P&L debit balance and the overvalued assets. 5 The balance sheet re-appears cleaned up, with "…and Reduced" added to the company's name.
- **Cues:** no new company, no cash leaves; the sacrifices *are* the gain.
- **Mention only:** alteration, variation of rights, reduction, compromise, surrender (all ICAI Ch 14 topic 2; see REFERENCES.md item 14).

### Scene 3 - THE BIG FORK: does the target company die?
- **Goal:** one question that sorts every later chapter.
- **On screen:** one decision node, "Target company: does it survive?", splitting into two columns.
- **Left column, DIES (red):** external reconstruction, amalgamation, absorption -> **AS 14** and Ch 13.
- **Right column, LIVES (green):** subsidiary, associate, joint venture -> **AS 21 / 23 / 27**, Ch 10.
- **Steps:** 1 Node. 2 Left column builds. 3 Right column builds. 4 Contrast table appears row by row.

| | Target dies (AS 14) | Target lives (AS 21) |
|---|---|---|
| Vendor / target | Wound up | Continues as a separate legal entity |
| Relationship | One-time event | Ongoing |
| Relevant date | Date of amalgamation | Date of acquisition |
| Pre/post split of reserves and profits | No | Yes |
| Dividend split (pre/post) | No (vendor cannot pay later dividends) | Yes |
| Minority interest | No | Yes, if not wholly owned |

- **Cues:** this slide is the spine. After every later section, a small "you are here" marker returns to this slide.

### Scene 4 - Target dies: three forms, two accounting methods
Two layers, deliberately kept separate.

**Layer A - what physically happens (ICAI Ch 13, p13.3 - p13.5):**
| Form | ICAI's meaning | Animation |
|---|---|---|
| External reconstruction | A **newly formed company takes over the business of an existing company** (often a loss-making one); only two companies involved; objective: reorganise financial structure. Per Ch 14 (p14.3): the business moves "to another company consisting **substantially of the same shareholders**" | Old company box -> new box with the same shareholder icons; old box fades |
| Amalgamation (A + B -> C) | Two or more companies wound up; a **new** company takes over their business | A and B slide together into C; A, B fade |
| Absorption (A absorbs B) | An **existing** company takes over the business of one or more existing companies; no new company | B's assets and liabilities slide into A; B's shell fades |

**Layer B - how it is accounted (the exam test):** the **5 conditions of AS 14** (Ch 9 U2 topic 2.4, p9.26). Pass **all five** = *amalgamation in the nature of merger* = **pooling of interests**. Fail **any one** = *nature of purchase* (topic 2.5, p9.27) = **purchase method**.
1. All assets and liabilities of the transferor come over.
2. Shareholders holding 90% or more (by face value of equity) become shareholders of the transferee.
3. Consideration to them is **wholly equity shares** (cash only for fractions).
4. The business is intended to carry on.
5. **No adjustment to book values** (except to align accounting policies).

- **Steps:** 1 Layer A, one form per click. 2 A line: "the form does NOT decide the method". 3 The five conditions tick in. 4 Two outcomes appear.
- **Cues:** "Marriage of equals *feels* like a merger, a big fish swallowing a small one *feels* like a purchase, **but the five conditions decide**." Two traps: an absorption of a subsidiary at book values can pass all five (merger); an A + B -> C that revalues assets fails condition 5 (purchase). **ICAI itself says external reconstruction is "essentially covered under the category of amalgamation in the nature of merger"** (Ch 14, p14.3).
- **Contrast with Scene 5:** buying the *shares* of a company does not make it die: that is an acquisition.
- **Terminology box:** AS 14 calls it **"consideration for the amalgamation"** (topic 2.7, p9.28); "purchase consideration" is the term used in Ch 13 for the purchase method.

**Merger vs purchase table:**
| Aspect | Merger | Purchase |
|---|---|---|
| Consideration | Wholly equity shares (cash only for fractions) | Cash, equity, preference shares or securities |
| Nature | Share swap / pooling | Outright buyout |
| Vendor's reserves | All preserved as they are | Revenue reserves **not** carried; only statutory reserves, through the Amalgamation Adjustment Reserve |
| Difference between net assets and consideration | None recognised | Goodwill or capital reserve |

- **Mention-only:** Realisation A/c; the 4 purchase-consideration methods; transferee's entries (REFERENCES.md items 1, 2).

### Scene 5 - Target lives: the ownership ladder
- **Goal:** pick the standard from the percentage.
- **On screen:** a vertical ladder 0% to 100%:
  - **Below 20% - "the stranger"** -> passive investment, **AS 13**, at cost.
  - **20% to 50% - "the friend"** -> significant influence -> **associate**, **AS 23**, equity method.
  - **Above 50% (or board control) - "father and son"** -> control -> **subsidiary**, **AS 21**, line-by-line consolidation.
  - **Joint control - "business partners"** -> **AS 27**: JCO, JCA, JCE.
- **Steps:** 1 Ladder. 2 Each band with its analogy. 3 For each band a mini card: "what appears in my books?". 4 **Hostile-takeover animation:** shares travel from the shareholders to the buyer; **the target stays standing** and moves into the "father and son" band.
- **Cues:** "Buying shares does not kill the company. Buying the *business* does." Standalone accounts keep the investment at cost; equity method and consolidation appear only in the consolidated statements.

### Scene 6 - NET ASSETS (Arjun's story, animated T-format)
- **Goal:** "net assets = assets - liabilities = equity = capital + reserves", and "net assets rise only when net worth rises".
- **On screen:** a T-format balance sheet with **Equity & Liabilities on the LEFT, Assets on the RIGHT**, filled step by step from section 3.1.
- **Steps:**
  1. **Arjun starts** (capital 50; four assets). Highlight: net assets = 50.
  2. **A year of business.** The profit of 50 slides into *Reserves & Surplus* on the left; assets on the right grow to 120; trade payables 20 appear. Label the 50 as **"net results of operations"**. The equation appears: *Assets 120 - Liabilities 20 = Equity 100 = Net assets*.
  3. **Arjun borrows ₹10 lakh.** Loan appears on the left; PPE and cash grow on the right; both sides jump to 1,120. A counter beside it keeps showing **Net assets: 100 (unchanged)**.
  4. **The lesson card** (gold): net assets rise only when net worth rises.
- **Cues:** "When you buy shares you are buying a share of *what is left after the creditors*; that is net assets; it is the same as equity, which is capital plus reserves."
- **Links:** AS 21 Topic 1.11, p10.20 (equity = residual interest = net worth).

### Scene 7 - CONTROL and what it triggers
- **Goal:** control is the trigger; everything else follows.
- **On screen:** a switch that turns on when holding crosses 50% (or the board is controlled).
- **Steps** (each consequence switches on in turn): 1 Assets and liabilities are reported (line-by-line). 2 Cost of control (Scene 8). 3 Pre/post acquisition (Scene 9). 4 Minority interest, only if below 100% (Scene 10). 5 Intra-group adjustments (Scene 12).
- **Line-by-line animation (key):** P's balance sheet shows **Investment in S: 120**. That one line **dissolves** and is replaced by S Ltd's assets (150) and liabilities (20), **not added on top of anything**. Then the net assets of 130 split three ways: **104** (P's 80%) cancels the investment; **16** (excess paid) stays as goodwill; **26** (the other 20%) appears as minority interest. Check on screen: 104 + 26 = 130; 120 = 104 + 16.
  - **Message:** "line-by-line consolidation is **not** adding every item of two balance sheets. In P's own books the investment line already *stands for* P's share of S's net assets. Consolidation swaps that one line for what it stands for."
- **Wholly owned vs partly owned:** toggle the example to Case B (100% for 150): the investment dissolves, 130 all belongs to P, goodwill 20, **no minority slice**. This toggle shows that **the only difference is the minority interest**.
- **Control definition:** AS 21 = more than half the voting power, or control of the composition of the board (topic 1.2 p10.6; topic 1.6 p10.11). The AS 18 definition is wider; **to be added only once the AS 18 text is available** to quote.
- **Mention-only:** exclusions (temporary control, long-term restrictions; topic 1.7 p10.12); syllabus note (single subsidiary, no cross-holding, no foreign, no disposal; p10.2).

### Scene 8 - COST OF CONTROL
- **Goal:** goodwill or capital reserve, and why.
- **On screen:** a balance scale. Left pan: **cost of investment (120)**. Right pan: **P's share of S's net assets on the acquisition date (104)**.
- **Steps:** 1 Both pans. 2 Left heavier -> **goodwill 16** (an asset: premium paid for control). 3 Swap the numbers (cost 90): right heavier -> **capital reserve 14** (a reserve: discount, often a distressed target). 4 Compare table appears.

| | Cost of investment (AS 13) | Cost of control (AS 21) |
|---|---|---|
| Appears in | Standalone statements | Consolidated statements |
| What it is | Total price paid (gross input) | Price paid minus parent's share of net assets (net output) |
| In the consolidated statements | Disappears | Shown as goodwill or capital reserve |

- **Cues:** cost of control arises for **every** subsidiary, wholly or partly owned. The same idea exists under the AS 14 purchase method (consideration vs net assets taken over).
- **Link:** AS 21 Topic 1.11, p10.20 - p10.21.

### Scene 9 - PRE- and POST-acquisition (and "net results of operations")
- **Goal:** the cut-off line, and exactly who gets which slice. **This scene is the main animation of the lecture.**
- **On screen:** a 12-month timeline (April to March) with a vertical **acquisition date** line at **1 January**: **9 months to the left (PRE), 3 months to the right (POST)**.

**Part 1 - the timeline.**
1. The line drops at 1 January. Left = **PRE: capital** (profits and reserves S had already earned: P paid for these when it bought the shares). Right = **POST: revenue** (earned while P owns it).
2. S's year-2 profit of 40 pours along the timeline in 12 equal blocks of ₹10/3 (about 3.33 each); the first 9 turn **red-bordered "pre"** (total 30) and the last 3 turn **green "post"** (total 10). *(Always 9 : 3: unmistakable which side is bigger.)*

**Part 2 - the reserves split (the animation Pranav asked for).** Show S Ltd's equity at 31 March as a tall stack:
- Capital 50
- Statutory reserve 10
- General reserve 15
- Profit & loss surplus 65 (25 brought forward + 30 pre + 10 post)

Click 1: a horizontal line is drawn across the stack at the acquisition date. **Everything below the line is PRE (capital):** capital 50, statutory 10, general 15, and **55** of the P&L surplus (the 25 brought forward and the 30 earned in the first 9 months). **Only 10 above the line is POST.**

Click 2: the whole stack **splits vertically** into two columns by shareholding: **P's 80% (blue)** and **minority's 20% (orange)**.

Click 3: the four resulting pieces fly to their destinations:
| Piece | Amount | Destination |
|---|---|---|
| P's share of PRE (capital + all pre-acquisition reserves: 80% x 130) | **104** | **Into the cost-of-control calculation** (compared with the investment of 120 -> goodwill 16); it does **not** appear as a reserve |
| Minority's share of PRE (20% x 130) | **26** | **Minority interest** |
| P's share of POST (80% x 10) | **8** | **Consolidated reserves** (revenue) |
| Minority's share of POST (20% x 10) | **2** | **Minority interest** |

Click 4: a total appears under minority interest: **26 + 2 = 28**, with a check beside it: *20% x S's total equity 140 = 28.* And under P: **104 + 8 = 112 = 80% x 140.**

**Part 3 - mentions** (as small cards, no animation): **dividends**: paid from *pre*-acquisition profit = return of the investment (credit Investment A/c, p10.33); from *post*-acquisition profit = income. **Mid-year rule:** profit for the year is split on a time basis unless stated otherwise (p10.32). **Bonus shares** issued by the subsidiary out of which reserves (p10.33).

- **Term note ("net results of operations"):** ICAI uses the phrase in the definition of minority interest (AS 21 p10.6, p10.26): outsiders own a share of both the **net assets** and the **net results of operations**.
- **Cues:** in amalgamation the target dies on one day, so nothing is "later". In consolidation the target keeps earning, so we need a line in time.

### Scene 10 - MINORITY INTEREST
- **Goal:** the only structural difference between partly owned and wholly owned.
- **On screen:** S Ltd's equity as one bar, **cut 80 / 20**. A toggle "make it 100%".
- **Steps:** 1 Bar at acquisition: 130 = 104 / 26. 2 Post-acquisition profit: 10 = 8 / 2. 3 Combine: MI = 26 + 2 = **28**, on its own line after shareholders' funds (presentation detail is a later lecture). 4 Toggle to 100%: MI vanishes, nothing else changes except that the whole 130 and 10 belong to P.
- **Cues:** MI is not a liability to be repaid; it is the outsiders' share of S's net assets and profit that the group includes because it controls 100% of S's assets.
- **Link:** AS 21 Topic 1.3 p10.7 (wholly vs partly owned); Topic 1.12 p10.24.

### Scene 11 - STATUTORY RESERVES (three fates)
- **Goal:** where this term bites, and where it does not.
- **On screen:** S's reserves (statutory 10, general 15, P&L) travel down **three lanes**:
  1. **Merger (pooling):** all reserves carried over **as they are** (statutory stays statutory, general stays general). AS 14 topic 2.9, p9.29.
  2. **Purchase:** vendor's reserves **not** carried, **except statutory reserves**, which keep their identity through the **Amalgamation Adjustment Reserve** (a separate line item). AS 14 topic 2.10, p9.30 - p9.31; Ch 13 p13.20.
  3. **Consolidation (target survives):** replays the Scene 9 animation, with the statutory 10 and general 15 highlighted inside the PRE block: they are simply part of the equity compared with the investment; they **disappear into the cost-of-control calculation** (parent's share) or become **minority interest** (minority's share). Nothing is "kept" as a statutory reserve in the consolidated statements by the study material's rules.
- **Honest note:** the AS 21 chapter text contains **no** specific rule on statutory reserves (searched). If a consolidation question includes one, follow the question's instructions and the pre/post logic.

### Scene 12 - Intra-group adjustments (concept only)
- **Goal:** "a group cannot make a profit by selling to itself."
- **On screen:** two boxes (P and S) inside one dashed "group" outline; goods move from S to P with a profit tag on them.
- **Steps:** 1 Goods move; profit tag shows in S's books. 2 Goods still unsold at year-end in P's stock. 3 The tag turns red: "unrealised; the group has not earned it". 4 Mutual debts (P owes S, S owes P) cancel inside the dashed line.
- **Mention-only:** unrealised profit in inventory (p10.68), non-current asset transfers (p10.70), mutual balances (p10.71), all in AS 21 topic 1.14 **section C** (starts p10.67).

### Scene 13 - Associates (AS 13 vs equity method) and joint ventures
- **Goal:** what changes when control is partial or shared.
- **On screen, panel 1 - the same investment under two methods, side by side** (ICAI's own numbers, section 3.3):
  - **Left (AS 13, cost):** a single bar **₹15,00,000**. When B earns ₹3,00,000 profit, **nothing moves**. When B pays a dividend, **₹45,000 appears as income** beside the bar.
  - **Right (equity method, AS 23):** the bar **grows** by ₹1,35,000 when B earns its profit (45% of 3,00,000) -> **₹16,35,000**; then **shrinks** by ₹45,000 when the dividend is received (the dividend is simply a *cash return of part of the investment*, not income) -> **₹15,90,000**. If the carrying amount ever reaches nil, the bar stops.
  - **Comparison table** (your Key Differences, tightened):

| Feature | AS 13 (cost / carrying value) | Equity method (AS 23) |
|---|---|---|
| Typical holding | Investor has no significant influence (usually under 20%) | Significant influence (usually 20% to 50%) |
| Initial recognition | Cost (price plus brokerage, stamp duty etc.) | Cost, with goodwill / capital reserve identified at acquisition |
| Subsequent measurement | Long-term: cost, less any permanent diminution. Current: lower of cost and fair value | Adjusted for the investor's share of post-acquisition change in the investee's net assets |
| Investee's profit or loss | Ignored | Share recognised; carrying amount goes up or down |
| Dividends | Income in P&L (pre-acquisition dividends reduce cost) | Reduce the carrying amount; **not** income |

- **On screen, panel 2 - joint ventures (AS 27):** three cards. **JCO:** each partner uses its own assets, books its own share of revenue and expenses; no new entity (p10.138). **JCA:** a jointly owned asset, each books its share (p10.143). **JCE:** a separate company under joint control; **proportionate consolidation**: each partner combines its % of every line (p10.149; consolidation p10.154).
- **Cues:** "Equity method = one line that grows and shrinks. Proportionate consolidation = your percentage of every line. Full consolidation = every line, then give the outsiders their share."
- **Real-world anchors (verify before filming):** Maruti Suzuki's origin as a joint venture between the Government of India and Suzuki; Vistara (Tata Sons / Singapore Airlines, 51:49) merged into Air India in November 2024, so use the **past tense**.

### Scene 14 - Also in this block (mention cards, with ICAI references)
One slide, one card each: **WHAT it is / WHERE it sits / the ICAI page**. Full topic and page references are in `REFERENCES.md` section A.

| Item | One line | ICAI reference |
|---|---|---|
| Realisation A/c | Vendor's closing account: assets out, consideration in, profit or loss on sale | Ch 13 topic 6, p13.21, p13.24 |
| 4 purchase-consideration methods | Lump sum, net payment, net assets, intrinsic value / share exchange: four ways to arrive at the price | Ch 13 topic 4, p13.7 - p13.8 |
| Capital Reduction A/c | The pooling account of Scene 2 | Ch 14 topic 2.3 p14.10; topic 3 p14.12 |
| Cross-holding | Only a **syllabus exclusion**. Sec 19: a subsidiary cannot ordinarily hold its holding company's shares (3 exceptions) | AS 21 Note-1 p10.2; topic 1.1 p10.4 |
| Foreign subsidiary | Excluded from numericals | AS 21 Note-1 p10.2 |
| Disposal of a subsidiary | Consolidate to the date of disposal; **not examined at Intermediate** | AS 21 topic 1.10, p10.19 - p10.20 |
| Mid-year acquisition | Profit apportioned pre/post on a time basis | AS 21 topic 1.13 p10.26; rule p10.32 |
| Dividend from a subsidiary | Pre-acquisition dividend credits Investment A/c; post-acquisition is income | AS 21 topic 1.14 B, p10.31 - p10.33 |
| Bonus shares by the subsidiary | Capitalises reserves; pre/post effect | AS 21 topic 1.14 B, Note 5 p10.33 |
| Revaluation on acquisition | Subsidiary's assets at fair value on acquisition date | AS 21 topic 1.14 A, p10.27 - p10.31 |
| Uniform policies; same reporting date | Prerequisites for adding lines together | AS 21 topic 1.17 p10.77; topic 1.14 D p10.72 |
| Consolidated cash flow statement | The cash-flow counterpart of consolidation | AS 21 topic 1.16, p10.76 |
| Disclosure: Form AOC-1, Sec 129, Schedule III | The legal wrapper of consolidated statements | AS 21 topic 1.4, p10.9 |
| Reconstruction forms | Alteration, variation of rights, reduction, compromise, surrender | Ch 14 topic 2, p14.4 - p14.12 |

*Page numbers are from the converted study-material files and must be eyeballed against the PDF before filming (see REFERENCES.md).*

### Scene 15 - Master map and word-bank
- **Goal:** one screen to take away.
- **On screen:** the decision tree (Scene 3) and the ownership ladder (Scene 5) redrawn together; each of the eight terms pinned where it is born: *net assets* (bottom of every balance sheet), *acquisition date* and *control* (the 50% mark), *cost of control* (first thing control triggers), *pre/post* (next to it), *minority interest* (below 100%), *statutory reserves* (on the "dies" side), *net results of operations* (the profit that moves net assets).
- **Close:** the eight-term word-bank (one plain line each), the tagline **AIR 1. AIR 1. AIR 5.**, and "CApranav.com".

---

## 5. Examples policy
- **Primary examples are fictional** (Arjun, P Ltd, S Ltd): they behave exactly as the standard needs and cannot go out of date.
- **Real-world examples are optional garnish**, never carrying a concept alone, each verified before shooting. Candidates (all to be verified): SBI's absorption of five associate banks (2017); Brooke Bond + Lipton (1993); Walmart-Flipkart (77%); Tata Digital-BigBasket (64%); Tata Motors-JLR (100%).
- **Not used as capital-reduction examples:** Vodafone Idea's government-equity conversion (a debt-to-equity conversion, not a Sec 66 reduction); and any example whose current legal classification cannot be confirmed (e.g. Titan Company, Hindustan Motors).

---

## 6. Corrections already accepted (carried into the deck)
1. Buying shares to take control = **acquisition**; the target survives. Absorption = taking over the **business**; the transferor is wound up (Ch 13 p13.3).
2. A mere name change or conversion into a private company is **not** external reconstruction. External reconstruction = business transferred to a new company of substantially the same shareholders (Ch 14, p14.3).
3. **Cost of control arises for every subsidiary**; minority interest is the extra for partly owned.
4. Intuition (marriage vs swallowing) and the **AS 14 five-condition test** are shown as **two layers**.
5. AS 18's wider control definition is **not in the AS 21 chapter**; included only once the bare standard is available.
6. **Cross-holding** is a syllabus exclusion only; Sec 19 is in AS 21 topic 1.1 p10.4 (REFERENCES.md section B).

---

## 7. Open points for Pranav
| # | Question | Default if you do not reply |
|---|---|---|
| 1 | **9 : 3 timing:** is "acquisition on 1 January in a 1 April - 31 March year (9 months before, 3 after)" what you meant? | Yes, as written in section 3.2 |
| 2 | **The loan in Arjun's story:** your figures put the full ₹10 lakh into PPE (+5 lakh) and cash (+5 lakh), none in inventory. Correct? | Follow your figures (inventory unchanged) |
| 3 | Where should the finished deck live on the website? (A new `.../slides/` page like the existing ones, or a separate lectures area) | Build it standalone now; decide placement when you add it |
| 4 | Please give me **AS 18** (and, if easy, the bare AS 14 / 21 / 23 / 27) | Without them, AS 18 points stay "to verify" |
| 5 | **Page-number check:** can you open the six chapter PDFs and confirm the pages in `REFERENCES.md`? (I cannot reach the PDFs in R2 from this session.) | Pages shown on slides stay marked "to verify" |

---

## 8. Source discipline
- Terms and the five conditions come from the July 2026 ICAI text in `books/ca-inter/smat-may-27-edition/all-modules/`.
- The converted files are machine-structured with visual validation pending; pages are bracket-checked against the raw conversion, not against the PDFs (REFERENCES.md).
- Your v4 / v5 roadmaps differ from ICAI's own topic numbering after AS 21 topic 1.14 (REFERENCES.md section D); ICAI's numbering is used here.

---

## 9. Coverage checklist (nothing major left out)
- [x] Winding-up / dissolution; rescue before winding up
- [x] Buyback vs reconstruction
- [x] Internal reconstruction; Capital Reduction A/c; Sec 61, 66
- [x] External reconstruction (ICAI: p14.3, p13.3)
- [x] Amalgamation, absorption; merger vs purchase; 5 conditions
- [x] Consideration for the amalgamation vs purchase consideration; 4 PC methods (mention)
- [x] Realisation A/c and transferee entries (mention)
- [x] Pooling vs purchase; goodwill / capital reserve; Amalgamation Adjustment Reserve
- [x] AS 13, AS 23, AS 21, AS 27 ladder; equity method vs cost; JCO / JCA / JCE; proportionate consolidation
- [x] Control (AS 21; AS 18 pending); exclusions; syllabus scope
- [x] Net assets; net results of operations; equity = capital + reserves; what changes net assets
- [x] Cost of control; pre/post (9 : 3); dividends; time apportionment; bonus shares; revaluation
- [x] Minority interest; wholly vs partly owned
- [x] Statutory reserves (three fates)
- [x] Intra-group adjustments (stock, non-current assets, mutual balances)
- [x] Cross-holding (with Sec 19) and foreign subsidiaries (mention; excluded from numericals)
- [x] Disposal of subsidiary (mention; not examined at Inter)
- [x] Uniform policies, reporting dates, consolidated cash flow, disclosure (Form AOC-1, Sec 129, Schedule III)
