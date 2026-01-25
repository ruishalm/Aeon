from abc import ABC, abstractmethod
from typing import List, Dict, Any

class AeonModule(ABC):
    """
    A classe base abstrata para todos os módulos do Aeon.
    """
    
    def __init__(self, core_context: Dict[str, Any]):
        self.core_context = core_context
        self._name = None
        self._triggers = []
        self._dependencies = []
        self._loaded = False

    @property
    def name(self) -> str:
        return getattr(self, '_name', 'Unnamed')
    
    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def triggers(self) -> List[str]:
        return getattr(self, '_triggers', [])
    
    @triggers.setter
    def triggers(self, value: List[str]):
        self._triggers = value

    @property
    def dependencies(self) -> List[str]:
        return self._dependencies
    
    # CORREÇÃO 1: Adicionado Setter para permitir self.dependencies = [...]
    @dependencies.setter
    def dependencies(self, value: List[str]):
        self._dependencies = value

    @property
    def metadata(self) -> Dict[str, str]:
        return {
            "version": "1.0.0",
            "author": "Unknown",
            "description": "Módulo sem descrição"
        }

    @abstractmethod
    def process(self, command: str) -> str:
        raise NotImplementedError

    def check_dependencies(self) -> bool:
        """
        Verifica se dependências (Core ou Outros Módulos) estão disponíveis.
        """
        if not self.dependencies:
            return True
        
        module_manager = self.core_context.get("module_manager")
        
        # Lista de nomes de módulos carregados (se houver)
        loaded_modules = []
        if module_manager and hasattr(module_manager, 'get_loaded_modules'):
            loaded_modules = [m.name.lower() for m in module_manager.get_loaded_modules()]

        for dep in self.dependencies:
            dep_key = dep.lower()
            
            # 1. Verifica no Core Context (Brain, IO, Config, etc.)
            # Nota: main.py deve usar chaves compatíveis (ex: 'brain', 'io_handler')
            if dep_key in self.core_context and self.core_context[dep_key] is not None:
                continue # Achou no Core, próximo
            
            # 2. Verifica se é um Módulo carregado (ex: 'biblioteca' depende de 'web')
            if dep_key in loaded_modules:
                continue # Achou nos módulos, próximo

            # Se chegou aqui, falhou
            print(f"[{self.name}] Dependência ausente: {dep}")
            return False
        
        return True

    def on_load(self) -> bool:
        self._loaded = True
        return True

    def on_unload(self) -> bool:
        self._loaded = False
        return True

    def is_loaded(self) -> bool:
        return self._loaded

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "triggers": self.triggers,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "loaded": self.is_loaded(),
            "dependencies_ok": self.check_dependencies()
        }