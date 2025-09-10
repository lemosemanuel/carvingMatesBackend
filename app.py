from flask import Flask

# IMPORTS CORRECTOS: 1 bp por archivo
from blueprints.auth import bp as auth_bp          # <--- nuevo
from blueprints.users import bp as users_bp
from blueprints.roles import bp as roles_bp
from blueprints.sports import bp as sports_bp
from blueprints.equipment import bp as equipment_bp
from blueprints.lookups import bp as lookups_bp
from blueprints.forecasts import bp as forecasts_bp
from blueprints.skills import bp as skills_bp
from blueprints.coaching import bp as coaching_bp
from blueprints.schools import bp as schools_bp
from blueprints.travel import bp as travel_bp
from blueprints.retreats import bp as retreats_bp
from blueprints.places import bp as places_bp
# from blueprints.equipment_calendar import bp as equipment_calendar_bp
from blueprints.bookings import bp as bookings_bp  # 👈 importa bookings
from blueprints.notifications import bp as noti_bp
from blueprints.trips import trips_bp


def create_app():
    app = Flask(__name__)

    # REGISTRO por prefijo correcto
    app.register_blueprint(auth_bp, url_prefix="/api/auth")           # /api/auth/...
    app.register_blueprint(users_bp, url_prefix="/api/users")         # /api/users/...
    app.register_blueprint(roles_bp, url_prefix="/api/roles")         # /api/roles/...
    app.register_blueprint(sports_bp, url_prefix="/api/sports")       # /api/sports/...
    app.register_blueprint(equipment_bp, url_prefix="/api/equipment") # /api/equipment/...
    app.register_blueprint(lookups_bp,   url_prefix="/api")          # ← aquí
    app.register_blueprint(forecasts_bp, url_prefix="/api/forecasts")
    app.register_blueprint(skills_bp, url_prefix="/api/skills")
    app.register_blueprint(coaching_bp, url_prefix="/api/coaching")
    app.register_blueprint(schools_bp, url_prefix="/api/schools")
    app.register_blueprint(travel_bp, url_prefix="/api/travel")
    app.register_blueprint(retreats_bp, url_prefix="/api/retreats")
    app.register_blueprint(places_bp)  # /api/places/*
    # app.register_blueprint(equipment_calendar_bp)
    app.register_blueprint(bookings_bp,   url_prefix="/api")           # 👈 registra /api/bookings
    app.register_blueprint(noti_bp, url_prefix="/api")
    app.register_blueprint(trips_bp, url_prefix="/api/trips")



    @app.get("/api/health")
    def health():
        return {"ok": True, "service": "carving-api"}

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
