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
from kokoro_onnx import Kokoro

def log_display(msg):
    print(f"[IO_HANDLER] {msg}")

class IOHandler:
    """
    Gerencia áudio com proteção de threads e suporte a KOKORO (Local Neural).
    """
    def __init__(self, config: dict, installer=None):
        self.config = config if config else {}
        self.installer = installer
        self.parar_fala = False
        self.audio_lock = threading.Lock()
        self.kokoro = None
        
        # Caminhos
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.temp_audio_path = os.path.join(base_path, "bagagem", "temp")
        self.kokoro_path = os.path.join(base_path, "bagagem", "kokoro", "kokoro-v0_19.onnx")
        self.voices_path = os.path.join(base_path, "bagagem", "kokoro", "voices.json")
        
        os.makedirs(self.temp_audio_path, exist_ok=True)
        
        # Inicializa Pygame Mixer
        try: 
            pygame.mixer.init()
        except Exception as e: 
            log_display(f"Erro ao inicializar mixer: {e}")

        # Inicializa KOKORO (Carrega na memória RAM)
        if os.path.exists(self.kokoro_path) and os.path.exists(self.voices_path):
            try:
                log_display("Carregando modelo Neural KOKORO...")
                self.kokoro = Kokoro(self.kokoro_path, self.voices_path)
                log_display("KOKORO carregado e pronto.")
            except Exception as e:
                log_display(f"Erro ao carregar Kokoro: {e}")
        else:
            log_display("AVISO: Arquivos do Kokoro não encontrados em bagagem/kokoro. Usando fallback.")

    def _tocar_audio(self, arquivo: str):
        with self.audio_lock:
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                pygame.mixer.music.load(arquivo)
                pygame.mixer.music.play()
            except Exception as e:
                log_display(f"Erro playback: {e}")
                return

        while pygame.mixer.music.get_busy():
            if self.parar_fala:
                pygame.mixer.music.stop()
                break
            time.sleep(0.1)
        
        # Limpeza em background
        threading.Thread(target=self._limpar_seguro, args=(arquivo,), daemon=True).start()

    def _limpar_seguro(self, arquivo: str):
        try: pygame.mixer.music.unload()
        except: pass
        time.sleep(0.5)
        try:
            if os.path.exists(arquivo): os.remove(arquivo)
        except: pass

    def falar(self, texto: str):
        if not texto: return
        self.parar_fala = False
        
        if len(texto) > 1000: texto = texto[:1000] + "..." # Limite de segurança
        clean_text = re.sub(r'[*_#`]', '', texto).replace('\n', ' ').strip()
        if not clean_text: return

        # Arquivo temporário
        temp_file = os.path.join(self.temp_audio_path, f"fala_{random.randint(1000, 9999)}.wav")

        # TENTATIVA 1: KOKORO (Local, Alta Qualidade)
        if self.kokoro:
            try:
                # Vozes pt-br mapeadas geralmente usam fonemas específicos. 
                # 'af_sarah' ou 'bm_lewis' são boas bases, mas precisamos forçar lang="pt-br"
                samples, sample_rate = self.kokoro.create(
                    clean_text, 
                    voice="bm_lewis", # Voz masculina grave (tente af_sarah para feminina)
                    speed=1.0, 
                    lang="pt-br"
                )
                sf.write(temp_file, samples, sample_rate)
                self._tocar_audio(temp_file)
                return
            except Exception as e:
                log_display(f"Kokoro falhou: {e}. Tentando fallback...")

        # TENTATIVA 2: EDGE-TTS (Online)
        try:
            async def save_edge():
                voz = self.config.get("VOICE", "pt-BR-AntonioNeural")
                com = edge_tts.Communicate(clean_text, voz)
                await com.save(temp_file)
            asyncio.run(save_edge())
            self._tocar_audio(temp_file)
            return
        except: pass

        # TENTATIVA 3: PYTTSX3 (Robótico Offline)
        try:
            with self.audio_lock:
                engine = pyttsx3.init()
                engine.save_to_file(clean_text, temp_file)
                engine.runAndWait()
            self._tocar_audio(temp_file)
        except Exception as e:
            log_display(f"Tudo falhou: {e}")

    def play_feedback_sound(self, tipo):
        # Implemente sons curtos aqui (bip, click) se tiver arquivos
        pass

    def calar_boca(self):
        self.parar_fala = True
        try: pygame.mixer.music.stop()
        except: pass