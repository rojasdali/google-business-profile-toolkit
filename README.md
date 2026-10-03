# Google Business Profile Toolkit (`gbp-toolkit`)

Agnostic, modular Python SDK and CLI for Google Business Profile automation: local posts, zero-repeat deduplication, holiday hours management, customer reviews, and local search performance metrics.

---

## 📦 Architecture & Design Principles

- **Zero-Repeat Deduplication:** Built-in persistent ledger (`gbp_posts_history.json`) enforcing configurable cooldowns (default 90 days) so you never trigger Google's duplicate content filters.
- **Bilingual & WhatsApp CTA Ready:** First-class support for Spanish/English copy, media uploads, and instant WhatsApp click-to-chat links (`wa.me`).
- **Dry-Run & Mock Modes:** Test payload construction and formatting safely before live deployment.
- **Modular Clean Architecture:** All modules kept strictly under 120 lines with cyclomatic complexity $\le 10$.

---

## 🚀 Quickstart

### Installation
```bash
pip install -e .
```

### Environment Configuration
Copy `.env.example` to `.env` or pass credentials directly:
```bash
GBP_OAUTH_CLIENT_ID=your_client_id.apps.googleusercontent.com
GBP_OAUTH_CLIENT_SECRET=your_client_secret
GBP_OAUTH_REFRESH_TOKEN=your_refresh_token
GBP_ACCOUNT_ID=accounts/your_account_id
GBP_LOCATION_ID=locations/your_location_id
```

---

## 💻 CLI Usage

### Publish a Local Update (with WhatsApp CTA)
```bash
gbp posts publish \
  --summary "🧺 Weekly wash & fold special! Save time and drop off your laundry today." \
  --topic "wash-fold-promo" \
  --cta-url "https://wa.me/15551234567" \
  --dry-run
```

### Set Special Holiday Hours
```bash
# Mark store closed on Christmas
gbp hours close --date 2026-12-25

# Set modified hours on Thanksgiving (8 AM - 2 PM)
gbp hours modify --date 2026-11-26 --open 08:00 --close 14:00
```

### Audit NAP Consistency
```bash
gbp audit \
  --title "Your Business Name" \
  --phone "(555) 123-4567" \
  --address "123 Main St, City, ST 12345"
```

---

## 🐍 Python SDK Usage

```python
from gbp_toolkit import GBPToolkit

# Initialize from environment
toolkit = GBPToolkit.from_env()

# Publish update with 90-day deduplication protection
result = toolkit.posts.publish(
    summary="Wash your king-size comforters with ease in our 60-lb heavy duty washers.",
    topic_slug="bulky-comforters",
    cta_url="https://wa.me/15551234567",
)
print(f"Post live: {result.post_id}")
```
