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
    page_title="NEA Level 5 Electrical - Smart Tutor",
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
        ["openai/gpt-oss-20b", "openai/gpt-oss-120b"],
        index=0
    )

    st.markdown("---")
    st.markdown("### 📚 नयाँ नोट थप्नुहोस् (Add Notes)")
    st.caption("तपाईंले थप्नुभएका सबै नोटहरू यहाँ क्रमशः जम्मा हुँदै जानेछन्।")
    
    uploaded_files = st.file_uploader(
        "नोट अपलोड गर्नुहोस् (PDF/TXT)", 
        type=["pdf", "txt"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        new_added = 0
        for file in uploaded_files:
            file_path = os.path.join(NOTES_DIR, file.name)
            # नयाँ फाइल सुरक्षित गर्ने
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            new_added += 1
        st.success(f"✅ {new_added} वटा नयाँ नोट सङ्ग्रहमा थपियो!")

    # सबै पुराना नोट मेटाउन चाहेमा
    if st.button("🗑️ सबै नोटहरू रिसेट गर्नुहोस्"):
        for f in os.listdir(NOTES_DIR):
            try:
                os.remove(os.path.join(NOTES_DIR, f))
            except Exception:
                pass
        st.rerun()

# सबै सङ्कलित नोटहरू पढ्ने फङ्सन
def load_all_accumulated_notes():
    combined_docs = []
    file_stats = []
    
    if os.path.exists(NOTES_DIR):
        for f in sorted(os.listdir(NOTES_DIR)):
            p = os.path.join(NOTES_DIR, f)
            file_text = ""
            if f.endswith(".pdf") and PYPDF_AVAILABLE:
                try:
                    reader = PdfReader(p)
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            file_text += t + "\n"
                except Exception:
                    pass
            elif f.endswith(".txt"):
                try:
                    with open(p, "r", encoding="utf-8") as file:
                        file_text = file.read() + "\n"
                except Exception:
                    pass
            
            words_count = len(file_text.split())
            file_stats.append((f, words_count))
            if file_text.strip():
                combined_docs.append({
                    "filename": f,
                    "text": file_text
                })
            
    return combined_docs, file_stats

all_docs, file_stats = load_all_accumulated_notes()

# साइडबारमा सङ्कलित नोटहरूको सूची देखाउने
with st.sidebar:
    st.markdown("---")
    st.write(f"📁 **सङ्कलित नोटहरू ({len(file_stats)} वटा फाइल):**")
    if file_stats:
        for fname, wcount in file_stats:
            if wcount > 0:
                st.caption(f"📄 **{fname}** ({wcount:,} शब्द)")
            else:
                st.caption(f"⚠️ **{fname}** (० शब्द - स्क्यान गरिएको फाइल)")
    else:
        st.info("अहिले कुनै नोट अपलोड गरिएको छैन।")

# सबै फाइलहरूबाट प्रश्नसँग सम्बन्धित अंश मात्र खोज्ने फङ्सन (टोकन बचत र गति बढाउन)
def search_relevant_excerpts(docs, query, max_total_chars=3800):
    if not docs:
        return ""
    
    query_words = set([w.lower() for w in query.replace("?", "").replace("।", "").replace(",", "").split() if len(w) > 1])
    scored_paragraphs = []
    
    for doc in docs:
        fname = doc["filename"]
        paragraphs = [p.strip() for p in doc["text"].split("\n") if len(p.strip()) > 25]
        for p in paragraphs:
            p_lower = p.lower()
            score = sum(1 for w in query_words if w in p_lower)
            scored_paragraphs.append((score, fname, p))
            
    # सान्दर्भिकताको आधारमा मिलाउने
    scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
    
    selected_text = []
    curr_len = 0
    for score, fname, p in scored_paragraphs:
        if score > 0 or len(selected_text) < 3:
            entry = f"[{fname} बाट]: {p}"
            if curr_len + len(entry) + 2 <= max_total_chars:
                selected_text.append(entry)
                curr_len += len(entry) + 2
            else:
                break
                
    return "\n\n".join(selected_text)

# मुख्य इन्टरफेस
st.title("⚡ नेपाल विद्युत प्राधिकरण (NEA) तह-५")
st.subheader("इलेक्ट्रिकल सुपरभाइजर — द्विभाषी (Nepali & English) प्रश्न-उत्तर प्रणाली")
st.caption("📖 तपाईंले अपलोड गर्नुभएका सबै पुराना र नयाँ नोटहरूबाट खोजी गरी नेपाली र अंग्रेजी दुवैमा उत्तर दिइन्छ।")
st.markdown("---")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# च्याट इनपुट
if q := st.chat_input("प्रश्न यहाँ सोध्नुहोस् (Ask your question here)..."):
    if not api_key:
        st.warning("कृपया साइडबारमा Groq API Key राख्नुहोस्।")
        st.stop()

    st.session_state.chat_history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("सङ्कलित सबै नोटहरू अध्ययन गर्दै..."):
            try:
                relevant_notes = search_relevant_excerpts(all_docs, q, max_total_chars=3800)
                
                # नेपाली र अंग्रेजी दुवैमा उत्तर माग्ने कडा प्रम्प्ट
                system_prompt = f"""तपाईं नेपाल विद्युत प्राधिकरण (NEA) तह-५ इलेक्ट्रिकल सुपरभाइजर परीक्षाको आधिकारिक विशेषज्ञ शिक्षक हुनुहुन्छ।

तपाईंलाई विद्यार्थीले सोधेको प्रश्नको उत्तर दिन तलका सङ्कलित आधिकारिक नोटहरू उपलब्ध गराइएको छ:
[सङ्कलित नोटहरूको सान्दर्भिक अंश]:
{relevant_notes if relevant_notes.strip() else "कुनै पनि नोटहरू उपलब्ध छैनन्, आफ्नो प्राविधिक ज्ञान प्रयोग गर्नुहोस्।"}

कडा निर्देशनहरू (Format Rules):
१. उत्तर अनिवार्य रूपमा दुई खण्ड (Bilingual) मा प्रस्तुत गर्नुहोस्:
   - खण्ड १: 🇳🇵 **नेपाली संस्करण (Nepali Version)** — मुख्य बुँदा, कार्यविधि र सरल व्याख्या।
   - खण्ड २: 🇬🇧 **English Version** — Clear bullet points, technical definitions, and formulas (if any).
२. उत्तर शतप्रतिशत उपलब्ध गराइएका नोटहरूका तथ्यमा आधारित हुनुपर्छ।
३. सम्भव भएसम्म उत्तरको पुछारमा जानकारी कुन नोट (फाइल) बाट लिइएको हो खुलाइदिनुहोस् (उदा: 📚 स्रोत: Chapter_Transformer.pdf)।
"""

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
                    st.warning("⚠️ Groq को प्रति-मिनेट टोकन सीमा पुगेको छ। कृपया १५-२० सेकेन्ड पर्खेर फेरि सोध्नुहोला।")
                else:
                    st.error(f"Groq API त्रुटि ({http_err.code}): {err_detail}")
            except Exception as err:
                st.error(f"त्रुटि देखा पर्यो: {err}")
