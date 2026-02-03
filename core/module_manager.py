from modules.base_module import AeonModule
import traceback
import json
from typing import List, Dict, Any

class ModuleManager:
    def __init__(self, core_context):
        self.core = core_context
        self.modules = {}  # Nome -> Instância
        self.triggers = {} # Palavra -> Nome do Módulo
        self.tools_json = [] # JSON para o 'function calling' da IA
        
        # Callbacks para a GUI
        self.on_module_loaded = None
        self.on_all_modules_loaded = None

    def load_modules(self):
        """Carrega módulos da pasta modules/ e notifica a GUI."""
        print("[MOD_MANAGER] INICIANDO CARREGAMENTO DE MÓDULOS...")
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "modules")
        print(f"[MOD_MANAGER] Buscando em: {path}")
        
        if not os.path.exists(path):
            print(f"[MOD_MANAGER] ERRO: O diretório de módulos não existe em '{path}'")
            if self.on_all_modules_loaded:
                self.on_all_modules_loaded()
            return

        module_folders = [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name)) and not name.startswith("__")]
        
        for name in module_folders:
            mod_path = os.path.join(path, name)
            try:
                print(f"[MOD_MANAGER] -> Processando diretório: '{name}'...")
                found_py = False
                for f in os.listdir(mod_path):
                    if f.endswith(".py") and not f.startswith("__"):
                        module_name = f"modules.{name}.{f[:-3]}"
                        
                        print(f"    - Importando '{module_name}'...")
                        lib = importlib.import_module(module_name)
                        
                        # Procura a classe principal do módulo
                        for attr_name in dir(lib):
                            attr = getattr(lib, attr_name)
                            if isinstance(attr, type) and issubclass(attr, AeonModule) and attr is not AeonModule:
                                print(f"    - Instanciando classe '{attr_name}'...")
                                instance = attr(self.core)
                                
                                # Chama o on_load, se existir, e verifica se foi bem-sucedido
                                if hasattr(instance, 'on_load') and not instance.on_load():
                                    print(f"[MOD_MANAGER] [AVISO] 'on_load' do módulo '{instance.name}' retornou False. O módulo não será ativado.")
                                    continue # Pula para o próximo

                                self.modules[instance.name.lower()] = instance
                                print(f"[MOD_MANAGER] + Módulo '{instance.name}' carregado e ATIVADO.")
                                
                                # Registra gatilhos
                                if hasattr(instance, 'triggers'):
                                    for t in instance.triggers:
                                        self.triggers[t.lower()] = instance.name.lower()
                                
                                # Registra ferramentas
                                if hasattr(instance, 'get_tools'):
                                    self.tools_json.extend(instance.get_tools())
                                    
                                if self.on_module_loaded:
                                    self.on_module_loaded(instance.name)
                                    
                                found_py = True
                                break 
                if found_py: break
            except Exception as e:
                print(f"[MOD_MANAGER] ERRO FATAL ao carregar o módulo '{name}': {e}")
                traceback.print_exc(limit=1)
        
        print(f"[MOD_MANAGER] Carregamento concluído. {len(self.modules)} módulos ativos.")
        with open("tools.json", "w", encoding="utf-8") as f:
            json.dump(self.tools_json, f, indent=2, ensure_ascii=False)
            
        if self.on_all_modules_loaded:
            print("[MOD_MANAGER] Notificando GUI que o carregamento terminou.")
            self.on_all_modules_loaded()

    def route_command(self, text: str) -> str:
        brain = self.core.get("brain")
        if not brain:
            return "Erro: Cérebro não detectado."

        # --- Abordagem AI-First ---
        print("[MOD_MANAGER] Delegando ao Cérebro para roteamento inteligente...")
        
        capabilities_str = json.dumps(self.tools_json, ensure_ascii=False, indent=2)
        response_from_brain = brain.pensar(prompt=text, capabilities=capabilities_str)
        
        # 1. Cérebro retornou uma AÇÃO (JSON/Dicionário)
        if isinstance(response_from_brain, dict) and "tool" in response_from_brain:
            print(f"[MOD_MANAGER] Cérebro solicitou ferramenta: {response_from_brain}")
            tool_name = response_from_brain.get("tool")
            params = response_from_brain.get("param")
            return self.executar_ferramenta(tool_name, params)
        
        # 2. Cérebro retornou uma CONVERSA (String não vazia)
        if isinstance(response_from_brain, str) and response_from_brain.strip():
            # Verifica se a resposta não é uma mensagem de erro genérica do cérebro
            if "falharam completamente" not in response_from_brain and "desconectado" not in response_from_brain:
                return response_from_brain

        # 3. --- Fallback para Triggers ---
        # Executado apenas se a IA falhou ou não deu uma resposta útil.
        print("[MOD_MANAGER] IA não respondeu ou falhou. Tentando roteamento por gatilho (fallback)...")
        text_lower = text.lower()
        for trigger, mod_name in self.triggers.items():
            if trigger in text_lower:
                instance = self.modules.get(mod_name)
                if instance and hasattr(instance, 'process'):
                    response = instance.process(text)
                    if response:
                        print(f"[MOD_MANAGER] Gatilho de fallback '{trigger}' acionou o módulo {mod_name}.")
                        return response
        
        # 4. Resposta final se tudo falhar
        return "Não consegui processar seu pedido. Verifique minha conexão ou os módulos."

    def executar_ferramenta(self, tool_name: str, params: Any) -> str:
        try:
            mod_key, func_key = tool_name.split(".")
            target_mod = self.modules.get(mod_key.lower())
            
            if target_mod and hasattr(target_mod, func_key):
                method = getattr(target_mod, func_key)
                
                # Executa o método. Se 'params' for um dict, desempacota. Senão, passa como argumento único.
                if isinstance(params, dict):
                    return method(**params)
                elif params is not None:
                    return method(params)
                else:
                    return method() # Para funções sem parâmetros
            else:
                return f"Ferramenta '{tool_name}' não encontrada ou inválida."
        except Exception as e:
            print(f"[MOD_MANAGER][ERRO] Falha ao executar ferramenta '{tool_name}': {e}")
            traceback.print_exc(limit=2)
            return f"Ocorreu um erro interno ao usar a ferramenta {tool_name}."

    def get_loaded_modules(self) -> List[Any]:
        return list(self.modules.values())
        
    def get_module(self, module_name: str) -> Any:
        """Retorna uma instância de um módulo carregado pelo nome."""
        return self.modules.get(module_name.lower())
        
import importlib