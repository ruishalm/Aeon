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
        # Define o piso da sensibilidade em 300, mas mantém o ajuste dinâmico ativo
        self.recognizer.energy_threshold = 300 
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_ratio = 1.5
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
            self.stop()
            return "Microfone desativado."
        
        return ""

    def stop(self):
        """Para o loop de escuta."""
        self.listening = False

    def _listen_loop(self):
        """Loop infinito que ouve, transcreve e injeta no sistema."""
        gui = self.core_context.get("gui")
        context = self.core_context.get("context")
        
        with sr.Microphone() as source:
            # Calibragem rápida de ruído (Apenas visual)
            if gui: gui.after(0, lambda: gui.add_message("Calibrando ruído...", "AUDIÇÃO"))
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            if gui: gui.after(0, lambda: gui.add_message("Escuta Ativa. Fale algo...", "AUDIÇÃO"))
            if context: context.set("mic_active", True)
            
            while self.listening:
                try:
                    # Garante que, mesmo com ajuste dinâmico, o filtro nunca caia abaixo de 300
                    if self.recognizer.energy_threshold < 300:
                        self.recognizer.energy_threshold = 300

                    # Ouve (bloqueante com timeout para não travar a thread para sempre)
                    print("[AUDIÇÃO] Ouvindo...")
                    # timeout=2 significa que espera por fala, mas desiste após 2s de silêncio
                    # para permitir que a thread verifique a flag self.listening
                    audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=10)
                    
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