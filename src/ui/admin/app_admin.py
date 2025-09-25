# Project: braintransplant-ai — File: src/ui/admin/app_admin.py
import os
import shutil
import time
import streamlit as st
from google.cloud import storage
import vertexai
from vertexai.preview import rag

# --- Configuration ---
PROJECT_ID = "fresh-myth-471317-j9"
LOCATION = "europe-west3"
RAG_CORPUS_NAME = "projects/754198198954/locations/europe-west3/ragCorpora/2305843009213693952"
STAGING_DIR = "/app/data/uploads"  # DevOps drops files here
INGESTED_DIR = "/app/data/ingested"  # Move files here after import
GCS_BUCKET = f"{PROJECT_ID}-rag-staging"
GCS_PREFIX = "imports"  # GCS prefix for uploads

# --- Vertex + GCS helpers ---
def _init_vertex() -> None:
    """Initializes the Vertex AI client."""
    vertexai.init(project=PROJECT_ID, location=LOCATION)

def _storage_client() -> storage.Client:
    """Returns a Google Cloud Storage client."""
    return storage.Client(project=PROJECT_ID)

def _ensure_gcs_bucket() -> storage.Bucket:
    """Creates the GCS bucket if it doesn't exist and verifies its existence."""
    client = _storage_client()
    bucket = client.bucket(GCS_BUCKET)
    if not bucket.exists():
        try:
            bucket.create(location=LOCATION)
            st.toast(f"Created GCS bucket: {GCS_BUCKET} in {LOCATION}")
        except Exception as e:
            st.error(f"Failed to create bucket {GCS_BUCKET}: {e}. Check permissions and region.")
            raise
    else:
        st.toast(f"Using existing GCS bucket: {GCS_BUCKET}")
    return bucket

def _gcs_uri(filename: str) -> str:
    """Constructs the GCS URI for a given filename."""
    return f"gs://{GCS_BUCKET}/{GCS_PREFIX}/{filename}"

# --- RAG operations ---
def _import_single_gcs_uri(gs_uri: str, timeout_s: int = 900) -> None:
    """Imports a single file from GCS into the RAG corpus."""
    _init_vertex()
    op = rag.import_files(
        rag_corpus=RAG_CORPUS_NAME,
        gcs_source_uris=[gs_uri],
        chunk_size=1024,
        chunk_overlap=200,
    )
    op.result(timeout=timeout_s)

def _list_rag_files():
    """Lists all files in the RAG corpus."""
    _init_vertex()
    try:
        return list(rag.list_files(corpus_name=RAG_CORPUS_NAME))  # Pass required corpus_name
    except (AttributeError, NotImplementedError) as e:
        st.error(f"Listing files not supported by RAG API: {e}. Deletion may require manual cleanup or import history.")
        return []  # Return empty list if listing fails

def _delete_rag_file(file_name: str) -> None:
    """Deletes a single file from the RAG corpus."""
    _init_vertex()
    try:
        operation = rag.delete_file(name=file_name)
        if operation:
            operation.result(timeout=300)  # Poll for completion
            st.write(f"Successfully deleted: {file_name}")
        else:
            st.error(f"Deletion operation returned None for {file_name}")
    except Exception as e:
        st.error(f"Failed to delete {file_name}: {e}")

def delete_all_rag_files() -> int:
    """Deletes all files from the RAG corpus."""
    files = _list_rag_files()
    deleted = 0
    for f in files:
        try:
            file_name = f.name if hasattr(f, 'name') else f
            _delete_rag_file(file_name)
            deleted += 1
        except Exception as e:
            st.error(f"Error processing file: {e}")
    if not files:
        st.warning("No files found to delete or listing not supported. Ensure corpus is populated.")
    return deleted

def upload_all_from_staging() -> tuple[int, int]:
    """
    Uploads all files from staging to GCS, imports to RAG, moves to ingested dir.
    Returns (success_count, failure_count).
    """
    os.makedirs(STAGING_DIR, exist_ok=True)
    os.makedirs(INGESTED_DIR, exist_ok=True)

    files_to_process = [f for f in os.listdir(STAGING_DIR) if
                        os.path.isfile(os.path.join(STAGING_DIR, f)) and not f.startswith('.')]
    if not files_to_process:
        return 0, 0

    bucket = _ensure_gcs_bucket()
    success_count = 0
    failure_count = 0

    progress_bar = st.progress(0.0, text="Starting upload...")

    for i, filename in enumerate(files_to_process):
        src_path = os.path.join(STAGING_DIR, filename)
        progress_text = f"Processing ({i + 1}/{len(files_to_process)}): {filename}"
        progress_bar.progress((i) / len(files_to_process), text=progress_text)

        try:
            # Upload to GCS
            blob_name = f"{GCS_PREFIX}/{filename}"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(src_path)
            gs_uri = _gcs_uri(filename)

            # Import to RAG
            _import_single_gcs_uri(gs_uri, timeout_s=900)

            # Move to ingested dir
            dst_path = os.path.join(INGESTED_DIR, filename)
            shutil.move(src_path, dst_path)

            st.write(f"✅ Successfully imported: {filename}")
            success_count += 1
        except Exception as e:
            st.write(f"❌ Failed to import {filename}: {e}")
            failure_count += 1

        progress_bar.progress((i + 1) / len(files_to_process), text=progress_text)

    progress_bar.empty()
    return success_count, failure_count

def render_admin():
    """Renders admin UI for RAG document management."""
    st.title("BrainTransplant Admin Panel")
    st.write("Manage documents for Vertex AI RAG index.")

    if st.button("Clear RAG Index"):
        with st.spinner("Clearing RAG index..."):
            deleted_count = delete_all_rag_files()
            if deleted_count > 0:
                st.success(f"Successfully cleared {deleted_count} documents from RAG index.")
            elif deleted_count == 0:
                st.warning("No files found to delete or listing not supported. Ensure corpus is populated.")

    if st.button("Upload Files to RAG"):
        with st.spinner("Uploading files to RAG index..."):
            successes, failures = upload_all_from_staging()
            if not successes and not failures:
                st.warning("No files found in staging directory.")
