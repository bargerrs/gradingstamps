"""GradingStamps static site generator.

Reads  data/products.json  +  assets/stamps/svg/  and writes the whole site
to  docs/  (GitHub Pages serves that folder). Zero dependencies, stdlib only.

    python site/build.py
"""

import html
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SVG_DIR = ROOT / "assets" / "stamps" / "svg"
GIF_DIR = ROOT / "assets" / "stamps"

E = html.escape

# --------------------------------------------------------------- categories
CATEGORIES = {
    "grading": ("grading-rubrics", "Grading & Rubrics",
                "Rubrics, score boxes, and correction stamps that grade in one press."),
    "praise": ("praise-motivation", "Praise & Motivation",
               "Excellent, terrific, great job — the fun ones kids hunt for on their papers."),
    "homework": ("homework-late-work", "Homework & Late Work",
                 "Missing, late, unfinished — documented in a second, no red-pen essay."),
    "parents": ("parent-communication", "Parent Communication",
                "Signature requests and notes home that actually come back signed."),
    "spanish": ("spanish", "Spanish Stamps",
                "En español — the classroom classics for bilingual and Spanish classes."),
    "classroom": ("classroom-fun", "Classroom & Fun",
                  "Book labels, lost teeth, and everything else a classroom celebrates."),
}

RULES = [
    ("spanish", r"spanish|espa|incompleto|entregado|bien hecho|muy bueno|tarea|trabajo no"),
    ("parents", r"parent|please sign|signature"),
    ("homework", r"homework|late|absent|unfinished|no work|make.?up"),
    ("praise", r"excellent|terrific|great job|good work|super|nice work|wiz|speller|"
               r"scientist|don.?t stop|extra credit|dolphin|happy face|very good"),
    ("grading", r"grading|rubric|scored|standards|corrected|correct|incomplete|"
                r"essay needs|paper needs|messy|neater|rethink|complete sentence|"
                r"rough draft|writing process|show your work|pencil|modifications"),
]


def classify(p: dict) -> str:
    text = " ".join([p["name"], " ".join(p["keywords"]), p.get("description") or ""]).lower()
    for key, pat in RULES:
        if re.search(pat, text):
            return key
    return "classroom"


# ----------------------------------------------------------------- helpers
def tidy_size(s: str | None) -> str:
    """'1 1/4 "' -> '1 1/4"' with typographic double-prime."""
    if not s:
        return ""
    return re.sub(r'\s*"', "&Prime;", s.strip())


def frac_to_float(s: str | None) -> float | None:
    if not s:
        return None
    s = s.replace('"', " ").strip()
    m = re.match(r"^(?:(\d+)\s+)?(\d+)/(\d+)$", s) or re.match(r"^(\d+)$", s)
    if not m:
        m2 = re.match(r"^(\d+)\s+(\d+)/(\d+)", s)
        if not m2:
            try:
                return float(s)
            except ValueError:
                return None
        m = m2
    g = m.groups()
    if len(g) == 1:
        return float(g[0])
    whole = float(g[0]) if g[0] else 0.0
    return whole + float(g[1]) / float(g[2])


def price_of(p: dict) -> float:
    if p.get("price_options"):
        return p["price_options"][0]["price"]
    m = re.search(r"[\d.]+", p.get("preink_price") or "")
    return float(m.group(0)) if m else 12.95


def url_slug(p: dict) -> str:
    stem = Path(p["image_file"]).stem            # A171_excellent-dog
    pid, name = stem.split("_", 1)
    return f"{name}-{pid.lower()}"


def img_stem(p: dict) -> str:
    return Path(p["image_file"]).stem


def description_for(p: dict) -> str:
    d = (p.get("description") or "").strip()
    if len(d) > 20:
        return d
    w, h = p.get("width_in"), p.get("height_in")
    size = f"about {tidy_size(w)} × {tidy_size(h)}" if w and h else "classroom sized"
    return (f'The {p["name"]} pre-ink teacher stamp ({size}) marks papers in one press — '
            f"no ink pad, no mess, and roughly {C.IMPRESSIONS} impressions before it "
            f"ever needs re-inking. Made on a modern pre-ink mount, manufactured in "
            f"Austria and assembled in the USA.")


# ----------------------------------------------------------- shared markup
VIEW_CART = (f"https://www.paypal.com/cgi-bin/webscr?cmd=_cart&display=1"
             f"&business={C.PAYPAL_BUSINESS}")


def paypal_form(p: dict, small: bool = False) -> str:
    btn = "btn small" if small else "btn"
    return f"""<form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
<input type="hidden" name="cmd" value="_cart"><input type="hidden" name="add" value="1">
<input type="hidden" name="business" value="{E(C.PAYPAL_BUSINESS)}">
<input type="hidden" name="item_name" value="{E(p['name'])} — pre-ink teacher stamp ({p['id']})">
<input type="hidden" name="item_number" value="{p['id']}">
<input type="hidden" name="amount" value="{price_of(p):.2f}">
<input type="hidden" name="currency_code" value="USD">
<input type="hidden" name="no_note" value="1">
<input type="hidden" name="shopping_url" value="{C.SITE_URL}/shop/">
<input type="hidden" name="return" value="{C.SITE_URL}/thanks/">
<input type="hidden" name="cancel_return" value="{C.SITE_URL}/shop/">
<button type="submit" class="{btn}">Add to cart</button>
</form>"""


def product_card(p: dict, R: str) -> str:
    cat_key = p["_cat"]
    _, cat_title, _ = *CATEGORIES[cat_key][:2], CATEGORIES[cat_key][2]
    w, h = p.get("width_in"), p.get("height_in")
    size = f"{tidy_size(w)} × {tidy_size(h)}" if w and h else ""
    return f"""<div class="pcard">
  <a class="art" href="{R}stamps/{url_slug(p)}/" aria-label="{E(p['name'])}">
    <img src="{R}img/stamps/{img_stem(p)}.svg" alt="{E(p['name'])} rubber stamp impression" loading="lazy" width="220" height="150"></a>
  <div class="info">
    <span class="cat">№ {p['id']} · {E(cat_title)}</span>
    <a class="pname" href="{R}stamps/{url_slug(p)}/">{E(p['name'])}</a>
    <span class="size">{size} · pre-ink mount</span>
    <div class="buyrow"><span class="price">${price_of(p):.2f}</span>{paypal_form(p, small=True)}</div>
  </div>
</div>"""


def shell(*, R: str, title: str, desc: str, canonical: str, body: str,
          active: str = "", extra_head: str = "") -> str:
    nav = []
    for href, label, key in [
        (f"{R}shop/", "Shop", "shop"),
        (f"{R}shop/spanish/", "Spanish", "spanish"),
        (f"{R}custom/", "Custom Stamps", "custom"),
        (f"{R}contact/", "Contact", "contact"),
    ]:
        cur = ' aria-current="page"' if key == active else ""
        nav.append(f'<a href="{href}"{cur}>{label}</a>')
    year = date.today().year
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{C.SITE_NAME}">
<link rel="icon" href="{R}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Alfa+Slab+One&family=Nunito+Sans:wght@400;700;800&family=Special+Elite&display=swap">
<link rel="stylesheet" href="{R}css/style.css">
{extra_head}</head>
<body>
<header class="site"><div class="wrap masthead">
  <a class="logo" href="{R}">GRADING<em>STAMPS</em></a>
  <span class="byline">From {E(C.MAKER)} · 20+ years</span>
  <nav class="main" aria-label="Main">
    {' '.join(nav)}
    <a class="cart" href="{VIEW_CART}">View cart</a>
  </nav>
</div></header>
{body}
<footer class="site"><div class="wrap">
  <div class="cols">
    <div>
      <b>{C.SITE_NAME}.com</b><br>
      {E(C.TAGLINE)}
    </div>
    <div>
      <b>Questions?</b><br>
      <a href="mailto:{C.CONTACT_EMAIL}">{C.CONTACT_EMAIL}</a><br>
      <a href="{C.PHONE_HREF}">{C.PHONE_DISPLAY}</a>
    </div>
    <div>
      <b>Shop</b><br>
      <a href="{R}shop/">All stamps</a><br>
      <a href="{R}custom/">Custom stamps</a>
    </div>
  </div>
  <div class="maker">© {year} {E(C.MAKER)} · Pre-ink stamps for teachers and schools</div>
</div></footer>
</body>
</html>"""


# ------------------------------------------------------------------ build
def main() -> None:
    products = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
    for p in products:
        p["_cat"] = classify(p)

    if DOCS.exists():
        shutil.rmtree(DOCS)
    (DOCS / "css").mkdir(parents=True)
    (DOCS / "img" / "stamps" / "orig").mkdir(parents=True)

    shutil.copy(ROOT / "site" / "style.css", DOCS / "css" / "style.css")
    for svg in SVG_DIR.glob("*.svg"):
        shutil.copy(svg, DOCS / "img" / "stamps" / svg.name)
    for gif in GIF_DIR.glob("*.gif"):
        shutil.copy(gif, DOCS / "img" / "stamps" / "orig" / gif.name)

    (DOCS / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect x="2" y="2" width="60" height="60" rx="12" fill="#C8102E"/>'
        '<text x="32" y="44" font-family="Georgia,serif" font-weight="bold" '
        'font-size="34" fill="#FFF" text-anchor="middle">A+</text></svg>',
        encoding="utf-8")

    if getattr(C, "WRITE_CNAME", True):
        (DOCS / "CNAME").write_text(C.DOMAIN + "\n", encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    urls: list[str] = []

    def write(path: str, content: str) -> None:
        out = DOCS / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")

    def page_url(path: str) -> str:
        rel = path.replace("index.html", "")
        return f"{C.SITE_URL}/{rel}".rstrip("/") + ("/" if rel else "")

    # ---------------- home ----------------
    hero_p = next(p for p in products if p["id"] == "A171")
    featured_ids = ["A171", "A146", "A179", "A120"]
    featured = [p for p in products if p["id"] in featured_ids]
    cat_tiles = []
    for key, (slug, title, blurb) in CATEGORIES.items():
        n = sum(1 for p in products if p["_cat"] == key)
        if n == 0:
            continue
        cat_tiles.append(
            f'<a class="cat-tile" href="shop/{slug}/"><span class="count">{n} stamps</span>'
            f'<b>{E(title)}</b><span>{E(blurb)}</span></a>')
    home_body = f"""
<main>
<div class="wrap hero">
  <div>
    <h1>Stop writing.<br>Stop explaining.<br><em>Start stamping.</em></h1>
    <p class="sub">Pre-ink grading stamps drawn for real classrooms — {C.IMPRESSIONS}
    impressions, no ink pad, no mess. Family-made for teachers for more than 20 years.</p>
    <a class="btn" href="shop/">Shop all {len(products)} stamps</a>
    <div class="trust">
      <span>{C.IMPRESSIONS} impressions</span>
      <span>Austrian-made mounts</span>
      <span>Family business</span>
    </div>
  </div>
  <div class="hero-art">
    <img src="img/stamps/{img_stem(hero_p)}.svg" alt="{E(hero_p['name'])} teacher stamp artwork" width="360" height="315">
  </div>
</div>
<section><div class="wrap">
  <span class="stampchip">Browse by job</span>
  <h2 class="sec">What do you need stamped?</h2>
  <div class="cats">{''.join(cat_tiles)}</div>
</div></section>
<section><div class="wrap">
  <span class="stampchip">Teacher favorites</span>
  <h2 class="sec">The ones kids look for</h2>
  <div class="grid">{''.join(product_card(p, '') for p in featured)}</div>
</div></section>
<section class="story"><div class="wrap" style="padding-top:36px;padding-bottom:36px;">
  <div class="cols">
    <div><h3>A real family business</h3><p>{E(C.FOUNDED_BLURB)}</p></div>
    <div><h3>Pre-ink, not ink pad</h3><p>{E(C.MOUNT_BLURB)}</p></div>
    <div><h3>Can't find it? We'll make it</h3><p>Need wording nobody sells?
      We manufacture custom pre-ink stamps from your design —
      <a href="custom/">tell us what you need</a>.</p></div>
  </div>
</div></section>
</main>"""
    write("index.html", shell(
        R="", title="GradingStamps — Pre-ink Rubber Stamps for Teachers & Schools",
        desc="Pre-ink grading, praise, homework, and parent-signature stamps for teachers. "
             "20,000 impressions, no ink pad. Family-made for 20+ years.",
        canonical=f"{C.SITE_URL}/", body=home_body))
    urls.append(page_url("index.html"))

    # ---------------- shop + category pages ----------------
    def filter_rail(active_slug: str | None, R: str) -> str:
        links = [f'<a href="{R}shop/"{" class=\"on\"" if active_slug is None else ""}>All</a>']
        for key, (slug, title, _) in CATEGORIES.items():
            if not any(p["_cat"] == key for p in products):
                continue
            on = ' class="on"' if slug == active_slug else ""
            links.append(f'<a href="{R}shop/{slug}/"{on}>{E(title)}</a>')
        return f'<div class="filters">{"".join(links)}</div>'

    def shop_page(path: str, R: str, items: list, title: str, desc: str,
                  active_slug: str | None, heading: str, blurb: str, active_nav: str):
        body = f"""
<main><section><div class="wrap">
  <span class="stampchip">{len(items)} stamps</span>
  <h2 class="sec">{E(heading)}</h2>
  <p style="margin-top:-8px;color:var(--ink-soft);">{E(blurb)}</p>
  {filter_rail(active_slug, R)}
  <div class="grid">{''.join(product_card(p, R) for p in items)}</div>
</div></section></main>"""
        write(path, shell(R=R, title=title, desc=desc, canonical=page_url(path),
                          body=body, active=active_nav))
        urls.append(page_url(path))

    shop_page("shop/index.html", "../", products,
              "Teacher Stamp Catalog — All Stamps | GradingStamps",
              "Browse all pre-ink rubber stamps for teachers: grading, praise, homework, "
              "parent signature, and Spanish classroom stamps.",
              None, "The whole catalog", "Every stamp we make, in one place.", "shop")

    for key, (slug, title, blurb) in CATEGORIES.items():
        items = [p for p in products if p["_cat"] == key]
        if not items:
            continue
        shop_page(f"shop/{slug}/index.html", "../../", items,
                  f"{title} Stamps for Teachers | GradingStamps",
                  f"{blurb} Pre-ink mounts, about {C.IMPRESSIONS} impressions each.",
                  slug, title, blurb, "spanish" if key == "spanish" else "shop")

    # ---------------- product pages ----------------
    PPI = 96  # CSS reference pixels per inch for the true-size box
    for p in products:
        R = "../../"
        slug = url_slug(p)
        path = f"stamps/{slug}/index.html"
        w_in = frac_to_float(p.get("width_in"))
        h_in = frac_to_float(p.get("height_in"))
        size_disp = (f'{tidy_size(p["width_in"])} × {tidy_size(p["height_in"])}'
                     if p.get("width_in") and p.get("height_in") else "")
        truesize = ""
        if w_in and h_in:
            truesize = f"""
  <div class="truesize">
    <div class="lbl">Shown at actual size — approx. {size_disp}</div>
    <div class="box"><img src="{R}img/stamps/{img_stem(p)}.svg" alt=""
      style="width:{w_in * PPI:.0f}px;height:{h_in * PPI:.0f}px;object-fit:contain;" ></div>
  </div>"""
        cat_key = p["_cat"]
        cat_slug, cat_title, _ = CATEGORIES[cat_key]
        related = [q for q in products if q["_cat"] == cat_key and q["id"] != p["id"]][:4]
        desc_text = description_for(p)
        jsonld = json.dumps({
            "@context": "https://schema.org",
            "@type": "Product",
            "name": f"{p['name']} — Pre-ink Teacher Stamp",
            "sku": p["id"],
            "image": f"{C.SITE_URL}/img/stamps/orig/{img_stem(p)}.gif",
            "description": re.sub(r"<[^>]+>", "", desc_text),
            "brand": {"@type": "Brand", "name": C.MAKER},
            "offers": {
                "@type": "Offer",
                "url": page_url(path),
                "priceCurrency": "USD",
                "price": f"{price_of(p):.2f}",
                "availability": "https://schema.org/InStock",
            },
        }, ensure_ascii=False)
        body = f"""
<main><div class="wrap">
<div class="product">
  <div>
    <div class="stage"><img src="{R}img/stamps/{img_stem(p)}.svg"
      alt="{E(p['name'])} rubber stamp impression" width="420" height="320"></div>
    {truesize}
  </div>
  <div>
    <span class="stampchip">№ {p['id']}</span>
    <h1>{E(p['name'])}</h1>
    <div class="specline">{size_disp}{' · ' if size_disp else ''}PRE-INK MOUNT · {C.IMPRESSIONS} IMPRESSIONS</div>
    <div class="price">${price_of(p):.2f}</div>
    <p class="desc">{desc_text}</p>
    <div class="buy-panel">
      {paypal_form(p)}
      <a href="{VIEW_CART}">View cart</a> · checkout by PayPal or card
      <ul class="mini-facts">
        <li>No ink pad — clean, even impressions</li>
        <li>About {C.IMPRESSIONS} impressions, re-inkable</li>
        <li>Made in Austria, assembled in the USA</li>
      </ul>
    </div>
    <p style="font-size:13.5px;color:var(--ink-soft);">Category:
      <a href="{R}shop/{cat_slug}/">{E(cat_title)}</a></p>
  </div>
</div>
<section class="related">
  <span class="stampchip">More like this</span>
  <h2 class="sec">Also in {E(cat_title)}</h2>
  <div class="grid">{''.join(product_card(q, R) for q in related)}</div>
</section>
</div></main>"""
        write(path, shell(
            R=R,
            title=f"{p['name']} — Pre-ink Teacher Stamp ({p['id']}) | GradingStamps",
            desc=re.sub(r"<[^>]+>", "", desc_text)[:158],
            canonical=page_url(path), body=body, active="shop",
            extra_head=f'<script type="application/ld+json">{jsonld}</script>\n'))
        urls.append(page_url(path))

    # ---------------- custom ----------------
    custom_body = f"""
<main><div class="wrap page">
  <span class="stampchip">Custom stamps</span>
  <h1>Design a stamp nobody sells</h1>
  <p>Need your name, your wording, or your own artwork on a pre-ink stamp?
  That's been our specialty for two decades — personalized teacher stamps,
  "From the desk of…" stamps, return address stamps, school office stamps.
  Tell us what you want and we'll reply with a proof and a quote, usually
  within a couple of days.</p>
  <form id="customForm">
    <div class="field"><label for="cName">Your name</label>
      <input id="cName" type="text" autocomplete="name"></div>
    <div class="field"><label for="cText">What should the stamp say?</label>
      <textarea id="cText" placeholder="e.g.  From the classroom of Mrs. Rivera — Room 12"></textarea></div>
    <div class="field"><label for="cSize">Rough size</label>
      <select id="cSize">
        <option>Small — about 1½" × ⅝"</option>
        <option selected>Medium — about 2¼" × 1"</option>
        <option>Large — about 2¾" × 2"</option>
        <option>Not sure — recommend one</option>
      </select></div>
    <div class="field"><label for="cNotes">Anything else? (artwork, deadline, quantity)</label>
      <textarea id="cNotes"></textarea></div>
    <button type="submit" class="btn">Compose order email</button>
  </form>
  <div class="notice">The button opens a ready-to-send email to
  <b>{C.CONTACT_EMAIL}</b> — attach artwork to that email if you have any.
  Prefer the phone? Call <a href="{C.PHONE_HREF}">{C.PHONE_DISPLAY}</a>.</div>
</div></main>
<script>
document.getElementById('customForm').addEventListener('submit', function (e) {{
  e.preventDefault();
  var v = function (id) {{ return document.getElementById(id).value; }};
  var body = 'Name: ' + v('cName') + '\\n\\nStamp text:\\n' + v('cText') +
             '\\n\\nSize: ' + v('cSize') + '\\n\\nNotes:\\n' + v('cNotes');
  location.href = 'mailto:{C.CONTACT_EMAIL}' +
    '?subject=' + encodeURIComponent('Custom stamp request') +
    '&body=' + encodeURIComponent(body);
}});
</script>"""
    write("custom/index.html", shell(
        R="../", title="Custom Rubber Stamps — Design Your Own | GradingStamps",
        desc="We manufacture custom pre-ink rubber stamps from your wording or artwork — "
             "personalized teacher stamps, address stamps, and school stamps.",
        canonical=page_url("custom/index.html"), body=custom_body, active="custom"))
    urls.append(page_url("custom/index.html"))

    # ---------------- contact ----------------
    contact_body = f"""
<main><div class="wrap page">
  <span class="stampchip">Contact</span>
  <h1>Talk to a person</h1>
  <p>We're a small family shop, and we answer our own email.</p>
  <p><b>Email:</b> <a href="mailto:{C.CONTACT_EMAIL}">{C.CONTACT_EMAIL}</a><br>
     <b>Phone:</b> <a href="{C.PHONE_HREF}">{C.PHONE_DISPLAY}</a></p>
  <p>Questions about an order, a stamp you can't find, bulk pricing for a school,
  or a custom design — all welcome.</p>
</div></main>"""
    write("contact/index.html", shell(
        R="../", title="Contact Us | GradingStamps",
        desc="Contact MJ's Art Stamps — email or call about teacher stamps, school orders, "
             "and custom pre-ink stamps.",
        canonical=page_url("contact/index.html"), body=contact_body, active="contact"))
    urls.append(page_url("contact/index.html"))

    # ---------------- thanks ----------------
    thanks_body = """
<main><div class="wrap page">
  <span class="stampchip">Order received</span>
  <h1>Thank you!</h1>
  <p>Your order is in — PayPal will email your receipt, and we'll get your
  stamps on their way. If anything looks off, just reply to the receipt or
  <a href="../contact/">contact us</a>.</p>
  <p><a class="btn ghost" href="../shop/">Keep browsing</a></p>
</div></main>"""
    write("thanks/index.html", shell(
        R="../", title="Thank You | GradingStamps",
        desc="Order received — thank you for shopping with GradingStamps.",
        canonical=page_url("thanks/index.html"), body=thanks_body))

    # ---------------- 404 ----------------
    p404 = next(p for p in products if p["id"] == "A103")
    body404 = f"""
<main><div class="wrap page" style="text-align:center;">
  <img src="/img/stamps/{img_stem(p404)}.svg" alt="INCOMPLETE stamp" style="max-width:340px;">
  <h1>This page is incomplete.</h1>
  <p style="margin:0 auto;">The page you're after doesn't exist — it may have moved
  when we rebuilt the site.</p>
  <p><a class="btn" href="/shop/">Browse the catalog</a></p>
</div></main>"""
    write("404.html", shell(
        R="/", title="Page Not Found | GradingStamps",
        desc="Page not found.", canonical=f"{C.SITE_URL}/404.html", body=body404))

    # ---------------- robots + sitemap ----------------
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {C.SITE_URL}/sitemap.xml\n")
    today = date.today().isoformat()
    entries = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          f"{entries}\n</urlset>\n")

    n_pages = len(list(DOCS.rglob("*.html")))
    size_mb = sum(f.stat().st_size for f in DOCS.rglob("*") if f.is_file()) / 1e6
    print(f"built {n_pages} pages, {len(urls)} sitemap URLs, docs/ = {size_mb:.1f} MB")
    if "GradingStamps.com" in C.PAYPAL_BUSINESS:
        print("NOTE: PayPal business email is the unconfirmed placeholder — "
              "confirm with Dad before launch (site/config.py).")


if __name__ == "__main__":
    main()
