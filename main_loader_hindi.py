import os
import urllib.request
import zipfile

def ensure_model():
    model_dir = "vosk-model-small-hi-0.22"
    zip_url = "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip"
    zip_name = "model.zip"

    if not os.path.exists(model_dir):
        print("📥 Downloading Hindi model...")
        urllib.request.urlretrieve(zip_url, zip_name)

        with zipfile.ZipFile(zip_name, 'r') as zip_ref:
            zip_ref.extractall(".")

        os.remove(zip_name)
        print("✅ Hindi model downloaded and extracted.")

    return model_dir
