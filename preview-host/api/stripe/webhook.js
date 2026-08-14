"use strict";

const { writePaidMarker } = require("../../lib/drafts");
const { getStripe } = require("../../lib/stripe-sessions");

module.exports.config = {
  api: {
    bodyParser: false,
  },
};

async function rawBody(req) {
  if (Buffer.isBuffer(req.body)) return req.body;
  if (typeof req.body === "string") return Buffer.from(req.body);
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.statusCode = 405;
    res.setHeader("Allow", "POST");
    res.end();
    return;
  }

  const stripe = getStripe();
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!stripe || !secret) {
    res.statusCode = 500;
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify({ error: "not_configured" }));
    return;
  }

  let event;
  try {
    const buf = await rawBody(req);
    const sig = req.headers["stripe-signature"];
    event = stripe.webhooks.constructEvent(buf, sig, secret);
  } catch (_) {
    res.statusCode = 400;
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify({ error: "invalid_signature" }));
    return;
  }

  if (event.type === "checkout.session.completed") {
    const session = (event.data && event.data.object) || {};
    const token = session.metadata && session.metadata.draft_token;
    const paid =
      session.payment_status === "paid" || session.status === "complete";
    if (token && paid) {
      writePaidMarker(token, {
        session_id: session.id || null,
        event_id: event.id || null,
      });
    }
  }

  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify({ received: true }));
};
