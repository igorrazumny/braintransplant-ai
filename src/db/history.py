# Project: braintransplant-ai — File: src/db/history.py
import traceback
from typing import Optional

from db.connection import get_connection

def save_chat_turn(
    session_id: str,
    user_query: str,
    model_response: str,
    retrieved_context: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """
    Saves a single turn of a conversation to the chat_history table.
    """
    sql = """
        INSERT INTO chat_history
            (user_id, session_id, user_query, model_response, retrieved_context)
        VALUES
            (%s, %s, %s, %s, %s)
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    user_id,
                    session_id,
                    user_query,
                    model_response,
                    retrieved_context
                ))
            conn.commit()
    except Exception:
        # For an MVP, printing the error is sufficient.
        # In production, you would use a structured logger.
        traceback.print_exc()
