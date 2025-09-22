# Project: logs-ai-reporting-model-train — File: src/sql/utils.py
import os
import datetime
import psycopg
from typing import List, Tuple

from db.connection import get_connection

# Statement timeout (ms); default 5 minutes if not set
DEFAULT_DB_TIMEOUT_MS = int(os.getenv("DB_STMT_TIMEOUT_MS", "300000"))

def strip_fences(s: str) -> str:
    return s.replace("```sql", "").replace("```SQL", "").replace("```", "").strip()

def extract_sql(text: str) -> str:
    """Extract a single SQL statement from possibly fenced output; drop trailing semicolon."""
    if not text:
        return ""
    t = text.strip()
    if "```" in t:
        parts = t.split("```")
        for i in range(len(parts) - 1):
            block = parts[i + 1]
            if block.lstrip().lower().startswith("sql"):
                candidate = (block.split("\n", 1)[1] if "\n" in block else "").strip()
                return candidate.replace("```", "").strip().rstrip(";")
        return parts[1].replace("```", "").strip().rstrip(";")
    return t.replace("```", "").strip().rstrip(";")

def looks_like_sql(s: str) -> bool:
    if not s:
        return False
    t = s.strip().lower()
    return ("select " in t and " from " in t) or t.startswith(("with ", "select "))

def exec_sql(sql: str, timeout_ms: int = DEFAULT_DB_TIMEOUT_MS) -> Tuple[List[str], list]:
    """Run a read-only SQL with per-statement timeout; return (columns, rows)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL statement_timeout = {timeout_ms};")
            cur.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall() if cur.description else []
            return cols, rows

def fmt_elapsed(seconds: float) -> str:
    """Human-friendly elapsed time."""
    seconds_int = int(round(seconds))
    h, rem = divmod(seconds_int, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    if m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"

def auto_answer(cols: List[str], rows: list) -> str:
    """Fallback natural answer when model returns SQL in Phase-B."""
    try:
        if len(rows) == 1 and len(cols) == 1 and isinstance(rows[0][0], (int, float)):
            c = cols[0].lower()
            v = rows[0][0]
            if c == "total_records":
                return f"There are **{v:,}** records in the system."
            if c == "total_recipes":
                return f"There are **{v:,}** distinct recipes in the system."
            return f"Result: **{v:,}** ({cols[0]})."
        if len(cols) == 1 and cols[0].lower() in ("recipe_name", "username"):
            label = "recipes" if cols[0].lower() == "recipe_name" else "users"
            items = [str(r[0]) for r in rows[:20]]
            total = len(rows)
            return f"Found **{total}** {label}. Showing {min(20, total)}:\n- " + "\n- ".join(items)
        total = len(rows)
        shown = min(5, total)
        preview = []
        for r in rows[:shown]:
            pairs = ", ".join(f"{cols[i]}={r[i]}" for i in range(len(cols)))
            preview.append(f"- {pairs}")
        return f"Found **{total}** rows. Preview:\n" + "\n".join(preview)
    except Exception:
        return "Here’s what I found based on the logs."