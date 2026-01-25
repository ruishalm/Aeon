import importlib
import inspect
import os
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
            self.vector_memory = VectorMemory(str(config_mgr.storage_path))

    def load_modules(self):
        """Escaneia /modules e carrega tudo."""
        root_dir = Path(__file__).resolve().parent
        # Se não encontrar a pasta modules aqui, tenta subir um nível (caso esteja em /core)
        if not (root_dir / "modules").exists():
            root_dir = root_dir.parent
        modules_dir = root_dir / "modules"
        
        if not modules_dir.exists():
            log_display(f"⚠ Erro: Pasta de módulos não encontrada em {modules_dir}")
            return

        log_display(f"Carregando módulos de: {modules_dir}")

        for item in modules_dir.iterdir():
            if item.is_dir() and item.name != "__pycache__":
                try:
                    for mod_file in item.glob("*_mod.py"):
                        module_name = f"modules.{item.name}.{mod_file.stem}"
                        self._import_and_register(module_name)
                except Exception as e:
                    log_display(f"  ✗ Erro ao carregar '{item.name}': {e}")

        log_display(f"Módulos carregados: {len(self.modules)}")

    def _import_and_register(self, module_name):
        """Helper para importar e registrar um único módulo com HOT RELOAD."""
        try:
            if module_name in sys.modules:
                module_import = importlib.reload(sys.modules[module_name])
                log_display(f"  ↻ Módulo '{module_name}' recarregado (Hot Reload).")
            else:
                module_import = importlib.import_module(module_name)
            
            for name, obj in inspect.getmembers(module_import):
                if inspect.isclass(obj) and issubclass(obj, AeonModule) and obj is not AeonModule:
                    module_instance = obj(self.core_context)
                    if not module_instance.check_dependencies():
                        log_display(f"  ⚠ Dependências falharam para {name} em {module_name}")
                        continue

                    if module_instance.on_load():
                        self.modules.append(module_instance)
                        self.module_map[module_instance.name.lower()] = module_instance
                        for trigger in module_instance.triggers:
                            self.trigger_map[trigger.lower()] = module_instance
                        log_display(f"  ✓ {module_instance.name} registrado.")
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

    def route_command(self, command: str) -> str:
        """Roteia comando com PRIORIDADE DE TAMANHO."""
        command_lower = command.lower()
        response = ""

        # 1. MODO FOCO
        if self.focused_module is not None:
            log_display(f"🔒 FOCO: {self.focused_module.name}")
            return self.focused_module.process(command) or ""
        
        # 2. MODO LIVRE (Ordenado)
        triggered = False
        sorted_triggers = sorted(self.trigger_map.items(), key=lambda x: len(x[0]), reverse=True)

        for trigger, module in sorted_triggers:
            if trigger in command_lower:
                if not module.check_dependencies():
                    return f"Erro: Dependência de {module.name} falhou."
                
                log_display(f"Trigger '{trigger}' acionou '{module.name}'")
                response = module.process(command)
                triggered = True
                break 

        # 3. FALLBACK (Brain)
        if not triggered:
            brain = self.core_context.get("brain")
            if brain:
                hist = self._format_history()
                caps = self.get_capabilities_summary()
                
                # Recupera memórias de longo prazo relevantes para a pergunta atual
                long_term = ""
                if self.vector_memory:
                    long_term = self.vector_memory.retrieve_relevant(command)
                
                response = brain.pensar(prompt=command, historico_txt=hist, system_override=None, capabilities=caps, long_term_context=long_term)
            else:
                response = "Cérebro indisponível."

        # 4. MEMÓRIA (Thread-Safe)
        if response:
            with self.history_lock:
                self.chat_history.append({"role": "user", "content": command})
                self.chat_history.append({"role": "assistant", "content": response})
                
                # Salva a interação na memória de longo prazo (apenas se não for comando de módulo)
                if self.vector_memory and not triggered:
                    self.vector_memory.store_interaction(command, response)
                
                # Garante que a lista não exceda o tamanho máximo
                history_len = len(self.chat_history)
                if history_len > self.max_history * 2:
                    self.chat_history = self.chat_history[history_len - self.max_history * 2:]

        return response if response else ""

    # Métodos de Foco
    def lock_focus(self, module, timeout=None):
        with self.focus_lock:
            self.focused_module = module
    
    def release_focus(self):
        with self.focus_lock:
            self.focused_module = None

    def get_module(self, name):
        """Retorna uma instância de módulo pelo nome."""
        return self.module_map.get(name.lower())

    def get_module(self, name):
        """Retorna uma instância de módulo pelo nome."""
        return self.module_map.get(name.lower())

    def get_loaded_modules(self):
        return self.modules