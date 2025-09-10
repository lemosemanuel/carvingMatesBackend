# blueprints/trips.py
from flask import Blueprint, request, g
from utils.auth import require_auth
from db import get_conn
from utils.http import ok, created, error
from psycopg2.extras import RealDictCursor
import json
from utils.notify import notify_user  # 👈 usa tu helper existente

trips_bp = Blueprint("trips", __name__)

# -----------------------------
# Helpers
# -----------------------------
def _jsonb_array(value):
    """
    Devuelve un string JSON listo para castear a ::jsonb (siempre array).
    - None -> "[]"
    - list/tuple -> json.dumps(list)
    - str que ya parece JSON array -> se devuelve tal cual
    - otro str -> lo wrapeo como ["str"]
    - cualquier otro -> lo wrapeo como [value]
    """
    if value is None:
        return json.dumps([])
    if isinstance(value, (list, tuple)):
        return json.dumps(list(value))
    if isinstance(value, str):
        s = value.strip()
        if s.startswith('[') and s.endswith(']'):
            return s  # ya es JSON array
        return json.dumps([s])
    # fallback
    return json.dumps([value])

def _opt_int(v):
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        return None

# -----------------------------
# Create Trip
# -----------------------------
@trips_bp.post("")
@require_auth
def create_trip():
    user = g.user
    body = request.get_json(force=True) or {}

    # --- Normalizo fotos ---
    photos = body.get("photos")
    if not isinstance(photos, list):
        photos = []
    legacy_photo = (body.get("photo_url") or "").strip()
    if legacy_photo:
        photos = [legacy_photo] + photos

    fields = [
        "title", "description", "destination", "latitude", "longitude",
        "start_date", "end_date", "budget_min", "budget_max", "includes",
        "sports", "max_people", "gender_requirement", "min_match_to_confirm",
    ]
    data = {k: body.get(k) for k in fields}

    if not data["title"] or not data["destination"] or not data["max_people"]:
        return error("title, destination, max_people are required", 400)

    def _opt_int(v):
        try:
            return None if v is None else int(v)
        except Exception:
            return None

    data["budget_min"] = _opt_int(data.get("budget_min"))
    data["budget_max"] = _opt_int(data.get("budget_max"))
    data["max_people"] = _opt_int(data.get("max_people"))
    if data["max_people"] is None or data["max_people"] < 1:
        return error("max_people must be >= 1", 400)

    def _jsonb_array(value):
        if value is None:
            return json.dumps([])
        if isinstance(value, (list, tuple)):
            return json.dumps(list(value))
        if isinstance(value, str):
            s = value.strip()
            if s.startswith('[') and s.endswith(']'):
                return s
            return json.dumps([s])
        return json.dumps([value])

    includes_json = _jsonb_array(data.get("includes"))
    sports_json   = _jsonb_array(data.get("sports"))
    photos_json   = _jsonb_array(photos)
    photo_url     = legacy_photo or (photos[0] if photos else None)

    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            INSERT INTO trip_plans
            (creator_id, title, description, destination, latitude, longitude,
             start_date, end_date, budget_min, budget_max,
             includes,  sports,  photo_url, photos,
             max_people, current_people, gender_requirement, min_match_to_confirm)
            VALUES (%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,
                    %s::jsonb, %s::jsonb, %s, %s::jsonb,
                    %s,         %s,            %s,                 %s)
            RETURNING *;
        """, (
            user["id"],
            data["title"], data.get("description"), data["destination"],
            data.get("latitude"), data.get("longitude"),
            data.get("start_date"), data.get("end_date"),
            data["budget_min"], data["budget_max"],
            includes_json,   sports_json,   photo_url, photos_json,
            data["max_people"], 1,          data.get("gender_requirement", "any"),
            data.get("min_match_to_confirm", 1),
        ))
        trip = cur.fetchone()

        # Autor como participante creador aprobado
        cur.execute("""
            INSERT INTO trip_participants (trip_id, user_id, role, approved)
            VALUES (%s,%s,'creator',TRUE)
            ON CONFLICT (trip_id, user_id) DO NOTHING;
        """, (trip["id"], user["id"]))

        return created(trip)

# -----------------------------
# Feed (con filtros)
# -----------------------------
@trips_bp.get("")
@require_auth
def list_feed():
    q = request.args
    sport  = q.get("sport")
    dest   = q.get("destination")
    minb   = q.get("min_budget", type=int)
    maxb   = q.get("max_budget", type=int)
    gender = q.get("gender")  # 'any'|'male_only'|'female_only'|'mixed'
    limit  = q.get("limit", type=int) or 30
    offset = q.get("offset", type=int) or 0

    wh = ["t.status = 'open'"]
    vals = []
    if sport:
        # jsonb array de strings soporta el operador '?'
        wh.append("t.sports ? %s")
        vals.append(sport)
    if dest:
        wh.append("t.destination ILIKE %s")
        vals.append(f"%{dest}%")
    if minb is not None:
        wh.append("(t.budget_min IS NULL OR t.budget_min >= %s)")
        vals.append(minb)
    if maxb is not None:
        wh.append("(t.budget_max IS NULL OR t.budget_max <= %s)")
        vals.append(maxb)
    if gender:
        wh.append("t.gender_requirement = %s")
        vals.append(gender)

    where = " AND ".join(wh) if wh else "TRUE"

    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""
            SELECT t.*,
                   COALESCE(AVG(r.rating), 0)::float AS creator_rating,
                   COUNT(DISTINCT r.id)        AS creator_reviews
              FROM trip_plans t
         LEFT JOIN trip_reviews r
                ON r.reviewee_id = t.creator_id
             WHERE {where}
               AND t.current_people < t.max_people
          GROUP BY t.id
          ORDER BY t.created_at DESC
             LIMIT %s OFFSET %s;
        """, (*vals, limit, offset))
        rows = cur.fetchall()
        return ok(rows)

# -----------------------------
# Swipe
# -----------------------------
@trips_bp.post("/<int:trip_id>/swipe")
@require_auth
def swipe_trip(trip_id):
    user = g.user
    body = request.get_json(force=True) or {}
    direction = body.get('direction')  # 1 like, -1 dislike
    if direction not in (1, -1):
        return error("direction must be 1 or -1", 400)

    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT creator_id, title, gender_requirement, max_people, current_people, status
            FROM trip_plans WHERE id=%s
        """, (trip_id,))
        trip = cur.fetchone()
        if not trip or trip['status'] != 'open':
            return error("trip not found or not open", 404)

        # registrar swipe
        cur.execute("""
            INSERT INTO trip_swipes (trip_id, user_id, direction)
            VALUES (%s,%s,%s)
            ON CONFLICT (trip_id, user_id) DO UPDATE SET direction=EXCLUDED.direction
            RETURNING *;
        """, (trip_id, user['id'], direction))
        swipe = cur.fetchone()

        match_made = False
        if direction == 1:
            cur.execute("""
                INSERT INTO trip_participants (trip_id, user_id, role, approved)
                VALUES (%s,%s,'participant',FALSE)
                ON CONFLICT (trip_id, user_id) DO NOTHING
                RETURNING *;
            """, (trip_id, user['id']))
            match_made = cur.fetchone() is not None

            if match_made:
                # 🔔 Notifica al creador: nueva solicitud
                applicant_name = user.get('full_name') or user.get('name') or 'Nuevo rider'
                notify_user(
                    user_id=trip['creator_id'],
                    ntype='trip_join_request',
                    title=f'Solicitud para "{trip["title"]}"',
                    body=f'{applicant_name} quiere unirse a tu viaje.',
                    data={
                        "trip_id": trip_id,
                        "applicant_id": user['id'],
                        "applicant_name": applicant_name
                    }
                )

        return ok({"swipe": swipe, "pending_match": match_made})


# -----------------------------
# Approve participant (solo creador)
# -----------------------------
@trips_bp.put("/<int:trip_id>/participants/<int:user_id>/approve")
@require_auth
def approve_participant(trip_id, user_id):
    user = g.user
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT creator_id, title, current_people, max_people, min_match_to_confirm, status
            FROM trip_plans WHERE id=%s
        """, (trip_id,))
        trip = cur.fetchone()
        if not trip: return error("trip not found", 404)
        if trip['creator_id'] != user['id']: return error("only creator can approve", 403)
        if trip['status'] != 'open': return error("trip is not open", 400)

        cur.execute("""
            UPDATE trip_participants
               SET approved=TRUE
             WHERE trip_id=%s AND user_id=%s AND role='participant'
             RETURNING *;
        """, (trip_id, user_id))
        part = cur.fetchone()
        if not part: return error("participant not found or already approved", 404)

        cur.execute("""
            UPDATE trip_plans
               SET current_people = current_people + 1,
                   updated_at = NOW()
             WHERE id=%s
             RETURNING *;
        """, (trip_id,))
        updated_trip = cur.fetchone()

        if updated_trip['current_people'] >= updated_trip['min_match_to_confirm']:
            cur.execute("""
                UPDATE trip_plans SET status='confirmed'
                WHERE id=%s AND status='open'
                RETURNING *;
            """, (trip_id,))
            maybe_conf = cur.fetchone()
            if maybe_conf:
                updated_trip = maybe_conf

        # 🔔 Notifica al solicitante
        notify_user(
            user_id=user_id,
            ntype='trip_request_approved',
            title='¡Solicitud aprobada!',
            body=f'Te aceptaron en "{trip["title"]}".',
            data={"trip_id": trip_id, "by_creator_id": user['id']}
        )

        return ok({"participant": part, "trip": updated_trip})

@trips_bp.put("/<int:trip_id>/participants/<int:user_id>/reject")
@require_auth
def reject_participant(trip_id, user_id):
    user = g.user
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT creator_id, title, status FROM trip_plans WHERE id=%s", (trip_id,))
        trip = cur.fetchone()
        if not trip: return error("trip not found", 404)
        if trip['creator_id'] != user['id']: return error("only creator can reject", 403)
        if trip['status'] != 'open': return error("trip is not open", 400)

        cur.execute("""
            DELETE FROM trip_participants
            WHERE trip_id=%s AND user_id=%s AND role='participant' AND approved=FALSE
            RETURNING user_id;
        """, (trip_id, user_id))
        deleted = cur.fetchone()
        if not deleted:
            return error("pending request not found", 404)

        # opcional: grabar swipe -1 para no re-sugerir
        cur.execute("""
            INSERT INTO trip_swipes (trip_id, user_id, direction)
            VALUES (%s,%s,-1)
            ON CONFLICT (trip_id, user_id) DO UPDATE SET direction=-1;
        """, (trip_id, user_id))

        # 🔔 Notifica al solicitante
        notify_user(
            user_id=user_id,
            ntype='trip_request_rejected',
            title='Solicitud rechazada',
            body=f'Tu solicitud para "{trip["title"]}" fue rechazada.',
            data={"trip_id": trip_id, "by_creator_id": user['id']}
        )

        return ok({"rejected_user_id": user_id})



# -----------------------------
# Review
# -----------------------------
@trips_bp.post("/<int:trip_id>/reviews")
@require_auth
def review_trip(trip_id):
    user = g.user
    body = request.get_json(force=True) or {}
    rating = _opt_int(body.get("rating")) or 0
    comment = body.get("comment")
    if rating < 1 or rating > 5:
        return error("rating must be 1..5", 400)

    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT creator_id, status
              FROM trip_plans
             WHERE id = %s;
        """, (trip_id,))
        trip = cur.fetchone()
        if not trip:
            return error("trip not found", 404)

        # chequear que el usuario haya sido aprobado
        cur.execute("""
            SELECT 1
              FROM trip_participants
             WHERE trip_id = %s AND user_id = %s AND approved = TRUE
             LIMIT 1;
        """, (trip_id, user["id"]))
        if not cur.fetchone():
            return error("only approved participants can review", 403)

        cur.execute("""
            INSERT INTO trip_reviews (trip_id, reviewer_id, reviewee_id, rating, comment)
            VALUES (%s, %s, %s, %s, %s)
        RETURNING *;
        """, (trip_id, user["id"], trip["creator_id"], rating, comment))
        return created(cur.fetchone())


@trips_bp.get("/<int:trip_id>/requests")
@require_auth
def list_requests(trip_id):
    user = g.user
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT creator_id FROM trip_plans WHERE id=%s", (trip_id,))
        t = cur.fetchone()
        if not t: 
            return error("trip not found", 404)
        if t['creator_id'] != user['id']:
            return error("only creator can see requests", 403)

        cur.execute("""
            SELECT p.user_id, u.full_name, u.email, u.bio, u.avatar_url,
                   u.gender, u.city, u.country,
                   COALESCE(avg(r.rating),0)::float AS rating,
                   COUNT(DISTINCT r.id) AS reviews
            FROM trip_participants p
            JOIN users u ON u.id = p.user_id
            LEFT JOIN trip_reviews r ON r.reviewee_id = u.id
            WHERE p.trip_id=%s AND p.role='participant' AND p.approved=FALSE
            GROUP BY p.user_id, u.full_name, u.email, u.bio, u.avatar_url, u.gender, u.city, u.country
            ORDER BY rating DESC, reviews DESC;
        """, (trip_id,))
        rows = cur.fetchall()
        return ok(rows)
