# Project: braintransplant-ai — File: src/web/app.py
import os
import streamlit as st

# Route: Admin by token => Admin UI; else Chat
from ui.admin.app_admin import render_admin
from ui.web.view_chat import view_chat

ADMIN_QUERY_KEY = "admin"  # routing only


def main() -> None:
    """
    Entry point for the BrainTransplant web app.
    Routes based on query param:
    - If ?admin=<ADMIN_TOKEN>, renders admin UI.
    - Else, renders chat UI.
    """
    qp = getattr(st, "query_params", None)



    if qp is None:
        params = st.experimental_get_query_params()
        admin_param = (params.get(ADMIN_QUERY_KEY, [None]) or [None])[0]
    else:
        admin_param = qp.get(ADMIN_QUERY_KEY, None)

    if admin_param and admin_param == os.getenv("ADMIN_TOKEN"):
        render_admin()
    else:
        view_chat()


if __name__ == "__main__":
    main()
