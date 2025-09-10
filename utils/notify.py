# utils/notify.py
from db import get_cur

def notify_user(user_id: int, ntype: str, title: str, body: str, data: dict | None = None):
    """Inserta una notificación y (opcional) envía push."""
    data = data or {}
    with get_cur(True) as cur:
        cur.execute("""
            INSERT INTO notifications (user_id, type, title, body, data)
            VALUES (%s, %s, %s, %s, %s::jsonb)
            RETURNING id
        """, (user_id, ntype, title, body, json_dumps(data)))
        nid = cur.fetchone()["id"]

    # (Opcional) push: integra FCM si tenés tokens guardados
    try:
        send_push_if_configured(user_id, title, body, data)
    except Exception:
        pass

    return nid

# ---- Helpers ----
import json
def json_dumps(d): return json.dumps(d, ensure_ascii=False)

def send_push_if_configured(user_id: int, title: str, body: str, data: dict):
    """Stub. Integra FCM si ya guardás device tokens por usuario."""
    # from utils.fcm import send_to_user_devices
    # send_to_user_devices(user_id=user_id, title=title, body=body, data=data)
    return
