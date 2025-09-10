# blueprints/forecasts.py
from flask import Blueprint, request, jsonify
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

bp = Blueprint("forecasts", __name__, url_prefix="/api/forecasts")

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"     # para viento/temperatura
ENSEMBLE_URL = "https://ensemble-api.open-meteo.com/v1/forecast"  # nieve (snowfall/snow_depth)

def _tzaware(timestr, tz):
    # Open-Meteo devuelve ISO en UTC por defecto; ajustamos a tz pedida
    dt = datetime.fromisoformat(timestr.replace("Z","+00:00"))
    return dt.astimezone(ZoneInfo(tz)).isoformat()

@bp.get("/surf")
def surf_forecast():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    tz = request.args.get("tz", "UTC")
    name = request.args.get("name")

    # 1) olas/swell
    marine_params = {
        "latitude": lat, "longitude": lon, "timezone": "UTC",
        "hourly": ",".join([
            "wave_height",
            "swell_wave_height","swell_wave_period","swell_wave_direction",
            "wind_wave_height","wind_wave_period","wind_wave_direction"
        ])
    }
    m = requests.get(MARINE_URL, params=marine_params, timeout=12).json()

    # 2) viento de superficie (útil para condiciones de surf)
    wx_params = {
        "latitude": lat, "longitude": lon, "timezone": "UTC",
        "hourly": "wind_speed_10m,wind_direction_10m"
    }
    w = requests.get(FORECAST_URL, params=wx_params, timeout=12).json()

    # normalizar por índice horario
    hours = []
    mtimes = m["hourly"]["time"]
    for i, t in enumerate(mtimes):
        item = {
            "time": _tzaware(t, tz),
            "wave_height_m": m["hourly"].get("wave_height",[None])[i],
            "swell_height_m": m["hourly"].get("swell_wave_height",[None])[i],
            "swell_period_s": m["hourly"].get("swell_wave_period",[None])[i],
            "swell_direction_deg": m["hourly"].get("swell_wave_direction",[None])[i],
            "wind_wave_height_m": m["hourly"].get("wind_wave_height",[None])[i],
            "wind_wave_period_s": m["hourly"].get("wind_wave_period",[None])[i],
            "wind_wave_direction_deg": m["hourly"].get("wind_wave_direction",[None])[i],
        }
        # si el tiempo coincide con el índice de viento
        try:
            wi = w["hourly"]["time"].index(t)
            item["wind_speed_ms"] = w["hourly"]["wind_speed_10m"][wi]
            item["wind_direction_deg"] = w["hourly"]["wind_direction_10m"][wi]
        except ValueError:
            item["wind_speed_ms"] = None
            item["wind_direction_deg"] = None
        hours.append(item)

    return jsonify({
        "spot": {"name": name, "lat": lat, "lon": lon, "timezone": tz},
        "hours": hours,
        "source": "open-meteo:marine"
        })

@bp.get("/snow")
def snow_forecast():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    tz = request.args.get("tz", "UTC")
    name = request.args.get("name")

    elevation = request.args.get("elevation")  # opcional

    params = {
        "latitude": lat, "longitude": lon, "timezone": tz,
        "daily": "snowfall_sum,snow_depth,temperature_2m_min,temperature_2m_max",
        "hourly": "temperature_2m,precipitation,weathercode",
        "forecast_days": 7
    }
    # Ensemble API expone snowfall/snow_depth con distintos modelos
    resp = requests.get(ENSEMBLE_URL, params=params, timeout=12).json()

    daily = []
    times = resp.get("daily", {}).get("time", [])
    for i, d in enumerate(times):
        daily.append({
            "date": d,
            "snowfall_cm": _safe_cm(resp["daily"].get("snowfall_sum",[None])[i]),
            "snow_depth_cm": _safe_cm(resp["daily"].get("snow_depth",[None])[i]),
            "min_temp_c": resp["daily"].get("temperature_2m_min",[None])[i],
            "max_temp_c": resp["daily"].get("temperature_2m_max",[None])[i],
        })

    return jsonify({
        "resort": {"name": name, "lat": lat, "lon": lon, "elevation_m": float(elevation) if elevation else None, "timezone": tz},
        "daily": daily,
        "source": "open-meteo:ensemble"
        })


def _safe_cm(value):
    if value is None:
        return None
    # Open-Meteo devuelve snowfall en mm de agua o cm según endpoint/modelo; aquí suponemos cm.
    # Si más tarde cambiamos de proveedor, ajustamos en un solo sitio.
    return float(value)
