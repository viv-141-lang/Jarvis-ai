import streamlit as st
import google.generativeai as genai
from groq import Groq
import ollama

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
""", unsafe_allow_html=True)

st.title("🤖 J.A.R.V.I.S. // Command Hub")
st.write("---")

# -------------------------
# NEURAL CORE ROUTER (SIDEBAR)
# -------------------------
with st.sidebar:
    st.markdown("### 🧠 NEURAL CORE ROUTER")
    # Let the user select which AI brain to use
    active_brain = st.radio("Active System Model:", [
        "Gemini 3.5 (Google Cloud)", 
        "Llama 3 (Groq Cloud)", 
        "Ollama (Local Rig)"
    ])
    st.write("---")
    st.markdown("### 📊 SYSTEM STATUS")
    st.metric(label="Active Core", value=active_brain.split(" ")[0])

# -------------------------
# API INITIALIZATION
# -------------------------
# 1. Initialize Google Gemini
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel('gemini-3.5-flash')
except Exception:
    pass # Handle gracefully if running purely locally without secrets

# 2. Initialize Groq (Free ultra-fast open-source API)
try:
    groq_client = Groq(api_key=st.secrets.get("GROQ_API_KEY", ""))
except Exception:
    groq_client = None

# -------------------------
# CHAT INTERFACE
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What are your commands, Sir?"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # --- ROUTE 1: GOOGLE GEMINI ---
            if active_brain == "Gemini 3.5 (Google Cloud)":
                response_stream = gemini_model.generate_content(prompt, stream=True)
                for chunk in response_stream:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
            
            # --- ROUTE 2: GROQ (e.g., Llama 3) ---
            elif active_brain == "Llama 3 (Groq Cloud)":
                if not groq_client:
                    st.error("Groq API Key missing.")
                    st.stop()
                
                response_stream = groq_client.chat.completions.create(
                    model="llama3-8b-8192", # Groq's free Llama 3 endpoint
                    messages=st.session_state.messages,
                    stream=True
                )
                for chunk in response_stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        placeholder.markdown(full_response + "▌")
            
            # --- ROUTE 3: LOCAL OLLAMA ---
            elif active_brain == "Ollama (Local Rig)":
                # Uses the local machine's network to talk to Ollama
                response_stream = ollama.chat(model='llama3', messages=st.session_state.messages, stream=True)
                for chunk in response_stream:
                    full_response += chunk['message']['content']
                    placeholder.markdown(full_response + "▌")

            # Final render
            placeholder.markdown(full_response)
        
        except Exception as e:
            st.error(f"System Error: {str(e)}\n\n(If using Ollama on the web, ensure your local port is exposed!)")
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
