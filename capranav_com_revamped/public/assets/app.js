/* Homepage logic: course attempt picker, guest checkout (course + physical books), contact form. */

const COURSE_BATCHES = [
  { id: "course-jan27", label: "Jan'27", price: 4999 },
  { id: "course-may27", label: "May'27", price: 5999 },
];
let selectedCourseBatch = COURSE_BATCHES[0];

function renderCoursePicker() {
  const el = document.getElementById("attempt-picker");
  el.innerHTML = COURSE_BATCHES.map(
    (b) => `<button type="button" class="pill${b.id === selectedCourseBatch.id ? " selected" : ""}" data-batch="${b.id}">${b.label}</button>`
  ).join("");
  document.getElementById("course-price").textContent = "₹" + selectedCourseBatch.price.toLocaleString("en-IN");
}
document.getElementById("attempt-picker").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-batch]");
  if (!btn) return;
  selectedCourseBatch = COURSE_BATCHES.find((b) => b.id === btn.dataset.batch);
  renderCoursePicker();
});
renderCoursePicker();

function openGuestForm({ title, priceLabel, needsShipping, onSubmit }) {
  window.openModal(`
    <h3>${title}</h3>
    <p class="note">${priceLabel}</p>
    <form class="modal-form" id="guest-form">
      <label>Full name<input name="name" required></label>
      <label>Email<input type="email" name="email" required></label>
      <label>Phone / WhatsApp<input type="tel" name="phone" required></label>
      ${
        needsShipping
          ? `<label>Delivery address<input name="address1" required></label>
             <label>Address line 2 (optional)<input name="address2"></label>
             <label>City<input name="city" required></label>
             <label>State<input name="state" required></label>
             <label>Pincode<input name="pincode" required></label>`
          : ""
      }
      <button type="submit" class="button button-primary">Proceed to pay</button>
    </form>
  `);
  document.getElementById("guest-form").addEventListener("submit", (e) => {
    e.preventDefault();
    onSubmit(Object.fromEntries(new FormData(e.target).entries()));
  });
}

function showResultModal(message) {
  window.openModal(`<h3>Thank you</h3><p class="note">${message}</p>`);
}

// TEMPORARY (Pranav, 2026-09-06): course enrolment redirects to VC
// Gurukul's own product page instead of this site's Razorpay checkout.
// Books are UNCHANGED — still buy directly on this site (see the
// data-buy-physical/data-buy-pdf handlers below, and dashboard.js for
// PDF purchases). Explicitly framed as temporary, not a removal — the
// original in-site course-checkout flow is kept right below, commented
// out rather than deleted, so restoring it later is: delete the redirect
// line, uncomment the block.
const COURSE_EXTERNAL_CHECKOUT_URL =
  "https://www.vcgurukul.com/product/ca-intermediated-gr1-advanced-accounting-ca-pranav-pratik-tulshyan-jan27-may27?variant=Q1344Q0CJUI2W4J82W7FAGXVUVD9L3F8&src=product_list&variantId=Q1344Q0CJUI2W4J82W7FAGXVUVD9L3F8";

document.getElementById("enrol-button").addEventListener("click", () => {
  window.location.href = COURSE_EXTERNAL_CHECKOUT_URL;
});

/* Original in-site Razorpay course checkout — restore by deleting the
   redirect handler above and uncommenting this block.
document.getElementById("enrol-button").addEventListener("click", () => {
  openGuestForm({
    title: "CA Inter Gr.1 Advanced Accounting — " + selectedCourseBatch.label,
    priceLabel: "₹" + selectedCourseBatch.price.toLocaleString("en-IN"),
    needsShipping: false,
    onSubmit: (data) => {
      window.closeModal();
      window.buyProduct(selectedCourseBatch.id, {
        buyer: { name: data.name, email: data.email, phone: data.phone },
        onSuccess: () => showResultModal("You're enrolled. We'll reach out on the email/phone you shared within 24 hours with your batch details."),
        onError: (err) => alert(err.message),
      });
    },
  });
});
*/

document.querySelectorAll("[data-buy-physical]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const productId = btn.dataset.buyPhysical;
    const title = btn.dataset.title;
    const amount = btn.dataset.amount;
    openGuestForm({
      title,
      priceLabel: "₹" + amount + " (shipping included)",
      needsShipping: true,
      onSubmit: (data) => {
        window.closeModal();
        window.buyProduct(productId, {
          buyer: { name: data.name, email: data.email, phone: data.phone },
          shipping: {
            address1: data.address1,
            address2: data.address2,
            city: data.city,
            state: data.state,
            pincode: data.pincode,
          },
          onSuccess: () => showResultModal("Order placed. Your book ships within a few working days — you'll get a tracking update on the phone number and email you shared."),
          onError: (err) => alert(err.message),
        });
      },
    });
  });
});

// TEMPORARY (Pranav, 2026-09-23): the Question Bank e-book is bought on VC
// Gurukul's own store, not through this site's Razorpay checkout — the same
// arrangement made for course enrolment on 2026-09-06 above. Only this one
// product is redirected; the Strategy Book PDF still buys in-site, and the
// in-site path below is kept intact rather than deleted, so restoring it is:
// remove this product's entry from PDF_EXTERNAL_CHECKOUT_URLS (and from
// products.js).
const PDF_EXTERNAL_CHECKOUT_URLS = {
  "book-qb-pdf":
    "https://www.vcgurukul.com/product/advanced-accounting-question-bank-e-book-ca-pranav-p-tulshyan",
};

// PDF-access buttons otherwise go through the dashboard (login required).
document.querySelectorAll("[data-buy-pdf]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const productId = btn.dataset.buyPdf;
    const external = PDF_EXTERNAL_CHECKOUT_URLS[productId];
    if (external) {
      window.location.href = external;
      return;
    }
    window.location.href = "/dashboard?buy=" + encodeURIComponent(productId);
  });
});

// Contact form
document.getElementById("contact-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const data = Object.fromEntries(new FormData(form).entries());
  const btn = form.querySelector("button[type=submit]");
  btn.disabled = true;
  btn.textContent = "Sending…";
  try {
    const res = await fetch("/api/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Could not send your message.");
    form.reset();
    document.getElementById("contact-status").textContent = "Thanks — your message has been sent.";
  } catch (err) {
    document.getElementById("contact-status").textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Send message";
  }
});
