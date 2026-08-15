#!/usr/bin/env python3
"""Lit Locals preview factory.

Turn a prospect JSON into a static draft site. Magical but dumb.
No CMS. No customer accounts. No email. No deploy.

Usage:
    python3 builder.py examples/hector-plumbing.json

Writes out/{slug}/index.html, styles.css, motion.js, assets/hero.*, assets/mark.svg

The 48-hour $1,500 clock is NOT started here. The preview bar uses a
placeholder. Henry starts the clock when he sends.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import urllib.error
import urllib.request
from html import escape
from urllib.parse import quote
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAYOUT = ROOT / "layout"
PACKS = ROOT / "packs"
OUT = ROOT / "out"
PRODUCT_MARK = Path("/workspace/litlocals/product-site/assets/mark.svg")
LOCAL_MARK = ROOT / "assets" / "mark.svg"

UA = "LitLocalsPreviewFactory/1.0 (+https://litlocals.com; draft builder, not a crawler)"
VERTICALS = ("hvac", "plumbing", "roofing", "landscaping", "cleaning", "electrical")
EXPIRY_PLACEHOLDER = "48 hours after we send this"
STARTER_CAPTION = "Starter photo — not their crew."
MAX_REVIEWS = 2
DOWNLOAD_TIMEOUT = 30


# ---------------------------------------------------------------------------
# Service icons — one 24x24 stroke SVG per trade, currentColor. Same icon
# for all six services of that trade.
# ---------------------------------------------------------------------------


def _icon(inner: str) -> str:
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        f"{inner}</svg>"
    )


TRADE_ICONS: dict[str, str] = {
    "plumbing": _icon(
        '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'
    ),
    "hvac": _icon(
        '<circle cx="12" cy="12" r="2.2"/>'
        '<path d="M12 3c2.4 2 2.6 5.2.4 6.4C10 8.2 9.6 5 12 3z'
        'M21 12c-2 2.4-5.2 2.6-6.4.4C15.8 10 19 9.6 21 12z'
        'M12 21c-2.4-2-2.6-5.2-.4-6.4C14 15.8 14.4 19 12 21z'
        'M3 12c2-2.4 5.2-2.6 6.4-.4C8.2 14 5 14.4 3 12z"/>'
    ),
    "roofing": _icon(
        '<path d="M3 12 12 4l9 8"/><path d="M5 10.5V20h14v-9.5"/>'
    ),
    "landscaping": _icon(
        '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>'
        '<path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>'
    ),
    "cleaning": _icon(
        '<path d="M12 2l1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5L12 2z"/>'
    ),
    "electrical": _icon(
        '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z"/>'
    ),
}


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------


def die(msg: str, code: int = 1) -> None:
    print(f"builder: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        die(f"not found: {path}")
    except json.JSONDecodeError as err:
        die(f"bad JSON in {path}: {err}")
    if not isinstance(data, dict):
        die(f"{path} must be a JSON object")
    return data


def load_pack(vertical: str) -> dict:
    path = PACKS / f"{vertical}.json"
    if not path.exists():
        die(f"no trade pack for vertical {vertical!r} ({path})")
    pack = load_json(path)
    if pack.get("id") != vertical:
        die(f"pack id mismatch in {path}")
    return pack


def fill_words(template: str, prospect: dict) -> str:
    return (template or "").replace("{name}", prospect["name"]).replace("{city}", prospect["city"])


def city_short(prospect: dict) -> str:
    city = str(prospect.get("city") or "").strip()
    return city.split(",")[0].strip() or city


def poster_line(pack: dict, prospect: dict) -> str:
    raw = pack.get("poster_line") or pack.get("headline_template") or ""
    return (
        str(raw)
        .replace("{city}", city_short(prospect))
        .replace("{name}", str(prospect.get("name") or "").strip())
        .replace("{phone}", str(prospect.get("phone") or "").strip())
    )


def trade_headline(pack: dict, prospect: dict) -> str:
    """Trade line only. h1 is already the shop name — do not repeat it."""
    raw = fill_words(pack.get("headline_template") or "", prospect).strip()
    name = (prospect.get("name") or "").strip()
    if name and raw.lower().startswith(name.lower()):
        raw = raw[len(name):].lstrip(" \t,.—–-")
        if raw:
            raw = raw[0].upper() + raw[1:]
    return raw


def is_http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip().lower()
    return v.startswith("http://") or v.startswith("https://")


def slug_ok(slug: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug or ""))


def tel_href(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if not digits:
        die("phone has no digits")
    if len(digits) == 10:
        return f"tel:+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"tel:+{digits}"
    if phone.strip().startswith("+"):
        plus = re.sub(r"[^\d+]", "", phone)
        return f"tel:{plus}"
    return f"tel:{digits}"


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------


def _ext_from_bytes(data: bytes, content_type: str) -> str:
    head = data[:16]
    ctype = (content_type or "").split(";")[0].strip().lower()
    if head.startswith(b"\xff\xd8\xff") or ctype in ("image/jpeg", "image/jpg"):
        return ".jpg"
    if head.startswith(b"RIFF") and b"WEBP" in head[:16] or ctype == "image/webp":
        return ".webp"
    if head.startswith(b"\x89PNG") or ctype == "image/png":
        return ".png"
    if head.startswith(b"GIF8") or ctype == "image/gif":
        return ".gif"
    return ".jpg"


def download_image(url: str, dest_dir: Path) -> Path | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/*,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "")
    except (urllib.error.URLError, TimeoutError, ValueError) as err:
        print(f"builder: photo download failed ({url}): {err}", file=sys.stderr)
        return None
    if len(data) < 32:
        print(f"builder: photo too small ({url})", file=sys.stderr)
        return None
    ext = _ext_from_bytes(data, ctype)
    dest = dest_dir / f"hero{ext}"
    dest.write_bytes(data)
    print(f"builder: saved {dest.name} ({len(data)} bytes) from {url.split('?')[0]}")
    return dest


def copy_local_hero(vertical: str, dest_dir: Path) -> Path | None:
    heroes = PACKS / "heroes"
    for ext in (".jpg", ".jpeg", ".webp", ".png"):
        src = heroes / f"{vertical}{ext}"
        if src.exists():
            dest = dest_dir / f"hero{src.suffix.lower().replace('.jpeg', '.jpg')}"
            shutil.copy2(src, dest)
            print(f"builder: copied local job-site hero {src.name}")
            return dest
    return None


def resolve_hero(prospect: dict, pack: dict, assets: Path) -> dict | None:
    """Listing photo, else local job-site hero, else Unsplash. Never a random object close-up."""
    photo_url = (prospect.get("photo_url") or "").strip()
    if is_http_url(photo_url):
        path = download_image(photo_url, assets)
        if path:
            return {"file": path.name, "kind": "listing"}
        print("builder: listing photo_url failed; trying local job-site hero", file=sys.stderr)

    path = copy_local_hero(pack["id"], assets)
    if path:
        return {"file": path.name, "kind": "ai"}

    unsplash = pack.get("unsplash") or {}
    image_url = (unsplash.get("image_url") or "").strip()
    if is_http_url(image_url):
        path = download_image(image_url, assets)
        if path:
            return {
                "file": path.name,
                "kind": "unsplash",
                "photographer": unsplash.get("photographer") or "",
                "unsplash_page": unsplash.get("unsplash_page") or "",
            }

    print("builder: no hero image (listing, local job-site, and Unsplash all missed)", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# HTML fragments
# ---------------------------------------------------------------------------


def hero_block(hero: dict | None) -> str:
    if not hero:
        return ""
    src = escape(f"assets/{hero['file']}", quote=True)
    if hero["kind"] == "listing":
        alt = "Shop photo"
        caption = ""
    else:
        alt = escape(STARTER_CAPTION, quote=True)
        caption = f'      <p class="hero-caption">{escape(STARTER_CAPTION)}</p>\n'
    return (
        f'      <figure class="hero-photo">\n'
        f'        <img src="{src}" alt="{alt}" width="1600" height="900">\n'
        f"{caption}"
        f"      </figure>\n"
    )


def facts_rows(prospect: dict) -> str:
    rows = []
    mapping = [
        ("Phone", prospect.get("phone")),
        ("Hours", prospect.get("hours")),
        ("Service area", prospect.get("service_area")),
        ("City", prospect.get("city")),
    ]
    for label, value in mapping:
        if not value or not str(value).strip():
            continue
        rows.append(
            "          <div>\n"
            f"            <dt>{escape(label)}</dt>\n"
            f"            <dd>{escape(str(value).strip())}</dd>\n"
            "          </div>"
        )
    return "\n".join(rows)


def reviews_block(prospect: dict) -> str:
    """Only quotes present in JSON. Never invent. Max two."""
    raw = prospect.get("reviews")
    if not raw or not isinstance(raw, list):
        return ""
    items = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        quote = (entry.get("quote") or "").strip()
        if not quote:
            continue
        items.append(f'      <p class="said">“{escape(quote)}”</p>')
        if len(items) >= MAX_REVIEWS:
            break
    if not items:
        return ""
    inner = "\n".join(items)
    return (
        '    <section class="reviews reveal">\n'
        f"{inner}\n"
        "    </section>\n"
    )


def listings_block(prospect: dict) -> str:
    links = []
    google = (prospect.get("google_url") or "").strip()
    yelp = (prospect.get("yelp_url") or "").strip()
    if is_http_url(google):
        links.append(
            f'          <li><a href="{escape(google, quote=True)}" rel="nofollow noopener">Google listing</a></li>'
        )
    if is_http_url(yelp):
        links.append(
            f'          <li><a href="{escape(yelp, quote=True)}" rel="nofollow noopener">Yelp listing</a></li>'
        )
    if not links:
        return ""
    inner = "\n".join(links)
    return (
        '    <section class="section listings reveal" id="listings" aria-labelledby="listings-title">\n'
        '      <div class="wrap">\n'
        '        <h2 id="listings-title">Find them</h2>\n'
        f'        <ul class="listings">\n{inner}\n        </ul>\n'
        "      </div>\n"
        "    </section>\n"
    )


def svc_name(svc) -> str:
    if isinstance(svc, dict):
        return str(svc.get("name") or "").strip()
    return str(svc).strip()


def services_items(pack: dict) -> str:
    icon = TRADE_ICONS.get(pack.get("id") or "", "")
    items = []
    for svc in pack.get("services") or []:
        label = svc_name(svc)
        if not label:
            continue
        sid = slugify(label)
        items.append(
            f'          <li class="svc">'
            f'<a href="#svc-{escape(sid, quote=True)}">'
            f'<span class="svc-icon" aria-hidden="true">{icon}</span>'
            f"<span>{escape(label)}</span></a></li>"
        )
    return "\n".join(items)



def intro_block(pack: dict, prospect: dict) -> str:
    """Short about band. Pack eyebrow + filled lede only. No invented years or crew."""
    eyebrow = str(pack.get("eyebrow") or pack.get("label") or "").strip()
    lede = fill_words(pack.get("lede_template") or "", prospect).strip()
    if not eyebrow and not lede:
        return ""
    heading = f"{eyebrow}, done in the open." if eyebrow else ""
    left = []
    if eyebrow:
        left.append(f'        <p class="eyebrow">{escape(eyebrow)}</p>')
    if heading:
        left.append(f"        <h2>{escape(heading)}</h2>")
    right = f"        <p>{escape(lede)}</p>" if lede else ""
    return (
        '    <section class="intro reveal" id="about">\n'
        '      <div class="intro-col">\n'
        + "\n".join(left)
        + "\n      </div>\n"
        '      <div class="intro-col">\n'
        + (right + "\n" if right else "")
        + "      </div>\n"
        "    </section>\n"
    )


def jobs_block(pack: dict) -> str:
    """First three services only. No icons. No svc-* links. No photos."""
    items = []
    for svc in pack.get("services") or []:
        if not isinstance(svc, dict):
            continue
        name = str(svc.get("name") or "").strip()
        what = str(svc.get("what") or "").strip()
        if not name:
            continue
        items.append(
            '        <li class="job-card">\n'
            f"          <h3>{escape(name)}</h3>\n"
            f"          <p>{escape(what)}</p>\n"
            "        </li>"
        )
        if len(items) >= 3:
            break
    if not items:
        return ""
    inner = "\n".join(items)
    return (
        '    <section class="jobs section reveal" id="jobs">\n'
        "      <h2>What they handle</h2>\n"
        f'      <ul class="job-cards">\n{inner}\n      </ul>\n'
        "    </section>\n"
    )


def matchbook_block(prospect: dict) -> str:
    """Name, city, hours only if present, phone as tel. No invented hours."""
    name = str(prospect.get("name") or "").strip()
    city = str(prospect.get("city") or "").strip()
    hours = str(prospect.get("hours") or "").strip()
    phone = str(prospect.get("phone") or "").strip()
    parts = []
    if name:
        parts.append(f'      <p class="shop-name">{escape(name)}</p>')
    if city:
        parts.append(f'      <p class="mb-city">{escape(city)}</p>')
    if hours:
        parts.append(f'      <p class="mb-hours">{escape(hours)}</p>')
    if phone:
        tel = escape(tel_href(phone), quote=True)
        parts.append(f'      <p class="mb-phone"><a href="{tel}">{escape(phone)}</a></p>')
    if not parts:
        return ""
    return (
        '    <section class="matchbook reveal" id="hours">\n'
        + "\n".join(parts)
        + "\n    </section>\n"
    )


def service_details(pack: dict, prospect: dict) -> str:
    phone = str(prospect.get("phone") or "").strip()
    tel = escape(tel_href(phone), quote=True) if phone else ""
    phone_l = escape(phone)
    blocks = []
    for i, svc in enumerate(pack.get("services") or []):
        if not isinstance(svc, dict):
            continue
        name = str(svc.get("name") or "").strip()
        what = str(svc.get("what") or "").strip()
        benefit = str(svc.get("benefit") or "").strip()
        if not name or not (what or benefit):
            continue
        sid = slugify(name)
        alt = ""
        call = ""
        if tel:
            call = (
                f'        <p class="tap-note"><a href="{tel}">Call {phone_l} about {escape(name)}</a></p>\n'
            )
        blocks.append(
            f'    <section class="section reveal" id="svc-{escape(sid, quote=True)}" aria-labelledby="svc-{escape(sid, quote=True)}-title">\n'
            f'      <div class="wrap">\n'
            f'        <p class="eyebrow">Service</p>\n'
            f'        <h2 id="svc-{escape(sid, quote=True)}-title">{escape(name)}</h2>\n'
            + (f'        <p class="svc-what">{escape(what)}</p>\n' if what else "")
            + (f'        <p class="svc-why"><strong>Why it matters.</strong> {escape(benefit)}</p>\n' if benefit else "")
            + call
            + "      </div>\n"
            "    </section>\n"
        )
    if not blocks:
        return ""
    return '    <div class="band-warm">\n' + "\n".join(blocks) + "    </div>\n"


def fill_city_phone(text: str, prospect: dict) -> str:
    return (
        (text or "")
        .replace("{city}", str(prospect.get("city") or "").strip())
        .replace("{phone}", str(prospect.get("phone") or "").strip())
        .replace("{name}", str(prospect.get("name") or "").strip())
    )


def process_block(pack: dict, prospect: dict) -> str:
    steps = pack.get("process") or []
    if not steps:
        return ""
    lis = []
    for i, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            continue
        title = fill_city_phone(str(step.get("title") or ""), prospect)
        body = fill_city_phone(str(step.get("body") or ""), prospect)
        if not title:
            continue
        hot = ' class="is-hot"' if not lis else ""
        lis.append(
            f"          <li{hot}>\n"
            f'            <span class="step-n">{i}</span>\n'
            f"            <div>\n"
            f"              <h3>{escape(title)}</h3>\n"
            f"              <p>{escape(body)}</p>\n"
            "            </div>\n"
            "          </li>"
        )
    if not lis:
        return ""
    return (
        '    <section class="process reveal" id="expect" aria-labelledby="expect-title">\n'
        '      <h2 id="expect-title">What happens when you call</h2>\n'
        f'      <ol class="steps">\n' + "\n".join(lis) + "\n      </ol>\n"
        "    </section>\n"
    )


def faq_block(pack: dict, prospect: dict) -> str:
    faqs = pack.get("faqs") or []
    if not faqs:
        return ""
    items = []
    for faq in faqs:
        if not isinstance(faq, dict):
            continue
        q = fill_city_phone(str(faq.get("q") or ""), prospect)
        a = fill_city_phone(str(faq.get("a") or ""), prospect)
        if not q or not a:
            continue
        items.append(
            "      <div class=\"faq\">\n"
            f"        <h3>{escape(q)}</h3>\n"
            f"        <p>{escape(a)}</p>\n"
            "      </div>"
        )
        if len(items) >= 3:
            break
    if not items:
        return ""
    return (
        '    <section class="faq-list reveal" id="faq">\n'
        "      <h2>Before you call</h2>\n"
        + "\n".join(items)
        + "\n    </section>\n"
    )


def area_block(prospect: dict) -> str:
    city = str(prospect.get("city") or "").strip()
    area = str(prospect.get("service_area") or "").strip() or city
    phone = str(prospect.get("phone") or "").strip()
    if not area:
        return ""
    tel = escape(tel_href(phone), quote=True) if phone else ""
    call = f'        <p class="tap-note"><a href="{tel}">Tap to call {escape(phone)}</a></p>\n' if tel else ""
    return (
        '    <section class="section reveal" id="area" aria-labelledby="area-title">\n'
        '      <div class="wrap">\n'
        '        <h2 id="area-title">Are they near you?</h2>\n'
        f'        <p class="lede">Listed in {escape(area)}. If that sounds like your neighborhood, call and ask if they cover your street.</p>\n'
        + call
        + "      </div>\n"
        "    </section>\n"
    )


def close_band(prospect: dict) -> str:
    """Last dark band. Real shop phone only. No invented help line."""
    phone = str(prospect.get("phone") or "").strip()
    if not phone:
        return ""
    tel = escape(tel_href(phone), quote=True)
    return (
        '    <section class="close-band reveal" aria-label="Call the shop">\n'
        '      <p class="close-line">Call them. The number rings the shop.</p>\n'
        f'      <a class="btn btn-call" href="{tel}">Call {escape(phone)}</a>\n'
        "    </section>\n"
    )


def call_band(prospect: dict) -> str:
    phone = str(prospect.get("phone") or "").strip()
    if not phone:
        return ""
    tel = escape(tel_href(phone), quote=True)
    return (
        '    <section class="call-band reveal" id="reach" aria-label="Call the shop">\n'
        '      <div class="wrap">\n'
        '        <p>The number on this page rings the shop. That’s how you know it isn’t a mockup.</p>\n'
        f'        <a class="btn btn-gold btn-lg" href="{tel}">Call {escape(phone)}</a>\n'
        "      </div>\n"
        "    </section>\n"
    )


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "service"


def unsplash_credit(hero: dict | None) -> str:
    if not hero or hero.get("kind") != "unsplash":
        return ""
    name = (hero.get("photographer") or "").strip()
    page = (hero.get("unsplash_page") or "").strip()
    if not name:
        return ""
    if is_http_url(page):
        return (
            f'      <p class="footer-note">Photo by {escape(name)} on '
            f'<a href="{escape(page, quote=True)}" rel="nofollow noopener">Unsplash</a>.</p>\n'
        )
    return f'      <p class="footer-note">Photo by {escape(name)} on Unsplash.</p>\n'


def apply_template(template: str, mapping: dict[str, str]) -> str:
    out = template
    for key, value in mapping.items():
        out = out.replace("{{" + key + "}}", value)
    leftover = re.findall(r"\{\{[a-z0-9_]+\}\}", out)
    if leftover:
        die(f"unfilled template placeholders: {', '.join(leftover)}")
    return out


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def validate_prospect(p: dict) -> None:
    for field in ("slug", "name", "vertical", "city", "phone"):
        if not str(p.get(field) or "").strip():
            die(f"missing required field: {field}")
    if not slug_ok(p["slug"]):
        die("slug must be lowercase letters, numbers, and hyphens")
    if p["vertical"] not in VERTICALS:
        die(f"vertical must be one of: {', '.join(VERTICALS)}")



def ask_href(prospect: dict) -> str:
    name = str(prospect.get("name") or "this shop")
    city = str(prospect.get("city") or "").strip()
    preview = str(prospect.get("preview_url") or "").strip()
    subject = f"Question about {name} draft"
    lines = [f"Shop: {name}"]
    if city:
        lines.append(f"City: {city}")
    lines.append(f"Preview: {preview}" if preview else "Preview: (the page I opened)")
    lines.append("")
    lines.append("My question:")
    lines.append("")
    return (
        "mailto:hello@litlocals.com?subject="
        + quote(subject)
        + "&body="
        + quote("\n".join(lines))
    )


def copy_mark(assets: Path) -> None:
    src = PRODUCT_MARK if PRODUCT_MARK.exists() else LOCAL_MARK
    if not src.exists():
        die(f"mark.svg not found at {PRODUCT_MARK} or {LOCAL_MARK}")
    shutil.copy2(src, assets / "mark.svg")


def build(prospect_path: Path) -> Path:
    prospect = load_json(prospect_path)
    validate_prospect(prospect)
    pack = load_pack(prospect["vertical"])

    dest = OUT / prospect["slug"]
    assets = dest / "assets"
    if dest.exists():
        shutil.rmtree(dest)
    assets.mkdir(parents=True)

    hero = resolve_hero(prospect, pack, assets)
    copy_mark(assets)
    shutil.copy2(LAYOUT / "styles.css", dest / "styles.css")
    shutil.copy2(LAYOUT / "motion.js", dest / "motion.js")

    buy = (prospect.get("stripe_url") or "").strip()
    buy_href = buy if is_http_url(buy) else "#buy"

    phone = prospect["phone"].strip()
    mapping = {
        "name": escape(prospect["name"]),
        "city": escape(prospect["city"]),
        "phone": escape(phone),
        "phone_tel": escape(tel_href(phone), quote=True),
        "trade": escape(pack["id"]),
        "poster_line": escape(poster_line(pack, prospect)),
        "buy_href": escape(buy_href, quote=True),
        "ask_href": escape(ask_href(prospect), quote=True),
        "hero_block": hero_block(hero),
        "intro_block": intro_block(pack, prospect),
        "jobs_block": jobs_block(pack),
        "reviews_block": reviews_block(prospect),
        "process_block": process_block(pack, prospect),
        "matchbook_block": matchbook_block(prospect),
        "faq_block": faq_block(pack, prospect),
        "listings_block": listings_block(prospect),
        "close_band": close_band(prospect),
        "unsplash_credit": unsplash_credit(hero),
    }

    template = (LAYOUT / "template.html").read_text(encoding="utf-8")
    html = apply_template(template, mapping)
    html = re.sub(r"\n{3,}", "\n\n", html)
    index = dest / "index.html"
    index.write_text(html, encoding="utf-8")
    print(f"builder: wrote {index}")
    return dest


def main(argv: list[str]) -> None:
    if len(argv) != 2 or argv[1] in ("-h", "--help"):
        print("Usage: python3 builder.py examples/hector-plumbing.json")
        print("Writes a static draft to out/{slug}/. Does not send email. Does not deploy.")
        raise SystemExit(0 if len(argv) != 2 else 2)
    path = Path(argv[1])
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    dest = build(path)
    print(f"builder: done → {dest}")
    print("builder: 48h clock not started. Henry starts it when he sends.")


if __name__ == "__main__":
    main(sys.argv)
