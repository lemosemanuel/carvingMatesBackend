from flask import Blueprint, request
from utils.http import ok, created, error
from utils.validators import CreateRole
from db import get_cur

bp = Blueprint("roles", __name__)

@bp.post("")
def create_role():
    try:
        data = CreateRole(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("INSERT INTO user_roles (name) VALUES (%s) RETURNING id", (data.name,))
        rid = cur.fetchone()["id"]
    return created({"id": rid})

@bp.get("")
def list_roles():
    with get_cur() as cur:
        cur.execute("SELECT id, name FROM user_roles ORDER BY id")
        rows = cur.fetchall()
    return ok(rows)