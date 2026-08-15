# Lit Locals preview factory (v1.4)

A small factory that turns a prospect JSON into a static preview site.

One layout engine. Six trade packs. Photo fallback. One Python builder.

Magical but dumb. No CMS. No customer accounts. No email. No deploy.
Company: Lit Locals only. Not AISMB Agency. Not a ChatGPT install.

v1.4 Estately-feel surface: Playfair Display (700) + Schibsted Grotesk (400/500/600).
Slate #1e2226 / off-white #f4f2ee / mist #d5dbe0 / forest #2f4538.
Full-bleed centered poster, three tall job cards, dark numbered process, thin shop tag.
Still one engine / six packs. No gold wash, no shimmer, no pills, no icon cards.

v1.3 poster (retired): Fraunces + Schibsted, ink / cream / brass hospitality poster.
v1.2 surface (retired): rounded cards, glass header, warm gradients, gold button shimmer.
v1.1 added scroll reveal and pack service copy. Reviews and hours still only render if the prospect JSON has them.

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
Caption when not a listing photo: "Starter photo — not their crew."

## Price

$2,500 regular. $1,500 if they buy the draft within 48 hours after Henry sends.
Deposit $750. 72 hours after the deposit they can cancel and get the $750 back; after that the deposit is earned. Not a $1,500 cash refund.
Contact: hello@litlocals.com only.

The builder does not start the 48-hour clock. Henry starts the clock when he sends. Henry takes payment.

Preview host: sales URLs live in /workspace/litlocals/preview-host/.
The factory still does not deploy and does not start the 48-hour clock.
Henry stamps sent_at on the draft JSON when he sends; preview-host reads that.

This factory does not contact anyone and does not send email and does not deploy.

## Reviews

Never invent reviews. If reviews is missing or empty, the page has no quotes. Packs have no fake reviews. Max two quotes when present.

## Prospect JSON

Schema: schema/prospect.schema.json
Example (labeled EXAMPLE, not a real shop): examples/hector-plumbing.json
Required: slug, name, vertical, city, phone.
Optional: hours, service_area, google_url, yelp_url, reviews, photo_url, stripe_url.

Frozen LA hunt cards were too thin for a second example (no review quotes, hours unknown). Do not invent those fields.

## Layout

layout/template.html plus layout/styles.css plus layout/motion.js
Off-white page #f4f2ee, slate type #1e2226, forest #2f4538 on buttons and rules only.
Display: Playfair Display 700. Grotesque: Schibsted Grotesk 400/500/600.
Phone-first. Desktop keeps the same full-bleed poster — no two-column hero.

Sections: poster, intro, three job cards, reviews (if any), process, matchbook (hours only if present), three FAQs, listings (if URLs exist), close band.
Thin shop tag: "Draft · $1,500 — $750 now" + Buy. Hamburger on phone; horizontal nav from 720px.

## Packs

Six packs: hvac, plumbing, roofing, landscaping, cleaning, electrical.
Each has a poster_line with {city}, six services (first three render as jobs), and a real Unsplash image plus photographer credit. No fake reviews in packs.

## Do not

- Do not deploy to production litlocals.com.
- Do not delete parked AISMB files.
- Do not add a CMS or a JS app.
- Do not contact prospects.
- Do not send email.
- Do not start the 48-hour clock from this script.
