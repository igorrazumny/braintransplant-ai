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

    # The top_k parameter goes directly inside the RagResource object
    response = rag.retrieval_query(
        rag_resources=[
            rag.RagResource(
                rag_corpus=RAG_CORPUS_NAME,
                top_k=5,  # Specify the number of results here
            )
        ],
        text=user_query,
    )

    # --- Format the response for the LLM and UI ---
    context_snippets = ""
    citations = set()
    for i, chunk in enumerate(response.get("chunks", [])):
        content = chunk.get("chunk_content", "").replace("\n", " ")
        source = chunk.get("source_uri", "")

        context_snippets += f"[{i+1}] {content}\n"
        if source:
            citations.add(os.path.basename(source))

    if not context_snippets:
        return "No relevant documents found.", []

    return context_snippets, list(citations)
