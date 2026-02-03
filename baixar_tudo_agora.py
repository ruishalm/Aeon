import os
import requests
import sys

# --- CONFIGURAÇÃO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminhos de destino
KOKORO_DIR = os.path.join(BASE_DIR, "bagagem", "kokoro")
VISAO_DIR = os.path.join(BASE_DIR, "modules", "visao")

# URLs e Arquivos
DOWNLOADS = [
    {
        "nome": "Cérebro de Voz (Kokoro ONNX)",
        "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx",
        "destino": os.path.join(KOKORO_DIR, "kokoro-v0_19.onnx"),
        "min_size_mb": 300 # Se tiver menos que isso, apaga e baixa de novo
    },
    {
        "nome": "Mapa de Vozes (JSON)",
        "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json",
        "destino": os.path.join(KOKORO_DIR, "voices.json"),
        "min_size_mb": 0.01
    },
    {
        "nome": "Cérebro de Visão (MediaPipe Hand)",
        "url": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        "destino": os.path.join(VISAO_DIR, "hand_landmarker.task"),
        "min_size_mb": 0.1
    }
]

def download_arquivo(item):
    nome = item['nome']
    url = item['url']
    destino = item['destino']
    min_size = item['min_size_mb'] * 1024 * 1024

    # Garante que a pasta existe
    os.makedirs(os.path.dirname(destino), exist_ok=True)

    # Verificação prévia
    if os.path.exists(destino):
        tamanho_atual = os.path.getsize(destino)
        if tamanho_atual < min_size:
            print(f"[!] {nome}: Arquivo corrompido ou incompleto ({tamanho_atual/1024/1024:.2f} MB). Baixando novamente...")
            os.remove(destino)
        else:
            print(f"[OK] {nome} já está pronto.")
            return

    print(f"⬇️ Baixando: {nome}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        
        with open(destino, 'wb') as f:
            baixado = 0
            for chunk in response.iter_content(chunk_size=8192):
                baixado += len(chunk)
                f.write(chunk)
                if total > 0:
                    done = int(50 * baixado / total)
                    sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {baixado/1024/1024:.2f} MB")
                    sys.stdout.flush()
        print("\n   ✅ Concluído!")
    except Exception as e:
        print(f"\n   ❌ Falha: {e}")

# --- EXECUÇÃO ---
if __name__ == "__main__":
    print("=== CENTRAL DE ATUALIZAÇÃO AEON V85 ===")
    print("Verificando integridade dos sistemas neurais...")
    print("-" * 40)
    
    for item in DOWNLOADS:
        download_arquivo(item)
        
    print("-" * 40)
    print("Tudo pronto. Inicie com: python main.py")