# AS 2 — Valuation of Inventories

## "Godown Ka Hisaab" — Full Production Storyboard

> **Chapter:** AS 2 — Valuation of Inventories
> **Course:** CA Inter — Advanced Accounting
> **Brand:** `#pranavBhaiya` · `#NewtonofAccounts` · VC Gurukul, Noida · CA Pranav Pratik Tulshyan
> **Format:** Click-to-advance interactive (visual-novel / comic-strip style), silent, static HTML/CSS/JS
> **Status:** Production spec — this is the single source of truth for the build.

---

## 0. How to read this document

This is the **shooting script**. Every click the viewer makes is one numbered **Step**. Each Step lists:

- **Trigger** — what advances to it (click / Enter / Space; ← goes back one Step).
- **On screen** — the full visible state *after* this Step fires (states are cumulative within a scene unless it says "clears").
- **Cast & position** — which characters are on stage and where.
- **Emotion** — the emoji badge floating near a character's head (only when emotion changes).
- **Dialogue / Panel (verbatim)** — exact text. **Hinglish is preserved exactly — never translate.**
- **Reveal** — the entrance animation for whatever is new this Step.

Two kinds of Step:

1. **`[CARD]`** — a full-frame interstitial (title card / scene-transition card / concept card). Replaces the stage.
2. **`[BEAT]`** — a story beat layered onto the current scene's set.

---

## 1. Technical architecture & routing

| Decision | Spec |
|---|---|
| **Hosting** | Cloudflare Pages, static folder upload. No build step, no npm, no backend. |
| **Anchor** | `index.html` is the AS-02 chapter (its own independent site / subdomain `as02.…`). Each of the 34 chapters is a separate, independent project. |
| **Scene routing** | **Single page, hash-based scene anchors.** `…/#scene1`, `…/#scene7`. Whole chapter plays as one continuous boxed frame (no reload between scenes). Each scene URL is deep-linkable & shareable. |
| **Resume** | Current Step index is mirrored to the URL hash + saved to `localStorage` so a refresh resumes where the viewer left off. |
| **Stage** | Fixed **16:9 boxed frame** ("video" feel), centered, letterboxed with a soft border on odd screens. |
| **Mobile** | A website cannot force rotation. In portrait on a phone → show a **"🔄 Rotate your device for the best view"** overlay. Optional: CSS-rotate the stage 90° so it still plays in landscape. |
| **Offline** | System fonts only (`'Segoe UI', system-ui, sans-serif`). No CDN, no Google Fonts call. Any raster art lives in `/assets/`. |
| **Modularity** | One shared component library reused across all 34 chapters; each chapter = a thin **beats data file**. Producing a new chapter = writing its script data, not rebuilding UI. |

### Folder shape (per chapter)
```
as02-inventory/
├── index.html                ← anchor: loads the chapter
├── assets/                   ← any raster art, favicon, logo
└── (component library + as02 beats data, modular files)
```

---

## 2. Brand & global furniture

- **Brand palette (only these colours):**
  | Token | Hex | Use |
  |---|---|---|
  | Navy | `#1A1A2E` | Concept boxes, name (Pranav), stage border, text |
  | Orange | `#E8813A` | Progress bar, highlight boxes, name (Rolly) |
  | Gold | `#F0A500` | Name (Sethji), accents |
  | Purple | `#6B3FA0` | Name (Diya), Weighted-Avg panel |
  | Green | `#2D8653` | Healthy numbers, FIFO panel, "LOWER ✓" |
  | Red/Loss | `#C0392B` | Losses, red cross, expiry flags |
  | Background | `#FDF8F3` (warm off-white) / navy-tinted for godown | Stage bg |
- **Footer (persistent, small, bottom of stage):** `AS 2 — Valuation of Inventories · CA Inter Advanced Accounting · #pranavBhaiya #NewtonofAccounts · VC Gurukul, Noida`
- **Top chrome (always on):**
  - Thin **orange progress bar** at the very top, grows left→right with Step number.
  - **Step counter** top-right: `Step 7 / 47`.
  - Scene tag top-left: `Scene 3 · Sethji Reviews`.
- **Bottom hint:** `click to continue ▶` (or `↵ Enter`) fades in when the current Step's reveal has finished.
- **Controls:** click / **Enter** / **Space** = next · **←** = back · (optional) **R** = restart scene.
- **Transitions:** new beat fades in (opacity 0→1, 200ms ease); dialogue bubbles slide up (translateY 12px→0, 250ms ease). `[CARD]` steps cross-fade the whole frame (300ms).

---

## 3. Cast — visual identity (flat vector, consistent every scene)

Built from simple flat shapes. Each character is recognisable by **silhouette + signature colour + one accessory**. Face is neutral by default; **emotion is shown by an emoji badge** floating top-right of the head, never by redrawing the face. A **floating name label** in the character's colour sits permanently under the feet.

| Character | Silhouette cues | Signature colour | Accessory | Name label |
|---|---|---|---|---|
| **ROLLY** — junior accountant | Young woman, round face, **neat bun**, smaller build | Orange | **Orange dupatta/scarf** + navy top + clipboard/laptop | Orange `#E8813A` |
| **PRANAV** — CA auditor (teacher) | Slim man, short hair, **glasses**, slightly taller | Navy | **Navy blazer** + light shirt + pen/invoice | Navy `#1A1A2E` |
| **SETHJI** — owner, BCPL | **Stocky**, older, short **grey hair** | Gold | **Cream kurta**, arms crossed / leaning | Gold `#F0A500` |
| **DIYA** — narrator/explainer | Young woman, **wavy hair**, cheerful | Purple | **Purple dupatta**, points to panels | Purple `#6B3FA0` |

### Emotion emoji set (use sparingly — only at real beats)
| Moment | Character | Emoji |
|---|---|---|
| Satisfied / confident | Rolly, Sethji | 🙂 |
| Aha / insight | Rolly | 💡 |
| Thinking / noting a problem | Pranav | 🤔 |
| Mild concern | Sethji | 😟 |
| Warm acceptance / laugh | Sethji | 😄 |
| Explaining a rule | Diya / Pranav | 👉 |

> Diya is optional per scene; use her for concept callouts when no main character is mid-dialogue. If a beat already has Pranav explaining, Diya stays off-stage to avoid clutter.

---

## 4. Component library (build once, reuse ×34)

| Component | Responsibility |
|---|---|
| `Stage` | 16:9 boxed frame, background swap per scene, letterbox, mobile rotate-overlay |
| `Chrome` | Progress bar + step counter + scene tag + footer + "click to continue ▶" hint |
| `SceneEngine` | Holds the beats array, current index; handles click/Enter/Space (next), ← (back); writes hash + localStorage; runs fade/slide transitions |
| `Character` | Vector body by `who`, signature colour, accessory, `pose` (stand/walk), `emoji` badge, floating name label |
| `SpeechBubble` / `ThoughtBubble` | White rounded bubble + tail; speaker name above in their colour; thought = cloud tail with dots |
| `NarratorBox` | Neutral caption band for narrator beats (no speaker) |
| `ConceptBox` | Navy panel, white text — rules/definitions |
| `HighlightBox` | Orange panel — key takeaways |
| `CalcPanel` | Step-by-step calculation rows (monospace), supports a "LOWER ✓" tag and red loss rows |
| `NumberTable` | White table, thin navy border, monospace — spreadsheets & batch tables |
| `FlowFx` | Small visual effects: green glow on a healthy number, red ✗ cross, red value "flowing" from inventory → P&L |
| `SceneCard` | `[CARD]` interstitial: "Scene N · Title", optional subtitle |
| `TitleCard` / `ClosingCard` | Opening & closing brand cards |

---

# 5. The Storyboard — every scene, every step

> **Master step count: 47** (1 title card + 12 scene cards + 34 content beats).
> The counter reads `Step X / 47`. Scene cards are quick; the viewer clicks through them like chapter breaks.

---

## STEP 1 — `[CARD]` Opening title

- **Trigger:** Visible on load (no click needed — first beat shows on load).
- **On screen:** Navy full-frame card.
  - Eyebrow: `CA Inter · Advanced Accounting`
  - Title (large, white): **AS 2 — Valuation of Inventories**
  - Subtitle (orange): **"Godown Ka Hisaab"**
  - Bottom, small: `#pranavBhaiya · #NewtonofAccounts`
- **Reveal:** title fades up; subtitle slides up 12px after 150ms.
- **Hint:** `click to begin ▶`

---

## SCENE 1 — Setting the stage
*Set: BCPL godown interior, wide. Navy-tinted warm background. Flat shelves with simple boxes (coconut soap), blue canisters (cooking oil), shrink-wrap sachets, biscuit cartons — low-contrast, subtle. Rolly in the aisle with a clipboard.*

### STEP 2 — `[CARD]` Scene transition
- `Scene 1 · Setting the Stage`
- Subtitle: *BCPL Warehouse, Noida — last week of March.*

### STEP 3 — `[BEAT]` Narrator
- **On screen:** Godown set fades in. Rolly stands mid-aisle, clipboard, neutral.
- **Cast:** Rolly (center-left, standing).
- **NarratorBox (bottom):** "Last week of March. The financial year was closing."
- **Reveal:** set fades in; narrator box slides up.

### STEP 4 — `[BEAT]` Narrator
- **NarratorBox:** "Rolly had been at BCPL's Noida warehouse for two days — counting boxes, checking batches, making notes."
- **Stage:** Rolly does a subtle **walk** a few steps along the aisle (simple translate, ~1s), then settles.

### STEP 5 — `[BEAT]` Narrator + emotion
- **NarratorBox:** "Sethji's FMCG godown: coconut soap, cooking oil, shampoo sachets, biscuit cartons — stacked to the ceiling."
- **Emotion:** Rolly 🙂 (satisfied), looking up at the neat shelves.
- **Reveal:** the four product groups on the shelves each pop in lightly, left→right.

---

## SCENE 2 — Rolly's valuation (the mistake)
*Set: cuts to a laptop / spreadsheet view — a clean white table floating on a soft navy desk surface. Numbers type in row by row.*

### STEP 6 — `[CARD]` Scene transition
- `Scene 2 · Rolly's Valuation`
- Subtitle: *The number that looked too good.*

### STEP 7 — `[BEAT]` Rolly thought bubble
- **Cast:** Rolly (right side), laptop open.
- **ThoughtBubble (Rolly):** "Inventory is worth what you can sell it for. Market price. Simple."
- **Reveal:** thought cloud fades+floats up with two trailing dots.

### STEP 8 — `[BEAT]` Spreadsheet builds (row by row on this single step's reveal)
- **NumberTable (floats center):** rows animate in top→bottom:
  ```
  ITEM           | QTY          | ROLLY's VALUE
  Coconut Soap   | 2,000 boxes  | ₹85 per box
  Hair Oil       |   500 bottles| ₹195 per bottle
  Cooking Oil    |   300 litres | ₹130 per litre
  ─────────────────────────────────────────────
  TOTAL INVENTORY (full godown) : ₹1.24 crore
  ```
- **Note:** label the total **"(full godown)"** — the three rows are illustrative samples, not the full sum, so a sharp student doesn't add them and get confused.

### STEP 9 — `[BEAT]` The big number + narrator
- **FlowFx:** **₹1.24 Crore** enlarges with a **green glow** — looks very healthy.
- **NarratorBox:** "A very healthy number."
- **Emotion:** Rolly 🙂 (quietly pleased).

---

## SCENE 3 — Sethji reviews
*Set: small back office. Table, simple whiteboard behind. Sethji + Rolly seated.*

### STEP 10 — `[CARD]` Scene transition
- `Scene 3 · Sethji Reviews`

### STEP 11 — `[BEAT]` Sethji speaks
- **Cast:** Sethji (left, leaning forward, arms relaxed), Rolly (right).
- **Emotion:** Sethji 🙂 (broad, pleased).
- **SpeechBubble (Sethji):** "Rolly ji, bahut achha! Balance sheet strong dikhega. Bank wale khush ho jaayenge."

### STEP 12 — `[BEAT]` Narrator (the stakes)
- **NarratorBox:** "He was applying for a ₹5 crore expansion loan next month. A strong balance sheet mattered."
- **Reveal:** a small **₹5 crore loan** chip slides in beside Sethji, then settles.

---

## SCENE 4 — Pranav arrives
*Set: godown exterior + door. Pranav enters with a folder of invoices.*

### STEP 13 — `[CARD]` Scene transition
- `Scene 4 · The Auditor Arrives`

### STEP 14 — `[BEAT]` Narrator
- **Cast:** Pranav (entering from right, **walk** across to center, folder in hand).
- **NarratorBox:** "Pranav arrived two days later for the statutory audit."

### STEP 15 — `[BEAT]` Narrator + invoice strip
- **NarratorBox:** "He opened Rolly's working. Coconut soap: ₹85 per unit. He went to the purchase invoices."
- **FlowFx:** a **mini invoice strip** slides up: `₹58 · ₹60 · ₹62 per box`.
- **Emotion:** Pranav 🤔 (quiet, thoughtful); a small pencil-note tick appears.

---

## SCENE 5 — The hair oil discovery
*Set: hair-oil shelf, rows of bottles. One batch tagged in red: "Expiry: May".*

### STEP 16 — `[CARD]` Scene transition
- `Scene 5 · The Hair-Oil Discovery`

### STEP 17 — `[BEAT]` Narrator
- **Cast:** Pranav at the shelf (left). One bottle highlighted with a red **"Expiry: May"** tag.
- **NarratorBox:** "October batch — 200 bottles. Expiry date: May. Only two months to expiry."

### STEP 18 — `[BEAT]` NRV calculation (builds step by step)
- **CalcPanel (center):**
  ```
  Current market selling price       =   ₹120
  Less: 10% distributor commission   = − ₹12
  ─────────────────────────────────────────
  Net Realisable Value (NRV)         =   ₹108
  Cost of purchase                   =   ₹140
  ```
- **Emotion:** Pranav 🤔 (calm, noting a problem); pencil-note tick.
- **Reveal:** rows reveal one by one; NRV line lands, then Cost line drops in **above** it for contrast (₹140 > ₹108).

---

## SCENE 6 — The meeting begins
*Set: back office. Pranav, Rolly, Sethji at the table. Whiteboard behind.*

### STEP 19 — `[CARD]` Scene transition
- `Scene 6 · The Meeting`

### STEP 20 — `[BEAT]` Pranav asks
- **Cast:** Pranav (left), Rolly (center), Sethji (right) — all seated.
- **SpeechBubble (Pranav):** "Rolly ji, yeh coconut soap ki valuation — ₹85 per unit. Purchase invoice ₹60 dikhata hai. Yeh ₹85 kahan se aaya?"
- **FlowFx:** side-by-side contrast appears — **Rolly's sheet ₹85** vs **Invoice ₹60**.

### STEP 21 — `[BEAT]` Rolly defends
- **SpeechBubble (Rolly):** "Market price! That's what they're worth right now. If we sold them today, we'd get ₹85."

### STEP 22 — `[BEAT]` Sethji backs Rolly
- **Emotion:** Sethji 🙂 (genuine question, not hostile).
- **SpeechBubble (Sethji):** "Toh phir kya problem hai, Pranav bhai? Agar bazar mein ₹85 mil raha hai, toh inventory ₹85 hi honi chahiye?"

---

## SCENE 7 — Pranav explains the core concept
*Set: table + whiteboard becomes active behind Pranav.*

### STEP 23 — `[CARD]` Scene transition
- `Scene 7 · Why Not Market Price?`

### STEP 24 — `[BEAT]` Pranav — think ahead
- **Emotion:** Pranav 👉 (explaining).
- **SpeechBubble (Pranav):** "Sethji, sochiye aage. Agar ₹85 pe value ki — toh hum keh rahe hain ki ₹25 per box ka profit pehle hi kama liya…"

### STEP 25 — `[BEAT]` Pranav — the punch + red cross
- **SpeechBubble (Pranav):** "…jabki soap abhi godown mein hai. Bika nahi hai. Ek rupaya bhi nahi aaya. Toh profit kahan hua?"
- **FlowFx:** a **₹25 profit** bubble appears, then a **RED ✗** strikes through it.
- **Label (red):** **"Unrealised Profit — Cannot Book Yet"**

### STEP 26 — `[BEAT]` The LCNRV rule (Highlight box)
- **HighlightBox (orange, center):**
  ```
  AS 2 Rule: Value inventory at
  LOWER OF COST AND NET REALISABLE VALUE (LCNRV)
  Dono mein se jo kam ho.
  ```

### STEP 27 — `[BEAT]` Worked on whiteboard + Rolly's aha
- **CalcPanel (on whiteboard):**
  ```
  Coconut Soap:
    Cost  = ₹60   ← LOWER ✓   (green)
    NRV   = ₹85
    Value = ₹60   (not ₹85)
  ```
- **Emotion:** Rolly 💡 (realisation / aha).

---

## SCENE 8 — The hair oil: loss booked NOW
*Set: same office. Pranav pulls out his hair-oil note.*

### STEP 28 — `[CARD]` Scene transition
- `Scene 8 · Provide for the Loss — Now`

### STEP 29 — `[BEAT]` Pranav — the falling-value item
- **Emotion:** Pranav 👉.
- **SpeechBubble (Pranav):** "October wali hair oil batch — cost ₹140. Ab sirf ₹108 mein bik sakti hai. NRV ₹108 hai."

### STEP 30 — `[BEAT]` Loss calculation + flow to P&L
- **CalcPanel:**
  ```
  Hair Oil (October batch):
    Cost  = ₹140
    NRV   = ₹108   ← LOWER ✓   (green)
    Value = ₹108
    Loss  = ₹32 per bottle      (RED)
    → Book ₹32 loss to P&L NOW.
  ```
- **FlowFx:** the red **₹32** visually **flows** from the Inventory box into a **P&L** box.

### STEP 31 — `[BEAT]` Sethji gets it
- **Emotion:** Sethji 🙂→ understanding nod.
- **SpeechBubble (Sethji):** "Loss hone wala hai, toh abhi book karo. Profit hone wala hai, toh ruko jab tak ho na jaye."

### STEP 32 — `[BEAT]` Conservatism (big navy concept box)
- **ConceptBox (navy, center, BIG):**
  ```
  CONSERVATISM PRINCIPLE
  "Anticipate no profits.
   Provide for all losses."

  AS 2 isi principle pe khada hai.
  ```
- **SpeechBubble (Pranav, small, below):** "Exactly, Sethji. Bilkul sahi."

---

## SCENE 9 — Cooking oil: FIFO vs Weighted Average
*Set: Rolly opens her laptop again. A three-batch table appears.*
**⚠ MATH CORRECTED HERE — see note.**

### STEP 33 — `[CARD]` Scene transition
- `Scene 9 · Cooking Oil — FIFO vs Weighted Average`

### STEP 34 — `[BEAT]` Rolly raises it
- **Cast:** Rolly (right, laptop), Pranav (left).
- **SpeechBubble (Rolly):** "Pranav bhai, ek aur baat. Cooking oil — teen batches, teen alag rates."

### STEP 35 — `[BEAT]` Batch table builds
- **NumberTable:**
  ```
  BATCH            | QTY    | PURCHASE RATE
  Batch 1 (July)   | 100 L  | ₹90/litre
  Batch 2 (Nov)    | 150 L  | ₹95/litre
  Batch 3 (Feb)    | 200 L  | ₹100/litre
  Sold during year : 330 litres
  ──────────────────────────────────
  Closing stock    : 120 litres — value = ?
  ```

### STEP 36 — `[BEAT]` FIFO panel (green)
- **CalcPanel (green tint):**
  ```
  FIFO (First In, First Out):
  Oldest sold first →
    July 100L sold, Nov 150L sold, Feb 80L sold = 330L
    Remaining: 120L from February batch
    Value = 120 × ₹100 = ₹12,000
  ```

### STEP 37 — `[BEAT]` Weighted Average panel (purple) — **CORRECTED**
- **CalcPanel (purple tint):**
  ```
  Weighted Average:
    Total cost = (100×90)+(150×95)+(200×100)
               = 9,000 + 14,250 + 20,000
               = ₹43,250
    Total qty  = 450 L
    Avg rate   = ₹96.11/litre
    Value = 120 × ₹96.11 = ₹11,533
  ```
- **❗ Correction note (do not ship the old numbers):**
  - OLD (wrong): total ₹42,250 · avg ₹93.89 · value ₹11,267
  - NEW (correct): **total ₹43,250 · avg ₹96.11 · value ₹11,533**

---

## SCENE 10 — The consistency rule
*Set: both answers side by side.*

### STEP 38 — `[CARD]` Scene transition
- `Scene 10 · Pick One. Stick to It.`

### STEP 39 — `[BEAT]` Side-by-side + Rolly
- **FlowFx:** two cards side by side — **FIFO ₹12,000** (green) vs **Weighted Avg ₹11,533** (purple). *(corrected)*
- **SpeechBubble (Rolly):** "Both give different values!"

### STEP 40 — `[BEAT]` Pranav — both allowed
- **SpeechBubble (Pranav):** "Haan. Aur AS 2 dono allow karta hai. Koi ek choose karo —"

### STEP 41 — `[BEAT]` Consistency (orange box)
- **HighlightBox (orange):**
  ```
  CONSISTENCY RULE
  Pick ONE method. Follow it every year.
  Saal-saal switch nahi kar sakte.
  ```

---

## SCENE 11 — Sethji's acceptance
*Set: Sethji looking at the revised (lower) inventory total. Calm, nodding.*

### STEP 42 — `[CARD]` Scene transition
- `Scene 11 · The Real Picture`

### STEP 43 — `[BEAT]` Sethji accepts
- **Emotion:** Sethji 🙂 (calm, nodding).
- **SpeechBubble (Sethji):** "Theek hai, Pranav bhai. Jo sach hai, wahi dikhana chahiye. Bank ko bhi toh asli tasveer chahiye."

### STEP 44 — `[BEAT]` Warm laugh
- **Emotion:** Sethji 😄 (warm laugh).
- **SpeechBubble (Sethji):** "Waise — ab godown thoda kam bhaari lag raha hai!"
- **Stage:** all three (Rolly 🙂, Pranav 🙂, Sethji 😄) shown together — light, warm closing moment.

---

## SCENE 12 — Closing recap
*Set: clean navy background. Three concept boxes fade in one by one.*

### STEP 45 — `[CARD]` Scene transition
- `Scene 12 · The Three Takeaways`

### STEP 46 — `[BEAT]` Three recap boxes (fade in one per sub-reveal)
- **Box 1 (navy):**
  ```
  1. LCNRV Rule
     Lower of Cost and NRV
  ```
- **Box 2 (navy):**
  ```
  2. Conservatism
     Anticipate no profits.
     Provide for all losses.
  ```
- **Box 3 (navy):**
  ```
  3. Cost Formulas
     FIFO  or  Weighted Average
     — consistently applied
  ```

### STEP 47 — `[CARD]` Closing card / footer
- **ClosingCard (navy):**
  ```
  AS 2 — Valuation of Inventories
  CA Inter · Advanced Accounting

  VC Gurukul, Noida · CA Pranav Pratik Tulshyan
  #pranavBhaiya   #NewtonofAccounts
  ```
- **Hint:** `↻ Restart` · (optional) `Next chapter →`

---

# 6. Master step index

| # | Type | Scene | What happens |
|---|---|---|---|
| 1 | CARD | — | Opening title |
| 2 | CARD | 1 | Scene 1 transition |
| 3 | BEAT | 1 | Narrator: FY closing |
| 4 | BEAT | 1 | Narrator: two days counting (Rolly walks) |
| 5 | BEAT | 1 | Narrator: product list, Rolly 🙂 |
| 6 | CARD | 2 | Scene 2 transition |
| 7 | BEAT | 2 | Rolly thought: "market price, simple" |
| 8 | BEAT | 2 | Spreadsheet builds |
| 9 | BEAT | 2 | ₹1.24 Cr green glow + narrator |
| 10 | CARD | 3 | Scene 3 transition |
| 11 | BEAT | 3 | Sethji 🙂: balance sheet strong |
| 12 | BEAT | 3 | Narrator: ₹5 Cr loan stakes |
| 13 | CARD | 4 | Scene 4 transition |
| 14 | BEAT | 4 | Narrator: Pranav arrives (walk) |
| 15 | BEAT | 4 | Narrator + invoice strip ₹58·60·62, Pranav 🤔 |
| 16 | CARD | 5 | Scene 5 transition |
| 17 | BEAT | 5 | Narrator: Oct batch, expiry May |
| 18 | BEAT | 5 | NRV calc builds, Pranav 🤔 |
| 19 | CARD | 6 | Scene 6 transition |
| 20 | BEAT | 6 | Pranav asks: ₹85 kahan se? + contrast |
| 21 | BEAT | 6 | Rolly defends: market price |
| 22 | BEAT | 6 | Sethji 🙂 backs Rolly |
| 23 | CARD | 7 | Scene 7 transition |
| 24 | BEAT | 7 | Pranav 👉: ₹25 profit pehle hi? |
| 25 | BEAT | 7 | Pranav: bika nahi + ₹25 RED ✗ |
| 26 | BEAT | 7 | LCNRV highlight box |
| 27 | BEAT | 7 | Whiteboard calc ₹60 ✓, Rolly 💡 |
| 28 | CARD | 8 | Scene 8 transition |
| 29 | BEAT | 8 | Pranav 👉: hair oil NRV ₹108 |
| 30 | BEAT | 8 | Loss calc ₹32 flows to P&L |
| 31 | BEAT | 8 | Sethji: loss abhi, profit ruko |
| 32 | BEAT | 8 | Conservatism navy box + Pranav |
| 33 | CARD | 9 | Scene 9 transition |
| 34 | BEAT | 9 | Rolly: teen batches |
| 35 | BEAT | 9 | Batch table builds |
| 36 | BEAT | 9 | FIFO panel ₹12,000 |
| 37 | BEAT | 9 | **WA panel ₹43,250 / ₹96.11 / ₹11,533 (corrected)** |
| 38 | CARD | 10 | Scene 10 transition |
| 39 | BEAT | 10 | Side-by-side ₹12,000 vs ₹11,533 |
| 40 | BEAT | 10 | Pranav: dono allowed |
| 41 | BEAT | 10 | Consistency orange box |
| 42 | CARD | 11 | Scene 11 transition |
| 43 | BEAT | 11 | Sethji: asli tasveer |
| 44 | BEAT | 11 | Sethji 😄: godown kam bhaari |
| 45 | CARD | 12 | Scene 12 transition |
| 46 | BEAT | 12 | Three recap boxes |
| 47 | CARD | 12 | Closing card + footer |

---

# 7. Asset list (kept tiny; mostly code-drawn)
- Characters, bubbles, boxes, tables, backgrounds: **all CSS/SVG in code** — no raster needed.
- `/assets/` reserved for: favicon, optional VC Gurukul logo, optional texture for godown bg.

---

# 8. Open decisions for you
1. **Scene cards on every scene (12 cards) — keep, or only on major shifts** (e.g. Scenes 4, 9, 12)? More cards = clearer chapters but more clicks. *(Default in this spec: one per scene.)*
2. **Mobile:** rotate-prompt only, or also CSS-rotate the stage so it plays in forced landscape? *(Default: rotate-prompt + auto-rotate stage.)*
3. **Diya:** the script never gives her a line — keep her as an optional explainer (off by default), or write her into the recap (Scene 12) as the narrator? *(Default: off; recap is box-only.)*
4. **Restart vs Next chapter** on the closing card — Next implies the hub exists; for a standalone AS-02 site I'll show **Restart** only unless you want a link out.

---

*End of storyboard. On your sign-off I'll build the shared component library + Scenes 1–3 as a style proof, then complete 4–12.*
