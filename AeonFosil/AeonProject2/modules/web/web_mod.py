from modules.base_module import AeonModule
from typing import List, Dict
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import feedparser
import re

# Suposição: um logger será passado pelo core_context
def log_display(msg):
    print(f"[WebMod] {msg}")

class WebModule(AeonModule):
    """
    Módulo para interagir com a web:
    - Pesquisas gerais
    - Busca de clima
    - Leitura de notícias RSS
    - Resumo de URLs
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Web"
        self.triggers = [
            "pesquise por", "procure por", "o que é", "quem é",
            "tempo", "clima", "notícias", "manchetes",
            "http:", "https://", "www."
        ]
        # Fontes de notícias, poderiam vir do config_manager no futuro
        self.rss_feeds = {
            "G1": "https://g1.globo.com/rss/g1/",
            "BBC": "http://feeds.bbci.co.uk/news/rss.xml"
        }

    @property
    def dependencies(self) -> List[str]:
        """Web depende de brain para processamento de respostas."""
        return ["brain"]

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do módulo."""
        return {
            "version": "2.0.0",
            "author": "Aeon Core",
            "description": "Interação com web: pesquisas, notícias, clima, resumos de URLs"
        }

    def on_load(self) -> bool:
        """Inicializa o módulo - valida acesso a brain."""
        brain = self.core_context.get("brain")
        if not brain:
            print("[WebModule] Erro: brain não encontrado")
            return False
        return True

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        return True

    def process(self, command: str) -> str:
        brain = self.core_context.get("brain")
        if not brain: return "Cérebro não encontrado."

        # Pesquisa na Web
        search_triggers = ["pesquise por", "procure por", "o que é", "quem é"]
        if any(command.startswith(t) for t in search_triggers):
            query = command
            for t in search_triggers:
                query = query.replace(t, "", 1) # Apenas a primeira ocorrência
            query = query.strip()
            
            contexto = self.web_search(query)
            if "erro" in contexto.lower(): return contexto
            
            prompt_final = f"Com base no seguinte texto, responda de forma concisa à pergunta: '{query}'\n\nTexto: {contexto}"
            return brain.pensar(prompt_final)

        # Clima
        if "tempo em" in command or "clima em" in command:
            cidade = command.split(" em ")[-1].strip()
            return self.obter_clima(cidade)
        elif "como está o tempo" in command or "previsão do tempo" in command:
            return self.obter_clima() # Tenta autodetectar

        # Notícias
        if "notícias" in command or "manchetes" in command:
            fonte = "G1" # Padrão
            for f in self.rss_feeds.keys():
                if f.lower() in command:
                    fonte = f
                    break
            return self.obter_noticias(fonte)

        # Resumo de URL
        if "http:" in command or "https:" in command or "www." in command:
            # Extrai a URL do comando
            match = re.search(r'(https?://[^\s]+)', command)
            if match:
                url = match.group(0)
                contexto = self.web_search(url)
                if "erro" in contexto.lower(): return contexto

                prompt_final = f"Resuma o seguinte texto de forma concisa:\n\n{contexto}"
                return brain.pensar(prompt_final)

        return ""

    def web_search(self, query: str) -> str:
        """Busca uma query ou extrai conteúdo de uma URL."""
        log_display(f"Processando Web: {query[:60]}")
        try:
            url = query if query.startswith("http") else list(search(query, num_results=1, lang="pt"))[0]
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in ['nav', 'footer', 'aside', 'script', 'style']:
                for s in soup(tag):
                    s.decompose()
            
            text_content = ' '.join(p.get_text() for p in soup.find_all('p'))
            return text_content[:4000] # Limita para não sobrecarregar a IA
            
        except Exception as e:
            return f"Ocorreu um erro ao processar a requisição web: {e}"

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
            
            return f"O tempo em {data['nearest_area'][0]['areaName'][0]['value']} é: {descricao}, {temp} graus com sensação de {sensacao}."
        except Exception as e:
            return "Não consegui verificar o tempo."

    def obter_noticias(self, fonte: str = "G1") -> str:
        url_rss = self.rss_feeds.get(fonte.upper())
        if not url_rss:
            return f"Fonte de notícias '{fonte}' não encontrada."

        try:
            feed = feedparser.parse(url_rss)
            manchetes = "; ".join(entry.title for entry in feed.entries[:3])
            return f"As manchetes do {fonte} são: {manchetes}"
        except Exception as e:
            return "Tive um problema ao buscar as notícias."
