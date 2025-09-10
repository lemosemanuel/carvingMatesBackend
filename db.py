# carving_flask_api_full/db.py
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from config import DB_CONFIG

@contextmanager
def get_conn():
    """
    Abre una conexión y:
      - COMMIT al salir si no hubo excepción
      - ROLLBACK si hubo excepción
    Importante: esto hace que los endpoints que usan get_conn()+cursor
    persistan sin tener que llamar conn.commit() a mano.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@contextmanager
def get_cur(commit=False):
    """
    Mantengo compatibilidad con el resto del código:
    - Si commit=True, se hace commit aquí (antes de que get_conn haga el suyo).
      Hacer commit dos veces no rompe nada.
    """
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
