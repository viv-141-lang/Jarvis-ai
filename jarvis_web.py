import streamlit as st
import google.generativeai as genai
import os

# Set page configuration
st.set_page_config(page_title="JARVIS AI", page_icon="🤖", layout="wide")

# Custom Iron Man / JARVIS Cyan Glow Aesthetic
st.markdown("""
    <style>
    .stApp { background-color: #0a1128; color: #00f0ff; }
    h1 { color: #00f0ff; text-shadow: 0 0 10px #00f0ff; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #001f3f; color: #00f0ff; border: 1px solid #00f0ff; box-shadow: 0 0 5px #00f0ff; }
    .stButton>button:hover { background-color: #00f0ff; color: #0a1128; }
    </style>
""", unsafe_with_html=True)

st.title("🤖 J.A.R.V.I.S. // Web Interface")
st.write("---")

# Retrieve API key securely from Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("🔑 API Key missing! Please configure GEMINI_API_KEY in your Streamlit Cloud Secrets dashboard.")
    st.stop()

# Initialize Model
model = genai.GenerativeModel('gemini-1.5-flash', 
                              system_instruction="You are JARVIS, a polite, witty, ultra-intelligent, and professional AI assistant inspired by Iron Man. Address the user with respect, using terms like 'Sir' or 'Ma'am' naturally.")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Sidebar Memory Bank
with st.sidebar:
    st.markdown("### 📊 CORE SYSTEMS")
    st.metric(label="AI Core Status", value="ONLINE")
    st.write("---")
    st.markdown("### 🧠 MEMORY BANK Quick Actions")
    if st.button("Recall Latest Insights"):
        st.info("Searching semantic database... (ChromaDB Integration Ready)")

# Display Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("What are your commands, Sir?"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            response = model.generate_content(prompt)
            full_response = response.text
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"System Error: {str(e)}")
