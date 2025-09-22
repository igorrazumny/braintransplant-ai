# Project: logs-ai-reporting-model-train — File: src/ingest/xlsx2db.py
# logs-ai-reporting-model-train/src/ingest/xlsx2db.py

import os
import typing
import pandas as pd
import psycopg
from db.connection import get_connection

# Explicit constants (no defaults)
UPLOAD_DIR = "/app/data/uploads"
TABLE_NAME = "logs_pkm"
BATCH_SIZE = 1000

COLUMNS: typing.List[str] = [
    "user_id","id","subseq_id","message","audit_time","action_raw","type","label","version",
    "recipe_id","recipe_name","material_name","material_id","name1","name2","username",
    "action_derived","session_start","session_end","session_duration",
]

def _coerce_datetime(df: pd.DataFrame, col: str) -> None:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

def _coerce_int(df: pd.DataFrame, col: str) -> None:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

def _rows_from_df(df: pd.DataFrame) -> typing.Iterable[typing.Tuple[typing.Any, ...]]:
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = pd.NA
    ordered = df[COLUMNS]
    for _, row in ordered.iterrows():
        yield tuple(None if pd.isna(v) else v for v in row.tolist())

def _insert_rows(conn: psycopg.Connection, rows: typing.Iterable[typing.Tuple[typing.Any, ...]]) -> int:
    sql = f"INSERT INTO {TABLE_NAME} ({', '.join(COLUMNS)}) VALUES ({', '.join(['%s'] * len(COLUMNS))})"
    inserted = 0
    with conn.cursor() as cur:
        batch: typing.List[typing.Tuple[typing.Any, ...]] = []
        for r in rows:
            batch.append(r)
            if len(batch) >= BATCH_SIZE:
                cur.executemany(sql, batch)
                inserted += len(batch)
                batch.clear()
        if batch:
            cur.executemany(sql, batch)
            inserted += len(batch)
    return inserted

# -------- small, testable units (for UI progress) --------

def list_staged_xlsx() -> typing.List[str]:
    if not os.path.isdir(UPLOAD_DIR):
        return []
    paths = [os.path.join(UPLOAD_DIR, f) for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(".xlsx")]
    paths.sort()
    return paths

def ingest_file(conn: psycopg.Connection, path: str) -> int:
    df = pd.read_excel(path, dtype="string", engine="openpyxl")
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    _coerce_datetime(df, "audit_time")
    _coerce_datetime(df, "session_start")
    _coerce_datetime(df, "session_end")
    _coerce_int(df, "session_duration")
    rows_iter = _rows_from_df(df)
    inserted = _insert_rows(conn, rows_iter)
    conn.commit()
    return inserted

def ingest_folder() -> dict:
    paths = list_staged_xlsx()
    total_rows = 0
    processed = 0
    with get_connection() as conn:
        for p in paths:
            total_rows += ingest_file(conn, p)
            processed += 1
    return {"files": processed, "rows": total_rows, "dir": UPLOAD_DIR}

def ingest_with_details() -> dict:
    """
    Same as ingest_folder() but returns per-file details for UI logging.
    """
    paths = list_staged_xlsx()
    details: typing.List[typing.Dict[str, typing.Any]] = []
    total_rows = 0
    with get_connection() as conn:
        for p in paths:
            inserted = ingest_file(conn, p)
            details.append({"file": p, "rows": inserted})
            total_rows += inserted
    return {"files": len(details), "rows": total_rows, "dir": UPLOAD_DIR, "details": details}