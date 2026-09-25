/*
  Thin wrapper around Cloudflare's Email Sending REST API.
  https://api.cloudflare.com/client/v4/accounts/{account_id}/email/sending/send
  Same product already verified working for capranav.com's domain.
*/
export async function sendEmail(env, { to, subject, html, fromLocal = "noreply", fromName = "CA Pranav" }) {
  const url = `https://api.cloudflare.com/client/v4/accounts/${env.CF_EMAIL_ACCOUNT_ID}/email/sending/send`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.CF_EMAIL_API_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: `${fromName} <${fromLocal}@capranav.com>`,
      to,
      subject,
      html,
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.success) {
    throw new Error("Email send failed: " + JSON.stringify(data));
  }
  return data;
}

export function otpEmailHtml(code) {
  return `
    <div style="font-family:sans-serif;max-width:420px;margin:0 auto;padding:24px;">
      <p style="font-size:13px;color:#667085;text-transform:uppercase;letter-spacing:.08em;">CA Pranav — login code</p>
      <p style="font-size:36px;font-weight:800;letter-spacing:.06em;margin:12px 0;">${code}</p>
      <p style="font-size:14px;color:#475467;">This code expires in 10 minutes. If you didn't request this, ignore this email.</p>
    </div>`;
}

const ACTION_BY_TYPE = {
  book_pdf: { label: "PDF access", action: "No action needed — reader access was granted automatically.", bg: "#eaf6ec", color: "#1a7f37" },
  book_physical: { label: "Physical book", action: "Action needed — pack and ship this book to the address below.", bg: "#fdf1e8", color: "#b45309" },
  course: { label: "Course enrolment", action: "Action needed — enrol this student in the batch and share access details.", bg: "#fdf1e8", color: "#b45309" },
};

/*
  The order-notification email, sent once per paid order (every product
  type — previously this only fired for courses/physical books, leaving
  every PDF purchase with zero email visibility at all). One place to fix
  formatting/detail going forward.
*/
export function orderNotificationEmailHtml(order, product, shipping) {
  const meta = ACTION_BY_TYPE[order.product_type] || { label: order.product_type, action: "", bg: "#f2f2f2", color: "#333" };
  const row = (label, value) =>
    value
      ? `<tr><td style="padding:7px 0;color:#667085;font-size:13px;vertical-align:top;white-space:nowrap;">${label}</td><td style="padding:7px 0 7px 14px;font-size:13px;">${value}</td></tr>`
      : "";
  return `
    <div style="font-family:sans-serif;max-width:540px;margin:0 auto;padding:24px;">
      <p style="font-size:13px;color:#667085;text-transform:uppercase;letter-spacing:.08em;margin:0 0 6px;">CA Pranav — new order</p>
      <h2 style="margin:0 0 4px;font-size:22px;">${product ? product.title : order.product_id}</h2>
      <p style="margin:0 0 18px;font-size:22px;font-weight:800;">₹${order.amount_rupees}</p>
      <table style="width:100%;border-collapse:collapse;">
        ${row("Type", meta.label)}
        ${row("Buyer", `${order.buyer_name} · ${order.buyer_email} · ${order.buyer_phone}`)}
        ${shipping ? row("Ship to", `${shipping.address1}${shipping.address2 ? ", " + shipping.address2 : ""}, ${shipping.city}, ${shipping.state} ${shipping.pincode}`) : ""}
        ${row("Order ID", `<span style="font-family:monospace;font-size:11.5px;">${order.id}</span>`)}
        ${row("Razorpay payment", `<span style="font-family:monospace;font-size:11.5px;">${order.razorpay_payment_id || "—"}</span>`)}
        ${row("Paid at", `${order.paid_at || "—"} (UTC)`)}
      </table>
      <p style="margin:18px 0 0;padding:12px 14px;border-radius:8px;background:${meta.bg};color:${meta.color};font-size:13px;font-weight:600;">${meta.action}</p>
    </div>`;
}

const BUYER_NEXT_STEP = {
  book_pdf: `Your book is ready to read — head to <a href="https://capranav.com/dashboard">your dashboard</a> and click "Read now".`,
  book_physical: "Your book ships prepaid — we'll dispatch it within a few business days and reach out on the phone/email you shared with delivery details.",
  course: "We'll reach out on the email/phone you shared within 24 hours with your batch details.",
};

/*
  Sent to the BUYER (not Pranav) once an order is marked paid — previously
  the only confirmation a buyer ever saw was an in-browser "Thank you"
  message that vanished the moment they closed the tab.
*/
export function buyerConfirmationEmailHtml(order, product) {
  const nextStep = BUYER_NEXT_STEP[order.product_type] || "";
  return `
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:24px;">
      <p style="font-size:13px;color:#667085;text-transform:uppercase;letter-spacing:.08em;margin:0 0 6px;">Order confirmed</p>
      <h2 style="margin:0 0 4px;font-size:22px;">${product ? product.title : order.product_id}</h2>
      <p style="margin:0 0 18px;font-size:20px;font-weight:800;">₹${order.amount_rupees}</p>
      <p style="font-size:14px;color:#475467;line-height:1.6;">Thanks for your order — payment has been received and confirmed.</p>
      <p style="font-size:14px;color:#475467;line-height:1.6;">${nextStep}</p>
      <p style="font-size:12px;color:#98a2b3;margin-top:24px;">Order ID: ${order.id}${order.razorpay_payment_id ? " · Payment ID: " + order.razorpay_payment_id : ""}</p>
      <p style="font-size:12px;color:#98a2b3;">Questions? Reply to this email or write to capranavpratiktulshyan@gmail.com.</p>
    </div>`;
}
