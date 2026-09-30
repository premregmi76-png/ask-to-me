import os
import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

st.set_page_config(page_title="NEA Level 5 - Ask To Me", page_icon="⚡", layout="wide")

# API Key
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
if not api_key:
    st.error("कृपया Streamlit Secrets मा GEMINI_API_KEY राख्नुहोस्।")
    st.stop()

# REST Mode
genai.configure(api_key=api_key, transport="rest")

NOTES_DIR = "uploaded_notes"
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

# NotebookLM को लिङ्क
NOTEBOOK_URL = "https://gemini.google.com/notebook/95067217-c097-43c8-9ffa-fe053d411f02"

with st.sidebar:
    st.header("📚 नोट व्यवस्थापन (Admin)")
    uploaded_files = st.file_uploader("नयाँ नोट अपलोड गर्नुहोस् (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            with open(os.path.join(NOTES_DIR, file.name), "wb") as f:
                f.write(file.getbuffer())
        st.cache_data.clear()
        st.success("नयाँ नोट सुरक्षित भयो!")
    
    st.markdown("---")
    st.write("📁 **अपलोड भएका फाइलहरू:**")
    for f in os.listdir(NOTES_DIR):
        st.caption(f"• {f}")
        
    st.markdown("---")
    st.info("💡 **असीमित अध्ययनको लागि:**")
    st.link_button("🚀 Open NotebookLM Hub", NOTEBOOK_URL)

@st.cache_data
def get_notes():
    text = ""
    if os.path.exists(NOTES_DIR):
        for f in os.listdir(NOTES_DIR):
            p = os.path.join(NOTES_DIR, f)
            if f.endswith(".pdf"):
                try:
                    reader = PdfReader(p)
                    for page in reader.pages[:25]:
                        t = page.extract_text()
                        if t:
                            text += t + "\n"
                except Exception:
                    pass
            elif f.endswith(".txt"):
                try:
                    with open(p, "r", encoding="utf-8") as file:
                        text += file.read() + "\n"
                except Exception:
                    pass
    return text[:30000]

notes_content = get_notes()

prompt = f"""
तपाईं नेपाल विद्युत प्राधिकरण (NEA) तह-५ (इलेक्ट्रिकल सुपरभाइजर) परीक्षाका लागि समर्पित AI शिक्षक हुनुहुन्छ।

उपलब्ध नोटहरू:
{notes_content if notes_content else "पाठ्यक्रम अनुसार उत्तर दिनुहोस्।"}

नियमहरू:
1. विद्यार्थीले नेपालीमा सोधे नेपालीमा, अंग्रेजीमा सोधे अंग्रेजीमा वा आवश्यकता अनुसार स्पष्ट प्राविधिक भाषामा उत्तर दिनुहोस्।
2. उत्तर परीक्षाको शैलीमा बुँदागत (Bullet Points), सूत्र, र परिभाषा स्पष्ट खुलाएर दिनुहोस्।
"""

model = genai.GenerativeModel("gemini-flash-latest", system_instruction=prompt)

st.title("⚡ NEA Level 5 Electrical - 'Ask To Me'")
st.caption("नेपाल विद्युत प्राधिकरण तह-५ अध्ययन सहयोगी")

# NotebookLM लाई माथि नै जोड्ने ब्यानर
st.success(f"📖 **सम्पूर्ण नोटहरू र असीमित प्रश्न सोध्नका लागि:** [यहाँ क्लिक गरी Google NotebookLM खोल्नुहोस्]({NOTEBOOK_URL})")

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
            try:
                response = model.generate_content(q, request_options={"timeout": 60})
                ans = response.text
                st.markdown(ans)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
            except Exception as err:
                if "429" in str(err):
                    st.warning(f"गुगलको निःशुल्क कोटा प्रति मिनेट सीमित छ। असीमित र तत्काल प्रश्न सोध्न कृपया [यहाँ क्लिक गरेर हाम्रो NotebookLM प्रयोग गर्नुहोस्]({NOTEBOOK_URL})।")
                else:
                    st.error(f"त्रुटि: {err}")
