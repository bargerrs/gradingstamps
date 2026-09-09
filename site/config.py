"""Single place for everything an owner might need to change."""

# CONFIRM before launch: the PayPal account email that receives payments.
# Until confirmed with Dad, this is a best-guess placeholder — payments sent
# to an email with no PayPal account sit "unclaimed" and auto-refund in 30 days.
PAYPAL_BUSINESS = "CustomerService@GradingStamps.com"

SITE_URL = "https://www.gradingstamps.com"   # canonical, no trailing slash
SITE_NAME = "GradingStamps"
DOMAIN = "www.gradingstamps.com"             # written to docs/CNAME

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
