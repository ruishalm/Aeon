import os
import chromadb
from chromadb.utils import embedding_functions
import uuid
import time

class VectorMemory:
    """
    Memória de Longo Prazo usando ChromaDB.
    Transforma conversas em vetores para busca semântica.
    """
    def __init__(self, storage_path):
        self.db_path = os.path.join(storage_path, "vector_db")
        os.makedirs(self.db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Usaremos um modelo de embedding leve que roda localmente
        # Nota: Requer 'pip install sentence-transformers'
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="aeon_long_term_memory",
            embedding_function=self.embed_fn
        )

    def store_interaction(self, user_input, aeon_response):
        """Guarda uma interação no banco vetorial."""
        text_to_embed = f"Usuário: {user_input} | Aeon: {aeon_response}"
        self.collection.add(
            documents=[text_to_embed],
            ids=[str(uuid.uuid4())],
            metadatas=[{"timestamp": time.time()}]
        )

    def retrieve_relevant(self, query, n_results=3):
        """Busca as memórias mais parecidas com a pergunta atual."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            if results and results['documents'] and results['documents'][0]:
                return "\n---\n".join(results['documents'][0])
        except Exception as e:
            print(f"[VECTOR_MEM] Erro na busca: {e}")
        return ""