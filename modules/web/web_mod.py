from modules.base_module import AeonModule
from typing import List, Dict
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import feedparser
import re

# Suposicao: um logger sera passado pelo core_context
def log_display(msg):
    print(f"[WebMod] {msg}")

class WebModule(AeonModule):
    """
    Modulo para interagir com a web:
    - Pesquisas gerais
    - Busca de clima
    - Leitura de noticias RSS
    - Resumo de URLs
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Web"
        self.triggers = [
            "pesquise por", "procure por", "o que e", "quem e",
            "tempo", "clima", "noticias", "manchetes",
            "arquive o site", "http:", "https://", "www."
        ]

    @property
    def dependencies(self) -> List[str]:
        """Web depende de brain para processamento e biblioteca para arquivamento."""
        return ["brain", "biblioteca"]

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do modulo."""
        return {
            "version": "2.0.0",
            "author": "Aeon Core",
            "description": "Interacao com web: pesquisas, noticias, clima, resumos de URLs"
        }

    def on_load(self) -> bool:
        """Inicializa o modulo - valida acesso a brain."""
        brain = self.core_context.get("brain")
        if not brain:
            print("[WebModule] Erro: brain nao encontrado")
            return False
        return True

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        return True

    def process(self, command: str) -> str:
        brain = self.core_context.get("brain")
        if not brain: return "Cerebro nao encontrado."

        cmd_lower = command.lower()

        # 1. Comando de arquivamento (mais especifico)
        if cmd_lower.startswith("arquive o site"):
            url = command.replace("arquive o site", "").strip()
            if not url.startswith("http"):
                return "Por favor, forneca uma URL valida para arquivar."
            
            log_display(f"Iniciando arquivamento do site: {url}")
            biblioteca = self.core_context.get("biblioteca")
            if not biblioteca:
                return "Modulo Biblioteca nao encontrado. Nao posso arquivar."
            
            titulo, conteudo = self.web_search(url)

            if titulo == "Erro":
                return conteudo # Retorna a mensagem de erro

            if not conteudo:
                return f"Nao consegui extrair conteudo do site {url}."

            return biblioteca.arquivar_texto(titulo, conteudo)

        # 2. Pesquisa na Web
        search_triggers = ["pesquise por", "procure por", "o que e", "quem e"]
        if any(cmd_lower.startswith(t) for t in search_triggers):
            query = command
            for t in search_triggers:
                query = query.replace(t, "", 1)
            query = query.strip()
            
            try:
                titulo, contexto = self.web_search(query) # Ignoramos o titulo aqui
                if not contexto: return "Nao encontrei conteudo para essa pesquisa."
                if "erro ao processar" in contexto: return contexto
                
                prompt_final = f"Com base no seguinte texto, responda de forma concisa a pergunta: '{query}'\n\nTexto: {contexto}"
                return brain.pensar(prompt_final)
            except (IndexError, TypeError, AttributeError) as e:
                log_display(f"Erro ao processar pesquisa: {e}")
                return "Desculpe, tive dificuldade em processar a pesquisa. Tente de novo."

        # 3. Resumo de URL (generico)
        if "http:" in cmd_lower or "https:" in cmd_lower or "www." in cmd_lower:
            match = re.search(r'(https?://[^\s]+)', cmd_lower)
            if match:
                url = match.group(0)
                _, contexto = self.web_search(url) # Ignoramos o titulo aqui
                if not contexto: return f"Nao consegui extrair conteudo do site {url}."
                if "erro ao processar" in contexto: return contexto

                prompt_final = f"Resuma o seguinte texto de forma concisa:\n\n{contexto}"
                return brain.pensar(prompt_final)

        # 4. Outros comandos (Clima, Noticias)
        if "tempo em" in cmd_lower or "clima em" in cmd_lower:
            cidade = cmd_lower.split(" em ")[-1].strip()
            return self.obter_clima(cidade)
        elif "como esta o tempo" in cmd_lower or "previsao do tempo" in cmd_lower:
            return self.obter_clima()

        if "noticias" in cmd_lower or "manchetes" in cmd_lower:
            fonte = "G1"
            for f in self.rss_feeds.keys():
                if f.lower() in cmd_lower:
                    fonte = f
                    break
            return self.obter_noticias(fonte)

        return ""

    def web_search(self, query: str) -> (str, str):
        """Busca uma query ou extrai titulo e conteudo de uma URL. Retorna (titulo, conteudo)."""
        log_display(f"Processando Web: {query[:60]}")
        try:
            if query.startswith("http"):
                url = query
            else:
                search_results = list(search(query, num_results=1, lang="pt"))
                if not search_results:
                    return "Erro", "Nenhum resultado encontrado para essa busca."
                url = search_results[0]
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extrai o titulo
            title = soup.find('title').get_text() if soup.find('title') else "Sem Titulo"
            
            # Limpa o conteudo
            for tag in ['nav', 'footer', 'aside', 'script', 'style', 'header', 'form']:
                for s in soup(tag):
                    s.decompose()
            
            # Pega o texto de tags relevantes, como 'p', 'article', 'h1', 'h2', 'h3'
            text_blocks = [p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'article'])]
            text_content = ' '.join(text_blocks)
            text_content = re.sub(r'\s+', ' ', text_content).strip() # Limpa espacos em branco
            
            return title.strip(), text_content[:8000] # Limite maior para arquivamento
            
        except Exception as e:
            error_msg = f"Ocorreu um erro ao processar a requisicao web: {e}"
            log_display(error_msg)
            return "Erro", error_msg

    def obter_clima(self, cidade: str = '') -> str:
        try:
            if not cidade: # Autodetecta por IP
                ip_info = requests.get('https://ipinfo.io/json').json()
                cidade = ip_info.get('city', 'Sao Paulo')
            
            url = f"https://wttr.in/{cidade.replace(' ', '+')}?format=j1"
            data = requests.get(url).json()
            
            condicao_atual = data['current_condition'][0]
            temp = condicao_atual['temp_C']
            sensacao = condicao_atual['FeelsLikeC']
            descricao = condicao_atual['lang_pt'][0]['value']
            
            return f"O tempo em {data['nearest_area'][0]['areaName'][0]['value']} e: {descricao}, {temp} graus com sensacao de {sensacao}."
        except Exception as e:
            return "Nao consegui verificar o tempo."

    def obter_noticias(self, fonte: str = "G1") -> str:
        url_rss = self.rss_feeds.get(fonte.upper())
        if not url_rss:
            return f"Fonte de noticias '{fonte}' nao encontrada."

        try:
            feed = feedparser.parse(url_rss)
            manchetes = "; ".join(entry.title for entry in feed.entries[:3])
            return f"As manchetes do {fonte} sao: {manchetes}"
        except Exception as e:
            return "Tive um problema ao buscar as noticias."
