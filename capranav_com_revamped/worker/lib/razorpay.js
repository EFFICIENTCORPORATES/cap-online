/*
  Server-side Razorpay integration: create an order (amount always looked up
  from products.js, never trusted from the client), and verify the payment
  signature Razorpay's Checkout hands back after a successful payment.
*/

export async function createRazorpayOrder(env, { amountRupees, receipt, notes }) {
  const auth = btoa(`${env.RAZORPAY_KEY_ID}:${env.RAZORPAY_KEY_SECRET}`);
  const res = await fetch("https://api.razorpay.com/v1/orders", {
    method: "POST",
    headers: {
      Authorization: `Basic ${auth}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      amount: Math.round(amountRupees * 100), // paise
      currency: "INR",
      receipt,
      notes,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error("Razorpay order creation failed: " + JSON.stringify(data));
  }
  return data; // { id, amount, currency, ... }
}

async function hmacHex(secret, message) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(message));
  return Array.from(new Uint8Array(sig), (b) => b.toString(16).padStart(2, "0")).join("");
}

/** Returns true only if the signature genuinely matches — never trust the client's own "success" claim without this. */
export async function verifyRazorpaySignature(env, { orderId, paymentId, signature }) {
  if (!orderId || !paymentId || !signature) return false;
  const expected = await hmacHex(env.RAZORPAY_KEY_SECRET, `${orderId}|${paymentId}`);
  return expected === signature;
}

/*
  Webhook signatures are a different construction from the checkout signature
  above: HMAC-SHA256 of the *raw* request body (not orderId|paymentId), keyed
  with the separate webhook secret configured in the Razorpay Dashboard —
  confirmed against Razorpay's own webhook docs, not assumed. `rawBody` must
  be the exact bytes/text as received, before any JSON.parse/stringify
  round-trip, since re-serializing can change whitespace/key order and break
  the signature.
*/
export async function verifyWebhookSignature(env, rawBody, signature) {
  if (!rawBody || !signature) return false;
  const expected = await hmacHex(env.RAZORPAY_WEBHOOK_SECRET, rawBody);
  return expected === signature;
}
