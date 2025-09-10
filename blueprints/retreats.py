from flask import Blueprint, request
from utils.http import ok, created, error
from utils.validators import RetreatCreate, RetreatApplicationCreate, RetreatReviewCreate
from db import get_cur

bp = Blueprint("retreats", __name__)

@bp.post("")
def create_retreat():
    try:
        data = RetreatCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO retreats (host_id, title, description, location, start_date, end_date, sport_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (data.host_id, data.title, data.description, data.location, data.start_date, data.end_date, data.sport_id))
        rid = cur.fetchone()["id"]
    return created({"id": rid})

@bp.post("/applications")
def apply_retreat():
    try:
        data = RetreatApplicationCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO retreat_applications (retreat_id, applicant_id, status)
            VALUES (%s,%s,%s) RETURNING id
        """, (data.retreat_id, data.applicant_id, data.status))
        aid = cur.fetchone()["id"]
    return created({"id": aid})

@bp.post("/reviews")
def review_retreat():
    try:
        data = RetreatReviewCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO retreat_reviews (retreat_id, reviewer_id, rating, comment)
            VALUES (%s,%s,%s,%s) RETURNING id
        """, (data.retreat_id, data.reviewer_id, data.rating, data.comment))
        rid = cur.fetchone()["id"]
    return created({"id": rid})

@bp.get("")
def list_retreats():
    with get_cur() as cur:
        cur.execute("""
            SELECT r.*, u.full_name as host_name FROM retreats r
            JOIN users u ON u.id = r.host_id
            ORDER BY r.start_date DESC
        """)
        rows = cur.fetchall()
    return ok(rows)