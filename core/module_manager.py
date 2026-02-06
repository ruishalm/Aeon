import importlib
import inspect
import sys
import threading
from pathlib import Path
import unicodedata

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
        # Exponha este gerenciador no contexto para que módulos possam consultá-lo
        try:
            if isinstance(self.core_context, dict):
                self.core_context["module_manager"] = self
        except Exception:
            pass
        self.modules = []
        self.trigger_map = {}
        self.trigger_orig_map = {}
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

    def _normalize(self, s: str) -> str:
        """Remove acentos e normaliza texto para matching insensível a diacríticos."""
        import re
        if not s:
            return ""
        s = unicodedata.normalize('NFD', s)
        s = ''.join(ch for ch in s if not unicodedata.combining(ch))
        s = s.lower()
        s = re.sub(r'[^a-z0-9\s]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

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
                            key = self._normalize(trigger)
                            self.trigger_map[key] = module_instance
                            self.trigger_orig_map[key] = trigger
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
        command_norm = self._normalize(command_lower)

        # 1. MODO FOCO
        if self.focused_module is not None:
            log_display(f"FOCO: {self.focused_module.name}")
            response = self.focused_module.process(command)
            # Se o módulo em foco não processou, delega ao Brain (retorna None)
            if response is None:
                return None
            # Salva na história
            if response:
                with self.history_lock:
                    self.chat_history.append({"role": "user", "content": command})
                    self.chat_history.append({"role": "assistant", "content": response})
                    # Persist to vector memory if available
                    try:
                        if self.vector_memory and getattr(self.vector_memory, 'available', False):
                            self.vector_memory.store_interaction(command, response)
                    except Exception:
                        pass
                    # Trim history to keep recent items only
                    history_len = len(self.chat_history)
                    if history_len > self.max_history * 2:
                        self.chat_history = self.chat_history[history_len - self.max_history * 2:]
            return response
        
        # 2. MODO LIVRE (Ordenado por comprimento de trigger)
        sorted_triggers = sorted(self.trigger_map.items(), key=lambda x: len(x[0]), reverse=True)

        for trigger, module in sorted_triggers:
            if trigger in command_norm:
                if not module.check_dependencies():
                    response = f"Erro: Dependencia de {module.name} falhou."
                    return response
                
                pretty = self.trigger_orig_map.get(trigger, trigger)
                log_display(f"Trigger '{pretty}' acionou '{module.name}'")
                response = module.process(command)
                # Se o módulo explicitamente não processou (None), continua procurando
                if response is None:
                    continue

                # Salva na história
                if response:
                    with self.history_lock:
                        self.chat_history.append({"role": "user", "content": command})
                        self.chat_history.append({"role": "assistant", "content": response})
                        try:
                            if self.vector_memory and getattr(self.vector_memory, 'available', False):
                                self.vector_memory.store_interaction(command, response)
                        except Exception:
                            pass
                        history_len = len(self.chat_history)
                        if history_len > self.max_history * 2:
                            self.chat_history = self.chat_history[history_len - self.max_history * 2:]

                return response
        
        # 3. Se nenhum trigger foi disparado, tenta matching difuso (token-based)
        fuzzy_mod, fuzzy_trigger, fuzzy_ratio = self._best_fuzzy_match(command_norm, min_ratio=0.70)
        if fuzzy_mod:
            if not fuzzy_mod.check_dependencies():
                return f"Erro: Dependencia de {fuzzy_mod.name} falhou."
            pretty = self.trigger_orig_map.get(fuzzy_trigger, fuzzy_trigger)
            log_display(f"Fuzzy trigger '{pretty}' (ratio={fuzzy_ratio:.2f}) acionou '{fuzzy_mod.name}'")
            response = fuzzy_mod.process(command)
            if response is None:
                return None
            if response:
                with self.history_lock:
                    self.chat_history.append({"role": "user", "content": command})
                    self.chat_history.append({"role": "assistant", "content": response})
                    try:
                        if self.vector_memory and getattr(self.vector_memory, 'available', False):
                            self.vector_memory.store_interaction(command, response)
                    except Exception:
                        pass
                    history_len = len(self.chat_history)
                    if history_len > self.max_history * 2:
                        self.chat_history = self.chat_history[history_len - self.max_history * 2:]
            return response

        # 4. Se nenhum trigger foi disparado, RETORNA NONE
        # MainLogic decidirá se manda pro Brain para conversa natural
        return None

    def executar_ferramenta(self, tool_name: str, params=None):
        """Executa uma ferramenta por nome no formato 'Modulo.metodo'.

        Exemplo: 'Lembretes.criar_lembrete' com params dict.
        """
        if not tool_name:
            return "Ferramenta invalida."

        parts = tool_name.split('.')
        if len(parts) != 2:
            return f"Nome de ferramenta mal formatado: {tool_name}"

        mod_name, func_name = parts[0].lower(), parts[1]
        
        # Tratamento especial para "Aeon" (meta-comandos)
        if mod_name == "aeon":
            if func_name == "limpar_contexto":
                with self.history_lock:
                    self.chat_history = []
                return "Contexto e histórico de conversa foram limpos. Começando do zero!"
            return f"Comando Aeon desconhecido: {func_name}"
        
        # Procura modulo pelo nome (case-insensitive)
        module = self.module_map.get(mod_name)
        if not module:
            # Tenta buscar por nome parcial
            for m in self.modules:
                if m.name.lower() == mod_name or m.name.lower().startswith(mod_name):
                    module = m
                    break

        if not module:
            return f"Modulo '{parts[0]}' nao encontrado."

        if not hasattr(module, func_name):
            return f"Metodo '{func_name}' nao encontrado em {module.name}."

        try:
            func = getattr(module, func_name)
            if params is None:
                return func()
            if isinstance(params, dict):
                return func(**params)
            return func(params)
        except Exception as e:
            return f"Erro executando ferramenta: {e}"

    def _best_fuzzy_match(self, command_lower: str, min_ratio: float = 0.5):
        """Retorna (module, trigger, ratio) do melhor match token-based, ou (None, None, 0)."""
        import re
        def tokens(s):
            return [t for t in re.findall(r"[a-zA-Z0-9]+", s)]

        best = (None, None, 0.0)
        cmd_tokens = set(tokens(command_lower))
        if not cmd_tokens:
            return best

        for trigger, module in self.trigger_map.items():
            trg_tokens = set(tokens(trigger))
            if not trg_tokens:
                continue
            inter = cmd_tokens.intersection(trg_tokens)
            ratio = len(inter) / len(trg_tokens)
            if ratio > best[2]:
                best = (module, trigger, ratio)

        if best[2] >= min_ratio:
            return best
        return (None, None, 0.0)

    # Métodos de Foco
    def lock_focus(self, module, timeout=None, timeout_seconds=None):
        """Lock focus on a module. Accepts both timeout and timeout_seconds for compatibility."""
        with self.focus_lock:
            self.focused_module = module
    
    def release_focus(self):
        with self.focus_lock:
            self.focused_module = None

    def get_loaded_modules(self):
        return self.modules
