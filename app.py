import os
import json
import urllib.request
import urllib.error
import streamlit as st

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

st.set_page_config(
    page_title="NEA Level 5 Electrical - Ask To Me",
    page_icon="⚡",
    layout="wide"
)

# API Key व्यवस्थापन
api_key = None
try:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = os.getenv("GROQ_API_KEY")

with st.sidebar:
    st.markdown("### ⚙️ सेटिङहरू")
    if not api_key:
        api_key = st.text_input("Groq API Key राख्नुहोस्:", type="password")
    
    selected_model = st.selectbox(
        "AI Model छान्नुहोस्:",
        ["openai/gpt-oss-20b", "openai/gpt-oss-120b"],
        index=0
    )

    st.markdown("---")
    st.markdown("### 📚 अध्ययन सामग्री (नोटहरू)")
    uploaded_files = st.file_uploader("नोट अपलोड गर्नुहोस् (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)

NOTES_DIR = "uploaded_notes"
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

if uploaded_files:
    for file in uploaded_files:
        file_path = os.path.join(NOTES_DIR, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
    st.cache_data.clear()

# सबै नोटहरू पढ्ने
@st.cache_data
def get_all_notes():
    text = ""
    if os.path.exists(NOTES_DIR):
        for f in os.listdir(NOTES_DIR):
            p = os.path.join(NOTES_DIR, f)
            if f.endswith(".pdf") and PYPDF_AVAILABLE:
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
    return text

all_notes_text = get_all_notes()

with st.sidebar:
    st.write("📁 **हाल उपलब्ध नोटहरू:**")
    files = os.listdir(NOTES_DIR) if os.path.exists(NOTES_DIR) else []
    if files:
        for f in files:
            st.caption(f"• {f}")
    else:
        st.info("कुनै नोट अपलोड गरिएको छैन।")

# रेट लिमिट (TPM) रोक्न प्रश्नसँग सम्बन्धित मुख्य भाग मात्र निकाल्ने स्मार्ट फङ्सन
def get_relevant_context(full_text, query, max_chars=3500):
    if not full_text or len(full_text) <= max_chars:
        return full_text
    
    paragraphs = [p.strip() for p in full_text.split("\n") if len(p.strip()) > 25]
    if not paragraphs:
        return full_text[:max_chars]
    
    query_words = set([w.lower() for w in query.split() if len(w) > 1])
    scored = []
    for i, p in enumerate(paragraphs):
        p_lower = p.lower()
        score = sum(1 for w in query_words if w in p_lower)
        scored.append((score, i, p))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    selected = []
    curr_len = 0
    for score, idx, p in scored:
        if score > 0 or len(selected) < 2:
            if curr_len + len(p) + 2 <= max_chars:
                selected.append((idx, p))
                curr_len += len(p) + 2
            else:
                break
    
    selected.sort(key=lambda x: x[0])
    extracted = "\n\n".join([p for _, p in selected])
    return extracted if extracted.strip() else full_text[:max_chars]

# मुख्य इन्टरफेस
st.title("⚡ नेपाल विद्युत प्राधिकरण (NEA) तह-५")
st.subheader("इलेक्ट्रिकल सुपरभाइजर — प्रश्न-उत्तर प्रणाली")
st.markdown("---")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if q := st.chat_input("प्रश्न यहाँ सोध्नुहोस्..."):
    if not api_key:
        st.warning("कृपया साइडबारमा Groq API Key राख्नुहोस्।")
        st.stop()

    st.session_state.chat_history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("उत्तर खोज्दै..."):
            try:
                # प्रश्न अनुसार सान्दर्भिक सानो अंश मात्र छान्ने (टोकन बचत गर्न)
                relevant_notes = get_relevant_context(all_notes_text, q, max_chars=3500)
                
                if relevant_notes.strip():
                    system_prompt = f"""तपाईं NEA Level 5 Electrical को आधिकारिक शिक्षक हुनुहुन्छ। तल दिइएको नोटको सान्दर्भिक अंश पढेर विद्यार्थीको प्रश्नको उत्तर दिनुहोस्।

[नोटको सान्दर्भिक अंश]:
{relevant_notes}

निर्देशन:
- केवल नोटको आधारमा तथ्यपरक र स्पष्ट उत्तर दिनुहोस्।
- यदि उत्तर नोटमा स्पष्ट छैन भने पनि सामान्य अनुमान नगरी नोटमा भएको जानकारी मात्र दिनुहोस्।"""
                else:
                    system_prompt = "तपाईं नेपाल विद्युत प्राधिकरण (NEA) तह-५ इलेक्ट्रिकल सुपरभाइजर परीक्षाको विज्ञ शिक्षक हुनुहुन्छ। विद्यार्थीका प्रश्नहरूको सरल, स्पष्ट र बुँदागत उत्तर दिनुहोस्।"

                payload = {
                    "model": selected_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": q}
                    ],
                    "temperature": 0.1
                }
                req_data = json.dumps(payload).encode("utf-8")

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
            except urllib.error.HTTPError as http_err:
                err_detail = http_err.read().decode("utf-8", errors="ignore")
                if http_err.code == 429:
                    st.warning("⚠️ Groq को प्रति-मिनेट सीमा पुगेको छ। कृपया १५-२० सेकेन्ड पर्खेर फेरि प्रश्न सोध्नुहोला।")
                else:
                    st.error(f"Groq API त्रुटि ({http_err.code}): {err_detail}")
            except Exception as err:
                st.error(f"त्रुटि: {err}")
