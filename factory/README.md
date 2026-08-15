# Lit Locals preview factory (v1.1)

A small factory that turns a prospect JSON into a static preview site.

One layout engine. Six trade packs. Photo fallback. One Python builder.

Magical but dumb. No CMS. No customer accounts. No email. No deploy.
Company: Lit Locals only. Not AISMB Agency. Not a ChatGPT install.

v1.2 surface: rounded cards, glass header, warm gradients, gold button shimmer, headline blur-in. Main sections alternate cream (#f7f3ea) and a light gold wash (#edd9a6). Still one engine / six packs.

v1.1 adds scroll reveal, service cards with trade icons, pack gold-family accents, and a desktop split hero. Sales chrome is a gold preview bar with Buy now, plus a Lit Locals overlay that appears when they hit the bottom. Not a shop section. Each pack now has service what/why copy, a three-step “what happens when you call,” area, and FAQ. Reviews and hours still only render if the prospect JSON has them.
Price and Henry-sends rules are unchanged.

## How to run

From this folder, run builder.py with a prospect JSON (see examples/).

Writes out/SLUG/: index.html, styles.css, motion.js, assets/hero image, assets/mark.svg

Open the generated index.html in a browser. Local preview only.

Stdlib plus urllib only.

## Photo order

1. If prospect.photo_url is a usable http(s) URL, download it. Listing photo. No starter caption.
2. Else use the local job-site hero for that trade (plumber under a sink, tech at the AC, roofers on a house). Starter caption on. Never a random pipe or tool close-up.
3. Else download the pack Unsplash image only if it is a real job scene. Credit the photographer. Starter caption on.

Never generate a fake storefront with their business name on the sign. Never invent a photo of their truck.

## Price

$2,500 regular. $1,500 if they buy within 48 hours after Henry sends this draft.
The builder does not start the 48-hour clock. Placeholder in the bar: 48 hours after we send this.
Henry starts the clock when he sends. Henry takes payment.

Preview host: sales URLs live in /workspace/litlocals/preview-host/.
The factory still does not deploy and does not start the 48-hour clock.
Henry stamps sent_at on the draft JSON when he sends; preview-host reads that.

This factory does not contact anyone and does not send email and does not deploy.

## Reviews

Never invent reviews. If reviews is missing or empty, the page has no quotes. Packs have no fake reviews.

## Prospect JSON

Schema: schema/prospect.schema.json
Example (labeled EXAMPLE, not a real shop): examples/hector-plumbing.json
Required: slug, name, vertical, city, phone.
Optional: hours, service_area, google_url, yelp_url, reviews, photo_url, stripe_url.

Frozen LA hunt cards were too thin for a second example (no review quotes, hours unknown). Do not invent those fields.

## Layout

layout/template.html plus layout/styles.css plus layout/motion.js
Cream page #f7f3ea, dark type, gold buttons, Source Serif + Source Sans, phone-first.
Cousins, not twins: each pack shifts gold a little. Desktop 720px+ splits the hero and the service cards.

## Packs

Six packs: hvac, plumbing, roofing, landscaping, cleaning, electrical.
Each has a local-shop headline (trade line only — the h1 is the name), a lede with city, six services, a gold-family accent, and a real Unsplash image plus photographer credit. No fake reviews in packs.

## Do not

- Do not deploy to production litlocals.com.
- Do not delete parked AISMB files.
- Do not add a CMS or a JS app.
- Do not contact prospects.
- Do not send email.
- Do not start the 48-hour clock from this script.
