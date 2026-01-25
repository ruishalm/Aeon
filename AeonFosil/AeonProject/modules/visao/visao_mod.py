from io import BytesIO
from modules.base_module import AeonModule

# SAFE IMPORT V80
try:
    import pyautogui
    VISAO_AVAILABLE = True
except ImportError:
    VISAO_AVAILABLE = False

class VisaoModule(AeonModule):
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Visao"
        self.triggers = ["veja isso", "leia a tela", "analise a imagem"]
        # Removemos dependencia hardcoded para não travar o carregamento
        self.dependencies = ["brain", "context"]

    def check_dependencies(self):
        if not VISAO_AVAILABLE:
            print("[VISAO] Aviso: 'pyautogui' não instalado. Módulo desativado.")
            return True # Retorna True para não matar o sistema, apenas fica inativo
        return super().check_dependencies()

    def process(self, command: str) -> str:
        if not VISAO_AVAILABLE:
            return "Erro: Instale 'pyautogui' para usar a visão."
            
        brain = self.core_context.get("brain")
        ctx = self.core_context.get("context")

        try:
            screenshot = pyautogui.screenshot()
            img_byte_arr = BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            
            analise = brain.ver(img_byte_arr.getvalue())

            if ctx:
                ctx.set("vision_last_result", analise, ttl=600)
            
            return f"Visão: {analise}"
        except Exception as e:
            return f"Erro visual: {e}"