/*
  Table of Contents data for the in-browser reader — one entry per product,
  chapter number/title/page pulled directly from each book's own printed
  Table of Contents (verified against the real PDF text, never invented).

  book-sb-pdf (The Exam Strategy Book) has no entry here on purpose: it's a
  visual slide-deck, not a chapter-structured book — its pages carry almost
  no extractable chapter-title text (checked directly against the real PDF:
  every page's largest text is just a page number or a hashtag, until a
  narrative section starting around page 95). Inventing chapter names for it
  would mean showing students a table of contents this session made up
  rather than one the book actually states — so it's left out rather than
  faked. If Pranav wants one, it needs either his own section breakdown or
  a manual page-by-page review he can sign off on.
*/
export const BOOK_TOC = {
  "book-qb-pdf": [
    { n: 1, title: "Intro to AS", page: 19 },
    { n: 2, title: "Applicability of AS", page: 26 },
    { n: 3, title: "Framework for Preparation and Presentation of Financial Statements", page: 30 },
    { n: 4, title: "AS 2: Valuation of Inventories", page: 44 },
    { n: 5, title: "AS 10: Property, Plant and Equipment", page: 65 },
    { n: 6, title: "AS 26: Intangible Assets", page: 83 },
    { n: 7, title: "AS 16: Borrowing Costs", page: 94 },
    { n: 8, title: "AS 19: Leases", page: 123 },
    { n: 9, title: "AS 28: Impairment of Assets", page: 139 },
    { n: 10, title: "AS 13: Accounting for Investments", page: 148 },
    { n: 11, title: "AS 29: Provisions, Contingent Liabilities and Contingent Assets", page: 187 },
    { n: 12, title: "AS 15: Employee Benefits", page: 198 },
    { n: 13, title: "AS 4: Contingencies and Events Occurring After the Balance Sheet Date", page: 207 },
    { n: 14, title: "AS 5: Net Profit or Loss, Prior Period Items and Changes in Accounting Policies", page: 221 },
    { n: 15, title: "AS 11: The Effects of Changes in Foreign Exchange Rates", page: 232 },
    { n: 16, title: "AS 9: Revenue Recognition", page: 249 },
    { n: 17, title: "AS 7: Construction Contracts", page: 265 },
    { n: 18, title: "AS 12: Accounting for Government Grants", page: 277 },
    { n: 19, title: "AS 22: Accounting for Taxes on Income", page: 293 },
    { n: 20, title: "AS 20: Earnings Per Share", page: 299 },
    { n: 21, title: "AS 1: Disclosure of Accounting Policies", page: 312 },
    { n: 22, title: "Financial Statements of Companies (Schedule III)", page: 324 },
    { n: 23, title: "Cash Flow Statement (AS 3)", page: 393 },
    { n: 24, title: "AS 17: Segment Reporting", page: 441 },
    { n: 25, title: "AS 18: Related Party Disclosures", page: 448 },
    { n: 26, title: "AS 24: Discontinuing Operations", page: 456 },
    { n: 27, title: "AS 21: Consolidated Financial Statements", page: 466 },
    { n: 28, title: "AS 23: Accounting for Investments in Associates in CFS", page: 513 },
    { n: 29, title: "AS 27: Financial Reporting of Interests in Joint Ventures", page: 520 },
    { n: 30, title: "AS 14: Amalgamation of Companies", page: 523 },
    { n: 31, title: "AS 25: Interim Financial Reporting", page: 582 },
    { n: 32, title: "Buy-back of Securities", page: 586 },
    { n: 33, title: "Internal Reconstruction", page: 599 },
    { n: 34, title: "Accounting for Branches Including Foreign Branches", page: 639 },
  ],
};
