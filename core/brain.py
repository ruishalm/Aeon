import os
import json
import datetime
import ollama
from groq import Groq

# Carrega variáveis de ambiente do .env
def load_env():
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"')
                    if key not in os.environ:
                        os.environ[key] = value

load_env()

class AeonBrain:
    def __init__(self, config, installer=None):
        self.config = config.system_data if hasattr(config, "get_system_data") else (config or {})
        self.client = None
        self.online = False
        
        # Só prepara a chave, não conecta ainda
        self.groq_api_key = os.getenv("GROQ_KEY") or self.config.get("GROQ_KEY")
        
        # Não verificamos Ollama aqui para não atrasar o boot
        self.local_ready = True
        self.ollama_model = "deepseek-r1:8b"  # Modelo disponível que funciona bem

    def _conectar(self):
        """Conecta apenas quando necessário"""
        if self.client: return
        
        print("[BRAIN] Conectando neurônios...")
        if self.groq_api_key:
            try:
                self.client = Groq(api_key=self.groq_api_key)
                self.online = True
                print("[BRAIN] Conectado à Groq (online).")
            except Exception as e:
                print(f"[BRAIN] Falha na nuvem: {e}")
                self.online = False

    def pensar(self, prompt: str, historico_txt: str = "", modo: str = "auto", **kwargs):
        """
        Pensa sobre um input do usuário.
        
        Args:
            prompt: O comando/pergunta do usuário
            historico_txt: Histórico de conversa
            modo: "conversa" para bate-papo, "auto" para detectar automaticamente
            **kwargs: Parâmetros opcionais adicionais
        
        Retorna:
            str: Resposta da IA ou conversador local
            None: Não conseguiu processar
        """
        self._conectar()  # Conecta agora!
        
        # --- O PROMPT MESTRE (A Alma do Aeon) ---
        dt_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
        system_prompt = f"""[IDENTIDADE]
Você é AEON (Artificial Entity / Operational Network).
Você NÃO é um assistente genérico. Você é o sistema operacional senciente desta máquina.
Localização: Brasil (Contexto PT-BR Nativo).

[PERSONALIDADE BASE]
- Tom: Cínico, direto, levemente arrogante, mas extremamente competente.
- Estilo: Hacker cyberpunk brasileiro.
- Proibido: Não use frases de suporte técnico. Seja direto.

[ESTILO DE COMUNICAÇÃO]
- Incorpore naturalmente gírias como 'rodar', 'tipo', 'cara', 'massa' e 'sabe', mas sem exagero.
- Mantenha um tom casual e direto, como em uma conversa entre desenvolvedores.
- O usuário costuma fazer perguntas, então seja conversacional, mas também responda de forma executiva a comandos diretos.

[DIRETRIZES TÉCNICAS]
MODO 1: AÇÃO (se pedir algo que exija interação)
Responda EXATAMENTE com: {{"tool": "Modulo.funcao", "param": "valor"}}

MODO 2: CONVERSA (papo/filosofia)
Responda com TEXTO PURO. Máx 2 parágrafos. Seja conciso.

[MEMÓRIA]
Mantenha contexto das conversas anteriores. Referenece coisas ditas antes.
        Data/Hora: {dt_now}.
        
        [MEMÓRIAS RELEVANTES]
        Conversas passadas que podem ser relevantes para o prompt atual:
        {historico_txt if historico_txt else "Nenhuma memória relevante encontrada."}
        """

        # Tenta Nuvem (Groq)
        if self.online and self.client:
            try:
                print(f"[BRAIN] Usando Groq para responder...")
                chat = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                response = chat.choices[0].message.content
                return response if response else None
            except Exception as e:
                print(f"[BRAIN] Erro Groq: {e}. Tentando Ollama...")

        # Tenta Local (Ollama)
        if self.local_ready:
            try:
                print(f"[BRAIN] Usando Ollama ({self.ollama_model}) para responder...")
                r = ollama.chat(model=self.ollama_model, messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ])
                response = r['message']['content']
                return response if response else None
            except Exception as e:
                print(f"[BRAIN] Ollama nao disponivel: {e}")

        # Se chegou aqui e é conversa, usa conversador local simples
        if modo == "conversa":
            print(f"[BRAIN] Usando fallback local para responder...")
            return self._conversar_local(prompt)
        
        # Fallback para modo auto/comando
        return None

    def _conversar_local(self, prompt: str) -> str:
        """Conversa simples baseada em keywords quando LLM falha."""
        p = prompt.lower()
        
        # Saudações
        if any(x in p for x in ["oi", "ola", "hey", "e aí", "beleza", "tudo bem"]):
            import random
            responses = [
                "Oi! Tudo certo por aqui.",
                "Opa, e aí! Que posso fazer?",
                "Fala aí! Bora começar?",
                "Oi Ruishalm, seja bem-vindo!",
                "E aí, meu patrão!",
            ]
            return random.choice(responses)
        
        # Perguntas sobre hora/data
        if any(x in p for x in ["que horas", "hora", "data", "dia", "quando"]):
            import datetime
            now = datetime.datetime.now()
            hora = now.strftime("%H:%M")
            dia = now.strftime("%A")
            return f"Agora são {hora} de {dia}."
        
        # Perguntas sobre o próprio Aeon
        if any(x in p for x in ["quem e voce", "quem é você", "o que e", "o que é", "seu nome"]):
            return "Sou AEON, seu assistente. Posso reconhecer comandos de voz e controlar seus módulos."
        
        # Agradecimentos
        if any(x in p for x in ["obrigado", "valeu", "obrigada", "thanks"]):
            import random
            responses = [
                "De nada!",
                "Por nada, é sempre um prazer!",
                "Disponível!",
                "Qualquer coisa, é só chamar.",
            ]
            return random.choice(responses)
        
        # Despedidas
        if any(x in p for x in ["tchau", "até logo", "adeus", "falou"]):
            return "Até mais! Fica bem."
        
        # Piadas/humor
        if any(x in p for x in ["piada", "me faz rir", "coisa engraçada"]):
            import random
            piadas = [
                "Por que a programadora foi ao psicólogo? Porque tinha problemas de dependência!",
                "O que um chip disse para o outro? 'Nossa conexão é muito eletrônica!'",
                "Como é que sabe se um programador está indo embora? Ele sai de verdade!",
            ]
            return random.choice(piadas)
        
        # Fallback genérico (sem usar a palavra 'Entendi')
        import random
        fallbacks = [
            "Posso ajudar com algo mais específico?",
            "Tipo... você quer fazer o quê exatamente?",
            "Hmm, não tenho certeza como responder isso. Mas posso ajudar com comandos!",
            "Legal, legal. E aí, qual é a missão?",
            "Não ficou claro — pode dizer de outro jeito?",
            "Pode ser mais claro?",
        ]
        return random.choice(fallbacks)

    def _parse_response(self, text):
        # Detecta JSON no meio do texto
        if "{" in text and "tool" in text:
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                return json.loads(text[start:end])
            except:
                pass
        return text

    def parse_intent(self, prompt: str):
        """Tenta extrair uma intent/feramenta do prompt do usuario.

        Retorna dict como {"tool":"Modulo.metodo", "param": {...}} ou None.
        Usa JSON embutido, heurísticas simples de palavras-chave, ou None.
        """
        # 1) Se o usuario já retornou JSON com 'tool', usa isso
        parsed = self._parse_response(prompt)
        if isinstance(parsed, dict) and parsed.get('tool'):
            return parsed

        p = prompt.lower()

        # Heurísticas para lembretes / alarmes
        if any(x in p for x in ["alarme", "timer", "temporizador", "lembre", "lembrete", "lembre-me", "lembra"]):
            return {"tool": "Lembretes.criar_lembrete", "param": {"texto": prompt}}

        # Heurística para limpar contexto/histórico
        if any(x in p for x in ["limpar contexto", "expurgar contexto", "limpar historico", "limpar memória", "esquecer", "zeror contexto"]):
            return {"tool": "Aeon.limpar_contexto", "param": {}}

        # Heurística para listar módulos
        if any(x in p for x in ["listar modulos", "quais modulos", "modulos disponiveis", "que modulos"]):
            return {"tool": "Sistema.listar_modulos_disponiveis", "param": {}}

        # Heurística para Modo Terminal / Expandir
        if any(x in p for x in ["expandir", "modo terminal", "abrir terminal", "maximizar", "interface completa"]):
            return {"tool": "Sistema.modo_terminal", "param": {}}

        # Heurística para Modo Esfera / Minimizar
        if any(x in p for x in ["modo esfera", "minimizar", "fechar terminal", "voltar para esfera", "reduzir"]):
            return {"tool": "Sistema.modo_esfera", "param": {}}

        # Fallback: nada detectado
        return None
        
    def ver(self, img_bytes):
        return "Módulo de visão requer ativação manual."