from __future__ import annotations

import streamlit as st

from pipeline import NutritionRAGSystem


st.set_page_config(page_title="NLP Nutrition RAG", layout="wide")
st.title("Hệ thống hỏi đáp dinh dưỡng (Hybrid RAG)")
st.caption("USDA + tài liệu y khoa tiếng Việt + LLM local")

if "bot" not in st.session_state:
    st.session_state.bot = NutritionRAGSystem()

if "history" not in st.session_state:
    st.session_state.history = []

for item in st.session_state.history:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

user_input = st.chat_input("Ví dụ: 100g ức gà có bao nhiêu protein?")

if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Đang phân tích và truy xuất dữ liệu..."):
            result = st.session_state.bot.answer(user_input)
        st.markdown(result.answer)
        with st.expander("Thông tin pipeline"):
            st.write("Intent:", result.intent)
            st.write("Entities:", result.entities)
            st.write("Sources:", result.sources)

    st.session_state.history.append({"role": "assistant", "content": result.answer})
