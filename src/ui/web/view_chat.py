# Project: braintransplant-ai — File: src/ui/web/view_chat.py
import os
import uuid
import time
import traceback
import streamlit as st
from dotenv import load_dotenv
from llm.adapter import call_llm
from ui.web.chat_skin import inject_chat_css, user_bubble
from db.history import save_chat_turn
from rag.vertex_client import get_grounded_context
from ui.web.examples import EXAMPLES_MD
from utils.logger import get_logger

load_dotenv()

def view_chat() -> None:
    """
    Render chat UI; all logs go to /app/outputs/logs/braintransplant.log via utils.logger.
    """
    logger = get_logger("btai.ui.chat")
    st.set_page_config(page_title="BC2 AI Assistant – Sabrina", page_icon="⛰️")
    inject_chat_css()

    st.title("BC2 AI Assistant – Sabrina")
    provider = os.environ.get("LLM_PROVIDER", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip()
    if provider and model:
        st.caption(f"Model: {model}")
    st.markdown(EXAMPLES_MD)

    logger.info(f"UI loaded | provider={provider} | model={model}")

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

    t0 = time.perf_counter()
    sess = st.session_state["session_id"]
    logger.info(f"Q start | session={sess} | len={len(user_q)} | text={user_q[:200]}")
    user_bubble(user_q)

    with st.spinner("Searching documents and thinking..."):
        # 1) RETRIEVE: Vertex RAG
        try:
            t_rag0 = time.perf_counter()
            context_for_llm, citations = get_grounded_context(user_q)
            t_rag = time.perf_counter() - t_rag0
            logger.info(f"RAG ok | ctx_chars={len(context_for_llm)} | cites={len(citations)} | dt={t_rag:.2f}s")
        except Exception as e:
            logger.error(f"RAG error | {e}\n{traceback.format_exc()}")
            st.error(f"Error retrieving documents: {e}")
            return

        # 2) AUGMENT & GENERATE: LLM call
        system_prompt = (
            "You are a helpful assistant named 'BC2 AI Assistant'. Based ONLY on the provided context snippets, "
            "answer the user's question concisely. Your answer must be grounded in the facts from the context. "
            "If the context does not contain the answer, state that you do not have enough information from the provided documents."
        )
        prompt = f"CONTEXT:\n{context_for_llm}\n\nUSER QUESTION:\n{user_q}"

        try:
            t_llm0 = time.perf_counter()
            final_answer = call_llm(system_prompt, prompt, timeout_s=60)
            t_llm = time.perf_counter() - t_llm0
            logger.info(f"LLM ok | ans_chars={len(final_answer)} | dt={t_llm:.2f}s")
        except Exception as e:
            logger.error(f"LLM error | {e}\n{traceback.format_exc()}")
            st.error(f"Error communicating with the language model: {e}")
            return

        # 3) DISPLAY: answer + sources
        final_answer_with_sources = final_answer
        if citations:
            sources_md = "\n\n**Sources:**\n" + "\n".join(f"- {c}" for c in sorted(citations))
            final_answer_with_sources += sources_md

        st.markdown(final_answer_with_sources)

        # 4) SAVE: persist
        st.session_state["history"].append({"user": user_q, "assistant": final_answer_with_sources})
        try:
            save_chat_turn(
                session_id=sess,
                user_query=user_q,
                retrieved_context=context_for_llm,
                model_response=final_answer_with_sources
            )
            logger.info("Turn saved")
        except Exception as e:
            logger.error(f"DB save error | {e}\n{traceback.format_exc()}")

    logger.info(f"Q end | session={sess} | total_dt={(time.perf_counter()-t0):.2f}s")

    # --- Sticky Footer Disclaimer (Option 3: Sticky footer at bottom of page) ---
    st.markdown(
        """
        <style>
        .sticky-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #2c2c2c;
            color: #ffffff;
            text-align: center;
            padding: 2px;
            font-size: 12px;
            z-index: 1000;
            opacity: 0.8;
        }
        </style>
        <div class="sticky-footer">
            Note: BC2 AI Assistant can make mistakes. Please always check the original documents.
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    view_chat()
