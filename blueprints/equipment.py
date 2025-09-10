# blueprints/equipment.py
from flask import Blueprint, request, jsonify
from utils.http import ok, created, error
from db import get_cur
from blueprints.auth_helpers import get_user_id_from_bearer
from utils.validators import UpdateEquipment  # si lo usás

bp = Blueprint("equipment", __name__)

@bp.post("")
def create_equipment():
    owner_id, err = get_user_id_from_bearer(request)
    if err:
        return err

    p = request.get_json(silent=True) or {}
    sport_id = p.get("sport_id")
    title = (p.get("title") or "").strip()
    description = p.get("description")
    size = p.get("size")
    condition_id = p.get("condition_id")
    latitude = p.get("latitude")
    longitude = p.get("longitude")
    images = p.get("images") or []
    availability = p.get("availability")

    if not sport_id or not title or not condition_id:
        return error("sport_id, title y condition_id son obligatorios", 400)

    with get_cur(True) as cur:
        cur.execute("SELECT 1 FROM sports WHERE id=%s", (sport_id,))
        if not cur.fetchone():
            return error("Invalid sport_id", 400)

        cur.execute("SELECT 1 FROM equipment_status WHERE id=%s", (condition_id,))
        if not cur.fetchone():
            return error("Invalid condition_id", 400)

        cur.execute("""
            INSERT INTO equipment
              (owner_id, sport_id, title, description, size, condition_id, latitude, longitude)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (owner_id, sport_id, title, description, size, condition_id, latitude, longitude))
        eid = cur.fetchone()["id"]

        for url in images:
            cur.execute("""
                INSERT INTO equipment_images (equipment_id, image_url)
                VALUES (%s,%s)
            """, (eid, url))

        def _insert_range(r):
            sd = r.get("start_date")
            ed = r.get("end_date")
            if not sd or not ed:
                return
            cur.execute("""
                INSERT INTO equipment_availability (equipment_id, start_date, end_date, kind)
                VALUES (%s, %s::date, %s::date, 'available')
            """, (eid, sd, ed))

        if isinstance(availability, dict):
            _insert_range(availability)
        elif isinstance(availability, list):
            for r in availability:
                if isinstance(r, dict):
                    _insert_range(r)

    return created({"id": eid})

@bp.get("")
def search_equipment():
    q = request.args.get("q")
    sport_id = request.args.get("sport_id", type=int)
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    radius_km = request.args.get("radius_km", type=float)
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = max(1, request.args.get("page", default=1, type=int))
    page_size = max(1, min(50, request.args.get("page_size", default=20, type=int)))

    conds, params = [], {}

    if q:
        conds.append("(e.title ILIKE %(q)s OR e.description ILIKE %(q)s OR e.size ILIKE %(q)s)")
        params["q"] = f"%{q}%"

    if sport_id:
        conds.append("e.sport_id = %(sport_id)s")
        params["sport_id"] = sport_id

    date_filter_sql = ""
    if start_date and end_date:
        date_filter_sql = """
            AND EXISTS (
                SELECT 1
                FROM equipment_availability a
                WHERE a.equipment_id = e.id
                  AND COALESCE(a.kind, 'available') = 'available'
                  AND a.start_date <= %(start_date)s::date
                  AND a.end_date   >= %(end_date)s::date
            )
            AND NOT EXISTS (
                SELECT 1
                FROM equipment_bookings b
                WHERE b.equipment_id = e.id
                  AND b.status IS DISTINCT FROM 'cancelled'
                  AND %(start_date)s::date <= b.end_date
                  AND %(end_date)s::date   >= b.start_date
            )
        """
        params["start_date"] = start_date
        params["end_date"] = end_date

    distance_expr = None
    distance_select = "NULL AS distance_km"
    distance_where = ""
    order_sql = " ORDER BY e.created_at DESC "

    if lat is not None and lng is not None and radius_km is not None:
        distance_expr = """
            (6371 * acos(
                cos(radians(%(lat)s)) * cos(radians(e.latitude)) *
                cos(radians(e.longitude) - radians(%(lng)s)) +
                sin(radians(%(lat)s)) * sin(radians(e.latitude))
            ))
        """
        params["lat"] = lat
        params["lng"] = lng

        conds.append("(e.latitude IS NOT NULL AND e.longitude IS NOT NULL)")

        distance_select = f"{distance_expr} AS distance_km"
        distance_where = f" AND {distance_expr} <= %(radius_km)s "
        params["radius_km"] = radius_km

        order_sql = " ORDER BY distance_km ASC, e.created_at DESC "

    where_sql = ("WHERE " + " AND ".join(conds)) if conds else ""
    limit_sql = " LIMIT %(limit)s OFFSET %(offset)s "
    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size

    sql = f"""
        SELECT
            e.id, e.title, e.description, e.size, e.sport_id,
            e.latitude, e.longitude, e.created_at,
            COALESCE(img.image_url, NULL) AS image_url,
            {distance_select}
        FROM equipment e
        LEFT JOIN LATERAL (
            SELECT image_url
            FROM equipment_images
            WHERE equipment_id = e.id
            ORDER BY id ASC
            LIMIT 1
        ) img ON TRUE
        {where_sql}
        {date_filter_sql}
        {distance_where}
        {order_sql}
        {limit_sql}
    """

    with get_cur() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return ok(rows)

@bp.get("/<int:eid>")
def get_equipment(eid):
    with get_cur() as cur:
        cur.execute("SELECT * FROM equipment WHERE id=%s", (eid,))
        row = cur.fetchone()
    if not row:
        return error("Equipment not found", 404)
    return ok(row)

@bp.put("/<int:eid>")
def update_equipment(eid):
    try:
        data = UpdateEquipment(**(request.get_json(silent=True) or {}))
    except Exception as e:
        return error("Invalid payload", details=str(e))
    fields, values = [], []
    for k, v in data.__dict__.items():
        if v is not None:
            fields.append(f"{k}=%s")
            values.append(v)
    if not fields:
        return error("No fields to update")
    values.append(eid)
    with get_cur(True) as cur:
        cur.execute(f"UPDATE equipment SET {', '.join(fields)} WHERE id=%s", tuple(values))
    return ok({"updated": True})

@bp.get("/<int:eid>/detail")
def equipment_detail(eid):
    with get_cur() as cur:
        cur.execute("""
            SELECT e.*, img.image_url
            FROM equipment e
            LEFT JOIN LATERAL (
                SELECT image_url FROM equipment_images
                WHERE equipment_id = e.id
                ORDER BY id ASC LIMIT 1
            ) img ON TRUE
            WHERE e.id=%s
        """, (eid,))
        eq = cur.fetchone()
        if not eq:
            return error("Equipment not found", 404)

        cur.execute("""
            SELECT id, image_url
            FROM equipment_images
            WHERE equipment_id=%s
            ORDER BY id ASC
        """, (eid,))
        images = cur.fetchall()

        cur.execute("""
            SELECT id, start_date, end_date
            FROM equipment_availability
            WHERE equipment_id=%s AND COALESCE(kind,'available')='available'
            ORDER BY start_date ASC
        """, (eid,))
        availability = cur.fetchall()

        cur.execute("""
            SELECT id, start_date, end_date, status
            FROM equipment_bookings
            WHERE equipment_id=%s AND status='approved'
            ORDER BY start_date ASC
        """, (eid,))
        approved = cur.fetchall()

        cur.execute("""
            SELECT r.id, r.rating, r.comment, r.created_at,
                   u.full_name AS reviewer_name
            FROM equipment_reviews r
            LEFT JOIN users u ON u.id = r.reviewer_id
            WHERE r.equipment_id=%s
            ORDER BY r.created_at DESC
            LIMIT 50
        """, (eid,))
        reviews = cur.fetchall()

        cur.execute("""
            SELECT COALESCE(AVG(rating),0) AS avg_rating,
                   COUNT(*) AS total
            FROM equipment_reviews
            WHERE equipment_id=%s
        """, (eid,))
        agg = cur.fetchone()

    return ok({
        "equipment": eq,
        "images": images,
        "availability": availability,
        "approved_bookings": approved,
        "reviews": reviews,
        "reviews_summary": agg
    })

@bp.get("/<int:eq_id>/calendar")
def equipment_calendar(eq_id):
    start_s = request.args.get("start")
    end_s   = request.args.get("end")
    debug   = request.args.get("debug") in ("1", "true", "yes")

    # Construimos SQL con un bloque de debug opcional
    debug_cte = """
    , booked_debug AS (
        SELECT d.d::text AS day_txt, eb.id,
               lower(trim(eb.status::text)) AS status,
               eb.start_date::text AS s, eb.end_date::text AS e
        FROM days d
        JOIN equipment_bookings eb
          ON eb.equipment_id = %s
         AND d.d >= eb.start_date
         AND d.d <  eb.end_date
    )
    """ if debug else ""

    debug_select = """,
      COALESCE((SELECT array_agg(
        day_txt || ' #id=' || id::text || ' ' || status || ' [' || s || '→' || e || ']'
      ) FROM booked_debug), ARRAY[]::text[]) AS _debug_rows
    """ if debug else ""

    sql = f"""
    WITH bounds AS (
      SELECT
        COALESCE(%s::date, CURRENT_DATE) AS start_date,
        COALESCE(%s::date, CURRENT_DATE + INTERVAL '90 days')::date AS end_date
    ),
    days AS (
      SELECT generate_series(b.start_date, b.end_date - INTERVAL '1 day', INTERVAL '1 day')::date AS d
      FROM bounds b
    ),
    -- Si querés "todo disponible salvo bloqueos", cambia este CTE por:  SELECT d.d FROM days d
    avail AS (
      SELECT d.d
      FROM days d
      JOIN equipment_availability ea
        ON ea.equipment_id = %s
       AND d.d >= ea.start_date
       AND d.d <  ea.end_date
      GROUP BY d.d
    ),
    booked_blocking AS (
      SELECT d.d
      FROM days d
      JOIN equipment_bookings eb
        ON eb.equipment_id = %s
       AND lower(trim(eb.status::text)) IN ('approved','handoff','in_use','returning')
       AND d.d >= eb.start_date
       AND d.d <  eb.end_date
      GROUP BY d.d
    ),
    pending_holds AS (
      SELECT d.d
      FROM days d
      JOIN equipment_bookings eb
        ON eb.equipment_id = %s
       AND lower(trim(eb.status::text)) = 'pending'
       AND d.d >= eb.start_date
       AND d.d <  eb.end_date
      GROUP BY d.d
    ),
    free_days AS (
      SELECT a.d
      FROM avail a
      LEFT JOIN booked_blocking b ON b.d = a.d
      WHERE b.d IS NULL
      ORDER BY a.d
    )
    {debug_cte}
    SELECT
      COALESCE((SELECT array_agg(f.d::text) FROM free_days f), ARRAY[]::text[])       AS available_days,
      COALESCE((SELECT array_agg(b.d::text) FROM booked_blocking b), ARRAY[]::text[]) AS booked_days,
      COALESCE((SELECT array_agg(p.d::text) FROM pending_holds p), ARRAY[]::text[])   AS pending_days
      {debug_select}
    ;
    """

    # Parámetros (si hay debug, se usa eq_id una vez más para booked_debug)
    params = [start_s, end_s, eq_id, eq_id, eq_id]
    if debug:
        params.append(eq_id)

    with get_cur() as cur:
      cur.execute(sql, tuple(params))
      row = cur.fetchone() or {}
    print('asdasd')
    print({
        "version": "calendar_v3_trim_lower",
        "equipment_id": eq_id,
        "start": start_s,
        "end": end_s,
        "available_days": row.get("available_days", []),
        "booked_days": row.get("booked_days", []),
        "pending_days": row.get("pending_days", [])
    })

    return jsonify({
        "version": "calendar_v3_trim_lower",
        "equipment_id": eq_id,
        "start": start_s,
        "end": end_s,
        "available_days": row.get("available_days", []),
        "booked_days": row.get("booked_days", []),
        "pending_days": row.get("pending_days", []),
        **({"_debug_rows": row.get("_debug_rows", [])} if debug else {}),
    })
