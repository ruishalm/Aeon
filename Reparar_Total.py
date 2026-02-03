import os
import requests
import shutil
import sys

# Configuração de Cores
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def download_seguro(url, caminho_destino, tamanho_minimo_mb):
    pasta = os.path.dirname(caminho_destino)
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    
    nome_arq = os.path.basename(caminho_destino)
    
    # 1. Verificar se arquivo já existe e é válido
    if os.path.exists(caminho_destino):
        tamanho_atual_mb = os.path.getsize(caminho_destino) / (1024 * 1024)
        if tamanho_atual_mb < tamanho_minimo_mb:
            print(f"{RED}[LIXO DETECTADO]{RESET} {nome_arq} tem apenas {tamanho_atual_mb:.2f}MB (Esperado: {tamanho_minimo_mb}MB).")
            print(f"   -> Deletando arquivo corrompido...")
            os.remove(caminho_destino)
        else:
            print(f"{GREEN}[OK]{RESET} {nome_arq} parece válido ({tamanho_atual_mb:.2f}MB).")
            return

    # 2. Baixar
    print(f"{CYAN}[BAIXANDO]{RESET} {nome_arq}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        baixado = 0
        
        with open(caminho_destino, 'wb') as f:
            for chunk in response.iter_content(block_size):
                f.write(chunk)
                baixado += len(chunk)
                # Barra de progresso simples
                if total_size > 0:
                    percent = int((baixado / total_size) * 100)
                    sys.stdout.write(f"\rProgresso: {percent}%")
                    sys.stdout.flush()
        
        print(f"\n{GREEN}[SUCESSO]{RESET} Download concluído!")
        
    except Exception as e:
        print(f"\n{RED}[ERRO]{RESET} Falha ao baixar {nome_arq}: {e}")

# --- LISTA DE ARQUIVOS VITAIS ---
tarefas = [
    {
        "nome": "Kokoro Voz (ONNX)",
        "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx",
        "caminho": os.path.join(BASE_DIR, "bagagem", "kokoro", "kokoro-v0_19.onnx"),
        "min_mb": 300 # Tem que ter ~350MB
    },
    {
        "nome": "Kokoro Vozes (JSON)",
        "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json",
        "caminho": os.path.join(BASE_DIR, "bagagem", "kokoro", "voices.json"),
        "min_mb": 0.01
    },
    {
        "nome": "Visão (MediaPipe Hand)",
        "url": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        "caminho": os.path.join(BASE_DIR, "modules", "visao", "hand_landmarker.task"),
        "min_mb": 0.1
    }
]

print("=== AEON SYSTEM REPAIR ===")
for t in tarefas:
    download_seguro(t['url'], t['caminho'], t['min_mb'])

print(f"\n{CYAN}=== FIM DA REPARAÇÃO ==={RESET}")
input("Pressione ENTER para sair...")