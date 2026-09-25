import { getProduct } from "./lib/products.js";
import { isDataPath, isSameSiteRequest, limited, deny } from "./lib/guard.js";
import { runBackup } from "./lib/backup.js";
import {
  randomOtpCode,
  otpExpiry,
  createSession,
  sessionCookieHeader,
  clearCookieHeader,
  getSessionEmail,
  isValidEmail,
} from "./lib/session.js";
import { sendEmail, otpEmailHtml, orderNotificationEmailHtml, buyerConfirmationEmailHtml } from "./lib/email.js";
import { createRazorpayOrder, verifyRazorpaySignature, verifyWebhookSignature } from "./lib/razorpay.js";
import {
  verifyAdminLogin,
  createAdminSession,
  adminCookieHeader,
  clearAdminCookieHeader,
  getAdminUsername,
  isLoginRateLimited,
  recordFailedLogin,
} from "./lib/admin.js";

const CONTACT_TO = "capranavpratiktulshyan@gmail.com";

// Rate limits — simple, D1-backed, windowed counts. Reasonable enough to
// stop unlimited automated abuse without getting in the way of a real
// person occasionally re-requesting a code or re-sending a message.
const OTP_MAX_PER_HOUR = 5;
// Per-IP ceiling across ALL emails — the per-email cap alone lets one bot request
// codes for unlimited different addresses (email-bombing third parties).
const OTP_MAX_PER_IP_PER_HOUR = 10;
const CONTACT_MAX_PER_HOUR = 5;

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

  // otp_codes already logs every request with a timestamp — reuse it as the
  // rate-limit counter rather than adding a new table.
  const recent = await env.DB
    .prepare("SELECT COUNT(*) AS c FROM otp_codes WHERE email = ? AND created_at > datetime('now', '-60 minutes')")
    .bind(clean)
    .first();
  if (recent && recent.c >= OTP_MAX_PER_HOUR) {
    return json({ error: "Too many codes requested for this email. Please wait a while and try again." }, { status: 429 });
  }

  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const recentFromIp = await env.DB
    .prepare("SELECT COUNT(*) AS c FROM otp_codes WHERE ip = ? AND created_at > datetime('now', '-60 minutes')")
    .bind(ip)
    .first();
  if (recentFromIp && recentFromIp.c >= OTP_MAX_PER_IP_PER_HOUR) {
    return json({ error: "Too many codes requested from this network. Please wait a while and try again." }, { status: 429 });
  }

  const code = randomOtpCode();
  await env.DB
    .prepare("INSERT INTO otp_codes (email, code, expires_at, ip) VALUES (?, ?, ?, ?)")
    .bind(clean, code, otpExpiry(), ip)
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

async function handleProfileGet(request, env) {
  const email = await getSessionEmail(env.DB, request);
  if (!email) return json({ error: "Please log in." }, { status: 401 });

  const profile = await env.DB
    .prepare("SELECT name, phone FROM student_profiles WHERE email = ?")
    .bind(email)
    .first();
  if (profile) return json({ email, name: profile.name, phone: profile.phone });

  // No saved profile yet — fall back to the most recent order's buyer
  // details as a sensible default, so the form isn't blank for someone
  // who's already bought something. Nothing is written until they Save.
  const lastOrder = await env.DB
    .prepare("SELECT buyer_name, buyer_phone FROM orders WHERE buyer_email = ? ORDER BY created_at DESC LIMIT 1")
    .bind(email)
    .first();
  return json({ email, name: lastOrder ? lastOrder.buyer_name : "", phone: lastOrder ? lastOrder.buyer_phone : "" });
}

async function handleProfileUpdate(request, env) {
  const email = await getSessionEmail(env.DB, request);
  if (!email) return json({ error: "Please log in." }, { status: 401 });

  const { name, phone } = await readJson(request);
  if (!name || !phone) return json({ error: "Name and phone are required." }, { status: 400 });

  await env.DB
    .prepare(
      `INSERT INTO student_profiles (email, name, phone, updated_at) VALUES (?, ?, ?, datetime('now'))
       ON CONFLICT(email) DO UPDATE SET name = excluded.name, phone = excluded.phone, updated_at = excluded.updated_at`
    )
    .bind(email, name, phone)
    .run();
  return json({ ok: true, name, phone });
}

async function handleOrdersMine(request, env) {
  const email = await getSessionEmail(env.DB, request);
  if (!email) return json({ error: "Please log in." }, { status: 401 });

  const rows = await env.DB
    .prepare(
      "SELECT id, product_id, product_type, amount_rupees, status, created_at, paid_at FROM orders WHERE buyer_email = ? ORDER BY created_at DESC"
    )
    .bind(email)
    .all();

  const orders = (rows.results || []).map((o) => {
    const product = getProduct(o.product_id);
    return {
      id: o.id,
      productId: o.product_id,
      productTitle: product ? product.title : o.product_id,
      productType: o.product_type,
      amountRupees: o.amount_rupees,
      status: o.status,
      createdAt: o.created_at,
      paidAt: o.paid_at,
    };
  });
  return json({ orders });
}

async function handleOrderCreate(request, env) {
  const body = await readJson(request);
  const product = getProduct(body.productId);
  if (!product) return json({ error: "Unknown product." }, { status: 400 });

  // Sold on an external store (see products.js) — never open a Razorpay order
  // for it here. Existing entitlements for such a product are untouched; only
  // NEW in-site purchases are refused.
  if (product.externalCheckoutUrl) {
    return json(
      { error: "This book is now sold on VC Gurukul.", externalCheckoutUrl: product.externalCheckoutUrl },
      { status: 409 }
    );
  }

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

/*
  Marks an order paid exactly once, no matter how many times this gets
  called for the same order — the browser's own /api/orders/verify call and
  the Razorpay webhook can both legitimately fire for the same payment, and
  can race each other. The idempotency guard is the UPDATE's WHERE clause
  itself (an atomic conditional write), not a SELECT-then-decide beforehand
  — that's what keeps this safe under a real race, not just a re-run. Only
  the caller whose UPDATE actually changed a row goes on to grant the
  entitlement / send the notification email; the other becomes a no-op.
*/
async function markOrderPaid(env, order, razorpayPaymentId) {
  // Computed here (not left to SQLite's datetime('now')) so the exact same
  // value can go into both the UPDATE and the notification email below —
  // `order` is a pre-update snapshot, so re-reading paid_at/payment_id off
  // it would show stale/null values otherwise.
  const paidAt = new Date().toISOString().slice(0, 19).replace("T", " ");
  const result = await env.DB
    .prepare(
      "UPDATE orders SET status = 'paid', razorpay_payment_id = ?, paid_at = ? WHERE id = ? AND status != 'paid'"
    )
    .bind(razorpayPaymentId, paidAt, order.id)
    .run();
  const didTransition = result.meta && result.meta.changes === 1;
  if (!didTransition) return; // already marked paid via the other path — nothing more to do

  if (order.product_type === "book_pdf") {
    await env.DB
      .prepare(
        "INSERT OR REPLACE INTO entitlements (user_email, product_id, order_id) VALUES (?, ?, ?)"
      )
      .bind(order.buyer_email, order.product_id, order.id)
      .run();
  }

  // Notify Pranav on every paid order, whatever the type — PDF purchases used
  // to send nothing at all here, leaving zero visibility into them beyond
  // querying D1 by hand.
  const product = getProduct(order.product_id);
  const shipping = order.shipping_json ? JSON.parse(order.shipping_json) : null;
  const orderForEmail = { ...order, razorpay_payment_id: razorpayPaymentId, paid_at: paidAt };
  try {
    await sendEmail(env, {
      to: CONTACT_TO,
      subject: `New order — ${product ? product.title : order.product_id} (₹${order.amount_rupees})`,
      html: orderNotificationEmailHtml(orderForEmail, product, shipping),
      fromLocal: "orders",
    });
  } catch (err) {
    console.error("order notification email failed:", err && err.message);
    // Order is already recorded in D1 either way — email is a convenience, not the record of truth.
  }

  // Also confirm the order to the buyer themselves — previously the only
  // thing they ever saw was an in-browser "Thank you" message that vanished
  // the moment the tab closed, no record of their own afterward.
  if (order.buyer_email) {
    try {
      await sendEmail(env, {
        to: order.buyer_email,
        subject: `Order confirmed — ${product ? product.title : order.product_id}`,
        html: buyerConfirmationEmailHtml(orderForEmail, product),
        fromLocal: "orders",
      });
    } catch (err) {
      console.error("buyer confirmation email failed:", err && err.message);
    }
  }
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

  await markOrderPaid(env, order, razorpayPaymentId);

  return json({ ok: true, productType: order.product_type, productId: order.product_id });
}

/*
  Razorpay calling us directly when a payment succeeds — independent of
  whether the buyer's browser is still around to call /api/orders/verify.
  This is what closes the gap where a payment succeeds on Razorpay's side
  but the tab closes/crashes before the client-side verify call runs.
*/
async function handleRazorpayWebhook(request, env) {
  // Read the raw body FIRST — the signature is computed over the exact bytes
  // Razorpay sent, and re-serializing parsed JSON can change whitespace/key
  // order and silently break verification.
  const rawBody = await request.text();
  const signature = request.headers.get("X-Razorpay-Signature") || "";
  const valid = await verifyWebhookSignature(env, rawBody, signature);
  if (!valid) return json({ error: "Invalid signature." }, { status: 400 });

  let event;
  try {
    event = JSON.parse(rawBody);
  } catch {
    return json({ error: "Bad payload." }, { status: 400 });
  }

  // Idempotency: Razorpay can legitimately deliver the same event more than
  // once. Its own X-Razorpay-Event-Id header is unique per event — recording
  // it here (PK conflict = "already seen") means a re-delivery is acked and
  // dropped before it can touch anything else.
  const eventId = request.headers.get("X-Razorpay-Event-Id") || "";
  if (eventId) {
    try {
      await env.DB
        .prepare("INSERT INTO webhook_events (event_id, event_type) VALUES (?, ?)")
        .bind(eventId, event.event || "")
        .run();
    } catch {
      return json({ ok: true, duplicate: true });
    }
  }

  if (event.event === "order.paid") {
    const orderEntity = event.payload && event.payload.order && event.payload.order.entity;
    const paymentEntity = event.payload && event.payload.payment && event.payload.payment.entity;
    if (orderEntity && orderEntity.id) {
      const order = await env.DB
        .prepare("SELECT * FROM orders WHERE razorpay_order_id = ?")
        .bind(orderEntity.id)
        .first();
      if (order) {
        await markOrderPaid(env, order, paymentEntity ? paymentEntity.id : null);
      }
      // No matching order row is unexpected (every order we create is written
      // to D1 before the buyer ever sees Razorpay Checkout) but not an error
      // worth failing/retrying the webhook over — acknowledge and move on.
    }
  }
  // payment.failed: acknowledged (recorded above for dedup/audit) but no
  // order mutation. A single failed attempt doesn't mean the order is dead —
  // Razorpay lets the buyer retry the same order — so leaving status as-is
  // means a later successful attempt on the same order still works normally.

  return json({ ok: true });
}

/*
  Parses a standard HTTP "bytes=..." Range header into an R2Range. Returns
  null for anything malformed or multi-range (multi-range responses are a
  real HTTP feature this doesn't support — PDF.js never sends one, so this
  intentionally falls back to a full 200 response rather than guessing).
*/
function parseRangeHeader(header, totalSize) {
  if (!header || !header.startsWith("bytes=")) return null;
  const spec = header.slice("bytes=".length).trim();
  if (spec.includes(",")) return null; // multi-range — not supported

  const suffixMatch = /^-(\d+)$/.exec(spec);
  if (suffixMatch) return { suffix: Math.min(Number(suffixMatch[1]), totalSize) };

  const rangeMatch = /^(\d+)-(\d*)$/.exec(spec);
  if (!rangeMatch) return null;
  const start = Number(rangeMatch[1]);
  if (start >= totalSize) return null;
  if (rangeMatch[2] === "") return { offset: start }; // "start-" = start through end of file
  const end = Number(rangeMatch[2]);
  return { offset: start, length: Math.min(end, totalSize - 1) - start + 1 };
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

  // PDF.js streams the file page-by-page via HTTP Range requests instead of
  // downloading the whole PDF up front — that only works if this endpoint
  // actually honors Range, not just returns the full body every time.
  const totalMeta = await env.VAULT.head(product.fileKey);
  if (!totalMeta) return json({ error: "File missing — contact support." }, { status: 500 });

  const range = parseRangeHeader(request.headers.get("Range"), totalMeta.size);
  const object = range ? await env.VAULT.get(product.fileKey, { range }) : await env.VAULT.get(product.fileKey);
  if (!object) return json({ error: "File missing — contact support." }, { status: 500 });

  const baseHeaders = {
    "Content-Type": "application/pdf",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Accept-Ranges": "bytes",
  };

  if (range && object.range) {
    const start = object.range.offset ?? totalMeta.size - object.range.length;
    const length = object.range.length ?? totalMeta.size - object.range.offset;
    const end = start + length - 1;
    return new Response(object.body, {
      status: 206,
      headers: {
        ...baseHeaders,
        "Content-Range": `bytes ${start}-${end}/${totalMeta.size}`,
        "Content-Length": String(length),
      },
    });
  }

  return new Response(object.body, {
    headers: { ...baseHeaders, "Content-Length": String(totalMeta.size) },
  });
}

async function handleContact(request, env) {
  const body = await readJson(request);
  const { name, email, message } = body;

  // Honeypot: a hidden field real visitors never see or fill, but a bot
  // filling every field in the form does. Ack as success without saving or
  // emailing anything — no signal back to the bot that it was caught.
  if (body.website) return json({ ok: true });

  if (!name || !isValidEmail(email) || !message) {
    return json({ error: "Please fill in your name, a valid email and a message." }, { status: 400 });
  }

  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const recent = await env.DB
    .prepare("SELECT COUNT(*) AS c FROM contact_messages WHERE ip = ? AND created_at > datetime('now', '-60 minutes')")
    .bind(ip)
    .first();
  if (recent && recent.c >= CONTACT_MAX_PER_HOUR) {
    return json({ error: "Too many messages sent recently. Please try again later." }, { status: 429 });
  }

  await env.DB
    .prepare("INSERT INTO contact_messages (id, name, email, message, ip) VALUES (?, ?, ?, ?, ?)")
    .bind(crypto.randomUUID(), name, email, message, ip)
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

async function handleAdminLogin(request, env) {
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  if (await isLoginRateLimited(env.DB, ip)) {
    return json({ error: "Too many failed attempts. Please wait a while and try again." }, { status: 429 });
  }

  const { username, password } = await readJson(request);
  const ok = await verifyAdminLogin(env.DB, username, password);
  if (!ok) {
    await recordFailedLogin(env.DB, ip);
    return json({ error: "Invalid username or password." }, { status: 401 });
  }

  const { token, expires } = await createAdminSession(env.DB, username);
  return json({ ok: true }, { headers: { "Set-Cookie": adminCookieHeader(token, expires) } });
}

async function handleAdminLogout(request, env) {
  return json({ ok: true }, { headers: { "Set-Cookie": clearAdminCookieHeader() } });
}

async function handleAdminMe(request, env) {
  const username = await getAdminUsername(env.DB, request);
  return json({ loggedIn: !!username, username: username || null });
}

/*
  Read-only preview of what a deletion would touch, shown before the admin
  confirms — same "show what will be affected before an irreversible
  action" discipline used for destructive actions elsewhere.
*/
async function handleAdminLookup(request, env) {
  const username = await getAdminUsername(env.DB, request);
  if (!username) return json({ error: "Please log in." }, { status: 401 });

  const { email } = await readJson(request);
  if (!isValidEmail(email)) return json({ error: "Enter a valid email address." }, { status: 400 });
  const clean = email.trim().toLowerCase();

  const [orders, profile, entitlements, sessionsRow, contactRow, otpRow] = await Promise.all([
    env.DB.prepare("SELECT COUNT(*) AS c FROM orders WHERE buyer_email = ?").bind(clean).first(),
    env.DB.prepare("SELECT 1 FROM student_profiles WHERE email = ?").bind(clean).first(),
    env.DB.prepare("SELECT COUNT(*) AS c FROM entitlements WHERE user_email = ?").bind(clean).first(),
    env.DB.prepare("SELECT COUNT(*) AS c FROM sessions WHERE user_email = ?").bind(clean).first(),
    env.DB.prepare("SELECT COUNT(*) AS c FROM contact_messages WHERE email = ?").bind(clean).first(),
    env.DB.prepare("SELECT COUNT(*) AS c FROM otp_codes WHERE email = ?").bind(clean).first(),
  ]);

  return json({
    email: clean,
    orders: orders.c,
    hasProfile: !!profile,
    entitlements: entitlements.c,
    sessions: sessionsRow.c,
    contactMessages: contactRow.c,
    otpCodes: otpRow.c,
  });
}

/*
  The actual privacy-policy deletion action: orders are ANONYMIZED (name/
  email/phone/shipping replaced, but the row itself — amount, product,
  date, status — is kept for accounting/GST record-keeping, matching what
  the privacy policy already promises), everything else tied to this
  email is deleted outright. Logged to deletion_log either way.
*/
async function handleAdminDeleteStudent(request, env) {
  const username = await getAdminUsername(env.DB, request);
  if (!username) return json({ error: "Please log in." }, { status: 401 });

  const { email } = await readJson(request);
  if (!isValidEmail(email)) return json({ error: "Enter a valid email address." }, { status: 400 });
  const clean = email.trim().toLowerCase();

  const [ordersResult, profileResult, entitlementsResult, sessionsResult, contactResult, otpResult] = await Promise.all([
    env.DB
      .prepare(
        "UPDATE orders SET buyer_name = '[deleted]', buyer_email = '[deleted]', buyer_phone = '[deleted]', shipping_json = NULL WHERE buyer_email = ?"
      )
      .bind(clean)
      .run(),
    env.DB.prepare("DELETE FROM student_profiles WHERE email = ?").bind(clean).run(),
    env.DB.prepare("DELETE FROM entitlements WHERE user_email = ?").bind(clean).run(),
    env.DB.prepare("DELETE FROM sessions WHERE user_email = ?").bind(clean).run(),
    env.DB.prepare("DELETE FROM contact_messages WHERE email = ?").bind(clean).run(),
    env.DB.prepare("DELETE FROM otp_codes WHERE email = ?").bind(clean).run(),
  ]);

  const details = {
    ordersAnonymized: ordersResult.meta.changes,
    profileDeleted: profileResult.meta.changes,
    entitlementsDeleted: entitlementsResult.meta.changes,
    sessionsDeleted: sessionsResult.meta.changes,
    contactMessagesDeleted: contactResult.meta.changes,
    otpCodesDeleted: otpResult.meta.changes,
  };

  await env.DB
    .prepare("INSERT INTO deletion_log (id, student_email, admin_username, details_json) VALUES (?, ?, ?, ?)")
    .bind(crypto.randomUUID(), clean, username, JSON.stringify(details))
    .run();

  return json({ ok: true, ...details });
}

async function handleAnatomyOverview(env) {
  const [counts, coverage, latestImport, sittingValidation] = await Promise.all([
    env.DB.prepare(`
      SELECT
        (SELECT COUNT(*) FROM aa_modules) AS modules,
        (SELECT COUNT(*) FROM aa_chapters) AS chapters,
        (SELECT COUNT(*) FROM aa_units) AS units,
        (SELECT COUNT(*) FROM aa_topics) AS topics,
        (SELECT COUNT(*) FROM aa_sittings) AS sittings,
        (SELECT COUNT(*) FROM aa_questions) AS questions,
        (SELECT COUNT(*) FROM aa_question_topics) AS question_topic_links,
        (SELECT COUNT(*) FROM aa_study_items) AS study_items,
        (SELECT COUNT(*) FROM aa_pyq_study_matches WHERE similarity_percent IS NOT NULL) AS verified_similarity_rows
    `).first(),
    env.DB.prepare(`
      SELECT
        SUM(CASE WHEN EXISTS (SELECT 1 FROM aa_question_topics qt WHERE qt.question_id = q.question_id) THEN 1 ELSE 0 END) AS mapped_questions,
        SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM aa_question_topics qt WHERE qt.question_id = q.question_id) THEN 1 ELSE 0 END) AS unmapped_questions,
        SUM(CASE WHEN q.marks IS NULL AND s.paper_type <> 'RTP' THEN 1 ELSE 0 END) AS questions_missing_marks
      FROM aa_questions q
      JOIN aa_sittings s ON s.sitting_id = q.sitting_id
    `).first(),
    env.DB.prepare("SELECT * FROM aa_import_runs ORDER BY imported_at DESC, rowid DESC LIMIT 1").first(),
    env.DB.prepare("SELECT * FROM aa_v_sitting_validation ORDER BY exam_year DESC, attempt_month_no DESC, paper_type, set_no").all(),
  ]);
  return json({ counts, coverage, latestImport, sittingValidation: sittingValidation.results || [] });
}

async function handleAnatomyHierarchy(env) {
  const [modules, chapters, units] = await Promise.all([
    env.DB.prepare("SELECT module_id, module_no, name, display_order FROM aa_modules ORDER BY display_order").all(),
    env.DB.prepare(`
      SELECT c.chapter_id, c.module_id, c.chapter_no, c.name, c.short_name, c.display_order,
             COUNT(DISTINCT u.unit_id) AS unit_count, COUNT(DISTINCT t.topic_id) AS topic_count
      FROM aa_chapters c
      LEFT JOIN aa_units u ON u.chapter_id = c.chapter_id
      LEFT JOIN aa_topics t ON t.unit_id = u.unit_id
      GROUP BY c.chapter_id ORDER BY c.display_order
    `).all(),
    env.DB.prepare(`
      SELECT u.unit_id, u.chapter_id, u.unit_no, u.name, u.accounting_standard, u.teaching_sequence,
             COUNT(DISTINCT t.topic_id) AS topic_count,
             COUNT(DISTINCT qu.question_id) AS question_count
      FROM aa_units u
      LEFT JOIN aa_topics t ON t.unit_id = u.unit_id
      LEFT JOIN aa_question_units qu ON qu.unit_id = u.unit_id
      GROUP BY u.unit_id ORDER BY u.display_order
    `).all(),
  ]);
  return json({ modules: modules.results || [], chapters: chapters.results || [], units: units.results || [] });
}

async function handleAnatomyTopics(env, url) {
  const clauses = [];
  const values = [];
  for (const [column, parameter] of [["m.module_id", "module"], ["c.chapter_id", "chapter"], ["u.unit_id", "unit"]]) {
    const value = url.searchParams.get(parameter);
    if (value) { clauses.push(`${column} = ?`); values.push(value); }
  }
  const search = (url.searchParams.get("q") || "").trim();
  if (search) {
    clauses.push("(t.topic_id LIKE ? OR t.name LIKE ? OR t.page_number LIKE ? OR u.name LIKE ? OR c.name LIKE ? OR t.priority_band LIKE ?)");
    const pattern = `%${search}%`;
    values.push(pattern, pattern, pattern, pattern, pattern, pattern);
  }
  const priorityBand = url.searchParams.get("priorityBand");
  if (priorityBand) { clauses.push("t.priority_band = ?"); values.push(priorityBand); }
  const where = clauses.length ? `WHERE ${clauses.join(" AND ")}` : "";
  const rows = await env.DB.prepare(`
    SELECT t.topic_id, t.topic_no, t.name, t.short_name, t.page_number, t.overall_rank, t.priority_band,
           u.unit_id, u.name AS unit_name, u.accounting_standard,
           c.chapter_id, c.name AS chapter_name, m.module_id, m.name AS module_name,
           COUNT(DISTINCT qt.question_id) AS question_count,
           COUNT(DISTINCT q.sitting_id) AS sitting_count,
           ROUND(SUM(COALESCE(q.marks, 0)), 2) AS linked_marks,
           (SELECT d.document_id FROM aa_unit_documents ud JOIN aa_documents d ON d.document_id = ud.document_id WHERE ud.unit_id = u.unit_id AND d.document_type = 'study_material' AND d.published = 1 LIMIT 1) AS study_document_id
    FROM aa_topics t
    JOIN aa_units u ON u.unit_id = t.unit_id
    JOIN aa_chapters c ON c.chapter_id = u.chapter_id
    JOIN aa_modules m ON m.module_id = c.module_id
    LEFT JOIN aa_question_topics qt ON qt.topic_id = t.topic_id
    LEFT JOIN aa_questions q ON q.question_id = qt.question_id
    ${where}
    GROUP BY t.topic_id
    ORDER BY t.display_order LIMIT 500
  `).bind(...values).all();
  return json({ topics: rows.results || [] });
}

async function handleAnatomyQuestions(env, url) {
  const clauses = [];
  const values = [];
  for (const [column, parameter] of [["q.sitting_id", "sitting"], ["s.paper_type", "paperType"], ["qu.unit_id", "unit"], ["qt.topic_id", "topic"]]) {
    const value = url.searchParams.get(parameter);
    if (value) { clauses.push(`${column} = ?`); values.push(value); }
  }
  const limit = Math.min(Math.max(Number(url.searchParams.get("limit")) || 100, 1), 200);
  const where = clauses.length ? `WHERE ${clauses.join(" AND ")}` : "";
  const rows = await env.DB.prepare(`
    SELECT DISTINCT q.question_id, q.question_no, q.sub_part, q.alternative_code, q.marks,
           q.question_type, q.source_file, q.topic_mapping_review,
           s.sitting_id, s.label AS sitting_label, s.paper_type, s.exam_year, s.attempt_month,
           u.unit_id AS final_unit_id, u.name AS final_unit_name,
           pm.match_status, pm.similarity_percent, pm.review_status,
           (SELECT d.document_id FROM aa_sitting_documents sd JOIN aa_documents d ON d.document_id = sd.document_id WHERE sd.sitting_id = s.sitting_id AND d.document_type = 'question_paper' AND d.published = 1 LIMIT 1) AS question_document_id,
           (SELECT d.document_id FROM aa_sitting_documents sd JOIN aa_documents d ON d.document_id = sd.document_id WHERE sd.sitting_id = s.sitting_id AND d.document_type = 'answer' AND d.published = 1 LIMIT 1) AS answer_document_id,
           (SELECT d.document_id FROM aa_sitting_documents sd JOIN aa_documents d ON d.document_id = sd.document_id WHERE sd.sitting_id = s.sitting_id AND d.document_type = 'examiner_comments' AND d.published = 1 LIMIT 1) AS comments_document_id
    FROM aa_questions q
    JOIN aa_sittings s ON s.sitting_id = q.sitting_id
    LEFT JOIN aa_units u ON u.unit_id = q.final_unit_id
    LEFT JOIN aa_question_units qu ON qu.question_id = q.question_id
    LEFT JOIN aa_question_topics qt ON qt.question_id = q.question_id
    LEFT JOIN aa_pyq_study_matches pm ON pm.question_id = q.question_id
    ${where}
    ORDER BY s.exam_year DESC, s.attempt_month_no DESC, s.paper_type, s.set_no, q.question_no, q.sub_part
    LIMIT ${limit}
  `).bind(...values).all();
  return json({ questions: rows.results || [], limit });
}

async function handleAnatomyDocument(request, env, url) {
  const documentId = url.searchParams.get("doc");
  if (!documentId) return json({ error: "Document not found." }, { status: 404 });
  const document = await env.DB.prepare(
    "SELECT title, r2_key, filename, byte_size, content_type FROM aa_documents WHERE document_id = ? AND published = 1"
  ).bind(documentId).first();
  if (!document) return json({ error: "Document not found." }, { status: 404 });

  const metadata = await env.VAULT.head(document.r2_key);
  if (!metadata) return json({ error: "Document file is unavailable." }, { status: 404 });
  const range = parseRangeHeader(request.headers.get("Range"), metadata.size);
  const object = range ? await env.VAULT.get(document.r2_key, { range }) : await env.VAULT.get(document.r2_key);
  if (!object) return json({ error: "Document file is unavailable." }, { status: 404 });
  const safeFilename = String(document.filename || "document.pdf").replace(/["\\\r\n]/g, "_");
  const disposition = url.searchParams.get("download") === "1" ? "attachment" : "inline";
  const baseHeaders = {
    "Content-Type": document.content_type || "application/pdf",
    "Content-Disposition": `${disposition}; filename="${safeFilename}"`,
    "Cache-Control": "public, max-age=3600",
    "X-Content-Type-Options": "nosniff",
    "Accept-Ranges": "bytes",
  };
  if (range && object.range) {
    const start = object.range.offset ?? metadata.size - object.range.length;
    const length = object.range.length ?? metadata.size - object.range.offset;
    return new Response(object.body, { status: 206, headers: { ...baseHeaders, "Content-Range": `bytes ${start}-${start + length - 1}/${metadata.size}`, "Content-Length": String(length) } });
  }
  return new Response(object.body, { headers: { ...baseHeaders, "Content-Length": String(metadata.size) } });
}

// Baseline security headers, applied to every response the Worker produces
// (static assets get the same set from public/_headers). The CSP here is
// deliberately limited to directives that cannot break the site's inline
// scripts/styles, Razorpay checkout or the pdf.js CDN import — a full
// script-src policy is a documented follow-up in SECURITY.md.
const SECURITY_HEADERS = {
  "Strict-Transport-Security": "max-age=31536000",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "SAMEORIGIN",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), usb=(), interest-cohort=()",
  "Content-Security-Policy": "frame-ancestors 'self'; base-uri 'self'; object-src 'none'; form-action 'self'",
};

function withSecurityHeaders(response) {
  const out = new Response(response.body, response);
  for (const [k, v] of Object.entries(SECURITY_HEADERS)) {
    if (!out.headers.has(k)) out.headers.set(k, v);
  }
  return out;
}

async function runScheduled(env) {
  const status = await runBackup(env);
  if (!status.ok) {
    try {
      await sendEmail(env, {
        to: CONTACT_TO,
        subject: "capranav.com nightly backup FAILED",
        html: `<p>The nightly backup did not complete cleanly.</p><pre>${String(status.error || "unknown error").replace(/[<&]/g, "")}</pre><p>Details: R2 bucket capranav-backups, status.json. Time: ${status.at}</p>`,
        fromLocal: "alerts",
      });
    } catch (e) {
      console.error("backup alert email failed:", e && e.message);
    }
  }
}

export default {
  async fetch(request, env) {
    return withSecurityHeaders(await handleRequest(request, env));
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runScheduled(env));
  },
};

async function handleRequest(request, env) {
    const url = new URL(request.url);

    // Bulk data files: same-site pages only, and rate limited per IP (see lib/guard.js).
    if (request.method === "GET" && isDataPath(url.pathname)) {
      if (!isSameSiteRequest(request)) return deny(403, "This file is only available from capranav.com pages.");
      if (await limited(env.RL_DATA, request, "data")) return deny(429, "Too many requests. Please slow down.", { "Retry-After": "60" });
      const res = await env.ASSETS.fetch(request);
      const out = new Response(res.body, res);
      out.headers.set("X-Robots-Tag", "noindex");
      out.headers.set("Cache-Control", "private, max-age=300");
      return out;
    }

    if (url.pathname.startsWith("/api/anatomy/")) {
      const isDoc = url.pathname === "/api/anatomy/document";
      // Documents are opened by direct link, so no same-site test there, but a much lower rate limit.
      if (!isDoc && !isSameSiteRequest(request)) return deny(403, "This endpoint is only available from capranav.com pages.");
      if (await limited(isDoc ? env.RL_DOC : env.RL_API, request, isDoc ? "doc" : "anatomy")) {
        return deny(429, "Too many requests. Please slow down.", { "Retry-After": "60" });
      }
    }

    if (url.pathname.startsWith("/api/")) {
      try {
        if (url.pathname === "/api/otp/send" && request.method === "POST") return await handleOtpSend(request, env);
        if (url.pathname === "/api/otp/verify" && request.method === "POST") return await handleOtpVerify(request, env);
        if (url.pathname === "/api/logout" && request.method === "POST") return await handleLogout(request, env);
        if (url.pathname === "/api/me" && request.method === "GET") return await handleMe(request, env);
        if (url.pathname === "/api/profile" && request.method === "GET") return await handleProfileGet(request, env);
        if (url.pathname === "/api/profile/update" && request.method === "POST") return await handleProfileUpdate(request, env);
        if (url.pathname === "/api/orders/mine" && request.method === "GET") return await handleOrdersMine(request, env);
        if (url.pathname === "/api/orders/create" && request.method === "POST") return await handleOrderCreate(request, env);
        if (url.pathname === "/api/orders/verify" && request.method === "POST") return await handleOrderVerify(request, env);
        if (url.pathname === "/api/razorpay/webhook" && request.method === "POST") return await handleRazorpayWebhook(request, env);
        if (url.pathname === "/api/read" && request.method === "GET") return await handleRead(request, env, url);
        if (url.pathname === "/api/contact" && request.method === "POST") return await handleContact(request, env);
        if (url.pathname === "/api/admin/login" && request.method === "POST") return await handleAdminLogin(request, env);
        if (url.pathname === "/api/admin/logout" && request.method === "POST") return await handleAdminLogout(request, env);
        if (url.pathname === "/api/admin/me" && request.method === "GET") return await handleAdminMe(request, env);
        if (url.pathname === "/api/admin/lookup" && request.method === "POST") return await handleAdminLookup(request, env);
        if (url.pathname === "/api/admin/delete-student" && request.method === "POST") return await handleAdminDeleteStudent(request, env);
        if (url.pathname === "/api/anatomy/overview" && request.method === "GET") return await handleAnatomyOverview(env);
        if (url.pathname === "/api/anatomy/hierarchy" && request.method === "GET") return await handleAnatomyHierarchy(env);
        if (url.pathname === "/api/anatomy/topics" && request.method === "GET") return await handleAnatomyTopics(env, url);
        if (url.pathname === "/api/anatomy/questions" && request.method === "GET") return await handleAnatomyQuestions(env, url);
        if (url.pathname === "/api/anatomy/document" && request.method === "GET") return await handleAnatomyDocument(request, env, url);
      } catch (err) {
        return json({ error: "Something went wrong. Please try again." }, { status: 500 });
      }
      return json({ error: "Not found." }, { status: 404 });
    }

    return env.ASSETS.fetch(request);
}
