# Project: braintransplant-ai — File: src/rag/vertex_client.py
import os
import traceback
from typing import List, Tuple

import vertexai
from vertexai.preview import rag
from utils.logger import get_logger

# ======= Explicit config (no defaults) =======
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "fresh-myth-471317-j9")
LOCATION = "europe-west3"
RAG_CORPUS_NAME = "projects/754198198954/locations/europe-west3/ragCorpora/2305843009213693952"

# High-recall caps
TOP_K_SNIPPETS = 10  # Start with reasonable number, can increase if needed
MAX_CONTEXT_CHARS = 120_000
MIN_SNIPPET_LEN = 20


def _init_vertex(logger) -> None:
    if not PROJECT_ID or PROJECT_ID == "your-gcp-project-id":
        raise ValueError("GCP_PROJECT_ID is not set correctly.")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    logger.info(f"vertexai.init(project={PROJECT_ID}, location={LOCATION})")


def _retrieve_snippets_rag(logger, user_query: str) -> List[str]:
    """
    Use retrieval_query which is the actual function available in the SDK.
    This matches your original working implementation.
    """
    _init_vertex(logger)
    logger.info(f"RAG retrieval_query start | top_k={TOP_K_SNIPPETS} | query={user_query[:200]}")

    try:
        # Use retrieval_query - the actual function that exists
        response = rag.retrieval_query(
            rag_resources=[
                rag.RagResource(
                    rag_corpus=RAG_CORPUS_NAME,
                )
            ],
            text=user_query,
            similarity_top_k=TOP_K_SNIPPETS,
        )
        logger.info("RAG retrieval_query succeeded")
    except Exception as e:
        logger.error(f"RAG retrieval_query failed: {e}\n{traceback.format_exc()}")
        raise

    # Parse response to extract snippets
    snippets: List[str] = []

    try:
        # Try different ways to access the contexts
        if hasattr(response, 'contexts') and hasattr(response.contexts, 'contexts'):
            # If contexts is nested
            contexts_list = response.contexts.contexts
        elif hasattr(response, 'contexts'):
            # If contexts is directly accessible but not iterable, try to get its items
            contexts_obj = response.contexts
            if hasattr(contexts_obj, 'items'):
                contexts_list = contexts_obj.items
            elif hasattr(contexts_obj, '__iter__'):
                contexts_list = list(contexts_obj)
            else:
                # Try to access as a list-like attribute
                contexts_list = getattr(contexts_obj, 'contexts', [])
        else:
            contexts_list = []

        for context in contexts_list:
            # Try different ways to access content
            content = ""

            if hasattr(context, 'source_snippet'):
                if hasattr(context.source_snippet, 'text'):
                    content = context.source_snippet.text.replace("\n", " ")
            elif hasattr(context, 'text'):
                content = context.text.replace("\n", " ")
            elif hasattr(context, 'chunk_content'):
                content = context.chunk_content.replace("\n", " ")

            if content and len(content) >= MIN_SNIPPET_LEN:
                snippets.append(content.strip())

    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        logger.error(f"Response type: {type(response)}")
        logger.error(f"Response attributes: {dir(response)}")

        # If we have contexts, print its type and attributes for debugging
        if hasattr(response, 'contexts'):
            logger.error(f"Contexts type: {type(response.contexts)}")
            logger.error(f"Contexts attributes: {dir(response.contexts)}")

    logger.info(f"RAG retrieval_query done | snippets={len(snippets)}")
    return snippets


def get_grounded_context(user_query: str) -> Tuple[str, List[str]]:
    """
    High-recall retrieval and CONTEXT builder.
    Returns (context_text, citations).
    """
    logger = get_logger("btai.rag.client")

    try:
        snippets = _retrieve_snippets_rag(logger, user_query)
    except Exception as e:
        logger.error(f"Failed to retrieve snippets: {e}")
        return "Error retrieving documents. Please try again.", []

    if not snippets:
        logger.info("no snippets returned")
        return "No relevant documents found.", []

    parts: List[str] = []
    total = 0
    citations = set()

    for i, snip in enumerate(snippets, start=1):
        s = (snip or "").strip()
        if len(s) < MIN_SNIPPET_LEN:
            continue
        line = f"[{i}] {s}\n"
        if total + len(line) > MAX_CONTEXT_CHARS:
            logger.info(f"context cap reached at {i - 1} snippets, chars={total}")
            break
        parts.append(line)
        total += len(line)
        # Add meaningful citation if you have document names
        citations.add("Corporate Reports")

    context = "".join(parts)
    logger.info(f"context built | ctx_chars={len(context)} | citations={len(citations)}")
    return context, sorted(citations)
