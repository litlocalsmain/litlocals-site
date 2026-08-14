"use strict";

const {
  safeToken,
  loadDraft,
  readPaidMarker,
  computeTier,
  previewBase,
  json,
  redirect,
} = require("../lib/drafts");
const {
  getStripe,
  listSessionsForToken,
  findPaid,
  findOpen,
} = require("../lib/stripe-sessions");

module.exports = async function handler(req, res) {
  if (req.method !== "GET" && req.method !== "POST") {
    res.setHeader("Allow", "GET, POST");
    return json(res, 405, { error: "method_not_allowed" });
  }

  const url = new URL(req.url, "http://localhost");
  const token = safeToken(url.searchParams.get("t"));
  if (!token) return json(res, 400, { error: "missing_token" });

  const draft = loadDraft(token);
  if (!draft) return json(res, 404, { error: "not_found" });
  if (!draft.sent_at) return json(res, 400, { error: "not_sent" });

  const pricing = computeTier(draft.sent_at);
  if (!pricing) return json(res, 400, { error: "not_sent" });

  const base = previewBase(req);
  const pageUrl = base + "/p/" + token + "/";
  const successUrl = pageUrl + "?paid=1";

  if (readPaidMarker(token)) return redirect(res, successUrl);

  const stripe = getStripe();
  if (!stripe) return json(res, 500, { error: "not_configured" });

  try {
    const sessions = await listSessionsForToken(stripe, token);
    if (findPaid(sessions)) return redirect(res, successUrl);

    const open = findOpen(sessions, pricing.tier);
    if (open && open.url) return redirect(res, open.url);

    const shop = draft.name || draft.shop || "this shop";
    const tierLabel = pricing.tier === "48h" ? " (48-hour price)" : "";
    const lineName =
      "Website draft for " +
      shop +
      " — deposit toward $" +
      pricing.total +
      " Lit Locals site" +
      tierLabel;

    const session = await stripe.checkout.sessions.create({
      mode: "payment",
      success_url: successUrl,
      cancel_url: pageUrl,
      customer_creation: "always",
      payment_intent_data: {
        setup_future_usage: "off_session",
      },
      line_items: [
        {
          quantity: 1,
          price_data: {
            currency: "usd",
            unit_amount: pricing.deposit_cents,
            product_data: { name: lineName },
          },
        },
      ],
      metadata: {
        draft_token: token,
        slug: String(draft.slug || ""),
        shop_name: String(shop),
        price_tier: pricing.tier,
        deposit_cents: String(pricing.deposit_cents),
        remainder_cents: String(pricing.remainder_cents),
        sent_at: String(draft.sent_at),
      },
      custom_text: {
        submit: {
          message:
            "This deposit starts the job. The remainder is due at go-live or when we zip the site.",
        },
      },
    });

    if (!session.url) return json(res, 500, { error: "checkout_failed" });
    return redirect(res, session.url);
  } catch (err) {
    const kind = err && (err.type || err.message);
    console.error("buy failed", kind || "error");
    return json(res, 500, { error: "checkout_failed" });
  }
};
