# Project: braintransplant-ai — File: src/ui/admin/app_admin.py
import os
import shutil
import time
import uuid
import traceback
import streamlit as st

from google.cloud import storage
import vertexai
from vertexai.preview import rag
from utils.logger import get_logger

# ========== Explicit configuration ==========
PROJECT_ID = "fresh-myth-471317-j9"
LOCATION = "europe-west4"
RAG_CORPUS_NAME = "projects/fresh-myth-471317-j9/locations/europe-west4/ragCorpora/6917529027641081856"

STAGING_DIR = "/app/data/uploads"   # DevOps drops files here
INGESTED_DIR = "/app/data/ingested" # Local archive after successful import
GCS_BUCKET = f"{PROJECT_ID}-rag-staging"  # Pre-created bucket (region: europe-west3)
GCS_PREFIX = "imports"

ALLOWED_EXTS = {".pdf", ".docx", ".txt", ".pptx", ".ppt", ".xlsx", ".csv"}


# ========== Vertex + GCS ==========
def _init_vertex(logger) -> None:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    logger.info(f"vertexai.init(project={PROJECT_ID}, location={LOCATION})")


def _storage_client(logger) -> storage.Client:
    logger.info("Creating GCS storage client")
    return storage.Client(project=PROJECT_ID)


def _ensure_gcs_bucket(logger) -> storage.Bucket:
    client = _storage_client(logger)
    bucket = client.bucket(GCS_BUCKET)  # do not call get() to avoid bucketViewer requirement
    logger.info(f"Using bucket handle: {GCS_BUCKET}")
    # Soft probe: try listing 1 object; ignore failures (objectAdmin-only still OK for uploads)
    try:
        next(iter(client.list_blobs(bucket_or_name=bucket, max_results=1)), None)
        logger.info("Bucket list probe succeeded.")
    except Exception as e:
        logger.warning(f"Bucket list probe failed (continuing): {e}")
    return bucket


def _gcs_uri(filename: str) -> str:
    return f"gs://{GCS_BUCKET}/{GCS_PREFIX}/{filename}"


# ========== Local staging ==========
def _staging_files(logger) -> list[str]:
    if not os.path.exists(STAGING_DIR):
        logger.info(f"Staging not found: {STAGING_DIR}")
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
def _import_single_gcs_uri(logger, gs_uri: str) -> None:
    """
    Import a single GCS URI to RAG corpus.
    On this SDK build, import_files returns a response directly (not an LRO).
    """
    _init_vertex(logger)
    logger.info(f"RAG import_files start: uri={gs_uri}")

    resp = None
    last_err = None

    # Try known signatures by age; stop on first success.
    try:
        resp = rag.import_files(RAG_CORPUS_NAME, [gs_uri], chunk_size=1024, chunk_overlap=200)
        logger.info("import_files variant=positional")
    except TypeError as e:
        last_err = e

    if resp is None:
        try:
            resp = rag.import_files(corpus_name=RAG_CORPUS_NAME, uris=[gs_uri], chunk_size=1024, chunk_overlap=200)
            logger.info("import_files variant=corpus_name+uris")
        except TypeError as e:
            last_err = e

    if resp is None:
        try:
            resp = rag.import_files(corpus_name=RAG_CORPUS_NAME, gcs_uris=[gs_uri], chunk_size=1024, chunk_overlap=200)
            logger.info("import_files variant=corpus_name+gcs_uris")
        except TypeError as e:
            last_err = e

    if resp is None:
        try:
            resp = rag.import_files(rag_corpus=RAG_CORPUS_NAME, gcs_source_uris=[gs_uri], chunk_size=1024, chunk_overlap=200)
            logger.info("import_files variant=rag_corpus+gcs_source_uris")
        except TypeError as e:
            last_err = e

    if resp is None:
        try:
            resp = rag.import_files(parent=RAG_CORPUS_NAME, gcs_source_uris=[gs_uri], chunk_size=1024, chunk_overlap=200)
            logger.info("import_files variant=parent+gcs_source_uris")
        except TypeError as e:
            last_err = e

    if resp is None:
        raise TypeError(f"All import_files signatures failed for {gs_uri}. Last error: {last_err}")

    logger.info(f"RAG import_files completed: uri={gs_uri}, response={resp}")


def _list_rag_files(logger):
    _init_vertex(logger)
    try:
        files = list(rag.list_files(RAG_CORPUS_NAME))  # positional corpus arg works broadly
        logger.info(f"list_files returned {len(files)} files")
        return files
    except Exception as e:
        logger.error(f"list_files failed: {e}\n{traceback.format_exc()}")
        return []


def _delete_rag_file(logger, file_name: str) -> None:
    _init_vertex(logger)
    resp = rag.delete_file(name=file_name)
    logger.info(f"Deleted {file_name}, response={resp}")


def _delete_all_rag_files(logger) -> int:
    files = _list_rag_files(logger)
    deleted = 0
    for f in files:
        try:
            _delete_rag_file(logger, f.name)
            deleted += 1
        except Exception as e:
            logger.error(f"delete failed for {getattr(f, 'name', 'unknown')}: {e}")
    logger.info(f"delete-all summary: deleted={deleted}, total_seen={len(files)}")
    return deleted


# ========== Upload pipeline ==========
def _upload_all_from_staging(logger) -> tuple[int, int]:
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
            # 1) Upload to GCS
            blob_name = f"{GCS_PREFIX}/{fname}"
            logger.info(f"GCS upload: {src} -> gs://{GCS_BUCKET}/{blob_name}")
            bucket.blob(blob_name).upload_from_filename(src)
            gs_uri = _gcs_uri(fname)

            # 2) Import to RAG
            _import_single_gcs_uri(logger, gs_uri)

            # 3) Move to ingested locally
            dst = os.path.join(INGESTED_DIR, fname)
            if os.path.exists(dst):
                base, ext = os.path.splitext(fname)
                dst = os.path.join(INGESTED_DIR, f"{base}_{uuid.uuid4().hex[:8]}{ext}")
            shutil.move(src, dst)
            logger.info(f"Local move to ingested: {src} -> {dst}")
            ok += 1
        except Exception as e:
            logger.error(f"Upload/import failed for {fname}: {e}\n{traceback.format_exc()}")
            bad += 1

    logger.info(f"upload summary: ok={ok}, bad={bad}, total={len(files)}")
    return ok, bad


# ========== Admin UI ==========
def render_admin() -> None:
    logger = get_logger("btai.admin")
    st.set_page_config(page_title="BrainTransplant Admin Panel", page_icon="⛰️")

    st.title("BrainTransplant Admin Panel")
    st.caption("Manage documents for Vertex AI RAG index. Logs go to /app/outputs/logs/braintransplant.log")

    # Current RAG files
    st.subheader("Current RAG Files")
    files = _list_rag_files(logger)
    st.write(f"Files in corpus: {len(files)}")
    if files:
        with st.expander("Show files"):
            for f in files:
                st.write(f"• {getattr(f, 'display_name', None) or f.name}")

    # Staging overview
    staging = _staging_files(logger)
    st.info(f"Files in staging: {len(staging)}  (path: {STAGING_DIR})")
    if staging:
        with st.expander("Show staging files"):
            for n in staging:
                st.write(f"- {n}")

    # Actions
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
