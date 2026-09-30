import streamlit as st

st.set_page_config(
    page_title="NEA Level 5 Electrical - Study Portal", 
    page_icon="⚡", 
    layout="wide"
)

# तपाईंका १४ वटै मुख्य नोटहरू भएको वास्तविक नोटबुक लिङ्क
PORTAL_URL = "https://gemini.google.com/notebook/10d1d5bd-f763-47b2-86d7-b403959adda5"

# मुख्य हेडर
st.title("⚡ नेपाल विद्युत प्राधिकरण (NEA) तह-५")
st.subheader("प्राविधिक सेवा, इलेक्ट्रिकल समूह/उपसमूह, सुपरभाइजर पद — परीक्षा सहयोगी पोर्टल ('Ask To Me')")
st.caption("खुला प्रतियोगितात्मक परीक्षा: प्रथम र द्वितीय पत्र विशेष अनलाइन तयारी")

st.markdown("---")

# आधिकारिक जानकारी
st.success("""
### 📢 आधिकारिक जानकारी
"यो हाम्रो नेपाल विद्युत प्राधिकरण (NEA) तह-५ तयारीका लागि तयार गरिएको आधिकारिक AI Study Portal हो। यसमा प्रथम र द्वितीय पत्रका सम्पूर्ण नोटहरू राखिएका छन्। तलको बक्समा जुनसुकै प्रश्न सोधेर तुरुन्तै परीक्षा-केन्द्रित उत्तर पाउन सक्नुहुन्छ।"
""")

# तपाईंका १४ वटै नोटहरूसँग सिधै जोड्ने मुख्य बटन
st.link_button("🚀 यहाँ क्लिक गरी सम्पूर्ण नोटहरूसहितको AI पोर्टल खोल्नुहोस्", PORTAL_URL, type="primary", use_container_width=True)

st.markdown("---")

# ट्याबहरू
tab1, tab2, tab3 = st.tabs(["📚 पाठ्यक्रम संरचना", "📝 नमुना प्रश्न-उत्तर (Model Q&A)", "💡 कसरी तयारी गर्ने?"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### प्रथम पत्र: सामान्य ज्ञान, गणित र कानून (१०० अङ्क)
        1. **सामान्य ज्ञान (४५ अङ्क):** भूगोल, नदीनाला, आर्थिक/सामाजिक अवस्था, दिगो विकास, SAARC/BIMSTEC/EU र समसामयिक घटनाहरू।
        2. **सामान्य गणित (१० अङ्क):** प्रतिशत, भिन्न, अनुपात, औसत, नाफा-नोक्सान, साधारण ब्याज, ऐकिक नियम।
        3. **संस्थागत तथा व्यवस्थापकीय ज्ञान (२५ अङ्क):** जलविद्युत विकास, प्रमुख आयोजनाहरू, सुरक्षा तथा प्राथमिक उपचार, कम्प्युटर ज्ञान।
        4. **कानून सम्बन्धी ज्ञान (२० अङ्क):** 
           - नेपालको वर्तमान संविधान (भाग १ र ३)
           - नेपाल विद्युत प्राधिकरण ऐन, २०४१
           - विद्युत चोरी नियन्त्रण ऐन २०५८ र नियमावली २०५९
           - विद्युत वितरण विनियमावली २०७८ र महसुल संकलन विनियमावली
        """)
    with col2:
        st.markdown("""
        ### द्वितीय पत्र: सेवा सम्बन्धी विस्तृत ज्ञान (१०० अङ्क)
        **खण्ड (क) - ५० अङ्क:**
        - Fundamentals: AC/DC Circuits, Ohm's & Kirchhoff's Laws
        - Electrical Machines: Transformers, DC Motors & Generators, Alternators, Induction Motors
        - Electrical Measurements: CT/PT, Energy Meters, Smart/TOD Meters
        - Power Electronics & Power Plants: Hydro, Diesel, Solar, Load Factors
        
        **खण्ड (ख) - ५० अङ्क:**
        - Control & Protection: Relays, Circuit Breakers (VCB, SF6), SCADA, PLCC
        - Substation & Transmission: Sag, Tension, Corona Effect, Earthing, Busbars
        - Distribution & Safety: Radial/Ring Systems, Tariff System, Safety Devices
        """)

with tab2:
    st.markdown("### परीक्षामा सोधिने मुख्य नमुना प्रश्न-उत्तरहरू:")
    with st.expander("❓ Buchholz Relay को कार्य सिद्धान्त के हो?"):
        st.write("""
        **उत्तर:**  
        Buchholz Relay तेलमा डुबेका ट्रान्सफर्मरको भित्री गम्भीर समस्याहरू पत्ता लगाउन प्रयोग गरिने ग्यास-सञ्चालित सुरक्षा उपकरण हो। यो ट्रान्सफर्मरको मुख्य ट्याङ्क र कन्जर्भेटर ट्याङ्क जोड्ने पाइपको बीचमा राखिन्छ।
        """)
        
    with st.expander("❓ नेपाल विद्युत प्राधिकरण ऐन, २०४१ अनुसार सञ्चालक समितिको गठन कसरी हुन्छ?"):
        st.write("""
        **उत्तर:**  
        ऐनको दफा ७ अनुसार प्राधिकरणको सञ्चालक समितिमा ८ जना सदस्यहरू रहने व्यवस्था छ, जसको अध्यक्ष नेपाल सरकारको ऊर्जा, जलस्रोत तथा सिँचाइ मन्त्री वा राज्यमन्त्री रहने व्यवस्था छ।
        """)

    with tab3:
        st.markdown("""
        ### 🎯 पूर्ण परीक्षा तयारी कसरी गर्ने?
        1. माथि रहेको मुख्य बटन थिच्नुहोस्।
        2. त्यहाँ तपाईंका सम्पूर्ण १४ वटा पुस्तक तथा नोटहरूका आधारमा जे सोधे पनि तुरुन्तै सटीक उत्तर आउनेछ।
        """)

# साइडबार
with st.sidebar:
    st.header("⚡ NEA Level 5 Portal")
    st.write("नेपाल विद्युत प्राधिकरण तह-५ खुला प्रतियोगितात्मक परीक्षा सहयोगी")
    st.markdown("---")
    st.link_button("👉 सिधै AI पोर्टल खोल्नुहोस्", PORTAL_URL, use_container_width=True)
