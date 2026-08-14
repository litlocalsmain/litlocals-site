"use strict";

const {
  safeToken,
  loadDraft,
  readPaidMarker,
  computeTier,
  json,
} = require("../lib/drafts");
const {
  getStripe,
  listSessionsForToken,
  findPaid,
} = require("../lib/stripe-sessions");

module.exports = async function handler(req, res) {
  if (req.method !== "GET") {
    res.setHeader("Allow", "GET");
    return json(res, 405, { error: "method_not_allowed" });
  }

  const url = new URL(req.url, "http://localhost");
  const token = safeToken(url.searchParams.get("t"));
  if (!token) return json(res, 400, { error: "missing_token" });

  const draft = loadDraft(token);
  if (!draft) return json(res, 404, { error: "not_found" });

  let paid = readPaidMarker(token);
  const stripe = getStripe();
  if (stripe && !paid) {
    try {
      const sessions = await listSessionsForToken(stripe, token);
      paid = Boolean(findPaid(sessions));
    } catch (err) {
      console.error(
        "draft stripe lookup failed",
        err && err.message ? err.message : "error"
      );
    }
  }

  const pricing = draft.sent_at ? computeTier(draft.sent_at) : null;

  return json(res, 200, {
    token,
    sent_at: draft.sent_at || null,
    paid,
    tier: pricing ? pricing.tier : null,
    expires_at: pricing ? pricing.expires_at : null,
    deposit_cents: pricing ? pricing.deposit_cents : null,
    total: pricing ? pricing.total : null,
  });
};
