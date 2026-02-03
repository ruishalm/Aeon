# SAFE IMPORT V86
try:
    import cv2
    GEAR_AVAILABLE = True
except ImportError:
    GEAR_AVAILABLE = False

try:
    import pyautogui
    VISAO_AVAILABLE = True
except ImportError:
    VISAO_AVAILABLE = False

from io import BytesIO
from modules.base_module import AeonModule

class VisaoModule(AeonModule):
    """
    Módulo de Visão para análise de imagens.
    - Analisa screenshots da tela.
    - Captura e analisa imagens da webcam.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Visao"
        self.triggers = [
            "veja isso", "leia a tela", "analise a imagem",
            "o que você está vendo", "descreva a câmera", "olhe para mim"
        ]
        self.dependencies = ["brain", "context"]

    def check_dependencies(self):
        if not VISAO_AVAILABLE:
            print("[VISAO] Aviso: 'pyautogui' não instalado. Funções de screenshot desativadas.")
        if not GEAR_AVAILABLE:
            print("[VISAO] Aviso: 'opencv-python' não instalado. Funções de câmera desativadas.")
        return super().check_dependencies()

    def process(self, command: str) -> str:
        cmd = command.lower()

        # Verifica se o comando é para este módulo
        analysis_triggers = ["veja isso", "leia a tela", "analise a imagem", "o que você está vendo", "descreva a câmera", "olhe para mim"]
        if not any(c in cmd for c in analysis_triggers):
            return ""

        brain = self.core_context.get("brain")
        ctx = self.core_context.get("context")
        if not brain:
            return "O cérebro não está disponível para analisar a imagem."

        # Decide se é para usar a Câmera ou a Tela
        use_camera = any(x in cmd for x in ["câmera", "vendo", "olhe", "mim"])

        try:
            if use_camera:
                if not GEAR_AVAILABLE:
                    return "Não consigo acessar a câmera. Instale 'opencv-python'."
                image_bytes = self._capture_webcam_frame()
            else:
                if not VISAO_AVAILABLE:
                    return "Não consigo ler a tela. Instale 'pyautogui'."
                screenshot = pyautogui.screenshot()
                img_byte_arr = BytesIO()
                screenshot.save(img_byte_arr, format='PNG')
                image_bytes = img_byte_arr.getvalue()
            
            analise = brain.ver(image_bytes)
            if ctx:
                ctx.set("vision_last_result", analise, ttl=600)
            
            return f"Visão: {analise}"
        except Exception as e:
            return f"Ocorreu um erro durante a análise visual: {e}"

    def _capture_webcam_frame(self) -> bytes:
        """Captura um único frame da webcam e retorna em bytes JPEG."""
        # Tenta abrir a câmera. Pode ser necessário ajustar o índice (0, 1, etc.)
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
             cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise Exception("Não consegui acessar a câmera. Verifique se ela não está em uso.")
        
        # Dá tempo para a câmera ajustar o brilho/foco
        for _ in range(5):
            cap.read()
            
        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise Exception("Falha ao capturar a imagem da câmera.")
        
        # Codifica a imagem para JPEG para transmissão
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            raise Exception("Erro ao codificar a imagem capturada.")
        
        return buffer.tobytes()

    def on_unload(self) -> bool:
        # Nada especial para descarregar neste módulo simplificado
        return True