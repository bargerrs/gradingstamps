"""Single place for everything an owner might need to change."""

# The PayPal account that receives payments — recovered from the old site's
# working ViewCart.aspx (its cart-upload form posted business=MJARTSTAMP@AOL.COM).
PAYPAL_BUSINESS = "MJARTSTAMP@AOL.COM"

SITE_URL = "https://www.gradingstamps.com"   # canonical, no trailing slash
SITE_NAME = "GradingStamps"
DOMAIN = "www.gradingstamps.com"             # written to docs/CNAME
# Keep False until the domain's DNS points at GitHub Pages — a CNAME file
# makes GitHub redirect the *.github.io preview to the (not-yet-live) domain.
WRITE_CNAME = True

CONTACT_EMAIL = "CustomerService@GradingStamps.com"
PHONE_DISPLAY = "(888) 288-2869"
PHONE_HREF = "tel:+18882882869"

TAGLINE = "Stop writing. Stop explaining. Start stamping."

# Shown in header byline / footer / about copy
MAKER = "MJ's Art Stamps"
FOUNDED_BLURB = (
    "MJ's Art Stamps has been making rubber stamps for teachers for more than "
    "20 years, built on 35+ years of real classroom experience."
)

# Product facts used across pages (from the original site's own copy)
IMPRESSIONS = "20,000"
MOUNT_BLURB = (
    "Every stamp ships on a modern pre-ink mount — no ink pad, no mess, about "
    "20,000 clean impressions before it ever needs re-inking. Mounts are "
    "manufactured in Austria and assembled in the USA."
)
