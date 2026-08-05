# Security Audit Findings

Date: 2026-07-26

## Security Research Result

### Verdict

PASS WITH FINDINGS

This was a ChatGPT-only, safe local audit of `D:\coding\simar`. I used the existing `SECURITY_AUDIT_FINDINGS.md` as prior input and re-verified the findings against the current code. No live external hacking, brute force, destructive testing, credential dumping, fuzzing, or public URL scanning was performed.

The app already has meaningful protections: global CSRF protection for browser-origin POSTs, Talisman security headers, HttpOnly auth cookies, parameterized database calls in reviewed routes, server-side cart pricing, Razorpay signature/provider verification, upload extension/MIME checks, image re-encoding, and production config validation for core secrets and SQLite usage.

### Scope

- Target: `D:\coding\simar` Flask blog/shop application.
- Existing report used: `D:\coding\simar\SECURITY_AUDIT_FINDINGS.md`.
- Main surfaces reviewed: auth, admin dashboard, public order/invoice/return pages, uploads, payments/webhooks, config/secrets, deployment script, templates, tests.
- Commands/checks run: `git status --short`, `git ls-files`, `git grep` route/security searches, direct file reads, dotenv key listing via EnvSitter.
- Tests: after recreating `.venv` with Python 3.14.6 and installing dependencies, `.venv\Scripts\python.exe -m pytest tests/test_security.py` passed with 21 tests.

### Findings

| Severity | Title | CWE | Exploitability | Impact | PoC | Fix |
| --- | --- | --- | --- | --- | --- | --- |
| High | Secrets and database files sit beside deployable app files | CWE-200 | If project root is served, synced, zipped, or exposed as static content, secrets/DB files can be downloaded | Full secret compromise, forged auth, provider/API compromise, database disclosure | Static evidence | Move secrets/DB/backups/logs/uploads outside any served/deployed root |
| Medium | In-memory rate-limit fallback weakens production brute-force protection | CWE-307 | If `REDIS_URL` is absent, limits use `memory://`, reset on restart, and do not coordinate across workers | Login/register/contact/payment abuse limits become easier to bypass | Static evidence | Require a shared limiter store in production config validation |
| Medium | Admin settings page renders third-party social tokens into HTML | CWE-522 | Any admin browser compromise, extension, screenshot, saved page, shoulder-surfing, or admin XSS can read full tokens | Facebook/Instagram API token compromise | Static evidence | Make tokens write-only/masked; preserve existing value when field is blank |
| Medium | Admin JSON data islands use raw `json.dumps(... )|safe` | CWE-79 | Admin-controlled text containing `</script>` can break out of `<script type="application/json">` | Stored admin-panel XSS, token theft, destructive admin actions | Safe local JSON proof | Render with Jinja `tojson`, not pre-serialized JSON marked safe |
| Medium | Order, invoice, and return pages use bearer order tokens only | CWE-639 | Anyone with a leaked order URL can view order details without login | Customer/order information disclosure | Static evidence | Require logged-in owner/admin for invoice and return pages; minimize public tracking |
| Low | Admin logout sidebar links GET to a POST-only logout route | CWE-613 | Admin clicking sidebar logout hits GET `/auth/logout`, but route only accepts POST | Admin may remain logged in while believing logout succeeded | Static evidence | Replace sidebar link with POST form/button or JS POST logout |
| Low | Razorpay webhook is likely blocked by global CSRF protection | CWE-693 | Razorpay cannot send app CSRF tokens, so valid webhook POSTs can be rejected before HMAC logic | Payment/order state updates can become stale or broken | Static evidence | Exempt only the webhook view from CSRF and keep HMAC verification |
| Low | Quick-tunnel script can expose a dev server to the internet | CWE-489 | Running `start_online.ps1` exposes `localhost:5000` to `trycloudflare.com` | Accidental public exposure of dev config/local data | Static evidence | Add production/dev guards or mark quick tunnel demo-only |

## Finding Details

### 1. Secrets and database files sit beside deployable app files

Evidence:
- `D:\coding\simar\.env` exists. EnvSitter key listing confirmed sensitive keys including `ADMIN_PASS`, `ADMIN_PASS_HASH`, `SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`, `RAZORPAY_KEY_SECRET`, `SENDGRID_API_KEY`, and Twilio keys. Values were not printed.
- `D:\coding\simar\simar.db`, `simar_backup2.db`, and `database_backup.db` exist in the app directory.
- `.gitignore` excludes `.env`, `*.db`, `uploads/`, logs, and `cloudflared.exe`, but ignore rules do not protect against bad static hosting, artifact packaging, backup sync, or a misconfigured reverse proxy.

Attack path:
1. The project root is accidentally served as a static root, uploaded to public hosting, zipped into a release artifact, or exposed by a bad reverse proxy rule.
2. An attacker requests or obtains `.env`, `*.db`, logs, or upload backups.
3. The attacker uses leaked secrets to forge sessions/JWTs, access payment/provider accounts, read customer/order data, or take over connected services.

Severity rationale:
- High because exploit impact is full application/provider compromise if the deployment mistake occurs. The precondition is a deployment/configuration mistake, not a direct Flask route in reviewed code.

Minimal fix:
- Keep `.env`, SQLite DBs, DB backups, logs, and upload directories outside any web-served/deployed root.
- Use managed Postgres through `DATABASE_URL` for production as `config.py` already pushes toward.
- Add deployment smoke tests for `/.env`, `/simar.db`, `/database_backup.db`, `/logs/onice.log`, and `/uploads/` expecting 404/403.

Regression check:
- Fail deployment if sensitive files are present under the document root or packaged artifact.

### 2. In-memory rate-limit fallback weakens production brute-force protection

Evidence:
- `config.py` sets `RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL", "memory://")`.
- `app.py` wires rate limits on login, registration, contact, and payment endpoints.
- `validate_config()` does not require `REDIS_URL` or another shared limiter backend in production.

Attack path:
1. App runs in production with multiple workers or frequent restarts and no shared rate-limit backend.
2. An attacker spreads login/register attempts across workers or waits for restarts.
3. Intended brute-force limits are weaker than operators expect.

Severity rationale:
- Medium because it does not grant direct access by itself, but it weakens a key defense around auth and abuse-prone endpoints.

Minimal fix:
- In production validation, require `REDIS_URL` or a deliberately configured shared limiter store.
- Add a test where `FLASK_ENV=production` and `REDIS_URL` is absent, expecting startup failure.

### 3. Admin settings page renders third-party social tokens into HTML

Evidence:
- `admin_bp.py` loads `social_tokens = db.execute("SELECT * FROM social_tokens").fetchall()`.
- `templates/admin/dashboard.html` renders raw saved access tokens into `#sFbToken` and `#sIgToken` input values.
- `api.py` stores submitted `fb_token` and `ig_token` values in `social_tokens`.

Attack path:
1. Admin opens the settings page on a compromised/shared browser, or a malicious extension/admin-panel XSS reads the DOM.
2. Full provider tokens are present in HTML input values.
3. The attacker copies the tokens and accesses connected social APIs.

Severity rationale:
- Medium because it requires admin browser/page access, but the impact is compromise of third-party API credentials.

Minimal fix:
- Render masked placeholders such as `token saved`, never the raw token.
- On submit, treat blank token fields as "leave unchanged" and use a separate remove-token action.
- Rotate any token that has already been exposed in browser HTML.

Regression check:
- Seed a fake token and assert `/admin/?sec=settings` does not contain the raw token string.

### 4. Admin JSON data islands use raw `json.dumps(... )|safe`

Evidence:
- `admin_bp.py` builds `techs_json=json.dumps(techs_json)` and `gallery_json=json.dumps(gallery_json)`.
- `templates/admin/dashboard.html` emits `<script id="techDataJson" type="application/json">{{ techs_json|safe }}</script>` and the same for gallery data.
- Technique/gallery fields are admin-controlled and flow into those JSON blobs.

Attack path:
1. A malicious or compromised admin/import process stores a value containing `</script><script>...</script>` or equivalent markup.
2. The dashboard renders that value inside a script tag as raw safe HTML.
3. The browser closes the script tag early and executes attacker-controlled markup/script in the admin origin.

Safe proof:
- A local JSON serialization check shows Python `json.dumps()` does not escape `</script>` into a browser-safe sequence. That is enough for static proof; no live exploit was run.

Severity rationale:
- Medium because the attacker must already control admin-editable content or an import path, but exploitation runs in the admin origin and can steal rendered tokens or perform admin actions.

Minimal fix:
- Pass Python dict/list objects to the template and render `{{ techs_json|tojson }}` / `{{ gallery_json|tojson }}` without prior `json.dumps()`.
- Add a regression test with a `</script>` payload and assert the response does not contain a data-origin literal closing script sequence.

### 5. Order, invoice, and return pages use bearer order tokens only

Evidence:
- `app.py` serves `/order/<order_token>`, `/invoice/<order_token>`, and `/returns/<order_token>` without login checks.
- `templates/invoice.html` displays customer name/address and totals.
- `templates/order_tracking.html` displays status, total, tracking number, line items, and links to invoice/returns.
- Mutation endpoints `/api/order/cancel` and `/api/returns/request` correctly require login and owner matching, but page viewing does not.

Attack path:
1. An order URL leaks via forwarded email, screenshot, browser history, logs, support chat, analytics/referrer, or shared device.
2. Anyone with the tokenized URL can load the tracking/invoice/return page without being the owner.
3. Order/customer details are disclosed.

Severity rationale:
- Medium because UUIDv4 token guessing is not realistic, but leaked bearer URLs are common and the invoice page contains PII.

Minimal fix:
- Require logged-in owner or admin for `/invoice/<order_token>` and `/returns/<order_token>`.
- Keep public `/order/<order_token>` minimal if anonymous tracking is desired: status only, no address, no invoice link, no return form.
- Avoid putting full order tokens into third-party links/referrers.

Regression check:
- Insert an order for user A, request invoice/returns anonymously and as user B, and expect 401/403 or redacted content.

### 6. Admin logout sidebar links GET to a POST-only logout route

Evidence:
- `auth.py` defines `@auth_bp.route("/auth/logout", methods=["POST"])`.
- `templates/admin/dashboard.html` has `<a href="{{ url_for('auth.logout') }}">Logout</a>`.
- `templates/base.html` already has JS that POSTs logout only for an element with `id="logoutBtn"`, but the admin sidebar link does not use that id.

Attack/breakage path:
1. Admin clicks sidebar Logout.
2. Browser sends GET `/auth/logout`.
3. The route does not match, so cookies/tokens remain active and the admin can think they are logged out when they are not.

Minimal fix:
- Replace the sidebar link with a POST form/button containing CSRF, or add `id="logoutBtn"` and prevent default navigation while POSTing `/auth/logout`.

### 7. Razorpay webhook is likely blocked by global CSRF protection

Evidence:
- `app.py` initializes `CSRFProtect()` globally before/around blueprint registration.
- `api.py` defines `/api/razorpay/webhook` as a POST route with HMAC verification, but there is no route-specific CSRF exemption.
- Razorpay cannot provide the app's CSRF token.

Attack/breakage path:
1. Razorpay sends a valid webhook with a valid `X-Razorpay-Signature`.
2. Flask-WTF CSRF validation can reject the POST before `razorpay_webhook()` verifies the HMAC.
3. Payment/order status updates from webhooks may fail.

Minimal fix:
- Exempt only the webhook view from CSRF.
- Keep the HMAC signature check exactly as the real security boundary for that route.
- Add a test that posts a valid-HMAC webhook without CSRF and reaches webhook logic rather than Flask-WTF's CSRF 400.

### 8. Quick-tunnel script can expose a dev server to the internet

Evidence:
- `start_online.ps1` downloads/runs `cloudflared.exe` and exposes `http://localhost:5000` through a public quick tunnel.
- `app.py` can run Flask's development server directly with `python app.py`; debug is controlled by `FLASK_DEBUG=1`.
- The script does not check `FLASK_ENV`, `FLASK_DEBUG`, server type, or whether production-safe config is active.

Attack path:
1. Developer starts the local Flask server with weak/dev settings.
2. Developer runs `start_online.ps1`.
3. Internet users reach the local development app through a public Cloudflare URL.

Minimal fix:
- Mark the script demo-only, or add guards refusing to run when `FLASK_DEBUG=1`, `FLASK_ENV!=production`, or production config validation has not passed.
- Prefer named Cloudflare tunnels and a proper WSGI server for real public exposure.

## Downgraded or Rejected Candidates

| Candidate | Reason |
| --- | --- |
| SQL injection in normal app routes | Reviewed dynamic queries use parameter placeholders for attacker-controlled values. Dynamic SQL fragments found are selected from server-side constants or internal table/column names. |
| Cart price tampering | `calculate_cart_total()` ignores browser-supplied price and uses database prices; tests cover this behavior. |
| Razorpay payment amount tampering | Verification checks signature, provider payment/order amount, currency, captured status, provider order amount, cart hash, and idempotency. |
| Public uploads immediate RCE | Upload endpoints are admin-only, filenames are generated, image uploads are MIME-checked and re-encoded. MP4 uploads remain a content-policy/deployment risk but not a proven RCE path from reviewed code. |
| Stored XSS in public post/product/page body via normal admin save | Bodies are passed through `purify_html()` before save, and tests cover script/javascript stripping. Residual risk remains for legacy database content and the admin JSON data-island issue above. |
| Missing basic security headers | Talisman config includes CSP, HSTS, Secure/HttpOnly/SameSite cookie settings. CSP still allows `'unsafe-inline'`, which worsens XSS impact but is not a standalone vulnerability without a sink. |
| Public health endpoint | `/api/health` returns only service/status and no secrets or build metadata. |

## Residual Risk

- The local test environment was repaired after the audit by recreating `.venv` with Python 3.14.6 and installing dependencies; `tests/test_security.py` now passes. Full-app browser/manual QA and live deployment verification were still not performed.
- No live deployment was attacked or scanned, so proxy/static-root rules, TLS, DNS, Cloudflare settings, and actual response headers were not verified.
- Secret values were not read or printed; only key names/shapes were inspected safely.
- Database contents were not inspected, so legacy stored HTML, real PII exposure volume, and existing token leakage could not be measured.
- Dependency CVEs were not fully audited because no working dependency-audit tool was available in the local environment.
- `rg` was unavailable in PowerShell, so searches used `git grep`, `git ls-files`, EnvSitter, and direct file reads instead.
