# Carving App - Flask API

Flask API (sin ORM) para el esquema de la Carving App.
Incluye blueprints por dominio y scripts para reset + seed de la base.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # edita con tus credenciales

# Reset + seed de base (desde la raíz del proyecto)
python sql/reset_and_seed_db.py

# Levantar API
export FLASK_APP=app.py
flask run --port ${APP_PORT:-5000}
```

## Rutas principales
- `/api/users` (CRUD, asignar roles, agregar deportes)
- `/api/roles` (crear/listar)
- `/api/sports` (crear/listar)
- `/api/equipment` (CRUD, imágenes, bookings, reviews, tips)
- `/api/forecasts` (fuentes, crear/listar pronósticos)
- `/api/skills` (videos y reviews AI)
- `/api/coaching` (aplicaciones de coach, cambiar estado, reviews a coach)
- `/api/schools` (crear escuela, asignar profesor, disponibilidad, fichas de alumno)
- `/api/travel` (planes de viaje y matches)
- `/api/retreats` (crear, aplicar, reviews, listar)# carvingMatesBackend
