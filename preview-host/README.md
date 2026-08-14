# Lit Locals preview host

Sales URLs for shop drafts. Not the public site.

Drafts are static HTML at /p/{token}/. Buy now hits /api/buy?t={token} and opens a Checkout Session in test mode.

The 48-hour clock starts from sent_at in drafts/{token}.json. The factory does not set this. Henry stamps sent_at when he sends. If sent_at is null, Buy refuses with error not_sent.

## Env (names only)

- STRIPE_SECRET_KEY
- STRIPE_WEBHOOK_SECRET
- PREVIEW_BASE_URL

Copy .env.example to .env.local. Do not commit values.

## Local

cd preview-host
npm install
npx vercel dev

Open /p/k7m2x9ingp/. Clock is off until sent_at is set (ISO). After 48h the page stays; Buy is 1250 of 2500. Inside 48h, Buy is 750 of 1500. After paid the bar says: Paid. We are finishing this.

Webhook: POST /api/stripe/webhook. Checkout list is the source of truth for paid.

## Do not

- Do not deploy this to litlocals.com.
- Do not start the clock from build time.
- Do not print secrets.
