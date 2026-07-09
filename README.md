# On Ice — Aurora Frost Edition

A comprehensive skating blog and e-commerce platform with full-stack security hardening.

## Overview

On Ice is a Flask-based web application for figure skating coaching, featuring a blog, gallery, marketplace, and secure e-commerce functionality. The platform has been completely rebuilt with enterprise-grade security including JWT authentication, HTTPS enforcement, rate limiting, and automated notifications.

## Features

### 📚 Blog & Content
- Full CRUD for posts, techniques, and custom pages
- Public blog feed with pagination and search
- Admin dashboard for content management
- Social media integration (Facebook, Instagram)

### 🛒 E-Commerce
- Product catalog with variants and images
- Razorpay and Paytm payment integration
- Order tracking and management
- Secure checkout process

### 🎬 Gallery & Media
- Comprehensive gallery with emoji-based categorization
- Media library upload (images + videos)
- Public gallery view with filtering

### 🔐 Security (Hardened)
- **JWT Authentication** with secure HttpOnly cookies
- **HTTPS Enforcement** via Talisman with HSTS
- **Rate Limiting** on all authentication and payment endpoints
- **Input Validation** and sanitization across all forms
- **CSRF Protection** for all state-changing operations
- **Secure Headers** with Content-Security-Policy
- **SQL Injection Prevention** with parameterized queries
- **Error Handling** without information leakage

### 📧 Notifications
- **Email** via SendGrid for order confirmations
- **SMS** via Twilio for customer notifications
- Automated order processing workflows

### 📊 Admin Interface
- Comprehensive admin dashboard
- User and content management
- System settings configuration

## Architecture

```
Frontend (React/Vue.js) ← HTTPS → Security Layer → JWT Auth → API Layer → Database
                                    ↑              ↑              ↑
                           Talisman (HTTPS)   Session Manager  SQLite
```

## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL or SQLite database
- Git

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/onice.git
cd onice

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python migrate.py

# Run application
python app.py
```

### Production Deployment

```bash
# Using Gunicorn for production
pip install gunicorn
python -m gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

# Or use the built-in WSGI server
python -m wsgi
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
SECRET_KEY=your_super_secure_random_key_here
JWT_SECRET_KEY=your_jwt_secret_key

# Google Sign-In
GOOGLE_CLIENT_ID=your_google_oauth_web_client_id.apps.googleusercontent.com

# Supabase/Postgres
# Use the Supabase pooler/session connection string from Project Settings > Database.
DATABASE_URL=postgresql://postgres.your-project-ref:your-password@aws-0-region.pooler.supabase.com:5432/postgres

# Supabase Storage uploads
STORAGE_BACKEND=supabase
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_STORAGE_BUCKET=onice-uploads

# Payment Gateways
RAZORPAY_KEY_ID=rzp_test_your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
PAYTM_MERCHANT_ID=your_paytm_merchant_id
PAYTM_MERCHANT_KEY=your_paytm_merchant_key

# Notifications
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=coach@onice.com
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_FROM_NUMBER=+15551234567
```

### Configuration

The application uses:
- **SQLite** when `DATABASE_URL` is not set
- **Supabase/Postgres** when `DATABASE_URL` is set
- **Supabase Storage** for uploads when `STORAGE_BACKEND=supabase`
- **HTTPs** enforced in production
- **Secure cookies** with SameSite=Lax
- **Rate limiting** to prevent abuse

## API Endpoints

### Authentication
- `POST /auth/login` - Login with JWT tokens
- `POST /auth/register` - Register new user
- `POST /auth/logout` - Logout and clear tokens
- `POST /auth/refresh` - Refresh JWT access token
- `GET /auth/me` - Get current user info
- `POST /auth/google` - Google Sign-In with verified Google ID token

### Payment Processing
- `POST /api/create_razorpay_order` - Create Razorpay order
- `POST /api/verify_razorpay` - Verify Razorpay payment
- `POST /api/create_paytm_order` - Create Paytm order
- `POST /api/verify_paytm` - Verify Paytm payment

### Content Management
- `GET /api/get_posts` - Get published posts
- `POST /api/save_post` - Create/update post (admin)
- `POST /api/save_technique` - Create/update technique (admin)
- `POST /api/save_page` - Create/update custom page (admin)
- `POST /api/save_product` - Create/update product (admin)

### Media
- `POST /api/upload_image` - Upload image (admin)
- `POST /api/upload_media` - Upload media file (admin)

### Contact & Communication
- `POST /api/contact` - Public contact form submission

## Security Features

### 1. Authentication & Authorization
- JWT tokens with 1-hour access and 7-day refresh expiration
- Secure HttpOnly cookies to prevent XSS
- Role-based access control (user/admin)
- Token refresh mechanism to maintain sessions

### 2. HTTPS & Security Headers
- **Talisman** enforces HTTPS with HSTS
- Content-Security-Policy (CSP) prevents XSS
- Secure cookie settings (Secure, HttpOnly, SameSite)
- Frame options prevent clickjacking

### 3. Rate Limiting
- 5 attempts/minute on login/register
- 10 attempts/minute on payment endpoints
- 200 requests/minute default limit
- Memory-based storage

### 4. Input Validation & Sanitization
- All form inputs validated for length and format
- HTML sanitization with bleach
- Parameterized SQL queries
- File upload validation (whitelist extensions)

### 5. Payment Security
- Razorpay signature verification
- Paytm checksum validation
- Idempotency keys to prevent replay attacks
- Unique transaction IDs

### 6. Error Handling
- Generic error messages (no stack traces)
- Log errors for debugging
- Rate limit specific error responses
- No information leakage

## Testing & Validation

### Code Quality
```bash
# Format code with black
black .

# Lint code with ruff
ruff check .

# Fix imports automatically with ruff
ruff check --fix .

# Type checking with mypy
mypy .
```

### Automated Testing
```bash
# Run tests (if test directory exists)
pytest tests/

# Or run specific test files
pytest tests/test_auth.py
```

## Deployment

### Local Development
```bash
# Run with development server
python app.py

# Or using gunicorn
pip install gunicorn
python -m gunicorn app:app
```

### Production
```bash
# Install system dependencies
# Configure reverse proxy (nginx/Apache)
# Set FLASK_ENV=production
# Deploy with gunicorn
export FLASK_ENV=production
python -m gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## License

MIT License - See LICENSE file for details.

## Contact

For support or questions:
- Email: coach@onice.com
- GitHub: https://github.com/your-org/onice

## Changelog

### v1.0.0
- Initial release with security hardening
- JWT authentication
- HTTPS enforcement
- Rate limiting
- Payment integration
- Automated notifications
