# Project: braintransplant-ai — File: src/ui/web/view_chat.py
import uuid
import streamlit as st
from llm.adapter import call_llm
from ui.web.chat_skin import inject_chat_css, user_bubble
from db.history import save_chat_turn
from rag.vertex_client import get_grounded_context
from ui.web.examples import EXAMPLES_MD # <-- Import the examples

def view_chat() -> None:
    """
    Main function to render the BC2 AI Assistant chat interface.
    """
    st.set_page_config(page_title="BC2 AI Assistant", page_icon="⛰️")
    inject_chat_css()

    st.title("BC2 AI Assistant")
    st.markdown(EXAMPLES_MD) # <-- Display the introductory text

    # --- Session State Initialization ---
    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())

    # --- Render Prior Conversation ---
    for turn in st.session_state["history"]:
        user_bubble(turn["user"])
        st.markdown(turn["assistant"])

    # --- Handle New User Input ---
    user_q = st.chat_input("Ask a question...")
    if not user_q:
        return

    user_bubble(user_q)

    with st.spinner("Searching documents and thinking..."):
        # 1. RETRIEVE: Get grounded context from Vertex AI Search
        try:
            context_for_llm, citations = get_grounded_context(user_q)
        except Exception as e:
            st.error(f"Error retrieving documents: {e}")
            return

        # 2. AUGMENT & GENERATE: Build the prompt and call the LLM
        system_prompt = (
            "You are a helpful assistant named 'BC2 AI Assistant'. Based ONLY on the provided context snippets, "
            "answer the user's question concisely. Your answer must be grounded in the facts from the context. "
            "If the context does not contain the answer, state that you do not have enough information from the provided documents."
        )
        prompt = (
            f"CONTEXT:\n{context_for_llm}\n\n"
            f"USER QUESTION:\n{user_q}"
        )

        try:
            final_answer = call_llm(system_prompt, prompt)
        except Exception as e:
            st.error(f"Error communicating with the language model: {e}")
            return

        # 3. DISPLAY: Show the answer and its sources to the user
        final_answer_with_sources = final_answer
        if citations:
            sources_md = "\n\n**Sources:**\n" + "\n".join(f"- {c}" for c in sorted(citations))
            final_answer_with_sources += sources_md

        st.markdown(final_answer_with_sources)

        # 4. SAVE: Update history and save to DB
        st.session_state["history"].append({"user": user_q, "assistant": final_answer_with_sources})

        save_chat_turn(
            session_id=st.session_state["session_id"],
            user_query=user_q,
            retrieved_context=context_for_llm,
            model_response=final_answer_with_sources
        )

if __name__ == "__main__":
    view_chat()
