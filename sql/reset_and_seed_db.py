from pathlib import Path
import sys
import psycopg2

# Añade el root del proyecto al sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from config import DB_CONFIG  # ← ahora absoluto

DROP_SQL = '''
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
  END LOOP;
END $$;
'''

def run():
    root = Path(__file__).resolve().parent
    schema = (root / 'schema.sql').read_text()
    seed = (root / 'seed.sql').read_text()

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    # cur.execute(DROP_SQL)  # descomenta si quieres dropear todo
    cur.execute(schema)
    cur.execute(seed)
    cur.close(); conn.close()
    print("Reset + seed completed.")

if __name__ == "__main__":
    run()
