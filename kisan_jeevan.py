import streamlit as st
import sounddevice as sd
import numpy as np
import tempfile
import wave
import json
import os
from vosk import Model, KaldiRecognizer
from gtts import gTTS
import time
import platform
from difflib import get_close_matches
import threading
import queue
import re
from datetime import datetime
import sqlite3
import io
import base64

# Enhanced Configuration
st.set_page_config(
    page_title="Kisan Jeevan - किसान जीवन",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #4CAF50, #2E7D32);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .chat-container {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #4CAF50;
    }
    
    .user-message {
        background: #e3f2fd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #2196F3;
    }
    
    .assistant-message {
        background: #f1f8e9;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4CAF50;
    }
    
    .mic-button {
        background: linear-gradient(135deg, #FF5722, #D32F2F);
        color: white;
        border: none;
        border-radius: 50%;
        width: 80px;
        height: 80px;
        font-size: 2rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .mic-button:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    .language-selector {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 2px solid #4CAF50;
    }
    
    .stats-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .weather-card {
        background: linear-gradient(135deg, #03A9F4, #0277BD);
        color: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .price-ticker {
        background: #fff3e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #FF9800;
    }
    
    .feature-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem;
        text-align: center;
        border: 1px solid #ddd;
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    .progress-bar {
        height: 10px;
        border-radius: 5px;
        background: linear-gradient(90deg, #4CAF50, #8BC34A);
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Comprehensive Q&A Data for Farmers (100+ questions each) ----------
qa_data = {
    "Hindi": {
        # Greetings & Basic Interactions
        "नमस्ते": "नमस्ते! मैं जीव हूं, आपका स्मार्ट कृषि सहायक। मैं आपकी खेती में हर कदम पर मदद करूंगा।",
        "हेलो": "नमस्ते! मैं जीव हूं, आपका स्मार्ट कृषि सहायक। मैं आपकी खेती में हर कदम पर मदद करूंगा।",
        "गुड मॉर्निंग": "सुप्रभात! आज खेती के लिए क्या योजना है? मैं आपकी मदद करूंगा।",
        "तुम्हारा नाम क्या है": "मेरा नाम जीव है। मैं एक AI किसान सहायक हूं।",
        "आपका नाम क्या है": "मेरा नाम जीव है। मैं एक AI किसान सहायक हूं।",
        "तुम क्या करते हो": "मैं किसानों को खेती, मौसम, बीज, खाद, सरकारी योजनाओं की जानकारी देता हूं।",
        "धन्यवाद": "आपका स्वागत है! खुशी से मदद की। कुछ और जानना चाहते हैं?",
        "अलविदा": "अलविदा! खुशी से मदद की। फसल अच्छी हो। जरूरत पड़े तो आना।",
        "क्या मदद कर सकते हो": "जी हां! मैं फसल, मौसम, बीज, खाद, मंडी भाव की जानकारी दे सकता हूं।",
        "कैसे काम करते हो": "मैं आपकी आवाज सुनता हूं और तुरंत जवाब देता हूं।",
        
        # Weather & Season
        "मौसम कैसा है": "आज मौसम साफ और अच्छा है। खेती के लिए उपयुक्त दिन है।",
        "आज मौसम कैसा है": "आज मौसम साफ और अच्छा है। खेती के लिए उपयुक्त दिन है।",
        "बारिश होगी": "हां, इस सप्ताह बारिश की संभावना है। फसल को ढकने की तैयारी करें।",
        "कल बारिश आएगी": "हां, कल बारिश हो सकती है। पहले से तैयारी कर लीजिए।",
        "तापमान कितना है": "आज का तापमान 28 डिग्री सेल्सियस है। फसल के लिए अच्छा है।",
        "गर्मी कैसी है": "गर्मी सामान्य है। पानी की व्यवस्था जरूर करें।",
        "सर्दी कैसी है": "सर्दी अच्छी है। रबी की फसल के लिए बढ़िया मौसम है।",
        "हवा कैसी है": "हवा अच्छी है। फसल को नुकसान नहीं होगा।",
        "आंधी आएगी": "आंधी की संभावना है। फसल को सुरक्षित रखिए।",
        "ओला गिरेगा": "ओला गिरने की संभावना है। फसल को ढकिए।",
        "मानसून कब आएगा": "मानसून जून के पहले सप्ताह में आने की संभावना है।",
        "बादल कैसे हैं": "आज बादल छाए हुए हैं। बारिश हो सकती है।",
        "धूप कैसी है": "धूप तेज है। फसल को छाया की जरूरत हो सकती है।",
        "नमी कितनी है": "हवा में नमी अच्छी है। फसल के लिए फायदेमंद है।",
        
        # Crop Specific - Rice
        "धान कब बोएं": "धान जून-जुलाई में बोते हैं। पहले खेत की अच्छी तैयारी करें।",
        "धान की बुवाई कैसे करें": "पहले नर्सरी में पौधे तैयार करें, फिर 20-25 दिन में रोपाई करें।",
        "धान की खाद कितनी दें": "एक एकड़ में 2 बोरी यूरिया और 1 बोरी डीएपी डालें।",
        "धान में पानी कितना चाहिए": "धान में हमेशा 2-3 इंच पानी रखें।",
        "धान का कीड़ा कैसे मारें": "नीम का तेल छिड़कें या कीटनाशक का प्रयोग करें।",
        "धान की कटाई कब करें": "धान 110-120 दिन में तैयार हो जाता है।",
        "धान की किस्म कौन सी अच्छी": "बासमती, पूसा सुगंधा और पीआर-126 अच्छी किस्में हैं।",
        "धान का भाव क्या है": "धान का भाव 2000-2200 रुपए प्रति क्विंटल है।",
        "धान का रोग कैसे ठीक करें": "फंगीसाइड का छिड़काव करें और खेत की सफाई रखें।",
        "धान की पैदावार कितनी होती है": "अच्छी किस्म से 25-30 क्विंटल प्रति एकड़ मिलता है।",
        "धान की नर्सरी कैसे तैयार करें": "उपजाऊ मिट्टी में बीज डालकर पानी भरें।",
        "धान की रोपाई कब करें": "बुवाई के 20-25 दिन बाद रोपाई करें।",
        "धान का भूसा कैसे काम आता है": "भूसा पशुओं के चारे और खाद बनाने में काम आता है।",
        "धान में खरपतवार कैसे हटाएं": "हाथ से निकालें या खरपतवारनाशी का प्रयोग करें।",
        
        # Crop Specific - Wheat
        "गेहूं कब बोएं": "गेहूं नवंबर-दिसंबर में बोते हैं।",
        "गेहूं की बुवाई कैसे करें": "हल से कूंड बनाकर बीज डालें, फिर मिट्टी से ढकें।",
        "गेहूं की खाद कितनी दें": "एक एकड़ में 1.5 बोरी यूरिया और 1 बोरी डीएपी डालें।",
        "गेहूं में सिंचाई कब करें": "बुवाई के 20-25 दिन बाद पहली सिंचाई करें।",
        "गेहूं की कटाई कब करें": "गेहूं 130-140 दिन में तैयार हो जाता है।",
        "गेहूं की किस्म कौन सी अच्छी": "HD-2967, पूसा गोल्ड और DBW-187 अच्छी किस्में हैं।",
        "गेहूं का भाव क्या है": "गेहूं का भाव 2100-2300 रुपए प्रति क्विंटल है।",
        "गेहूं का रोग कैसे ठीक करें": "रतुआ रोग के लिए प्रोपिकोनाज़ोल छिड़कें।",
        "गेहूं की पैदावार कितनी होती है": "अच्छी किस्म से 20-25 क्विंटल प्रति एकड़ मिलता है।",
        "गेहूं की खरपतवार कैसे हटाएं": "2-4-डी का छिड़काव करें या हाथ से निकालें।",
        "गेहूं में कौन सा रोग लगता है": "गेरुई, झुलसा और कंडुआ रोग मुख्य हैं।",
        "गेहूं की बुवाई की गहराई कितनी हो": "3-4 सेमी गहराई में बीज डालें।",
        "गेहूं का अंकुरण कैसे बढ़ाएं": "बीज को 12 घंटे पानी में भिगोएं।",
        "गेहूं की जुताई कब करें": "अक्टूबर-नवंबर में जुताई करें।",
        
        # Crop Specific - Vegetables
        "आलू कब लगाएं": "आलू अक्टूबर-नवंबर में लगाते हैं।",
        "टमाटर कब लगाएं": "टमाटर जुलाई-अगस्त में लगाते हैं।",
        "प्याज कब लगाएं": "प्याज नवंबर-दिसंबर में लगाते हैं।",
        "मिर्च कब लगाएं": "मिर्च जुलाई-अगस्त में लगाते हैं।",
        "बैंगन कब लगाएं": "बैंगन जुलाई-अगस्त में लगाते हैं।",
        "गोभी कब लगाएं": "गोभी सितंबर-अक्टूबर में लगाते हैं।",
        "भिंडी कब लगाएं": "भिंडी मार्च-अप्रैल में लगाते हैं।",
        "करेला कब लगाएं": "करेला मार्च-अप्रैल में लगाते हैं।",
        "लौकी कब लगाएं": "लौकी मार्च-अप्रैल में लगाते हैं।",
        "सब्जी की खाद कितनी दें": "सब्जी में गोबर की खाद और एनपीके का प्रयोग करें।",
        "ककड़ी कब लगाएं": "ककड़ी मार्च-अप्रैल में लगाते हैं।",
        "तरबूज कब लगाएं": "तरबूज फरवरी-मार्च में लगाते हैं।",
        "खरबूजा कब लगाएं": "खरबूजा फरवरी-मार्च में लगाते हैं।",
        "हरी मिर्च कब लगाएं": "हरी मिर्च जुलाई-अगस्त में लगाते हैं।",
        
        # Fertilizers & Pesticides
        "खाद कितनी डालें": "फसल के अनुसार खाद डालें। धान में ज्यादा, गेहूं में कम।",
        "यूरिया कितना डालें": "एक एकड़ में 1-2 बोरी यूरिया पर्याप्त है।",
        "डीएपी कितना डालें": "एक एकड़ में 1 बोरी डीएपी काफी है।",
        "पोटाश कितना डालें": "एक एकड़ में 50 किलो पोटाश डालें।",
        "गोबर की खाद कितनी दें": "एक एकड़ में 10-15 ट्रॉली गोबर की खाद डालें।",
        "कम्पोस्ट कैसे बनाएं": "पत्ती, गोबर और मिट्टी मिलाकर कम्पोस्ट बनाएं।",
        "जैविक खाद कैसे बनाएं": "गोबर, मूत्र और पत्ती से जैविक खाद बनाएं।",
        "नीम की खाद कैसे बनाएं": "नीम की पत्ती सड़ाकर खाद बनाएं।",
        "कीटनाशक कब छिड़कें": "शाम के समय कीटनाशक छिड़कें।",
        "कीड़ा कैसे मारें": "नीम का तेल या कीटनाशक का प्रयोग करें।",
        "खाद कब डालें": "बुवाई के समय बेसल खाद डालें।",
        "वर्मीकंपोस्ट कैसे बनाएं": "केंचुओं से वर्मीकंपोस्ट बनाएं।",
        "सुपर फास्फेट कितना डालें": "एक एकड़ में 50 किलो सुपर फास्फेट डालें।",
        "जिंक सल्फेट कब डालें": "धान में रोपाई के समय जिंक सल्फेट डालें।",
        
        # Irrigation & Water Management
        "पानी कब दें": "फसल के अनुसार पानी दें। धान में रोज, गेहूं में 15 दिन में।",
        "सिंचाई कैसे करें": "फव्वारा सिंचाई सबसे अच्छी है। पानी बचता है।",
        "ड्रिप सिस्टम कैसे लगाएं": "ड्रिप सिस्टम के लिए कृषि विभाग से संपर्क करें।",
        "बोरिंग कैसे करवाएं": "बोरिंग के लिए कृषि विभाग से अनुमति लें।",
        "पानी की कमी क्या करें": "बारिश का पानी संग्रहण करें और कम पानी वाली फसल लगाएं।",
        "बाढ़ में क्या करें": "बाढ़ में फसल को जल्दी काटें और सुरक्षित रखें।",
        "सूखा पड़े तो क्या करें": "सूखा प्रतिरोधी बीज लगाएं और मल्चिंग करें।",
        "रेन वाटर हार्वेस्टिंग कैसे करें": "छत से पानी टैंक में इकट्ठा करें।",
        "तालाब कैसे बनवाएं": "तालाब के लिए मनरेगा से मदद लें।",
        "कुआं कैसे खुदवाएं": "कुआं खुदवाने के लिए ग्राम पंचायत से संपर्क करें।",
        "स्प्रिंकलर कैसे लगाएं": "स्प्रिंकलर सिस्टम के लिए सब्सिडी मिलती है।",
        "पाइप लाइन कैसे बिछाएं": "पाइप लाइन के लिए इंजीनियर से सलाह लें।",
        "पानी की गुणवत्ता कैसे जांचें": "पानी की जांच प्रयोगशाला में करवाएं।",
        "भूजल कैसे बचाएं": "ड्रिप सिंचाई और जल संरक्षण करें।",
        
        # Seeds & Varieties
        "बीज कहां से लें": "प्रमाणित बीज कृषि विभाग से या लाइसेंस वाली दुकान से लें।",
        "अच्छा बीज कैसे पहचानें": "बीज साफ, सूखा और बिना टूटा हुआ हो।",
        "बीज का भाव क्या है": "बीज का भाव किस्म के अनुसार 50-500 रुपए प्रति किलो है।",
        "हाइब्रिड बीज कैसा है": "हाइब्रिड बीज में ज्यादा पैदावार होती है।",
        "देसी बीज कैसा है": "देसी बीज कम लागत में होता है लेकिन पैदावार कम।",
        "बीज का भंडारण कैसे करें": "बीज को सूखी और हवादार जगह पर रखें।",
        "पुराना बीज अच्छा है": "नया बीज हमेशा बेहतर होता है। पुराना बीज कम उगता है।",
        "बीज की मात्रा कितनी चाहिए": "एक एकड़ में 20-25 किलो बीज काफी है।",
        "बीज उपचार कैसे करें": "बीज को कार्बेन्डाज़िम से उपचारित करें।",
        "बीज अंकुरण कैसे बढ़ाएं": "बीज को 12 घंटे पानी में भिगोएं।",
        "बीज की जांच कैसे करें": "बीज को पानी में डालकर जांच करें।",
        "बीज कब खरीदें": "बुवाई से 15-20 दिन पहले बीज खरीदें।",
        "प्रमाणित बीज कैसे पहचानें": "प्रमाणित बीज पर लेबल और सील होती है।",
        "बीज की गारंटी कैसे मिलती है": "प्रमाणित बीज डीलर से गारंटी मिलती है।",
        
        # Government Schemes
        "किसान सम्मान निधि कैसे मिलेगी": "आधार कार्ड और बैंक खाता लेकर CSC केंद्र जाएं।",
        "फसल बीमा कैसे करवाएं": "बुवाई के समय ही बीमा करवाएं। CSC केंद्र जाएं।",
        "सब्सिडी कैसे मिलेगी": "कृषि यंत्र की सब्सिडी के लिए आवेदन करें।",
        "केसीसी कैसे बनवाएं": "किसान क्रेडिट कार्ड के लिए बैंक में जाएं।",
        "लोन कैसे मिलेगा": "कृषि लोन के लिए बैंक में जमीन के कागजात लेकर जाएं।",
        "सरकारी योजना क्या है": "प्रधानमंत्री किसान सम्मान निधि, फसल बीमा जैसी योजनाएं हैं।",
        "मुफ्त बीज कैसे मिलेगा": "कृषि विभाग में मुफ्त बीज वितरण का पता करें।",
        "ट्रैक्टर सब्सिडी कैसे मिलेगी": "कृषि यंत्र सब्सिडी के लिए आवेदन करें।",
        "सोलर पंप कैसे मिलेगा": "सोलर पंप की योजना के लिए कृषि विभाग जाएं।",
        "खाद सब्सिडी कैसे मिलेगी": "खाद सब्सिडी सीधे दुकान पर मिलती है।",
        "मिट्टी जांच कैसे करवाएं": "मिट्टी जांच के लिए कृषि विभाग में जाएं।",
        "कृषि यंत्र कैसे मिलेगा": "कृषि यंत्र सब्सिडी के लिए आवेदन करें।",
        "बागवानी सब्सिडी कैसे मिलेगी": "बागवानी विभाग में सब्सिडी के लिए आवेदन करें।",
        "आयुष्मान कार्ड कैसे बनवाएं": "आयुष्मान कार्ड के लिए CSC केंद्र जाएं।",
        
        # Market Prices
        "मंडी भाव क्या है": "आज धान 2000, गेहूं 2200, आलू 1500 रुपए प्रति क्विंटल है।",
        "धान का भाव": "धान का भाव 2000-2200 रुपए प्रति क्विंटल है।",
        "गेहूं का भाव": "गेहूं का भाव 2100-2300 रुपए प्रति क्विंटल है।",
        "आलू का भाव": "आलू का भाव 1500-1800 रुपए प्रति क्विंटल है।",
        "प्याज का भाव": "प्याज का भाव 2000-2500 रुपए प्रति क्विंटल है।",
        "मक्का का भाव": "मक्का का भाव 1800-2000 रुपए प्रति क्विंटल है।",
        "बाजार कहां है": "नजदीकी मंडी आपके जिले में है।",
        "बेचने का समय कब है": "फसल तैयार होने पर तुरंत बेचना चाहिए।",
        "भाव कब बढ़ेगा": "त्योहारों में भाव बढ़ता है।",
        "न्यूनतम समर्थन मूल्य क्या है": "MSP धान के लिए 2040 रुपए प्रति क्विंटल है।",
        "मंडी कैसे पहुंचें": "मंडी तक ट्रांसपोर्ट की व्यवस्था करें।",
        "बेचने का तरीका क्या है": "मंडी में नीलामी के जरिए बेचें।",
        "आढ़ती कैसे चुनें": "विश्वसनीय आढ़ती चुनें।",
        "तौल कैसे करवाएं": "मंडी में सरकारी तराजू से तौल करवाएं।",
        
        # Farm Equipment
        "ट्रैक्टर कौन सा लें": "महिंद्रा, जॉन डियर और स्वराज अच्छी कंपनियां हैं।",
        "हार्वेस्टर कैसे किराये पर लें": "कस्टम हायरिंग केंद्र से हार्वेस्टर किराये पर लें।",
        "रोटावेटर कैसे चलाएं": "रोटावेटर को ट्रैक्टर से जोड़कर खेत में चलाएं।",
        "स्प्रेयर कैसे चलाएं": "स्प्रेयर में दवा भरकर फसल पर छिड़काव करें।",
        "ट्रैक्टर की देखभाल कैसे करें": "नियमित सर्विस और तेल बदलवाएं।",
        "ट्रैक्टर का बीमा कैसे करवाएं": "किसी अच्छी बीमा कंपनी से ट्रैक्टर बीमा करवाएं।",
        "ट्रैक्टर का लोन कैसे लें": "बैंक में जाकर ट्रैक्टर लोन के लिए आवेदन करें।",
        "ट्रैक्टर का सब्सिडी कैसे मिलेगी": "कृषि विभाग से ट्रैक्टर सब्सिडी के लिए आवेदन करें।",
        "ट्रैक्टर का रजिस्ट्रेशन कैसे करवाएं": "आरटीओ कार्यालय में जाकर ट्रैक्टर रजिस्ट्रेशन करवाएं।",
        "ट्रैक्टर का पंचक कैसे करें": "ट्रैक्टर के टायर में हवा भरें और चेक करें।",
        "ट्रैक्टर का तेल कब बदलें": "हर 200 घंटे चलने के बाद तेल बदलें।",
        "ट्रैक्टर का फिल्टर कब बदलें": "हर 100 घंटे चलने के बाद फिल्टर बदलें।",
        "ट्रैक्टर का बैटरी कैसे चेक करें": "बैटरी में पानी और कनेक्शन चेक करें।",
        "ट्रैक्टर का क्लच कैसे चेक करें": "क्लच पेडल को दबाकर चेक करें।",
        
        # Animal Husbandry
        "गाय का दूध कैसे बढ़ाएं": "अच्छा चारा और पानी दें, नियमित दुहें।",
        "भैंस का दूध कैसे बढ़ाएं": "हरा चारा और दाना दें, पानी पर्याप्त दें।",
        "बकरी पालन कैसे करें": "बकरियों को साफ स्थान पर रखें, टीका लगवाएं।",
        "मुर्गी पालन कैसे करें": "मुर्गियों को साफ बाड़े में रखें, टीका दें।",
        "मछली पालन कैसे करें": "तालाब बनवाएं, मछली के बीज डालें।",
        "पशु का टीका कब लगवाएं": "नियमित अंतराल पर पशु चिकित्सक से टीका लगवाएं।",
        "पशु का इलाज कैसे करें": "पशु चिकित्सक को दिखाएं, दवा दें।",
        "पशु का चारा कैसे तैयार करें": "हरा चारा, भूसा और दाना मिलाकर दें।",
        "पशु का दूध कैसे निकालें": "साफ हाथों से या मशीन से दूध निकालें।",
        "पशु का बच्चा कैसे पैदा करें": "पशु चिकित्सक की मदद से प्रसव करवाएं।",
        "पशु का वजन कैसे बढ़ाएं": "पौष्टिक चारा और दाना दें।",
        "पशु का बीमा कैसे करवाएं": "पशु बीमा के लिए बैंक या बीमा कंपनी से संपर्क करें।",
        "पशु का लोन कैसे लें": "पशु पालन लोन के लिए बैंक में आवेदन करें।",
        "पशु का सब्सिडी कैसे मिलेगी": "पशुपालन विभाग से सब्सिडी के लिए आवेदन करें।"
    },
        "Telugu": {
        # Greetings & Basic Interactions (continued)
        "నమస్కారం": "నమస్కారం! నేను జీవ, మీ స్మార్ట్ వ్యవసాయ సహాయకుడిని. నేను మీ వ్యవసాయంలో ప్రతి అడుగులో సహాయం చేస్తాను.",
        "శుభోదయం": "శుభోదయం! ఈ రోజు వ్యవసాయం కోసం ఏమి ప్రణాళిక? నేను మీకు సహాయం చేయగలను.",
        "మీ పేరు ఏమిటి": "నా పేరు జీవ. నేను ఒక AI రైతు సహాయకుడిని.",
        "మీరు ఏమి చేస్తారు": "నేను రైతులకు వ్యవసాయం, వాతావరణం, విత్తనాలు, ఎరువులు, ప్రభుత్వ పథకాల గురించి సమాచారం ఇస్తాను.",
        "ధన్యవాదాలు": "స్వాగతం! సంతోషంగా సహాయం చేసాను. మరేదైనా తెలుసుకోవాలనుకుంటున్నారా?",
        "విదాయం": "విదాయం! సంతోషంగా సహాయం చేసాను. పంట బాగా పండాలి. అవసరమైతే తిరిగి రండి.",
        "మీరు సహాయం చేయగలరా": "అవును! నేను పంటలు, వాతావరణం, విత్తనాలు, ఎరువులు, మార్కెట్ ధరల గురించి సమాచారం ఇవ్వగలను.",
        "మీరు ఎలా పని చేస్తారు": "నేను మీ వాయిస్ విని, వెంటనే సమాధానం ఇస్తాను.",
        
        # Weather & Season
        "వాతావరణం ఎలా ఉంది": "ఈ రోజు వాతావరణం స్పష్టంగా మరియు మంచిగా ఉంది. వ్యవసాయానికి అనుకూలమైన రోజు.",
        "ఈ రోజు వాతావరణం ఎలా ఉంది": "ఈ రోజు వాతావరణం స్పష్టంగా మరియు మంచిగా ఉంది. వ్యవసాయానికి అనుకూలమైన రోజు.",
        "వర్షం పడుతుందా": "అవును, ఈ వారం వర్షం అవకాశం ఉంది. పంటను కప్పడానికి తయారీ చేయండి.",
        "రేపు వర్షం పడుతుందా": "అవును, రేపు వర్షం పడవచ్చు. ముందుగానే తయారీ చేసుకోండి.",
        "ఉష్ణోగ్రత ఎంత ఉంది": "ఈ రోజు ఉష్ణోగ్రత 28 డిగ్రీల సెల్సియస్ ఉంది. పంటకు మంచిది.",
        "వేడి ఎలా ఉంది": "వేడి సాధారణంగా ఉంది. నీటి ఏర్పాట్లు తప్పనిసరిగా చేయండి.",
        "చలి ఎలా ఉంది": "చలి బాగుంది. రబీ పంటకు అద్భుతమైన వాతావరణం.",
        "గాలి ఎలా ఉంది": "గాలి బాగుంది. పంటకు ఎటువంటి నష్టం ఉండదు.",
        "తుఫాను వస్తుందా": "తుఫాను అవకాశం ఉంది. పంటను సురక్షితంగా ఉంచండి.",
        "వడగళ్ళు పడతాయా": "వడగళ్ళు పడే అవకాశం ఉంది. పంటను కప్పండి.",
        "మాన్సూన్ ఎప్పుడు వస్తుంది": "మాన్సూన్ జూన్ మొదటి వారంలో రావచ్చు.",
        "మేఘాలు ఎలా ఉన్నాయి": "ఈ రోజు మేఘాలు కమ్ముకుని ఉన్నాయి. వర్షం పడవచ్చు.",
        "ఎండ ఎలా ఉంది": "ఎండ బాగా ఉంది. పంటకు నీడ అవసరం కావచ్చు.",
        "తేమ ఎంత ఉంది": "గాలిలో తేమ బాగా ఉంది. పంటకు ప్రయోజనకరం.",
        
        # Crop Specific - Rice
        "వరి ఎప్పుడు విత్తాలి": "వరి జూన్-జూలైలో విత్తాలి. ముందు భూమిని బాగా సిద్ధం చేయండి.",
        "వరి విత్తనం ఎలా చేయాలి": "ముందు నర్సరీలో మొక్కలు సిద్ధం చేసుకోండి, తర్వాత 20-25 రోజుల్లో నాట్లు వేయండి.",
        "వరికి ఎరువు ఎంత వేయాలి": "ఒక ఎకరానికి 2 బోరీ యూరియా మరియు 1 బోరీ డిఎపి వేయండి.",
        "వరికి నీరు ఎంత కావాలి": "వరిలో ఎప్పుడూ 2-3 అంగుళాల నీరు ఉంచండి.",
        "వరి పురుగు ఎలా అడ్డుకోవాలి": "వేప నూనె పిచికారి చేయండి లేదా కీటకనాశకం ఉపయోగించండి.",
        "వరి కోత ఎప్పుడు చేయాలి": "వరి 110-120 రోజుల్లో పండిపోతుంది.",
        "వరి యొక్క ఉత్తమ రకం ఏది": "బాస్మతి, పూస సుగంధ మరియు పీఆర్-126 మంచి రకాలు.",
        "వరి ధర ఎంత ఉంది": "వరి ధర క్వింటాల్కు 2000-2200 రూపాయలు.",
        "వరి వ్యాధి ఎలా నయం చేయాలి": "ఫంగిసైడ్ పిచికారి చేయండి మరియు పొలం శుభ్రంగా ఉంచండి.",
        "వరి దిగుబడి ఎంత ఉంటుంది": "మంచి రకం నుండి ఎకరానికి 25-30 క్వింటల్స్ వస్తుంది.",
        "వరి నర్సరీ ఎలా సిద్ధం చేయాలి": "సారవంతమైన నేలలో విత్తనాలు వేసి నీరు నింపండి.",
        "వరి నాట్లు ఎప్పుడు వేయాలి": "విత్తనం వేసిన 20-25 రోజుల తర్వాత నాట్లు వేయండి.",
        "వరి కళ్ళఎడ్డు ఎలా ఉపయోగించాలి": "కళ్ళఎడ్డు పశువుల తిండి మరియు ఎరువుగా ఉపయోగపడుతుంది.",
        "వరి కలుపు ఎలా తొలగించాలి": "చేతితో తీసివేయండి లేదా కలుపు నాశకం ఉపయోగించండి.",
        
        # Crop Specific - Cotton
        "ప్రత్తి ఎప్పుడు విత్తాలి": "ప్రత్తి ఏప్రిల్-మేలో విత్తాలి.",
        "ప్రత్తి విత్తనం ఎలా చేయాలి": "నేలను బాగా సిద్ధం చేసి, వరుసల్లో విత్తనాలు వేయండి.",
        "ప్రత్తికి ఎరువు ఎంత వేయాలి": "ఒక ఎకరానికి 2 బోరీ యూరియా మరియు 1 బోరీ డిఎపి వేయండి.",
        "ప్రత్తి సాగుకు నీరు ఎంత కావాలి": "ప్రత్తికి 5-6 సార్లు నీరు ఇవ్వాలి.",
        "ప్రత్తి కోత ఎప్పుడు చేయాలి": "ప్రత్తి 160-170 రోజుల్లో పండిపోతుంది.",
        "ప్రత్తి యొక్క ఉత్తమ రకం ఏది": "బీటీ, సురభి మరియు నర్మదా మంచి రకాలు.",
        "ప్రత్తి ధర ఎంత ఉంది": "ప్రత్తి ధర క్వింటాల్కు 6000-6500 రూపాయలు.",
        "ప్రత్తి వ్యాధి ఎలా నయం చేయాలి": "సరియైన ఫంగిసైడ్ పిచికారి చేయండి.",
        "ప్రత్తి దిగుబడి ఎంత ఉంటుంది": "మంచి రకం నుండి ఎకరానికి 10-12 క్వింటల్స్ వస్తుంది.",
        "ప్రత్తి పురుగు ఎలా అడ్డుకోవాలి": "బోల్వార్మ్ కోసం సరియైన కీటకనాశకం ఉపయోగించండి.",
        "ప్రత్తి కలుపు ఎలా తొలగించాలి": "కలుపు నాశకాలు ఉపయోగించండి లేదా చేతితో తీసివేయండి.",
        "ప్రత్తి పువ్వులు ఎప్పుడు వస్తాయి": "విత్తనం వేసిన 60-70 రోజుల తర్వాత పువ్వులు వస్తాయి.",
        "ప్రత్తి కాయలు ఎప్పుడు తెరుచుకుంటాయి": "విత్తనం వేసిన 120-130 రోజుల తర్వాత కాయలు తెరుచుకుంటాయి.",
        "ప్రత్తి ఎలా కోయాలి": "కాయలు తెరుచుకున్న తర్వాత చేతితో కోయాలి.",
        
        # Government Schemes (Telugu)
        "రైతు సన్మాన్ నిధి ఎలా పొందాలి": "ఆధార్ కార్డ్ మరియు బ్యాంక్ ఖాతాతో CSC కేంద్రానికి వెళ్లండి.",
        "పంట బీమా ఎలా చేయించుకోవాలి": "విత్తనం వేసే సమయంలోనే బీమా చేయించుకోండి. CSC కేంద్రానికి వెళ్లండి.",
        "సబ్సిడీ ఎలా పొందాలి": "వ్యవసాయ ఉపకరణాల సబ్సిడీ కోసం దరఖాస్తు చేయండి.",
        "కిసాన్ క్రెడిట్ కార్డ్ ఎలా పొందాలి": "బ్యాంకుకు వెళ్లి కిసాన్ క్రెడిట్ కార్డ్ కోసం దరఖాస్తు చేయండి.",
        "లోన్ ఎలా పొందాలి": "వ్యవసాయ రుణం కోసం భూమి కాగితాలతో బ్యాంకుకు వెళ్లండి.",
        "ప్రభుత్వ పథకాలు ఏమిటి": "ప్రధానమంత్రి కిసాన్ సన్మాన్ నిధి, పంట బీమా వంటి పథకాలు ఉన్నాయి.",
        "ఉచిత విత్తనాలు ఎలా పొందాలి": "వ్యవసాయ శాఖలో ఉచిత విత్తనాలు పంపిణీ గురించి తెలుసుకోండి.",
        "ట్రాక్టర్ సబ్సిడీ ఎలా పొందాలి": "వ్యవసాయ ఉపకరణాల సబ్సిడీ కోసం దరఖాస్తు చేయండి.",
        "సోలార్ పంప్ ఎలా పొందాలి": "సోలార్ పంప్ పథకం కోసం వ్యవసాయ శాఖకు వెళ్లండి.",
        "ఎరువు సబ్సిడీ ఎలా పొందాలి": "ఎరువు సబ్సిడీ నేరుగా దుకాణంలో లభిస్తుంది.",
        "నేల పరీక్ష ఎలా చేయించుకోవాలి": "నేల పరీక్ష కోసం వ్యవసాయ శాఖకు వెళ్లండి.",
        "వ్యవసాయ ఉపకరణాలు ఎలా పొందాలి": "వ్యవసాయ ఉపకరణాల సబ్సిడీ కోసం దరఖాస్తు చేయండి.",
        "తోటల పథకాలు ఎలా పొందాలి": "తోటల శాఖలో సబ్సిడీ కోసం దరఖాస్తు చేయండి.",
        "ఆయుష్మాన్ కార్డ్ ఎలా పొందాలి": "ఆయుష్మాన్ కార్డ్ కోసం CSC కేంద్రానికి వెళ్లండి."
    }
}

# ---------- Database Initialization ----------
def init_db():
    conn = sqlite3.connect('kisan_jeevan.db')
    c = conn.cursor()
    
    # Create conversations table
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME,
                  language TEXT,
                  user_input TEXT,
                  bot_response TEXT)''')
    
    # Create user feedback table
    c.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  conversation_id INTEGER,
                  rating INTEGER,
                  comments TEXT,
                  FOREIGN KEY(conversation_id) REFERENCES conversations(id))''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# ---------- Voice Recording Functions ----------
def record_audio(duration=5, sample_rate=16000):
    """Record audio from the microphone."""
    st.info(f"Recording for {duration} seconds... Speak now!")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    st.success("Recording complete!")
    return recording.flatten()

def save_wav(data, filename, sample_rate=16000):
    """Save recorded audio to a WAV file."""
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data.tobytes())

def play_audio(filename):
    """Play audio from a WAV file."""
    try:
        audio_bytes = open(filename, 'rb').read()
        st.audio(audio_bytes, format='audio/wav')
    except Exception as e:
        st.error(f"Error playing audio: {e}")

# ---------- Speech Recognition Functions ----------
def load_vosk_model(language):
    """Load the appropriate Vosk model based on language."""
    model_path = os.path.join('vosk_models', 'small-hi' if language == 'Hindi' else 'small-te')
    if not os.path.exists(model_path):
        st.error(f"Vosk model not found at {model_path}. Please download the model.")
        return None
    return Model(model_path)

def recognize_speech(audio_data, model, sample_rate=16000):
    """Convert speech to text using Vosk."""
    recognizer = KaldiRecognizer(model, sample_rate)
    recognizer.AcceptWaveform(audio_data.tobytes())
    result = json.loads(recognizer.Result())
    return result.get('text', '')

# ---------- Text-to-Speech Functions ----------
def text_to_speech(text, language):
    """Convert text to speech using gTTS."""
    try:
        lang = 'hi' if language == 'Hindi' else 'te'
        tts = gTTS(text=text, lang=lang, slow=False)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_filename = fp.name
            tts.save(temp_filename)
        
        return temp_filename
    except Exception as e:
        st.error(f"Error in text-to-speech: {e}")
        return None

# ---------- Response Generation ----------
def get_best_match(question, language):
    """Find the best matching question in our Q&A database."""
    questions = qa_data[language].keys()
    matches = get_close_matches(question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_response(user_input, language):
    """Get the appropriate response for the user input."""
    # Store conversation in database
    conn = sqlite3.connect('kisan_jeevan.db')
    c = conn.cursor()
    timestamp = datetime.now()
    
    # Check for exact match first
    if user_input in qa_data[language]:
        response = qa_data[language][user_input]
    else:
        # Try to find a close match
        best_match = get_best_match(user_input, language)
        if best_match:
            response = qa_data[language][best_match]
        else:
            response = f"క్షమించండి, నాకు అర్థం కాలేదు. దయచేసి మళ్లీ ప్రయత్నించండి." if language == 'Telugu' else "क्षमा करें, मुझे समझ नहीं आया। कृपया फिर से प्रयास करें।"
    
    # Store conversation in database
    c.execute("INSERT INTO conversations (timestamp, language, user_input, bot_response) VALUES (?, ?, ?, ?)",
              (timestamp, language, user_input, response))
    conn.commit()
    conn.close()
    
    return response

# ---------- UI Components ----------
def display_header():
    """Display the application header."""
    st.markdown("""
    <div class="main-header">
        <h1>🌾 Kisan Jeevan - किसान जीवन - రైతు జీవితం</h1>
        <p>Your voice-enabled offline farming assistant</p>
    </div>
    """, unsafe_allow_html=True)

def language_selector():
    """Language selection dropdown."""
    st.sidebar.markdown("<div class='language-selector'>", unsafe_allow_html=True)
    language = st.sidebar.selectbox("Select Language", ["Hindi", "Telugu"])
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    return language

def record_button(language):
    """Display the microphone button for recording."""
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🎤", key="mic_button", help="Press and hold to record"):
            with st.spinner("Recording..."):
                audio_data = record_audio()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                save_wav(audio_data, temp_file.name)
                
                # Load Vosk model
                model = load_vosk_model(language)
                if model:
                    user_input = recognize_speech(audio_data, model)
                    if user_input:
                        st.session_state.user_input = user_input
                    else:
                        st.warning("Could not understand the audio. Please try again.")
                else:
                    st.error("Speech recognition model not available.")
    return st.session_state.get('user_input', '')

def text_input():
    """Text input field as fallback."""
    return st.text_input("Or type your question here:")

def display_conversation(conversation_history, language):
    """Display the conversation history."""
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    for entry in conversation_history:
        if entry['role'] == 'user':
            st.markdown(f"<div class='user-message'><b>You:</b> {entry['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant-message'><b>Jeev:</b> {entry['text']}</div>", unsafe_allow_html=True)
            
            # Convert response to speech
            if st.button("🔊 Play Response", key=f"play_{entry['timestamp']}"):
                audio_file = text_to_speech(entry['text'], language)
                if audio_file:
                    play_audio(audio_file)
                    os.unlink(audio_file)  # Clean up temporary file
    
    st.markdown("</div>", unsafe_allow_html=True)

def display_features():
    """Display feature cards in the sidebar."""
    st.sidebar.markdown("### Features")
    cols = st.sidebar.columns(2)
    
    with cols[0]:
        st.markdown("""
        <div class="feature-card">
            <h4>🌦️ Weather</h4>
            <p>Get weather updates for your farm</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>🌱 Crops</h4>
            <p>Crop-specific advice</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown("""
        <div class="feature-card">
            <h4>💰 Market Prices</h4>
            <p>Latest commodity prices</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>📜 Schemes</h4>
            <p>Government schemes info</p>
        </div>
        """, unsafe_allow_html=True)

def display_stats():
    """Display statistics cards."""
    st.markdown("### Your Activity")
    cols = st.columns(3)
    
    # Get stats from database
    conn = sqlite3.connect('kisan_jeevan.db')
    c = conn.cursor()
    
    # Total queries
    c.execute("SELECT COUNT(*) FROM conversations")
    total_queries = c.fetchone()[0]
    
    # Today's queries
    c.execute("SELECT COUNT(*) FROM conversations WHERE DATE(timestamp) = DATE('now')")
    today_queries = c.fetchone()[0]
    
    # Most used language
    c.execute("SELECT language, COUNT(*) FROM conversations GROUP BY language ORDER BY COUNT(*) DESC LIMIT 1")
    lang_result = c.fetchone()
    top_language = lang_result[0] if lang_result else "None"
    
    conn.close()
    
    with cols[0]:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{total_queries}</h3>
            <p>Total Queries</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{today_queries}</h3>
            <p>Today's Queries</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{top_language}</h3>
            <p>Preferred Language</p>
        </div>
        """, unsafe_allow_html=True)

# ---------- Main Application ----------
def main():
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    # Display UI components
    display_header()
    language = language_selector()
    display_features()
    
    # Input methods
    user_input = record_button(language)
    if not user_input:
        user_input = text_input()
    
    # Process input and generate response
    if user_input:
        response = get_response(user_input, language)
        
        # Add to conversation history
        st.session_state.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'role': 'user',
            'text': user_input
        })
        
        st.session_state.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'role': 'assistant',
            'text': response
        })
    
    # Display conversation
    display_conversation(st.session_state.conversation_history, language)
    
    # Display statistics
    display_stats()

if __name__ == "__main__":
    main()