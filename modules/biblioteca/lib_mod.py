import os
import re
import threading
import shutil
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import List, Dict, Optional, Any
from modules.base_module import AeonModule

# SAFE IMPORTS
try:
    from googlesearch import search
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

def log_display(msg):
    print(f"[LibMod] {msg}")

class BibliotecaModule(AeonModule):
    """
    Modulo para gerenciar e pesquisar na biblioteca de conhecimento local do Aeon.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Biblioteca"
        self.dependencies = ["io_handler", "context"]
        self.triggers = ["livro", "livros", "biblioteca", "ler"]
        
        base_dir = Path(__file__).resolve().parent
        self.gaveta_path = base_dir / "livros" / "gaveta"
        self.estante_path = base_dir / "livros" / "Estante"
        
        self.gaveta_path.mkdir(parents=True, exist_ok=True)
        self.estante_path.mkdir(parents=True, exist_ok=True)

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "Biblioteca.pesquisar_livros",
                    "description": "Pesquisa um topico ou termo em todos os livros da biblioteca e retorna trechos relevantes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": { "type": "string", "description": "O topico, termo ou pergunta a ser pesquisado." }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Biblioteca.listar_livros",
                    "description": "Retorna uma lista com os titulos de todos os livros disponiveis na Estante.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Biblioteca.baixar_livro",
                    "description": "Busca e baixa um livro do Projeto Gutenberg (em ingles) e o salva na biblioteca.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "titulo": { "type": "string", "description": "O titulo do livro a ser baixado." }
                        },
                        "required": ["titulo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Biblioteca.apagar_livro",
                    "description": "Apaga um livro da 'gaveta' (livros nao processados) ou da 'estante' (biblioteca principal).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome_livro": { "type": "string", "description": "O titulo ou nome do arquivo do livro a ser apagado." },
                            "local": { "type": "string", "enum": ["gaveta", "estante"], "description": "O local de onde apagar o livro. Padrao: 'estante'." }
                        },
                        "required": ["nome_livro"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Biblioteca.extrair_textos_gaveta",
                    "description": "Processa todos os arquivos da 'gaveta' (area de entrada) e os move para a 'estante' (biblioteca principal).",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

    def process(self, command: str) -> str:
        # A logica principal agora e feita pela IA.
        # Este metodo serve como fallback para comandos de bypass.
        if "listar" in command:
            return self.listar_livros()
        if "processar" in command or "organizar" in command:
            return self.extrair_textos_gaveta()
        return "Modulo Biblioteca ativo. A IA agora pode usar minhas ferramentas para pesquisar, listar, baixar ou apagar livros."

    # --- METODOS DE FERRAMENTA (Usados pela IA) ---

    def pesquisar_livros(self, query: str, max_results: int = 5) -> str:
        log_display(f"Pesquisando livros por: '{query}'")
        query_lower = query.lower()
        found_snippets = []
        
        for book_file in self.estante_path.glob("*.txt"):
            if len(found_snippets) >= max_results: break
            try:
                content = book_file.read_text(encoding='utf-8')
                if query_lower in content.lower():
                    index = content.lower().find(query_lower)
                    start = max(0, index - 200)
                    end = min(len(content), index + len(query) + 200)
                    snippet = content[start:end].strip()
                    found_snippets.append(f"Do livro '{book_file.stem}':\n\"...{snippet}...\"")
            except Exception as e:
                log_display(f"Erro ao ler o livro {book_file.name}: {e}")

        if not found_snippets: return f"Nao encontrei nada sobre '{query}' na minha biblioteca."
            
        log_display(f"Encontrados {len(found_snippets)} trechos relevantes.")
        return "Encontrei os seguintes trechos relevantes na biblioteca:\n\n" + "\n\n".join(found_snippets)

    def listar_livros(self) -> str:
        livros = [p.stem for p in self.estante_path.glob("*.txt")]
        return "Os livros na sua biblioteca sao: " + ", ".join(livros) if livros else "Sua biblioteca esta vazia."

    def baixar_livro(self, titulo: str) -> str:
        io_handler = self.core_context.get("io_handler")
        threading.Thread(target=self._baixar_livro_thread, args=(titulo, io_handler)).start()
        return f"Certo. A busca e download do livro '{titulo}' foi iniciada em segundo plano."

    def apagar_livro(self, nome_livro: str, local: str = "estante") -> str:
        path = self.estante_path if local == "estante" else self.gaveta_path
        
        target_file = next(path.glob(f"{nome_livro}*"), None) # Busca flexivel
        if not target_file or not target_file.exists():
            return f"Nao encontrei o livro '{nome_livro}' em '{local}'."
        
        try:
            nome_real = target_file.name
            target_file.unlink()
            self._update_context()
            return f"O livro '{nome_real}' foi apagado de '{local}'."
        except Exception as e:
            return f"Ocorreu um erro ao apagar o livro: {e}"

    def extrair_textos_gaveta(self) -> str:
        processed, errors = 0, 0
        log_display("Iniciando extracao de textos da Gaveta para a Estante...")
        for file_path in self.gaveta_path.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() == ".txt":
                try:
                    shutil.move(str(file_path), self.estante_path / file_path.name)
                    processed += 1
                except Exception as e:
                    log_display(f"Erro ao mover {file_path.name}: {e}")
                    errors += 1
        self._update_context()
        return f"Processamento concluido. {processed} livros movidos para a Estante. {errors} erros."

    # --- METODOS DE SUPORTE (Nao expostos como ferramentas) ---

    def _update_context(self):
        ctx = self.core_context.get("context")
        if ctx:
            livros = [p.stem for p in self.estante_path.glob("*.txt")]
            ctx.set("library_books", livros)

    def _baixar_livro_thread(self, titulo, io_handler):
        try:
            from googlesearch import search
            import requests
        except ImportError:
            io_handler.falar("Erro: Dependencias de internet nao estao instaladas para baixar livros.")
            return

        try:
            log_display(f"Buscando livro: {titulo}")
            query = f'"{titulo}" filetype:txt site:gutenberg.org'
            urls = list(search(query, num_results=1, lang="en"))
            
            if not urls:
                io_handler.falar(f"Nao encontrei o livro '{titulo}' no Projeto Gutenberg.")
                return
            
            url = urls[0]
            log_display(f"Encontrado: {url}")
            
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            response.raise_for_status()
            book_content = response.content.decode('utf-8', errors='replace')
            
            safe_title = re.sub(r'[\\/*?:\"<>|]', "", titulo)
            file_path = self.gaveta_path / f"{safe_title}.txt"
            file_path.write_text(book_content, encoding='utf-8')
                
            self._update_context()
            io_handler.falar(f"O livro '{titulo}' foi baixado e salvo na sua gaveta. Diga 'processar livros' para move-lo para a estante.")
        except Exception as e:
            log_display(f"Erro ao baixar livro: {e}")
            io_handler.falar(f"Ocorreu um erro ao tentar baixar o livro.")
    
    # Funcoes antigas mantidas para referencia ou uso interno, mas nao como ferramentas primarias
    def get_available_books(self) -> List[str]:
        return [p.stem for p in self.estante_path.glob("*.txt")]

    def get_book_content(self, title: str) -> Optional[str]:
        try:
            target_file = next(self.estante_path.glob(f"{title}.txt"), None)
            if target_file and target_file.exists():
                return target_file.read_text(encoding='utf-8')
            return None
        except Exception:
            return None