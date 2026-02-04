import os
import json
import datetime
import ollama
from groq import Groq

class AeonBrain:
    def __init__(self, config, installer=None):
        self.config = config.system_data if hasattr(config, "get_system_data") else (config or {})
        self.client = None
        self.online = False
        
        # Só prepara a chave, não conecta ainda
        self.groq_api_key = os.getenv("GROQ_KEY") or self.config.get("GROQ_KEY")
        
        # Não verificamos Ollama aqui para não atrasar o boot
        self.local_ready = True 

    def _conectar(self):
        """Conecta apenas quando necessário"""
        if self.client: return
        
        print("[BRAIN] Conectando neurônios...")
        if self.groq_api_key:
            try:
                self.client = Groq(api_key=self.groq_api_key)
                self.online = True
                print("[BRAIN] Conectado à Groq.")
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
        
        # Define sistema baseado no modo
        if modo == "conversa":
            system_prompt = """Você é AEON, uma IA brasileira sociável e cínica.
            Data: {}.
            
            Responda de forma natural e conversacional. Não mencione comandos ou módulos a menos que perguntado.
            Seja amigável, um pouco irreverente, mas sempre respeitoso.
            Respostas curtas (1-2 frases).
            """.format(__import__('datetime').datetime.now().strftime("%d/%m/%Y"))
        else:
            system_prompt = """Você é AEON.
            Data: {}.
            Responda de forma direta e cínica.
            """.format(__import__('datetime').datetime.now().strftime("%d/%m/%Y"))

        # Tenta Nuvem (Groq)
        if self.online and self.client:
            try:
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
                print(f"[BRAIN] Erro nuvem: {e}. Tentando local...")

        # Tenta Local (Ollama)
        if self.local_ready:
            try:
                r = ollama.chat(model="qwen2.5-coder:7b", messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ])
                response = r['message']['content']
                return response if response else None
            except Exception as e:
                print(f"[BRAIN] Ollama nao disponivel: {e}")

        # Se chegou aqui e é conversa, usa conversador local simples
        if modo == "conversa":
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
        
        # Fallback genérico
        import random
        fallbacks = [
            "Entendi. Posso ajudar com algo mais específico?",
            "Tipo... você quer fazer o quê exatamente?",
            "Hmm, não tenho certeza como responder isso. Mas posso ajudar com comandos!",
            "Legal, legal. E aí, qual é a missão?",
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
        
    def ver(self, img_bytes):
        return "Módulo de visão requer ativação manual."