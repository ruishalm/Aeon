import os
import requests
from tqdm import tqdm

def download_file(url, filename):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    t = tqdm(total=total_size, unit='iB', unit_scale=True)
    with open(filename, 'wb') as f:
        for data in response.iter_content(block_size):
            t.update(len(data))
            f.write(data)
    t.close()

# Caminhos
base_dir = os.path.dirname(os.path.abspath(__file__))
kokoro_dir = os.path.join(base_dir, "bagagem", "kokoro")
model_path = os.path.join(kokoro_dir, "kokoro-v0_19.onnx")

print("=== CORREÇÃO DO KOKORO AEON ===")

# 1. Apagar o arquivo errado (Pickle)
if os.path.exists(model_path):
    print(f"Apagando arquivo corrompido/errado: {model_path}")
    os.remove(model_path)

# 2. Baixar o correto (ONNX Real)
url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
print(f"Baixando modelo ONNX CORRETO (~350MB)...")
try:
    download_file(url, model_path)
    print("\n✅ Sucesso! Agora a voz vai funcionar.")
except Exception as e:
    print(f"\n❌ Erro no download: {e}")