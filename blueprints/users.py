from flask import Blueprint, request
from utils.http import ok, created, error
from utils.validators import CreateUser, UpdateUser, AssignRole, UserSport
from db import get_cur

bp = Blueprint("users", __name__)

@bp.post("")
def create_user():
    try:
        data = CreateUser(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute(
            "INSERT INTO users (full_name, email, password_hash) VALUES (%s,%s,%s) RETURNING id",
            (data.full_name, data.email, data.password_hash)
        )
        uid = cur.fetchone()["id"]
    return created({"id": uid})

@bp.get("")
def list_users():
    with get_cur() as cur:
        cur.execute("SELECT id, full_name, email, created_at FROM users ORDER BY id DESC")
        rows = cur.fetchall()
    return ok(rows)

@bp.get("/<int:user_id>")
def get_user(user_id):
    with get_cur() as cur:
        cur.execute("SELECT id, full_name, email, created_at FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
    if not row:
        return error("User not found", 404)
    return ok(row)

@bp.put("/<int:user_id>")
def update_user(user_id):
    try:
        data = UpdateUser(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    fields, values = [], []
    for k,v in data.model_dump(exclude_unset=True).items():
        fields.append(f"{k}=%s")
        values.append(v)
    if not fields:
        return error("No fields to update")
    values.append(user_id)
    with get_cur(True) as cur:
        cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=%s", tuple(values))
    return ok({"updated": True})

@bp.delete("/<int:user_id>")
def delete_user(user_id):
    with get_cur(True) as cur:
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    return ok({"deleted": True})

@bp.post("/assign-role")
def assign_role():
    try:
        data = AssignRole(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute(
            "INSERT INTO user_role_assignments (user_id, role_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (data.user_id, data.role_id)
        )
    return created({"assigned": True})

@bp.post("/add-sport")
def add_sport():
    try:
        data = UserSport(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute(
            "INSERT INTO user_sports (user_id, sport_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (data.user_id, data.sport_id)
        )
    return created({"linked": True})