import sqlite3
from src.storage import db

db_path = db.DEFAULT_DB_PATH
db.init_db(db_path)

with db.get_db(db_path) as conn:
    c = conn.cursor()
    c.execute("DELETE FROM ideas")
    c.execute("DELETE FROM clusters")
    c.execute("DELETE FROM pain_points")
    conn.commit()
    print("Deleted all ideas, clusters, and pain_points. Ready to re-extract.")
