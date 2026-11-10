# Dividend (divisible profit) vs Buy-back: pages, the difference, traps per illustration, CRR rule

_Written 2026-11-09 by an AI session for Pranav (teaching aid, not student-facing). Sources: `M3_C11_U1_ Preparation of Financial Statements_BEAUTIFIED.md` (topic 1.6 only; Balance Sheet and P&L are already covered) and `M3_C12_U0_ Buyback of Securities_BEAUTIFIED.md`, under `books/ca-inter/smat-may-27-edition/all-modules/`. Page numbers are printed pages from the converted files; not checked against the PDFs (which Pranav attached in the chat but are not in the repo). Figures were recomputed with a script. Method: `.claude/skills/chapter-illustration-traps/SKILL.md`._

**Status:** illustration traps done. **Not done:** the "what is new in TYK" list for Chapter 12 and for the dividend-related Chapter 11 TYK; and the teaching deliverable itself (deck / note), because Pranav had not chosen a format when the session ended.

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

**Same company, both calculations** (ICAI's own Ch 11 Ill. 1 data: equity ₹80,00,000, 9% preference ₹17,50,000, general reserve ₹25,00,000): base = ₹1,22,50,000. Dividend: 10% -> cap ₹12,25,000; actual draw ₹6,57,500. Buy-back (my application of the Ch 12 percentages to that data, **not in the book**): amount cap 25% × ₹1,22,50,000 = ₹30,62,500 **if preference capital counts as paid-up capital**, or 25% × ₹1,05,00,000 (equity ₹80,00,000 + free reserves ₹25,00,000) = ₹26,25,000 if it does not (see section 5: the chapter does not say); share cap 25% × 8,00,000 = 2,00,000 shares (equity only); debt test needs the company's debt.

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

- **Does "paid-up capital" in the buy-back tests include preference capital?** The Chapter 12 text and summary say "total paid-up capital and free reserves" for the resource and debt-equity tests, and "paid-up equity capital" for the board-resolution threshold and the shares-outstanding test. No Chapter 12 worked example that applies a test (Ill. 5, Ill. 6, TYK Q8, Q10) has preference capital on the balance sheet, so the book never shows the treatment. Chapter 11 Ill. 1 (dividend) does count preference capital as paid-up capital. Outside the chapter, the Companies Act wording "paid-up capital" is generally read as all classes of paid-up share capital: confirm before teaching, and tell students the chapter is silent.

- Chapter 12 text p12.3 states the share-outstanding test as 25% of "total paid-up capital and free reserves"; the summary (p12.31) and the illustrations use 25% of the **number of shares outstanding** / paid-up equity capital. Teach the illustrations' version.
- Chapter 12 says securities premium counts as free reserves for Sec 68 (Explanation II, p12.7). Chapter 11 does not say whether it counts for dividends; nothing in these chapters says it cannot be used for a dividend. Do not assert it.
- Chapter 11 TYK Q15 answer (p11.74): the alternative working prints "(12+14+10)/5 = 12%"; it should be /3. The question lists five years but only the last three count.
