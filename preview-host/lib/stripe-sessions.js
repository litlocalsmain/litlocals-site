"use strict";

function getStripe() {
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) return null;
  const Stripe = require("stripe");
  return new Stripe(key);
}

async function listSessionsForToken(stripe, token) {
  const found = [];
  const page = await stripe.checkout.sessions.list({ limit: 100 });
  for (const s of page.data) {
    if (s.metadata && s.metadata.draft_token === token) found.push(s);
  }
  return found;
}

function findPaid(sessions) {
  return sessions.find((s) => s.payment_status === "paid") || null;
}

function findOpen(sessions, tier) {
  const now = Math.floor(Date.now() / 1000);
  return (
    sessions.find((s) => {
      if (s.status !== "open") return false;
      if (s.payment_status === "paid") return false;
      if (s.metadata && s.metadata.price_tier && s.metadata.price_tier !== tier) {
        return false;
      }
      if (s.expires_at && s.expires_at <= now) return false;
      return Boolean(s.url);
    }) || null
  );
}

module.exports = {
  getStripe,
  listSessionsForToken,
  findPaid,
  findOpen,
};
