import datetime

class StatusManager:
    """
    Gerencia o estado da aplicação: modo de operação, status dos backends (LEDs),
    e outras informações de estado.
    """
    def __init__(self):
        self.operation_mode = "DIRETO"  # DIRETO ou CHAMAR
        self.cloud_online = False
        self.local_online = False
        self.triggers = ["aeon", "aion", "iron", "filho", "assistente", "computador"]
        
        # Callbacks para atualização da UI
        self.on_mode_change = None
        self.on_status_change = None

    # --- Modo de Operação (DIRETO / CHAMAR) ---
    def toggle_mode(self):
        """Alterna entre DIRETO e CHAMAR."""
        self.operation_mode = "CHAMAR" if self.operation_mode == "DIRETO" else "DIRETO"
        if self.on_mode_change:
            self.on_mode_change(self.operation_mode)
        return self.operation_mode

    def set_mode(self, mode: str):
        """Define o modo manualmente."""
        if mode in ["DIRETO", "CHAMAR"]:
            self.operation_mode = mode
            if self.on_mode_change:
                self.on_mode_change(mode)
            return True
        return False

    def get_mode(self):
        """Retorna o modo atual."""
        return self.operation_mode

    def is_chamar_mode(self):
        """Verifica se está em modo CHAMAR (requer trigger)."""
        return self.operation_mode == "CHAMAR"

    # --- Status dos Backends (LEDs) ---
    def update_cloud_status(self, online: bool):
        """Atualiza o status do backend de nuvem (Groq)."""
        self.cloud_online = online
        if self.on_status_change:
            self.on_status_change()

    def update_local_status(self, online: bool):
        """Atualiza o status do backend local (Ollama)."""
        self.local_online = online
        if self.on_status_change:
            self.on_status_change()

    def get_status(self) -> dict:
        """Retorna o status atual como dicionário."""
        return {
            "cloud": self.cloud_online,
            "local": self.local_online,
            "mode": self.operation_mode
        }

    def get_led_status(self) -> dict:
        """Retorna o status dos LEDs para a UI."""
        has_cloud = self.cloud_online
        has_local = self.local_online
        
        return {
            "cloud": "on" if has_cloud else "off",
            "local": "on" if has_local else "off",
            "hybrid": "on" if (has_cloud and has_local) else "off"
        }

    # --- Triggers customizados ---
    def add_trigger(self, word: str):
        """Adiciona um novo gatilho."""
        if word.lower() not in self.triggers:
            self.triggers.append(word.lower())
            return True
        return False

    def remove_trigger(self, word: str):
        """Remove um gatilho."""
        if word.lower() in self.triggers:
            self.triggers.remove(word.lower())
            return True
        return False

    def has_trigger(self, text: str) -> bool:
        """Verifica se o texto contém algum trigger."""
        text_lower = text.lower()
        return any(t in text_lower for t in self.triggers)

    def get_triggers(self) -> list:
        """Retorna a lista de triggers."""
        return self.triggers.copy()
