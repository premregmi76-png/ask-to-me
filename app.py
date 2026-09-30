import os
import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

st.set_page_config(page_title="NEA Level 5 - Ask To Me", page_icon="⚡", layout="wide")

api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if not api_key:
    st.error("कृपया Streamlit Secrets मा GEMINI_API_KEY राख्नुहोस्।")
    st.stop()

genai.configure(api_key=api_key)

NOTES_DIR = "uploaded_notes"
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

with st.sidebar:
    st.header("📚 नोट व्यवस्थापन (Admin)")
    uploaded_files = st.file_uploader("नयाँ नोट अपलोड गर्नुहोस् (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            with open(os.path.join(NOTES_DIR, file.name), "wb") as f:
                f.write(file.getbuffer())
        st.success("नोट सुरक्षित भयो!")

def get_notes():
    text = ""
    for f in os.listdir(NOTES_DIR):
        p = os.path.join(NOTES_DIR, f)
        if f.endswith(".pdf"):
            reader = PdfReader(p)
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        elif f.endswith(".txt"):
            with open(p, "r", encoding="utf-8") as file:
                text += file.read() + "\n"
    return text

notes_content = get_notes()

prompt = f"""
तपाईं नेपाल विद्युत प्राधिकरण (NEA) तह-५ (इलेक्ट्रिकल सुपरभाइजर) परीक्षाका लागि समर्पित AI शिक्षक हुनुहुन्छ।
पाठ्यक्रम:
१. प्रथम पत्र: सामान्य ज्ञान, गणित, संस्थागत/व्यवस्थापकीय ज्ञान, र कानून (NEA ऐन २०४१, विद्युत चोरी नियन्त्रण ऐन, महसुल विनियमावली)।
२. द्वितीय पत्र: Circuits, Electrical Machines, Measurements, Power Electronics, Power Plants, Transmission, Substations, Distribution, Safety।

उपलब्ध नोटहरू:
{notes_content if notes_content else "पाठ्यक्रम अनुसार उत्तर दिनुहोस्।"}

नियम:
- विद्यार्थीले सोधेको भाषामा (नेपाली/अंग्रेजी) परीक्षामा लेख्ने बुँदागत ढाँचामा सटिक उत्तर दिनुहोस्।
"""

model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=prompt)

st.title("⚡ NEA Level 5 Electrical - 'Ask To Me'")
st.caption("नेपाल विद्युत प्राधिकरण तह-५ अध्ययन सहयोगी")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if q := st.chat_input("तपाईंको प्रश्न यहाँ सोध्नुहोस्..."):
    st.session_state.chat_history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"):
        with st.spinner("उत्तर तयार गर्दै..."):
            ans = model.generate_content(q).text
            st.markdown(ans)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
