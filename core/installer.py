import subprocess
import sys
import os
import requests

class AeonInstaller:
    """
    Gerencia instalação automática de dependências e downloads de modelos.
    """
    def __init__(self):
        self.piper_exe = None
        self.voice_model = None

    def install_package(self, package_name):
        print(f"[INSTALLER] Verificando/Instalando {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            return True
        except Exception as e:
            print(f"[INSTALLER] Erro ao instalar {package_name}: {e}")
            return False

    def download_file(self, url, dest_path):
        if os.path.exists(dest_path):
            return True
            
        print(f"[INSTALLER] Baixando {os.path.basename(dest_path)}...")
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            # Adiciona headers para evitar bloqueio (403 Forbidden)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[INSTALLER] Download concluído: {dest_path}")
            return True
        except Exception as e:
            print(f"[INSTALLER] Erro ao baixar arquivo: {e}")
            return False

    def check_pyaudio(self):
        """Verifica e tenta instalar PyAudio (crítico para audição)."""
        # Verifica dependência do módulo de lembretes que estava falhando
        self.install_package("dateparser")
        self.install_package("mediapipe")
        self.install_package("python-dotenv")

        try:
            import pyaudio
            return True
        except ImportError:
            print("[INSTALLER] PyAudio ausente. Tentando instalar...")
            # Tenta instalar via pip normal
            if self.install_package("pyaudio"):
                return True
            
            # Se falhar (comum no Windows), tenta pipwin
            print("[INSTALLER] Pip falhou. Tentando via pipwin...")
            self.install_package("pipwin")
            try:
                subprocess.check_call([sys.executable, "-m", "pipwin", "install", "pyaudio"])
                return True
            except Exception as e:
                print(f"[INSTALLER] Falha crítica no PyAudio: {e}")
                return False

    def verificar_piper(self):
        return False 
    def verificar_ollama(self):
        return False