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

    def pensar(self, prompt: str, historico_txt: str = "", **kwargs):
        self._conectar() # Conecta agora!
        
        # Prompt que define a personalidade
        system_prompt = f"""Você é AEON.
        Data: {datetime.datetime.now().strftime("%d/%m/%Y")}.
        Responda de forma direta e cínica.
        
        REGRAS:
        1. Se for conversa: Responda texto puro.
        2. Se for comando (abrir, pesquisar, lembrar): Responda JSON: {{"tool": "...", "param": "..."}}
        """

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
                return self._parse_response(chat.choices[0].message.content)
            except Exception as e:
                print(f"[BRAIN] Erro nuvem: {e}. Tentando local...")

        # Tenta Local (Ollama)
        try:
            r = ollama.chat(model="qwen2.5-coder:7b", messages=[{"role": "user", "content": prompt}])
            return self._parse_response(r['message']['content'])
        except Exception as e:
            print(f"[BRAIN] Ollama nao disponivel: {e}")
            # Retorna um fallback neutro ao invés de mensagem de erro
            return f"Entendi: {prompt}. Processando..."

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