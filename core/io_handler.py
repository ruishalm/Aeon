import os
import re
import asyncio
import random
import threading
import time
import pygame
import edge_tts
import pyttsx3
import soundfile as sf

# --- REMOVI O IMPORT DO TOPO PARA NÃO TRAVAR SE FALTAR DLL ---
# from kokoro_onnx import Kokoro 

def log_display(msg):
    print(f"[IO_HANDLER] {msg}")

class IOHandler:
    """
    Gerencia áudio com proteção contra falhas de DLL e Threads.
    """
    def __init__(self, config: dict, installer=None):
        self.config = config if config else {}
        self.installer = installer
        self.parar_fala = False
        self.audio_lock = threading.Lock()
        
        # Atributos para lazy loading
        self.kokoro = None
        self.kokoro_loaded = False
        self.kokoro_failed = False

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
            log_display(f"Erro mixer: {e}")

    def _lazy_load_kokoro(self):
        """Carrega o motor Kokoro apenas quando chamado pela primeira vez."""
        if self.kokoro_loaded or self.kokoro_failed:
            return

        if os.path.exists(self.kokoro_path):
            try:
                log_display("Tentando carregar motor neural (Kokoro) - Lazy Load...")
                from kokoro_onnx import Kokoro 
                self.kokoro = Kokoro(self.kokoro_path, self.voices_path)
                self.kokoro_loaded = True
                log_display("[OK] Kokoro carregado com sucesso.")
            except ImportError as e:
                log_display(f"[AVISO] Falha de DLL no Kokoro. Usando fallback. (Erro: {e})")
                self.kokoro_failed = True
            except Exception as e:
                log_display(f"[AVISO] Erro ao iniciar Kokoro: {e}")
                self.kokoro_failed = True
        else:
            log_display("Arquivo do Kokoro não encontrado. Usando fallback.")
            self.kokoro_failed = True

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

        # Espera tocar sem travar a thread principal
        while pygame.mixer.music.get_busy():
            if self.parar_fala:
                pygame.mixer.music.stop()
                break
            time.sleep(0.1)
        
        # Limpa arquivo depois
        threading.Thread(target=self._limpar_seguro, args=(arquivo,), daemon=True).start()

    def _limpar_seguro(self, arquivo: str):
        try: 
            pygame.mixer.music.unload() 
        except: pass
        time.sleep(0.5)
        try:
            if os.path.exists(arquivo): os.remove(arquivo)
        except: pass

    def falar(self, texto: str):
        """Inicia a geração e reprodução da fala em uma nova thread."""
        if not texto: return
        
        # Roda o processo de fala em background para não travar
        thread_fala = threading.Thread(target=self._falar_worker, args=(texto,), daemon=True)
        thread_fala.start()

    def _falar_worker(self, texto: str):
        """Lógica de geração de áudio que roda em background."""
        self.parar_fala = False
        
        clean_text = re.sub(r'[*_#`]', '', texto).strip()
        if len(clean_text) > 800: clean_text = clean_text[:800] + "..."
        if not clean_text: return

        temp_file = os.path.join(self.temp_audio_path, f"fala_{random.randint(1000, 9999)}.wav")

        # Garante que o Kokoro seja carregado antes de usar
        self._lazy_load_kokoro()

        # 1. Tenta KOKORO
        if self.kokoro:
            try:
                samples, sample_rate = self.kokoro.create(
                    clean_text, 
                    voice="bm_lewis", 
                    speed=1.0, 
                    lang="pt-br"
                )
                sf.write(temp_file, samples, sample_rate)
                self._tocar_audio(temp_file)
                return
            except Exception as e:
                log_display(f"Erro ao gerar fala Kokoro: {e}")

        # 2. Fallback EDGE-TTS (Se Kokoro falhar ou não existir)
        try:
            # edge-tts precisa de um loop de evento asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def save_edge():
                com = edge_tts.Communicate(clean_text, "pt-BR-AntonioNeural")
                await com.save(temp_file)
            
            loop.run_until_complete(save_edge())
            loop.close()

            self._tocar_audio(temp_file)
            return
        except Exception as e:
            log_display(f"Erro no Edge-TTS: {e}")

        # 3. Fallback PYTTSX3 (Último recurso)
        try:
            engine = pyttsx3.init()
            engine.save_to_file(clean_text, temp_file)
            engine.runAndWait()
            self._tocar_audio(temp_file)
        except Exception as e: 
            log_display(f"Todos os métodos de fala falharam. Erro final: {e}")

    def play_feedback_sound(self, tipo):
        pass

    def calar_boca(self):
        self.parar_fala = True
        try: pygame.mixer.music.stop()
        except: pass