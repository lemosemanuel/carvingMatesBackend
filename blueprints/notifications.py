# blueprints/notifications.py
from flask import Blueprint, request, jsonify
from db import get_cur
from blueprints.auth_helpers import get_user_id_from_bearer

bp = Blueprint("notifications", __name__)

@bp.get("/notifications")
def list_notifications():
    user_id, err = get_user_id_from_bearer(request)
    if err:
        return err
    only_unread = request.args.get("unread") in ("1","true","yes")
    with get_cur() as cur:
        cur.execute(f"""
            SELECT id, type, title, body, data, created_at, read_at
            FROM notifications
            WHERE user_id=%s
            {"AND read_at IS NULL" if only_unread else ""}
            ORDER BY created_at DESC
            LIMIT 100
        """, (user_id,))
        rows = cur.fetchall()
    return jsonify(rows)

@bp.put("/notifications/<int:nid>/read")
def mark_notification_read(nid):
    user_id, err = get_user_id_from_bearer(request)
    if err:
        return err
    with get_cur(True) as cur:
        cur.execute("""
            UPDATE notifications
               SET read_at = NOW()
             WHERE id=%s AND user_id=%s
        """, (nid, user_id))
    return jsonify({"ok": True})
