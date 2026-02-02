# instalar_forca_bruta.py
import os
import requests

def download(url, path):
    print(f"Baixando: {os.path.basename(path)}...")
    r = requests.get(url, stream=True)
    with open(path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Concluído.")

base = os.path.join(os.path.dirname(__file__), "bagagem", "kokoro")
os.makedirs(base, exist_ok=True)

# Links Oficiais Diretos (Garantidos)
url_model = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
url_voices = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json"

download(url_model, os.path.join(base, "kokoro-v0_19.onnx"))
download(url_voices, os.path.join(base, "voices.json"))

print("\n✅ ARQUIVOS DE VOZ RESTAURADOS.")