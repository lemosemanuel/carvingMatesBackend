# # blueprints/equipment_calendar.py
# from flask import Blueprint, request, jsonify
# from db import get_cur

# bp = Blueprint("equipment_calendar", __name__)

# # Estados que SÍ bloquean (NO 'pending')
# BLOCKING_STATUSES = ("approved", "handoff", "in_use", "returning")

# @bp.get("/equipment/<int:eq_id>/calendar")
# def equipment_calendar(eq_id):
#     start_s = request.args.get("start")
#     end_s   = request.args.get("end")
#     debug   = request.args.get("debug") in ("1", "true", "yes")

#     # Construimos SQL con un bloque de debug opcional
#     debug_cte = """
#     , booked_debug AS (
#         SELECT d.d::text AS day_txt, eb.id,
#                lower(trim(eb.status::text)) AS status,
#                eb.start_date::text AS s, eb.end_date::text AS e
#         FROM days d
#         JOIN equipment_bookings eb
#           ON eb.equipment_id = %s
#          AND d.d >= eb.start_date
#          AND d.d <  eb.end_date
#     )
#     """ if debug else ""

#     debug_select = """,
#       COALESCE((SELECT array_agg(
#         day_txt || ' #id=' || id::text || ' ' || status || ' [' || s || '→' || e || ']'
#       ) FROM booked_debug), ARRAY[]::text[]) AS _debug_rows
#     """ if debug else ""

#     sql = f"""
#     WITH bounds AS (
#       SELECT
#         COALESCE(%s::date, CURRENT_DATE) AS start_date,
#         COALESCE(%s::date, CURRENT_DATE + INTERVAL '90 days')::date AS end_date
#     ),
#     days AS (
#       SELECT generate_series(b.start_date, b.end_date - INTERVAL '1 day', INTERVAL '1 day')::date AS d
#       FROM bounds b
#     ),
#     -- Si querés "todo disponible salvo bloqueos", cambia este CTE por:  SELECT d.d FROM days d
#     avail AS (
#       SELECT d.d
#       FROM days d
#       JOIN equipment_availability ea
#         ON ea.equipment_id = %s
#        AND d.d >= ea.start_date
#        AND d.d <  ea.end_date
#       GROUP BY d.d
#     ),
#     booked_blocking AS (
#       SELECT d.d
#       FROM days d
#       JOIN equipment_bookings eb
#         ON eb.equipment_id = %s
#        AND lower(trim(eb.status::text)) IN ('approved','handoff','in_use','returning')
#        AND d.d >= eb.start_date
#        AND d.d <  eb.end_date
#       GROUP BY d.d
#     ),
#     pending_holds AS (
#       SELECT d.d
#       FROM days d
#       JOIN equipment_bookings eb
#         ON eb.equipment_id = %s
#        AND lower(trim(eb.status::text)) = 'pending'
#        AND d.d >= eb.start_date
#        AND d.d <  eb.end_date
#       GROUP BY d.d
#     ),
#     free_days AS (
#       SELECT a.d
#       FROM avail a
#       LEFT JOIN booked_blocking b ON b.d = a.d
#       WHERE b.d IS NULL
#       ORDER BY a.d
#     )
#     {debug_cte}
#     SELECT
#       COALESCE((SELECT array_agg(f.d::text) FROM free_days f), ARRAY[]::text[])       AS available_days,
#       COALESCE((SELECT array_agg(b.d::text) FROM booked_blocking b), ARRAY[]::text[]) AS booked_days,
#       COALESCE((SELECT array_agg(p.d::text) FROM pending_holds p), ARRAY[]::text[])   AS pending_days
#       {debug_select}
#     ;
#     """

#     # Parámetros (si hay debug, se usa eq_id una vez más para booked_debug)
#     params = [start_s, end_s, eq_id, eq_id, eq_id]
#     if debug:
#         params.append(eq_id)

#     with get_cur() as cur:
#       cur.execute(sql, tuple(params))
#       row = cur.fetchone() or {}
#     print('asdasd')
#     print({
#         "version": "calendar_v3_trim_lower",
#         "equipment_id": eq_id,
#         "start": start_s,
#         "end": end_s,
#         "available_days": row.get("available_days", []),
#         "booked_days": row.get("booked_days", []),
#         "pending_days": row.get("pending_days", [])
#     })

#     return jsonify({
#         "version": "calendar_v3_trim_lower",
#         "equipment_id": eq_id,
#         "start": start_s,
#         "end": end_s,
#         "available_days": row.get("available_days", []),
#         "booked_days": row.get("booked_days", []),
#         "pending_days": row.get("pending_days", []),
#         **({"_debug_rows": row.get("_debug_rows", [])} if debug else {}),
#     })
