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
        import os # Reforço local
        root_dir = Path(__file__).resolve().parent
        # Se não encontrar a pasta modules aqui, tenta subir um nível (caso esteja em /core)
        if not (root_dir / "modules").exists():
            root_dir = root_dir.parent
        
        # FIX: Garante que a raiz do projeto esteja no sys.path para imports funcionarem
        if str(root_dir) not in sys.path:
            sys.path.append(str(root_dir))
            
        modules_dir = root_dir / "modules"
        
        if not modules_dir.exists():
            log_display(f"⚠ Erro: Pasta de módulos não encontrada em {modules_dir}")
            return

        log_display(f"Carregando módulos de: {modules_dir}")

        for item in modules_dir.iterdir():
            if item.is_dir() and item.name != "__pycache__":
                try:
                    log_display(f"  > Verificando: {item.name}...")
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
                        log_display(f"  + {module_instance.name} registrado.")
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
        """Retorna uma lista de todas as ferramentas de todos os módulos como uma string JSON."""
        import json
        all_tools = []
        for mod in self.modules:
            try:
                module_tools = mod.get_tools()
                if module_tools:
                    all_tools.extend(module_tools)
            except Exception as e:
                log_display(f"Erro ao obter ferramentas do módulo '{mod.name}': {e}")
        
        # Converte a lista de ferramentas para uma string JSON formatada
        return json.dumps(all_tools, indent=2)

    def _route_by_trigger(self, command: str) -> str:
        """Helper para rotear um comando usando a lógica de gatilhos (para bypass)."""
        command_lower = command.lower()

        # 1. MODO FOCO (tem prioridade no bypass)
        if self.focused_module is not None:
            log_display(f"🔒 FOCO: {self.focused_module.name}")
            return self.focused_module.process(command) or ""
        
        # 2. MODO LIVRE (Ordenado)
        sorted_triggers = sorted(self.trigger_map.items(), key=lambda x: len(x[0]), reverse=True)
        for trigger, module in sorted_triggers:
            if trigger in command_lower:
                if not module.check_dependencies():
                    return f"Erro: Dependência de {module.name} falhou."
                
                log_display(f"Trigger de bypass '{trigger}' acionou '{module.name}'")
                return module.process(command)
        return ""

    def route_command(self, command: str) -> str:
        """
        Roteia o comando usando uma abordagem AI-First.
        A IA interpreta todos os comandos, a menos que um bypass '!' seja usado.
        """
        # ETAPA 1: Checar por comandos de bypass (ex: !desligar)
        if command.startswith("!"):
            bypass_command = command[1:].strip()
            response = self._route_by_trigger(bypass_command)
            if not response:
                log_display(f"Comando de bypass '{bypass_command}' não encontrou um gatilho.")
                response = f"Comando de bypass '{bypass_command}' não reconhecido."
        else:
            # ETAPA 2: ROTEAMENTO PRINCIPAL VIA CÉREBRO (AI-First)
            brain = self.core_context.get("brain")
            if brain:
                # Coleta de contexto para a IA
                biblioteca_mod = self.get_module("Biblioteca")
                library_context = ""
                if biblioteca_mod and hasattr(biblioteca_mod, 'pesquisar_livros'):
                    library_context = biblioteca_mod.pesquisar_livros(command) or ""
                
                hist = self._format_history()
                caps = self.get_capabilities_summary()
                long_term = self.vector_memory.retrieve_relevant(command) if self.vector_memory else ""
                
                # O Cérebro decide a ação, retornando um dict para 'tool call' ou string para 'conversa'
                ai_decision = brain.pensar(
                    prompt=command, historico_txt=hist, capabilities=caps,
                    long_term_context=long_term, library_context=library_context
                )

                # ETAPA 3: EXECUTAR A DECISÃO DA IA
                if isinstance(ai_decision, dict):
                    if "fallback" in ai_decision:
                        response = ai_decision["fallback"]
                    elif "tool_name" in ai_decision:
                        tool_name = ai_decision.get("tool_name")
                        params = ai_decision.get("parameters", {})
                        
                        try:
                            module_name, function_name = tool_name.split('.')
                            module_instance = self.get_module(module_name)
                            
                            if module_instance and hasattr(module_instance, function_name):
                                log_display(f"IA executando: {tool_name} com params: {params}")
                                method_to_call = getattr(module_instance, function_name)
                                # Executa a função do módulo com os parâmetros
                                result = method_to_call(**params) if isinstance(params, dict) else method_to_call(params)
                                response = str(result) if result is not None else f"Ação {tool_name} executada."
                            else:
                                response = f"Erro: A IA tentou usar uma ferramenta inexistente: {tool_name}"
                        except ValueError:
                            response = f"Erro: O formato do 'tool_name' ('{tool_name}') é inválido. Esperado 'Modulo.funcao'."
                        except Exception as e:
                            response = f"Erro ao executar a ferramenta '{tool_name}': {e}"
                    else:
                        response = "A IA retornou uma decisão que não consigo entender."
                
                elif isinstance(ai_decision, str):
                    response = ai_decision # Resposta de conversação direta
                else:
                    response = "Cérebro indisponível ou resposta inválida."
            else:
                response = "Cérebro indisponível."

        # ETAPA 4: MEMÓRIA
        if response:
            with self.history_lock:
                self.chat_history.append({"role": "user", "content": command})
                self.chat_history.append({"role": "assistant", "content": response})
                
                if self.vector_memory and not command.startswith("!"):
                    self.vector_memory.store_interaction(command, response)
                
                history_len = len(self.chat_history)
                if history_len > self.max_history * 2:
                    self.chat_history = self.chat_history[history_len - self.max_history * 2:]

        return response or "Não entendi."

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

    def get_loaded_modules(self):
        return self.modules