import sys
from pathlib import Path

import streamlit as st


# =====================================================
# ROOT PATH
# =====================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))


# =====================================================
# IMPORT PROJECT MODULES
# =====================================================

from chatbot.chatbot_pipeline import ChatbotPipeline
from dialogue.qwen_dialogue_policy import QwenDialoguePolicy
from recommendation.recommendation_service import run_recommendation_from_state


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="AI Flower Shop Chatbot",
    page_icon="🌸",
    layout="wide",
)


# =====================================================
# LOAD QWEN POLICY
# =====================================================

@st.cache_resource
def load_qwen_policy():
    qwen_policy = QwenDialoguePolicy(
        adapter_path="outputs/qwen2.5-3b-dialogue-policy-final",
        max_new_tokens=96,
    )

    return qwen_policy


@st.cache_resource
def load_chatbot():
    qwen_policy = load_qwen_policy()

    chatbot = ChatbotPipeline(
        recommender_func=run_recommendation_from_state,
        dialogue_policy_func=qwen_policy.predict,
    )

    return chatbot


# =====================================================
# SESSION STATE INIT
# =====================================================

if "chatbot" not in st.session_state:
    st.session_state.chatbot = load_chatbot()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    st.title("🌸 AI Flower Shop")

    st.markdown("### Trạng thái hệ thống")

    chatbot = st.session_state.chatbot
    current_state = chatbot.state.get_state()

    st.json(current_state)

    st.markdown("---")

    if st.button("🔄 Reset hội thoại"):
        chatbot.reset()
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()

    st.markdown("---")

    st.markdown("### Debug")

    if st.session_state.last_result:
        with st.expander("Policy output"):
            st.json(st.session_state.last_result.get("policy_output", {}))

        with st.expander("Last recommendation"):
            st.json(st.session_state.last_result.get("last_recommendation", {}))
    else:
        st.caption("Chưa có debug output.")


# =====================================================
# MAIN UI
# =====================================================

st.title("🌸 AI Flower Shop Chatbot")
st.caption("Tư vấn bó hoa, kiểm tra tồn kho, tạo đơn hàng và sinh mã thanh toán.")

st.markdown(
    """
Bạn có thể thử các câu như:

- `tôi muốn mua một bó hoa tặng người yêu nhân dịp valentine`
- `tầm trên 700k đi`
- `những hoa trên có màu nào khác không`
- `cẩm tú cầu màu xanh làm chủ đạo nhé`
- `ok tôi lấy bó này`
- `Nguyễn Viết Anh - 0866660251 - Xóm Trung Tiến, Xã Hưng Đông, Vinh, Nghệ An`
"""
)


# =====================================================
# DISPLAY CHAT HISTORY
# =====================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =====================================================
# CHAT INPUT
# =====================================================

user_input = st.chat_input("Nhập yêu cầu của bạn...")

if user_input:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý..."):
            try:
                result = st.session_state.chatbot.chat(user_input)

                bot_message = result.get(
                    "message",
                    "Dạ em chưa xử lý được yêu cầu này ạ.",
                )

                st.markdown(bot_message)

                st.session_state.last_result = result

            except Exception as e:
                bot_message = (
                    "Dạ hệ thống đang gặp lỗi khi xử lý yêu cầu.\n\n"
                    f"**Chi tiết lỗi:** `{str(e)}`"
                )

                st.error(bot_message)

                st.session_state.last_result = {
                    "error": str(e),
                }

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": bot_message,
        }
    )

    st.rerun()