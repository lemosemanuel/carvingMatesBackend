import json
from flask import Blueprint, request
from utils.http import ok, created, error
from utils.validators import SkillVideoCreate, SkillAIReviewCreate
from db import get_cur

bp = Blueprint("skills", __name__)

@bp.post("/videos")
def create_video():
    try:
        data = SkillVideoCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO skill_videos (user_id, sport_id, video_url)
            VALUES (%s,%s,%s) RETURNING id
        """, (data.user_id, data.sport_id, data.video_url))
        vid = cur.fetchone()["id"]
    return created({"id": vid})

@bp.post("/ai-reviews")
def create_ai_review():
    try:
        data = SkillAIReviewCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO skill_ai_reviews (skill_video_id, review_data)
            VALUES (%s,%s) RETURNING id
        """, (data.skill_video_id, json.dumps(data.review_data)))
        rid = cur.fetchone()["id"]
    return created({"id": rid})

@bp.get("/videos/<int:user_id>")
def list_user_videos(user_id):
    with get_cur() as cur:
        cur.execute("SELECT * FROM skill_videos WHERE user_id=%s ORDER BY uploaded_at DESC", (user_id,))
        rows = cur.fetchall()
    return ok(rows)