"""
IPLytics Frontend — AI Assistant Page

Allows users to ask natural language questions about IPL players, teams,
venues, and matches, retrieving answers powered by Google Gemini and our database.
"""

import sys
from pathlib import Path

# Add project root to Python path so 'frontend' is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from frontend.api_client import ask_ai

# --- Page Config ---
st.set_page_config(
    page_title="AI Assistant | IPLytics",
    page_icon="🤖",
    layout="wide",
)

# --- Custom CSS for Chat Interface ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23, #1a1a2e);
    }
    
    /* Style suggestions buttons */
    div.stButton > button {
        background-color: #16213e !important;
        color: #8892b0 !important;
        border: 1px solid #e9456040 !important;
        border-radius: 20px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.9rem !important;
        transition: all 0.3s ease !important;
        text-align: left !important;
        width: 100% !important;
    }
    
    div.stButton > button:hover {
        background-color: #e9456015 !important;
        color: #e94560 !important;
        border-color: #e94560 !important;
        transform: translateY(-2px) !important;
    }
    
    /* Customize chat messages */
    div[data-testid="stChatMessage"] {
        background-color: #1a1a2e80 !important;
        border: 1px solid #e9456015 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
    }
    
    div[data-testid="stChatMessage"] img {
        border-radius: 50% !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Branding
with st.sidebar:
    st.markdown("### 🏏 IPLytics AI")
    st.caption("Google Gemini RAG Assistant")
    st.divider()
    
    st.markdown(
        "This assistant uses **Retrieval-Augmented Generation (RAG)**. "
        "It translates your natural language questions, extracts players, teams, "
        "or venues, retrieves real-time statistics from our database (2008–2025), "
        "and sends that data to Google Gemini to formulate an analytical response."
    )
    
    st.divider()
    
    # Clear conversation button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Page Header
st.title("🤖 AI Assistant")
st.markdown(
    "<p style='color: #8892b0; font-size: 1.15rem; margin-top: -0.5rem;'>"
    "Ask natural language questions about IPL history, player performances, "
    "team analytics, venue dynamics, or direct head-to-head comparisons."
    "</p>",
    unsafe_allow_html=True
)
st.divider()

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Suggested sample questions
suggested_questions = [
    "Who has scored the most runs in IPL history?",
    "Compare Virat Kohli and MS Dhoni",
    "Which venue has the highest average first innings score?",
    "How does Mumbai Indians perform at Wankhede Stadium?",
]

# Display suggestions if no chat history
if not st.session_state.messages:
    st.subheader("💡 Try asking one of these:")
    
    cols = st.columns(2)
    for idx, q in enumerate(suggested_questions):
        col = cols[idx % 2]
        if col.button(q, key=f"suggest_{idx}"):
            st.session_state.messages.append({"role": "user", "content": q})
            
            # Show the spinner and invoke API
            with st.spinner("🔍 IPLytics AI is analyzing database stats..."):
                response = ask_ai(q)
                if response and "answer" in response:
                    st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
                else:
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "⚠️ Sorry, I encountered an error communicating with the backend. Please ensure the backend server is running."
                    })
            st.rerun()

# Display chat history
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# User Chat Input
if prompt := st.chat_input("Ask IPLytics AI... e.g. Who has the lowest bowling economy?"):
    # Append user question
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Render user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        
    # Generate assistant answer
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🔍 IPLytics AI is analyzing database stats..."):
            response = ask_ai(prompt)
            if response and "answer" in response:
                answer = response["answer"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                err_msg = "⚠️ Sorry, I encountered an error communicating with the backend. Please ensure the backend server is running."
                st.markdown(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
