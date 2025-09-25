# Project: braintransplant-ai — File: src/rag/vertex_client.py
import os
import re
import json
import traceback
from typing import List, Tuple

import vertexai
from vertexai.preview import rag
from utils.logger import get_logger
from llm.adapter import call_llm  # For Gemini reranking

# ======= Explicit config (no defaults) =======
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "fresh-myth-471317-j9")
LOCATION = "europe-west3"
RAG_CORPUS_NAME = "projects/754198198954/locations/europe-west3/ragCorpora/2305843009213693952"

# High-recall caps
TOP_K_SNIPPETS = 50  # First pass
TOP_K_SNIPPETS_SECOND = 10  # Per sub-query in second pass
MAX_SUB_QUERIES = 3
MIN_SNIPPET_LEN = 20
MAX_CONTEXT_CHARS = 120_000

# Reranking config
ENABLE_SECOND_PASS = True  # Second RAG pass for multi-entity
ENABLE_RERANK = True  # Second evaluating model (Gemini-based)
RERANK_MODEL = "gemini-2.5-flash"  # Use Flash for faster reranking (no new config needed, just model name)
RERANK_BATCH_SIZE = 10  # Batch snippets for fewer LLM calls
RERANK_TIMEOUT_S = 10  # Per batch timeout


def _init_vertex(logger) -> None:
    if not PROJECT_ID or PROJECT_ID == "your-gcp-project-id":
        raise ValueError("GCP_PROJECT_ID is not set correctly.")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    logger.info(f"vertexai.init(project={PROJECT_ID}, location={LOCATION})")


def _retrieve_snippets_rag(logger, user_query: str, top_k: int) -> List[str]:
    """
    Use retrieval_query which is the actual function available in the SDK.
    This matches your original working implementation.
    """
    _init_vertex(logger)
    logger.info(f"RAG retrieval_query start | top_k={top_k} | query={user_query[:200]}")

    try:
        response = rag.retrieval_query(
            rag_resources=[
                rag.RagResource(
                    rag_corpus=RAG_CORPUS_NAME,
                )
            ],
            text=user_query,
            similarity_top_k=top_k,
        )
        logger.info("RAG retrieval_query succeeded")
    except Exception as e:
        logger.error(f"RAG retrieval_query failed: {e}\n{traceback.format_exc()}")
        raise

    # Parse response to extract snippets
    snippets: List[str] = []

    try:
        if hasattr(response, 'contexts') and hasattr(response.contexts, 'contexts'):
            contexts_list = response.contexts.contexts
        elif hasattr(response, 'contexts'):
            contexts_obj = response.contexts
            if hasattr(contexts_obj, 'items'):
                contexts_list = contexts_obj.items
            elif hasattr(contexts_obj, '__iter__'):
                contexts_list = list(contexts_obj)
            else:
                contexts_list = getattr(contexts_obj, 'contexts', [])
        else:
            contexts_list = []

        for context in contexts_list:
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

        if hasattr(response, 'contexts'):
            logger.error(f"Contexts type: {type(response.contexts)}")
            logger.error(f"Contexts attributes: {dir(response.contexts)}")

    logger.info(f"RAG retrieval_query done | snippets={len(snippets)}")
    return snippets


def _decompose_query(logger, user_query: str) -> List[str]:
    """Decompose multi-entity query into sub-queries (e.g., 'compare A B C' -> ['A', 'B', 'C'])."""
    lower_q = user_query.lower()
    entities = re.findall(r'\b(roche|lonza|sandoz)\b', lower_q)  # Simple entity extraction
    sub_queries = [f"{entity} {user_query.split(' of ')[0].split('compare ')[-1]}" for entity in set(entities)]  # e.g., "roche assets"
    logger.info(f"Decomposed into {len(sub_queries)} sub-queries: {sub_queries}")
    return sub_queries[:MAX_SUB_QUERIES]


def _gemini_rerank(logger, user_query: str, snippets: List[str]) -> List[str]:
    """Rerank snippets using Gemini (Pro or Flash). Returns sorted snippets high-to-low score."""
    if not snippets:
        return []

    batches = [snippets[i:i + RERANK_BATCH_SIZE] for i in range(0, len(snippets), RERANK_BATCH_SIZE)]
    ranked_snippets = []

    for batch in batches:
        system_prompt = (
            "You are a reranker. For each snippet, score its relevance to the query on a scale of 1-10. "
            "Output strict JSON array of scores only, matching the order of snippets."
        )
        prompt = f"Query: {user_query}\nSnippets:\n" + "\n".join(f"[{i+1}] {s[:200]}" for i, s in enumerate(batch))
        try:
            raw = call_llm(system_prompt, prompt, timeout_s=RERANK_TIMEOUT_S, model=RERANK_MODEL)
            scores = json.loads(raw)
            if len(scores) != len(batch):
                raise ValueError("Score length mismatch")
            ranked_snippets.extend(zip(scores, batch))
        except Exception as e:
            logger.error(f"Rerank batch failed: {e}. Skipping batch.")
            ranked_snippets.extend([(0, s) for s in batch])  # Fallback low score

    ranked_snippets.sort(key=lambda x: x[0], reverse=True)
    return [s for score, s in ranked_snippets]


def get_grounded_context(user_query: str) -> Tuple[str, List[str]]:
    """
    Retrieval with second RAG pass for multi-entity queries and reranking for quality.
    Returns (context_text, citations).
    """
    logger = get_logger("btai.rag.client")

    try:
        snippets = _retrieve_snippets_rag(logger, user_query, TOP_K_SNIPPETS)
    except Exception as e:
        logger.error(f"Failed to retrieve snippets: {e}")
        return "Error retrieving documents. Please try again.", []

    if not snippets:
        logger.info("no snippets returned")
        return "No relevant documents found.", []

    # Rerank snippets (second evaluating model with Gemini)
    if ENABLE_RERANK:
        snippets = _gemini_rerank(logger, user_query, snippets)

    # Second RAG pass for multi-entity queries
    if ENABLE_SECOND_PASS and 'compare' in user_query.lower():
        sub_queries = _decompose_query(logger, user_query)
        for sub_q in sub_queries:
            try:
                sub_snippets = _retrieve_snippets_rag(logger, sub_q, TOP_K_SNIPPETS_SECOND)
                snippets.extend(sub_snippets)
            except Exception as e:
                logger.error(f"Second pass failed for sub-query '{sub_q}': {e}")

        # Dedup after second pass
        snippets = list(set(snippets))  # Simple dedup by exact match

    # Head/tail emphasis: Top 3 first, 2 strong at end, middle in between
    head = snippets[:3]
    tail = snippets[-2:] if len(snippets) > 5 else []
    middle = snippets[3:-2] if len(snippets) > 5 else snippets[3:]

    ordered = head + middle + tail

    parts: List[str] = []
    total = 0
    citations: List[str] = []  # Empty for now, as no doc IDs available

    for i, snip in enumerate(ordered, start=1):
        s = (snip or "").strip()
        if len(s) < MIN_SNIPPET_LEN:
            continue
        line = f"[{i}] {s}\n"
        if total + len(line) > MAX_CONTEXT_CHARS:
            logger.info(f"context cap reached at {i - 1} snippets, chars={total}")
            break
        parts.append(line)
        total += len(line)

    context = "".join(parts)
    logger.info(f"context built | ctx_chars={len(context)} | citations={len(citations)}")
    return context, citations
