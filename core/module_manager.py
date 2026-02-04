import importlib
import inspect
import sys
import threading
from pathlib import Path

from modules.base_module import AeonModule
from core.memory_vector import VectorMemory

def log_display(msg):
    print(f"[MOD_MANAGER] {msg}")

class ModuleManager:
    """
    Carrega, gerencia e roteia comandos para todos os módulos do Aeon.
    """
    
    def __init__(self, core_context):
        self.core_context = core_context
        self.modules = []
        self.trigger_map = {}
        self.module_map = {}
        self.failed_modules = []
        
        self.focused_module = None
        self.focus_timeout = None
        self.focus_lock = threading.Lock()
        
        self.chat_history = []
        self.max_history = 10
        self.history_lock = threading.Lock()
        
        # Inicializa Memória Vetorial
        self.vector_memory = None
        config_mgr = self.core_context.get("config_manager")
        if config_mgr:
            try:
                self.vector_memory = VectorMemory(str(config_mgr.storage_path))
            except Exception as e:
                log_display(f"AVISO - Falha ao inicializar VectorMemory: {e}")
                self.vector_memory = None

    def load_modules(self):
        """Escaneia /modules e carrega tudo."""
        # CORREÇÃO: Usa resolve() para caminho absoluto
        modules_dir = Path(__file__).resolve().parent.parent / "modules"
        log_display(f"Carregando módulos de: {modules_dir}")

        for item in modules_dir.iterdir():
            if item.is_dir() and item.name != "__pycache__":
                try:
                    for mod_file in item.glob("*_mod.py"):
                        module_name = f"modules.{item.name}.{mod_file.stem}"
                        self._import_and_register(module_name)
                except Exception as e:
                    log_display(f"  ERRO Erro ao carregar '{item.name}': {e}")

        log_display(f"Módulos carregados: {len(self.modules)}")

    def _import_and_register(self, module_name):
        """Helper para importar e registrar um único módulo com HOT RELOAD."""
        try:
            if module_name in sys.modules:
                module_import = importlib.reload(sys.modules[module_name])
                log_display(f"  RECARREG Módulo '{module_name}' recarregado (Hot Reload).")
            else:
                module_import = importlib.import_module(module_name)
            
            for name, obj in inspect.getmembers(module_import):
                if inspect.isclass(obj) and issubclass(obj, AeonModule) and obj is not AeonModule:
                    module_instance = obj(self.core_context)
                    if not module_instance.check_dependencies():
                        log_display(f"  AVISO Dependências falharam para {module_instance.name}")
                        return

                    if module_instance.on_load():
                        self.modules.append(module_instance)
                        self.module_map[module_instance.name.lower()] = module_instance
                        for trigger in module_instance.triggers:
                            self.trigger_map[trigger.lower()] = module_instance
                        log_display(f"  OK {module_instance.name} registrado.")
                    break
        except Exception as e:
            log_display(f"Erro importando {module_name}: {e}")

    def scan_new_modules(self):
        """Re-escaneia módulos (usado pela Singularidade)."""
        log_display("Re-escaneando novos módulos...")
        self.trigger_map = {}
        self.modules = []
        self.load_modules()
        return ["Reloaded"]

    def _format_history(self):
        """Formata histórico para o LLM de forma segura."""
        with self.history_lock:
            history_text = ""
            for msg in self.chat_history:
                role = "Usuário" if msg['role'] == 'user' else "Aeon"
                history_text += f"{role}: {msg['content']}\n"
            return history_text

    def get_capabilities_summary(self) -> str:
        """Retorna uma lista de todos os módulos e o que eles fazem para o Brain."""
        summary = "Você tem acesso aos seguintes módulos técnicos:\n"
        for mod in self.modules:
            desc = getattr(mod, 'metadata', {}).get('description', 'Sem descrição.')
            summary += f"- {mod.name}: {desc} (Gatilhos: {', '.join(mod.triggers[:5])})\n"
        return summary

    def route_command(self, command: str):
        """Roteia comando com PRIORIDADE DE TAMANHO.
        
        Retorna:
        - str: resposta do módulo (comando encontrado)
        - None: nenhum trigger encontrado (deixa pro Brain conversar)
        """
        command_lower = command.lower()

        # 1. MODO FOCO
        if self.focused_module is not None:
            log_display(f"FOCO: {self.focused_module.name}")
            response = self.focused_module.process(command)
            # Salva na história
            if response:
                with self.history_lock:
                    self.chat_history.append({"role": "user", "content": command})
                    self.chat_history.append({"role": "assistant", "content": response})
            return response or ""
        
        # 2. MODO LIVRE (Ordenado por comprimento de trigger)
        sorted_triggers = sorted(self.trigger_map.items(), key=lambda x: len(x[0]), reverse=True)

        for trigger, module in sorted_triggers:
            if trigger in command_lower:
                if not module.check_dependencies():
                    response = f"Erro: Dependencia de {module.name} falhou."
                    return response
                
                log_display(f"Trigger '{trigger}' acionou '{module.name}'")
                response = module.process(command)
                
                # Salva na história
                if response:
                    with self.history_lock:
                        self.chat_history.append({"role": "user", "content": command})
                        self.chat_history.append({"role": "assistant", "content": response})
                
                return response if response else ""
        
        # 3. Se nenhum trigger foi disparado, RETORNA NONE
        # MainLogic decidirá se manda pro Brain para conversa natural
        return None

    # Métodos de Foco
    def lock_focus(self, module, timeout=None):
        with self.focus_lock:
            self.focused_module = module
    
    def release_focus(self):
        with self.focus_lock:
            self.focused_module = None

    def get_loaded_modules(self):
        return self.modules
