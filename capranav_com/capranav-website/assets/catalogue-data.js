/*
  CATALOGUE — single source of truth for everything sold on capranav.com.
  Edit prices/availability here only; courses.html, books.html and index.html
  all read from this one file so a price never needs updating in two places.

  Chapter list and unique_chapter_id values are taken directly from the
  canonical syllabus index: books/concept-book/syllabus-engine/data/
  1-ca-inter-adv-accounts-topic-page-index.json (locked, 36 chapters).

  price: null  ->  shown as "Coming soon", no Buy button.
  Fill in a number (rupees, no commas) to make an item purchasable.
*/
window.CATALOGUE = {

  fullCourse: {
    id: "full-course-adv-accounts",
    title: "CA Inter Gr.1 Advanced Accounting",
    subtitle: "Complete course — live + recorded, full syllabus",
    batches: ["January 2027", "May 2027"],
    price: 6999,
    description: "Every chapter of CA Inter Advanced Accounting taught end to end — the Kahaani (story), Koncept (theory) and Karma (practice) method, built around the same syllabus this website's free resources are organised on.",
  },

  // 36 chapters, in ICAI teaching sequence. `as` is the Accounting Standard
  // number where one applies (null for the four non-AS chapters: Framework,
  // Applicability, Financial Statements of Companies, and the four
  // company-law chapters — Amalgamation, Buyback, Internal Reconstruction,
  // Branch Accounting).
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
        description: "Every Advanced Accounting question from Mock Test Papers, RTPs and Past Year Papers (2023 onward), organised chapter-wise with official answers, topic tags and Examiner's Comments where available.",
        mrp: 990,
        price: 699, // all-inclusive of shipping
      },
      {
        id: "strategy-book",
        title: "The Exam Strategy Book",
        subtitle: "Plan · Learn · Revise · Deliver",
        description: "The complete CA Inter exam-strategy book in print — the same 5×5 framework as the interactive edition, fixing your attempt, chapter calendar, revision rounds and exam-day system.",
        mrp: 990,
        price: 699, // all-inclusive of shipping
      },
    ],
  },
};
