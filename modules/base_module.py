import abc

class AeonModule:
    """
    Classe Base para todos os módulos do AEON.
    Restaurada para permitir funcionalidades completas sem travar o boot.
    """
    def __init__(self, core_context):
        self.core_context = core_context
        self.config = core_context.get('config_manager')
        self.io = core_context.get('io_handler')
        self.brain = core_context.get('brain')
        self.gui = core_context.get('gui')
        
        self.name = "BaseModule"
        self.triggers = [] # Lista de comandos que ativam este módulo

    def process(self, command: str) -> str:
        """
        Método padrão. Se o módulo filho não sobrescrever, 
        ele apenas retorna None em vez de crashar o sistema.
        """
        return None

    # --- Métodos Utilitários (Helpers) para os Módulos ---
    
    def log(self, message, type="INFO"):
        """Envia log para o terminal formatado"""
        print(f"[{self.name.upper()}] {message}")

    def send_gui(self, message, sender=None):
        """Atalho para mandar mensagem na bolha azul"""
        if self.gui:
            author = sender if sender else self.name.upper()
            self.gui.add_message(message, author)

    def speak(self, text):
        """Atalho para falar"""
        if self.io:
            self.io.falar(text)