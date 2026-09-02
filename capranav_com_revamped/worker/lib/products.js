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
    amountRupees: 199,
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
