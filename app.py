import os
import json
import urllib.request
import streamlit as st
from pypdf import PdfReader

# पेज कन्फिगरेसन
st.set_page_config(
    page_title="NEA Level 5 Electrical - Ask To Me", 
    page_icon="⚡", 
    layout="wide"
)

# Groq API Key
api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
if not api_key:
    st.error("प्रणाली कन्फिगरेसन (GROQ_API_KEY) मिलाउन बाँकी छ।")
    st.stop()

NOTES_DIR = "uploaded_notes"
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

# साइडबार: नोटहरू अपलोड गर्ने ठाउँ
with st.sidebar:
    st.markdown("### 📚 अध्ययन सामग्री (नोटहरू)")
    st.caption("यहाँ अपलोड गरिएका नोटहरूबाट मात्र प्रणालीले उत्तर दिनेछ।")
    uploaded_files = st.file_uploader("नोट अपलोड गर्नुहोस् (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            with open(os.path.join(NOTES_DIR, file.name), "wb") as f:
                f.write(file.getbuffer())
        st.cache_data.clear()
        st.success("नयाँ नोट सुरक्षित गरियो!")
    
    st.markdown("---")
    st.write("📁 **हाल उपलब्ध नोटहरू:**")
    files = os.listdir(NOTES_DIR)
    if files:
        for f in files:
            st.caption(f"• {f}")
    else:
        st.warning("कुनै नोट अपलोड गरिएको छैन।")

# नोटहरूबाट टेक्स्ट पढ्ने
@st.cache_data
def get_notes():
    text = ""
    if os.path.exists(NOTES_DIR):
        for f in os.listdir(NOTES_DIR):
            p = os.path.join(NOTES_DIR, f)
            if f.endswith(".pdf"):
                try:
                    reader = PdfReader(p)
                    for page in reader.pages:
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
    return text[:60000]

notes_content = get_notes()

# कडा शिक्षक नियम (१००% नोट भित्रबाट मात्र उत्तर आउने)
system_prompt = f"""
तपाईंको एकमात्र काम तल दिइएको [आधिकारिक नोटहरू] पढेर विद्यार्थीको प्रश्नको उत्तर दिनु हो।

[आधिकारिक नोटहरू]:
{notes_content if notes_content.strip() else "कुनै पनि नोटहरू उपलब्ध छैनन्।"}

कडा निर्देशनहरू (Strict Guardrails):
१. तपाईंले आफ्नो व्यक्तिगत वा बाहिरी ज्ञान प्रयोग गर्न कडा रूपमा निषेध गरिएको छ।
२. तपाईंको उत्तर शतप्रतिशत माथि दिइएको [आधिकारिक नोटहरू] मा लेखिएका तथ्यहरूमा मात्र आधारित हुनुपर्छ।
३. यदि विद्यार्थीले सोधेको प्रश्नको उत्तर माथिको [आधिकारिक नोटहरू] भित्र स्पष्ट रूपमा लेखिएको छैन भने, कुनै पनि अनुमान वा बाहिरी उत्तर नदिनुहोस्। सिधै यो निश्चित वाक्य मात्र जवाफ दिनुहोस्:
   "माफ गर्नुहोला, यो प्रश्नको उत्तर उपलब्ध गराइएका नोटहरूमा समावेश छैन। कृपया उपलब्ध नोटहरूसँग सम्बन्धित प्रश्न मात्र सोध्नुहोला।"
४. यदि नोट भित्र उत्तर भेटियो भने, विद्यार्थीले सोधेको भाषामा (नेपाली वा English) बुँदागत रूपमा नोटकै आधारमा स्पष्ट उत्तर दिनुहोस्।
"""

# मुख्य वेबसाइट शीर्षक
st.title("⚡ नेपाल विद्युत प्राधिकरण (NEA) तह-५")
st.subheader("इलेक्ट्रिकल सुपरभाइजर — आधिकारिक नोटमा आधारित प्रश्न-उत्तर प्रणाली")
st.caption("यो प्रणालीले केवल उपलब्ध गराइएका आधिकारिक नोटहरू भित्रबाट मात्र उत्तर दिन्छ।")
st.markdown("---")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# विद्यार्थीको प्रश्न इनपुट
if q := st.chat_input("उपलब्ध नोट सम्बन्धी प्रश्न यहाँ सोध्नुहोस्..."):
    st.session_state.chat_history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("नोटहरू हेरेर उत्तर खोज्दै..."):
            try:
                req_data = json.dumps({
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": q}
                    ],
                    "temperature": 0.0  # शून्य कल्पनाशीलता (नोटमा जे छ त्यही मात्र आउने)
                }).encode("utf-8")

                req = urllib.request.Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=req_data,
                    headers={
                        "Authorization": f"Bearer {api_key.strip()}",
                        "Content-Type": "application/json",
                        "User-Agent": "StreamlitApp"
                    }
                )

                with urllib.request.urlopen(req, timeout=45) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    ans = result["choices"][0]["message"]["content"]
                
                st.markdown(ans)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
            except Exception as err:
                st.error(f"त्रुटि देखा पर्यो: {err}")
