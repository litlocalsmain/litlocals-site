"use strict";

const fs = require("fs");
const path = require("path");

const TOKEN_RE = /^[a-zA-Z0-9_-]{4,64}$/;
const HOURS_48_MS = 48 * 60 * 60 * 1000;

const TIERS = {
  "48h": {
    tier: "48h",
    deposit_cents: 75000,
    remainder_cents: 75000,
    total: 1500,
  },
  list: {
    tier: "list",
    deposit_cents: 125000,
    remainder_cents: 125000,
    total: 2500,
  },
};

function safeToken(raw) {
  if (!raw || typeof raw !== "string") return null;
  const t = raw.trim();
  return TOKEN_RE.test(t) ? t : null;
}

function draftsDir() {
  const candidates = [
    path.join(process.cwd(), "drafts"),
    path.join(__dirname, "..", "drafts"),
    path.join(__dirname, "..", "..", "drafts"),
  ];
  for (const dir of candidates) {
    try {
      if (fs.existsSync(dir)) return dir;
    } catch (_) {}
  }
  return candidates[0];
}

function loadDraft(token) {
  const t = safeToken(token);
  if (!t) return null;
  const file = path.join(draftsDir(), t + ".json");
  try {
    const data = JSON.parse(fs.readFileSync(file, "utf8"));
    if (!data || typeof data !== "object") return null;
    return data;
  } catch (_) {
    return null;
  }
}

function paidMarkerPath(token) {
  return path.join(draftsDir(), token + ".paid.json");
}

function readPaidMarker(token) {
  try {
    const data = JSON.parse(fs.readFileSync(paidMarkerPath(token), "utf8"));
    return Boolean(data && data.paid === true);
  } catch (_) {
    return false;
  }
}

function writePaidMarker(token, extra) {
  try {
    const body = Object.assign(
      { paid: true, at: new Date().toISOString() },
      extra || {}
    );
    fs.writeFileSync(paidMarkerPath(token), JSON.stringify(body, null, 2) + "\n");
    return true;
  } catch (_) {
    return false;
  }
}

function computeTier(sentAtIso, nowMs) {
  const sent = Date.parse(sentAtIso);
  if (!Number.isFinite(sent)) return null;
  const now = typeof nowMs === "number" ? nowMs : Date.now();
  const expiresAt = sent + HOURS_48_MS;
  const base = now < expiresAt ? TIERS["48h"] : TIERS.list;
  return Object.assign(
    {
      expires_at: new Date(expiresAt).toISOString(),
      sent_at: new Date(sent).toISOString(),
    },
    base
  );
}

function previewBase(req) {
  const env = (process.env.PREVIEW_BASE_URL || "").trim().replace(/\/$/, "");
  if (env) return env;
  const headers = (req && req.headers) || {};
  const proto = String(headers["x-forwarded-proto"] || "https")
    .split(",")[0]
    .trim();
  const host = String(headers["x-forwarded-host"] || headers.host || "")
    .split(",")[0]
    .trim();
  if (!host) return "";
  return proto + "://" + host;
}

function json(res, status, body) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(body));
}

function redirect(res, location, status) {
  res.statusCode = status || 303;
  res.setHeader("Location", location);
  res.setHeader("Cache-Control", "no-store");
  res.end();
}

module.exports = {
  HOURS_48_MS,
  TIERS,
  safeToken,
  draftsDir,
  loadDraft,
  readPaidMarker,
  writePaidMarker,
  computeTier,
  previewBase,
  json,
  redirect,
};
