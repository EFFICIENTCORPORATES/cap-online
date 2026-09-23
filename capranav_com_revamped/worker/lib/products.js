/*
  The ONE place prices live. The server never trusts an amount sent by the
  browser — every order looks the amount up here by product_id.
*/
export const PRODUCTS = {
  "course-jan27": {
    type: "course",
    title: "CA Inter Gr.1 Advanced Accounting — Jan'27 batch",
    amountRupees: 4999,
  },
  "course-may27": {
    type: "course",
    title: "CA Inter Gr.1 Advanced Accounting — May'27 batch",
    amountRupees: 5999,
  },
  "book-qb-physical": {
    type: "book_physical",
    title: "The Question Bank Book — printed copy",
    amountRupees: 599,
    mrpRupees: 999,
  },
  "book-sb-physical": {
    type: "book_physical",
    title: "The Exam Strategy Book — printed copy",
    amountRupees: 299,
    mrpRupees: 499,
  },
  "book-qb-pdf": {
    type: "book_pdf",
    title: "The Question Bank Book — PDF access",
    // TEMPORARY (Pranav, 2026-09-23): the ₹199 Question Bank e-book is now
    // sold on VC Gurukul's own store instead of through this site's Razorpay
    // checkout — same arrangement already in place for course enrolment (see
    // app.js, 2026-09-06). externalCheckoutUrl is what turns the in-site
    // checkout off: handleOrderCreate refuses to open a Razorpay order for
    // any product carrying it, so no new ₹199 order can be created here even
    // by a hand-crafted request.
    //
    // The entry itself is deliberately KEPT (not deleted) because students
    // who already bought PDF access hold a `book-qb-pdf` entitlement and need
    // `fileKey` to keep reading via /api/read. amountRupees is kept, commented
    // out, so restoring in-site checkout is: delete externalCheckoutUrl and
    // uncomment amountRupees.
    // amountRupees: 199,
    externalCheckoutUrl:
      "https://www.vcgurukul.com/product/advanced-accounting-question-bank-e-book-ca-pranav-p-tulshyan",
    fileKey: "question-bank-book.pdf",
  },
  "book-sb-pdf": {
    type: "book_pdf",
    title: "The Exam Strategy Book — PDF access",
    amountRupees: 99,
    fileKey: "strategy-book.pdf",
  },
};

export function getProduct(productId) {
  return PRODUCTS[productId] || null;
}
