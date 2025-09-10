# blueprints/auth_helpers.py
from db import get_cur
from utils.http import error

def get_user_id_from_bearer(request):
    auth = request.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None, error("Missing bearer token", 401)
    token = auth.split(" ", 1)[1]
    with get_cur() as cur:
        cur.execute("""
            SELECT u.id
            FROM auth_tokens t
            JOIN users u ON u.id = t.user_id
            WHERE t.token = %s
        """, (token,))
        row = cur.fetchone()
    if not row:
        return None, error("Invalid token", 401)
    return row["id"], None
