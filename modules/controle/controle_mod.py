import subprocess
import webbrowser
import shutil
import threading
from typing import List, Dict
from modules.base_module import AeonModule

class ControleModule(AeonModule):
    """
    Modulo para controlar o proprio Aeon:
    - Conectar/reconectar ao servico de nuvem
    - Instalar modelos offline (Ollama)
    - Recalibrar microfone
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Controle"
        self.triggers = [
            "conectar", "online", "reconectar",
            "instalar offline", "baixar modelos", "instalar ollama",
            "calibrar microfone", "ajustar audio", "recalibrar",
            "diagnostico", "diagnostico", "verificar modulos", "verificar modulos",
            "modo visivel", "aparecer", "ficar visivel", "mostrar"
        ]

    @property
    def dependencies(self) -> List[str]:
        """Controle depende de brain e io_handler."""
        return []  # Dependencias do core_context, nao de modulos

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do modulo."""
        return {
            "version": "2.0.0",
            "author": "Aeon Core",
            "description": "Controla conexao com nuvem, instalacao offline e calibracao de audio"
        }

    def on_load(self) -> bool:
        """Inicializa o modulo - valida dependencias."""
        brain = self.core_context.get("brain")
        io_handler = self.core_context.get("io_handler")
        if not brain or not io_handler:
            print("[ControleModule] Erro: dependencias nao encontradas")
            return False
        return True

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        return True

    def process(self, command: str) -> str:
        # O metodo process agora serve como um fallback ou para gatilhos diretos
        # que nao sao chamados pela IA.
        if "diagnostico" in command or "diagnostico" in command or "verificar modulos" in command or "verificar modulos" in command:
            return self.diagnostico_modulos()
        if "conectar" in command or "online" in command or "reconectar" in command:
            return self.reconectar_nuvem()
        if "instalar offline" in command or "baixar modelos" in command or "instalar ollama" in command:
            return self.instalar_offline()
        if "calibrar microfone" in command or "ajustar audio" in command or "recalibrar" in command:
            return self.recalibrar_microfone()
        if "modo visivel" in command or "aparecer" in command or "ficar visivel" in command or "mostrar" in command:
            return self.toggle_modo_visivel()
        return ""

    # --- Metodos de Ferramentas para a IA ---

    def diagnostico_modulos(self) -> str:
        """Executa um diagnostico dos modulos."""
        module_manager = self.core_context.get("module_manager")
        if module_manager and hasattr(module_manager, 'get_info'):
            # Supondo que get_info de cada modulo retorne um dict com o status
            all_info = [m.get_info() for m in module_manager.get_loaded_modules()]
            report = "Diagnostico dos Modulos:\n"
            for info in all_info:
                status = "OK" if info.get('loaded') and info.get('dependencies_ok') else "FALHA"
                report += f"- {info.get('name')}: {status}\n"
            return report
        return "Nao foi possivel acessar o gerenciador de modulos para o diagnostico."

    def reconectar_nuvem(self) -> str:
        """Forca a reconexao com o servico de IA na nuvem."""
        brain = self.core_context.get("brain")
        if brain and hasattr(brain, 'reconectar'):
            return brain.reconectar()
        return "Cerebro nao encontrado ou nao suporta reconexao."

    def recalibrar_microfone(self) -> str:
        """Inicia o processo de recalibracao do microfone."""
        io_handler = self.core_context.get("io_handler")
        if io_handler and hasattr(io_handler, "recalibrar_mic"):
            io_handler.recalibrar_mic()
            return "Entendido. Silencio por 3 segundos para recalibracao do microfone."
        return "O handler de audio nao suporta recalibracao."

    def instalar_offline(self) -> str:
        """Instala Ollama e baixa modelos de IA para uso offline."""
        brain = self.core_context.get("brain")
        io_handler = self.core_context.get("io_handler")
        status_manager = self.core_context.get("status_manager")

        def install_thread():
            if not shutil.which("ollama"):
                if io_handler: io_handler.falar("Ollama nao encontrado. Tentando instalar via winget...")
                try:
                    subprocess.run(["winget", "install", "Ollama.Ollama"], check=True, capture_output=True, text=True)
                    if io_handler: io_handler.falar("Ollama instalado com sucesso.")
                except Exception as e:
                    if io_handler: io_handler.falar(f"Erro ao instalar Ollama: {e}. Abrindo o site para download manual.")
                    webbrowser.open("https://ollama.com/download")
                    return

            if io_handler: io_handler.falar("Iniciando download dos modelos de IA offline. Isso pode demorar varios minutos.")
            subprocess.Popen("ollama pull llama3")
            subprocess.Popen("ollama pull moondream")

            if brain: brain.local_ready = True
            if status_manager: status_manager.update_local_status(True)
            if io_handler: io_handler.falar("Modelos offline baixados. O Aeon agora pode funcionar sem internet.")

        threading.Thread(target=install_thread, daemon=True).start()
        return "Iniciando processo de instalacao e download em segundo plano. Avisarei quando terminar."

    # --- Declaracao das Ferramentas para a IA ---

    def get_tools(self) -> List[Dict[str, any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "Controle.diagnostico_modulos",
                    "description": "Verifica e reporta o status de todos os modulos carregados, informando se estao ativos e com as dependencias resolvidas.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Controle.reconectar_nuvem",
                    "description": "Forca uma nova tentativa de conexao com o servico de Inteligencia Artificial na nuvem (Groq). Util se a conexao cair.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Controle.recalibrar_microfone",
                    "description": "Inicia o processo de recalibracao do microfone para ajustar a sensibilidade ao ruido ambiente. Exige 3 segundos de silencio.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Controle.instalar_offline",
                    "description": "Inicia o processo de instalacao do Ollama (se nao estiver instalado) e o download dos modelos de IA 'llama3' e 'moondream' para permitir o funcionamento offline.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    def toggle_modo_visivel(self) -> str:
        """Mostra a esfera (modo visível)."""
        gui = self.core_context.get("gui")
        if gui and hasattr(gui, "show_sphere"):
            gui.show_sphere()
            return "Modo visível ativado. Estou aqui!"
        return "Interface gráfica não disponível."

