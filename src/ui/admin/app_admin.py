# Project: braintransplant-ai — File: src/admin/app_admin.py
import os
import io
import glob
import zipfile
import traceback
import streamlit as st

from db.init_db import main as init_db_main
from db.connection import get_connection
from db.ingest.xlsx2db import list_staged_xlsx, ingest_file

UPLOAD_DIR = "/app/data/uploads"  # bind mount


def _reset_database() -> None:
    try:
        db_user = os.getenv("POSTGRES_USER")
        if not db_user:
            raise RuntimeError("POSTGRES_USER is not set; cannot GRANT schema privileges.")

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


def _clear_staged_files() -> None:
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        cnt = 0
        for pat in ("*.xlsx", "*.XLSX"):
            for p in glob.glob(os.path.join(UPLOAD_DIR, pat)):
                try:
                    os.remove(p)
                    cnt += 1
                except Exception:
                    pass
        st.success(f"Cleared {cnt} staged file(s) from {UPLOAD_DIR}")
        st.session_state["uploader_key"] += 1
        st.rerun()
    except Exception as e:
        st.error(f"Clear failed: {e}")
        st.code(traceback.format_exc())


def render_admin() -> None:
    st.set_page_config(page_title="[Admin] BC2 AI Assistant", page_icon="⛰️")

    st.title("[Admin] BC2 AI Assistant")
    st.caption("DB controls and file staging")

    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0

    st.subheader("1) Database")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Reset database (drop & re-apply schema)"):
            _reset_database()
    with c2:
        if st.button("Clear staged files"):
            _clear_staged_files()

    staged = list_staged_xlsx()
    st.caption(f"Currently staged: {len(staged)} file(s) in {UPLOAD_DIR}")

    st.subheader("2) Stage files (XLSX / ZIP)")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    uploaded = st.file_uploader(
        "Choose .xlsx or .zip",
        type=["xlsx", "zip"],
        accept_multiple_files=True,
        help=f"Files are saved to {UPLOAD_DIR}. Use the button below to upload them into the DB.",
        key=f"uploader_{st.session_state['uploader_key']}",
    )

    if uploaded:
        saved, errors = [], []
        for up in uploaded:
            try:
                data = up.read()
                name = os.path.basename(up.name)
                if name.lower().endswith(".zip"):
                    try:
                        with zipfile.ZipFile(io.BytesIO(data)) as zf:
                            for info in zf.infolist():
                                if not info.filename.lower().endswith(".xlsx"):
                                    continue
                                dest = os.path.join(UPLOAD_DIR, os.path.basename(info.filename))
                                os.makedirs(os.path.dirname(dest), exist_ok=True)
                                with zf.open(info) as src, open(dest, "wb") as out:
                                    out.write(src.read())
                                saved.append(dest)
                    except zipfile.BadZipFile:
                        errors.append(f"Bad ZIP: {name}")
                elif name.lower().endswith(".xlsx"):
                    dest = os.path.join(UPLOAD_DIR, name)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, "wb") as out:
                        out.write(data)
                    saved.append(dest)
                else:
                    errors.append(f"Unsupported file: {name}")
            except Exception as e:
                errors.append(f"{name}: {e}")

        if saved:
            st.success(f"Staged {len(saved)} file(s).")
            staged = list_staged_xlsx()

        if errors:
            st.error("Some files failed:")
            st.code("\n".join(errors))

    if staged:
        st.code("\n".join(staged))

    st.subheader("3) Upload to DB")
    upload_disabled = (len(staged) == 0)
    if st.button("Upload staged files to DB", disabled=upload_disabled):
        try:
            if not staged:
                st.warning("No staged .xlsx files found.")
                return

            progress = st.progress(0)
            log_box = st.empty()
            log_lines = []
            total_rows = 0

            with get_connection() as conn:
                for i, p in enumerate(staged, start=1):
                    fname = os.path.basename(p)
                    log_lines.append(f"[{i}/{len(staged)}] {fname} …")
                    log_box.code("\n".join(log_lines))
                    inserted = ingest_file(conn, p)
                    total_rows += inserted
                    log_lines[-1] = f"[{i}/{len(staged)}] {fname} → rows={inserted}"
                    log_box.code("\n".join(log_lines))
                    progress.progress(int(i * 100 / len(staged)))

            st.success(f"Ingest complete: files={len(staged)} rows={total_rows} dir={UPLOAD_DIR}")
        except Exception as e:
            st.error(f"Ingest failed: {e}")
            st.code(traceback.format_exc())
