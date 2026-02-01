# PRÉ-REQUISITOS PARA KOKORO TTS:
# 1. Instale as dependências: pip install kokoro-onnx soundfile
# 2. Baixe 'kokoro-v0_19.onnx' e 'voices.json'.
# 3. Crie a pasta 'bagagem/kokoro/' e coloque os arquivos lá.

import os
import re
import asyncio
import subprocess
import random
import threading
import time
import pygame
import edge_tts
import pyttsx3
import soundfile as sf
try:
    from kokoro_onnx import Kokoro
except ImportError:
    Kokoro = None

def log_display(msg):
    print(f"[IO_HANDLER] {msg}")

class IOHandler:
    """
    Gerencia áudio com proteção de threads (Lock).
    Prioridade de fala: Kokoro (local) > Edge-TTS (online) > pyttsx3 (legado).
    """
    def __init__(self, config: dict, installer=None):
        self.config = config if config else {}
        self.installer = installer
        self.parar_fala = False
        self.audio_lock = threading.Lock() # <--- A PROTEÇÃO
        self.kokoro_instance = None
        
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.temp_audio_path = os.path.join(base_path, "bagagem", "temp")
        os.makedirs(self.temp_audio_path, exist_ok=True)
        
        # Carrega o modelo Kokoro na inicialização
        if Kokoro:
            try:
                kokoro_model_path = os.path.join(base_path, "bagagem", "kokoro", "kokoro-v0_19.onnx")
                kokoro_voices_path = os.path.join(base_path, "bagagem", "kokoro", "voices.json")

                if os.path.exists(kokoro_model_path) and os.path.exists(kokoro_voices_path):
                    log_display("Carregando modelo Kokoro TTS...")
                    self.kokoro_instance = Kokoro(model_path=kokoro_model_path, voices_path=kokoro_voices_path)
                    log_display("Kokoro TTS carregado com sucesso.")
                else:
                    log_display("[AVISO] Arquivos do Kokoro TTS não encontrados em 'bagagem/kokoro/'.")
            except Exception as e:
                log_display(f"[ERRO] Falha ao carregar Kokoro TTS: {e}")
                self.kokoro_instance = None
        else:
            log_display("[AVISO] Biblioteca 'kokoro-onnx' não instalada. Kokoro TTS desativado.")

        try:
            pygame.mixer.init()
        except Exception as e:
            log_display(f"Erro ao inicializar pygame.mixer: {e}")

    def _tocar_audio(self, arquivo: str):
        with self.audio_lock: # Só um por vez
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                pygame.mixer.music.load(arquivo)
                pygame.mixer.music.play()
            except Exception as e:
                log_display(f"Erro ao tocar áudio: {e}")
                return

        while pygame.mixer.music.get_busy():
            if self.parar_fala:
                pygame.mixer.music.stop()
                break
            time.sleep(0.1)
        
        threading.Thread(target=self._limpar_seguro, args=(arquivo,), daemon=True).start()

    def _limpar_seguro(self, arquivo: str):
        try:
            pygame.mixer.music.unload()
        except: pass
        
        time.sleep(0.5)
        try:
            if os.path.exists(arquivo): os.remove(arquivo)
        except Exception as e:
            log_display(f"Erro ao limpar arquivo de áudio temporário: {e}")

    def falar(self, texto: str):
        if not texto: return
        self.parar_fala = False
        
        if len(texto) > 1000:
            texto = texto.split('\n')[0]

        clean_text = re.sub(r'[*_#`]', '', texto).replace('\n', ' ').strip()
        if not clean_text: return

        # Tentativa 1: KOKORO TTS (Local & Neural)
        try:
            if self.kokoro_instance:
                log_display(f"Tentando Kokoro-TTS para: {clean_text[:30]}...")
                # Lê a voz do arquivo de configuração, com 'bm_lewis' como padrão
                kokoro_voice = self.config.get("KOKORO_VOICE", "bm_lewis")
                
                # O lang="pt-br" é CRUCIAL para a pronúncia correta
                samples, sample_rate = self.kokoro_instance.create(
                    clean_text, 
                    voice=kokoro_voice, 
                    speed=1.0, 
                    lang="pt-br"
                )
                
                temp_file = os.path.join(self.temp_audio_path, f"fala_kokoro_{random.randint(1000, 9999)}.wav")
                sf.write(temp_file, samples, sample_rate)
                
                self._tocar_audio(temp_file)
                return
        except Exception as e:
            log_display(f"[IO] Falha no Kokoro: {e}. Tentando fallback...")

        # Tentativa 2: EDGE-TTS (Fallback Online)
        temp_file_edge = os.path.join(self.temp_audio_path, f"fala_edge_{random.randint(1000, 9999)}.mp3")
        try:
            async def save_edge_tts():
                log_display(f"Tentando Edge-TTS para: {clean_text[:30]}...")
                voz = self.config.get("VOICE", "pt-BR-AntonioNeural")
                com = edge_tts.Communicate(clean_text, voz)
                await com.save(temp_file_edge)
            asyncio.run(save_edge_tts())
            self._tocar_audio(temp_file_edge)
            return
        except Exception as e:
            log_display(f"Falha no edge-tts (Sem internet?): {e}")

        # Tentativa 3 (se disponível): Piper
        if self.installer and self.installer.verificar_piper():
            temp_file_piper = os.path.join(self.temp_audio_path, f"fala_piper_{random.randint(1000, 9999)}.wav")
            try:
                log_display(f"Tentando Piper TTS para: {clean_text[:30]}...")
                cmd = f'echo {clean_text} | "{self.installer.piper_exe}" --model "{self.installer.voice_model}" --output_file "{temp_file_piper}"'
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self._tocar_audio(temp_file_piper)
                return
            except Exception as e:
                log_display(f"Falha no Piper: {e}")

        # Tentativa 4: PYTTSX3 (Fallback Offline Legacy)
        try:
            log_display(f"Tentando pyttsx3 (fallback final) para: {clean_text[:30]}...")
            with self.audio_lock:
                engine = pyttsx3.init()
                engine.say(clean_text)
                engine.runAndWait()
                engine.stop()
        except Exception as e:
            log_display(f"Falha total no sistema de fala: {e}")

    def calar_boca(self):
        self.parar_fala = True
        try:
            with self.audio_lock:
                if pygame.mixer.get_init(): pygame.mixer.music.stop()
        except Exception as e:
            log_display(f"Falha ao parar pygame.mixer: {e}")

    def is_busy(self):
        """Retorna True se estiver reproduzindo áudio."""
        try:
            if pygame.mixer.get_init():
                return pygame.mixer.music.get_busy()
            return False
        except Exception:
            return False

    def play_feedback_sound(self, sound_type='start'):
        """Toca um som de feedback simples."""
        # Esta função pode ser expandida para ter diferentes sons
        # Por agora, vamos manter simples para evitar mais dependências
        pass