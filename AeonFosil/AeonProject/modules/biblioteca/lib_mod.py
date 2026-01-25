import os
import re
import threading
from typing import List, Dict
from modules.base_module import AeonModule
from googlesearch import search
import requests

# Suposição: um logger e o io_handler serão passados pelo core_context
def log_display(msg):
    print(f"[LibMod] {msg}")

class BibliotecaModule(AeonModule):
    """
    Módulo para gerenciar a biblioteca de livros digitais.
    Permite criar, listar, ler e baixar livros.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Biblioteca"
        self.triggers = ["livro", "livros", "biblioteca"]
        
        # Define o caminho para salvar os livros
        self.books_path = os.path.join("AeonProject", "modules", "biblioteca", "livros")
        os.makedirs(self.books_path, exist_ok=True)

    @property
    def dependencies(self) -> List[str]:
        """Biblioteca depende de io_handler para feedback."""
        return ["io_handler"]

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do módulo."""
        return {
            "version": "2.1.0",
            "author": "Aeon Core",
            "description": "Gerencia biblioteca digital e fornece acesso a textos para outros módulos."
        }

    def on_load(self) -> bool:
        """Inicializa o módulo - cria diretório de livros."""
        try:
            os.makedirs(self.books_path, exist_ok=True)
            self._update_context()
            return True
        except Exception as e:
            print(f"[BibliotecaModule] Erro ao carregar: {e}")
            return False

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        return True
    
    def _baixar_livro_thread(self, titulo, io_handler):
        """Função executada em uma thread para não bloquear a UI."""
        resultado = self.baixar_livro(titulo)
        io_handler.falar(resultado)

    def _update_context(self):
        """Atualiza o contexto compartilhado com o índice da biblioteca."""
        ctx = self.core_context.get("context")
        if ctx:
            ctx.set("library_books", self.get_available_books())

    def get_available_books(self) -> List[str]:
        """Retorna lista de livros disponíveis (API pública para outros módulos)."""
        try:
            if not os.path.exists(self.books_path): return []
            return [f.replace('.txt', '') for f in os.listdir(self.books_path) if f.endswith(".txt")]
        except: return []

    def get_book_content(self, title: str) -> str:
        """Retorna o conteúdo completo de um livro (API pública para outros módulos)."""
        try:
            # Busca flexível pelo arquivo
            target = None
            title_clean = re.sub(r'[\\/*?:"<>|]', "", title).lower()
            
            for f in os.listdir(self.books_path):
                if f.lower().endswith(".txt"):
                    fname = f.replace('.txt', '').lower()
                    if title_clean == fname or title_clean in fname:
                        target = os.path.join(self.books_path, f)
                        break
            
            if target and os.path.exists(target):
                with open(target, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        except Exception:
            return None

    def process(self, command: str) -> str:
        io_handler = self.core_context.get("io_handler")
        if not io_handler: return "IO Handler não encontrado."

        if "crie o livro" in command:
            titulo = command.split("crie o livro")[-1].strip()
            return self.criar_livro(titulo)
            
        elif "baixar livro" in command or "baixe o livro" in command:
            titulo = command.replace("baixar livro", "").replace("baixe o livro", "").strip()
            if titulo:
                # Executa em uma thread para não travar
                threading.Thread(target=self._baixar_livro_thread, args=(titulo, io_handler)).start()
                return f"Ok, vou tentar baixar o livro '{titulo}'. Isso pode levar um momento."
            else:
                return "Não entendi o título do livro que você quer baixar."

        elif "listar livros" in command:
            return self.listar_livros()

        elif "leia o livro" in command or "ler o livro" in command:
            titulo = command.replace("leia o livro", "").replace("ler o livro", "").strip()
            if titulo:
                # A leitura pode ser longa, então é bom ter um retorno imediato
                # A função ler_livro em si já é blocante, mas o TTS irá demorar.
                return self.ler_livro(titulo)
            else:
                return "Não entendi qual livro você quer que eu leia."
        
        return "" # Nenhum comando do módulo foi acionado

    def criar_livro(self, titulo: str) -> str:
        if not titulo:
            return "Não entendi o título do livro que você quer criar."
        try:
            safe_title = re.sub(r'[\\/*?:"<>|]', "", titulo)
            file_path = os.path.join(self.books_path, f"{safe_title}.txt")
            if os.path.exists(file_path):
                return f"O livro '{titulo}' já existe na sua biblioteca."
            else:
                open(file_path, 'w', encoding='utf-8').close() # Cria arquivo vazio
                self._update_context()
                return f"Criei o livro em branco '{titulo}' na sua biblioteca."
        except Exception as e:
            return f"Não consegui criar o livro. Erro: {e}"

    def listar_livros(self) -> str:
        try:
            livros = [f.replace('.txt', '') for f in os.listdir(self.books_path) if f.endswith(".txt")]
            if livros:
                return "Os livros na sua biblioteca são: " + ", ".join(livros)
            else:
                return "Sua biblioteca está vazia."
        except Exception as e:
            return f"Ocorreu um erro ao listar os livros: {e}"

    def ler_livro(self, titulo: str) -> str:
        try:
            safe_title = re.sub(r'[\\/*?:"<>|]', "", titulo)
            file_path = os.path.join(self.books_path, f"{safe_title}.txt")

            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(2000) # Limita para não sobrecarregar o TTS
                if len(content) >= 2000:
                    content += "... O livro é muito longo para ser lido completamente."
                return content if content else f"O livro '{titulo}' está vazio."
            else:
                return f"Não encontrei o livro '{titulo}' na sua biblioteca."
        except Exception as e:
            return f"Ocorreu um erro ao tentar ler o livro: {e}"

    def baixar_livro(self, titulo: str) -> str:
        """Busca um livro no Project Gutenberg e o salva."""
        try:
            log_display(f"Buscando livro: {titulo}")
            query = f'"{titulo}" filetype:txt site:gutenberg.org'
            urls = list(search(query, num_results=1, lang="en"))
            
            if not urls:
                return f"Não encontrei o livro '{titulo}' no Projeto Gutenberg."
            
            url = urls[0]
            log_display(f"Encontrado: {url}")
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            book_content = response.content.decode('utf-8', errors='replace')
            
            safe_title = re.sub(r'[\\/*?:"<>|]', "", titulo)
            file_path = os.path.join(self.books_path, f"{safe_title}.txt")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(book_content)
                
            self._update_context()
            return f"O livro '{titulo}' foi baixado e salvo na sua biblioteca."

        except Exception as e:
            log_display(f"Erro ao baixar livro: {e}")
            return f"Ocorreu um erro ao tentar baixar o livro: {e}"
