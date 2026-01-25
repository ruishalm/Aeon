import json
from pathlib import Path
import os

class ConfigManager:
    """
    Gerencia o carregamento e salvamento de todos os arquivos de configuração
    e dados persistentes do Aeon, como sistema, tarefas e memória.
    """
    def __init__(self, storage_path=None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Constrói o caminho para a pasta 'bagagem' a partir da localização deste arquivo.
            # __file__ -> .../AeonProject/core/config_manager.py
            # parent -> .../AeonProject/core/
            # parent -> .../AeonProject/
            # 'bagagem' -> .../AeonProject/bagagem/
            base_path = Path(__file__).resolve().parent.parent
            self.storage_path = base_path / "bagagem"

        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        print(f"[CONFIG] Pasta de dados (Bagagem): {self.storage_path}")
        
        self.sys_path = self.storage_path / "system.json"
        self.tasks_path = self.storage_path / "tasks.json"
        self.mem_path = self.storage_path / "memoria.json"
        self.history_path = self.storage_path / "historico.json"

        self.system_data = self._load_json(self.sys_path, default={"apps": {}, "routines": {}, "triggers": [], "themes": {}})
        
        # Se o arquivo não existir ou não tiver a chave, cria/avisa
        if not self.sys_path.exists() or "GROQ_KEY" not in self.system_data:
            print(f"\n{'='*60}")
            print(f"[CONFIG] ARQUIVO DE SISTEMA CRIADO/CARREGADO EM:\n   {self.sys_path}")
            print(f"[CONFIG] >> COLOQUE SUA GROQ_KEY DENTRO DESTE ARQUIVO! <<")
            print(f"{'='*60}\n")
            if not self.sys_path.exists():
                self.system_data["GROQ_KEY"] = ""
                self._save_json(self.sys_path, self.system_data)

        self.tasks = self._load_json(self.tasks_path, default=[])
        self.memory = self._load_json(self.mem_path, default=[])
        self.history = self._load_json(self.history_path, default={"conversations": [], "last_context": ""})
        
        # Alias para compatibilidade com componentes legados (como Brain)
        # que esperam um dicionário de configuração direto, em vez de usar
        # os métodos `get_system_data`. Idealmente, seria refatorado no futuro.
        self.config = self.system_data

    def _load_json(self, file_path, default=None):
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return default if default is not None else {}
        return default if default is not None else {}

    def _save_json(self, file_path, data):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    # --- Métodos do Sistema ---
    def get_system_data(self, key, default=None):
        return self.system_data.get(key, default)

    def set_system_data(self, key, value):
        self.system_data[key] = value
        self._save_json(self.sys_path, self.system_data)

    # --- Métodos de Tarefas (TaskManager) ---
    def get_tasks(self):
        return self.tasks

    def add_task(self, task_data):
        self.tasks.append(task_data)
        self._save_json(self.tasks_path, self.tasks)

    def save_tasks(self):
        self._save_json(self.tasks_path, self.tasks)

    # --- Métodos de Memória (Conversa) ---
    def get_memory(self):
        return self.memory
    
    def add_to_memory(self, user_input, aeon_response, timestamp):
        self.memory.append({"user": user_input, "aeon": aeon_response, "time": str(timestamp)})
        # Salva apenas as últimas 20 interações
        self._save_json(self.mem_path, self.memory[-20:])

    # --- Métodos de Histórico (Contexto Persistente) ---
    def get_history(self):
        """Retorna o histórico completo de conversas"""
        return self.history.get("conversations", [])
    
    def add_to_history(self, user_input, aeon_response):
        """Adiciona uma interação ao histórico"""
        import datetime
        interaction = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user": user_input,
            "aeon": aeon_response
        }
        self.history["conversations"].append(interaction)
        # Mantém apenas as últimas 100 conversas
        if len(self.history["conversations"]) > 100:
            self.history["conversations"] = self.history["conversations"][-100:]
        self._save_json(self.history_path, self.history)
    
    def get_context_summary(self, num_previous=5):
        """
        Retorna um RESUMO dos tópicos discutidos (para passar ao Brain).
        Não retorna mensagens inteiras, apenas temas.
        """
        hist = self.history.get("conversations", [])
        if not hist:
            return "Nenhuma conversa anterior."
        
        # Pega últimas N conversas
        recent = hist[-num_previous:]
        
        # Cria um resumo dos tópicos
        summary = "Conversas anteriores desta sessão:\n"
        for i, conv in enumerate(recent, 1):
            user = conv.get('user', '?')[:50]  # Primeira 50 chars
            summary += f"  {i}. Usuário perguntou sobre: {user}...\n"
        
        return summary
    
    def get_last_context(self):
        """Retorna o último contexto salvo"""
        return self.history.get("last_context", "")
    
    def save_context(self, context):
        """Salva contexto atual para próximas sessões"""
        self.history["last_context"] = context
        self._save_json(self.history_path, self.history)