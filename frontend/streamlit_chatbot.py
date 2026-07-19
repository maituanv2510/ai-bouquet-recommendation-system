import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from chatbot.chatbot_pipeline import ChatbotPipeline
from recommendation.recommendation_service import run_recommendation_from_state


st.set_page_config(
    page_title="AI Bouquet Chatbot",
    page_icon="💐",
    layout="centered"
)

st.title("💐 AI Bouquet Recommendation Chatbot")
st.caption(
    "Chatbot tư vấn bó hoa dựa trên nhu cầu, ngân sách và sở thích của khách hàng."
)


if "bot" not in st.session_state:
    st.session_state.bot = ChatbotPipeline(
        recommender_func=run_recommendation_from_state
    )


if "messages" not in st.session_state:
    st.session_state.messages = []


with st.sidebar:
    st.subheader("Current Requirements")

    current_state = st.session_state.bot.state.get_state()
    st.json(current_state)

    if st.button("Reset conversation"):
        st.session_state.bot.reset()
        st.session_state.messages = []
        st.rerun()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


user_message = st.chat_input("Nhập yêu cầu bó hoa của bạn...")

if user_message:
    st.session_state.messages.append({
        "role": "user",
        "content": user_message
    })

    with st.chat_message("user"):
        st.markdown(user_message)

    result = st.session_state.bot.chat(user_message)
    bot_response = result["message"]

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_response
    })

    with st.chat_message("assistant"):
        st.markdown(bot_response)

    with st.expander("Debug result"):
        st.json(result)