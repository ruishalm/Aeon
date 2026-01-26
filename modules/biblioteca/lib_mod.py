import os
import re
import threading
from pathlib import Path
from typing import List, Dict, Optional
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
    Módulo para gerenciar a biblioteca de conhecimento local do Aeon.
    Permite criar, listar, baixar e, mais importante, pesquisar livros
    para fornecer contexto "ground-truth" ao cérebro.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Biblioteca"
        self.triggers = ["livro", "livros", "biblioteca", "pesquise na biblioteca", 
                        "extrair livros", "processar biblioteca", "organizar livros",
                        "processar livro", "extrair livro", "listar gaveta", "gaveta"]
        
        # Caminhos estruturados (Gaveta -> Estante)
        base_dir = Path(__file__).resolve().parent
        self.gaveta_path = base_dir / "livros" / "gaveta"
        self.estante_path = base_dir / "livros" / "Estante"
        
        self.gaveta_path.mkdir(parents=True, exist_ok=True)
        self.estante_path.mkdir(parents=True, exist_ok=True)

    @property
    def dependencies(self) -> List[str]:
        return ["io_handler", "context"]

    @property
    def metadata(self) -> Dict[str, str]:
        return {
            "version": "2.2.0",
            "author": "Aeon Core",
            "description": "Gerencia e pesquisa na biblioteca de conhecimento local para fornecer respostas baseadas em fatos."
        }

    def on_load(self) -> bool:
        installer = self.core_context.get("installer")
        
        if not GOOGLE_AVAILABLE:
            print("[BIBLIOTECA] 'googlesearch' ausente. Tentando instalar...")
            if installer: installer.install_package("googlesearch-python")
                
        if not REQUESTS_AVAILABLE:
            print("[BIBLIOTECA] 'requests' ausente. Tentando instalar...")
            if installer: installer.install_package("requests")

        self._update_context()
        return True

    def _update_context(self):
        """Atualiza o contexto compartilhado com o índice da biblioteca."""
        ctx = self.core_context.get("context")
        if ctx:
            ctx.set("library_books", self.get_available_books())

    def get_available_books(self) -> List[str]:
        """Retorna lista de livros disponíveis."""
        return [p.stem for p in self.estante_path.glob("*.txt")]

    def get_book_content(self, title: str) -> Optional[str]:
        """Retorna o conteúdo completo de um livro."""
        try:
            target_file = next(self.estante_path.glob(f"{title}.txt"), None)
            if target_file and target_file.exists():
                return target_file.read_text(encoding='utf-8')
            return None
        except Exception:
            return None

    def pesquisar_livros(self, query: str, max_results: int = 5) -> Optional[str]:
        """
        Pesquisa em todos os livros por uma query.
        Esta é a "âncora" principal do módulo, fornecendo contexto local.
        Retorna uma string formatada com os resultados ou None.
        """
        log_display(f"Pesquisando livros por: '{query}'")
        query_lower = query.lower()
        found_snippets = []
        
        # Procura em arquivos .txt e .md
        for book_file in self.estante_path.glob("*.txt"):
            try:
                content = book_file.read_text(encoding='utf-8')
                if query_lower in content.lower():
                    # Para simplificar, pegamos um trecho ao redor da primeira ocorrência
                    # Uma implementação mais avançada usaria um índice ou regex.
                    index = content.lower().find(query_lower)
                    start = max(0, index - 150)
                    end = min(len(content), index + len(query) + 150)
                    snippet = content[start:end]
                    
                    found_snippets.append(f"Do livro '{book_file.stem}':\n\"...{snippet}...\"")
                    
                    if len(found_snippets) >= max_results:
                        break 
            except Exception as e:
                log_display(f"Erro ao ler o livro {book_file.name}: {e}")
            
            if len(found_snippets) >= max_results:
                break

        if not found_snippets:
            return None
            
        log_display(f"Encontrados {len(found_snippets)} trechos relevantes.")
        return "\n\n".join(found_snippets)


    def process(self, command: str) -> str:
        io_handler = self.core_context.get("io_handler")
        if not io_handler: return "IO Handler não encontrado."

        if "pesquise na biblioteca sobre" in command:
            query = command.split("pesquise na biblioteca sobre")[-1].strip()
            if not query:
                return "O que você gostaria que eu pesquisasse na biblioteca?"
            
            resultados = self.pesquisar_livros(query)
            return resultados if resultados else "Não encontrei nada sobre isso na minha biblioteca."

        if "crie o livro" in command:
            titulo = command.split("crie o livro")[-1].strip()
            return self.criar_livro(titulo)
            
        elif "baixar livro" in command or "baixe o livro" in command:
            titulo = command.replace("baixar livro", "").replace("baixe o livro", "").strip()
            if titulo:
                threading.Thread(target=self._baixar_livro_thread, args=(titulo, io_handler)).start()
                return f"Ok, vou tentar baixar o livro '{titulo}'. Isso pode levar um momento."
            else:
                return "Qual livro você quer baixar?"

        elif "listar livros" in command:
            return self.listar_livros()

        elif "leia o livro" in command or "ler o livro" in command:
            titulo = command.replace("leia o livro", "").replace("ler o livro", "").strip()
            return self.ler_livro(titulo) if titulo else "Qual livro você quer que eu leia?"

        elif "listar gaveta" in command or "abrir gaveta" in command or "ver gaveta" in command:
            return self.listar_gaveta()

        elif "processar livro" in command or "extrair livro" in command:
            # Tenta extrair o índice numérico do comando
            match = re.search(r'(?:processar|extrair) livro (\d+)', command)
            if match:
                try:
                    idx = int(match.group(1))
                    return self.extrair_livro_por_indice(idx)
                except ValueError:
                    return "Número do livro inválido."
            
        elif any(k in command for k in ["extrair livros", "processar biblioteca", "organizar livros"]):
            return self.extrair_textos_gaveta()
        
        return ""

    def criar_livro(self, titulo: str) -> str:
        if not titulo: return "Por favor, especifique um título para o livro."
        
        safe_title = re.sub(r'[\\/*?:"<>|]', "", titulo)
        file_path = self.gaveta_path / f"{safe_title}.txt"
        
        if file_path.exists():
            return f"O livro '{titulo}' já existe."
        
        file_path.touch()
        self._update_context()
        return f"Criei o livro em branco '{titulo}'."

    def listar_livros(self) -> str:
        livros = self.get_available_books()
        return "Os livros na sua biblioteca são: " + ", ".join(livros) if livros else "Sua biblioteca está vazia."

    def ler_livro(self, titulo: str) -> str:
        conteudo = self.get_book_content(titulo)
        if conteudo is None:
            return f"Não encontrei o livro '{titulo}'."
            
        if not conteudo.strip():
            return f"O livro '{titulo}' está vazio."
            
        # Limita a leitura para não sobrecarregar o TTS
        if len(conteudo) > 2000:
            return conteudo[:2000] + "... O livro é muito longo para ser lido completamente."
        return conteudo

    def _baixar_livro_thread(self, titulo, io_handler):
        """Função executada em uma thread para não bloquear a UI."""
        resultado = self.baixar_livro(titulo)
        io_handler.falar(resultado)

    def baixar_livro(self, titulo: str) -> str:
        """Busca um livro no Project Gutenberg e o salva."""
        # Tenta importar localmente caso tenha sido instalado em tempo de execução
        try:
            from googlesearch import search
            import requests
        except ImportError:
            return "Erro: Dependências de internet (googlesearch, requests) não instaladas."

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
            file_path = self.gaveta_path / f"{safe_title}.txt"
            
            file_path.write_text(book_content, encoding='utf-8')
                
            self._update_context()
            return f"O livro '{titulo}' foi baixado e salvo na sua biblioteca."

        except Exception as e:
            log_display(f"Erro ao baixar livro: {e}")
            return f"Ocorreu um erro ao tentar baixar o livro: {e}"

    def extrair_textos_gaveta(self) -> str:
        """
        Processa os livros da 'gaveta' (input) e salva o texto limpo na 'Estante' (output).
        """
        processed = 0
        errors = 0
        
        log_display("Iniciando extração de textos da Gaveta para a Estante...")
        
        for file_path in self.gaveta_path.glob("*"):
            if file_path.is_file():
                try:
                    # Suporte atual: .txt (Futuramente PDF/EPUB)
                    if file_path.suffix.lower() == ".txt":
                        content = file_path.read_text(encoding='utf-8', errors='replace')
                        dest_path = self.estante_path / file_path.name
                        dest_path.write_text(content, encoding='utf-8')
                        processed += 1
                except Exception as e:
                    log_display(f"Erro ao extrair {file_path.name}: {e}")
                    errors += 1
        
        self._update_context()
        return f"Processamento concluído. {processed} livros extraídos para a Estante. {errors} erros."

    def listar_gaveta(self) -> str:
        """Lista os arquivos na gaveta com índices para processamento individual."""
        files = sorted([f for f in self.gaveta_path.glob("*") if f.is_file()])
        if not files:
            return "A gaveta de livros está vazia."
        
        lista = []
        for i, f in enumerate(files, 1):
            lista.append(f"{i}. {f.name}")
        return "Livros na Gaveta (Input):\n" + "\n".join(lista)

    def extrair_livro_por_indice(self, indice: int) -> str:
        """Processa um único livro da gaveta baseado no índice da listagem."""
        files = sorted([f for f in self.gaveta_path.glob("*") if f.is_file()])
        
        if not files:
            return "A gaveta está vazia."
        
        if indice < 1 or indice > len(files):
            return f"Índice {indice} inválido. Escolha um número entre 1 e {len(files)}."
            
        target_file = files[indice - 1]
        
        # Reutiliza a lógica de extração (atualmente suporta .txt)
        if target_file.suffix.lower() == ".txt":
            try:
                content = target_file.read_text(encoding='utf-8', errors='replace')
                dest_path = self.estante_path / target_file.name
                dest_path.write_text(content, encoding='utf-8')
                self._update_context()
                return f"Livro '{target_file.name}' processado com sucesso e movido para a Estante."
            except Exception as e:
                return f"Erro ao processar '{target_file.name}': {e}"
        else:
            return f"O arquivo '{target_file.name}' não é um formato de texto suportado (.txt)."
