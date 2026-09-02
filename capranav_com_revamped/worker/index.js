import { getProduct } from "./lib/products.js";
import {
  randomOtpCode,
  otpExpiry,
  createSession,
  sessionCookieHeader,
  clearCookieHeader,
  getSessionEmail,
  isValidEmail,
} from "./lib/session.js";
import { sendEmail, otpEmailHtml } from "./lib/email.js";
import { createRazorpayOrder, verifyRazorpaySignature } from "./lib/razorpay.js";

const CONTACT_TO = "capranavpratiktulshyan@gmail.com";

function json(data, init = {}) {
  return new Response(JSON.stringify(data), {
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
  });
}

async function readJson(request) {
  try {
    return await request.json();
  } catch {
    return {};
  }
}

async function handleOtpSend(request, env) {
  const { email } = await readJson(request);
  if (!isValidEmail(email)) return json({ error: "Enter a valid email address." }, { status: 400 });
  const clean = email.trim().toLowerCase();
  const code = randomOtpCode();
  await env.DB
    .prepare("INSERT INTO otp_codes (email, code, expires_at) VALUES (?, ?, ?)")
    .bind(clean, code, otpExpiry())
    .run();
  try {
    await sendEmail(env, {
      to: clean,
      subject: `Your login code: ${code}`,
      html: otpEmailHtml(code),
      fromLocal: "login",
    });
  } catch (err) {
    console.error("otp send failed:", err && err.message);
    return json({ error: "Could not send the code. Try again in a moment." }, { status: 502 });
  }
  return json({ ok: true });
}

async function handleOtpVerify(request, env) {
  const { email, code } = await readJson(request);
  if (!isValidEmail(email) || !code) return json({ error: "Enter the email and the 6-digit code." }, { status: 400 });
  const clean = email.trim().toLowerCase();
  const row = await env.DB
    .prepare(
      "SELECT rowid AS id, expires_at FROM otp_codes WHERE email = ? AND code = ? AND consumed = 0 ORDER BY rowid DESC LIMIT 1"
    )
    .bind(clean, String(code).trim())
    .first();
  if (!row) return json({ error: "That code is wrong or already used." }, { status: 400 });
  if (new Date(row.expires_at).getTime() < Date.now()) {
    return json({ error: "That code has expired. Request a new one." }, { status: 400 });
  }
  await env.DB.prepare("UPDATE otp_codes SET consumed = 1 WHERE rowid = ?").bind(row.id).run();
  const { token, expires } = await createSession(env.DB, clean);
  return json({ ok: true, email: clean }, { headers: { "Set-Cookie": sessionCookieHeader(token, expires) } });
}

async function handleLogout(request, env) {
  return json({ ok: true }, { headers: { "Set-Cookie": clearCookieHeader() } });
}

async function handleMe(request, env) {
  const email = await getSessionEmail(env.DB, request);
  if (!email) return json({ loggedIn: false });
  const rows = await env.DB
    .prepare("SELECT product_id FROM entitlements WHERE user_email = ?")
    .bind(email)
    .all();
  const entitlements = (rows.results || []).map((r) => r.product_id);
  return json({ loggedIn: true, email, entitlements });
}

async function handleOrderCreate(request, env) {
  const body = await readJson(request);
  const product = getProduct(body.productId);
  if (!product) return json({ error: "Unknown product." }, { status: 400 });

  const buyer = body.buyer || {};
  let buyerEmail = (buyer.email || "").trim().toLowerCase();

  if (product.type === "book_pdf") {
    // PDF access is tied to a logged-in account, always — the buyer never
    // gets to pick a different email for this one.
    const sessionEmail = await getSessionEmail(env.DB, request);
    if (!sessionEmail) return json({ error: "Please log in first to buy PDF access." }, { status: 401 });
    buyerEmail = sessionEmail;
  } else {
    if (!isValidEmail(buyerEmail)) return json({ error: "Enter a valid email address." }, { status: 400 });
  }
  if (!buyer.name || !buyer.phone) return json({ error: "Name and phone are required." }, { status: 400 });

  if (product.type === "book_physical") {
    const s = body.shipping || {};
    if (!s.address1 || !s.city || !s.state || !s.pincode) {
      return json({ error: "Full delivery address is required." }, { status: 400 });
    }
  }

  const orderId = crypto.randomUUID();
  const receipt = orderId.slice(0, 40);
  let rzpOrder;
  try {
    rzpOrder = await createRazorpayOrder(env, {
      amountRupees: product.amountRupees,
      receipt,
      notes: { product_id: body.productId, our_order_id: orderId },
    });
  } catch (err) {
    return json({ error: "Could not start checkout. Try again." }, { status: 502 });
  }

  await env.DB
    .prepare(
      `INSERT INTO orders
       (id, razorpay_order_id, product_id, product_type, amount_rupees, buyer_name, buyer_email, buyer_phone, shipping_json, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')`
    )
    .bind(
      orderId,
      rzpOrder.id,
      body.productId,
      product.type,
      product.amountRupees,
      buyer.name,
      buyerEmail,
      buyer.phone,
      body.shipping ? JSON.stringify(body.shipping) : null
    )
    .run();

  return json({
    razorpayOrderId: rzpOrder.id,
    amount: rzpOrder.amount,
    currency: rzpOrder.currency,
    keyId: env.RAZORPAY_KEY_ID,
    productTitle: product.title,
  });
}

async function handleOrderVerify(request, env) {
  const body = await readJson(request);
  const { razorpayOrderId, razorpayPaymentId, razorpaySignature } = body;

  const valid = await verifyRazorpaySignature(env, {
    orderId: razorpayOrderId,
    paymentId: razorpayPaymentId,
    signature: razorpaySignature,
  });
  if (!valid) return json({ error: "Payment could not be verified." }, { status: 400 });

  const order = await env.DB
    .prepare("SELECT * FROM orders WHERE razorpay_order_id = ?")
    .bind(razorpayOrderId)
    .first();
  if (!order) return json({ error: "Order not found." }, { status: 404 });

  if (order.status !== "paid") {
    await env.DB
      .prepare("UPDATE orders SET status = 'paid', razorpay_payment_id = ?, paid_at = datetime('now') WHERE id = ?")
      .bind(razorpayPaymentId, order.id)
      .run();

    if (order.product_type === "book_pdf") {
      await env.DB
        .prepare(
          "INSERT OR REPLACE INTO entitlements (user_email, product_id, order_id) VALUES (?, ?, ?)"
        )
        .bind(order.buyer_email, order.product_id, order.id)
        .run();
    }

    // Notify Pranav for anything needing manual follow-up (shipping, course enrolment).
    if (order.product_type !== "book_pdf") {
      const product = getProduct(order.product_id);
      const shipping = order.shipping_json ? JSON.parse(order.shipping_json) : null;
      const lines = [
        `<p><strong>${product ? product.title : order.product_id}</strong> — ₹${order.amount_rupees}</p>`,
        `<p>${order.buyer_name} · ${order.buyer_email} · ${order.buyer_phone}</p>`,
      ];
      if (shipping) {
        lines.push(
          `<p>Ship to: ${shipping.address1}${shipping.address2 ? ", " + shipping.address2 : ""}, ${shipping.city}, ${shipping.state} ${shipping.pincode}</p>`
        );
      }
      try {
        await sendEmail(env, {
          to: CONTACT_TO,
          subject: `New order — ${product ? product.title : order.product_id}`,
          html: lines.join("\n"),
          fromLocal: "orders",
        });
      } catch {
        // Order is already recorded in D1 either way — email is a convenience, not the record of truth.
      }
    }
  }

  return json({ ok: true, productType: order.product_type, productId: order.product_id });
}

async function handleRead(request, env, url) {
  const productId = url.searchParams.get("product");
  const product = productId && getProduct(productId);
  if (!product || product.type !== "book_pdf") return json({ error: "Not found." }, { status: 404 });

  const email = await getSessionEmail(env.DB, request);
  if (!email) return json({ error: "Please log in." }, { status: 401 });

  const entitled = await env.DB
    .prepare("SELECT 1 FROM entitlements WHERE user_email = ? AND product_id = ?")
    .bind(email, productId)
    .first();
  if (!entitled) return json({ error: "You don't have access to this book." }, { status: 403 });

  const object = await env.VAULT.get(product.fileKey);
  if (!object) return json({ error: "File missing — contact support." }, { status: 500 });

  return new Response(object.body, {
    headers: {
      "Content-Type": "application/pdf",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

async function handleContact(request, env) {
  const { name, email, message } = await readJson(request);
  if (!name || !isValidEmail(email) || !message) {
    return json({ error: "Please fill in your name, a valid email and a message." }, { status: 400 });
  }
  await env.DB
    .prepare("INSERT INTO contact_messages (id, name, email, message) VALUES (?, ?, ?, ?)")
    .bind(crypto.randomUUID(), name, email, message)
    .run();
  try {
    await sendEmail(env, {
      to: CONTACT_TO,
      subject: `Website contact form — ${name}`,
      html: `<p><strong>${name}</strong> (${email})</p><p>${String(message).replace(/</g, "&lt;")}</p>`,
      fromLocal: "contact",
    });
  } catch {
    // Message is already saved in D1 even if the notification email fails.
  }
  return json({ ok: true });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/")) {
      try {
        if (url.pathname === "/api/otp/send" && request.method === "POST") return await handleOtpSend(request, env);
        if (url.pathname === "/api/otp/verify" && request.method === "POST") return await handleOtpVerify(request, env);
        if (url.pathname === "/api/logout" && request.method === "POST") return await handleLogout(request, env);
        if (url.pathname === "/api/me" && request.method === "GET") return await handleMe(request, env);
        if (url.pathname === "/api/orders/create" && request.method === "POST") return await handleOrderCreate(request, env);
        if (url.pathname === "/api/orders/verify" && request.method === "POST") return await handleOrderVerify(request, env);
        if (url.pathname === "/api/read" && request.method === "GET") return await handleRead(request, env, url);
        if (url.pathname === "/api/contact" && request.method === "POST") return await handleContact(request, env);
      } catch (err) {
        return json({ error: "Something went wrong. Please try again." }, { status: 500 });
      }
      return json({ error: "Not found." }, { status: 404 });
    }

    return env.ASSETS.fetch(request);
  },
};
