# Project: braintransplant-ai — File: src/db/connection.py
import os
import psycopg  # psycopg v3

def get_connection() -> psycopg.Connection:
    """
    Open a new PostgreSQL connection using environment variables provided by docker-compose.
    Required: DB_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, DB_PORT
    """
    required = ["DB_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "DB_PORT"]
    missing = [k for k in required if os.getenv(k) is None]
    if missing:
        raise RuntimeError(f"Missing required DB env vars: {', '.join(missing)}")

    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("DB_PORT"),
    )
