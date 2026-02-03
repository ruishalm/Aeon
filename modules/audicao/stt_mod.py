import threading
import speech_recognition as sr
import numpy as np
import os
import time
from faster_whisper import WhisperModel
from modules.base_module import AeonModule

class STTModule(AeonModule):
    """
    Módulo de Audição Blindado (Versão Final).
    - Sem Picovoice (Wake Word por energia).
    - Faster-Whisper automático (Small/Int8).
    - Carregamento tardio para não travar o boot.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Audicao"
        # Palavras que ativam o sistema sem passar pelo Brain
        self.triggers = ["escuta", "escutar", "ativar", "parar", "dormir", "calibrar"]
        self.listening = False
        self.recognizer = None 
        self.model = None
        self.mic_source = None

    def process(self, command: str) -> str:
        cmd = command.lower()
        
        # 1. Comandos de Controle
        if "calibrar" in cmd:
            return "Calibrando sensibilidade do microfone... Fique em silêncio."

        if any(w in cmd for w in ["escuta", "ativar"]):
            if not self.listening:
                self.listening = True
                # Inicia em thread separada para não congelar a GUI
                threading.Thread(target=self._start_engine, daemon=True).start()
                return "Iniciando protocolos de audição..."
            return "Meus ouvidos já estão abertos."
        
        if "parar" in cmd or "dormir" in cmd:
            self.listening = False
            return "Audição encerrada."
            
        return None 

    def _start_engine(self):
        """Carrega o peso do Whisper só agora."""
        gui = self.core_context.get("gui")
        
        # Carrega SpeechRecognition se ainda não carregou
        if not self.recognizer:
            if gui: gui.add_message("Carregando drivers auditivos...", "SISTEMA")
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 1000 # Sensibilidade padrão
                self.recognizer.dynamic_energy_threshold = True
                
                # Carrega o Modelo Faster-Whisper
                # 'small' é o equilíbrio perfeito. Ele baixa sozinho se não tiver.
                print("[AUDIÇÃO] Carregando modelo Whisper 'small'...")
                self.model = WhisperModel("small", device="cpu", compute_type="int8")
                
                if gui: gui.add_message("Ouvido Biônico: ONLINE", "SISTEMA")
            except Exception as e:
                print(f"[AUDIÇÃO] Erro fatal no driver: {e}")
                if gui: gui.add_message(f"Falha de driver: {e}", "ERRO")
                self.listening = False
                return

        self._listen_loop()

    def _listen_loop(self):
        gui = self.core_context.get("gui")
        print("[AUDIÇÃO] Loop iniciado.")
        
        while self.listening:
            try:
                with sr.Microphone(sample_rate=16000) as source:
                    # Ajuste de ruído rápido (opcional, pode deixar lento se o ambiente for barulhento)
                    # self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    print("[AUDIÇÃO] Aguardando som...")
                    try:
                        # Ouve com timeout curto para checar se self.listening mudou
                        audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=10)
                    except sr.WaitTimeoutError:
                        continue # Ninguém falou, segue o loop

                    if not self.listening: break

                    if gui: gui.add_message("Processando áudio...", "STATUS")
                    
                    # --- Decodificação (Faster Whisper) ---
                    # 1. Converte bytes brutos para float32
                    raw_data = audio.get_raw_data()
                    audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # 2. Transcreve
                    segments, _ = self.model.transcribe(
                        audio_np, 
                        language="pt", 
                        beam_size=5,
                        vad_filter=True, # Filtra respiração e ventilador
                        vad_parameters=dict(min_silence_duration_ms=500)
                    )
                    
                    texto_final = " ".join([s.text for s in segments]).strip()
                    
                    if texto_final:
                        print(f"[VOCÊ]: {texto_final}")
                        if gui: gui.add_message(texto_final, "VOCÊ")
                        
                        # Comandos de Voz Imediatos
                        if any(x in texto_final.lower() for x in ["parar audição", "dormir", "desativar"]):
                            self.listening = False
                            if gui: gui.add_message("Dormindo.", "AEON")
                        else:
                            # Envia para o Cérebro processar
                            if gui: gui.process_in_background(texto_final)
            
            except Exception as e:
                print(f"[AUDIÇÃO] Erro no loop: {e}")
                time.sleep(1) # Espera um pouco antes de tentar de novo
        
        print("[AUDIÇÃO] Loop encerrado.")