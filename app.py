import os
import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# पेज कन्फिगरेसन
st.set_page_config(
    page_title="NEA Level 5 Electrical - Ask To Me", 
    page_icon="⚡", 
    layout="wide"
)

# गोप्य रूपमा ब्याकएन्ड जडान गर्ने
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
if not api_key:
    st.error("सिस्टम कन्फिगरेसन अधुरो छ।")
    st.stop()

genai.configure(api_key=api_key, transport="rest")

NOTES_DIR = "uploaded_notes"
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

# एडमिनका लागि साइडबार (विद्यार्थीलाई नदेखिने गरी सामान्य रूपमा राख्ने)
with st.sidebar:
    st.markdown("### ⚙️ अध्ययन सामग्री व्यवस्थापन")
    uploaded_files = st.file_uploader("नोटहरू अपलोड गर्नुहोस् (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            with open(os.path.join(NOTES_DIR, file.name), "wb") as f:
                f.write(file.getbuffer())
        st.cache_data.clear()
        st.success("नयाँ सामग्री सुरक्षित गरियो!")
    
    st.markdown("---")
    st.write("📁 **उपलब्ध फाइलहरू:**")
    for f in os.listdir(NOTES_DIR):
        st.caption(f"• {f}")

# नोटहरू ब्याकग्राउन्डमा छिटो पढ्ने
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
तपाईं नेपाल विद्युत प्राधिकरण (NEA) तह-५ (इलेक्ट्रिकल सुपरभाइजर) खुला प्रतियोगितात्मक परीक्षाका लागि एक आधिकारिक डिजिटल शिक्षक हुनुहुन्छ।

उपलब्ध आधिकारिक अध्ययन सामग्री:
{notes_content if notes_content else "पाठ्यक्रम अनुसार उत्तर दिनुहोस्।"}

नियमहरू:
1. विद्यार्थीले नेपालीमा सोधे नेपालीमा, अंग्रेजीमा सोधे अंग्रेजीमा वा आवश्यकता अनुसार स्पष्ट प्राविधिक भाषामा उत्तर दिनुहोस्।
2. उत्तर परीक्षाको शैलीमा बुँदागत (Bullet Points), सूत्र, र परिभाषा स्पष्ट खुलाएर दिनुहोस्।
3. तपाईं केवल NEA तह-५ परीक्षा सहयोगी हुनुहुन्छ, बाहिरी कम्पनी वा प्रविधिको नाम नलिनुहोस्।
"""

model = genai.GenerativeModel("gemini-flash-latest", system_instruction=prompt)

# मुख्य वेबसाइट शीर्षक (कुनै बाहिरी ब्रान्डिङ नभएको)
st.title("⚡ नेपाल विद्युत प्राधिकरण (NEA) तह-५")
st.subheader("इलेक्ट्रिकल सुपरभाइजर — परीक्षा सहयोगी प्रणाली ('Ask To Me')")
st.markdown("पाठ्यक्रम (प्रथम र द्वितीय पत्र) सम्बन्धी कुनै पनि प्रश्न सोध्न सक्नुहुन्छ।")
st.markdown("---")

# दोहोरिने प्रश्नहरू छिटो दिन क्यास मेमोरी
if "faq_cache" not in st.session_state:
    st.session_state.faq_cache = {}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# च्याट हिस्ट्री देखाउने
for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# प्रश्न सोध्ने बाकस
if q := st.chat_input("तपाईंको प्रश्न यहाँ टाइप गर्नुहोस् (नेपाली वा English मा)..."):
    st.session_state.chat_history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        # यदि पहिले नै सोधिएको प्रश्न हो भने तत्काल उत्तर दिने
        clean_q = q.strip().lower()
        if clean_q in st.session_state.faq_cache:
            cached_ans = st.session_state.faq_cache[clean_q]
            st.markdown(cached_ans)
            st.session_state.chat_history.append({"role": "assistant", "content": cached_ans})
        else:
            with st.spinner("उत्तर तयार गर्दै..."):
                try:
                    response = model.generate_content(q, request_options={"timeout": 60})
                    ans = response.text
                    st.markdown(ans)
                    st.session_state.chat_history.append({"role": "assistant", "content": ans})
                    # भविष्यका लागि सेभ गर्ने
                    st.session_state.faq_cache[clean_q] = ans
                except Exception as err:
                    if "429" in str(err):
                        st.warning("अहिले धेरै विद्यार्थीहरू सक्रिय रहेकाले सर्भर व्यस्त छ। कृपया ३० सेकेन्ड पर्खेर पुन: सोध्नुहोस्।")
                    else:
                        st.warning("प्रणाली व्यस्त छ। कृपया केही क्षणपछि फेरि प्रयास गर्नुहोस्।")
