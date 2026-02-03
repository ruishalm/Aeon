import os
import sys
import importlib
import inspect
import threading

class ModuleManager:
    def __init__(self, core_context):
        # compatibilidade com testes e código existente
        self.core_context = core_context
        self.context = core_context

        # Lista de instâncias dos módulos carregados
        self.modules = []
        # Mapas úteis
        self.module_map = {}   # name (lower) -> instance
        self.trigger_map = {}  # trigger -> instance

        # Histórico de conversa para passagem ao Brain
        self.chat_history = []
        self.max_history = 10

    def load_modules(self):
        """Varre a pasta 'modules' e carrega tudo dinamicamente."""
        print("[MOD_MANAGER] Iniciando varredura de módulos...")
        
        # Caminho absoluto da pasta modules
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        modules_dir = os.path.join(base_dir, "modules")
        
        if not os.path.exists(modules_dir):
            print(f"[ERRO] Pasta de módulos não encontrada: {modules_dir}")
            return

        # Garante que o Python enxerga a pasta raiz
        if base_dir not in sys.path:
            sys.path.append(base_dir)

        # Varre cada subpasta (audicao, visao, etc)
        for folder_name in os.listdir(modules_dir):
            folder_path = os.path.join(modules_dir, folder_name)
            
            # Ignora arquivos soltos e pastas ocultas (__pycache__)
            if os.path.isdir(folder_path) and not folder_name.startswith("__"):
                self._load_single_module(folder_name)

        print(f"[MOD_MANAGER] Total de módulos carregados: {len(self.modules)}")

    def _load_single_module(self, module_name):
        try:
            # Tenta importar: modules.audicao.stt_mod (exemplo)
            module_pkg = importlib.import_module(f"modules.{module_name}")

            # Procura o arquivo principal dentro do pacote
            target_file = None
            for f in os.listdir(os.path.join("modules", module_name)):
                if f.endswith("_mod.py"):
                    target_file = f[:-3]  # Remove .py
                    break

            if target_file:
                full_import_name = f"modules.{module_name}.{target_file}"
                mod_lib = importlib.import_module(full_import_name)

                for name, obj in inspect.getmembers(mod_lib):
                    if inspect.isclass(obj) and hasattr(obj, "process"):
                        instance = obj(self.core_context)
                        # Compatibilidade: lista e mapas
                        self.modules.append(instance)
                        self.module_map[instance.name.lower()] = instance

                        # Registra triggers
                        if hasattr(instance, "triggers"):
                            for trigger in instance.triggers:
                                self.trigger_map[trigger.lower()] = instance

                        print(f"   [OK] Módulo carregado: {instance.name}")
                        return

        except Exception as e:
            print(f"   [FALHA] Erro ao carregar '{module_name}': {e}")

    def _format_history(self):
        """Formata o histórico em texto para envio ao Brain."""
        if not self.chat_history:
            return ""
        lines = []
        for msg in self.chat_history:
            if msg.get("role") == "user":
                lines.append(f"Usuário: {msg.get('content')}")
            else:
                lines.append(f"Aeon: {msg.get('content')}")
        return "\n".join(lines)

    def _append_to_history(self, role, content):
        self.chat_history.append({"role": role, "content": content})
        # FIFO cleanup
        while len(self.chat_history) > self.max_history * 2:
            self.chat_history.pop(0)

    def route_command(self, text):
        """Recebe o texto do usuário, tenta módulos locais e depois consulta o Brain."""
        text_lower = text.lower()

        # 1. Checa triggers rápidos
        for trigger, module_instance in self.trigger_map.items():
            if trigger in text_lower:
                try:
                    return module_instance.process(text)
                except Exception as e:
                    return f"Erro no módulo {module_instance.name}: {e}"

        # 2. Se não houver módulo local, consulta o Brain (se existir)
        brain = self.core_context.get("brain") if self.core_context else None
        historico_txt = self._format_history()

        if brain:
            ai_decision = brain.pensar(prompt=text, historico_txt=historico_txt, user_prefs={})

            # Interpreta a decisão da IA
            try:
                if isinstance(ai_decision, dict):
                    # Chamadas de ferramenta
                    if ai_decision.get("tool_name"):
                        tool = ai_decision["tool_name"]
                        params = ai_decision.get("parameters", {})

                        try:
                            mod_name, func_name = tool.split(".")
                        except ValueError:
                            return "formato de ferramenta inválido"

                        mod = self.module_map.get(mod_name.lower())
                        if not mod:
                            return "ferramenta inexistente"

                        # Chama método com parâmetros
                        if hasattr(mod, func_name):
                            result = getattr(mod, func_name)(**params)
                            # Salva histórico
                            self._append_to_history("user", text)
                            self._append_to_history("assistant", str(result))
                            return result
                        else:
                            # Ferramenta não existe no módulo
                            resp = "ferramenta inexistente"
                            self._append_to_history("user", text)
                            self._append_to_history("assistant", resp)
                            return resp

                    # Fallback de conversa
                    if ai_decision.get("fallback"):
                        resp = ai_decision.get("fallback")
                        self._append_to_history("user", text)
                        self._append_to_history("assistant", resp)
                        return resp

                # Se a IA retornou uma string (conversação)
                if isinstance(ai_decision, str):
                    self._append_to_history("user", text)
                    self._append_to_history("assistant", ai_decision)
                    return ai_decision

                # Default
                return str(ai_decision)
            except Exception as e:
                return f"Erro ao processar decisão da IA: {e}"

        # Sem brain e sem módulo -> None
        return None

    def executar_ferramenta(self, tool_name, param):
        """Executa uma ferramenta pedida pelo Cérebro (JSON)"""
        # Formato esperado: "Visao.process" ou "Sistema.criar_arquivo"
        try:
            mod_name, func_name = tool_name.split(".")
            
            # Acha o módulo (ignora case)
            module = None
            for name, mod in self.modules.items():
                if name.lower() == mod_name.lower():
                    module = mod
                    break
            
            if not module:
                return f"Ferramenta desconhecida: {mod_name}"
            
            # Tenta chamar a função
            if hasattr(module, func_name):
                method = getattr(module, func_name)
                return method(param)
            else:
                # Se não achar a função específica, tenta passar pro process() genérico
                return module.process(f"{func_name} {param}")
                
        except Exception as e:
            return f"Erro ao executar ferramenta: {e}"