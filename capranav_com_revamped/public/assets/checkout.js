/*
  Real server-verified checkout. The browser never decides the price or
  marks a payment "successful" on its own — /api/orders/create looks the
  amount up server-side, and /api/orders/verify checks Razorpay's signature
  before anything is recorded as paid.
*/
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

/**
 * window.buyProduct(productId, { buyer, shipping, onSuccess, onError })
 * buyer = { name, email, phone }; shipping (book_physical only) =
 * { address1, address2, city, state, pincode }.
 */
window.buyProduct = async function buyProduct(productId, { buyer, shipping, onSuccess, onError } = {}) {
  try {
    const res = await fetch("/api/orders/create", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ productId, buyer, shipping }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Could not start checkout.");

    await loadRazorpay();

    const rzp = new window.Razorpay({
      key: data.keyId,
      order_id: data.razorpayOrderId,
      amount: data.amount,
      currency: data.currency,
      name: "CA Pranav",
      description: data.productTitle,
      prefill: { name: buyer.name, email: buyer.email, contact: buyer.phone },
      theme: { color: "#111827" },
      handler: async function (response) {
        try {
          const vres = await fetch("/api/orders/verify", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              razorpayOrderId: response.razorpay_order_id,
              razorpayPaymentId: response.razorpay_payment_id,
              razorpaySignature: response.razorpay_signature,
            }),
          });
          const vdata = await vres.json();
          if (!vres.ok) throw new Error(vdata.error || "Payment verification failed.");
          if (onSuccess) onSuccess(vdata);
        } catch (err) {
          if (onError) onError(err);
          else alert(err.message);
        }
      },
    });
    rzp.on("payment.failed", function (response) {
      const msg = "Payment failed: " + ((response.error && response.error.description) || "please try again.");
      if (onError) onError(new Error(msg));
      else alert(msg);
    });
    rzp.open();
  } catch (err) {
    if (onError) onError(err);
    else alert(err.message);
  }
};
