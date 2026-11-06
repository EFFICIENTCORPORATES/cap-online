# Kahaani — Reconstruction, Amalgamation and Consolidation: "the map before the maths"
## Flow and design record (Draft 3: deck built)

**Course:** CA Inter, Advanced Accounting (May 2027 attempt, July 2026 edition of the study material)
**Place in sequence:** straight after *Buyback of Securities* (Ch 12), before *Internal Reconstruction* (Ch 14), *Amalgamation of Companies* (Ch 13), AS 14 (Ch 9 Unit 2) and AS 21 / 23 / 27 (Ch 10 Units 1 - 3).

**Files**
| File | What it is |
|---|---|
| `deck/kahaani-restructuring-map.html` | The finished deck: one self-contained HTML file, 31 slides, 158 clicks in all. **Generated**: edit `deck/src/` and run `python3 deck/build_deck.py`. |
| `outline/SPEAKER-NOTES.md` | Your talking points, slide by slide. **Never part of the HTML.** Checked against the deck by `deck/check_notes_sync.py`. |
| `outline/REFERENCES.md` | ICAI topic number and printed page for every item. Page numbers confirmed by Pranav against the PDFs. |
| this file | Why the deck is built the way it is, and the slide map. |

---

## 1. Decisions (all confirmed by Pranav)

| Topic | Decision |
|---|---|
| Format | HTML slide deck, click-through animation (not a video). |
| Where it lives | A separate lectures area on the website, called **Kahaani**; earlier kahaanis will be kept there too. Not yet placed on the site. |
| Brand | Matches capranav.com and the "Practice with Pranav Bhaiya" slides (section 2). |
| Print | A **Print / Save PDF** button (also `P`) produces one landscape A4 page per slide, every step revealed, with a **CApranav.com** watermark on every page. |
| Speaker notes | In a separate Markdown file only; nothing of them is in the HTML. |
| T-format | **Equity & Liabilities on the left, Assets on the right.** |
| Net-assets story | **Arjun's company**: start, a year of profit, then a ₹10 lakh loan (spent half on PPE, half kept as cash, none on inventory). |
| One story for the rest | **Arjun Ltd** is the target; **Bhim Ltd** invests in it: first as a stranger (10%), then an associate (40%), a subsidiary with minority interest (80%), a wholly owned subsidiary (100%). |
| Pre / post timing | Always **9 : 3**: Bhim buys on 1 January in a 1 April - 31 March year. Never 6 : 6. |
| Control | AS 21's definition and the wider AS 18 definition (clause c) shown side by side; AS 18 text supplied by Pranav. |
| Consolidated cash flow statement | **Outside the syllabus** (shown as such on the mention cards). |
| Cross-holding | Only a syllabus exclusion; Sec 19 shown as the reason a subsidiary cannot ordinarily hold its parent's shares. |
| Scope of Lecture 1 | Concept level only: what it is, where it sits, how it relates. No journal entries. Every major topic at least mentioned (section 6). |

---

## 2. Brand, as built
Read from the site's own files (`capranav_com_revamped/public/assets/site.css`, `whiteboard-theme.css`, and the two existing slide pages).

| Element | Value |
|---|---|
| Stage | 16:9, centred, dark navy surround, cream paper `#f7f2e8` with a soft gold glow top right |
| Ink | `#10233f` |
| Accents | red `#e5484d` (eyebrows, "the dying side"), gold `#f2b84b` (hard offset shadow on cards), green `#0f8a70` (survives / goodwill / income), blue `#1f62d0` (Bhim), orange `#e8733f` (minority) |
| Type | Aptos / Segoe UI, no web fonts, so it works offline and drops into the website unchanged |
| Patterns | red caps eyebrow over a heavy headline; dark cards with gold shadow; one item revealed per click; red progress bar; round prev/next buttons and an "n / N · step i/j" counter |
| Wordmark / tagline | "P CA PRANAV" and "AIR 1 · AIR 1 · AIR 5" in the contents panel and on the closing slide |

**Controls:** `Space` / `→` / `Enter` / click = next step; `←` / `Backspace` = back; `T` = contents; `P` = print; `F` = full screen; `Home` / `End`; a slide can be opened directly with `#7` in the address.

**Print:** one slide per landscape A4 page, all steps shown, the watermark diagonal at about 8% opacity. In the print dialog choose "Save as PDF", Layout Landscape, Margins None, and tick **Background graphics**. A test PDF made through the same print stylesheet had **31 pages**; the watermark was confirmed by eye on sampled pages 1, 11, 20 and 29.

---

## 3. The running examples (₹ thousand; equity & liabilities left, assets right)

**Arjun's company (net assets)**
| Step | Equity & liabilities | Assets | Net assets |
|---|---|---|---|
| 1 Arjun starts | Capital 50 | Cash 5, inventory 10, investment 15, PPE 20 = 50 | 50 |
| 2 A year of business, profit 50 | Capital 50, reserves & surplus 50 (equity 100), trade payables 20 = 120 | Cash 10, inventory 20, receivables 20, investments 30, PPE 40 = 120 | 120 − 20 = **100** |
| 3 Borrows ₹10 lakh (1,000) | + Loan 1,000 = 1,120 | PPE 540, cash 510, rest unchanged = 1,120 | 1,120 − 1,020 = **100** |

**Arjun Ltd on 1 January (the acquisition date)**: capital 50; reserves 80 (statutory 10, general 15, P&L 25 + 30 = 55); trade payables 20 | cash 15, inventory 25, receivables 25, investments 35, PPE 50 = 150. **Net assets 130.** Year-2 profit 40, evenly: **30 before, 10 after**.

**Bhim's price list: ₹1.5 for every 1%**
| Stake | Pays | Share of net assets (130) | Premium | Treatment |
|---|---|---|---|---|
| 10% | 15 | 13 | 2 | AS 13, at cost |
| 40% | 60 | 52 | 8 | AS 23, equity method; goodwill inside the carrying amount |
| 80% | 120 | 104 | 16 | AS 21: goodwill 16; minority interest 26 on the date, 28 at 31 March |
| 100% | 150 | 130 | 20 | AS 21: goodwill 20; no minority interest |

**Checks:** 80%: 120 = 104 + 16; net assets 130 = 104 + 26. At 31 March Arjun Ltd's equity = 50 + 90 = 140; Bhim's 80% = 112 = 104 (pre) + 8 (post); minority 20% = 28 = 26 + 2.
**Associate (40% for 60):** post-acquisition profit 10 → Bhim's share 4 → carrying amount 64; dividend 5 → Bhim's share 2 → carrying amount 62 (= 40% × 135 + goodwill 8). Under AS 13: stays 60, dividend income 2. (This dividend belongs to the associate scene only; the subsidiary example assumes none.)
**ICAI's own associate illustration** (AS 23 p10.114 - 10.115, 45%, cost 15,00,000 → carrying amount 15,90,000) is quoted on the slide footer.

*Numbers are illustrative and chosen to be clean; they are not from the ICAI text.*

---

## 4. Slide map (generated from the deck)

| # | Id | Section | Slide | Clicks |
|---|---|---|---|---|
| 1 | `s00` | Start | Kahaani: the map before the maths | 8 |
| 2 | `s01` | 1 · Rescue before winding up | Rescue before winding up | 6 |
| 3 | `s02` | 2 · Internal reconstruction | Internal reconstruction | 4 |
| 4 | `s03a` | 3 · The big fork | Does the target company die? | 4 |
| 5 | `s03b` | 3 · The big fork | Dies vs lives: the contrast | 6 |
| 6 | `s04a` | 4 · Target dies | Three forms: what physically happens | 6 |
| 7 | `s04b` | 4 · Target dies | The five conditions of AS 14 | 8 |
| 8 | `s04c` | 4 · Target dies | Merger vs purchase, and the words | 5 |
| 9 | `s05a` | 5 · Target lives: the ladder | The ownership ladder | 4 |
| 10 | `s05b` | 5 · Target lives: the ladder | Buying shares vs buying the business | 5 |
| 11 | `s06a` | 6 · Net assets | Arjun's company: what net assets really are | 4 |
| 12 | `s06b` | 6 · Net assets | Bhim Ltd meets Arjun Ltd | 3 |
| 13 | `s06c` | 6 · Net assets | Bhim's price list: stake, price, share of net assets | 5 |
| 14 | `s07a` | 7 · Control | Control switches five things on | 8 |
| 15 | `s07b` | 7 · Control | Control: AS 21 and the wider AS 18 | 4 |
| 16 | `s07c` | 7 · Control | Line-by-line is not adding every item | 5 |
| 17 | `s08a` | 8 · Cost of control | Cost of control: goodwill or capital reserve | 4 |
| 18 | `s08b` | 8 · Cost of control | Cost of investment vs cost of control | 3 |
| 19 | `s09a` | 9 · Pre- and post-acquisition | The cut-off line: 9 months before, 3 months after | 4 |
| 20 | `s09b` | 9 · Pre- and post-acquisition | The reserves split: who gets which slice | 5 |
| 21 | `s09c` | 9 · Pre- and post-acquisition | Three small rules that ride on the cut-off line | 4 |
| 22 | `s10` | 10 · Minority interest | Minority interest: the outsiders' share | 5 |
| 23 | `s11` | 11 · Statutory reserves | Statutory reserves: three fates | 4 |
| 24 | `s12` | 12 · Intra-group adjustments | A group cannot make a profit by selling to itself | 6 |
| 25 | `s13a` | 13 · Associates and joint ventures | Same 40% stake, two treatments | 4 |
| 26 | `s13b` | 13 · Associates and joint ventures | AS 13 vs equity method: key differences | 5 |
| 27 | `s13c` | 13 · Associates and joint ventures | Joint ventures: JCO, JCA, JCE | 4 |
| 28 | `s14a` | 14 · Also in this block | Also in this block: mention cards (1 of 2) | 7 |
| 29 | `s14b` | 14 · Also in this block | Also in this block: mention cards (2 of 2) | 7 |
| 30 | `s15` | 15 · The map and the word-bank | The master map: where each word is born | 8 |
| 31 | `s16` | 15 · The map and the word-bank | The eight words, in plain language | 3 |

---

## 5. Examples policy
- Primary examples are fictional (Arjun, Bhim, Sick Ltd): they behave as the standard needs and cannot go out of date.
- Real-world examples are optional, never carry a concept alone, and are checked before use. Candidates: SBI's absorption of five associate banks (2017); Brooke Bond + Lipton (1993); Walmart-Flipkart (77%); Tata Digital-BigBasket (64%); Tata Motors-JLR (100%). **Not** used as capital-reduction examples: Vodafone Idea's government-equity conversion, or anything whose classification cannot be confirmed (Titan, Hindustan Motors). Vistara merged into Air India in November 2024: past tense only.

## 6. Corrections accepted
1. Buying shares to take control = acquisition (the target survives). Absorption = taking over the business (Ch 13 p13.3).
2. A name change or conversion to a private company is not external reconstruction (Ch 14 p14.3).
3. Cost of control arises for every subsidiary; minority interest is the extra for a partly owned one.
4. Intuition (marriage vs swallowing) and the AS 14 five-condition test are two layers, never merged.
5. AS 18's wider control definition (clause c) is now quoted from the text Pranav supplied.
6. Cross-holding is a syllabus exclusion only; Sec 19 is at AS 21 topic 1.1, p10.4.
7. The consolidated cash flow statement is outside the syllabus.

## 7. Still to do (not part of the deck itself)
| Item | Note |
|---|---|
| Place the deck in the Kahaani area of capranav.com | The site's slide pages are standalone HTML under `capranav_com_revamped/public/practice-with-pranav-bhaiya/slides/`; a Kahaani area does not exist yet. The deck is a single file with no network dependency, so it can be dropped in as it is. |
| Verify any real-world example before filming | Section 5. |

## 8. Coverage checklist (nothing major left out)
- [x] Winding-up / dissolution; rescue before winding up (s01)
- [x] Buyback vs reconstruction (s01); internal reconstruction, Capital Reduction A/c, Sec 61, 66 (s02, s14)
- [x] External reconstruction, amalgamation, absorption (s04a)
- [x] Merger vs purchase; five conditions; "consideration for the amalgamation" (s04b, s04c)
- [x] Realisation A/c, 4 purchase-consideration methods, transferee's entries (s04c, s14a)
- [x] Pooling vs purchase; Amalgamation Adjustment Reserve; goodwill / capital reserve (s04c, s11)
- [x] Ownership ladder: AS 13, AS 23, AS 21, AS 27; AS 18 thresholds (s05a)
- [x] Hostile takeover vs absorption (s05b)
- [x] Net assets, equity, net results of operations (s06a, s09a)
- [x] Control: AS 21 and AS 18; exclusions; syllabus limits (s07a, s07b)
- [x] Line-by-line consolidation (s07c)
- [x] Cost of control; cost of investment vs cost of control (s08a, s08b)
- [x] Pre / post acquisition, 9 : 3, reserves split, dividends, time basis, bonus shares (s09a - s09c)
- [x] Minority interest; wholly vs partly owned (s07c, s10)
- [x] Statutory reserves (s11)
- [x] Intra-group adjustments (s12)
- [x] Equity method vs cost method; JCO / JCA / JCE; proportionate consolidation (s13a - s13c)
- [x] Cross-holding and Sec 19; foreign subsidiary; disposal; mid-year acquisition; revaluation; uniform policies; reporting dates; disclosure; reconstruction forms (s14a, s14b)
- [x] Consolidated cash flow statement: outside the syllabus (s14b)
