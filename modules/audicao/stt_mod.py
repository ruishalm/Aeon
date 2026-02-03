import threading
import speech_recognition as sr
import numpy as np
import time
from modules.base_module import AeonModule

# NENHUMA importação pesada aqui para garantir o boot rápido.

class STTModule(AeonModule):
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Audicao"
        self.triggers = ["escuta", "escutar", "ativar", "parar", "dormir"]
        self.listening = False
        self.recognizer = None 
        self.model = None
        # None = não verificado, True = advanced engine disponível, False = não disponível
        self.drivers_ok = None

    def process(self, command: str) -> str:
        cmd = command.lower()
        
        if "calibrar" in cmd:
            return "Calibrando microfone..."

        # Usa as triggers configuradas para decidir ativação (mantém "parar"/"dormir" separadas)
        activate_keywords = [k for k in self.triggers if k not in ("parar", "dormir")]
        if any(w in cmd for w in activate_keywords):
            if not self.listening:
                self.listening = True
                # A verificação de drivers e o carregamento do modelo ocorrerão na thread
                threading.Thread(target=self._start_engine, daemon=True).start()
                return "Ouvidos abertos. (Inicializando sistema de áudio...)"
            return "Já estou ouvindo."
        
        if "parar" in cmd or "dormir" in cmd:
            self.listening = False
            return "Audição pausada."
            
        return None 

    def _check_drivers(self):
        """Verifica os drivers de áudio pesados apenas uma vez."""
        if self.drivers_ok is not None:
            return self.drivers_ok

        try:
            # --- IMPORTS PESADOS AQUI ---
            import torch
            from faster_whisper import WhisperModel
            # --------------------------
            self.drivers_ok = True
            print("[AUDICAO] Drivers de áudio verificados com sucesso.")
            return True
        except ImportError as e:
            print(f"[AUDICAO] ⚠️ AVISO: driver de áudio avançado faltando. Erro: {e}")
            self.drivers_ok = False
            return False
        except Exception as e:
            print(f"[AUDICAO] ⚠️ AVISO: Falha crítica na DLL do PyTorch. (WinError 1114). {e}")
            self.drivers_ok = False
            return False

    def _start_engine(self):
        gui = self.core_context.get("gui")

        # 1. Verifica os drivers (importações pesadas) de forma segura
        advanced = self._check_drivers()
        if not advanced and gui:
            gui.add_message("Driver de áudio avançado indisponível — usando fallback SpeechRecognition.", "AVISO")

        # 2. Se os drivers estiverem OK, carrega o modelo
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 1000

        if advanced:
            try:
                if gui: gui.add_message("Carregando Whisper AI...", "SISTEMA")
                from faster_whisper import WhisperModel
                self.model = WhisperModel("small", device="cpu", compute_type="int8")
                if gui: gui.add_message("Audição Neural: ONLINE", "SISTEMA")
                # Inicia loop com modelo avançado
                self._listen_loop(fallback=False)
                return
            except Exception as e:
                print(f"[AUDIÇÃO] Erro ao carregar modelo avançado: {e}")
                if gui: gui.add_message("Falha ao carregar modelo avançado — usando fallback.", "ERRO")

        # Se chegou até aqui, usa fallback baseado em SpeechRecognition (Google/Sphinx)
        self._listen_loop(fallback=True)

    def _listen_loop(self, fallback=False):
        gui = self.core_context.get("gui")
        if gui: gui.set_status("OUVINDO...")
        
        while self.listening:
            try:
                with sr.Microphone(sample_rate=16000) as source:
                    try:
                        audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=10)
                    except sr.WaitTimeoutError:
                        continue 

                    if not self.listening: break

                    if gui: gui.set_status("PROCESSANDO...")
                    
                    if not fallback and self.model is not None:
                        raw_data = audio.get_raw_data()
                        audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                        segments, _ = self.model.transcribe(
                            audio_np, language="pt", beam_size=5,
                            vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500)
                        )
                        texto_final = " ".join([s.text for s in segments]).strip()
                    else:
                        # Fallback para Google Speech Recognition (requer internet) — mais leve
                        try:
                            texto_final = self.recognizer.recognize_google(audio, language="pt-BR")
                        except sr.UnknownValueError:
                            texto_final = ""
                        except Exception as e:
                            print(f"[AUDIÇÃO] Erro no reconhecimento fallback: {e}")
                            texto_final = ""
                    
                    if texto_final:
                        if gui: gui.logic_callback(texto_final)
                        
                        if any(x in texto_final.lower() for x in ["parar", "chega", "dormir"]):
                            self.listening = False
            except Exception as e:
                # Evita crashar se o microfone for desconectado, etc.
                print(f"[AUDIÇÃO] Erro no loop de escuta: {e}")
                time.sleep(2)
        
        if gui: gui.set_status("ONLINE")