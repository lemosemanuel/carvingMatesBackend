from flask import Blueprint, request
from utils.http import ok, created, error
from utils.validators import CoachApplicationCreate, CoachReviewCreate
from db import get_cur

bp = Blueprint("coaching", __name__)

@bp.post("/applications")
def create_application():
    try:
        data = CoachApplicationCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO coach_applications (skill_video_id, coach_id, price, experience, status)
            VALUES (%s,%s,%s,%s,%s) RETURNING id
        """, (data.skill_video_id, data.coach_id, data.price, data.experience, data.status))
        aid = cur.fetchone()["id"]
    return created({"id": aid})

@bp.put("/applications/<int:app_id>/status")
def update_application_status(app_id):
    status = request.json.get("status")
    if status not in ("pending", "accepted", "rejected"):
        return error("Invalid status")
    with get_cur(True) as cur:
        cur.execute("UPDATE coach_applications SET status=%s WHERE id=%s", (status, app_id))
    return ok({"updated": True})

@bp.get("/applications")
def list_applications():
    video_id = request.args.get("skill_video_id")
    with get_cur() as cur:
        if video_id:
            cur.execute("SELECT * FROM coach_applications WHERE skill_video_id=%s ORDER BY id DESC", (video_id,))
        else:
            cur.execute("SELECT * FROM coach_applications ORDER BY id DESC")
        rows = cur.fetchall()
    return ok(rows)

@bp.post("/reviews")
def create_coach_review():
    try:
        data = CoachReviewCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO coach_reviews (coach_id, reviewer_id, rating, comment)
            VALUES (%s,%s,%s,%s) RETURNING id
        """, (data.coach_id, data.reviewer_id, data.rating, data.comment))
        rid = cur.fetchone()["id"]
    return created({"id": rid})