from model_loader import ensure_model
import vosk
import wave
import json
import os
import sounddevice as sd
import tempfile
import threading
from gtts import gTTS

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


class JeevaUI(BoxLayout):
    def __init__(self, **kwargs):
        super(JeevaUI, self).__init__(orientation="vertical", **kwargs)

        self.label = Label(text="🎤 Tap to speak in Telugu", font_size=18)
        self.add_widget(self.label)

        self.btn = Button(text="🎙️ Speak", font_size=20, size_hint=(1, 0.3))
        self.btn.bind(on_press=self.start_listening)
        self.add_widget(self.btn)

        # Load model once and reuse
        self.model_path = ensure_model()
        self.model = vosk.Model(self.model_path)
        self.samplerate = 16000

    def start_listening(self, instance):
        self.label.text = "🎧 Listening... Please speak!"
        threading.Thread(target=self.record_and_process).start()

    def record_and_process(self):
        try:
            duration = 5  # seconds
            audio = sd.rec(int(self.samplerate * duration), samplerate=self.samplerate,
                           channels=1, dtype='int16')
            sd.wait()

            # Save temp WAV file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
                wav_file = tmpfile.name
                with wave.open(wav_file, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.samplerate)
                    wf.writeframes(audio.tobytes())

            # Recognize
            with wave.open(wav_file, "rb") as wf:
                rec = vosk.KaldiRecognizer(self.model, self.samplerate)
                text = ""
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text += result.get("text", "") + " "
                final = json.loads(rec.FinalResult())
                text += final.get("text", "")

            os.remove(wav_file)

            if not text.strip():
                response = "🙏 మీరు ఏదైనా చెబుతారా?"
            else:
                response = self.generate_response(text)

            self.label.text = f"🗣 మీరు: {text}\n🤖 జీవా: {response}"
            self.speak(response)

        except Exception as e:
            self.label.text = f"❌ Error: {str(e)}"

    def generate_response(self, query):
        query = query.lower()
        if "ఎరువులు" in query:
            return "🌱 ఈ పంటకి ఆర్గానిక్ ఎరువులు, నత్రజని మరియు పొటాష్ వాడండి."
        elif "వర్షం" in query:
            return "🌧️ నేడు వర్షం పడే అవకాశం 60% ఉంది."
        elif "వ్యాధి" in query or "నివారణ" in query:
            return "🧪 నిమ్ ఆయిల్ వాడండి, ఇది వైరస్‌కి మంచిది."
        elif "ధర" in query:
            return "📈 ఈ రోజు మార్కెట్ లో టమోటా ధర రూ.20 కిలోకు ఉంది."
        else:
            return "🤖 మాఫ్ చేయండి, దయచేసి మీ ప్రశ్నను మరింత స్పష్టంగా అడగండి."

    def speak(self, text, lang='te'):
        try:
            tts = gTTS(text=text, lang=lang)
            audio_path = os.path.join(tempfile.gettempdir(), "response.mp3")
            tts.save(audio_path)
            os.system(f"mpg123 {audio_path}")
        except Exception as e:
            self.label.text += f"\n🔈 Error in TTS: {e}"


class JeevaApp(App):
    def build(self):
        return JeevaUI()


if __name__ == "__main__":
    JeevaApp().run()
