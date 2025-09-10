# blueprints/auth.py
from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from utils.http import ok, created, error
from db import get_cur
import secrets

bp = Blueprint("auth", __name__)

def _ensure_auth_tokens(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
          token TEXT PRIMARY KEY,
          user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)

def _issue_token(user_id: int) -> str:
    token = secrets.token_hex(32)
    with get_cur(True) as cur:
        _ensure_auth_tokens(cur)  # asegura que exista
        cur.execute("""
            INSERT INTO auth_tokens (token, user_id, created_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (token) DO NOTHING
        """, (token, user_id))
    return token

@bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    full_name = (payload.get("full_name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or payload.get("password_hash") or ""
    current_sports = payload.get("current_sports") or []
    wishlist_sports = payload.get("wishlist_sports") or []

    if not full_name or not email or not password:
        return error("full_name, email y password son obligatorios", 400)

    pw_hash = generate_password_hash(password)

    with get_cur(True) as cur:
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            return error("Email already registered", 409)

        cur.execute("""
            INSERT INTO users (full_name, email, password_hash)
            VALUES (%s,%s,%s) RETURNING id
        """, (full_name, email, pw_hash))
        uid = cur.fetchone()["id"]

        # user_sports (con o sin years_experience)
        def has_years():
            cur.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name='user_sports' AND column_name='years_experience'
                LIMIT 1
            """)
            return cur.fetchone() is not None

        if has_years():
            for item in current_sports:
                sid = int(item.get("sport_id"))
                years = int(item.get("years_experience", 0))
                cur.execute("""
                    INSERT INTO user_sports (user_id, sport_id, years_experience)
                    VALUES (%s,%s,%s) ON CONFLICT DO NOTHING
                """, (uid, sid, years))
        else:
            for item in current_sports:
                sid = int(item.get("sport_id"))
                cur.execute("""
                    INSERT INTO user_sports (user_id, sport_id)
                    VALUES (%s,%s) ON CONFLICT DO NOTHING
                """, (uid, sid))

        # wishlist si existe
        cur.execute("SELECT to_regclass('public.user_wishlist_sports')")
        if cur.fetchone()[0]:
            for sid in wishlist_sports:
                cur.execute("""
                    INSERT INTO user_wishlist_sports (user_id, sport_id)
                    VALUES (%s,%s) ON CONFLICT DO NOTHING
                """, (uid, int(sid)))

    token = _issue_token(uid)
    return created({"token": token, "user": {"id": uid, "full_name": full_name, "email": email}})

@bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        return error("email y password son obligatorios", 400)

    with get_cur() as cur:
        cur.execute("SELECT id, password_hash, full_name, email FROM users WHERE email=%s", (email,))
        row = cur.fetchone()

    if not row or not check_password_hash(row["password_hash"], password):
        return error("Invalid credentials", 401)

    token = _issue_token(row["id"])
    return ok({"token": token, "user": {"id": row["id"], "full_name": row["full_name"], "email": row["email"]}})

@bp.get("/me")
def me():
    auth = request.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return error("Missing bearer token", 401)
    token = auth.split(" ", 1)[1]

    with get_cur() as cur:
        cur.execute("""
            SELECT u.id, u.full_name, u.email, u.created_at
            FROM auth_tokens t
            JOIN users u ON u.id = t.user_id
            WHERE t.token = %s
        """, (token,))
        row = cur.fetchone()

    if not row:
        return error("Invalid token", 401)
    return ok(row)

@bp.post("/logout")
def logout():
    auth = request.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return error("Missing bearer token", 401)
    token = auth.split(" ", 1)[1]
    with get_cur(True) as cur:
        cur.execute("DELETE FROM auth_tokens WHERE token=%s", (token,))
    return ok({"logout": True})
