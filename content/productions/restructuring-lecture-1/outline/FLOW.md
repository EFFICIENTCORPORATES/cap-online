# Lecture 1 — Flow & Storyboard
## "Reconstruction, Amalgamation and Consolidation: the map before the maths"

**Course:** CA Inter, Advanced Accounting (May 2027 attempt, July 2026 edition of the study material)
**Place in sequence:** straight after *Buyback of Securities* (Ch 12), before *Internal Reconstruction* (Ch 14), *Amalgamation of Companies* (Ch 13), AS 14 (Ch 9 U2) and AS 21 / 23 / 27 (Ch 10 U1-U3).
**Status:** DRAFT 1 for Pranav's review. Nothing here has been built as slides yet.

---

## 0. What this lecture is, and is not

**Purpose.** Give the student the *whole map* of the block in one sitting, so that every later chapter feels like "zooming into a box they have already seen" instead of a new topic.

**The rule for this lecture:** explain the **WHAT** (what it is), the **WHERE** (where it sits in the financial statements and in the syllabus) and the **WHY / HOW IT RELATES** to its neighbours. **No journal entries and no solving.** One tiny running example (section 3) is used only so that terms have a number behind them.

**Every major concept gets at least a mention** (see the coverage checklist in section 9), so a student who has seen only Lecture 1 can place any term they meet later.

**The eight target terms** (the words that decide marks in the paper):
1. Net assets
2. Net results of operations
3. Acquisition (holding - subsidiary)
4. Control
5. Cost of control
6. Pre- and post-acquisition
7. Statutory reserves
8. Minority interest

---

## 1. Format recommendation

**HTML slide deck, scene-based, with click-to-advance animation. Not a video.**

Why:
- You are recording the lecture yourself. A deck you click through (arrow key or mouse) lets *you* control the pacing; an animation baked into a video cannot be paused to answer "wait, why?".
- The concepts here are **movements** (shares moving from shareholders to the buyer, a company disappearing, an investment line splitting into pieces). Static slides cannot show a movement; step-by-step reveals can.
- Single self-contained `.html` file: no server, no internet needed at record time, and it can later be dropped into the website (`capranav_com_revamped/public/`) as it is.

**Deck features (proposed):**
| Feature | Detail |
|---|---|
| Table of contents | Left sidebar; every section is a clickable link; current section highlighted |
| Steps | Each scene has numbered steps (`Space` / `->` next, `<-` back). Nothing appears before you click it |
| T-format balance sheet | Drawn in the deck itself (HTML/CSS, not an image) so it can animate |
| Speaker notes | Press `N` to toggle your cues on screen (hidden while recording) |
| Print | `Ctrl+P` gives a clean static handout with every step shown |
| Phone | Readable at phone width; sidebar collapses into a menu |
| Accessibility | Respects "reduce motion"; colour never the only signal |

*(Repo rule: "no SVGs/diagrams unless explicitly asked" - you asked for the T-format and animations, so they are in scope here.)*

**Suggested build order:** (1) you approve this flow, (2) I build the deck, (3) you review it scene by scene, (4) record.

---

## 2. Table of contents (what the sidebar will show)

| # | Section | Core question the student can answer afterwards |
|---|---|---|
| 1 | The company life-cycle | Why do we have so many chapters? |
| 2 | Sick company: Internal Reconstruction | How can a company be saved without closing it? |
| 3 | **The big fork: does the target company die?** | Which chapter / standard applies? |
| 4 | Target dies: reconstruction, amalgamation, absorption | What is the difference, and what decides "merger" vs "purchase"? |
| 5 | Target lives: the ownership ladder | AS 13, AS 23, AS 21 or AS 27? |
| 6 | **Net assets** (T-format) | What exactly is being bought? |
| 7 | **Control** and what it triggers | Why does line-by-line consolidation exist? |
| 8 | **Cost of control** | Goodwill or capital reserve? |
| 9 | **Pre- and post-acquisition** (+ net results of operations) | Why must reserves and profits be split? |
| 10 | **Minority interest** | What changes when the subsidiary is not wholly owned? |
| 11 | **Statutory reserves** | Where do they matter, and where not? |
| 12 | Intra-group adjustments | Why can't a group book a profit on selling to itself? |
| 13 | Associates and joint ventures | What if control is not full? |
| 14 | Also in this block (mention-only) | What else will I meet? |
| 15 | Master map & word-bank | Can I place every term? |

---

## 3. The running example (used from section 6 onwards)

**S Ltd, balance sheet on the acquisition date (T-format):**

| Assets | ₹ | Equity & liabilities | ₹ |
|---|---|---|---|
| Fixed assets | 120 | Share capital | 100 |
| Current assets | 80 | Reserves: statutory 10, general 20, P&L 30 | 60 |
| | | Creditors | 40 |
| **Total** | **200** | **Total** | **200** |

- **Net assets** = Assets 200 - Liabilities 40 = **160** = Equity (capital 100 + reserves 60).
- **P Ltd buys 80% of S Ltd for ₹150** (case A, partly owned) or **100% for ₹180** (case B, wholly owned).

| Item | Case A: 80% for 150 | Case B: 100% for 180 |
|---|---|---|
| Parent's share of net assets | 80% x 160 = **128** | **160** |
| Cost of control | 150 - 128 = **22 goodwill** | 180 - 160 = **20 goodwill** |
| Minority interest at acquisition | 20% x 160 = **32** | **nil** |
| S earns ₹50 after acquisition | P's 40 -> consolidated reserves; minority's 10 -> MI (MI becomes 42) | P's 50 -> consolidated reserves; no MI |

Arithmetic check: Case A: 150 = 128 + 22; the 32 is the minority's slice of the same 160. Total net assets 160 = 128 (P) + 32 (minority).

*These numbers are illustrative, chosen so every figure is a clean whole number. They are not from the ICAI text.*

---

## 4. Scene-by-scene storyboard

Format for each scene: **Goal / On screen / Click steps / Cues for you / Links**. "Cues" are prompts, not a script; you speak in your own words.

### Scene 1 - The company life-cycle
- **Goal:** the student sees the whole block as one story.
- **On screen:** a horizontal ladder, left to right: *Happy company (Buyback, Sec 68)* -> *Sick company (Internal Reconstruction)* -> *Cannot survive in this form (External Reconstruction)* -> *Combine with another (Amalgamation / Absorption)* -> *Buy control (Subsidiary)* -> *Partial control (Associate)* -> *Shared control (Joint Venture)*. Winding-up / dissolution sits at the far end, dimmed.
- **Steps:** 1 Winding-up appears ("the end"). 2 Buyback appears ("happy company: cash goes out"). 3 Internal Reconstruction ("sick: no cash, sacrifices"). 4-7 each remaining box lights up with a one-line tag.
- **Cues:** winding-up = *process*, dissolution = *outcome* (students know this from Foundation). "Everything in the next 20-30 hours is a way of NOT reaching the last box, or of changing who owns what."
- **Links:** Buyback (Sec 68) -> Internal Reconstruction (Sec 66, Sec 230).

### Scene 2 - Sick company: Internal Reconstruction (mention-level)
- **Goal:** what it is and where it sits; no entries.
- **On screen:** a T-format balance sheet of a sick company: a large P&L debit balance and overvalued assets on the assets side.
- **Steps:** 1 Show the sick BS. 2 Arrows from shareholders, debenture holders and creditors labelled "sacrifice / waive". 3 All arrows flow into one box: **Capital Reduction (Reconstruction) Account**. 4 The box empties onto the P&L debit balance and the overvalued assets. 5 The BS re-appears cleaned up, labelled "... and Reduced".
- **Cues:** "No new company. No cash leaves. The sacrifices *are* the gain." Mention Sec 61 (alteration), Sec 66 (reduction), Sec 230 (compromise), tribunal sanction.
- **Mention only:** surrender of shares, reissue, debenture/ creditor compromises, the "and Reduced" Balance Sheet.

### Scene 3 - THE BIG FORK: does the target company die?
- **Goal:** one question that sorts every later chapter.
- **On screen:** a single decision node "Target company: does it survive?" splitting into two columns.
- **Left column - DIES:** External reconstruction, Amalgamation, Absorption -> **AS 14**, Ch 13 -> *one-time event, no pre/post split, no minority interest*.
- **Right column - LIVES:** Subsidiary, Associate, Joint Venture -> **AS 21 / AS 23 / AS 27**, Ch 10 -> *ongoing relationship, pre/post split, minority interest where partly owned*.
- **Steps:** 1 Node appears. 2 Left column builds. 3 Right column builds. 4 Contrast table (below) slides in row by row.
- **Contrast table (from your notes):**

| | Target dies (AS 14) | Target lives (AS 21) |
|---|---|---|
| Vendor / target | Wound up | Continues as a separate legal entity |
| Relationship | One-time event | Ongoing |
| Relevant date | Date of amalgamation / appointed date | Date of acquisition |
| Pre/post split of reserves and profits | No | Yes |
| Dividend split (pre/post) | No (vendor cannot pay later dividends) | Yes |
| Minority interest | No | Yes, if not wholly owned |

- **Cues:** this slide is the spine. Return to it at the end of every later section ("which column are we in?").

### Scene 4 - Target dies: three forms, two accounting methods
This scene has **two layers**, kept deliberately separate. (Your v5 "golden exam caveat".)

**Layer A - what physically happens (the story):**
| Form | Story | Animation |
|---|---|---|
| External reconstruction | One old company sells its **business** to a **new company with substantially the same shareholders**; old company is liquidated | Old company box -> new box with the same shareholder icons; old box fades |
| Amalgamation (A + B -> C) | Two companies' businesses go into a **new** company; both old companies close | A and B boxes slide together, merge into C; A, B fade |
| Absorption (A absorbs B) | A **buys the business** of B; B is wound up; A continues | B's assets and liabilities slide into A; B's shell fades |

**Layer B - how it is accounted (the exam test):** run the **5 conditions of AS 14** (ICAI Ch 9 U2, topic 2.4, p 9.26). Pass **all five** -> *Amalgamation in the nature of merger* -> **Pooling of Interests**. Fail **any one** -> *nature of purchase* -> **Purchase Method** (topic 2.5, p 9.27).

The five, as one-line student wording:
1. All assets and liabilities of the transferor come over.
2. 90% or more of the transferor's equity shareholders (by face value) become shareholders of the transferee.
3. Consideration to them is **wholly in equity shares** (cash only for fractions).
4. The business is meant to carry on.
5. **No revaluation** of book values (except to align accounting policies).

- **Steps:** 1 Layer A animations one at a time. 2 A line appears: "form does NOT decide the method". 3 The five-condition checklist ticks in. 4 Two outcomes appear.
- **Cues (your intuition, then the test):** "Marriage of equals *feels* like a merger; a big fish swallowing a small one *feels* like a purchase. But the 5 conditions decide, not the feeling." Show the two traps: an absorption that passes all five is still a merger (e.g. a parent absorbing its own subsidiary at book values); an A + B -> C that revalues assets becomes a purchase.
- **Hostile takeover (use as a CONTRAST, in the next scene):** buying the *shares* of a company does **not** make it die. That is an acquisition (Scene 5), not absorption.
- **Terminology box:** AS 14 calls it **"consideration for the amalgamation"**; **"purchase consideration"** is the term used in practice and in the ICAI chapter for the purchase method. Merger consideration may be only equity shares; purchase consideration may be cash, equity, preference shares or securities.
- **Mention-only (not explained):** **Realisation A/c** and closing the vendor's books, the **4 purchase-consideration methods** (lump sum, net payment, net assets, intrinsic value / share exchange ratio), **Transferee's entries**, goodwill / capital reserve on purchase.

**Compare table (merger vs purchase) goes on screen here:**

| Aspect | Merger | Purchase |
|---|---|---|
| Consideration | Wholly equity shares (cash only for fractions) | Cash, equity, preference shares or securities |
| Nature | Share swap / pooling | Outright buyout |
| Reserves of the vendor | All preserved as they are | Revenue reserves **not** carried; only statutory reserves via Amalgamation Adjustment Reserve |
| Difference between net assets and consideration | None recognised (adjusted in reserves) | Goodwill or capital reserve |

### Scene 5 - Target lives: the ownership ladder
- **Goal:** pick the standard from the percentage.
- **On screen:** a vertical ladder / thermometer 0%-100%, with the bands labelled:
  - **Below 20% - "the stranger"** -> passive investment, **AS 13**, shown at cost.
  - **20% to 50% - "the friend"** -> significant influence -> **Associate**, **AS 23**, **equity method** (in consolidated statements).
  - **Above 50% (or board control) - "father and son"** -> **Control** -> **Subsidiary**, **AS 21**, **line-by-line consolidation**.
  - **Joint control** -> "business partners" -> **AS 27**: JCO, JCA, JCE.
- **Steps:** 1 Ladder base. 2 Each band slides in with its analogy. 3 For each band, a mini-card: "what appears in my books?". 4 Hostile takeover animation: shareholders' shares travel to the buyer; **target stays standing** -> it slides into the "father and son" band.
- **Cues:** "Buying shares does not kill the company. Buying the *business* does." That one sentence separates Scene 4 from Scene 5.
- **Mention:** standalone accounts always keep the investment at cost under AS 13; the equity method / consolidation happen **only in consolidated financial statements (CFS)**.

### Scene 6 - NET ASSETS (animated T-format)
- **Goal:** the student can say "net assets = assets - liabilities = equity = capital + reserves", and understands why that is **exactly what an investor really buys**.
- **On screen:** S Ltd's T-format balance sheet (section 3).
- **Steps:**
  1. Draw the T: assets left, equity & liabilities right.
  2. Highlight **Liabilities** (creditors 40) and slide them across to the left, *subtracting* from assets: the left becomes "Net assets 160".
  3. What remains on the right is only **Equity 160**: share capital 100 + reserves 60. The equation "Assets - Liabilities = Equity" is written under the T.
  4. Zoom on the reserves: split into statutory 10, general 20, P&L 30 (this split is reused in Scene 11).
  5. A shareholder with 80% points at the equity: "80% of this is mine" -> 128.
- **Cues:** "When you buy shares you do not buy the building and the creditors separately; you buy a share of what is left after the creditors are paid. That left-over is net assets, which is the same thing as equity, which is the same thing as capital plus reserves."
- **Links:** ICAI Ch 10 U1 topic 1.11 defines equity as "the residual interest in the assets after deducting all its liabilities... equal to the net worth" (p 10.20).

### Scene 7 - CONTROL and what it triggers
- **Goal:** control is the *trigger*; everything else follows from it.
- **On screen:** a "control switch" icon turning on when holding crosses 50% (or when the board is controlled).
- **Steps (each is a consequence that switches on in turn):**
  1. **Assets and liabilities are reported** by the parent (line-by-line consolidation) - "if I control it, I must show it".
  2. **Cost of control** appears (Scene 8).
  3. **Pre/post acquisition** line appears (Scene 9).
  4. **Minority interest** appears *only if holding < 100%* (Scene 10).
  5. **Intra-group adjustments** appear (Scene 12).
- **Cues:** "Say the word *control* and five things switch on at once. That is why this chapter feels crowded; it is five ideas arriving together."
- **Line-by-line, the key animation:** side-by-side, P's investment of 150 vs S's full balance sheet.
  - Step A: P's balance sheet shows "Investment in S: 150".
  - Step B: that single line **dissolves and is replaced by S's assets and liabilities** (200 and 40), **not added on top**.
  - Step C: the part of S's net assets that belongs to P (128) cancels the investment; the excess paid (22) stays as goodwill; the part that belongs to outsiders (32) appears as minority interest.
  - **Message:** "line-by-line consolidation is **not** adding every item of two balance sheets. In P's own books the investment line already *stands for* P's share of S's net assets. Consolidation just swaps that one line for what it stands for."
- **Control definition note:** AS 21 control = more than half of voting power, **or** control of the composition of the board so as to get economic benefit. The AS 18 definition of control is **wider** (it adds a substantial voting interest plus the power to direct policies). *(Not in the AS 21 chapter; add only after we have the AS 18 text to quote.)*
- **Mention-only:** exclusion where control is temporary (intended to be disposed of within 12 months) or under severe long-term restrictions; the syllabus note that exam sums use **one subsidiary, no cross-holdings, no foreign subsidiary**.

### Scene 8 - COST OF CONTROL
- **Goal:** goodwill or capital reserve, and why.
- **On screen:** two pans of a balance scale. Left pan: **Cost of investment (150)**. Right pan: **Parent's share of S's net assets on acquisition date (128)**.
- **Steps:** 1 Both pans appear. 2 Left heavier: tag "premium paid for control -> **Goodwill** (an asset)". 3 Swap the numbers (cost 120): right heavier: tag "discount -> **Capital reserve** (a reserve)". 4 Caption: a discount usually signals a distressed or unwanted target.
- **Cues:** "Cost of investment is the **gross input** you paid, shown in P's own books (AS 13). **Cost of control** is the **net output**: the difference between that and what you actually got. In the consolidated statements, the investment line disappears and this difference takes its place."

| | Cost of investment (AS 13) | Cost of control (AS 21) |
|---|---|---|
| Appears in | Standalone statements | Consolidated statements |
| What it is | Total price paid | Price paid minus parent's share of net assets |
| In the CFS | Disappears | Shown as goodwill or capital reserve |

- **Wholly owned vs partly owned:** *cost of control arises in both.* The only difference is the minority interest (Scene 10).
- **Compare, in one glance:** AS 14 purchase method also produces goodwill / capital reserve (consideration vs net assets taken over). Same idea, different standard: "the premium or discount for getting the business."
- **Link:** ICAI Ch 10 U1 topic 1.11, p 10.20.

### Scene 9 - PRE- and POST-acquisition (plus "net results of operations")
- **Goal:** the cut-off line.
- **On screen:** a timeline for S Ltd with a vertical **acquisition date** line.
- **Steps:**
  1. Timeline appears; left of the line labelled **PRE** (profits and reserves S had already earned = *capital*: P effectively **paid for them** when it bought the shares). Right of the line labelled **POST** (what S earns while P owns it = *revenue*).
  2. Reserves of S (statutory 10, general 20, P&L 30) sit on the pre side at the acquisition date. They are part of the 160 used in Scene 8.
  3. A year passes: S earns ₹50 (this is the **net results of operations** for the period). The 50 lands on the POST side and splits: 40 -> parent (consolidated reserves), 10 -> minority.
  4. **Dividend rule** (mention): a dividend paid out of **pre**-acquisition profits is a return of the investment cost (credit Investment A/c), not income; out of **post**-acquisition profits it is income.
  5. **Mid-year acquisition** (mention): profit of the year is time-apportioned at the acquisition date.
- **Cues:** "In amalgamation the target dies on one day, so nothing is 'later'. In consolidation the target keeps earning every year, so we need a line in time."
- **Term note:** ICAI uses "net results of operations" in the **definition of minority interest** ("that part of the net results of operations and of the net assets of a subsidiary attributable to interests not owned by the parent", AS 21 topic 1.12). So net assets and net results are the two things the outsiders also own a share of.

### Scene 10 - MINORITY INTEREST
- **Goal:** the only structural difference between a partly owned and a wholly owned subsidiary.
- **On screen:** the same S Ltd bar, **cut in two**: 80% (P) and 20% (outsiders). Toggle "make it 100%" and the 20% slice disappears.
- **Steps:** 1 Show 80 / 20 on net assets (128 / 32). 2 Show 80 / 20 on post-acquisition profit (40 / 10). 3 Combine: MI = 32 + 10 = 42, shown in the CFS between **shareholders' funds** and **liabilities** (presentation is a later lecture; say "its own line, in equity"). 4 Toggle to wholly owned: MI vanishes, nothing else changes.
- **Cues:** "Minority interest is not a liability to be paid back; it is the outsiders' share of S's net assets and profit that the group had to include because it controls 100% of S's assets."
- **Link:** ICAI Ch 10 U1 topic 1.12.

### Scene 11 - STATUTORY RESERVES (three fates)
- **Goal:** the student knows where this term bites and where it does not.
- **On screen:** S Ltd's reserves bar (statutory 10, general 20, P&L 30) travels down three lanes.
  1. **Lane 1 - Merger (pooling):** every reserve is carried over **as it is** (statutory stays statutory, general stays general).
  2. **Lane 2 - Purchase:** reserves of the vendor are **not** carried over, **except statutory reserves**, which the law requires to keep their identity; this is done through the **Amalgamation Adjustment Reserve** (ICAI Ch 9 U2, topics 2.8-2.10, pp 9.29-9.30). *The Amalgamation Adjustment Reserve is a balancing account that makes the statutory reserve visible without inflating real reserves.*
  3. **Lane 3 - Consolidation (target survives):** reserves are not "kept" at all in the sense of lanes 1-2. They are **split pre / post**. The **pre-acquisition** part (of every reserve, statutory included) is simply part of the equity compared against the investment in Scene 8; it disappears into the cost-of-control calculation. The **post-acquisition** part of P's share goes to consolidated reserves; the minority's share goes to MI.
- **Cues:** "Statutory reserve is an AS 14 *purchase* issue. In AS 21 we do not treat it as a special topic; it follows the same pre / post logic as every other reserve."
- **Honest note for you:** the AS 21 chapter text contains **no** specific rule on statutory reserves. Where a consolidation sum includes one in the subsidiary, follow the question's instructions; do not invent a rule.

### Scene 12 - Intra-group adjustments (concept only)
- **Goal:** one idea: "a group cannot make a profit by selling to itself."
- **On screen:** two boxes (P and S) inside one dashed "group" outline; goods move from S to P; a price tag with profit stuck on the goods.
- **Steps:** 1 Goods move, profit tag appears in S's books. 2 Goods are still unsold at year-end in P's stock. 3 The profit tag turns red: "unrealised, group has not earned it". 4 Mutual debts (P owes S, S owes P) cancel inside the dashed line.
- **Cues:** "Inside the group boundary, the group is dealing with itself. Only transactions that cross the dashed line with an outsider are real."
- **Mention-only:** unrealised profit in closing stock (upstream vs downstream: affects minority interest or only the parent's share), transfers of fixed assets between group companies (profit, extra depreciation), mutual debts (receivables and payables, loans), unpaid interest accrued, bonus shares issued by the subsidiary.
- **Link:** ICAI Ch 10 U1 topic 1.16 (per your roadmap, pp 10.61-10.72).

### Scene 13 - Associates and joint ventures
- **Goal:** what happens when control is not full or not single.
- **On screen:** two panels.
  - **Associate (AS 23):** the investment line is not replaced by assets; instead it **moves**: opening at cost, then goes up with P's share of the associate's post-acquisition profit, down with dividends received. The "carrying amount" ticks up and down like a thermometer. If it reaches nil, stop.
  - **Joint ventures (AS 27):** three cards: **JCO** (each partner uses own assets, books own share of revenue and expenses; no new entity), **JCA** (jointly owned asset, each books its share), **JCE** (a separate company under joint control; **proportionate consolidation**: each partner combines its % of each line).
- **Cues:** "Equity method = one line that grows. Proportionate = your percentage of every line. Full consolidation = every line, then give the outsiders their share."
- **Real-world anchors (verify each before filming):** Maruti Suzuki's origin as a JV between the Government of India and Suzuki; Vistara (Tata Sons / Singapore Airlines, 51:49) was a joint venture until its merger into Air India in November 2024 - describe it in the **past tense**.

### Scene 14 - Also in this block (mention-only, one card each)
One slide with a card per item: **WHAT it is / WHERE it sits / what it is related to**.
| Item | One line |
|---|---|
| Realisation A/c | Vendor's closing account that shows what the vendor earns from selling its business; sits in Ch 13, links to purchase consideration |
| 4 purchase-consideration methods | Lump sum, net payment, net assets, intrinsic value/ share exchange ratio; different ways to compute the same "price" |
| Capital Reduction A/c | The pooling account of Scene 2; sits in Ch 14 |
| Cross-holdings | When the subsidiary also holds shares of the parent (or group companies hold each other); **excluded from the Intermediate syllabus** numericals |
| Foreign subsidiary | Needs currency translation; **excluded from the Intermediate syllabus** numericals |
| Disposal of a subsidiary | Not examined at Intermediate; consolidated up to date of disposal, gain/ loss on disposal |
| Mid-year acquisition | Time apportionment of profit; pre/post at the date |
| Dividend in a subsidiary | Pre-acquisition vs post-acquisition treatment |
| Bonus shares by the subsidiary | Capitalising reserves; pre/post effect |
| Revaluation on acquisition | Assets at fair value on acquisition date; extra depreciation after |
| Uniform policies, same reporting date | Prerequisite for adding lines |
| Consolidated Cash Flow, AS 3 style | Where consolidated statements appear in the CFS ecosystem |
| Disclosure (Form AOC-1, Sec 129, Schedule III) | The legal wrapper of consolidated statements |
| Reconstruction forms | Alteration, variation of rights, reduction, compromise, surrender |

### Scene 15 - Master map and word-bank
- **Goal:** one screen to take away.
- **On screen:** the decision tree from Scene 3 and the ladder from Scene 5 redrawn together, with each of the eight terms pinned in the place where it is born: *net assets* (at the bottom of every balance sheet), *acquisition date* and *control* (at the 50% mark), *cost of control* (at the first thing control triggers), *pre/post* (next to it), *minority interest* (below 100%), *statutory reserves* (on the "dies" side).
- **Close with the word-bank:** the eight terms, each in one plain line, which is also what goes in the printed handout.

---

## 5. Examples policy

- **Primary examples: fictional** (P Ltd, S Ltd, X Ltd, Y Ltd). They behave exactly as the standard needs them to and cannot go out of date.
- **Real-world examples: optional garnish**, never carrying a concept alone, each verified before shooting. Suggested keepers, all still to be **checked for current facts**: SBI's absorption of five associate banks (2017); the Brooke Bond + Lipton amalgamation (1993); Walmart-Flipkart (77%); Tata Digital-BigBasket (64%); Tata Motors-JLR (100%).
- **Do not use as capital-reduction or reconstruction examples:** Vodafone Idea's government-equity conversion (a debt-to-equity conversion, not a Sec 66 reduction); and any example whose current legal classification you cannot confirm (e.g. Titan Company, Hindustan Motors) until checked against the source.

---

## 6. Corrections already accepted (carry into the deck)

1. Buying shares to take control = **acquisition**; the target survives and becomes a subsidiary. Absorption = taking over the **business**; the transferor is wound up.
2. A name change or conversion to a private company is **not** external reconstruction. External reconstruction = business transferred to a new company with substantially the same shareholders; old company liquidated.
3. **Cost of control arises for every subsidiary**, wholly or partly owned; minority interest is the extra for partly owned.
4. Intuition (marriage vs swallowing) and the **AS 14 5-condition test** are shown as **two layers**, never merged.
5. AS 18's wider control definition is **not in the AS 21 chapter**: included only once we have the bare standard.

---

## 7. Open points for Pranav (defaults chosen so work can continue)

| # | Question | Default if you do not reply |
|---|---|---|
| 1 | Language on slides | English on slides; you speak in your own mix |
| 2 | Look and feel | Same navy / gold identity as your Question Bank materials |
| 3 | Do you want your **own speaker script** written out in full in the MD, or only cues? | **Cues only** (you teach better in your own words) |
| 4 | Should the printed handout version be a separate PDF? | Yes: generated from the same HTML (print view) |
| 5 | Provide AS 18 and bare AS 14 / 21 / 23 / 27 text | Without them, those points stay marked "to verify" |

---

## 8. Source discipline

- Terms and the **5 conditions** are taken from the July 2026 ICAI text in `books/ca-inter/smat-may-27-edition/all-modules/` (AS 14: `M2_C9_U2_...`, topics 2.3-2.6; AS 21: `M2_C10_U1_...`, topics 1.11-1.12).
- Page numbers quoted here were read from those files' page markers. The files are machine-converted and **not yet visually validated**; each page number should be checked against the PDF before it goes on a slide.
- Pages quoted from your own roadmaps (v4 / v5) are marked "per your roadmap" and **disagree in places** (e.g. AS 27 JCO/JCA topic numbers; Capital Reduction page ranges). v5 is treated as the later version; confirm against the PDF.

---

## 9. Coverage checklist (nothing major left out)

- [x] Winding-up / dissolution
- [x] Buyback vs reconstruction
- [x] Internal reconstruction; Capital Reduction A/c; Sec 61, 66, 230
- [x] External reconstruction
- [x] Amalgamation, absorption; merger vs purchase; 5 conditions
- [x] Consideration for amalgamation vs purchase consideration; 4 PC methods (mention)
- [x] Realisation A/c and transferee entries (mention)
- [x] Pooling vs purchase; goodwill / capital reserve; Amalgamation Adjustment Reserve
- [x] AS 13, AS 23, AS 21, AS 27 ladder; equity method; JCO / JCA / JCE; proportionate consolidation
- [x] Control (AS 21 and AS 18); exclusions; syllabus scope
- [x] Net assets; net results of operations; equity = capital + reserves
- [x] Cost of control; pre/post; dividends; mid-year; bonus shares
- [x] Minority interest; wholly vs partly owned
- [x] Statutory reserves
- [x] Intra-group adjustments (stock, fixed assets, mutual debts)
- [x] Cross-holdings and foreign subsidiaries (mention; out of syllabus numericals)
- [x] Disposal of subsidiary (mention; not examined at Inter)
