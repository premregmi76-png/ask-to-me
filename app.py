import os
import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

st.set_page_config(
    page_title="NEA Level 5 Electrical - Ask To Me", 
    page_icon="⚡", 
    layout="wide"
)

# API Key
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
if not api_key:
    st.error("सिस्टम कन्फिगरेसन अधुरो छ।")
    st.stop()

genai.configure(api_key=api_key, transport="rest")

NOTES_DIR = "uploaded_notes"
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

with st.sidebar:
    st.markdown("### 📚 अध्ययन सामग्री (Admin)")
    uploaded_files = st.file_uploader("नयाँ नोट अपलोड गर्नुहोस् (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            with open(os.path.join(NOTES_DIR, file.name), "wb") as f:
                f.write(file.getbuffer())
        st.cache_data.clear()
        st.success("नयाँ नोट सुरक्षित गरियो!")
    
    st.markdown("---")
    st.write("📁 **अपलोड भएका फाइलहरू:**")
    for f in os.listdir(NOTES_DIR):
        st.caption(f"• {f}")

@st.cache_data
def get_notes():
    text = ""
    if os.path.exists(NOTES_DIR):
        for f in os.listdir(NOTES_DIR):
            p = os.path.join(NOTES_DIR, f)
            if f.endswith(".pdf"):
                try:
                    reader = PdfReader(p)
                    for page in reader.pages[:10]:
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
    return text[:10000]

notes_content = get_notes()

system_rules = f"""
तपाईं नेपाल विद्युत प्राधिकरण (NEA) तह-५ (इलेक्ट्रिकल सुपरभाइजर) खुला प्रतियोगितात्मक परीक्षाका लागि विशेषज्ञ शिक्षक र डिजिटल सहायक ('Ask To Me') हुनुहुन्छ।

उपलब्ध आधिकारिक नोटहरू:
{notes_content if notes_content else "पाठ्यक्रम अनुसार उत्तर दिनुहोस्।"}

नियमहरू:
1. भाषा: विद्यार्थीले नेपालीमा सोधे नेपालीमा, अंग्रेजीमा सोधे अंग्रेजीमा वा आवश्यकता अनुसार स्पष्ट प्राविधिक भाषामा उत्तर दिनुहोस्।
2. ढाँचा: उत्तर परीक्षाको शैलीमा बुँदागत (Bullet Points), सूत्र, र परिभाषा स्पष्ट खुलाएर दिनुहोस्।
"""

# नयाँ AQ. Key लाई समर्थन गर्ने आधिकारिक मोडल
model = genai.GenerativeModel("gemini-flash-latest")

st.title("⚡ नेपाल विद्युत प्राधिकरण (NEA) तह-५")
st.subheader("इलेक्ट्रिकल सुपरभाइजर — परीक्षा सहयोगी प्रणाली ('Ask To Me')")
st.caption("पाठ्यक्रम (प्रथम र द्वितीय पत्र) सम्बन्धी कुनै पनि प्रश्न सोध्न सक्नुहुन्छ।")
st.markdown("---")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if q := st.chat_input("तपाईंको प्रश्न यहाँ टाइप गर्नुहोस् (उदा: What is Buchholz relay? वा विद्युत चोरी नियन्त्रण ऐनका मुख्य बुँदा)..."):
    st.session_state.chat_history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("उत्तर तयार गर्दै..."):
            try:
                full_payload = f"{system_rules}\n\n---\nविद्यार्थीको प्रश्न:\n{q}"
                response = model.generate_content(full_payload, request_options={"timeout": 60})
                ans = response.text
                st.markdown(ans)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
            except Exception as err:
                st.error(f"त्रुटि: {err}")
