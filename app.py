import streamlit as st

st.set_page_config(
    page_title="NEA Level 5 Electrical - Study Portal", 
    page_icon="⚡", 
    layout="wide"
)

PORTAL_URL = "https://gemini.google.com/notebook/95067217-c097-43c8-9ffa-fe053d411f02"

# मुख्य हेडर
st.title("⚡ नेपाल विद्युत प्राधिकरण (NEA) तह-५")
st.subheader("इलेक्ट्रिकल सुपरभाइजर — परीक्षा सहयोगी पोर्टल ('Ask To Me')")
st.caption("खुला प्रतियोगितात्मक परीक्षा: प्रथम र द्वितीय पत्र विशेष तयारी")

st.markdown("---")

# मुख्य AI सहायक बटन
st.info("💡 **24/7 AI शिक्षकसँग असीमित प्रश्न सोध्न तलको मुख्य बटन थिच्नुहोस्:**")
st.link_button("🚀 यहाँ क्लिक गरी AI स्टडी असिस्टेन्ट खोल्नुहोस् (Ask AI)", PORTAL_URL, type="primary", use_container_width=True)

st.markdown("---")

# ट्याबहरू
tab1, tab2, tab3 = st.tabs(["📚 पाठ्यक्रम संरचना", "📝 नमुना प्रश्न-उत्तर (Model Q&A)", "ℹ️ कसरी तयारी गर्ने?"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### प्रथम पत्र: सामान्य ज्ञान, गणित र कानून (१०० अङ्क)
        1. **सामान्य ज्ञान (४५ अङ्क):** भूगोल, नदीनाला, इतिहास, समसामयिक, SAARC/BIMSTEC/EU
        2. **सामान्य गणित (१० अङ्क):** प्रतिशत, नाफा-नोक्सान, ब्याज, अनुपात, औसत, ऐकिक नियम
        3. **संस्थागत तथा व्यवस्थापकीय ज्ञान (२५ अङ्क):** विद्युत विकास, जलविद्युत आयोजना, सुरक्षा र प्राथमिक उपचार, कम्प्युटर
        4. **कानून सम्बन्धी ज्ञान (२० अङ्क):** 
           - नेपालको संविधान (भाग १ र ३)
           - नेपाल विद्युत प्राधिकरण ऐन, २०४१
           - विद्युत चोरी नियन्त्रण ऐन २०५८ र नियमावली २०५९
           - विद्युत वितरण विनियमावली २०७८ र महसुल संकलन विनियमावली
        """)
    with col2:
        st.markdown("""
        ### द्वितीय पत्र: सेवा सम्बन्धी विस्तृत ज्ञान (१०० अङ्क)
        **खण्ड (क) - ५० अङ्क:**
        - Fundamentals of AC/DC, Ohm's & Kirchhoff's Laws
        - Electrical Machines (Transformers, DC Motors/Generators, Alternators, Induction Motors)
        - Electrical Measurements (Meters, CT/PT, Smart/TOD Meters)
        - Power Electronics & Power Plants (Hydro, Diesel, Solar)
        
        **खण्ड (ख) - ५० अङ्क:**
        - Control & Protection (Relays, Circuit Breakers, SCADA, PLCC)
        - Substation & Transmission Line (Sag, Corona, Earthing, Busbars)
        - Distribution & Consumer Services (Tariff, Energy Meters, Safety)
        """)

with tab2:
    st.markdown("### परीक्षामा सोधिने मुख्य नमुना प्रश्न-उत्तरहरू:")
    with st.expander("❓ Buchholz Relay को कार्य सिद्धान्त के हो?"):
        st.write("""
        **उत्तर:**  
        Buchholz Relay तेलमा डुबेका (Oil-immersed) ट्रान्सफर्मरको भित्री गम्भीर समस्याहरू (Internal Faults) पत्ता लगाउन प्रयोग गरिने ग्यास-सञ्चालित (Gas-actuated) सुरक्षा उपकरण हो। यो ट्रान्सफर्मरको मुख्य ट्याङ्क र कन्जर्भेटर ट्याङ्क जोड्ने पाइपको बीचमा राखिन्छ।
        """)
        
    with st.expander("❓ नेपाल विद्युत प्राधिकरण ऐन, २०४१ अनुसार सञ्चालक समितिको गठन कसरी हुन्छ?"):
        st.write("""
        **उत्तर:**  
        ऐनको दफा ७ अनुसार प्राधिकरणको सञ्चालक समितिमा ८ जना सदस्यहरू रहने व्यवस्था छ, जसको अध्यक्ष नेपाल सरकारको ऊर्जा, जलस्रोत तथा सिँचाइ मन्त्री वा राज्यमन्त्री रहने व्यवस्था छ।
        """)

    with st.expander("❓ Corona Effect भनेको के हो?"):
        st.write("""
        **उत्तर:**  
        हाई भोल्टेज ट्रान्समिसन लाइनमा कन्डक्टरहरूको वरिपरिको हावाको डाइइलेक्ट्रिक स्ट्रेन्थ भन्दा भोल्टेज बढी भएर हावा आयोनिकरण हुँदा बैजनी रङको चमक (Violet Glow), हिसिङ आवाज र ओजोन ग्यास निस्कने प्रक्रियालाई Corona Effect भनिन्छ।
        """)

with tab3:
    st.markdown("""
    ### 🎯 पूर्ण परीक्षा तयारी कसरी गर्ने?
    1. माथि रहेको **"🚀 यहाँ क्लिक गरी AI स्टडी असिस्टेन्ट खोल्नुहोस्"** बटन थिच्नुहोस्।
    2. स्क्रिनमा खुल्ने बक्समा आफ्ना सम्पूर्ण प्रश्नहरू सोध्नुहोस्।
    3. AI ले उपलब्ध आधिकारिक पाठ्यक्रम र नोटहरू अनुसार परीक्षामा लेख्ने शैलीमा उत्तर दिनेछ।
    """)

# साइडबार
with st.sidebar:
    st.header("⚡ NEA Level 5 Portal")
    st.write("नेपाल विद्युत प्राधिकरण तह-५ खुला प्रतियोगितात्मक परीक्षा सहयोगी")
    st.markdown
