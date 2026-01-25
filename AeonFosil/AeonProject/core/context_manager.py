import json
import time
import threading
from pathlib import Path

class ContextManager:
    """
    O 'Quadro Branco' do Aeon (Thread-Safe).
    Permite que módulos compartilhem dados entre si sem acoplamento.
    Exemplo: Visão salva 'erro_lido', Dev lê 'erro_lido'.
    """
    def __init__(self):
        self.data = {}
        self.metadata = {}  # Para guardar timestamps (TTL)
        self._lock = threading.Lock()

    def set(self, key: str, value, ttl: int = None):
        """
        Salva um dado no contexto de forma segura.
        Args:
            key: Nome da chave (ex: 'clipboard_content')
            value: O valor (pode ser qualquer objeto)
            ttl: (Opcional) Tempo de vida em segundos. Se passar, o dado expira.
        """
        with self._lock:
            self.data[key] = value
            self.metadata[key] = {
                "created_at": time.time(),
                "ttl": ttl
            }
        # A limpeza é chamada fora do lock para evitar deadlocks se a limpeza
        # precisar chamar outro método que também usa o lock.
        self.cleanup()

    def get(self, key: str):
        """
        Recupera um dado de forma segura. Retorna None se não existir ou tiver expirado.
        """
        with self._lock:
            if key not in self.data:
                return None
            
            meta = self.metadata.get(key)
            if meta and meta["ttl"]:
                if time.time() - meta["created_at"] > meta["ttl"]:
                    self._cleanup_key(key) # Usa método interno para remover
                    return None
            
            return self.data.get(key)

    def _cleanup_key(self, key: str):
        """Método auxiliar para remover uma chave específica (deve ser chamado dentro de um lock)."""
        if key in self.data:
            del self.data[key]
        if key in self.metadata:
            del self.metadata[key]

    def cleanup(self):
        """Remove todas as chaves expiradas (Garbage Collector)."""
        now = time.time()
        expired = []
        # Primeiro, coleta as chaves a serem removidas sem modificar o dict
        with self._lock:
            for key, meta in self.metadata.items():
                if meta.get("ttl") and now - meta["created_at"] > meta["ttl"]:
                    expired.append(key)
        
        # Depois, remove as chaves encontradas
        if expired:
            with self._lock:
                for key in expired:
                    self._cleanup_key(key)
            print(f"[CONTEXT] Limpeza: {len(expired)} itens removidos.")

    def get_all(self):
        """Retorna uma cópia do contexto atual (útil para debug)."""
        self.cleanup()
        with self._lock:
            return self.data.copy()

    def save_snapshot(self, path=None):
        """Salva o estado atual em JSON para persistência entre reboots."""
        self.cleanup()
        
        if path:
            filepath = Path(path)
        else:
            filepath = Path(__file__).resolve().parent.parent / "bagagem" / "memory_dump.json"
        
        with self._lock:
            # Filtra apenas dados serializáveis
            serializable_data = {
                k: v for k, v in self.data.items() 
                if isinstance(v, (str, int, float, bool, list, dict, type(None)))
            }

        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[CONTEXT] Erro ao salvar snapshot: {e}")
            return False

    def load_snapshot(self, path=None):
        """Carrega estado anterior do JSON."""
        if path:
            filepath = Path(path)
        else:
            filepath = Path(__file__).resolve().parent.parent / "bagagem" / "memory_dump.json"

        if not filepath.exists():
            return False
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            
            with self._lock:
                self.data.update(loaded)
            return True
        except Exception as e:
            print(f"[CONTEXT] Erro ao carregar snapshot: {e}")
            return False