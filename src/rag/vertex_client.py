# Project: braintransplant-ai | File: rag_retrieval.py

import os
from typing import List, Tuple
import vertexai
from vertexai.preview import rag

# --- Configuration ---
PROJECT_ID = "fresh-myth-471317-j9"
LOCATION = "europe-west3"
RAG_CORPUS_NAME = "projects/754198198954/locations/europe-west3/ragCorpora/2305843009213693952"


def get_grounded_context(user_query: str) -> Tuple[str, List[str]]:
    """
    Calls the Vertex AI RAG Engine to retrieve relevant document snippets.

    Returns:
        A tuple containing:
        1. A formatted string of context snippets for the LLM.
        2. A list of source citations (document URIs).
    """
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    response = rag.retrieval_query(
        rag_resources=[
            rag.RagResource(
                rag_corpus=RAG_CORPUS_NAME,
            )
        ],
        text=user_query,
        similarity_top_k=5,
    )

    # --- Format the response for the LLM and UI ---
    context_snippets = ""
    citations = set()

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

        for i, context in enumerate(contexts_list):
            # Try different ways to access content and source
            content = ""
            source = ""

            if hasattr(context, 'source_snippet'):
                if hasattr(context.source_snippet, 'text'):
                    content = context.source_snippet.text.replace("\n", " ")
                if hasattr(context.source_snippet, 'source_uri'):
                    source = context.source_snippet.source_uri
            elif hasattr(context, 'text'):
                content = context.text.replace("\n", " ")
                source = getattr(context, 'source_uri', '')
            elif hasattr(context, 'chunk_content'):
                content = context.chunk_content.replace("\n", " ")
                source = getattr(context, 'source_uri', '')

            if content:
                context_snippets += f"[{i + 1}] {content}\n"
                if source:
                    citations.add(os.path.basename(source))

    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response type: {type(response)}")
        print(f"Response attributes: {dir(response)}")

        # If we have contexts, print its type and attributes for debugging
        if hasattr(response, 'contexts'):
            print(f"Contexts type: {type(response.contexts)}")
            print(f"Contexts attributes: {dir(response.contexts)}")

    if not context_snippets:
        return "No relevant documents found.", []

    return context_snippets, list(citations)
