# Project: logs-ai-reporting-model-train — File: src/ui/chat_skin.py
import streamlit as st

def inject_chat_css():
    st.markdown(
        """
        <style>
        .user-row{display:flex;justify-content:flex-end;margin:8px 0;}
        .user-bubble{
            max-width:72%;
            background:rgba(255,255,255,0.06);
            border:1px solid rgba(255,255,255,0.08);
            border-radius:10px;
            padding:10px 12px;
            white-space:pre-wrap;
            word-break:break-word;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def user_bubble(text: str):
    st.markdown(
        f"<div class='user-row'><div class='user-bubble'>{text}</div></div>",
        unsafe_allow_html=True,
    )