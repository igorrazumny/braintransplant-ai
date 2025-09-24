# Project: braintransplant-ai — File: src/admin/app_admin.py
import os
import io
import glob
import zipfile
import traceback
import streamlit as st

from db.init_db import main as init_db_main
from db.connection import get_connection

# NOTE: The admin panel is for document management, not the old xlsx ingest.
# This will be refactored later to upload PDFs/Docs to Google Drive.
UPLOAD_DIR = "/app/data/uploads"

def _reset_database() -> None:
    try:
        db_user = os.getenv("POSTGRES_USER")
        if not db_user:
            raise RuntimeError("POSTGRES_USER is not set.")

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DROP SCHEMA public CASCADE;")
                cur.execute("CREATE SCHEMA public;")
                cur.execute(f"GRANT ALL ON SCHEMA public TO {db_user};")
            conn.commit()

        rc = init_db_main()
        if rc == 0:
            st.success("Database reset: schema dropped and reapplied.")
        else:
            st.error(f"Schema re-apply failed (exit {rc}). See container logs.")
    except Exception as e:
        st.error(f"Reset failed: {e}")
        st.code(traceback.format_exc())


def render_admin() -> None:
    st.set_page_config(page_title="[Admin] BC2 AI Assistant", page_icon="⛰️")

    st.title("[Admin] BC2 AI Assistant")
    st.caption("Database Controls & Document Management")

    st.subheader("Database")
    if st.button("Reset Database (Drop & Re-apply Schema)"):
        _reset_database()

    # Future functionality for document upload will go here
    st.subheader("Document Management (Future)")
    st.info("This section will be used to upload and manage documents for the RAG service.")
