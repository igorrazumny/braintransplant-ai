import os
from typing import List, Tuple

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine

# --- Configuration ---
# IMPORTANT: Replace these with the actual values from your Google Cloud project.
PROJECT_ID = "your-gcp-project-id"
LOCATION = "global"  # Use "global" unless you created your Search App in a specific region
DATA_STORE_ID = "your-data-store-id"


def get_grounded_context(user_query: str) -> Tuple[str, List[str]]:
    """
    Calls the Vertex AI Search API to retrieve relevant document snippets.

    Returns:
        A tuple containing:
        1. A formatted string of context snippets for the LLM.
        2. A list of source citations (document names).
    """
    client_options = (
        ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com")
        if LOCATION != "global"
        else None
    )
    client = discoveryengine.SearchServiceClient(client_options=client_options)

    serving_config = client.serving_config_path(
        project=PROJECT_ID,
        location=LOCATION,
        data_store=DATA_STORE_ID,
        serving_config="default_config",
    )

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=user_query,
        page_size=5,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True
            ),
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=5,
                include_citations=True,
            ),
        ),
    )

    response = client.search(request)

    context_snippets = ""
    citations = set()
    for i, result in enumerate(response.results):
        doc = result.document
        if doc.content_search_spec and doc.content_search_spec.snippet_spec:
             snippet = doc.content_search_spec.snippet_spec.snippet
             snippet = snippet.replace("\n", " ")
             context_snippets += f"[{i+1}] {snippet}\n"

        if doc.derived_struct_data and "title" in doc.derived_struct_data:
            citations.add(doc.derived_struct_data["title"])

    if not context_snippets:
        return "No relevant documents found.", []

    return context_snippets, list(citations)
