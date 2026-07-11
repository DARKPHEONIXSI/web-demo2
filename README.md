# On Ice

A Flask/Jinja website for a figure-skating blog, gallery, and e-commerce shop.

## What It Includes

- Blog/journal with posts, drafts, cover images, categories, tags, slugs, and SEO fields
- Admin dashboard for posts, pages, gallery, media, products, users, messages, and orders
- Shop with product categories, badges, SKU, stock, sale pricing, variants, and images
- Server-priced cart quote with shipping and tax calculation
- Coupons, product search/filter/sort, wishlists, reviews, server-side saved carts, and stock checks
- Razorpay checkout for signed-in customers
- Real order confirmation, invoices, tracking links, cancellation/return requests, profile order history, and admin fulfillment/refund status
- Blog search, pagination, category/tag archives, comments, RSS feed, sitemap, robots.txt, canonical URLs, and structured data
- Legal pages for privacy, terms, shipping/returns, and refund policy
- Contact form, auth modals, password login, Google Sign-In support, and admin login
- Local file uploads and SQLite database by default
- CSRF protection, secure cookies, rate limits, upload validation, and HTML sanitization

## Tech Stack

- Python 3.9+
- Flask + Jinja templates
- SQLite by default
- Razorpay for active checkout payments
- SendGrid/Twilio optional notifications
- Pytest for tests

## Setup

```bash
cd D:\coding\simar
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python migrate.py
python app.py
```

Open `http://localhost:5000`.

## Required Environment Variables

Create `.env` in `D:\coding\simar`:

```env
SECRET_KEY=replace_with_a_long_random_secret
JWT_SECRET_KEY=replace_with_a_long_random_jwt_secret
ADMIN_USER=sir
ADMIN_PASS_HASH=generate_with_werkzeug

RAZORPAY_KEY_ID=rzp_test_xxx
RAZORPAY_KEY_SECRET=xxx
RAZORPAY_WEBHOOK_SECRET=xxx

GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com

SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=coach@onice.com
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
```

Generate an admin password hash:

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```

## Common Commands

```bash
python app.py
pytest tests/
ruff check .
black .
```

## Important Routes

- `/` - blog home
- `/post/<slug-or-id>` - blog post
- `/shop` - product catalog
- `/shop/<product_id>` - product details
- `/checkout` - signed-in checkout
- `/order/<order_token>` - order tracking
- `/invoice/<order_token>` - printable invoice
- `/returns/<order_token>` - return request
- `/sitemap.xml`, `/robots.txt`, `/feed.xml` - SEO/discovery endpoints
- `/profile` - account and order history
- `/admin/` - admin dashboard
- `/admin/orders` - order fulfillment dashboard

## Notes

- Checkout is intentionally signed-in only so orders can be tied to a customer profile.
- File uploads are stored locally in `uploads/`.
- SQLite is the supported default database for this local build.
