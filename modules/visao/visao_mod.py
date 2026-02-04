import os
import threading
from modules.base_module import AeonModule

# NOTA: Nao importamos cv2 ou mediapipe aqui para nao travar o boot!

class VisaoModule(AeonModule):
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Visao"
        self.triggers = ["ativar visao", "ativar visao", "olhos", "ver", "o que voce ve"]
        self.cap = None
        self.running = False
        self.thread = None

    def process(self, command: str) -> str:
        if any(t in command.lower() for t in ["ativar", "ligar", "iniciar"]):
            if self.running:
                return "O sistema visual ja esta online."
            
            # Inicia em thread para nao travar enquanto carrega o TensorFlow
            self.running = True
            threading.Thread(target=self._iniciar_sistema_visual, daemon=True).start()
            return "Inicializando cortex visual... (Isso pode levar alguns segundos)"
        
        if any(t in command.lower() for t in ["parar", "desligar", "fechar"]):
            self.running = False
            return "Sistema visual encerrado."

        return None

    def _iniciar_sistema_visual(self):
        gui = self.core_context.get("gui")
        if gui: gui.add_message("Carregando bibliotecas de visao...", "SISTEMA")

        try:
            # --- IMPORTS PESADOS AQUI DENTRO ---
            # Isso garante que o boot do Aeon seja instantaneo
            import cv2
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            # -----------------------------------

            if gui: gui.add_message("Bibliotecas carregadas. Abrindo camera...", "SISTEMA")

            base_options = python.BaseOptions(model_asset_path='modules/visao/hand_landmarker.task')
            options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=2)
            detector = vision.HandLandmarker.create_from_options(options)

            self.cap = cv2.VideoCapture(0)
            
            while self.running and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret: break

                # Aqui iria a logica de desenho na tela (simplifiquei para focar no boot)
                # O importante e que o CV2 agora vive aqui dentro
                cv2.imshow('Visao Aeon (Q para Sair)', frame)
                
                if cv2.waitKey(5) & 0xFF == 27: # ESC
                    self.running = False

            self.cap.release()
            cv2.destroyAllWindows()
            if gui: gui.add_message("Camera fechada.", "SISTEMA")

        except Exception as e:
            print(f"[VISAO] Erro: {e}")
            if gui: gui.add_message(f"Erro ao iniciar visao: {e}", "ERRO")
            self.running = False