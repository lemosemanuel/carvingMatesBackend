# blueprints/bookings.py
from flask import Blueprint, request, jsonify
from utils.http import ok, created, error
from db import get_cur
from blueprints.auth_helpers import get_user_id_from_bearer
from utils.notify import notify_user

bp = Blueprint("bookings", __name__)

# Estados que BLOQUEAN disponibilidad real (bloquean el calendario)
BLOCKING_STATUSES = ('approved', 'handoff', 'in_use', 'returning')

@bp.post("/bookings")
def create_booking():
    """
    Crea 'pending'.
    - Chequea que exista el equipo.
    - Chequea que el rango esté cubierto por availability declarada.
    - NO bloquea por otras 'pending'; solo falla si solapa con booking bloqueante.
    """
    renter_id, err = get_user_id_from_bearer(request)
    if err:
        return err

    p = request.get_json(silent=True) or {}
    equipment_id   = p.get("equipment_id")
    start_date     = p.get("start_date")   # "YYYY-MM-DD" (inclusive)
    end_date       = p.get("end_date")     # "YYYY-MM-DD" (exclusive)
    deposit_amount = p.get("deposit_amount")

    if not equipment_id or not start_date or not end_date:
        return error("equipment_id, start_date, end_date are required", 400)

    with get_cur(True) as cur:
        # validar equipo
        cur.execute("SELECT 1 FROM equipment WHERE id=%s", (equipment_id,))
        if not cur.fetchone():
            return error("Invalid equipment_id", 400)

        # ✅ Rango CUBIERTO por availability declarada
        cur.execute("""
            SELECT 1
            FROM equipment_availability a
            WHERE a.equipment_id = %s
              AND COALESCE(a.kind, 'available') = 'available'
              AND a.start_date <= %s::date
              AND a.end_date   >= %s::date
            LIMIT 1
        """, (equipment_id, start_date, end_date))
        if not cur.fetchone():
            return error("Requested dates are outside declared availability", 409)

        # ✅ Solape contra bookings bloqueantes
        cur.execute("""
            SELECT 1
            FROM equipment_bookings b
            WHERE b.equipment_id = %s
              AND b.status IN ('approved','handoff','in_use','returning')
              AND %s::date < b.end_date
              AND %s::date > b.start_date
            LIMIT 1
        """, (equipment_id, start_date, end_date))
        if cur.fetchone():
            return error("Overlaps with an existing approved/active booking", 409)

        # crear pending
        cur.execute("""
            INSERT INTO equipment_bookings
                (equipment_id, renter_id, start_date, end_date, status, deposit_amount)
            VALUES (%s, %s, %s::date, %s::date, 'pending', %s)
            RETURNING id, status
        """, (equipment_id, renter_id, start_date, end_date, deposit_amount))
        row = cur.fetchone()

    return created({"booking_id": row["id"], "status": row["status"]})


@bp.get("/bookings/owner/requests")
def owner_requests():
    owner_id, err = get_user_id_from_bearer(request)
    if err:
        return err

    with get_cur() as cur:
        cur.execute("""
            SELECT
                b.id          AS booking_id,
                b.equipment_id,
                e.title       AS equipment_title,
                b.start_date,
                b.end_date,
                b.status,
                u.full_name   AS renter_name,
                u.email       AS renter_email
            FROM equipment_bookings b
            JOIN equipment e ON e.id = b.equipment_id
            LEFT JOIN users u ON u.id = b.renter_id
            WHERE e.owner_id = %s
              AND b.status = 'pending'
            ORDER BY b.start_date ASC
        """, (owner_id,))
        rows = cur.fetchall()

    return ok(rows)


@bp.put("/bookings/<int:booking_id>/status")
def set_booking_status(booking_id):
    owner_id, err = get_user_id_from_bearer(request)
    if err:
        return err

    p = request.get_json(silent=True) or {}
    new_status = (p.get("status") or "").strip().lower()
    if new_status not in ("approved", "rejected"):
        return jsonify({"error": "status must be 'approved' or 'rejected'"}), 400

    with get_cur(True) as cur:
        # Traemos la booking y validamos ownership
        cur.execute("""
            SELECT b.id, b.equipment_id, b.renter_id, b.start_date, b.end_date, b.status,
                   e.title, e.owner_id
            FROM equipment_bookings b
            JOIN equipment e ON e.id = b.equipment_id
            WHERE b.id=%s
            FOR UPDATE
        """, (booking_id,))
        bk = cur.fetchone()
        if not bk:
            return jsonify({"error": "booking not found"}), 404
        if bk["owner_id"] != owner_id:
            return jsonify({"error": "forbidden"}), 403

        # Si vamos a aprobar, validamos que no se solape con otra aprobada/bloqueante
        if new_status == "approved":
            cur.execute("""
                SELECT 1
                FROM equipment_bookings eb
                WHERE eb.equipment_id = %s
                  AND eb.id <> %s
                  AND eb.status = ANY(%s)
                  AND daterange(eb.start_date, eb.end_date, '[)') && daterange(%s, %s, '[)')
                LIMIT 1
            """, (bk["equipment_id"], booking_id, list(BLOCKING_STATUSES), bk["start_date"], bk["end_date"]))
            if cur.fetchone():
                return jsonify({"error": "overlap"},), 409

        # Actualizamos estado
        cur.execute("""
            UPDATE equipment_bookings
               SET status=%s
             WHERE id=%s
            RETURNING id
        """, (new_status, booking_id))

    # Notificamos al renter
    title_ok = "✅ Solicitud aprobada"
    body_ok  = f"Tu solicitud para '{bk['title']}' del {bk['start_date']} al {bk['end_date']} fue aprobada."
    title_no = "❌ Solicitud rechazada"
    body_no  = f"Tu solicitud para '{bk['title']}' del {bk['start_date']} al {bk['end_date']} fue rechazada."

    notify_user(
        user_id=bk["renter_id"],
        ntype=f"booking_{new_status}",
        title=title_ok if new_status=="approved" else title_no,
        body= body_ok  if new_status=="approved" else body_no,
        data={
            "booking_id": booking_id,
            "equipment_id": bk["equipment_id"],
            "title": bk["title"],
            "start_date": str(bk["start_date"]),
            "end_date": str(bk["end_date"]),
            "status": new_status,
        }
    )

    return jsonify({"ok": True, "status": new_status})


@bp.get("/equipment/mine")
def my_equipment():
    owner_id, err = get_user_id_from_bearer(request)
    if err:
        return err
    with get_cur() as cur:
        cur.execute("""
            SELECT
              e.id, e.title, e.description, e.size, e.sport_id,
              e.latitude, e.longitude, e.created_at,
              COALESCE(img.image_url, NULL) AS image_url
            FROM equipment e
            LEFT JOIN LATERAL (
              SELECT image_url
              FROM equipment_images
              WHERE equipment_id = e.id
              ORDER BY id ASC
              LIMIT 1
            ) img ON TRUE
            WHERE e.owner_id = %s
            ORDER BY e.created_at DESC
        """, (owner_id,))
        rows = cur.fetchall()
    return ok(rows)
