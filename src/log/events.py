# Project: logs-ai-reporting-model-train — File: src/log/events.py
import datetime
import json
from pathlib import Path
from typing import List

from nl_sql.utils import fmt_elapsed  # reuse the human formatter

LOG_PATH = Path("outputs/logs/chat_sql.log")
SQL_LATEST_PATH = Path("outputs/logs/chat_sql_last.sql")
SQL_HISTORY_PATH = Path("outputs/logs/chat_sql_history.sql")

def _write_sql_files(user_q: str, sql: str) -> None:
    try:
        if not sql:
            return
        SQL_LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        sql_pretty = sql.strip()
        if not sql_pretty.endswith(";"):
            sql_pretty += ";"
        header = f"-- {datetime.datetime.utcnow().isoformat()}Z | {user_q}\n"
        SQL_LATEST_PATH.write_text(header + sql_pretty + "\n", encoding="utf-8")
        with SQL_HISTORY_PATH.open("a", encoding="utf-8") as hf:
            hf.write(header + sql_pretty + "\n\n")
    except Exception:
        pass

def log_sql_event(
    user_q: str,
    sql: str,
    cols: List[str] | None,
    rows_sample: list | None,
    total_rows: int | None,
    error: str | None = None,
    raw_a: str | None = None,
    raw_b: str | None = None,
    elapsed_total: float | None = None,
) -> None:
    """Append JSONL event and write copy-pasteable .sql files for the last query."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "user_query": user_q,
            "sql": sql,  # JSON escapes newlines; use .sql files to copy paste
            "columns": cols or [],
            "row_count": total_rows if total_rows is not None else 0,
            "rows_sample": rows_sample or [],
            "error": error or "",
            "model_raw_phase_a": raw_a or "",
            "model_raw_phase_b": raw_b or "",
            "elapsed_human": fmt_elapsed(elapsed_total or 0.0),
            "elapsed_seconds": round(elapsed_total or 0.0, 3),
        }
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # Always try to persist pretty SQL files
    _write_sql_files(user_q, sql or "")