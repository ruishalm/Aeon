import subprocess
import webbrowser
import shutil
import threading
from typing import List, Dict
from modules.base_module import AeonModule

class ControleModule(AeonModule):
    """
    Módulo para controlar o próprio Aeon:
    - Conectar/reconectar ao serviço de nuvem
    - Instalar modelos offline (Ollama)
    - Recalibrar microfone
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Controle"
        self.triggers = [
            "conectar", "online", "reconectar",
            "instalar offline", "baixar modelos", "instalar ollama",
            "calibrar microfone", "ajustar áudio", "recalibrar",
            "diagnóstico", "diagnostico", "verificar módulos", "verificar modulos"
        ]

    @property
    def dependencies(self) -> List[str]:
        """Controle depende de brain e io_handler."""
        return []  # Dependências do core_context, não de módulos

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do módulo."""
        return {
            "version": "2.0.0",
            "author": "Aeon Core",
            "description": "Controla conexão com nuvem, instalação offline e calibração de áudio"
        }

    def on_load(self) -> bool:
        """Inicializa o módulo - valida dependências."""
        brain = self.core_context.get("brain")
        io_handler = self.core_context.get("io_handler")
        if not brain or not io_handler:
            print("[ControleModule] Erro: dependências não encontradas")
            return False
        return True

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        return True

    def process(self, command: str) -> str:
        # O método process agora serve como um fallback ou para gatilhos diretos
        # que não são chamados pela IA.
        if "diagnóstico" in command or "diagnostico" in command or "verificar módulos" in command or "verificar modulos" in command:
            return self.diagnostico_modulos()
        if "conectar" in command or "online" in command or "reconectar" in command:
            return self.reconectar_nuvem()
        if "instalar offline" in command or "baixar modelos" in command or "instalar ollama" in command:
            return self.instalar_offline()
        if "calibrar microfone" in command or "ajustar áudio" in command or "recalibrar" in command:
            return self.recalibrar_microfone()
        return ""

    # --- Métodos de Ferramentas para a IA ---

    def diagnostico_modulos(self) -> str:
        """Executa um diagnóstico dos módulos."""
        module_manager = self.core_context.get("module_manager")
        if module_manager and hasattr(module_manager, 'get_info'):
            # Supondo que get_info de cada módulo retorne um dict com o status
            all_info = [m.get_info() for m in module_manager.get_loaded_modules()]
            report = "Diagnóstico dos Módulos:\n"
            for info in all_info:
                status = "OK" if info.get('loaded') and info.get('dependencies_ok') else "FALHA"
                report += f"- {info.get('name')}: {status}\n"
            return report
        return "Não foi possível acessar o gerenciador de módulos para o diagnóstico."

    def reconectar_nuvem(self) -> str:
        """Força a reconexão com o serviço de IA na nuvem."""
        brain = self.core_context.get("brain")
        if brain and hasattr(brain, 'reconectar'):
            return brain.reconectar()
        return "Cérebro não encontrado ou não suporta reconexão."

    def recalibrar_microfone(self) -> str:
        """Inicia o processo de recalibração do microfone."""
        io_handler = self.core_context.get("io_handler")
        if io_handler and hasattr(io_handler, "recalibrar_mic"):
            io_handler.recalibrar_mic()
            return "Entendido. Silêncio por 3 segundos para recalibração do microfone."
        return "O handler de áudio não suporta recalibração."

    def instalar_offline(self) -> str:
        """Instala Ollama e baixa modelos de IA para uso offline."""
        brain = self.core_context.get("brain")
        io_handler = self.core_context.get("io_handler")
        status_manager = self.core_context.get("status_manager")

        def install_thread():
            if not shutil.which("ollama"):
                if io_handler: io_handler.falar("Ollama não encontrado. Tentando instalar via winget...")
                try:
                    subprocess.run(["winget", "install", "Ollama.Ollama"], check=True, capture_output=True, text=True)
                    if io_handler: io_handler.falar("Ollama instalado com sucesso.")
                except Exception as e:
                    if io_handler: io_handler.falar(f"Erro ao instalar Ollama: {e}. Abrindo o site para download manual.")
                    webbrowser.open("https://ollama.com/download")
                    return

            if io_handler: io_handler.falar("Iniciando download dos modelos de IA offline. Isso pode demorar vários minutos.")
            subprocess.Popen("ollama pull llama3")
            subprocess.Popen("ollama pull moondream")

            if brain: brain.local_ready = True
            if status_manager: status_manager.update_local_status(True)
            if io_handler: io_handler.falar("Modelos offline baixados. O Aeon agora pode funcionar sem internet.")

        threading.Thread(target=install_thread, daemon=True).start()
        return "Iniciando processo de instalação e download em segundo plano. Avisarei quando terminar."

    # --- Declaração das Ferramentas para a IA ---

    def get_tools(self) -> List[Dict[str, any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "Controle.diagnostico_modulos",
                    "description": "Verifica e reporta o status de todos os módulos carregados, informando se estão ativos e com as dependências resolvidas.",
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
                    "description": "Força uma nova tentativa de conexão com o serviço de Inteligência Artificial na nuvem (Groq). Útil se a conexão cair.",
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
                    "description": "Inicia o processo de recalibração do microfone para ajustar a sensibilidade ao ruído ambiente. Exige 3 segundos de silêncio.",
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
                    "description": "Inicia o processo de instalação do Ollama (se não estiver instalado) e o download dos modelos de IA 'llama3' e 'moondream' para permitir o funcionamento offline.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
