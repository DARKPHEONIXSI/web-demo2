"""
auth.py — Authentication blueprint for the On Ice skating blog.
Handles login, register, logout, JWT tokens, password change, and auth modals.
"""

from functools import wraps
import json
import urllib.parse
import urllib.request

from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token
except ImportError:
    google_requests = None
    google_id_token = None

from models import (
    clear_tokens,
    create_access_token,
    create_refresh_token,
    ensure_builtin_admin_user,
    gen_id,
    get_db,
    get_settings,
    get_user_by_access_token,
    log_audit,
    store_tokens,
    verify_refresh_token,
)

auth_bp = Blueprint("auth", __name__)


def verify_turnstile() -> str | None:
    """Verify Cloudflare Turnstile when configured; return an error message if invalid."""
    secret = current_app.config.get("TURNSTILE_SECRET_KEY")
    if not secret:
        return None
    token = request.form.get("cf-turnstile-response") or ""
    if not token:
        return "Human verification is required."
    data = urllib.parse.urlencode(
        {"secret": secret, "response": token, "remoteip": request.remote_addr or ""}
    ).encode("utf-8")
    try:
        req = urllib.request.Request("https://challenges.cloudflare.com/turnstile/v0/siteverify", data=data)
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception:
        current_app.logger.warning("Turnstile verification request failed")
        return "Human verification failed."
    return None if result.get("success") else "Human verification failed."


# ── JWT Cookie helpers ────────────────────────────────────────


def set_auth_cookies(response, access_token: str, refresh_token: str):
    """Set HttpOnly Secure cookies for access and refresh tokens."""
    secure = current_app.config["JWT_COOKIE_SECURE"]
    response.set_cookie(
        "access_token",
        access_token,
        httponly=current_app.config["JWT_COOKIE_HTTPONLY"],
        secure=secure,
        samesite=current_app.config["JWT_COOKIE_SAMESITE"],
        max_age=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=current_app.config["JWT_COOKIE_HTTPONLY"],
        secure=secure,
        samesite=current_app.config["JWT_COOKIE_SAMESITE"],
        max_age=current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
        path="/auth/refresh",
    )


def clear_auth_cookies(response):
    """Clear auth cookies."""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/auth/refresh")


def get_access_token_from_cookie() -> str | None:
    """Get access token from HttpOnly cookie."""
    return request.cookies.get("access_token")


def get_refresh_token_from_cookie() -> str | None:
    """Get refresh token from HttpOnly cookie."""
    return request.cookies.get("refresh_token")


# ── Auth decorators ──────────────────────────────────────────


def jwt_required(f):
    """Decorator: require valid JWT access token."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_access_token_from_cookie()
        if not token:
            return (
                jsonify(
                    {
                        "ok": False,
                        "msg": "Authentication required",
                        "code": "AUTH_REQUIRED",
                    }
                ),
                401,
            )

        user = get_user_by_access_token(token)
        if not user:
            return (
                jsonify(
                    {
                        "ok": False,
                        "msg": "Invalid or expired token",
                        "code": "TOKEN_INVALID",
                    }
                ),
                401,
            )

        # Attach user to request context
        request.current_user = user
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Decorator: require admin role."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_access_token_from_cookie()
        if not token:
            return (
                jsonify(
                    {
                        "ok": False,
                        "msg": "Authentication required",
                        "code": "AUTH_REQUIRED",
                    }
                ),
                401,
            )

        user = get_user_by_access_token(token)
        if not user or user.get("role") != "admin":
            return (
                jsonify(
                    {
                        "ok": False,
                        "msg": "Admin access required",
                        "code": "ADMIN_REQUIRED",
                    }
                ),
                403,
            )

        request.current_user = user
        return f(*args, **kwargs)

    return decorated


# ── Session helpers (for backward compatibility) ──────────────


def get_sess():
    """Get current user display data from JWT, falling back to legacy session."""
    token = get_access_token_from_cookie()
    if token:
        user = get_user_by_access_token(token)
        if user:
            return {
                "id": user["id"],
                "role": user["role"],
                "username": "Admin" if user["id"] == "admin" else user["id"],
            }
    return session.get("simar_user")


def set_sess(user_data: dict):
    """Store user data in session."""
    session["simar_user"] = user_data


def clear_sess():
    """Clear session data."""
    session.pop("simar_user", None)


def is_admin() -> bool:
    """Check if current user is admin via JWT only."""
    token = get_access_token_from_cookie()
    if token:
        user = get_user_by_access_token(token)
        if user and user.get("role") == "admin":
            return True
    return False


def require_admin(f):
    """Decorator: redirect to admin login if not admin (backward compat)."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return redirect(url_for("admin.admin_login"))
        return f(*args, **kwargs)

    return decorated


# ── Modal endpoint ───────────────────────────────────────────


@auth_bp.route("/auth/modal")
def auth_modal():
    """Return login/register modal HTML fragment."""
    mode = request.args.get("mode", "login")
    s = get_settings()
    return render_template("partials/auth_modal.html", mode=mode, settings=s)


# ── Logout ───────────────────────────────────────────────────


@auth_bp.route("/auth/logout", methods=["POST"])
@jwt_required
def logout():
    """Clear tokens and cookies."""
    user_id = request.current_user["id"]
    clear_tokens(user_id)

    response = make_response(jsonify({"ok": True, "msg": "Logged out successfully"}))
    clear_auth_cookies(response)

    # Also clear legacy session
    clear_sess()
    return response


# ── Login (AJAX) ─────────────────────────────────────────────


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Handle login via AJAX POST. Returns JWT tokens in HttpOnly cookies."""
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    # Admin shortcut — compare via hash
    if username == current_app.config["ADMIN_USER"]:
        if check_password_hash(current_app.config["ADMIN_PASS_HASH"], password):
            ensure_builtin_admin_user()
            access_token, access_expires = create_access_token("admin", "admin")
            refresh_token, refresh_expires = create_refresh_token("admin")
            store_tokens(
                "admin", access_token, access_expires, refresh_token, refresh_expires
            )

            response = make_response(
                jsonify({"ok": True, "msg": "Welcome, Coach!", "role": "admin"})
            )
            set_auth_cookies(response, access_token, refresh_token)
            set_sess({"role": "admin", "username": "Admin", "id": "admin"})
            return response
        return jsonify({"ok": False, "msg": "Incorrect username or password."}), 401

    # Database user lookup
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ? AND is_google = 0 LIMIT 1", (username,)
    ).fetchone()

    if user and check_password_hash(user["password"], password):
        access_token, access_expires = create_access_token(user["id"], user["role"])
        refresh_token, refresh_expires = create_refresh_token(user["id"])
        store_tokens(
            user["id"], access_token, access_expires, refresh_token, refresh_expires
        )

        response = make_response(
            jsonify(
                {
                    "ok": True,
                    "msg": f'Welcome back, {user["username"]}!',
                    "role": user["role"],
                }
            )
        )
        set_auth_cookies(response, access_token, refresh_token)
        set_sess({"role": user["role"], "username": user["username"], "id": user["id"]})
        return response

    current_app.logger.warning("failed login for username %r from %s", username, request.remote_addr)
    log_audit("auth.login_failed", ip_address=request.remote_addr, username=username)
    return jsonify({"ok": False, "msg": "Incorrect username or password."}), 401


# ── Register (AJAX) ──────────────────────────────────────────


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Handle registration via AJAX POST. Returns JWT tokens in HttpOnly cookies."""
    turnstile_error = verify_turnstile()
    if turnstile_error:
        log_audit("auth.register_turnstile_failed", ip_address=request.remote_addr)
        return jsonify({"ok": False, "msg": turnstile_error}), 400

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    password2 = request.form.get("password2") or ""

    if len(username) < 3:
        return jsonify({"ok": False, "msg": "Username must be 3+ characters."}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "msg": "Password must be 6+ characters."}), 400
    if password != password2:
        return jsonify({"ok": False, "msg": "Passwords do not match."}), 400
    if username.lower() == current_app.config["ADMIN_USER"].lower():
        return jsonify({"ok": False, "msg": "That username is reserved."}), 400

    db = get_db()
    existing = db.execute(
        "SELECT id FROM users WHERE username = ? LIMIT 1", (username,)
    ).fetchone()
    if existing:
        current_app.logger.warning("duplicate registration attempt for username %r from %s", username, request.remote_addr)
        log_audit("auth.register_duplicate", ip_address=request.remote_addr, username=username)
        return jsonify({"ok": False, "msg": "Username already taken."}), 409

    user_id = gen_id()
    db.execute(
        "INSERT INTO users (id, username, password, role) VALUES (?, ?, ?, ?)",
        (user_id, username, generate_password_hash(password), "user"),
    )
    db.commit()
    current_app.logger.info("registered user %s from %s", user_id, request.remote_addr)
    log_audit("auth.register_success", actor_id=user_id, ip_address=request.remote_addr, username=username)

    access_token, access_expires = create_access_token(user_id, "user")
    refresh_token, refresh_expires = create_refresh_token(user_id)
    store_tokens(user_id, access_token, access_expires, refresh_token, refresh_expires)

    response = make_response(
        jsonify({"ok": True, "msg": f"Welcome, {username}!", "role": "user"})
    )
    set_auth_cookies(response, access_token, refresh_token)
    set_sess({"role": "user", "username": username, "id": user_id})
    return response


# ── Google (simulated) ───────────────────────────────────────


@auth_bp.route("/auth/google", methods=["POST"])
def google_login():
    """Google sign-in using a verified Google ID token."""
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    credential = request.form.get("credential") or ""
    if not client_id:
        current_app.logger.warning("Google login attempted without GOOGLE_CLIENT_ID")
        log_audit("auth.google_not_configured", ip_address=request.remote_addr)
        return jsonify({"ok": False, "msg": "Google sign-in is not configured."}), 501
    if google_id_token is None or google_requests is None:
        current_app.logger.warning("Google login attempted without google-auth installed")
        return jsonify({"ok": False, "msg": "Google auth dependency is not installed."}), 501
    if not credential:
        return jsonify({"ok": False, "msg": "Missing Google credential."}), 400

    try:
        payload = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id
        )
    except ValueError:
        current_app.logger.warning("invalid Google ID token from %s", request.remote_addr)
        log_audit("auth.google_invalid", ip_address=request.remote_addr)
        return jsonify({"ok": False, "msg": "Invalid Google sign-in."}), 401

    if payload.get("aud") != client_id:
        current_app.logger.warning("Google token audience mismatch from %s", request.remote_addr)
        return jsonify({"ok": False, "msg": "Invalid Google sign-in."}), 401

    email = (payload.get("email") or "").strip().lower()
    if not email or not payload.get("email_verified"):
        return jsonify({"ok": False, "msg": "Google email is not verified."}), 401

    name = (payload.get("name") or email.split("@")[0]).strip()
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE google_email = ? LIMIT 1", (email,)
    ).fetchone()

    if not user:
        user_id = gen_id()
        username_base = "".join(
            ch for ch in (email.split("@")[0] or "google_user") if ch.isalnum() or ch in "_-"
        )[:30] or "google_user"
        username = username_base
        suffix = 2
        while db.execute("SELECT id FROM users WHERE username = ? LIMIT 1", (username,)).fetchone():
            username = f"{username_base}_{suffix}"
            suffix += 1
        db.execute(
            'INSERT INTO users (id, username, password, google_email, is_google, role) VALUES (?, ?, "", ?, 1, ?)',
            (user_id, username, email, "user"),
        )
        db.commit()
        user_data = {"id": user_id, "username": username, "role": "user"}
        current_app.logger.info("registered Google user %s from %s", user_id, request.remote_addr)
        log_audit("auth.google_register", actor_id=user_id, ip_address=request.remote_addr, email=email)
    else:
        user_data = {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        }

    access_token, access_expires = create_access_token(
        user_data["id"], user_data["role"]
    )
    refresh_token, refresh_expires = create_refresh_token(user_data["id"])
    store_tokens(
        user_data["id"], access_token, access_expires, refresh_token, refresh_expires
    )

    response = make_response(
        jsonify({"ok": True, "msg": f"Signed in as {name}", "role": user_data["role"]})
    )
    set_auth_cookies(response, access_token, refresh_token)
    set_sess({**user_data, "google_email": email})
    return response


# ── Token Refresh ────────────────────────────────────────────


@auth_bp.route("/auth/refresh", methods=["POST"])
def refresh():
    """Refresh access token using refresh token from cookie."""
    refresh_token = get_refresh_token_from_cookie()
    if not refresh_token:
        return (
            jsonify(
                {
                    "ok": False,
                    "msg": "Refresh token required",
                    "code": "REFRESH_REQUIRED",
                }
            ),
            401,
        )

    user = verify_refresh_token(refresh_token)
    if not user:
        response = make_response(
            jsonify(
                {
                    "ok": False,
                    "msg": "Invalid or expired refresh token",
                    "code": "REFRESH_INVALID",
                }
            ),
            401,
        )
        clear_auth_cookies(response)
        return response

    # Create new tokens (rotate refresh token)
    access_token, access_expires = create_access_token(user["id"], user["role"])
    new_refresh_token, refresh_expires = create_refresh_token(user["id"])
    store_tokens(
        user["id"], access_token, access_expires, new_refresh_token, refresh_expires
    )

    response = make_response(jsonify({"ok": True, "msg": "Token refreshed"}))
    set_auth_cookies(response, access_token, new_refresh_token)
    return response


# ── Get Current User ─────────────────────────────────────────


@auth_bp.route("/auth/me", methods=["GET"])
@jwt_required
def me():
    """Get current authenticated user info."""
    return jsonify(
        {
            "ok": True,
            "user": {
                "id": request.current_user["id"],
                "role": request.current_user["role"],
            },
        }
    )


# ── Change password (AJAX) ───────────────────────────────────


@auth_bp.route("/auth/change_password", methods=["POST"])
@jwt_required
def change_password():
    """Change password for logged-in non-admin, non-Google users."""
    if request.current_user.get("role") == "admin":
        return jsonify({"ok": False, "msg": "Admins cannot change password here."}), 403

    current = request.form.get("current") or ""
    new_pw = request.form.get("new") or ""
    new_pw2 = request.form.get("new2") or ""

    if len(new_pw) < 6:
        return jsonify({"ok": False, "msg": "New password must be 6+ characters."}), 400
    if new_pw != new_pw2:
        return jsonify({"ok": False, "msg": "Passwords do not match."}), 400

    db = get_db()
    user = db.execute(
        "SELECT password FROM users WHERE id = ? LIMIT 1", (request.current_user["id"],)
    ).fetchone()
    if not user or not check_password_hash(user["password"], current):
        return jsonify({"ok": False, "msg": "Current password is incorrect."}), 401

    db.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (generate_password_hash(new_pw), request.current_user["id"]),
    )
    db.commit()
    return jsonify({"ok": True, "msg": "Password updated!"})
