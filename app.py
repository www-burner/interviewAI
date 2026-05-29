import streamlit as st
import os
from openai import OpenAI
import PyPDF2
import time

# --- INITIALIZATION & CONFIG ---
st.set_page_config(page_title="InterviewAI", page_icon="🎤", layout="wide")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# --- SESSION STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

# --- HELPER FUNCTIONS ---
def extract_text_from_pdf(file):
    """Extracts text from an uploaded PDF resume."""
    try:
        reader = PyPDF2.PdfReader(file)
        text = "".join([page.extract_text() for page in reader.pages])
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def get_system_prompt(role, difficulty, i_type, resume):
    """Generates the anti-hallucination system prompt."""
    prompt = (
        f"You are an expert, professional technical and behavioral interviewer for a {role} position. "
        f"The interview difficulty is {difficulty}, and the focus is {i_type}. "
        "RULES: "
        "1. Ask only ONE question at a time. Wait for the user's response. "
        "2. When the user responds, evaluate their answer. Provide a brief, structured JSON-like response format in your thought process, but output it as clear Markdown: "
        "\n- **Feedback**: (Brief critique)\n- **Confidence Score**: (X/10)\n- **Improvement**: (How to fix it)\n- **Stronger Answer**: (A brief better example)\n\n"
        "3. After providing feedback, ask the NEXT question or a follow-up question. "
        "4. Do NOT hallucinate technologies or concepts. Stay strictly within the bounds of standard industry practices. "
        "5. Keep the tone professional, encouraging, but realistic."
    )
    if resume:
        prompt += f"\n\nTailor your questions to the candidate's resume here: {resume[:2000]}"
    return prompt

def generate_ai_response():
    """Calls the OpenAI API with the current conversation history."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=st.session_state.messages,
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {e}"

# --- SIDEBAR & DASHBOARD ---
with st.sidebar:
    st.header("⚙️ Interview Settings")
    
    role = st.text_input("Job Role", "Software Engineer")
    difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced", "Expert"])
    interview_type = st.selectbox("Interview Type", ["Technical", "Behavioral", "Casual", "System Design"])
    
    st.divider()
    
    st.header("📄 Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF Resume (Optional)", type="pdf")
    if uploaded_file is not None:
        st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
        st.success("Resume processed!")

    st.divider()
    
    if st.button("🚀 Start / Reset Interview", use_container_width=True, type="primary"):
        st.session_state.messages = [
            {"role": "system", "content": get_system_prompt(role, difficulty, interview_type, st.session_state.resume_text)}
        ]
        st.session_state.interview_started = True
        
        # Trigger the AI to ask the first question
        with st.spinner("Preparing your first question..."):
            first_q = generate_ai_response()
            st.session_state.messages.append({"role": "assistant", "content": first_q})

# --- MAIN UI ---
st.title("🎤 InterviewAI Dashboard")
st.markdown("Practice your interview skills with real-time feedback from GPT-4o.")

if not st.session_state.interview_started:
    st.info("👈 Please configure your settings in the sidebar and click 'Start Interview'.")
else:
    # Display chat history (skipping the hidden system prompt)
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # User Input
    if user_input := st.chat_input("Type your answer here..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate and display AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your response..."):
                start_time = time.time()
                ai_response = generate_ai_response()
                elapsed = round(time.time() - start_time, 2)
                
                st.markdown(ai_response)
                st.caption(f"⏱️ Response generated in {elapsed}s")
                
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
