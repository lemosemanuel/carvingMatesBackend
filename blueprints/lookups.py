# blueprints/lookups.py
from flask import Blueprint
from utils.http import ok
from db import get_cur

bp = Blueprint("lookups", __name__)

@bp.get("/equipment_status")
def list_equipment_status():
    with get_cur() as cur:
        cur.execute("""
            SELECT id, status_name
            FROM equipment_status
            ORDER BY id ASC
        """)
        rows = cur.fetchall()
    return ok(rows)
