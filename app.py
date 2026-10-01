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

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

st.set_page_config(
    page_title="NEA Level 5 Electrical - Gemini AI Tutor",
    page_icon="⚡",
    layout="wide"
)

api_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = os.getenv("GEMINI_API_KEY")

NOTES_DIR = "uploaded_notes"
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

with st.sidebar:
    st.markdown("### ⚙️ Google Gemini सेटिङहरू")
    if not api_key:
        api_key = st.text_input(
            "Gemini API Key राख्नुहोस्:", 
            type="password",
            help="aistudio.google.com बाट नि:शुल्क की लिन सकिन्छ।"
        )
        st.markdown("[👉 यहाँ क्लिक गरी नि:शुल्क Gemini Key लिनुहोस्](https://aistudio.google.com)")

    # Google ले तोकेको आधिकारिक नयाँ मोडल
    selected_model = "gemini-3.8-flash"
    st.caption(f"🤖 **सक्रिय मोडल:** `{selected_model}`")

    st.markdown("---")
    st.markdown("### 📚 नोट व्यवस्थापन (Upload & Manage)")
    st.caption("यहाँ नयाँ नोट अपलोड गर्दा पुराना नोटहरू पनि सुरक्षित रहन्छन्।")
    
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
                text_blocks.append(f"\n=== [फाइल: {f}] ===\n" + content)
                
    full_text = "\n".join(text_blocks)
    return full_text, file_info

all_notes_text, file_info = load_all_notes()

st.title("⚡ नेपाल विद्युत प्राधिकरण (NEA) तह-५")
st.subheader("इलेक्ट्रिकल सुपरभाइजर — Google Gemini आधारित स्मार्ट प्रश्न-उत्तर प्रणाली")
st.caption("🚀 १० लाख टोकन क्षमता | रोमन नेपाली, नेपाली तथा English दुवै भाषामा परीक्षा-स्तरको विस्तृत उत्तर")
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
        st.warning("कृपया साइडबारमा Google Gemini API Key राख्नुहोस्।")
        st.stop()

    st.session_state.chat_history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)

    with st.chat_message("assistant"):
        with st.spinner("Gemini AI ले नोटहरू अध्ययन गरी उत्तर तयार गर्दै..."):
            trimmed_notes = all_notes_text[:80000]

            system_prompt = f"""तपाईं नेपाल विद्युत प्राधिकरण (NEA) तह-५ इलेक्ट्रिकल सुपरभाइजर परीक्षाको आधिकारिक विशेषज्ञ प्रशिक्षक हुनुहुन्छ।

विद्यार्थीले अपलोड गरेका आधिकारिक नोटहरू:
[सङ्कलित नोटहरू]:
{trimmed_notes if trimmed_notes.strip() else "कुनै नोट अपलोड गरिएको छैन। आधिकारिक NEA तह-५ इलेक्ट्रिकल पाठ्यक्रमको ज्ञान प्रयोग गर्नुहोस्।"}

कडा निर्देशनहरू (Strict Rules):
१. रोमन नेपाली बुझ्नुहोस्:
   - विद्यार्थीले रोमन नेपाली (जस्तै 'transformer ko working principle k ho', 'motor ra generator ma difference k chha') मा सोधे पनि प्राविधिक आशय बुझेर पूर्ण उत्तर दिनुहोस्।
२. नोटको गहन प्रयोग:
   - उत्तरलाई उपलब्ध नोटका तथ्य, कार्यविधि, सूत्र र बुँदाहरूमा आधारित बनाउनुहोस्।
   - अल्छी वा एक-लाइनको उत्तर नदिनुहोस्। लोकसेवा लिखित परीक्षामा पूर्ण अङ्क आउने गरी स्पष्ट व्याख्या गर्नुहोस्।
३. अनिवार्य द्विभाषी ढाँचा (Bilingual Format):
   प्रत्येक उत्तर अनिवार्य रूपमा तलका दुई खण्डमा प्रस्तुत गर्नुहोस्:

### 🇳🇵 नेपाली संस्करण (Nepali Version)
- शुद्ध नेपाली (देवनागरी लिपि) मा परिभाषा, कार्यसिद्धान्त, मुख्य बुँदाहरू र फाइदा/बेफाइदा लेख्नुहोस्।

---
### 🇬🇧 English Version
- Provide technical definitions, working formulas, specifications, and structured bullet points in English.
"""

            user_prompt = f"विद्यार्थीको प्रश्न: {q}\n\n[निर्देशन: उपलब्ध नोट अध्ययन गरी उत्तर अनिवार्य रूपमा पहिले नेपाली (देवनागरी) र पछि English दुवैमा दिनुहोस्।]"

            payload = {
                "system_instruction": {
                    "parts": [{"text": system_prompt}]
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": user_prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2
                }
            }
            req_data = json.dumps(payload).encode("utf-8")

            # Google ले तोकेको gemini-3.8-flash मा सिधै अनुरोध
            endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={api_key.strip()}"

            try:
                req = urllib.request.Request(
                    endpoint_url,
                    data=req_data,
                    headers={"Content-Type": "application/json"}
                )

                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    ans = result["candidates"][0]["content"]["parts"][0]["text"]
                    st.markdown(ans)
                    st.session_state.chat_history.append({"role": "assistant", "content": ans})
            except urllib.error.HTTPError as http_err:
                err_detail = http_err.read().decode("utf-8", errors="ignore")
                st.error(f"Gemini API त्रुटि ({http_err.code}): {err_detail}")
            except Exception as err:
                st.error(f"त्रुटि: {err}")
