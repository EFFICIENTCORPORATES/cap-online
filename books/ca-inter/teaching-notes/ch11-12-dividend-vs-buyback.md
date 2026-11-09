# Dividend (divisible profit) vs Buy-back: pages, the difference, traps per illustration, CRR rule

_Written 2026-11-09 by an AI session for Pranav (teaching aid, not student-facing). Sources: `M3_C11_U1_ Preparation of Financial Statements_BEAUTIFIED.md` (topic 1.6 only; Balance Sheet and P&L are already covered) and `M3_C12_U0_ Buyback of Securities_BEAUTIFIED.md`, under `books/ca-inter/smat-may-27-edition/all-modules/`. Page numbers are printed pages from the converted files; not checked against the PDFs (which Pranav attached in the chat but are not in the repo). Figures were recomputed with a script. Method: `.claude/skills/chapter-illustration-traps/SKILL.md`._

**Status:** illustration traps done (sections 3-4). Chapter 12 TYK "what is new" done 2026-11-09 (section 6). **Not done:** the same for the dividend-related Chapter 11 TYK (MCQ 5, 8, 9; Q15 Z Ltd); and the teaching deliverable itself (deck / note), because Pranav had not chosen a format.

## 1. Where it is in the study material

**Chapter 11 Unit 1 (dividend)**

| Part | Pages |
|---|---|
| Topic 1.6 Distributable Profit: meaning of dividend, Sec 123, depreciation, dividend out of reserves (2014 Rules, 3 conditions), transfer to reserves, interim dividend, preference and partly paid shares, Unpaid Dividend Account (Sec 124) | pp 11.18 – 11.24 |
| Illustration 1 (dividend out of general reserve): the **only** dividend calculation illustration | pp 11.24 – 11.25 |
| TYK: MCQ 5, MCQ 8 (interim dividend after a loss), MCQ 9 (10% vs 8% average) | pp 11.50 – 11.52 |
| TYK: scenario Q15 Z Ltd (dividend out of reserves) | question p11.59; answer pp 11.74 – 11.76 |
| TYK answers | p11.61 onwards |

**Chapter 12 (Buyback)**

| Part | Pages |
|---|---|
| Introduction, Sec 68 conditions, the three tests, CRR rule (Sec 69), free reserves | pp 12.1 – 12.6 (Note-1 same-kind rule p12.2; tests p12.3; CRR p12.5) |
| Sec 70 | pp 12.6 – 12.7 |
| Illustrations 1 / 2 / 3 / 4 / 5 / 6 | p12.7 / p12.10 / p12.14 / p12.18 / p12.23 / p12.25 – 12.29 (Note-5 p12.29) |
| Summary | p12.30 |
| TYK: MCQ 1-6, theory Q7, scenario Q8-Q11 | pp 12.31 – 12.38 |
| TYK answers | pp 12.38 – 12.52 |

## 2. The two calculations side by side

| | Dividend out of reserves (Ch 11 topic 1.6, Ill. 1) | Buy-back (Ch 12, Sec 68) |
|---|---|---|
| Question answered | How much can be paid to shareholders from profits and reserves? | How much (and how many shares) may the company buy back? |
| Governing rule | Sec 123; Declaration and Payment of Dividend Rules, 2014 | Sec 68 - 70 |
| Cap in amount | **10%** of (paid-up share capital + free reserves) can be drawn from reserves | **25%** of (paid-up capital + free reserves) (resource test) |
| Second limit | Reserves left after the draw must stay at or above **15% of paid-up capital** | Shares bought back in a year ≤ **25% of shares outstanding** |
| Third limit | Dividend rate ≤ **average rate of the last 3 years** | Debt after buy-back ≤ **2 × (paid-up capital + free reserves)** |
| First priority | The draw first sets off the current year's losses | None (not an appropriation of profit) |
| Which reserves | Free reserves only; ICAI's illustration uses general reserve only (capital and revaluation reserve excluded) | Free reserves **or** securities premium **or** proceeds of a fresh issue of a different kind. Revaluation reserve excluded |
| Capital | Untouched | Shares **cancelled**; capital falls |
| Capital Redemption Reserve | Not involved | Nominal value bought back is transferred to CRR (to the extent funded from free reserves or securities premium) |
| Who decides | Board declares | **Special resolution**, unless the buy-back is 10% or less of paid-up equity capital + free reserves (then a board resolution suffices) |

**Look-alike traps:** 10% means a cap on drawing from reserves (dividend) but the board-resolution threshold (buy-back). 25% appears twice in buy-back (amount; number of shares).

**Same company, both calculations** (ICAI's own Ch 11 Ill. 1 data: equity ₹80,00,000, 9% preference ₹17,50,000, general reserve ₹25,00,000): base = ₹1,22,50,000. Dividend: 10% -> cap ₹12,25,000; actual draw ₹6,57,500. Buy-back (my application of the Ch 12 percentages to that data, **not in the book**): 25% -> amount cap ₹30,62,500; share cap 25% × 8,00,000 = 2,00,000 shares; debt test needs the company's debt.

## 3. Main trap in each illustration

**Ch 11 Illustration 1, XYZ Ltd (p11.24)**
- The draw is **net of this year's profit**: 10% dividend ₹8,00,000, current profit after preference dividend ₹3,00,000 − ₹1,57,500 = ₹1,42,500, so ₹6,57,500 is drawn.
- Preference dividend ranks first: 9% × ₹17,50,000 = ₹1,57,500.
- Three conditions all tested: rate vs 12% average; draw ≤ 10% × ₹1,22,50,000 = ₹12,25,000; reserves left ₹18,42,500 ≥ 15% × ₹97,50,000 = ₹14,62,500.
- Preference capital counts as paid-up capital; free reserves here = general reserve only.

**Ch 12 Illustration 1, M Ltd (p12.7): basic entries**
- 20% of 3,00,000 equity shares at ₹15 = 60,000 shares: nominal ₹6,00,000, premium ₹3,00,000. Preference capital not included.
- Loss on investments sold (₹5,00,000) is debited to **P&L** (reduces free reserves).
- Premium against Securities Premium; **CRR ₹6,00,000** from revenue reserve. The three tests are not applied in this illustration.

**Illustration 2, Anu Ltd (p12.10): redemption of preference shares and buy-back together**
- **CRR ₹80 crore = ₹75 (preference) + ₹5 (equity nominal)**, both from revenue reserve (no fresh issue).
- ₹20 crore premium (₹40 × 50 lakh) against Securities Premium (₹25 crore). Preference shares go first to a "Preference shareholders" account, then are paid. Capital reserve untouched.

**Illustration 3, Dee Ltd (p12.14): CRR is not the full nominal value**
- ₹2 lakh of preference shares had been issued two months earlier **for the buy-back**: **CRR is ₹3 lakh, not ₹5 lakh**. ICAI gives no working; 3 = 5 − 2 is my reconstruction.
- Equity may be bought back out of preference proceeds because the shares are of a **different kind** (Note-1, p12.2). Premium ₹20 lakh against Securities Premium (₹22 lakh). ₹8 lakh loss on investments to P&L.

**Illustration 4, Extra Ltd (p12.18): many items together**
- Preference redeemed at **10% premium** (₹2 crore), charged to revenue reserve by ICAI.
- **Own debentures:** face ₹2.20 lakh vs cost ₹2.00 lakh: ₹0.20 lakh profit on cancellation, credited to revenue reserve by ICAI.
- **ESOP:** 50,000 options exercised at ₹20 vs ₹30 market; liability ₹5 lakh (₹10 × 50,000) cleared by the shares: bank ₹10 lakh, equity ₹5 lakh, Securities Premium ₹10 lakh.
- **CRR ₹50 lakh = preference ₹20 lakh + equity ₹30 lakh.**
- ICAI's solution leaves **revenue reserve at (1.80), a negative balance** (CRR uses all ₹50 lakh, then the preference premium is charged on top). Flagged, not corrected.

**Illustration 5, Pratham Ltd (p12.23): the debt-equity test**
- **Revaluation reserve is excluded.** Free reserves ₹42.80 lakh; equity ₹72.80 lakh.
- **The CRR transfer also reduces equity**, because CRR is not a free reserve (Note-5, p12.29). Equity after the buy-back = present equity − amount paid − CRR transfer.
- Simultaneous equations (price = 3 × nominal): y = ₹38,85,000, i.e. 1,29,500 shares; x (CRR) = ₹12,95,000. The book labels these "crores"; they are rupees.

**Illustration 6, Perrotte Ltd (p12.25): all three tests, three situations**
- Offer price ₹25 × 120% = ₹30. Maximum = **least of the three tests**.
- **Free reserves ₹420 crore** (general reserve + securities premium + P&L). **Infrastructure Development Reserve ₹180 crore is excluded** (created to satisfy the Income-tax Act).
- Shares outstanding: 8.25 crore. Resources: 25% × ₹750 crore ÷ ₹30 = 6.25 crore.
- **Debt-equity decides:** loans ₹1,800 crore or ₹1,500 crore -> **nil**; ₹1,200 crore -> **3.75 crore shares**.
- Entries only for the qualifying situation: premium ₹75 crore from Securities Premium, CRR ₹37.5 crore from general reserve.

## 4. When is the transfer to CRR not required?

Sec 69 (p12.5) requires CRR when the buy-back is paid out of **free reserves or securities premium**. So it is **not required to the extent the buy-back is funded from the proceeds of a fresh issue** of shares or other specified securities (the third source in Sec 68(1)(c)).
- Shown in **Illustration 3** (nominal ₹5 lakh, fresh preference issue ₹2 lakh, CRR ₹3 lakh).
- The fresh issue must be of a **different kind** (Note-1, p12.2).
- Premium on buy-back is adjusted against free reserves or securities premium, not CRR (p12.6). P&L balances count as free reserves, so a buy-back out of profits needs CRR.
- CRR is not a free reserve (p12.29), so it changes the debt-equity test; Illustration 6 assumes the buy-back is out of reserves and says so.
- These two chapters give **no other exception**.

## 5. Things to check against the PDF

- Chapter 12 text p12.3 states the share-outstanding test as 25% of "total paid-up capital and free reserves"; the summary (p12.31) and the illustrations use 25% of the **number of shares outstanding** / paid-up equity capital. Teach the illustrations' version.
- Chapter 12 says securities premium counts as free reserves for Sec 68 (Explanation II, p12.7). Chapter 11 does not say whether it counts for dividends; nothing in these chapters says it cannot be used for a dividend. Do not assert it.
- Chapter 11 TYK Q15 answer (p11.74): the alternative working prints "(12+14+10)/5 = 12%"; it should be /3. The question lists five years but only the last three count.

## 6. Chapter 12 TYK: illustration vs TYK, and what is new (2026-11-09)

Figures recomputed with a script; all four balance sheets and every ICAI figure reconcile. Page numbers are printed pages inferred from the odd-page headers of the converted file, not checked against the PDF.

### 6.1 One-liner comparison

| TYK (question p / answer p) | Closest illustration | One-liner |
|---|---|---|
| **MCQ 1-6** (p12.31-12.32) | Text, Note-1 | Only rule-recall; one wording gap (MCQ 2, below). |
| **Q7 theory** (p12.33) | Text pp 12.1-12.6 | Sec 68 conditions; ICAI's answer only points to "Para 1.1 and 1.2". |
| **Q8 SMM Ltd** (p12.33 / pp12.38-12.41) | **Ill 6 Perrotte** | Same three-test drill with the Infrastructure Development Reserve excluded; new: the premium is more than Securities Premium, so the rest comes from General Reserve / P&L. |
| **Q9 KG Ltd** (p12.33-12.35 / pp12.41-12.43) | Ill 1 (entries), Ill 3 (balance sheet) | New: a **bonus issue after the buy-back, out of CRR, on the reduced share count**; and a **profit** (not loss) on selling investments. |
| **Q10 Competent Ltd** (p12.35-12.37 / pp12.43-12.49) | Ill 5 + Ill 6 | New: not "find the maximum" but **"is 25,000 shares allowed?"**, with a verdict; short-term borrowings count as debt. |
| **Q11 Z Ltd** (p12.37 / pp12.49-12.51) | Ill 2 Anu + Ill 4 Extra | No new adjustment type; new: both premiums from **different** sources, and cash is the **balancing figure of a bank account**. |

### 6.2 What is new, question by question

**Q8 SMM Ltd (p12.33; answer p12.38)**
- **Same as Illustration 6:** shares test 30 crore, resources test 24 crore (free reserves 1,080 + 400 + 200 = 1,680; the 320 Infrastructure Development Reserve is out), debt-equity test by simultaneous equation (CRR x = 320, buy-back y = 960, so 32 crore shares). Maximum = least = **24 crore**.
- **New:** premium = 24 crore x (30 - 10) = **₹480 crore, more than Securities Premium ₹400 crore**. ICAI debits SP 400 and **General Reserve / P&L 80**. In Illustration 6 the premium (₹75 crore) fitted inside SP.
- **New:** CRR ₹240 crore is also taken from General Reserve / P&L, so the free reserve used is **80 + 240 = ₹320 crore** (the answer says "General Reserve / Profit & Loss A/c" without choosing).
- **Situation II (loans 6,000):** minimum equity 3,000 is already **above present equity 2,880**, so the answer is nil before any buy-back is considered. Same logic as Illustration 6's ₹1,800 crore case.

**Q9 KG Ltd (p12.33-12.35; answer p12.41)**
- **New: bonus after the buy-back.** One-for-four bonus is on **90 lakh** shares left (1,200 - 300 = 900), not 120 lakh: bonus **₹225 lakh**, not 300. Capital ends at 1,125.
- **New: the bonus comes out of CRR**, the only use CRR allows (Sec 69(2), p12.29). CRR 200 (old) + 300 (new) = 500, less 225 = **275**. The old ₹200 lakh CRR is not used for the buy-back; it only funds the bonus.
- **New direction:** investments sold for 75 vs cost 74, a **profit** of ₹1 lakh to P&L (Illustrations 1 and 3 had losses).
- **Premium split:** 30 lakh shares x ₹15 = 450; nominal 300, premium 150 from Securities Premium (175 -> 25). CRR 300 = General Reserve 265 + P&L 35 (ICAI's note says any free reserve will do). Cash 740 + 75 - 450 = **365**.
- ICAI does not test the limits here. My check: 25% of (1,200 + 610 free reserves) = 452.5 against 450, and 30 lakh is exactly 25% of 120 lakh shares: **both pass, one by a hair**.

**Q10 Competent Ltd (p12.35-12.37; answer pp12.43-12.49)**
- **New requirement:** "comment whether the buy-back is within the Act", then journal and balance sheet. The illustrations only computed the maximum. Here the three maxima (31,250 / 39,062 / 28,750) are **compared with the 25,000 proposed**.
- **Debt includes short-term borrowings:** 18,75,000 + 10,00,000 + 16,50,000 = ₹45,25,000, minimum equity 22,62,500.
- **Two different CRR figures:** the debt-equity equation uses CRR for the **maximum** (x = ₹2,87,500, y = ₹5,75,000, 28,750 shares); the **journal** uses CRR for the **actual** 25,000 shares = ₹2,50,000. Easy to mix up.
- **Source of funds:** the whole premium ₹2,50,000 exhausts Securities Premium (nil left); CRR comes from revenue reserve. The 39,062 is rounded down from 39,062.5.
- My check after the buy-back: equity without CRR = 10,00,000 + 1,25,000 + 12,50,000 = 23,75,000; twice that, 47,50,000, covers debt 45,25,000.
- The question prints P&L as "1,25.000" (typo for 1,25,000); the total 18,75,000 confirms it.

**Q11 Z Ltd (p12.37; answer p12.49)**
- **Not new in type:** preference redemption plus buy-back together (Ill 2), premium on preference redemption (Ill 4), investments sold to raise cash (Ill 1).
- **New combination:** preference premium ₹500 lakh goes to **P&L**; equity premium ₹1,600 lakh goes to **Securities Premium** (1,600, used up). Ill 4 charged the preference premium to revenue reserve.
- **CRR ₹6,600 lakh = preference 5,000 + equity 1,600**, from General Reserve, on top of the existing CRR 2,000 (closing 8,600).
- **Cash is a balancing figure:** 4,600 + 5,000 (investments) - 5,500 - 3,200 = **₹900 lakh**, shown as a working-note bank account.
- **Profit** on investments ₹300 lakh credited to P&L (5,000 - 4,700). Closing P&L = 600 + 300 - 500 = 400.
- **ICAI inconsistency:** entry 3's narration says the preference premium is adjusted "through securities premium", but the entry debits P&L. Teach the entry; do not quote the narration.
- The tests (shares, resources, debt-equity) are not asked here. 160 lakh shares is 10% of 1,600 lakh.

**MCQ and theory (one line each)**
- **MCQ 2 (answer c):** option (b) says "proceeds of the issue of **any** shares". The text (Note-1, p12.2) allows it only for shares of a **different kind**. Teach the text, not the option.
- **MCQ 4 (answer b):** partly paid shares cannot be bought back (only fully paid-up). The same option set tests 25% of **total capital + free reserves** in (a) and 25% of **equity capital** in (c); both are the look-alike pair from section 2.
- **MCQ 1, 3, 5, 6:** direct recall (25%; CRR; premium against free reserves or SP; option (c) discourages hostile bids).
- **Q7:** no new rule; ICAI's answer only refers to Para 1.1 and 1.2.

### 6.3 Same as an illustration, so skipped
- Q8 shares and resources tests, IDR exclusion, nil result when debt is too high: **Illustration 6**.
- Q9 and Q10 CRR entry and cancellation entries: **Illustration 1**; simultaneous equation for CRR in the debt test: **Illustration 5**.
- Q11 CRR = preference + equity: **Illustration 2**; premium on preference redemption: **Illustration 4**.
