import os
import json
import urllib.request
import urllib.error
import time
import streamlit as st

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

st.set_page_config(
    page_title="NEA Level 5 Electrical - AI Tutor",
    page_icon="⚡",
    layout="wide"
)

# Groq API Key व्यवस्थापन
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
    st.markdown("### ⚙️ Groq सेटिङहरू")
    if not api_key:
        api_key = st.text_input(
            "Groq API Key राख्नुहोस्:", 
            type="password",
            help="console.groq.com बाट नि:शुल्क की लिन सकिन्छ।"
        )
        st.markdown("[👉 यहाँ क्लिक गरी नि:शुल्क Groq Key लिनुहोस्](https://console.groq.com)")

    # नेपाली भाषा राम्रो लेख्ने Qwen मोडल डिफल्ट राखिएको छ
    selected_model = st.selectbox(
        "AI Model छान्नुहोस्:",
        ["qwen/qwen3.8-27b", "openai/gpt-oss-120b"],
        index=0,
        help="Qwen मोडलले नेपाली भाषा (देवनागरी) मा शतप्रतिशत शुद्ध उत्तर दिन्छ।"
    )

    st.markdown("---")
    st.markdown("### 📚 नोट व्यवस्थापन (Upload & Manage)")
    st.caption("यहाँ नयाँ नोट थप्दा पुराना नोटहरू पनि सुरक्षित रहन्छन्।")
    
    uploaded_files = st.file_uploader(
        "नयाँ नोट थप्नुहोस् (PDF/TXT):", 
        type=["pdf", "txt"], 
        accept_multiple_files=True
    )
    if uploaded_files:
        new_count = 0
        for file in uploaded_files:
            file_path = os.path.join(NOTES_DIR, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            new_count += 1
        st.success(f"✅ {new_count} वटा नोट सुरक्षित गरियो!")

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

ROMAN_STOPWORDS = {
    "k", "ko", "ma", "le", "lai", "bata", "bhaneko", "bujhinchha", "ho", "hunchha", 
    "chha", "chhan", "thiyo", "kin", "kina", "kasari", "kun", "kati", "barema", 
    "bataunus", "lekhnus", "gareko", "garne", "hune", "ra", "ani", "wa", "athawa", 
    "yo", "tyo", "yesko", "tyesko", "haru", "haruko", "euta", "duita", "nepali"
}

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
    "fault": ["फल्ट", "fault"],
    "protection": ["सुरक्षा", "protection"],
    "loss": ["हानि", "नोक्सानी", "loss", "losses"],
    "losses": ["हानि", "नोक्सानी", "loss", "losses"],
    "type": ["प्रकार", "वर्गीकरण", "type", "types"],
    "types": ["प्रकार", "वर्गीकरण", "type", "types"],
    "difference": ["फरक", "तुलना", "difference", "comparison"]
}

def get_smart_context(full_text, query, max_chars=3600):
    if not full_text or len(full_text) <= max_chars:
        return full_text

    paragraphs = [p.strip() for p in full_text.split("\n") if len(p.strip()) > 25]
    if not paragraphs:
        return full_text[:max_chars]

    clean_words = [
        w.lower().replace("?", "").replace("।", "").replace(",", "") 
        for w in query.split() if len(w) > 1 and w.lower() not in ROMAN_STOPWORDS
    ]
    
    expanded = set(clean_words)
    for w in clean_words:
        if w in KEYWORD_MAP:
            expanded.update(KEYWORD_MAP[w])

    scored = []
    for i, p in enumerate(paragraphs):
        p_lower = p.lower()
        score = sum(1 for w in expanded if w in p_lower)
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

st.title("⚡ नेपाल विद्युत प्राधिकरण (NEA) तह-५")
st.subheader("इलेक्ट्रिकल सुपरभाइजर — स्मार्ट द्विभाषी प्रश्न-उत्तर प्रणाली")
st.caption("💡 दैनिक १,००० प्रश्न क्षमता | अनिवार्य नेपाली (देवनागरी) र English दुवैमा विस्तृत उत्तर")
st.markdown("---")

if all_notes_text.strip():
    with st.expander("🔍 नोटबाट पढिएको सामग्रीको स्थिति हेर्नुहोस्"):
        for fname, wc in file_info:
            if wc > 0:
                st.write(f"✅ **{fname}**: {wc:,} शब्दहरू प्रणालीमा उपलब्ध छन्।")
            else:
                st.write(f"⚠️ **{fname}**: ० शब्द भेटियो (यो स्क्यान गरिएको PDF हुन सक्छ)।")

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
        with st.spinner("नोटहरू गहन अध्ययन गरी अनिवार्य रूपमा नेपाली र English दुवैमा उत्तर तयार गर्दै..."):
            relevant_notes = get_smart_context(all_notes_text, q, max_chars=3600)

            # नेपाली भाषा अनिवार्य गराउने कडा नमूना सहितको प्रम्प्ट
            system_prompt = f"""तपाईं नेपाल विद्युत प्राधिकरण (NEA) तह-५ इलेक्ट्रिकल सुपरभाइजर परीक्षाको आधिकारिक विशेषज्ञ प्रशिक्षक हुनुहुन्छ।

विद्यार्थीले अपलोड गरेका आधिकारिक नोटहरू:
{relevant_notes if relevant_notes.strip() else "कुनै नोट छैन। आधिकारिक NEA तह-५ इलेक्ट्रिकल पाठ्यक्रमको ज्ञान प्रयोग गर्नुहोस्।"}

कडा निर्देशनहरू (STRICT RULES):
१. विद्यार्थीले रोमन नेपाली (जस्तै 'transformer ko working principle k ho', 'motor ra generator ma difference k chha') मा प्रश्न सोधे पनि प्राविधिक आशय बुझेर पूर्ण उत्तर दिनुहोस्।
२. तपाईंको उत्तर अनिवार्य रूपमा तल दिइएको ढाँचामा दुईवटा स्पष्ट खण्डमा हुनुपर्छ:

### 🇳🇵 नेपाली संस्करण (Nepali Version)
- यो खण्डका सम्पूर्ण वाक्यहरू अनिवार्य रूपमा नेपाली भाषा (देवनागरी लिपि) मा लेखिएको हुनुपर्छ। यहाँ अङ्ग्रेजी वाक्य लेख्न कडा निषेध छ।
- प्राविधिक परिभाषा, कार्यसिद्धान्त, मुख्य बुँदाहरू र सूत्रहरू सरल नेपालीमा व्याख्या गर्नुहोस् ताकि विद्यार्थीले परीक्षामा लेख्न सकून्।

---
### 🇬🇧 English Version
- Provide technical definitions, working formulas, specifications, and structured bullet points in English.

नमूना ढाँचा (FOLLOW THIS FORMAT EXACTLY):
### 🇳🇵 नेपाली संस्करण (Nepali Version)
- ट्रान्सफर्मर एक स्थिर विद्युतीय उपकरण (static device) हो, जसले फ्रिक्वेन्सी परिवर्तन नगरी भोल्टेजको स्तर बढाउने वा घटाउने गर्दछ।
- कार्यसिद्धान्त: यो माइकल फराडेको म्युचुअल इन्डक्सन (Mutual Induction) को नियममा काम गर्दछ।

---
### 🇬🇧 English Version
- A transformer is a static electrical machine that transfers electrical energy without changing frequency.
- Working Principle: It operates on Faraday's law of mutual electromagnetic induction.
"""

            user_message = f"विद्यार्थीको प्रश्न: {q}\n\n[अनिवार्य निर्देशन: खण्ड १ मा सम्पूर्ण विवरण नेपाली भाषा (देवनागरी लिपि) मा लेख्नुहोस् र खण्ड २ मा मात्र English प्रयोग गर्नुहोस्। दुवै खण्ड अनिवार्य छन्।]"

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

            ans = None
            for attempt in range(2):
                try:
                    with urllib.request.urlopen(req, timeout=45) as resp:
                        result = json.loads(resp.read().decode("utf-8"))
                        ans = result["choices"][0]["message"]["content"]
                        break
                except urllib.error.HTTPError as http_err:
                    err_detail = http_err.read().decode("utf-8", errors="ignore")
                    if http_err.code == 429 and attempt == 0:
                        st.info("⏳ प्रति-मिनेट ट्राफिक व्यवस्थापन हुँदैछ, कृपया १० सेकेन्ड पर्खनुहोस्...")
                        time.sleep(12)
                        continue
                    else:
                        st.error(f"Groq API त्रुटि ({http_err.code}): {err_detail}")
                        break
                except Exception as err:
                    st.error(f"त्रुटि: {err}")
                    break

            if ans:
                st.markdown(ans)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
