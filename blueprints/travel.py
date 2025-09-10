from flask import Blueprint, request
from utils.http import ok, created, error
from utils.validators import TravelPlanCreate, TravelMatchCreate
from db import get_cur

bp = Blueprint("travel", __name__)

@bp.post("/plans")
def create_plan():
    try:
        data = TravelPlanCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO travel_plans (user_id, destination, start_date, end_date, sport_id)
            VALUES (%s,%s,%s,%s,%s) RETURNING id
        """, (data.user_id, data.destination, data.start_date, data.end_date, data.sport_id))
        pid = cur.fetchone()["id"]
    return created({"id": pid})

@bp.post("/matches")
def create_match():
    try:
        data = TravelMatchCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO travel_matches (plan_id, matched_user_id) VALUES (%s,%s) RETURNING id
        """, (data.plan_id, data.matched_user_id))
        mid = cur.fetchone()["id"]
    return created({"id": mid})

@bp.get("/plans")
def list_plans():
    with get_cur() as cur:
        cur.execute("""
            SELECT tp.*, u.full_name as owner_name FROM travel_plans tp
            JOIN users u ON u.id = tp.user_id
            ORDER BY tp.start_date DESC
        """)
        rows = cur.fetchall()
    return ok(rows)