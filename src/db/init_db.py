# Project: braintransplant-ai — File: src/db/init_db.py
import os
import sys
import psycopg  # psycopg v3
import traceback
import db.connection  # uses env: DB_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, DB_PORT


SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def main() -> int:
    """
    Apply the SQL schema from db/schema.sql to the connected PostgreSQL database.

    Behavior:
    - Reads the schema file located alongside this module (db/schema.sql).
    - Opens a new connection using db.connection.get_connection() (env-driven).
    - Executes the SQL as-is inside a single transaction and commits on success.
    - Prints a short status line; returns non-zero if anything fails.
    """
    if not os.path.isfile(SCHEMA_PATH):
        print(f"[init_db] schema not found: {SCHEMA_PATH}", file=sys.stderr)
        return 2

    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            sql = f.read()

        with db.connection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()

        print("[init_db] schema applied.")
        return 0

    except Exception as e:
        print(f"[init_db] ERROR: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
