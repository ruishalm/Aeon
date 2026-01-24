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

def log_display(msg):
    print(f"[IO_HANDLER] {msg}")

class IOHandler:
    """
    Gerencia áudio com proteção de threads (Lock).
    """
    def __init__(self, config: dict, installer=None):
        self.config = config if config else {}
        self.installer = installer
        self.parar_fala = False
        self.audio_lock = threading.Lock() # <--- A PROTEÇÃO V80
        
        # CORREÇÃO: Usa abspath para garantir que a pasta bagagem seja a real, não uma fantasma
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.temp_audio_path = os.path.join(base_path, "bagagem", "temp")
        os.makedirs(self.temp_audio_path, exist_ok=True)
        
        try: pygame.mixer.init()
        except Exception as e: log_display(f"Erro ao inicializar pygame.mixer: {e}")

    def _tocar_audio(self, arquivo: str):
        with self.audio_lock: # Só um por vez
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                pygame.mixer.music.load(arquivo)
                pygame.mixer.music.play()
            except Exception as e:
                log_display(f"Erro audio: {e}")
                return

        while pygame.mixer.music.get_busy():
            if self.parar_fala:
                pygame.mixer.music.stop()
                break
            time.sleep(0.1)
        
        threading.Thread(target=self._limpar_seguro, args=(arquivo,), daemon=True).start()

    def _limpar_seguro(self, arquivo: str):
        # Solta o arquivo do mixer para o Windows permitir deletar
        try:
            pygame.mixer.music.unload()
        except: pass
        
        time.sleep(0.5) # Margem de segurança
        try:
            if os.path.exists(arquivo): os.remove(arquivo)
        except Exception as e:
            log_display(f"Erro ao limpar arquivo de áudio temporário: {e}")
            log_display(f"Falha ao parar pygame.mixer: {e}")

    def falar(self, texto: str):
        if not texto: return
        self.parar_fala = False
        
        # Aumentado limite para permitir explicações mais completas
        if len(texto) > 1000:
            texto = texto.split('\n')[0]

        clean_text = re.sub(r'[*_#`]', '', texto).replace('\n', ' ').strip()
        
        # Se o texto limpo for vazio (ex: primeira linha era só markdown), não faz nada.
        if not clean_text:
            return
            
        temp_file = os.path.join(self.temp_audio_path, f"fala_{random.randint(1000, 9999)}.mp3")

        try:
            async def save_edge_tts():
                log_display(f"Tentando Edge-TTS para: {clean_text[:30]}...")
                voz = self.config.get("VOICE", "pt-BR-AntonioNeural")
                com = edge_tts.Communicate(clean_text, voz)
                await com.save(temp_file)
            asyncio.run(save_edge_tts())
            self._tocar_audio(temp_file)
            return
        except Exception as e:
            log_display(f"Falha no edge-tts (Sem internet?): {e}")

        if self.installer and self.installer.verificar_piper():
            try:
                cmd = f'echo {clean_text} | "{self.installer.piper_exe}" --model "{self.installer.voice_model}" --output_file "{temp_file}"'
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self._tocar_audio(temp_file)
                return
            except Exception as e:
                log_display(f"Falha no Piper: {e}")

        try:
            with self.audio_lock:
                engine = pyttsx3.init()
                engine.say(clean_text)
                engine.runAndWait()
                engine.stop()
        except Exception as e:
            log_display(f"Falha no pyttsx3: {e}")

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
            return pygame.mixer.music.get_busy()
        except:
            return False