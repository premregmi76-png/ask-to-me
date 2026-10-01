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

# १. API Key व्यवस्थापन
api_key = None
try:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = os.getenv("GROQ_API_KEY")

NOTES_DIR = "uploaded_notes"
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

with st.sidebar:
    st.markdown("### ⚙️ सेटिङहरू")
    if not api_key:
        api_key = st.text_input("Groq API Key राख्नुहोस्:", type="password")
    
    selected_model = st.selectbox(
        "AI Model छान्नुहोस्:",
        ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"],
        index=0,
        help="Qwen मोडलले नेपाली, रोमन नेपाली र प्राविधिक उत्तर धेरै राम्रो बुझ्छ।"
    )

    st.markdown("---")
    st.markdown("### 📚 अध्ययन सामग्री (नोटहरू)")
    st.caption("यहाँ नयाँ नोट अपलोड गर्दा पुराना नोटहरू पनि यथावत रहन्छन्।")
    uploaded_files = st.file_uploader(
        "नोट अपलोड गर्नुहोस् (PDF/TXT)", 
        type=["pdf", "txt"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        for file in uploaded_files:
            file_path = os.path.join(NOTES_DIR, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        st.cache_data.clear()

# सबै नोटहरू पढ्ने फङ्सन
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
                            text += f"\n--- [{f}] ---\n" + t + "\n"
                except Exception:
                    pass
            elif f.endswith(".txt"):
                try:
                    with open(p, "r", encoding="utf-8") as file:
                        text += f"\n--- [{f}] ---\n" + file.read() + "\n"
                except Exception:
                    pass
    return text

all_notes_text = get_all_notes()

with st.sidebar:
    st.write("📁 **हाल सङ्कलित नोटहरू:**")
    files = os.listdir(NOTES_DIR) if os.path.exists(NOTES_DIR) else []
    if files:
        for f in files:
            st.caption(f"• {f}")
    else:
        st.info("कुनै नोट अपलोड गरिएको छैन।")

# रोमन नेपाली शब्दहरू हटाउन सूची
ROMAN_STOPWORDS = {
    "k", "ko", "ma", "le", "lai", "bata", "bhaneko", "bujhinchha", "ho", "hunchha", 
    "chha", "chhan", "thiyo", "kin", "kina", "kasari", "kun", "kati", "barema", 
    "bataunus", "lekhnus", "gareko", "garne", "hune", "ra", "ani", "wa", "athawa", 
    "yo", "tyo", "yesko", "tyesko", "haru", "haruko", "euta", "duita", "nepali"
}

# प्राविधिक शब्दहरूको नेपाली-अंग्रेजी जोडी (ताकि रोमन वा अंग्रेजीमा सोधे पनि नेपाली नोट भेटियोस्)
KEYWORD_MAP = {
    "transformer": ["ट्रान्सफर्मर", "transformer"],
    "generator": ["जेनेरेटर", "generator"],
    "motor": ["मोटर", "motor"],
    "working": ["कार्य", "काम", "working"],
    "principle": ["कार्यसिद्धान्त", "सिद्धान्त", "principle"],
    "transmission": ["प्रसारण", "transmission"],
    "distribution": ["वितरण", "distribution"],
    "substation": ["सबस्टेसन", "substation"],
    "relay": ["रिले", "relay"],
    "breaker": ["ब्रेकर", "breaker"],
    "circuit": ["सर्किट", "circuit"],
    "efficiency": ["दक्षता", "efficiency"],
    "earthing": ["अर्थिङ", "earthing", "grounding"],
    "cooling": ["कुलीङ", "cooling"],
    "fault": ["फल्ट", "खराबी", "fault"],
    "protection": ["सुरक्षा", "protection"],
    "loss": ["हानि", "नोक्सानी", "loss", "losses"],
    "losses": ["हानि", "नोक्सानी", "loss", "losses"],
    "type": ["प्रकार", "वर्गीकरण", "type", "types"],
    "types": ["प्रकार", "वर्गीकरण", "type", "types"],
    "difference": ["फरक", "तुलना", "difference", "comparison"],
    "advantage": ["फाइदा", "लाभ", "advantage"],
    "disadvantage": ["बेफाइदा", "हानि", "disadvantage"]
}

# स्मार्ट नोट खोजी फङ्सन (४,८०० क्यारेक्टर सम्म अध्ययन गर्ने)
def get_relevant_context(full_text, query, max_chars=4800):
    if not full_text or len(full_text) <= max_chars:
        return full_text

    paragraphs = [p.strip() for p in full_text.split("\n") if len(p.strip()) > 25]
    if not paragraphs:
        return full_text[:max_chars]

    # १. रोमन नेपाली हटाएर मुख्य प्राविधिक शब्द निकाल्ने
    clean_words = [
        w.lower().replace("?", "").replace("।", "").replace(",", "") 
        for w in query.split() if len(w) > 1 and w.lower() not in ROMAN_STOPWORDS
    ]
    
    # २. अंग्रेजी र नेपाली दुवै पर्यायवाची शब्दहरू थप्ने
    expanded_search = set(clean_words)
    for w in clean_words:
        if w in KEYWORD_MAP:
            expanded_search.update(KEYWORD_MAP[w])

    scored = []
    for i, p in enumerate(paragraphs):
        p_lower = p.lower()
        score = sum(1 for w in expanded_search if w in p_lower)
        scored.append((score, i, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = []
    curr_len = 0
    for score, idx, p in scored:
        if score > 0 or len(selected) < 3:
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
st.subheader("इलेक्ट्रिकल सुपरभाइजर — स्मार्ट द्विभाषी प्रश्न-उत्तर प्रणाली")
st.caption("💡 तपाईंले नेपाली, अङ्ग्रेजी वा रोमन नेपाली (जस्तै: *'transformer ko working principle k ho'*) मा सोध्न सक्नुहुन्छ।")
st.markdown("---")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if q := st.chat_input("प्रश्न यहाँ सोध्नुहोस् (रोमन वा नेपालीमा)..."):
    if not api_key:
        st.warning("कृपया साइडबारमा Groq API Key राख्नुहोस्।")
        st.stop()

    st.session_state.chat_history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("नोटहरू गहन अध्ययन गरी उत्तर तयार गर्दै..."):
            try:
                relevant_notes = get_relevant_context(all_notes_text, q, max_chars=4800)

                # रोमन बुझ्ने र स्तरीय उत्तर दिने प्रम्प्ट
                system_prompt = f"""You are a senior electrical engineering instructor preparing students for the Nepal Electricity Authority (NEA) Level 5 Supervisor exams.

CONTEXT FROM UPLOADED NOTES:
{relevant_notes if relevant_notes.strip() else "Use standard NEA Level 5 Electrical syllabus knowledge."}

CRITICAL RULES:
1. UNDERSTAND ROMANIZED NEPALI:
   - The student often asks in Romanized Nepali (e.g., 'transformer ko working principle k ho', 'motor ra generator ma k difference hunchha').
   - Accurately understand the technical question and intent.

2. THOROUGH, DETAILED EXAM-QUALITY ANSWERS:
   - Do NOT provide one-line or superficial responses.
   - Base your answer deeply on the provided notes. Explain principles, definitions, working steps, circuit formulas, and classifications in detail suitable for NEA written exams.

3. MANDATORY BILINGUAL FORMAT:
   Always structure the response into two distinct sections:

### 🇳🇵 नेपाली संस्करण (Nepali Version)
- Write an extensive, clear explanation entirely in Nepali (देवनागरी लिपि).
- Include bullet points, working steps, and definitions that a candidate can directly write in an NEA exam.

---
### 🇬🇧 English Version
- Provide crisp technical definitions, formulas, and bullet points in English.
"""

                user_message = f"विद्यार्थीको प्रश्न: {q}\n\n[Instruction: Understand Romanized Nepali if used. Give a complete, detailed, exam-standard answer in BOTH Nepali (देवनागरी) and English.]"

                payload = {
                    "model": selected_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.15
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
                    st.warning("⚠️ Groq को प्रति-मिनेट सीमा पुगेको छ। कृपया १५-२० सेकेन्ड पर्खेर फेरि सोध्नुहोला।")
                else:
                    st.error(f"Groq API त्रुटि ({http_err.code}): {err_detail}")
            except Exception as err:
                st.error(f"त्रुटि: {err}")
