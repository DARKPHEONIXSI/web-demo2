# Vercel Deployment Checklist for Simar/On Ice

## ✅ Files Created
- `vercel.json` — Vercel configuration
- `api/index.py` — Serverless entry point
- `.vercelignore` — Excludes unnecessary files
- `runtime.txt` — Python 3.11

## 🔧 Required Changes Before Deploy

### 1. Database (CRITICAL)
**SQLite won't work on Vercel** (ephemeral filesystem). You must use Postgres:
- **Vercel Postgres** (easiest: `vercel storage create postgres`)
- **Neon** (free tier: `neon.tech`)
- **Supabase** (free tier: `supabase.com`)

Set `DATABASE_URL` in Vercel dashboard:
```
postgresql://user:pass@host:5432/dbname?sslmode=require
```

Run migrations after first deploy:
```bash
# Connect to your Postgres and run:
psql $DATABASE_URL -f schema_postgres.sql
```

### 2. Redis for Rate Limiting (CRITICAL)
`flask-limiter` needs Redis. Use **Upstash** (free tier):
- Create database at `upstash.com`
- Set `REDIS_URL` in Vercel:
```
redis://default:password@host:port
```

### 3. File Uploads (CRITICAL)
Local `uploads/` folder won't persist. Options:
- **Vercel Blob** (native, easy): `vercel storage create blob`
- **AWS S3** / **Cloudflare R2**
- Set `STORAGE_BACKEND` in config (currently `"local"`)

### 4. Environment Variables (Set in Vercel Dashboard → Settings → Environment Variables)
| Variable | Required | Notes |
|----------|----------|-------|
| `SECRET_KEY` | ✅ | 32+ char random string |
| `JWT_SECRET_KEY` | ✅ | 32+ char, different from SECRET_KEY |
| `ADMIN_USER` | ✅ | Your admin username |
| `ADMIN_PASS_HASH` | ✅ | Generate: `python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('yourpass'))"` |
| `DATABASE_URL` | ✅ | Postgres connection string |
| `REDIS_URL` | ✅ | Upstash Redis URL |
| `FLASK_ENV` | ✅ | `production` |
| `RAZORPAY_KEY_ID` | ⚠️ | If using Razorpay |
| `RAZORPAY_KEY_SECRET` | ⚠️ | If using Razorpay |
| `RAZORPAY_WEBHOOK_SECRET` | ⚠️ | If using Razorpay |
| `PAYTM_MERCHANT_ID` | ⚠️ | If using Paytm |
| `PAYTM_MERCHANT_KEY` | ⚠️ | If using Paytm |
| `GOOGLE_CLIENT_ID` | ⚠️ | If using Google Sign-In |
| `SENDGRID_API_KEY` | ⚠️ | If using email |
| `SENDGRID_FROM_EMAIL` | ⚠️ | If using email |
| `TWILIO_ACCOUNT_SID` | ⚠️ | If using SMS |
| `TWILIO_AUTH_TOKEN` | ⚠️ | If using SMS |
| `TWILIO_FROM_NUMBER` | ⚠️ | If using SMS |
| `TURNSTILE_SITE_KEY` | ⚠️ | If using Cloudflare Turnstile |
| `TURNSTILE_SECRET_KEY` | ⚠️ | If using Cloudflare Turnstile |

### 5. Generate Secure Keys
```bash
# Generate SECRET_KEY and JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Run twice for two different keys
```

## 🚀 Deploy Steps

1. **Push to GitHub:**
   ```bash
   cd D:\coding\simar
   git add .
   git commit -m "Add Vercel config"
   git push origin main
   ```

2. **Import in Vercel:**
   - Go to `vercel.com/new`
   - Import your GitHub repo
   - Vercel should auto-detect Python/Flask

3. **Configure Environment Variables** (see table above)

4. **Deploy**

5. **Run Migrations:**
   - Go to Vercel Functions → View Function Logs
   - Or use Vercel CLI: `vercel env pull .env.local` then run migrations locally

## 🐛 Common Issues & Fixes

| Error | Fix |
|-------|-----|
| `FUNCTION_INVOCATION_FAILED` | Check function logs in Vercel dashboard |
| `ModuleNotFoundError` | Ensure all deps in `requirements.txt` |
| `sqlite3.OperationalError` | You're using SQLite — switch to Postgres |
| `redis.exceptions.ConnectionError` | Set `REDIS_URL` to Upstash |
| `ADMIN_PASS_HASH missing` | Generate and set in Vercel env vars |
| `Secure cookies must be enabled` | Set `FLASK_ENV=production` |
| `Rate limit store required` | Set `REDIS_URL` |

## 📝 Notes
- The app uses SPA catch-all (`static/index.html`) for frontend routing
- API routes under `/api/*` are handled by Flask blueprints
- Static files served directly by Vercel CDN (see `vercel.json` routes)
- Max function duration: 30s, Memory: 1024MB

## 🔗 Useful Links
- Vercel Python docs: `vercel.com/docs/concepts/functions/serverless-functions/runtimes/python`
- Vercel Postgres: `vercel.com/docs/storage/vercel-postgres`
- Upstash Redis: `upstash.com/docs/redis/getting-started`
- Vercel Blob: `vercel.com/docs/storage/vercel-blob`