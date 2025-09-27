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
from utils.logger import get_logger

load_dotenv()

def view_chat() -> None:
    """
    Render chat UI with verbose response and response time display; logs to /app/outputs/logs/braintransplant.log.
    """
    logger = get_logger("btai.ui.chat")
    st.set_page_config(page_title="BC2 AI Assistant – Sabrina", page_icon="⛰️")
    inject_chat_css()

    # st.title("BC2 AI Assistant – Sabrina")
    provider = os.environ.get("LLM_PROVIDER", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip()
    # if provider and model:
    #     st.caption(f"Model: {provider} / {model}")

    logger.info(f"UI loaded | provider={provider} | model={model}")

    # --- Dynamic Intro: Overview of Documents + Examples (via RAG) ---
    if "intro_shown" not in st.session_state:
        st.session_state["intro_shown"] = True
        try:
            t0 = time.perf_counter()
            # RAG query for corpus overview
            overview_context, _ = get_grounded_context("Give a two-sentence overview of all loaded documents and their topics.")
            overview = overview_context.strip().split('\n')[0]  # Take first clean line

            # RAG query for example questions
            examples_context, _ = get_grounded_context("Extract 2-3 real example questions users might ask based on document content.")
            ex_lines = [l.strip() for l in examples_context.split('\n') if l.strip().startswith('-') or l.strip().startswith('*')][:3]  # Extract bullet-like lines

            # Build dynamic markdown
            dynamic_md = (
                f"Hello! I'm Sabrina, your Basecamp 2.0 AI Assistant.\n\n"
                f"Basecamp 2.0 is Roche's Product Lifecycle Management (PLM) system, designed to manage "
                f"manufacturing process specifications across the network, including steps, activities, parameters, and "
                f"materials. I can provide insights and explanations on its core functions.\n\n"
                f"Overview of loaded documents: {overview}\n\n"
                f"You can ask such questions as:\n" + "\n".join(ex_lines)
            )
            st.markdown(dynamic_md)
            logger.info(f"Dynamic intro generated | dt={(time.perf_counter() - t0):.2f}s")
        except Exception as e:
            logger.error(f"Dynamic intro failed: {e}")
            st.markdown("Hello! I'm Sabrina, your Basecamp 2.0 AI Assistant. Ask me about manufacturing specs or processes.")

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

        # 2) AUGMENT & GENERATE: LLM call with verbose mode
        system_prompt = (
            "You are a helpful assistant named 'BC2 AI Assistant'. Based ONLY on the provided context snippets, "
            "answer the user's question in sufficient detail so that user probably wouldn't even go to the source file, including breakdowns and explanations where needed and relevant. "
            "Be comprehensive enough so users have enough information without needing to open sources—provide tables or lists if data allows. "
            "If the context does not contain the answer, state that you do not have enough information from the provided documents."
        )
        prompt = f"CONTEXT:\n{context_for_llm}\n\nUSER QUESTION:\n{user_q}"

        try:
            t_llm0 = time.perf_counter()
            final_answer = call_llm(system_prompt, prompt, timeout_s=60)  # Removed stream=True
            t_llm = time.perf_counter() - t_llm0
            # Simulate partial progress (fallback for no streaming)
            st.write("Generating response... Initializing analysis.")
            time.sleep(1)  # Simulate first chunk delay (~1s for user feedback)
            st.write(final_answer)  # Full response
            logger.info(f"LLM ok | ans_chars={len(final_answer)} | dt={t_llm:.2f}s")
        except Exception as e:
            logger.error(f"LLM error | {e}\n{traceback.format_exc()}")
            st.error(f"Error communicating with the language model: {e}")
            return

        # 3) DISPLAY: Finalize with sources (if not streamed) and response time
        total_time = time.perf_counter() - t0
        final_answer_with_sources = final_answer
        if citations and not any(c in final_answer for c in citations):  # Add sources if LLM didn't
            sources_md = "\n\n**Sources:**\n" + "\n".join(f"- {c}" for c in sorted(citations))
            final_answer_with_sources += sources_md
            st.markdown(sources_md)

        # Display response time
        st.markdown(f"**Response generated in {total_time:.2f} seconds.**")

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

if __name__ == "__main__":
    view_chat()
