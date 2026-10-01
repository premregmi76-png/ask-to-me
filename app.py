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
    
    # नेपाली राम्रो लेख्ने Qwen मोडललाई पहिलो प्राथमिकतामा राखिएको छ
    selected_model = st.selectbox(
        "AI Model छान्नुहोस्:",
        ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"],
        index=0,
        help="Qwen मोडलले नेपाली भाषामा धेरै राम्रो र शुद्ध उत्तर दिन्छ।"
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

# रेट लिमिट (TPM) रोक्न प्रश्नसँग सम्बन्धित अंश मात्र छान्ने
def get_relevant_context(full_text, query, max_chars=3500):
    if not full_text or len(full_text) <= max_chars:
        return full_text

    paragraphs = [p.strip() for p in full_text.split("\n") if len(p.strip()) > 25]
    if not paragraphs:
        return full_text[:max_chars]

    query_words = set([w.lower() for w in query.replace("?", "").replace("।", "").split() if len(w) > 1])
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
st.caption("🇳🇵 नेपाली र 🇬🇧 English दुवै भाषामा अनिवार्य उत्तर आउनेछ।")
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
        with st.spinner("नोटहरू हेरेर नेपाली र English दुवैमा उत्तर तयार गर्दै..."):
            try:
                relevant_notes = get_relevant_context(all_notes_text, q, max_chars=3500)

                # नेपाली भाषा अनिवार्य गराउने कडा निर्देशन
                system_prompt = f"""You are an expert tutor for Nepal Electricity Authority (NEA) Level 5 Electrical examination.
You must answer the student's question based strictly on the provided notes excerpts below:

[NOTES EXCERPTS]:
{relevant_notes if relevant_notes.strip() else "No notes uploaded. Use your general electrical engineering knowledge for NEA syllabus."}

CRITICAL DUAL-LANGUAGE REQUIREMENT:
You MUST structure your response into TWO distinct sections:

### 🇳🇵 नेपाली संस्करण (Nepali Version)
- Write this section entirely in Nepali language (देवनागरी लिपि).
- Explain the concepts, working principles, definitions, and points clearly in Nepali so that students can write it in their NEA exam.

---
### 🇬🇧 English Version
- Provide the technical definitions, formulas, and key points in English.

Rule: DO NOT omit or skip the Nepali section. Both sections are mandatory.
"""

                user_message = f"{q}\n\n(कृपया उत्तर अनिवार्य रूपमा पहिले नेपाली देवनागरी लिपिमा र त्यसपछि मात्र English मा दिनुहोस्।)"

                payload = {
                    "model": selected_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
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
                    st.warning("⚠️ Groq को प्रति-मिनेट सीमा पुगेको छ। कृपया १५-२० सेकेन्ड पर्खेर फेरि सोध्नुहोला।")
                else:
                    st.error(f"Groq API त्रुटि ({http_err.code}): {err_detail}")
            except Exception as err:
                st.error(f"त्रुटि: {err}")
