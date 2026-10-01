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

# सुरक्षित Rerun फङ्सन (सबै Streamlit भर्सनमा सजिलै चल्ने)
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

st.set_page_config(
    page_title="NEA Level 5 Electrical - Smart Tutor",
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

NOTES_DIR = "uploaded_notes"
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

# १. साइडबार: नोट अपलोड र हटाउने (Delete) प्रणाली
with st.sidebar:
    st.markdown("### ⚙️ सेटिङहरू")
    if not api_key:
        api_key = st.text_input("Groq API Key राख्नुहोस्:", type="password")
    
    selected_model = st.selectbox(
        "AI Model छान्नुहोस्:",
        ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"],
        index=0,
        help="Qwen मोडलले नेपाली, रोमन नेपाली र द्विभाषी उत्तर धेरै उत्कृष्ट दिन्छ।"
    )

    st.markdown("---")
    st.markdown("### 📚 नोट व्यवस्थापन (Upload & Manage)")
    
    # नयाँ नोट अपलोड गर्ने
    uploaded_files = st.file_uploader(
        "नयाँ नोट थप्नुहोस् (PDF/TXT):", 
        type=["pdf", "txt"], 
        accept_multiple_files=True
    )
    if uploaded_files:
        for file in uploaded_files:
            file_path = os.path.join(NOTES_DIR, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        st.success("नयाँ फाइल सङ्ग्रहमा थपियो!")

    st.markdown("---")
    st.write("📁 **सङ्कलित नोटहरू (फाइल अनुसार हटाउनुहोस्):**")
    
    existing_files = sorted(os.listdir(NOTES_DIR)) if os.path.exists(NOTES_DIR) else []
    if existing_files:
        for fname in existing_files:
            col1, col2 = st.columns([3, 1])
            col1.caption(f"📄 {fname}")
            if col2.button("❌", key=f"del_{fname}", help=f"{fname} मेटाउनुहोस्"):
                target = os.path.join(NOTES_DIR, fname)
                if os.path.exists(target):
                    os.remove(target)
                safe_rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ सबै नोटहरू एकैपटक हटाउनुहोस्"):
            for f in os.listdir(NOTES_DIR):
                os.remove(os.path.join(NOTES_DIR, f))
            safe_rerun()
    else:
        st.info("कुनै नोट अपलोड गरिएको छैन।")

# २. सबै नोटहरू लोड गर्ने फङ्सन
def load_all_notes():
    text_blocks = []
    file_info = []
    if os.path.exists(NOTES_DIR):
        for f in sorted(os.listdir(NOTES_DIR)):
            p = os.path.join(NOTES_DIR, f)
            content = ""
            if f.endswith(".pdf") and PYPDF_AVAILABLE:
                try:
                    reader = PdfReader(p)
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            content += extracted + "\n"
                except Exception:
                    pass
            elif f.endswith(".txt"):
                try:
                    with open(p, "r", encoding="utf-8") as file:
                        content = file.read() + "\n"
                except Exception:
                    pass
            
            w_count = len(content.split())
            file_info.append((f, w_count))
            if content.strip():
                text_blocks.append(f"\n=== [स्रोत फाइल: {f}] ===\n" + content)
                
    full_text = "\n".join(text_blocks)
    return full_text, file_info

all_notes_text, file_info = load_all_notes()

# ३. सन्दर्भ तयार गर्ने (नोट पूरै पढ्ने गरी)
def prepare_notes_for_prompt(full_text, query, max_chars=12000):
    if not full_text.strip():
        return ""
    
    # यदि नोट १२,००० क्यारेक्टर भन्दा सानो छ भने पूरै नोट पठाउने (कुनै कुरा नछुट्ने)
    if len(full_text) <= max_chars:
        return full_text

    paragraphs = [p.strip() for p in full_text.split("\n") if len(p.strip()) > 20]
    stopwords = {"k", "ko", "ma", "le", "lai", "bata", "bhaneko", "bujhinchha", "ho", "hunchha", "chha", "chhan", "kina", "kasari", "kun", "kati", "ra", "ani", "wa"}
    clean_words = [w.lower().replace("?", "").replace("।", "") for w in query.split() if len(w) > 1 and w.lower() not in stopwords]
    
    scored = []
    for i, p in enumerate(paragraphs):
        p_lower = p.lower()
        score = sum(1 for w in clean_words if w in p_lower)
        scored.append((score, i, p))
        
    scored.sort(key=lambda x: x[0], reverse=True)
    
    selected = []
    curr_len = 0
    for score, idx, p in scored:
        if curr_len + len(p) + 2 <= max_chars:
            selected.append((idx, p))
            curr_len += len(p) + 2
        else:
            break
            
    selected.sort(key=lambda x: x[0])
    return "\n\n".join([p for _, p in selected])

# मुख्य च्याट इन्टरफेस
st.title("⚡ नेपाल विद्युत प्राधिकरण (NEA) तह-५")
st.subheader("इलेक्ट्रिकल सुपरभाइजर — स्मार्ट द्विभाषी प्रश्न-उत्तर प्रणाली")
st.caption("🇳🇵 नेपाली र 🇬🇧 English दुवैमा विस्तृत परीक्षा-स्तरको उत्तर दिइन्छ।")
st.markdown("---")

# नोटको स्थिति जाँच गर्न मिल्ने ड्रपडाउन
if all_notes_text.strip():
    with st.expander("🔍 नोटबाट पढिएको सामग्रीको स्थिति हेर्नुहोस्"):
        for fname, wc in file_info:
            if wc > 0:
                st.write(f"✅ **{fname}**: {wc:,} शब्दहरू प्रणालीले सफलतापूर्वक पढ्यो।")
            else:
                st.write(f"⚠️ **{fname}**: ० शब्द भेटियो (यो स्क्यान गरिएको/फोटो PDF हुन सक्छ, जसमा डिजिटल टेक्स्ट छैन)।")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if q := st.chat_input("प्रश्न यहाँ सोध्नुहोस् (रोमन, नेपाली वा English मा)..."):
    if not api_key:
        st.warning("कृपया साइडबारमा Groq API Key राख्नुहोस्।")
        st.stop()

    st.session_state.chat_history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("नोटहरू गहन अध्ययन गरी नेपाली र English दुवैमा उत्तर तयार गर्दै..."):
            try:
                context_notes = prepare_notes_for_prompt(all_notes_text, q, max_chars=12000)

                system_prompt = f"""You are an elite Electrical Engineering Professor preparing students for the Nepal Electricity Authority (NEA) Level 5 Supervisor written exams.

OFFICIAL STUDY NOTES PROVIDED BY STUDENT:
{context_notes if context_notes.strip() else "No notes uploaded. Use official NEA Level 5 Electrical syllabus standards."}

MANDATORY INSTRUCTIONS:
1. THOROUGH STUDY OF NOTES:
   - Study the provided notes thoroughly. Even if the student's question is phrased in Romanized Nepali (e.g. 'transformer ko working principle k ho', 'earthing kina garinchha'), understand their core engineering intent.
   - Explain the working principle, definition, construction, circuit diagram concepts, formulas, and points directly from the notes.
   - Do NOT say 'उत्तर नोटमा छैन' if the topic exists in the notes. Formulate a rich, complete exam-level answer.

2. STRICT BILINGUAL (DUAL-LANGUAGE) FORMAT:
   You MUST write the response in TWO distinct, complete sections:

### 🇳🇵 नेपाली संस्करण (Nepali Version)
- Write an extensive, clear, technical explanation entirely in Nepali (देवनागरी लिपि).
- Include core definitions, working principles, bullet points, and advantages/disadvantages in Nepali so the student can directly write this in their NEA exam.

---
### 🇬🇧 English Version
- Provide the technical definitions, formulas, specifications, and structured bullet points in English.

Rule: Both sections are mandatory. Never answer in only one language.
"""

                user_message = f"विद्यार्थीको प्रश्न: {q}\n\n[Instruction: Provide the comprehensive answer in BOTH 1. 🇳🇵 Nepali (देवनागरी लिपि) and 2. 🇬🇧 English based on the uploaded notes.]"

                payload = {
                    "model": selected_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.2
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

                with urllib.request.urlopen(req, timeout=50) as resp:
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
