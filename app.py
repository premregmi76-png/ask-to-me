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

# Groq API Key लिने
api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
if not api_key:
    st.error("प्रणाली कन्फिगरेसन (GROQ_API_KEY) मिलाउन बाँकी छ।")
    st.stop()

NOTES_DIR = "uploaded_notes"
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

# साइडबार: नोटहरू अपलोड गर्ने ठाउँ
with st.sidebar:
    st.markdown("### 📚 अध्ययन सामग्री व्यवस्थापन")
    st.write("यहाँ नयाँ नोट अपलोड गर्नासाथ प्रणालीले यसैका आधारमा उत्तर दिनेछ।")
    uploaded_files = st.file_uploader("नयाँ नोट अपलोड गर्नुहोस् (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            with open(os.path.join(NOTES_DIR, file.name), "wb") as f:
                f.write(file.getbuffer())
        st.cache_data.clear()
        st.success("नयाँ नोट सुरक्षित गरियो!")
    
    st.markdown("---")
    st.write("📁 **अपलोड भएका फाइलहरू:**")
    files = os.listdir(NOTES_DIR)
    for f in files:
        st.caption(f"• {f}")

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
                    for page in reader.pages[:20]:
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

# कडा शिक्षक नियम (तपाईंले हाल्नुभएको नोटबाट मात्र उत्तर दिने):
system_prompt = f"""
तपाईं नेपाल विद्युत प्राधिकरण (NEA) तह-५ (इलेक्ट्रिकल सुपरभाइजर) परीक्षा तयारीका लागि समर्पित एक विशेषज्ञ डिजिटल शिक्षक हुनुहुन्छ।

उपलब्ध आधिकारिक नोट तथा सन्दर्भ सामग्रीहरू:
{notes_content if notes_content else "हाल कुनै विशेष नोट अपलोड भएको छैन। सामान्य NEA तह-५ पाठ्यक्रम अनुसार सीमित रहनुहोस्।"}

कडा नियमहरू (Strict Rules):
१. तपाईंले उपलब्ध गराइएका नोटहरू र नेपाल विद्युत प्राधिकरण तह-५ को पाठ्यक्रम (प्रथम र द्वितीय पत्र) भित्र रहेर मात्र उत्तर दिनुहोस्।
२. यदि विद्यार्थीले सोधेको प्रश्नको उत्तर यी नोटहरू वा पाठ्यक्रममा छैन भने, कुनै पनि बाहिरी गफ नलगाउनुहोस् र सिधै यो मात्र भन्नुहोस्:
   "यो प्रश्नको उत्तर उपलब्ध नोट वा पाठ्यक्रममा समावेश छैन। कृपया नेपाल विद्युत प्राधिकरण तह-५ (इलेक्ट्रिकल) पाठ्यक्रम सम्बन्धी विषयका प्रश्नहरू मात्र सोध्नुहोला।"
३. नेपालको इतिहास, चलचित्र, मनोरञ्जन वा अन्य असम्बन्धित विषय सोधिएमा पनि सिधै माथिको नियम २ अनुसार अस्वीकार गर्नुहोस्।
४. पाठ्यक्रम भित्रको प्रश्न भएमा नेपाली वा अंग्रेजीमा परीक्षामा लेख्ने उत्कृष्ट बुँदागत ढाँचा (Bullet Points), सूत्र, र परिभाषासहित स्पष्ट उत्तर दिनुहोस्।
"""

# मुख्य वेबसाइट शीर्षक
st.title("⚡ नेपाल विद्युत प्राधिकरण (NEA) तह-५")
st.subheader("इलेक्ट्रिकल सुपरभाइजर — परीक्षा सहयोगी प्रणाली ('Ask To Me')")
st.caption("उपलब्ध आधिकारिक नोटहरूका आधारमा परीक्षा केन्द्रित प्रश्न-उत्तर")
st.markdown("---")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# विद्यार्थीले सिधै यहीँ प्रश्न सोध्ने बाकस
if q := st.chat_input("तपाईंको प्रश्न यहाँ टाइप गर्नुहोस् (उदा: What is Buchholz relay? वा नेपाल विद्युत प्राधिकरण ऐनका मुख्य बुँदा)..."):
    st.session_state.chat_history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("नोटहरू हेरेर उत्तर तयार गर्दै..."):
            try:
                req_data = json.dumps({
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": q}
                    ],
                    "temperature": 0.3
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
