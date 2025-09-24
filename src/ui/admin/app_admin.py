import streamlit as st
import os
import shutil
import time
import vertexai
from vertexai.preview import rag
from google.cloud import storage

# --- Configuration ---
PROJECT_ID = "fresh-myth-471317-j9"
LOCATION = "europe-west3"
RAG_CORPUS_NAME = "projects/754198198954/locations/europe-west3/ragCorpora/2305843009213693952"
STAGING_DIR = "/app/data/uploads"  # Directory where DevOps places new files
INGESTED_DIR = "/app/data/ingested"  # Subfolder for successfully processed files

# Use a simple, predictable bucket name
GCS_BUCKET = f"{PROJECT_ID}-rag-staging"
GCS_PREFIX = "imports"


def init_vertex():
    """Initialize Vertex AI."""
    vertexai.init(project=PROJECT_ID, location=LOCATION)


def ensure_gcs_bucket():
    """Ensure GCS bucket exists for RAG staging."""
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        try:
            bucket = storage_client.create_bucket(GCS_BUCKET, location=LOCATION)
            st.info(f"Created bucket: {GCS_BUCKET}")
        except:
            bucket = storage_client.bucket(GCS_BUCKET)
        return bucket
    except Exception as e:
        st.error(f"Bucket error: {e}")
        return None


def upload_all_to_rag():
    """Upload all files from staging to RAG."""
    init_vertex()

    os.makedirs(STAGING_DIR, exist_ok=True)
    os.makedirs(INGESTED_DIR, exist_ok=True)

    files = [f for f in os.listdir(STAGING_DIR)
             if os.path.isfile(os.path.join(STAGING_DIR, f))]

    if not files:
        return 0, 0

    bucket = ensure_gcs_bucket()
    if not bucket:
        return 0, len(files)

    success = 0
    failed = 0

    for filename in files:
        source_path = os.path.join(STAGING_DIR, filename)
        try:
            # Upload to GCS
            blob_name = f"{GCS_PREFIX}/{filename}"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(source_path)
            gcs_uri = f"gs://{GCS_BUCKET}/{blob_name}"

            # Import to RAG (using preview API correctly)
            operation = rag.import_files(
                corpus_name=RAG_CORPUS_NAME,  # First positional argument
                gcs_uris=[gcs_uri],  # List of URIs
                chunk_size=1024,
                chunk_overlap=200
            )

            # Wait for import to complete
            result = operation.result(timeout=300)

            # Move to ingested folder on success
            dest_path = os.path.join(INGESTED_DIR, filename)
            shutil.move(source_path, dest_path)
            st.write(f"✅ Imported: {filename}")
            success += 1

        except Exception as e:
            st.error(f"Failed {filename}: {e}")
            failed += 1

    return success, failed


def delete_all_from_rag():
    """Delete all files from RAG corpus."""
    init_vertex()
    deleted = 0

    try:
        # List files using the correct API call (corpus name as first argument)
        files = list(rag.list_files(RAG_CORPUS_NAME))

        for file in files:
            try:
                # Delete using the file's full resource name
                rag.delete_file(name=file.name).result(timeout=60)
                deleted += 1
            except Exception as e:
                st.error(f"Failed to delete {file.name}: {e}")

    except Exception as e:
        st.error(f"Error listing files: {e}")

    return deleted


def show_current_rag_files():
    """Show files currently in RAG."""
    init_vertex()
    try:
        # List files with corpus name as first positional argument
        files = list(rag.list_files(RAG_CORPUS_NAME))

        if files:
            st.write(f"Files in corpus: **{len(files)}**")
            for file in files:
                # Get display name or extract from resource name
                display_name = getattr(file, 'display_name', None)
                if not display_name and hasattr(file, 'name'):
                    display_name = file.name.split('/')[-1]
                st.write(f"• {display_name or 'Unnamed'}")
        else:
            st.write("No files in RAG corpus")

    except Exception as e:
        st.error(f"Cannot list files: {e}")


def render_admin():
    """Simple admin interface with two buttons for RAG management."""
    st.title("Admin")

    # Show current RAG contents
    with st.expander("Current RAG Files", expanded=False):
        show_current_rag_files()

    # File count in staging
    staging_count = 0
    if os.path.exists(STAGING_DIR):
        staging_count = len([f for f in os.listdir(STAGING_DIR)
                             if os.path.isfile(os.path.join(STAGING_DIR, f))])

    st.info(f"Files in staging: {staging_count}")

    # Two main action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Remove All from RAG", type="secondary", use_container_width=True):
            with st.spinner("Removing all files..."):
                try:
                    deleted = delete_all_from_rag()
                    st.success(f"Deleted {deleted} files from RAG")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with col2:
        if st.button("📤 Upload All to RAG", type="primary", use_container_width=True):
            if staging_count > 0:
                with st.spinner("Uploading files..."):
                    try:
                        success, failed = upload_all_to_rag()
                        if success:
                            st.success(f"Uploaded {success} files to RAG")
                        if failed:
                            st.error(f"Failed: {failed} files")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("No files in staging to upload")
