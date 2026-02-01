import threading
import os
import tempfile
import struct
import pyaudio
import pvporcupine
import numpy as np
import speech_recognition as sr
from faster_whisper import WhisperModel
from modules.base_module import AeonModule
import time

class STTModule(AeonModule):
    """
    Módulo de Audição responsável por Speech-to-Text (STT).
    Usa Porcupine para detecção de wake word e Faster-Whisper para transcrição local de comandos.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Audicao"
        self.triggers = ["escuta", "escutar", "parar escuta", "dormir", "acordar", "acorde"]
        self.dependencies = ["gui", "io_handler", "context"]
        
        self.listening = False
        self.thread = None
        self.is_awake = False
        self.last_interaction_time = 0
        self.sleep_timeout = 120  # 2 minutos
        
        # --- Configuração das Chaves ---
        self.picovoice_key = os.getenv("PICOVOICE_ACCESS_KEY")

        # --- Configuração dos Motores de Áudio ---
        self.porcupine = None
        self.pa = None
        self.audio_stream = None
        self.recognizer = sr.Recognizer()
        self.whisper_model = None

    def on_load(self) -> bool:
        # installer = self.core_context.get("installer")
        # if installer:
        #     installer.check_pyaudio()
        
        # O modelo Whisper será carregado sob demanda (lazy-loading)
        return True

    def process(self, command: str) -> str:
        if any(w in command for w in ["escuta", "escutar", "ativar"]):
            if not self.listening:
                self.listening = True
                self.thread = threading.Thread(target=self._listen_loop, daemon=True)
                self.thread.start()
                return "Microfone ativado. Aguardando palavra de ativação..."
            return "Já estou em modo de escuta."
        
        if "parar" in command:
            self.stop()
            return "Microfone desativado."
        
        if "dormir" in command:
            self.go_to_sleep()
            return "Ok, dormindo."
        
        if command in ["acordar", "acorde"]:
            self.is_awake = True
            return "Estou ouvindo."
        
        return ""

    def stop(self):
        """Para a thread de escuta e libera os recursos."""
        print("[AUDIÇÃO] Recebido comando para parar.")
        self.listening = False
        self.is_awake = False

    def go_to_sleep(self):
        """Força o módulo a voltar para o modo de escuta passiva (dormir)."""
        if self.is_awake:
            print("[AUDIÇÃO] Voltando para o modo de escuta passiva (dormindo).")
            self.is_awake = False
            self.core_context.get("io_handler").play_feedback_sound('stop')
            gui = self.core_context.get("gui")
            if gui:
                gui.after(0, lambda: gui.add_message("Aguardando ativação...", "AUDIÇÃO"))

    def _initialize_porcupine(self):
        """Inicializa o Porcupine e o stream de áudio."""
        if not self.picovoice_key:
            print("[AUDIÇÃO][ERRO] PICOVOICE_ACCESS_KEY não configurada no .env!")
            return False
        try:
            # Lista de palavras-chave disponíveis
            available_keywords = list(pvporcupine.KEYWORD_PATHS.keys())
            # Palavra de ativação principal. A pronúncia é em INGLÊS.
            # Outras opções gratuitas: 'alexa', 'jarvis', 'porcupine', 'bumblebee', etc.
            aeon_keywords = ['computer']
            
            keyword_paths = [pvporcupine.KEYWORD_PATHS[x] for x in aeon_keywords]

            self.porcupine = pvporcupine.create(
                access_key=self.picovoice_key,
                keyword_paths=keyword_paths
            )
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            print(f"[AUDIÇÃO] Porcupine inicializado com as palavras: {aeon_keywords}")
            return True
        except Exception as e:
            print(f"[AUDIÇÃO][ERRO] Falha ao iniciar Porcupine: {e}")
            if "keyword_path" in str(e).lower():
                print("  └> Causa provável: Palavra-chave não encontrada. Disponíveis: ", available_keywords)
            return False

    def _release_resources(self):
        """Libera os recursos do Porcupine e PyAudio."""
        if self.audio_stream is not None:
            self.audio_stream.close()
            self.audio_stream = None
        if self.porcupine is not None:
            self.porcupine.delete()
            self.porcupine = None
        if self.pa is not None:
            self.pa.terminate()
            self.pa = None
        print("[AUDIÇÃO] Recursos de áudio liberados.")

    def _initialize_whisper(self):
        """Inicializa o modelo Whisper sob demanda."""
        if self.whisper_model:
            return True
        try:
            bagagem_path = "bagagem"
            model_path = os.path.join(bagagem_path, "models", "systran-whisper-base")
            print(f"[AUDIÇÃO] Carregando modelo Whisper pela primeira vez: {model_path}")
            if not os.path.exists(model_path):
                print(f"[AUDIÇÃO][ERRO] Caminho do modelo Whisper não encontrado: {model_path}")
                self.core_context.get("io_handler").falar("Atenção: o modelo de reconhecimento de fala não foi encontrado.")
                return False
            self.whisper_model = WhisperModel(model_path, device="cpu", compute_type="int8")
            print("[AUDIÇÃO] Modelo Whisper carregado com sucesso.")
            return True
        except Exception as e:
            print(f"[AUDIÇÃO][ERRO] Falha crítica ao carregar o modelo Whisper: {e}")
            self.core_context.get("io_handler").falar("Erro crítico ao carregar o modelo de reconhecimento de fala.")
            return False

    def _listen_loop(self):
        print("[AUDIÇÃO] Thread de escuta iniciada.")
        gui = self.core_context.get("gui")
        context = self.core_context.get("context")

        if not self._initialize_porcupine():
            gui.after(0, lambda: gui.add_message("ERRO: Falha no Porcupine.", "AUDIÇÃO"))
            return

        try:
            context.set("mic_active", True)
            if gui: gui.after(0, lambda: gui.add_message("Aguardando ativação...", "AUDIÇÃO"))

            while self.listening:
                if not self.is_awake:
                    # --- MODO PASSIVO: OUVINDO COM PORCUPINE ---
                    pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                    
                    keyword_index = self.porcupine.process(pcm)
                    if keyword_index >= 0:
                        print("[AUDIÇÃO] Wake word detectado!")
                        self.is_awake = True
                        self.last_interaction_time = time.time() # Inicia o timer de atividade
                        if context: context.set('aeon_state', 'OUVINDO')
                        self.core_context.get("io_handler").play_feedback_sound('start')
                        if gui:
                            if hasattr(gui, 'wake_up'): gui.after(0, gui.wake_up)
                            gui.after(0, lambda: gui.add_message("Ouvindo...", "AEON"))
                
                else:
                    # --- MODO ATIVO: OUVINDO O COMANDO COM WHISPER LOCAL ---

                    # Inicializa o Whisper na primeira vez que for necessário
                    if self.whisper_model is None:
                        if not self._initialize_whisper():
                            # Se falhar, avisa e volta a dormir para não quebrar o loop
                            self.go_to_sleep()
                            continue
                    
                    # Verifica inatividade
                    if time.time() - self.last_interaction_time > self.sleep_timeout:
                        print(f"[AUDIÇÃO] Inatividade por {self.sleep_timeout}s. Voltando a dormir.")
                        self.go_to_sleep()
                        continue # Volta para o modo passivo

                    try:
                        print("[AUDIÇÃO] Modo ativo: escutando comando (5s timeout)...")
                        with sr.Microphone(sample_rate=16000) as source:
                            self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                            audio_data = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

                        if gui: context.set('aeon_state', 'PROCESSANDO')
                        print("[AUDIÇÃO] Transcrevendo áudio localmente...")
                        self.last_interaction_time = time.time() # Reseta o timer ao detectar som

                        raw_data = audio_data.get_raw_data()
                        audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

                        segments, info = self.whisper_model.transcribe(audio_np, beam_size=5, language="pt")
                        texto_comando = "".join(segment.text for segment in segments).strip()
                        
                        if texto_comando:
                            print(f"[AUDIÇÃO] Você disse: {texto_comando}")
                            if gui: gui.after(0, lambda t=texto_comando: gui.add_message(t, "VOCÊ"))

                            # Comandos para dormir anulam o timer e forçam o sono
                            if texto_comando.lower().strip() in ["dormir", "silêncio", "cancelar", "já chega", "pode dormir"]:
                                self.go_to_sleep()
                                continue

                            # Processa o comando e reseta o timer de inatividade
                            self.last_interaction_time = time.time()
                            if gui: gui.process_in_background(texto_comando)
                        else:
                            print("[AUDIÇÃO] Nenhum texto transcrito, continuando a ouvir.")
                                
                    except sr.WaitTimeoutError:
                        # Silêncio não é um erro, apenas continua no loop. O timer de inatividade geral cuidará disso.
                        print("[AUDIÇÃO] Silêncio detectado, aguardando próximo comando...")
                    except Exception as e:
                        print(f"[AUDIÇÃO] Erro no modo ativo: {e}")
                        # Em caso de erro, talvez seja prudente voltar a dormir
                        self.go_to_sleep()

        except Exception as e:
            print(f"[AUDIÇÃO] ERRO CRÍTICO NO LOOP: {e}")
            if gui: gui.after(0, lambda: gui.add_message("ERRO: Microfone inacessível.", "AUDIÇÃO"))
        finally:
            self._release_resources()
            if context: context.set("mic_active", False)
            self.listening = False
            self.is_awake = False
            print("[AUDIÇÃO] Thread de escuta finalizada.")

