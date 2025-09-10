from flask import Blueprint, request
from utils.http import ok, created, error
from utils.validators import SchoolCreate, SchoolProfessorAssign, ProfessorAvailabilityCreate, StudentProfileCreate
from db import get_cur

bp = Blueprint("schools", __name__)

@bp.post("")
def create_school():
    try:
        data = SchoolCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO schools (owner_id, name, description, latitude, longitude)
            VALUES (%s,%s,%s,%s,%s) RETURNING id
        """, (data.owner_id, data.name, data.description, data.latitude, data.longitude))
        sid = cur.fetchone()["id"]
    return created({"id": sid})

@bp.post("/assign-professor")
def assign_professor():
    try:
        data = SchoolProfessorAssign(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO school_professors (school_id, professor_id)
            VALUES (%s,%s) ON CONFLICT DO NOTHING
        """, (data.school_id, data.professor_id))
    return created({"assigned": True})

@bp.post("/availability")
def add_availability():
    try:
        data = ProfessorAvailabilityCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO professor_availability (professor_id, day_of_week, start_time, end_time, location)
            VALUES (%s,%s,%s,%s,%s) RETURNING id
        """, (data.professor_id, data.day_of_week, data.start_time, data.end_time, data.location))
        aid = cur.fetchone()["id"]
    return created({"id": aid})

@bp.get("/availability/<int:professor_id>")
def list_availability(professor_id):
    with get_cur() as cur:
        cur.execute("SELECT * FROM professor_availability WHERE professor_id=%s ORDER BY day_of_week, start_time", (professor_id,))
        rows = cur.fetchall()
    return ok(rows)

@bp.post("/student-profiles")
def create_student_profile():
    try:
        data = StudentProfileCreate(**request.json)
    except Exception as e:
        return error("Invalid payload", details=str(e))
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO student_profiles (student_id, sport_id, notes)
            VALUES (%s,%s,%s) RETURNING id
        """, (data.student_id, data.sport_id, data.notes))
        pid = cur.fetchone()["id"]
    return created({"id": pid})

@bp.get("/schools-with-professors")
def schools_with_professors():
    with get_cur() as cur:
        cur.execute("""
            SELECT s.id as school_id, s.name as school, u.id as professor_id, u.full_name as professor
            FROM school_professors sp
            JOIN schools s ON sp.school_id = s.id
            JOIN users u ON sp.professor_id = u.id
            ORDER BY s.name, u.full_name
        """)
        rows = cur.fetchall()
    return ok(rows)