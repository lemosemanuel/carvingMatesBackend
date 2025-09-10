# utils/auth.py
from functools import wraps
from flask import request, g
from psycopg2.extras import RealDictCursor
from db import get_conn
from utils.http import error

def _extract_bearer_token() -> str | None:
    """
    Devuelve el token de Authorization, o None si no viene/está mal formado.
    Acepta: 'Bearer abc123' (case-insensitive en 'Bearer').
    """
    auth = request.headers.get("Authorization", "") or request.headers.get("authorization", "")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2:
        return None
    scheme, token = parts[0], parts[1]
    if scheme.lower() != "bearer":
        return None
    return token.strip() or None

def _load_user_by_token(token: str):
    """
    Carga usuario por token. Si la tabla auth_tokens no tiene columnas
    'revoked' o 'expires_at', omite esos checks de forma segura.
    """
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Descubrir columnas disponibles
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'auth_tokens'
        """)
        cols = {r['column_name'] for r in cur.fetchall()}
        has_revoked = 'revoked' in cols
        has_expires = 'expires_at' in cols

        base = """
            SELECT u.*
            FROM auth_tokens t
            JOIN users u ON u.id = t.user_id
            WHERE t.token = %s
        """
        filters = []
        if has_revoked:
            filters.append("COALESCE(t.revoked, FALSE) = FALSE")
        if has_expires:
            filters.append("(t.expires_at IS NULL OR t.expires_at > NOW())")

        where_extra = ""
        if filters:
            where_extra = " AND " + " AND ".join(filters)

        query = base + where_extra + " LIMIT 1;"

        cur.execute(query, (token,))
        return cur.fetchone()   

def require_auth(fn):
    """
    Decorador para endpoints que requieren login.
    - Coloca el usuario en g.user
    - Retorna 401 si no hay token o no es válido
    Uso:
        @blueprint.get("/algo")
        @require_auth
        def endpoint():
            user = g.user
            ...
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return error("Unauthorized: missing bearer token", 401)
        user = _load_user_by_token(token)
        if not user:
            return error("Unauthorized: invalid token", 401)
        g.user = user
        return fn(*args, **kwargs)
    return wrapper

def require_role(*roles):
    """
    Decorador adicional (opcional) para chequear roles.
    Asume relación users -> user_role_assignments(user_id, role_id) -> user_roles(id, name)
    Ajusta el SQL si tu esquema difiere.
    """
    def inner(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = _extract_bearer_token()
            if not token:
                return error("Unauthorized: missing bearer token", 401)
            user = _load_user_by_token(token)
            if not user:
                return error("Unauthorized: invalid token", 401)
            # chequear roles si se pasaron
            if roles:
                with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT r.name
                        FROM user_role_assignments a
                        JOIN user_roles r ON r.id = a.role_id
                        WHERE a.user_id = %s
                    """, (user["id"],))
                    user_roles = {row["name"] for row in cur.fetchall()}
                if not any(r in user_roles for r in roles):
                    return error("Forbidden: missing required role", 403)
            g.user = user
            return fn(*args, **kwargs)
        return wrapper
    return inner

def optional_auth(fn):
    """
    Si hay token válido, setea g.user; si no, sigue como anónimo (g.user = None).
    Útil para endpoints públicos con personalización si hay sesión.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token()
        g.user = None
        if token:
            user = _load_user_by_token(token)
            if user:
                g.user = user
        return fn(*args, **kwargs)
    return wrapper
