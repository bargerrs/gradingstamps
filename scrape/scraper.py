"""Scrape gradingstamps.com: pages, product data, and all images.

Output layout (relative to project root):
  scrape/raw/pages/      - HTML snapshots of every site page
  scrape/raw/moreinfo/   - HTML snapshots of every product detail popup
  assets/stamps/         - product art, renamed  <ID>_<slug>.gif
  assets/site/           - logos, buttons, chrome images, stylesheet
  data/products.json     - structured product database
"""

import html
import json
import re
import time
import urllib.request
from pathlib import Path

BASE = "http://www.gradingstamps.com/"
ROOT = Path(__file__).resolve().parent.parent
RAW_PAGES = ROOT / "scrape" / "raw" / "pages"
RAW_INFO = ROOT / "scrape" / "raw" / "moreinfo"
ASSETS_STAMPS = ROOT / "assets" / "stamps"
ASSETS_SITE = ROOT / "assets" / "site"
DATA = ROOT / "data"
for d in (RAW_PAGES, RAW_INFO, ASSETS_STAMPS, ASSETS_SITE, DATA):
    d.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (site-migration scraper; owner-authorized)"}
DELAY = 0.25


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    time.sleep(DELAY)
    return data


def fetch_text(url: str) -> str:
    return fetch(url).decode("utf-8", errors="replace")


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "stamp"


# ---------------------------------------------------------------- site pages
SITE_PAGES = {
    "home": "Default.aspx",
    "catalog_teacher_p1": "Catalog.aspx?category=Teacher&firstStamp=0",
    "catalog_teacher_p2": "Catalog.aspx?category=Teacher&firstStamp=10",
    "catalog_teacher_p3": "Catalog.aspx?category=Teacher&firstStamp=20",
    "catalog_teacher_p4": "Catalog.aspx?category=Teacher&firstStamp=30",
    "catalog_teacher_p5": "Catalog.aspx?category=Teacher&firstStamp=40",
    "catalog_spanish": "Catalog.aspx?category=Spanish&firstStamp=0",
    "catalog_view_all": "Catalog.aspx?firstStamp=57",
    "custom_generator": "CustomGenerator.aspx",
    "custom_return_address": "CustomReturnAddressStamps.aspx",
    "custom_tutorial": "CustomStampTutorial.aspx",
    "contact": "ContactUs.aspx",
}

pages: dict[str, str] = {}
for name, path in SITE_PAGES.items():
    try:
        pages[name] = fetch_text(BASE + path)
        (RAW_PAGES / f"{name}.html").write_text(pages[name], encoding="utf-8")
        print(f"page  {name}: {len(pages[name])} bytes")
    except Exception as e:
        print(f"page  {name}: FAILED {e}")

# stylesheet
try:
    css = fetch(BASE + "Stylesheet.css")
    (ASSETS_SITE / "Stylesheet.css").write_bytes(css)
    print(f"css   Stylesheet.css: {len(css)} bytes")
except Exception as e:
    print(f"css   FAILED {e}")

# ------------------------------------------------------------ parse products
BLOCK_RE = re.compile(
    r'<div style="display: block; width: 425px;.*?</table>', re.S
)
NAME_RE = re.compile(r'spanStamp1Name">(.*?)</span>', re.S)
ID_RE = re.compile(r'spanStampId">(.*?)</span>', re.S)
IMG_RE = re.compile(r'imgStamp1"\s+src="([^"]+)"(?:\s+height="(\d+)")?(?:\s+width="(\d+)")?')
KEYWORDS_RE = re.compile(r'spanStamp1Keywords">(.*?)</span>', re.S)
PRICE_RE = re.compile(r'value="([\d.]+)"[^>]*/><label[^>]*>(.*?)</label>', re.S)

products: dict[str, dict] = {}

def parse_catalog(html_text: str, category: str):
    for block in BLOCK_RE.findall(html_text):
        m_id = ID_RE.search(block)
        if not m_id:
            continue
        pid = clean(m_id.group(1))
        m_img = IMG_RE.search(block)
        entry = products.setdefault(pid, {
            "id": pid,
            "name": clean(NAME_RE.search(block).group(1)) if NAME_RE.search(block) else "",
            "image_url": None,
            "image_width": None,
            "image_height": None,
            "keywords": [],
            "price_options": [],
            "categories": [],
        })
        if category not in entry["categories"]:
            entry["categories"].append(category)
        if m_img:
            entry["image_url"] = m_img.group(1)
            entry["image_height"] = int(m_img.group(2)) if m_img.group(2) else None
            entry["image_width"] = int(m_img.group(3)) if m_img.group(3) else None
        m_kw = KEYWORDS_RE.search(block)
        if m_kw:
            entry["keywords"] = [clean(k) for k in clean(m_kw.group(1)).split("&") if clean(k)]
        opts = [{"price": float(v), "label": clean(lbl)} for v, lbl in PRICE_RE.findall(block)]
        if opts:
            entry["price_options"] = opts

for name, text in pages.items():
    if name.startswith("catalog_teacher"):
        parse_catalog(text, "Teacher")
    elif name == "catalog_spanish":
        parse_catalog(text, "Spanish")
    elif name == "catalog_view_all":
        parse_catalog(text, "All")

print(f"\nparsed {len(products)} unique products")

# ----------------------------------------------------------- product details
H_RE = re.compile(r'id="stampHeightCell"[^>]*>(.*?)</td>', re.S)
W_RE = re.compile(r'id="stampWidthCell"[^>]*>(.*?)</td>', re.S)
WOOD_RE = re.compile(r'<div id="stamp0Price">\s*(.*?)\s*</div>', re.S)
PREINK_RE = re.compile(r'id="stamp0PricePreink">(.*?)</div>', re.S)
DESC_RE = re.compile(r'id="pStampDesc"[^>]*>(.*?)</p>', re.S)

for pid, entry in products.items():
    try:
        text = fetch_text(f"{BASE}MoreInfo.aspx?stampID={pid}")
        (RAW_INFO / f"{pid}.html").write_text(text, encoding="utf-8")
        m = H_RE.search(text)
        entry["height_in"] = clean(m.group(1)) if m else None
        m = W_RE.search(text)
        entry["width_in"] = clean(m.group(1)) if m else None
        m = WOOD_RE.search(text)
        entry["wood_mount_price"] = clean(m.group(1)) if m else None
        m = PREINK_RE.search(text)
        entry["preink_price"] = clean(m.group(1)) if m else None
        m = DESC_RE.search(text)
        entry["description"] = clean(m.group(1)) if m else None
        print(f"info  {pid}: {entry['name']}")
    except Exception as e:
        print(f"info  {pid}: FAILED {e}")

# --------------------------------------------------------------- images
def download(url_path: str, dest: Path) -> bool:
    if dest.exists():
        return True
    try:
        dest.write_bytes(fetch(BASE + url_path.lstrip("/")))
        print(f"img   {url_path} -> {dest.name}")
        return True
    except Exception as e:
        print(f"img   {url_path}: FAILED {e}")
        return False

# product art: renamed <ID>_<slug>.<ext>
for pid, entry in sorted(products.items()):
    src = entry.get("image_url")
    if not src:
        entry["image_file"] = None
        continue
    ext = Path(src).suffix or ".gif"
    fname = f"{pid}_{slugify(entry['name'])}{ext}"
    if download(src, ASSETS_STAMPS / fname):
        entry["image_file"] = f"assets/stamps/{fname}"
        entry["image_original_name"] = Path(src).name
    else:
        entry["image_file"] = None

# site chrome: every images/... reference in any fetched page
site_imgs: set[str] = set()
for text in pages.values():
    site_imgs.update(re.findall(r'(?:src|href)="((?:images|Images)/[^"]+)"', text))
    # also url(...) references in inline styles
    site_imgs.update(re.findall(r"url\(((?:images|Images)/[^)]+)\)", text))
for info_file in RAW_INFO.glob("*.html"):
    t = info_file.read_text(encoding="utf-8")
    site_imgs.update(re.findall(r'(?:src|href)="((?:images|Images)/[^"]+)"', t))
    site_imgs.update(re.findall(r"url\(((?:images|Images)/[^)]+)\)", t))
# and any referenced by the stylesheet
try:
    css_text = (ASSETS_SITE / "Stylesheet.css").read_text(encoding="utf-8", errors="replace")
    site_imgs.update(m.strip("'\" ") for m in re.findall(r"url\(([^)]+)\)", css_text))
except Exception:
    pass

for ref in sorted(site_imgs):
    ref = ref.strip("'\" ").lstrip("./")
    if ref.startswith("http"):
        continue
    download(ref, ASSETS_SITE / Path(ref).name)

# --------------------------------------------------------------- save data
catalog = sorted(products.values(), key=lambda p: p["id"])
(DATA / "products.json").write_text(
    json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(f"\nwrote data/products.json with {len(catalog)} products")
