import os
import psutil
import pygetwindow as gw
import pyautogui
import shutil
import subprocess
import webbrowser
from typing import List, Dict
from modules.base_module import AeonModule

class SistemaModule(AeonModule):
    """
    Módulo para interagir com o sistema operacional:
    - Controle de janelas
    - Status do sistema (CPU/RAM)
    - Abrir aplicativos indexados
    - Gerenciamento de arquivos (criar/deletar pastas)
    - Controle de rolagem
    - Abrir e-mail
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Sistema"
        self.triggers = [
            "minimize", "minimizar", "maximize", "maximizar", "restaurar", "restore",
            "feche", "fechar", "close", "alterne para", "foco em", "janela",
            "status do sistema", "uso de cpu", "desempenho do pc",
            "abre", "iniciar", "role para", "scroll",
            "crie uma pasta", "delete", "apague", "exclua",
            "email", "sair", "desliga", "instalar pacote",
            "bateria", "nível de bateria", "desligar computador", "reiniciar computador",
            "volume máximo", "volume mudo"
        ]
        self.pending_action = None
        self.indexed_apps = {}

    @property
    def dependencies(self) -> List[str]:
        """Sistema não depende de nenhum componente externo."""
        return []

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do módulo."""
        return {
            "version": "2.0.0",
            "author": "Aeon Core",
            "description": "Controla janelas, aplicativos e gerencia arquivos do sistema"
        }

    def on_load(self) -> bool:
        # DESATIVADO: Conflito com sys_mod.py (Unificado)
        return False