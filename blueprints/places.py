# blueprints/places.py
from flask import Blueprint, request, jsonify
import requests

bp = Blueprint("places", __name__, url_prefix="/api/places")

NOMINATIM = "https://nominatim.openstreetmap.org/search"
REVERSE = "https://nominatim.openstreetmap.org/reverse"
UA = {"User-Agent": "CarvingMates/1.0 (contact@carvingmates.app)"}

@bp.get("/search")
def search_places():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})
    params = {"q": q, "format": "json", "limit": 8, "addressdetails": 1}
    r = requests.get(NOMINATIM, params=params, headers=UA, timeout=10)
    r.raise_for_status()
    out = []
    for it in r.json():
        out.append({
            "name": it.get("display_name"),
            "lat": float(it["lat"]),
            "lon": float(it["lon"]),
            "type": it.get("type"),
            "country": (it.get("address") or {}).get("country"),
        })

    print({"results": out})
    return jsonify({"results": out})

@bp.get("/reverse")
def reverse_place():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "lat/lon required"}), 400
    params = {"lat": lat, "lon": lon, "format": "json"}
    r = requests.get(REVERSE, params=params, headers=UA, timeout=10)
    r.raise_for_status()
    j = r.json()
    return jsonify({
        "name": j.get("display_name"),
        "lat": float(j.get("lat", lat)),
        "lon": float(j.get("lon", lon)),
        "country": (j.get("address") or {}).get("country")
    })
