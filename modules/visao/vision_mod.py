import cv2
import time
from modules.base_module import AeonModule
from typing import List, Dict

class VisionModule(AeonModule):
    """
    Módulo que permite ao Aeon 'ver' através da webcam.
    Captura imagens e envia para o cérebro processar.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Visão"
        self.triggers = [
            "o que você está vendo", "descreva esta imagem", "o que é isso",
            "analisar ambiente", "ligar câmera", "ativar visão"
        ]

    @property
    def dependencies(self) -> List[str]:
        return ["brain"]

    @property
    def metadata(self) -> Dict[str, str]:
        return {
            "version": "1.0.0",
            "description": "Captura imagens da webcam e descreve o conteúdo."
        }

    def on_load(self) -> bool:
        # DESATIVADO: Conflito com visao_mod.py (Unificado)
        return False