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
        self.mic_device_index = None  # Índice do microfone selecionado
        self._calibrated = False

    def on_load(self) -> bool:
        """Inicia o sistema de audição assim que o módulo carrega."""
        print("[AUDICAO] Iniciando sistema de audição...")
        self.listening = True
        # Inicia a thread de escuta em background
        threading.Thread(target=self._start_engine, daemon=True).start()
        print("[AUDICAO] Sistema de audição ativado.")
        return True

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
            print("[AUDICAO] Drivers de audio verificados com sucesso.")
            return True
        except ImportError as e:
            print(f"[AUDICAO] AVISO: driver de audio avancado faltando. Erro: {e}")
            self.drivers_ok = False
            return False
        except Exception as e:
            print(f"[AUDICAO] AVISO: Falha critica na DLL do PyTorch. (WinError 1114). {e}")
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
        
        # Detecta e seleciona o melhor microfone disponível
        try:
            mic_names = sr.Microphone.list_microphone_names()
            print(f"[AUDICAO] Microfones detectados: {mic_names}")
            
            # Tenta encontrar Headset ou Headphones como primeira opção
            self.mic_device_index = None
            for idx, name in enumerate(mic_names):
                name_lower = name.lower()
                # Prioridade: EDIFIER Headset > Qualquer Headset > Default
                if "edifier" in name_lower and "headset" in name_lower:
                    self.mic_device_index = idx
                    print(f"[AUDICAO] Microfone EDIFIER selecionado: {name} (índice {idx})")
                    break
                elif "headset" in name_lower:
                    self.mic_device_index = idx
                    print(f"[AUDICAO] Headset selecionado: {name} (índice {idx})")
                    # Não para aqui - continua procurando por EDIFIER
            
            if self.mic_device_index is None:
                print(f"[AUDICAO] Nenhum Headset encontrado. Usando mic padrão.")
                self.mic_device_index = None  # Deixa sr.Microphone() usar o padrão
        except Exception as e:
            print(f"[AUDICAO] Erro ao listar microfones: {e}")
            self.mic_device_index = None

        # Valor inicial; será recalibrado por ambient noise se possível (apenas uma vez)
        self.recognizer.energy_threshold = 300

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
        
        print(f"[AUDICAO] Iniciando loop de escuta (fallback={fallback})")
        
        # Faz calibração de ruido ambiente uma vez antes do loop principal
        try:
            with sr.Microphone(device_index=self.mic_device_index, sample_rate=16000) as source:
                try:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                    # Cap no energy_threshold para evitar valores absurdos
                    if self.recognizer.energy_threshold > 800:
                        self.recognizer.energy_threshold = 400
                    self._calibrated = True
                    print(f"[AUDICAO] energy_threshold calibrado para {self.recognizer.energy_threshold}")
                except Exception as e:
                    print(f"[AUDICAO] Nao foi possivel ajustar ruido ambiente: {e}")
        except Exception:
            # Falha ao abrir microfone para calibração; continuará sem calibrar
            pass

        while self.listening:
            try:
                # Usa o microfone selecionado, ou o padrão se None
                with sr.Microphone(device_index=self.mic_device_index, sample_rate=16000) as source:
                    # Não recalibrar a cada iteração para evitar flutuações constantes
                    try:
                        print("[AUDICAO] Aguardando áudio do microfone...")
                        audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=10)
                    except sr.WaitTimeoutError:
                        print("[AUDICAO] Timeout - sem áudio detectado")
                        continue 

                    if not self.listening: break

                    if gui: gui.set_status("PROCESSANDO...")
                    print("[AUDICAO] Áudio capturado, processando...")
                    
                    if not fallback and self.model is not None:
                        raw_data = audio.get_raw_data()
                        audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                        segments, _ = self.model.transcribe(
                            audio_np, language="pt", beam_size=5,
                            vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500)
                        )
                        texto_final = " ".join([s.text for s in segments]).strip()
                        print(f"[AUDICAO] Transcrito (Whisper): {texto_final}")
                        # update mic level from audio
                        try:
                            audio_np = audio_np if 'audio_np' in locals() else np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
                            rms = float(np.sqrt(np.mean(audio_np**2)))
                            level = min(1.0, rms * 10.0)
                            if gui and hasattr(gui, 'set_mic_level'):
                                gui.set_mic_level(level)
                        except Exception:
                            pass
                    else:
                        # Fallback para Google Speech Recognition (requer internet) — mais leve
                        try:
                            print("[AUDICAO] Usando Google Speech Recognition...")
                            texto_final = self.recognizer.recognize_google(audio, language="pt-BR")
                            print(f"[AUDICAO] Transcrito (Google): {texto_final}")
                        except sr.UnknownValueError:
                            print("[AUDICAO] Não consegui entender o áudio (UnknownValue)")
                            texto_final = ""
                        except sr.RequestError as e:
                            print(f"[AUDICAO] Erro na requisição (sem internet?): {e}")
                            texto_final = ""
                        except Exception as e:
                            print(f"[AUDICAO] Erro no reconhecimento fallback: {e}")
                            texto_final = ""

                    # Update mic visual level in GUI for fallback path as well
                    try:
                        raw = audio.get_raw_data()
                        audio_np2 = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                        rms2 = float(np.sqrt(np.mean(audio_np2**2)))
                        level2 = min(1.0, rms2 * 10.0)
                        if gui and hasattr(gui, 'set_mic_level'):
                            gui.set_mic_level(level2)
                    except Exception:
                        pass
                    
                    if texto_final:
                        print(f"[AUDICAO] Enviando para GUI: '{texto_final}'")
                        if gui: gui.logic_callback(texto_final)
                        
                        if any(x in texto_final.lower() for x in ["parar", "chega", "dormir"]):
                            self.listening = False
                    else:
                        print("[AUDICAO] Texto vazio após transcrição")
            except Exception as e:
                # Evita crashar se o microfone for desconectado, etc.
                print(f"[AUDICAO] Erro no loop de escuta: {e}")
                time.sleep(2)
        
        print("[AUDICAO] Loop de escuta finalizado")
        if gui: gui.set_status("ONLINE")