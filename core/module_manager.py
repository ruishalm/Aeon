import os
import importlib
import traceback

class ModuleManager:
    def __init__(self, core_context):
        self.core = core_context
        self.modules = {} # Nome -> Instância
        self.triggers = {} # Palavra -> Nome do Módulo

    def load_modules(self):
        """Carrega módulos da pasta modules/"""
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "modules")
        print(f"[MOD_MANAGER] Buscando em: {path}")
        
        for name in os.listdir(path):
            mod_path = os.path.join(path, name)
            if os.path.isdir(mod_path) and not name.startswith("__"):
                try:
                    # Tenta importar dinamicamente
                    # Espera que o arquivo principal tenha o nome do modulo_mod.py ou similar
                    # Simplificação: procura o primeiro arquivo .py que não seja __init__
                    found_py = False
                    for f in os.listdir(mod_path):
                        if f.endswith(".py") and not f.startswith("__"):
                            module_name = f"modules.{name}.{f[:-3]}"
                            lib = importlib.import_module(module_name)
                            
                            # Procura classe que herda de AeonModule
                            for attr_name in dir(lib):
                                attr = getattr(lib, attr_name)
                                if hasattr(attr, 'is_aeon_module') and attr_name != 'AeonModule':
                                    instance = attr(self.core)
                                    self.modules[instance.name.lower()] = instance
                                    print(f"[MOD_MANAGER] + {instance.name} carregado.")
                                    
                                    # Registra gatilhos (triggers)
                                    if hasattr(instance, 'triggers'):
                                        for t in instance.triggers:
                                            self.triggers[t.lower()] = instance.name.lower()
                                    found_py = True
                                    break
                        if found_py: break
                except Exception as e:
                    print(f"[MOD_MANAGER] Erro ao carregar {name}: {e}")

    def route_command(self, text):
        """
        A LÓGICA DE OURO:
        1. Verifica Trigger Exato (Velocidade máxima).
        2. Se não achar, usa o Cérebro (IA).
        """
        text_lower = text.lower()
        
        # 1. Busca por palavra-chave direta (Old School Mode)
        for trigger, mod_name in self.triggers.items():
            if trigger in text_lower:
                print(f"[MOD_MANAGER] Trigger '{trigger}' detectado -> Módulo {mod_name}")
                instance = self.modules.get(mod_name)
                if instance:
                    resposta = instance.process(text)
                    if resposta: return resposta # Se o módulo lidou, retorna.

        # 2. Se nenhum módulo pegou pelo trigger, usa o Brain
        print("[MOD_MANAGER] Sem trigger direto. Chamando o Cérebro...")
        brain = self.core.get("brain")
        if brain:
            # O Brain decide o que fazer (Texto ou JSON de Ação)
            return brain.pensar(text)
        
        return "Erro: Cérebro não detectado."

    def executar_ferramenta(self, tool_name, param):
        """Executa comando vindo do JSON da IA"""
        # Formato esperado: "Modulo.funcao"
        try:
            mod_key, func_key = tool_name.split(".")
            # Procura módulo (busca flexível)
            target = None
            for nome, instancia in self.modules.items():
                if mod_key.lower() in nome.lower():
                    target = instancia
                    break
            
            if target and hasattr(target, func_key):
                method = getattr(target, func_key)
                return method(param)
            else:
                return f"Ferramenta {tool_name} não encontrada."
        except Exception as e:
            return f"Erro ao executar ferramenta: {e}"