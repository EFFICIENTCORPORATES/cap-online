/*
  Store checkout — shared Razorpay flow for the Course, Chapters and Books.

  There is no backend yet (by design — see VAULT-BLUEPRINT.html for the phased
  plan). This opens Razorpay's own Checkout widget client-side using the public
  Key ID from store-config.js, after collecting the buyer's details in a short
  form. Every field the buyer enters — including a book's shipping address —
  rides along as Razorpay "notes", so it shows up against the payment in the
  Razorpay Dashboard for manual fulfilment. Razorpay's Key ID is safe to expose
  in browser code; the Key Secret is not and is never used here.
*/
(function () {
  const RAZORPAY_SCRIPT = "https://checkout.razorpay.com/v1/checkout.js";
  let scriptLoading = null;

  function loadRazorpay() {
    if (window.Razorpay) return Promise.resolve();
    if (scriptLoading) return scriptLoading;
    scriptLoading = new Promise((resolve, reject) => {
      const tag = document.createElement("script");
      tag.src = RAZORPAY_SCRIPT;
      tag.onload = resolve;
      tag.onerror = () => reject(new Error("Could not reach Razorpay. Check your connection and try again."));
      document.head.appendChild(tag);
    });
    return scriptLoading;
  }

  function keyReady() {
    return typeof window.RAZORPAY_KEY_ID === "string" &&
      window.RAZORPAY_KEY_ID.trim() !== "" &&
      !window.RAZORPAY_KEY_ID.includes("NOT_SET");
  }

  function rupees(n) {
    return "₹" + Number(n).toLocaleString("en-IN");
  }

  // ---- a single reusable modal -----------------------------------------
  let modalRoot = null;
  function ensureModal() {
    if (modalRoot) return modalRoot;
    modalRoot = document.createElement("div");
    modalRoot.className = "store-modal";
    modalRoot.innerHTML =
      '<div class="store-modal-card" role="dialog" aria-modal="true">' +
        '<button type="button" class="store-modal-close" aria-label="Close">&times;</button>' +
        '<div class="store-modal-body"></div>' +
      "</div>";
    document.body.appendChild(modalRoot);
    modalRoot.addEventListener("click", (event) => {
      if (event.target === modalRoot) closeModal();
    });
    modalRoot.querySelector(".store-modal-close").addEventListener("click", closeModal);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeModal();
    });
    return modalRoot;
  }
  function openModal(html) {
    const root = ensureModal();
    root.querySelector(".store-modal-body").innerHTML = html;
    root.classList.add("is-open");
    document.body.classList.add("store-modal-lock");
  }
  function closeModal() {
    if (!modalRoot) return;
    modalRoot.classList.remove("is-open");
    document.body.classList.remove("store-modal-lock");
  }

  function fieldHtml(field) {
    const required = field.required !== false;
    const req = required ? "required" : "";
    if (field.type === "textarea") {
      return '<label>' + field.label + (required ? "" : " (optional)") +
        '<textarea name="' + field.name + '" ' + req + " rows=\"2\"></textarea></label>";
    }
    return '<label>' + field.label + (required ? "" : " (optional)") +
      '<input type="' + (field.type || "text") + '" name="' + field.name + '" ' + req +
      ' placeholder="' + (field.placeholder || "") + '"></label>';
  }

  const DEFAULT_FIELDS = [
    { name: "name", label: "Full name", required: true },
    { name: "email", label: "Email", type: "email", required: true },
    { name: "phone", label: "WhatsApp / phone number", type: "tel", required: true },
  ];

  const BOOK_FIELDS = DEFAULT_FIELDS.concat([
    { name: "address1", label: "Delivery address", required: true },
    { name: "address2", label: "Address line 2 / landmark", required: false },
    { name: "city", label: "City", required: true },
    { name: "state", label: "State", required: true },
    { name: "pincode", label: "Pincode", required: true },
  ]);

  /**
   * window.Store.buy(product)
   *
   * product = {
   *   type: "course" | "chapter" | "book",
   *   title: string,
   *   amountRupees: number,        // required, > 0 — Buy is disabled otherwise
   *   shippingRupees: number,      // optional, added to the total (books)
   *   fields: [...],               // optional override of the order form
   *   notesExtra: {}               // optional extra fields folded into Razorpay notes
   * }
   */
  function buy(product) {
    if (!product || !product.amountRupees || product.amountRupees <= 0) {
      openModal(
        '<p class="store-modal-eyebrow">Not available yet</p>' +
        "<h3>" + (product && product.title ? product.title : "This item") + "</h3>" +
        "<p>Pricing is still being finalised for this one. Check back soon, or reach out directly:</p>" +
        '<p><a href="https://www.instagram.com/capranavptulshyan/" target="_blank" rel="noopener">Instagram ↗</a> · ' +
        '<a href="https://www.linkedin.com/in/capranavptulshyan/" target="_blank" rel="noopener">LinkedIn ↗</a></p>'
      );
      return;
    }

    if (!keyReady()) {
      openModal(
        '<p class="store-modal-eyebrow">Online payment isn’t switched on yet</p>' +
        "<h3>" + product.title + "</h3>" +
        "<p>The store is being finalised. Please reach out directly and we’ll get you sorted:</p>" +
        '<p><a href="https://www.instagram.com/capranavptulshyan/" target="_blank" rel="noopener">Instagram ↗</a> · ' +
        '<a href="https://www.linkedin.com/in/capranavptulshyan/" target="_blank" rel="noopener">LinkedIn ↗</a></p>'
      );
      return;
    }

    const fields = product.fields || (product.type === "book" ? BOOK_FIELDS : DEFAULT_FIELDS);
    const total = product.amountRupees + (product.shippingRupees || 0);

    openModal(
      '<p class="store-modal-eyebrow">' + (product.type === "book" ? "Delivery details" : "Your details") + "</p>" +
      "<h3>" + product.title + "</h3>" +
      '<p class="store-modal-price">' + rupees(product.amountRupees) +
        (product.shippingRupees ? " + " + rupees(product.shippingRupees) + " shipping" : "") + "</p>" +
      '<form class="store-form">' +
        fields.map(fieldHtml).join("") +
        '<button type="submit" class="button button-primary">Proceed to pay ' + rupees(total) + "</button>" +
      "</form>"
    );

    const form = modalRoot.querySelector(".store-form");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(form).entries());
      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      submitBtn.textContent = "Opening secure checkout…";

      try {
        await loadRazorpay();
      } catch (err) {
        alert(err.message);
        submitBtn.disabled = false;
        submitBtn.textContent = "Proceed to pay " + rupees(total);
        return;
      }

      const notes = Object.assign(
        {
          product_type: product.type,
          product_title: product.title,
        },
        data,
        product.notesExtra || {}
      );

      const rzp = new window.Razorpay({
        key: window.RAZORPAY_KEY_ID,
        amount: Math.round(total * 100), // paise
        currency: "INR",
        name: "CA Pranav",
        description: product.title,
        prefill: { name: data.name || "", email: data.email || "", contact: data.phone || "" },
        notes: notes,
        theme: { color: "#111827" },
        handler: function (response) {
          openModal(
            '<p class="store-modal-eyebrow">Payment received</p>' +
            "<h3>You’re in.</h3>" +
            "<p>Payment ID <strong>" + response.razorpay_payment_id + "</strong> — keep this for your records.</p>" +
            "<p>" + (product.type === "book"
              ? "Your book ships within a few working days. You’ll get a tracking update on the phone number and email you shared."
              : "Access details will reach you on the email / WhatsApp number you shared, usually within 24 hours.") +
            "</p>"
          );
        },
      });

      rzp.on("payment.failed", function (response) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Proceed to pay " + rupees(total);
        alert("Payment failed: " + (response.error && response.error.description ? response.error.description : "please try again."));
      });

      rzp.open();
      submitBtn.textContent = "Proceed to pay " + rupees(total);
      submitBtn.disabled = false;
    });
  }

  window.Store = { buy: buy, closeModal: closeModal };
})();
