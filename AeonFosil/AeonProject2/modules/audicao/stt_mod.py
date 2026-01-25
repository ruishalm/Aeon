import threading
import speech_recognition as sr
from modules.base_module import AeonModule

class STTModule(AeonModule):
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Audicao"
        self.triggers = ["ativar escuta", "ouvir", "parar escuta"]
        self.dependencies = ["gui", "io_handler"]
        
        self.recognizer = sr.Recognizer()
        self.listening = False
        self.thread = None

    def process(self, command: str) -> str:
        if "ativar" in command or "ouvir" in command:
            if not self.listening:
                self.listening = True
                self.thread = threading.Thread(target=self._listen_loop, daemon=True)
                self.thread.start()
                return "aeon iniciado"
            return "Já estou ouvindo."
        
        if "parar" in command:
            self.listening = False
            return "Microfone desativado."
        
        return ""

    def _listen_loop(self):
        """Loop infinito que ouve, transcreve e injeta no sistema."""
        gui = self.core_context.get("gui")
        
        with sr.Microphone() as source:
            # Calibragem rápida de ruído (Apenas visual)
            if gui: gui.after(0, lambda: gui.add_message("Calibrando ruído...", "AUDIÇÃO"))
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            if gui: gui.after(0, lambda: gui.add_message("Escuta Ativa. Fale algo...", "AUDIÇÃO"))
            
            while self.listening:
                try:
                    # Ouve (bloqueante com timeout para não travar a thread para sempre)
                    print("[AUDIÇÃO] Ouvindo...")
                    # timeout=None significa que espera indefinidamente por uma fala
                    # phrase_time_limit=10 corta se a pessoa falar por mais de 10s
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=10)
                    
                    # Transcreve
                    print("[AUDIÇÃO] Processando áudio...")
                    texto = self.recognizer.recognize_google(audio, language="pt-BR")
                    
                    if texto:
                        print(f"[AUDIÇÃO] Ouvi: {texto}")
                        
                        if gui:
                            # 1. Mostra o que você falou no chat (Visual)
                            gui.after(0, lambda t=texto: gui.add_message(t, "VOCÊ"))
                            
                            # 2. Manda processar direto (Lógico) - Sem depender do botão enviar
                            # Injeta diretamente no fluxo de comando do Main
                            gui.process_in_background(texto)
                            
                except sr.WaitTimeoutError:
                    pass # Silêncio, continua ouvindo
                except sr.UnknownValueError:
                    pass # Ruído não identificado, ignora
                except Exception as e:
                    print(f"[AUDIÇÃO] Erro: {e}")
                    self.listening = False # Para em caso de erro crítico (ex: mic desconectado)