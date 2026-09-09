# GradingStamps.com — Scrape Report

Scraped 2026-08-27 from `http://www.gradingstamps.com` (MJ's Art Stamps / Teacher's Rubber Stamps).

## Folder layout

```
GradingStamps/
├── assets/
│   ├── stamps/        56 product images, renamed <CatalogID>_<slug>.gif
│   └── site/          logo, buttons, ruler chrome, Stylesheet.css
├── data/
│   └── products.json  structured catalog: id, name, keywords, prices,
│                      dimensions, description, category, image mapping
└── scrape/
    ├── scraper.py     the scraper (re-runnable)
    └── raw/
        ├── pages/     HTML snapshots of every site page
        └── moreinfo/  HTML snapshots of all 56 product detail popups
```

## What was captured

- **56 products** — 50 Teacher + 7 Spanish (1 bilingual overlap: A194).
  Every product has: name, catalog # (A086–A410), image, keywords,
  price, physical stamp dimensions (e.g. `2 1/4" × 1"`), and description.
- **Prices**: all pre-ink mount only (wood mount "Not Available" on every item).
  $12.95 ×40, $14.95 ×10, $19.95 ×5, $8.49 ×1.
- **Product images**: black & white line art GIFs. Sizes range 184×52 up to
  1259×1235. The image is the literal stamp impression — any "refresh" must
  preserve the artwork exactly (vectorize/upscale, never regenerate).
- **Site pages**: home, catalog (all pages/categories), custom generator,
  custom stamp tutorial, custom return address stamps, contact.

## Business facts worth keeping (from site copy)

- Tagline: "Stop Writing... Stop Explaining... Start Stamping"
- 20+ years serving teachers; 35+ years classroom experience behind the brand
- Pre-ink stamps: ~20,000 impressions before re-inking; "Not made in China.
  Designed and manufactured in Austria and assembled in the USA."
- Phone: (888) 288-2869 · Email: CustomerService@GradingStamps.com
- Promo video: YouTube `6a3_ZCirFFA` (embedded on the home page)
- Google Analytics UA-23006919-1 (legacy UA — dead since 2023, needs GA4 or none)

## Broken / legacy findings

1. **The Custom Stamp Generator is Flash** (`CustomStampGenerator.swf`).
   Flash was killed in all browsers in Jan 2021 — this feature has been
   non-functional for every visitor for years.
2. **Custom Return Address Stamps page is just an Etsy Mini widget**
   (Etsy shop ID `6652717`, legacy widget JS — also likely broken).
   → Confirm whether the Etsy shop is still active; it may be the cheapest
   checkout path for the new site.
3. Cart/checkout is ASP.NET WebForms postback (`ViewCart.aspx`) — the main
   reason the site needs a paid Windows server today.
4. Copyright footer still says 2011; XHTML 1.0 Transitional; UA analytics;
   Facebook Like button and StatCounter — all obsolete.
