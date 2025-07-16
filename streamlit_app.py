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

# Import for transliteration
from indic_transliteration import sanscript
from indic_transliteration.sanscript import SchemeMap, SCHEMES, transliterate

# Enhanced Configuration
st.set_page_config(
    page_title="Kisan JEEVA - किसान जीवा", # Changed from Jeevan to JEEVA
    page_icon="�",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* General body styling */
    body {
        font-family: 'Inter', sans-serif;
        background-color: #eef2f6; /* Lighter, softer background */
    }

    .main-header {
        background: linear-gradient(135deg, #4CAF50, #2E7D32); /* Vibrant green gradient */
        color: white;
        padding: 2.8rem; /* Increased padding */
        border-radius: 20px; /* More rounded corners */
        margin-bottom: 3rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3); /* Stronger, softer shadow */
        animation: fadeInDown 1s ease-out;
    }
    .main-header h1 {
        font-size: 3.8rem; /* Larger title */
        margin-bottom: 0.6rem;
        text-shadow: 2px 2px 5px rgba(0,0,0,0.4); /* More pronounced text shadow */
        font-weight: 700; /* Bolder title */
    }
    .main-header p {
        font-size: 1.3rem; /* Slightly larger subtitle */
        opacity: 0.95;
    }

    .stApp {
        background-color: #eef2f6;
    }

    /* Chat container */
    .chat-container {
        background: #ffffff; /* White background for chat */
        border-radius: 25px; /* Even more rounded */
        padding: 2.2rem; /* Increased padding */
        margin-bottom: 2rem;
        border: 1px solid #e5e5e5; /* Very subtle border */
        box-shadow: 0 6px 20px rgba(0,0,0,0.12); /* Softer, wider shadow */
        max-height: 70vh; /* Limit height for scrollability */
        overflow-y: auto; /* Enable scrolling */
        display: flex;
        flex-direction: column-reverse; /* Show latest messages at bottom */
    }
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    .chat-container::-webkit-scrollbar-track {
        background: #f8f8f8;
        border-radius: 10px;
    }
    .chat-container::-webkit-scrollbar-thumb {
        background: #a0a0a0; /* Darker scrollbar */
        border-radius: 10px;
    }
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #777;
    }
    
    /* Message styling */
    .user-message, .assistant-message {
        border-radius: 18px; /* Slightly more rounded message bubbles */
        padding: 1.3rem 1.6rem;
        margin: 1rem 0; /* More vertical spacing */
        max-width: 80%; /* Slightly narrower messages */
        word-wrap: break-word;
        animation: fadeInUp 0.5s ease-out;
        font-size: 1.05rem; /* Slightly larger text */
    }

    .user-message {
        background: #e0f2f7; /* Lighter, softer blue */
        border-left: 6px solid #2196F3; /* Stronger border */
        align-self: flex-end; /* Align user messages to the right */
        margin-left: auto; /* Push to right */
        box-shadow: 0 3px 10px rgba(33, 150, 243, 0.25); /* Refined shadow */
    }
    
    .assistant-message {
        background: #e8f5e9; /* Lighter, softer green */
        border-left: 6px solid #4CAF50; /* Stronger border */
        align-self: flex-start; /* Align assistant messages to the left */
        margin-right: auto; /* Push to left */
        box-shadow: 0 3px 10px rgba(76, 175, 80, 0.25); /* Refined shadow */
    }

    .user-message b, .assistant-message b {
        font-weight: 700; /* Bolder names */
        color: #222; /* Darker text for names */
    }

    /* Microphone button */
    div.stButton > button:first-child[key="mic_button"] {
        background: linear-gradient(135deg, #FF7043, #F4511E); /* More vibrant orange-red gradient */
        color: white;
        border: none;
        border-radius: 50%;
        width: 100px; /* Even larger */
        height: 100px;
        font-size: 3rem; /* Larger icon */
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(255,112,67,0.5); /* Stronger, softer shadow */
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem auto; /* Center and add more margin */
        border: 4px solid #FFCCBC; /* Slightly thicker light border */
    }
    div.stButton > button:first-child[key="mic_button"]:hover {
        transform: scale(1.18); /* More pronounced hover effect */
        box-shadow: 0 10px 30px rgba(255,112,67,0.6);
    }

    /* Play Response Button */
    .stButton button {
        background-color: #78909C; /* Softer greyish blue */
        color: white;
        border-radius: 10px; /* More rounded */
        padding: 0.6rem 1.2rem; /* Slightly more padding */
        font-size: 0.95rem; /* Slightly larger font */
        margin-top: 0.6rem;
        transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease;
        box-shadow: 0 3px 8px rgba(0,0,0,0.15); /* Softer shadow */
    }
    .stButton button:hover {
        background-color: #607D8B;
        transform: translateY(-3px);
        box-shadow: 0 5px 12px rgba(0,0,0,0.25);
    }

    /* Language selector and sidebar */
    .language-selector {
        background: white;
        border-radius: 15px; /* More rounded */
        padding: 1.5rem; /* Increased padding */
        margin-bottom: 2rem;
        border: 2px solid #81C784; /* Softer green border */
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); /* Softer shadow */
    }
    .stSidebar > div:first-child {
        background: linear-gradient(180deg, #E8F5E9, #DCEDC8); /* Light green gradient for sidebar */
        padding-top: 2.5rem;
        border-right: 1px solid #c8e6c9;
        box-shadow: 2px 0 10px rgba(0,0,0,0.05); /* Subtle shadow for sidebar */
    }
    .stSidebar .stSelectbox {
        margin-bottom: 1.2rem;
    }

    /* Stats cards */
    .stats-card {
        background: white;
        border-radius: 15px; /* More rounded */
        padding: 2rem; /* Increased padding */
        margin: 0.8rem; /* More margin */
        text-align: center;
        box-shadow: 0 5px 18px rgba(0,0,0,0.15); /* Stronger, softer shadow */
        border: 1px solid #f2f2f2;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .stats-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.25);
    }
    .stats-card h3 {
        color: #388E3C; /* Green for stats numbers */
        font-size: 2.8rem; /* Larger numbers */
        margin-bottom: 0.6rem;
        font-weight: 700;
    }
    .stats-card p {
        color: #666; /* Softer text color */
        font-size: 1.1rem; /* Slightly larger text */
    }

    /* Feature cards */
    .feature-card {
        background: white;
        border-radius: 15px; /* More rounded */
        padding: 1.8rem; /* Increased padding */
        margin: 0.8rem 0;
        text-align: center;
        border: 1px solid #e5e5e5;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08); /* Softer shadow */
    }
    .feature-card:hover {
        transform: translateY(-10px); /* More pronounced hover effect */
        box-shadow: 0 10px 25px rgba(0,0,0,0.18);
    }
    .feature-card h4 {
        color: #4CAF50;
        margin-bottom: 0.6rem;
        font-size: 1.4rem; /* Slightly larger title */
        font-weight: 600;
    }
    .feature-card p {
        font-size: 1rem; /* Slightly larger text */
        color: #777;
    }

    /* Clear Chat Button */
    .stButton[key="clear_chat_button"] button {
        background-color: #E57373; /* Softer red for clear button */
        color: white;
        border-radius: 10px; /* More rounded */
        padding: 1rem 1.8rem; /* More padding */
        font-size: 1.1rem; /* Larger font */
        margin-top: 2rem;
        transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease;
        box-shadow: 0 5px 15px rgba(229,115,115,0.4); /* Stronger, softer shadow */
    }
    .stButton[key="clear_chat_button"] button:hover {
        background-color: #EF5350;
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(229,115,115,0.5);
    }

    /* Text Input Field */
    .stTextInput > div > div > input {
        border-radius: 12px; /* Rounded corners for input */
        padding: 0.8rem 1rem; /* More padding */
        border: 2px solid #ccc; /* Subtle border */
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.08); /* Inner shadow */
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #4CAF50; /* Green border on focus */
        box-shadow: 0 0 0 0.2rem rgba(76, 175, 80, 0.25); /* Focus ring */
    }

    /* Submit Text Button */
    .stButton[key="submit_text_button"] button {
        background-color: #66BB6A; /* Green for submit button */
        color: white;
        border-radius: 10px;
        padding: 0.8rem 1.5rem;
        font-size: 1rem;
        margin-top: 1rem; /* Space below input */
        transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease;
        box-shadow: 0 3px 8px rgba(102,187,106,0.3);
    }
    .stButton[key="submit_text_button"] button:hover {
        background-color: #4CAF50;
        transform: translateY(-2px);
        box-shadow: 0 5px 12px rgba(102,187,106,0.4);
    }

    /* Animations */
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-30px); } /* More pronounced animation */
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); } /* More pronounced animation */
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# ---------- Comprehensive Q&A Data for Farmers (100+ questions each) ----------
qa_data = {
    "Hindi": {
        # Greetings & Basic Interactions
        "नमस्ते": "नमस्ते! मैं जीवा हूं, आपका स्मार्ट कृषि सहायक। मैं आपकी खेती में हर कदम पर मदद करूंगा।", # Changed from जीव to जीवा
        "हेलो": "नमस्ते! मैं जीवा हूं, आपका स्मार्ट कृषि सहायक। मैं आपकी खेती में हर कदम पर मदद करूंगा।", # Changed from जीव to जीवा
        "गुड मॉर्निंग": "सुप्रभात! आज खेती के लिए क्या योजना है? मैं आपकी मदद करूंगा।",
        "तुम्हारा नाम क्या है": "मेरा नाम जीवा है। मैं एक AI किसान सहायक हूं।", # Changed from जीव to जीवा
        "आपका नाम क्या है": "मेरा नाम जीवा है। मैं एक AI किसान सहायक हूं।", # Changed from जीव to जीवा
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
        "स्प्रिंकलर कैसे लगाएं": "स्प्रinkler सिस्टम के लिए सब्सिडी मिलती है।",
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
        "पशु का सब्सिडी कैसे मिलेगी": "पशुपालन विभाग से सब्सिडी के लिए आवेदन करें."
    },
        "Telugu": {
        # Greetings & Basic Interactions (continued)
        "నమస్కారం": "నమస్కారం! నేను జీవా, మీ స్మార్ట్ వ్యవసాయ సహాయకుడిని. నేను మీ వ్యవసాయంలో ప్రతి అడుగులో సహాయం చేస్తాను.", # Changed from జీవ to జీవా
        "శుభోదయం": "శుభోదయం! ఈ రోజు వ్యవసాయం కోసం ఏమి ప్రణాళిక? నేను మీకు సహాయం చేయగలను.",
        "మీ పేరు ఏమిటి": "నా పేరు జీవా. నేను ఒక AI రైతు సహాయకుడిని.", # Changed from జీవ to జీవా
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
    # Ensure the vosk_models directory exists and contains the models
    model_name = 'small-hi' if language == 'Hindi' else 'small-te'
    model_path = os.path.join(os.getcwd(), 'vosk_models', model_name) 
    
    if not os.path.exists(model_path):
        st.error(f"Vosk model for {language} not found at {model_path}.")
        st.markdown(f"""
        <p>Please download the <b>{model_name}</b> Vosk model and place it in a folder named <code>vosk_models</code> in the same directory as this script.</p>
        <p>You can find models here: <a href="https://alphacephei.com/vosk/models" target="_blank">Vosk Models</a></p>
        <p>For Hindi, look for a model like <code>vosk-model-hi-0.22</code>. After downloading, extract it and rename the inner folder (e.g., <code>vosk-model-hi-0.22</code>) to <code>small-hi</code>.</p>
        <p>For Telugu, look for a model like <code>vosk-model-te-0.4</code>. After downloading, extract it. **Important:** The contents of the extracted folder (e.g., <code>vosk-model-te-0.4</code>) should be moved directly into your <code>small-te</code> folder, not the folder itself. For example, <code>vosk_models/small-te/am</code> should exist, not <code>vosk_models/small-te/vosk-model-te-0.4/am</code>.</p>
        """, unsafe_allow_html=True)
        return None
    
    # Check if the model directory is empty or doesn't contain expected subdirectories
    expected_subdirs = ['am', 'conf', 'graph', 'ivector'] # Common Vosk model subdirectories
    if not any(os.path.isdir(os.path.join(model_path, d)) for d in expected_subdirs):
        st.error(f"Vosk model for {language} at {model_path} appears empty or incorrectly structured.")
        st.markdown(f"""
        <p>The folder <code>{model_path}</code> does not seem to contain the necessary Vosk model files. Please ensure you have extracted the model correctly and that its contents (like 'am', 'conf', 'graph' folders) are directly inside <code>{model_name}</code>, not in a nested subfolder.</p>
        """, unsafe_allow_html=True)
        return None

    try:
        return Model(model_path)
    except Exception as e:
        st.error(f"Error loading Vosk model from {model_path}. This might be due to an incorrect model path or a corrupted model. Ensure the model's contents are directly inside '{model_name}' folder, not nested further: {e}")
        return None

def recognize_speech(audio_data, model, sample_rate=16000):
    """Convert speech to text using Vosk."""
    try:
        recognizer = KaldiRecognizer(model, sample_rate)
        recognizer.AcceptWaveform(audio_data.tobytes())
        result = json.loads(recognizer.Result())
        return result.get('text', '')
    except Exception as e:
        st.error(f"Error during speech recognition: {e}")
        return ""

# ---------- Text-to-Speech Functions ----------
def text_to_speech(text, language):
    """Convert text to speech using gTTS."""
    try:
        lang_code = 'hi' if language == 'Hindi' else 'te'
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
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
    # Lowercase all questions in qa_data for consistent comparison
    lower_case_questions = {q.lower(): q for q in questions}
    
    st.info(f"DEBUG: Searching for match for input: '{question.lower()}'") # Debugging message
    st.info(f"DEBUG: Available questions (lowercased): {list(lower_case_questions.keys())}") # Debugging message
    
    # Adjusted cutoff for more flexibility in matching
    matches = get_close_matches(question.lower(), lower_case_questions.keys(), n=1, cutoff=0.75) # Increased cutoff
    
    if matches:
        # Return the original cased question from the qa_data
        st.info(f"DEBUG: Found raw match: '{matches[0]}'") # Debugging message
        return lower_case_questions[matches[0]]
    return None

def get_response(user_input, language):
    """Get the appropriate response for the user input."""
    conn = sqlite3.connect('kisan_jeevan.db')
    c = conn.cursor()
    timestamp = datetime.now()
    
    response = ""
    # Check for exact match first (case-insensitive)
    found_exact = False
    for q_key in qa_data[language]:
        if user_input.lower() == q_key.lower():
            response = qa_data[language][q_key]
            found_exact = True
            st.info(f"DEBUG: Found exact match for '{user_input}' as '{q_key}'") # Debugging message
            break
            
    if not found_exact:
        # Try to find a close match
        best_match_key = get_best_match(user_input, language)
        if best_match_key:
            response = qa_data[language][best_match_key]
            st.info(f"DEBUG: Found best match for '{user_input}' as '{best_match_key}'") # Debugging message
        else:
            response = f"క్షమించండి, నాకు అర్థం కాలేదు. దయచేసి మళ్లీ ప్రయత్నించండి." if language == 'Telugu' else "क्षमा करें, मुझे समझ नहीं आया। कृपया फिर से प्रयास करें।"
            st.warning(f"DEBUG: No close match found for '{user_input}' in {language} Q&A data.") # Debugging message
    
    # Store conversation in database
    try:
        c.execute("INSERT INTO conversations (timestamp, language, user_input, bot_response) VALUES (?, ?, ?, ?)",
                  (timestamp, language, user_input, response))
        conn.commit()
    except Exception as e:
        st.error(f"Error saving conversation to database: {e}")
    finally:
        conn.close()
        
    return response

# ---------- Transliteration Function ----------
def transliterate_input(text, target_language):
    """Transliterates Roman script to Hindi (Devanagari) or Telugu script."""
    if not text:
        return ""

    # Normalize input to lowercase for consistent transliteration
    text_lower = text.lower()

    if target_language == "Hindi":
        # Transliterate from Roman (ITRANS) to Devanagari
        return transliterate(text_lower, sanscript.ITRANS, sanscript.DEVANAGARI)
    elif target_language == "Telugu":
        # Transliterate from Roman (ITRANS) to Telugu
        return transliterate(text_lower, sanscript.ITRANS, sanscript.TELUGU)
    else:
        return text # Return original if language not supported for transliteration

# ---------- UI Components ----------
def display_header():
    """Display the application header."""
    st.markdown("""
    <div class="main-header">
        <h1>🌾 Kisan JEEVA - किसान जीवा - రైతు జీవితం</h1>
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
        # Using a fixed width button for better styling control
        st.markdown(
            """
            <style>
            div.stButton > button:first-child {
                background: linear-gradient(135deg, #FF5722, #D32F2F);
                color: white;
                border: none;
                border-radius: 50%;
                width: 90px; /* Slightly larger */
                height: 90px;
                font-size: 2.5rem; /* Larger icon */
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 6px 20px rgba(255,87,34,0.4); /* More prominent shadow */
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 1.5rem auto; /* Center and add more margin */
                border: 3px solid #FFCCBC; /* Light border */
            }
            div.stButton > button:first-child:hover {
                transform: scale(1.15); /* More pronounced hover effect */
                box-shadow: 0 8px 25px rgba(255,87,34,0.5);
            }
            </style>
            """, unsafe_allow_html=True
        )
        if st.button("🎤", key="mic_button", help="Click to record for 5 seconds"):
            with st.spinner("Recording..."):
                audio_data = record_audio()
                # Use BytesIO to avoid saving to disk for temporary audio
                audio_io = io.BytesIO()
                with wave.open(audio_io, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(audio_data.tobytes())
                audio_io.seek(0) # Rewind to the beginning of the BytesIO object
                
                # Load Vosk model
                model = load_vosk_model(language)
                if model:
                    user_input_text = recognize_speech(audio_data, model)
                    if user_input_text:
                        st.session_state.processed_input = user_input_text # Store in a new session state variable
                    else:
                        st.warning("Could not understand the audio. Please try again.")
                else:
                    st.error("Speech recognition model not available. Please check the setup instructions in the sidebar.")
            # Important: Rerun only after processing the input
            st.rerun()
    return "" # Return empty string to prevent immediate processing on button press

def text_input_field(language):
    """Text input field with transliteration and a submit button."""
    # Use a unique key for the text input to manage its state
    # Store the raw input in session state to persist it across reruns
    if 'raw_text_input' not in st.session_state:
        st.session_state.raw_text_input = ""
    
    raw_input = st.text_input("Or type your question here (in Roman script for transliteration):", 
                              value=st.session_state.raw_text_input, 
                              key="user_text_input_widget")
    
    # Update session state with the current raw input
    st.session_state.raw_text_input = raw_input

    transliterated_text = ""
    if raw_input:
        transliterated_text = transliterate_input(raw_input, language)
        st.markdown(f"**Transliterated:** *{transliterated_text}*")
        st.info(f"DEBUG: Raw input: '{raw_input}'") # Debugging message
        st.info(f"DEBUG: Transliterated input: '{transliterated_text}'") # Debugging message
        
    # Add a submit button for the text input
    if st.button("Submit Text", key="submit_text_button"):
        if transliterated_text:
            st.session_state.processed_input = transliterated_text # Store in a new session state variable
            st.session_state.raw_text_input = "" # Clear the raw input field after submission
            st.rerun() # Rerun only after storing the processed input
        else:
            st.warning("Please type a question before submitting.")
    return "" # Always return empty string here, actual processing happens via session_state.processed_input

def display_conversation(conversation_history, language):
    """Display the conversation history."""
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    # Iterate through history in normal order to display from oldest to newest
    for i, entry in enumerate(conversation_history): # Changed to normal order
        if entry['role'] == 'user':
            st.markdown(f"<div class='user-message'><b>You:</b> {entry['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant-message'><b>JEEVA:</b> {entry['text']}</div>", unsafe_allow_html=True) # Changed from Jeev to JEEVA
            
            # Convert response to speech and provide a play button
            # Use a unique key for each play button based on index or timestamp
            play_button_key = f"play_response_{i}_{entry['timestamp']}"
            if st.button("🔊 Play Response", key=play_button_key):
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
    if 'processed_input' not in st.session_state:
        st.session_state.processed_input = "" # New variable to hold input for processing

    # Display UI components
    display_header()
    language = language_selector()
    display_features()
    
    st.write("---") # Separator
    st.markdown("### Ask JEEVA") # Changed from Jeev to JEEVA

    # Input methods
    # These functions now only *set* st.session_state.processed_input and trigger rerun
    record_button(language) 
    text_input_field(language)
    
    # Process input ONLY if processed_input is set and not empty
    if st.session_state.processed_input:
        current_user_input = st.session_state.processed_input
        st.session_state.processed_input = "" # Clear it immediately after reading to prevent re-processing
        
        st.session_state.conversation_history.append({'role': 'user', 'text': current_user_input})
        bot_response = get_response(current_user_input, language)
        st.session_state.conversation_history.append({'role': 'assistant', 'text': bot_response, 'timestamp': datetime.now().isoformat()})
        # No st.rerun() here, as it was already triggered by the button click in input functions
        # This ensures the conversation is appended only once.

    # Display conversation history
    # The display_conversation function now iterates in normal order, so reverse() is removed there.
    display_conversation(st.session_state.conversation_history, language)

    st.write("---") # Separator
    display_stats()

    # Clear chat button
    if st.button("Clear Chat History", key="clear_chat_button"):
        st.session_state.conversation_history = []
        st.session_state.processed_input = "" # Also clear any pending input
        st.session_state.raw_text_input = "" # Clear the raw text input field
        st.rerun()

# Run the main application
if __name__ == "__main__":
    main()
