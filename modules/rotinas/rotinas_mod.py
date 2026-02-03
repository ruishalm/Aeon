from modules.base_module import AeonModule
from typing import List, Dict, Any
import time
import threading

class RotinasModule(AeonModule):
    """
    Módulo para criar, executar e listar rotinas (macros) de comandos.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Rotinas"
        self.triggers = ["rotina", "rotinas"]
        self.recording_routine_name = None
        self.recorded_commands = []

    @property
    def dependencies(self) -> List[str]:
        return ["config_manager", "io_handler", "module_manager"]

    @property
    def metadata(self) -> Dict[str, str]:
        return {
            "version": "3.0.0",
            "author": "Aeon Core",
            "description": "Cria e executa rotinas de comandos (macros)."
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "Rotinas.iniciar_gravacao_rotina",
                    "description": "Inicia a gravação de uma nova rotina (macro). Todos os comandos seguintes do usuário serão adicionados a esta rotina até que a gravação seja parada.",
                    "parameters": {
                        "type": "object",
                        "properties": {"nome_rotina": {"type": "string", "description": "O nome para a nova rotina. Ex: 'bom dia', 'setup de trabalho'"}},
                        "required": ["nome_rotina"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Rotinas.parar_gravacao_rotina",
                    "description": "Para a gravação da rotina atual e a salva permanentemente.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Rotinas.executar_rotina",
                    "description": "Executa uma rotina de comandos previamente salva.",
                    "parameters": {
                        "type": "object",
                        "properties": {"nome_rotina": {"type": "string", "description": "O nome da rotina a ser executada."}},
                        "required": ["nome_rotina"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Rotinas.listar_rotinas",
                    "description": "Lista os nomes de todas as rotinas salvas.",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

    def process(self, command: str) -> str:
        """Processa comandos apenas quando uma gravação está ativa."""
        if self.recording_routine_name:
            if "parar" in command and "gravar" in command:
                return self.parar_gravacao_rotina()
            else:
                self.recorded_commands.append(command)
                return f"Adicionado: '{command}' à rotina '{self.recording_routine_name}'."
        return ""

    # --- FERRAMENTAS PARA A IA ---

    def iniciar_gravacao_rotina(self, nome_rotina: str) -> str:
        if not nome_rotina:
            return "Preciso de um nome para a rotina."
        self.recording_routine_name = nome_rotina
        self.recorded_commands = []
        return f"Ok, gravando a rotina '{nome_rotina}'. Diga os comandos. Use 'parar gravação' quando terminar."

    def parar_gravacao_rotina(self) -> str:
        config_manager = self.core_context.get("config_manager")
        if not self.recording_routine_name:
            return "Nenhuma gravação estava em andamento."

        if self.recorded_commands:
            routines = config_manager.get_system_data("routines", {})
            routines[self.recording_routine_name] = self.recorded_commands
            config_manager.set_system_data("routines", routines)
            response = f"Rotina '{self.recording_routine_name}' salva com sucesso."
        else:
            response = "Nenhum comando foi gravado. Rotina cancelada."
            
        self.recording_routine_name = None
        self.recorded_commands = []
        return response

    def listar_rotinas(self) -> str:
        config_manager = self.core_context.get("config_manager")
        routines = config_manager.get_system_data("routines", {})
        if routines:
            return f"Suas rotinas salvas são: {', '.join(routines.keys())}."
        else:
            return "Você ainda não tem nenhuma rotina salva."

    def executar_rotina(self, nome_rotina: str) -> str:
        config_manager = self.core_context.get("config_manager")
        routines = config_manager.get_system_data("routines", {})
        
        if nome_rotina in routines:
            def run_routine():
                module_manager = self.core_context.get("module_manager")
                io_handler = self.core_context.get("io_handler")
                
                io_handler.falar(f"Executando a rotina '{nome_rotina}'.")
                
                for command in routines[nome_rotina]:
                    print(f"Executando (Rotina): {command}")
                    response = module_manager.route_command(command)
                    if response:
                        io_handler.falar(response)
                    time.sleep(1.5)
                
                io_handler.falar(f"Rotina '{nome_rotina}' finalizada.")

            threading.Thread(target=run_routine, daemon=True).start()
            return f"Iniciando a execução da rotina '{nome_rotina}'."
        else:
            return f"Não encontrei a rotina chamada '{nome_rotina}'."
