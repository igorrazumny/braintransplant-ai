# Project: braintransplant-ai — File: src/ui/admin/app_admin.py
import os
import shutil
import time
import uuid
import logging
import traceback
import streamlit as st

from google.cloud import storage
import vertexai
from vertexai.preview import rag

# ========== Explicit configuration ==========
PROJECT_ID = "fresh-myth-471317-j9"
LOCATION = "europe-west3"
RAG_CORPUS_NAME = "projects/754198198954/locations/europe-west3/ragCorpora/2305843009213693952"

STAGING_DIR = "/app/data/uploads"  # DevOps drops files here
INGESTED_DIR = "/app/data/ingested"  # Local archive after successful import
GCS_BUCKET = f"{PROJECT_ID}-rag-staging"  # Pre-created bucket
GCS_PREFIX = "imports"

ALLOWED_EXTS = {".pdf", ".docx", ".txt", ".pptx", ".ppt", ".xlsx", ".csv"}

LOG_DIR = "/app/outputs/logs"
LOG_FILE = "admin_rag.log"


# ========== Logging ==========
def _ensure_logger() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("btai.admin")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE), encoding="utf-8")
        fh.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


# ========== Vertex + GCS ==========
def _init_vertex(logger: logging.Logger) -> None:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    logger.info(f"vertexai.init(project={PROJECT_ID}, location={LOCATION})")


def _storage_client(logger: logging.Logger) -> storage.Client:
    return storage.Client(project=PROJECT_ID)


def _ensure_gcs_bucket(logger: logging.Logger) -> storage.Bucket:
    client = _storage_client(logger)
    bucket = client.bucket(GCS_BUCKET)
    logger.info(f"Using bucket {GCS_BUCKET}")
    return bucket


def _gcs_uri(filename: str) -> str:
    return f"gs://{GCS_BUCKET}/{GCS_PREFIX}/{filename}"


# ========== Local staging ==========
def _staging_files(logger: logging.Logger) -> list[str]:
    if not os.path.exists(STAGING_DIR):
        return []
    out = []
    for name in os.listdir(STAGING_DIR):
        path = os.path.join(STAGING_DIR, name)
        if not os.path.isfile(path):
            continue
        if name.startswith("."):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext in ALLOWED_EXTS:
            out.append(name)
    logger.info(f"Found {len(out)} staging file(s): {out}")
    return sorted(out)


# ========== RAG ops ==========
def _import_single_gcs_uri(logger: logging.Logger, gs_uri: str, timeout_s: int = 900) -> None:
    """
    Import a single GCS URI to RAG corpus.
    The import_files function returns a response directly, not an operation.
    """
    _init_vertex(logger)
    logger.info(f"RAG import_files start: uri={gs_uri}")

    try:
        # The import_files function returns ImportRagFilesResponse directly
        response = rag.import_files(
            RAG_CORPUS_NAME,
            [gs_uri],
            chunk_size=1024,
            chunk_overlap=200
        )
        logger.info(f"RAG import_files completed: uri={gs_uri}, response={response}")
    except Exception as e:
        logger.error(f"RAG import failed: {e}")
        raise


def _list_rag_files(logger: logging.Logger):
    _init_vertex(logger)
    try:
        files = list(rag.list_files(RAG_CORPUS_NAME))
        logger.info(f"list_files returned {len(files)} files")
        return files
    except Exception as e:
        logger.error(f"list_files failed: {e}\n{traceback.format_exc()}")
        return []


def _delete_rag_file(logger: logging.Logger, file_name: str) -> None:
    _init_vertex(logger)
    response = rag.delete_file(name=file_name)
    logger.info(f"Deleted {file_name}, response={response}")


def _delete_all_rag_files(logger: logging.Logger) -> int:
    files = _list_rag_files(logger)
    deleted = 0
    for f in files:
        try:
            _delete_rag_file(logger, f.name)
            deleted += 1
        except Exception as e:
            logger.error(f"delete failed for {f.name}: {e}")
    return deleted


# ========== Upload pipeline ==========
def _upload_all_from_staging(logger: logging.Logger) -> tuple[int, int]:
    os.makedirs(STAGING_DIR, exist_ok=True)
    os.makedirs(INGESTED_DIR, exist_ok=True)

    files = _staging_files(logger)
    if not files:
        return 0, 0

    bucket = _ensure_gcs_bucket(logger)
    ok, bad = 0, 0

    for fname in files:
        src = os.path.join(STAGING_DIR, fname)
        try:
            blob_name = f"{GCS_PREFIX}/{fname}"
            bucket.blob(blob_name).upload_from_filename(src)
            gs_uri = _gcs_uri(fname)
            _import_single_gcs_uri(logger, gs_uri, timeout_s=900)

            dst = os.path.join(INGESTED_DIR, fname)
            if os.path.exists(dst):
                base, ext = os.path.splitext(fname)
                dst = os.path.join(INGESTED_DIR, f"{base}_{uuid.uuid4().hex[:8]}{ext}")
            shutil.move(src, dst)
            ok += 1
        except Exception as e:
            logger.error(f"Upload/import failed for {fname}: {e}\n{traceback.format_exc()}")
            bad += 1
    return ok, bad


# ========== Admin UI ==========
def render_admin() -> None:
    logger = _ensure_logger()
    st.set_page_config(page_title="BrainTransplant Admin Panel", page_icon="⛰️")

    st.title("BrainTransplant Admin Panel")
    st.caption("Manage documents for Vertex AI RAG index.")
    st.info(f"Logs: {os.path.join(LOG_DIR, LOG_FILE)}")

    st.subheader("Current RAG Files")
    files = _list_rag_files(logger)
    st.write(f"Files in corpus: {len(files)}")
    if files:
        with st.expander("Show files"):
            for f in files:
                st.write(f"• {getattr(f, 'display_name', None) or f.name}")

    staging = _staging_files(logger)
    st.info(f"Files in staging: {len(staging)}")
    if staging:
        with st.expander("Show staging files"):
            for n in staging:
                st.write(f"- {n}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Upload ALL from staging → RAG", type="primary", use_container_width=True):
            with st.spinner("Uploading…"):
                ok, bad = _upload_all_from_staging(logger)
                st.success(f"Imported {ok}, Failed {bad}")
                st.rerun()

    with col2:
        if st.button("🗑️ Remove ALL files from RAG", type="secondary", use_container_width=True):
            with st.spinner("Deleting…"):
                n = _delete_all_rag_files(logger)
                st.success(f"Deleted {n} files")
                st.rerun()
