import os
import queue
import sounddevice as sd
import vosk
import json
import tempfile
from gtts import gTTS
import pygame
import time
from difflib import SequenceMatcher

# Initialize pygame for playing audio
pygame.mixer.init()

# Initialize queue and sample rate
q = queue.Queue()
sample_rate = 16000

# Load Vosk Hindi model
model_path = "vosk-model-small-hi-0.22"
if not os.path.exists(model_path):
    print("❌ Hindi model not found. Please download it from: https://alphacephei.com/vosk/models")
    exit()

model = vosk.Model(model_path)
rec = vosk.KaldiRecognizer(model, sample_rate)

# Callback function to collect audio
def callback(indata, frames, time, status):
    if status:
        print("⚠️", status)
    q.put(bytes(indata))

# Function to correct similar recognition errors
def improve_text(text):
    corrections = {
        "namastey": "namaste", "namasthy": "namaste", "namste": "namaste", "hello": "namaste",
        "fertile": "urvarak", "manure": "urvarak", "khaad": "urvarak", "urvarakh": "urvarak",
        "barish": "baarish", "mosam": "mausam", "baaris": "baarish", "rain": "baarish",
        "disease": "bimari", "illness": "bimari", "kit": "bimari", "rog": "bimari",
        "rate": "daam", "cost": "daam", "price": "daam", "keemat": "daam", "kimat": "daam",
        "sahay": "sahayata", "halp": "sahayata", "madad": "sahayata"
    }
    words = text.split()
    return " ".join([corrections.get(word, word) for word in words])

# Fuzzy match to allow slight mistakes
def fuzzy_match(keywords, sentence, threshold=0.7):
    for keyword in keywords:
        for word in sentence.split():
            if SequenceMatcher(None, word, keyword).ratio() >= threshold:
                return True
    return False

# Function to get response based on query
def get_response(query):
    query = query.lower().strip()
    print(f"🤖 प्रोसेस कर रहा हूँ: {query}")

    if fuzzy_match(["namaste", "नमस्ते", "hello"], query):
        return "नमस्ते! मैं जीवन सहायक हूँ, आपकी क्या सहायता कर सकता हूँ?"
    elif fuzzy_match(["sahayata", "help", "मदद", "सहायता"], query):
        return "मैं खेती, उर्वरक, मौसम, बाजार भाव और रोगों की जानकारी दे सकता हूँ।"
    elif fuzzy_match(["urvarak", "खाद", "fertilizer"], query):
        return "आप नाइट्रोजन और जैविक खाद का उपयोग कर सकते हैं।"
    elif fuzzy_match(["baarish", "मौसम", "वर्षा", "बरसात"], query):
        return "आज आपके क्षेत्र में बारिश की 60 प्रतिशत संभावना है।"
    elif fuzzy_match(["bimari", "रोग", "कीट", "disease"], query):
        return "आप नीम तेल का छिड़काव करें, यह कीटों को रोकने में सहायक होगा।"
    elif fuzzy_match(["daam", "कीमत", "भाव", "rate", "price"], query):
        return "आज टमाटर का भाव ₹20 प्रति किलो है।"
    else:
        return f"आपने '{query}' कहा। कृपया खेती, मौसम, खाद या कीमत से जुड़ा सवाल पूछें।"

# ✅ Updated Function to speak the response using gTTS and save to a safe location
def speak(text):
    try:
        # Save file in Documents folder with a unique name
        filename = f"jeeva_response_{int(time.time())}.mp3"
        file_path = os.path.join(os.path.expanduser("~/Documents"), filename)

        # Convert text to speech and save
        tts = gTTS(text=text, lang='hi')
        tts.save(file_path)

        # Play audio
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        # Now wait briefly to ensure the file is unlocked
        time.sleep(0.5)  # Ensure pygame releases the file
        os.remove(file_path)

    except Exception as e:
        print("🔊 बोलने में त्रुटि:", e)


# Main function to run the assistant
def run_jeeva():
    print("🎙️ जीवन हिंदी वॉयस असिस्टेंट सक्रिय है... बोलें!\n")
    with sd.RawInputStream(samplerate=sample_rate, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                text = json.loads(result)["text"]
                if text:
                    corrected = improve_text(text)
                    print(f"\n👂 आपने कहा: {corrected}")
                    response = get_response(corrected)
                    print(f"🗣️ जीवन: {response}")
                    speak(response)

# Start the assistant
if __name__ == "__main__":
    try:
        run_jeeva()
    except KeyboardInterrupt:
        print("\n👋 जीवन सहायक बंद हो गया।")
