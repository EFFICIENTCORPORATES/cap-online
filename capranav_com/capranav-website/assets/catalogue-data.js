/*
  CATALOGUE — single source of truth for everything sold/shown on capranav.com.
  Edit here only; index.html, courses.html and books.html all read from this
  one file so a price or fact never needs updating in two places.

  Chapter list and unique_chapter_id values are taken directly from the
  canonical syllabus index: books/concept-book/syllabus-engine/data/
  1-ca-inter-adv-accounts-topic-page-index.json (locked, 36 chapters).

  price: null  ->  shown as "Coming soon", no Buy button.
*/
window.CATALOGUE = {

  fullCourse: {
    id: "full-course-adv-accounts",
    title: "CA Inter Gr.1 Advanced Accounting",
    subtitle: "CA Pranav Pratik Tulshyan",
    mode: "Live + Recorded",
    plan: "Plus",
    planFeatures: [
      "Live Classes",
      "Recorded Lectures with Unlimited Views",
      "Regular Doubt Session",
      "E-Book Access in App",
      "100% Detailed Syllabus Coverage",
      "Unlimited MCQs Practice",
      "Hard Copy Books",
    ],
    // Two batches, each its own price — shown as an Attempt picker.
    batches: [
      { id: "jan27", label: "Jan'27", price: 4999 },
      { id: "may27", label: "May'27", price: 5999 },
    ],
    description: "Every chapter of CA Inter Advanced Accounting, taught end to end — live classes with unlimited-view recordings, regular doubt sessions and full syllabus coverage.",
  },

  // Chapter-by-chapter selling is on hold — not currently permitted.
  // Data kept intact for when it reopens; no chapter Buy UI is rendered
  // anywhere on the site while chaptersSellingEnabled is false.
  chaptersSellingEnabled: false,
  chapters: [
    { seq: "1",   id: "M1-C1-U0",  as: null,    title: "Introduction to Accounting Standards", price: null },
    { seq: "2",   id: "M1-C3-U0",  as: null,    title: "Applicability of Accounting Standards", price: null },
    { seq: "3",   id: "M1-C2-U0",  as: null,    title: "Framework for Preparation & Presentation of Financial Statements", price: null },
    { seq: "4",   id: "M2-C5-U1",  as: "AS 2",  title: "Valuation of Inventory", price: 299 },
    { seq: "5",   id: "M2-C5-U2",  as: "AS 10", title: "Property, Plant and Equipment", price: 399 },
    { seq: "6",   id: "M2-C5-U6",  as: "AS 26", title: "Intangible Assets", price: 399 },
    { seq: "7",   id: "M2-C5-U4",  as: "AS 16", title: "Borrowing Costs", price: 399 },
    { seq: "8",   id: "M2-C5-U5",  as: "AS 19", title: "Leases", price: 399 },
    { seq: "9",   id: "M2-C5-U7",  as: "AS 28", title: "Impairment of Assets", price: 399 },
    { seq: "10",  id: "M2-C5-U3",  as: "AS 13", title: "Accounting for Investments", price: 399 },
    { seq: "11",  id: "M2-C6-U2",  as: "AS 29", title: "Provisions, Contingent Liabilities and Contingent Assets", price: null },
    { seq: "12",  id: "M2-C6-U1",  as: "AS 15", title: "Employee Benefits", price: null },
    { seq: "13",  id: "M2-C7-U1",  as: "AS 4",  title: "Contingencies and Events Occurring After the Balance Sheet Date", price: 199 },
    { seq: "14",  id: "M2-C7-U2",  as: "AS 5",  title: "Net Profit or Loss for the Period, Prior Period Items and Changes in Accounting Policies", price: 199 },
    { seq: "15",  id: "M2-C7-U3",  as: "AS 11", title: "The Effects of Changes in Foreign Exchange Rates", price: null },
    { seq: "16",  id: "M2-C8-U2",  as: "AS 9",  title: "Revenue Recognition", price: null },
    { seq: "17",  id: "M2-C8-U1",  as: "AS 7",  title: "Construction Contracts", price: null },
    { seq: "18",  id: "M2-C9-U1",  as: "AS 12", title: "Accounting for Government Grants", price: null },
    { seq: "19",  id: "M2-C7-U4",  as: "AS 22", title: "Accounting for Taxes on Income", price: null },
    { seq: "20",  id: "M1-C4-U5",  as: "AS 20", title: "Earnings Per Share", price: null },
    { seq: "21",  id: "M1-C4-U1",  as: "AS 1",  title: "Disclosure of Accounting Policies", price: null },
    { seq: "22",  id: "M3-C11-U1", as: null,    title: "Preparation of Financial Statements of Companies", price: null },
    { seq: "23A", id: "M3-C11-U2", as: null,    title: "Cash Flow Statement", price: null },
    { seq: "23B", id: "M1-C4-U2",  as: "AS 3",  title: "Cash Flow Statement", price: null },
    { seq: "24",  id: "M1-C4-U3",  as: "AS 17", title: "Segment Reporting", price: null },
    { seq: "25",  id: "M1-C4-U4",  as: "AS 18", title: "Related Party Disclosures", price: null },
    { seq: "26",  id: "M1-C4-U6",  as: "AS 24", title: "Discontinuing Operations", price: null },
    { seq: "27",  id: "M2-C10-U1", as: "AS 21", title: "Consolidated Financial Statements", price: null },
    { seq: "28",  id: "M2-C10-U2", as: "AS 23", title: "Accounting for Investments in Associates in Consolidated Financial Statements", price: null },
    { seq: "29",  id: "M2-C10-U3", as: "AS 27", title: "Financial Reporting of Interests in Joint Ventures", price: null },
    { seq: "30A", id: "M3-C13-U0", as: null,    title: "Amalgamation of Companies", price: null },
    { seq: "30B", id: "M2-C9-U2",  as: "AS 14", title: "Accounting for Amalgamations", price: null },
    { seq: "31",  id: "M1-C4-U7",  as: "AS 25", title: "Interim Financial Reporting", price: null },
    { seq: "32",  id: "M3-C12-U0", as: null,    title: "Buyback of Securities", price: null },
    { seq: "33",  id: "M3-C14-U0", as: null,    title: "Internal Reconstruction", price: null },
    { seq: "34",  id: "M3-C15-U0", as: null,    title: "Accounting for Branches Including Foreign Branches", price: null },
  ],

  books: {
    flatShippingRupees: 0, // shipping is built into the sale price (all-inclusive)
    prepaidOnly: true,     // no Cash on Delivery
    items: [
      {
        id: "question-bank-book",
        title: "The Question Bank Book",
        subtitle: "Every MTP · RTP · PYQ question, chapter by chapter",
        description: "Every Advanced Accounting question from Mock Test Papers, RTPs and Past Year Papers, organised chapter-wise with official answers, topic tags and real ICAI Examiner's Comments where available.",
        stats: [
          { label: "Questions covered", value: "450+" },
          { label: "Exam sittings covered", value: "34 (2023–2026)" },
          { label: "Chapters", value: "34" },
        ],
        mrp: 990,
        price: 699, // all-inclusive of shipping
      },
      {
        id: "strategy-book",
        title: "The Exam Strategy Book",
        subtitle: "Plan · Learn · Revise · Deliver",
        description: "The complete CA Inter exam-strategy book in print — fixing your attempt, chapter calendar, revision rounds and exam-day delivery system, built around the same approach that took CA Pranav to AIR 1, AIR 1 and AIR 5.",
        stats: [
          { label: "Framework", value: "5×5" },
          { label: "Built around", value: "Plan · Learn · Revise · Deliver" },
        ],
        mrp: 990,
        price: 699, // all-inclusive of shipping
      },
    ],
  },

  // Free MCQ + descriptive practice bot on Telegram — a funnel into the
  // paid course/books, not a paid product itself.
  mcqBot: {
    username: "CAPranavExamBot",
    url: "https://t.me/CAPranavExamBot",
    stats: [
      { label: "MCQs", value: "300+" },
      { label: "Descriptive questions", value: "450+" },
    ],
    features: [
      "Practice by chapter, MCQ or full descriptive questions",
      "Instant answers with explanations after every attempt",
      "Real ICAI Examiner's Comments shown where available",
      "A personal report on request — accuracy, chapters practised, time spent",
      "Always free",
    ],
  },
};
