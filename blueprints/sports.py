from flask import Blueprint, request
from utils.http import ok, created, error
from utils.validators import CreateSport
from db import get_cur

bp = Blueprint("sports", __name__)

@bp.post("")
def create_sport():
    try:
        data = CreateSport(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("INSERT INTO sports (name) VALUES (%s) RETURNING id", (data.name,))
        sid = cur.fetchone()["id"]
    return created({"id": sid})

@bp.get("")
def list_sports():
    with get_cur() as cur:
        cur.execute("SELECT id, name FROM sports ORDER BY name")
        rows = cur.fetchall()
    return ok(rows)