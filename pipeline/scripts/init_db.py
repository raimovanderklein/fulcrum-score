"""Initialize encounter.db from schema.sql. Idempotent."""
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent
DATA = REPO / "data"
DATA.mkdir(exist_ok=True)
DB_PATH = DATA / "encounter.db"
SCHEMA_PATH = HERE / "schema.sql"

def main():
    fresh = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'encounter_%' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Database: {DB_PATH} ({'created' if fresh else 'updated'})")
    print(f"Tables ({len(tables)}):")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        n = cur.fetchone()[0]
        print(f"  {t}: {n} rows")
    conn.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
