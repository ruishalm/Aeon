import ollama
from groq import Groq
import base64
from PIL import Image
from io import BytesIO
import datetime
import os
import json
import re

def log_display(msg):
    print(f"[BRAIN] {msg}")

def _extract_and_parse_json(text: str):
    if "tool" not in text:
        return text
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        return text
    except json.JSONDecodeError:
        log_display("Falha ao analisar JSON da IA, tratando como texto.")
        return text

class AeonBrain:
    def __init__(self, config, installer=None):
        self.config = config.system_data if hasattr(config, "get_system_data") else (config or {})
        self.config_manager = config if hasattr(config, "get_system_data") else None
        
        self.client = None
        self.online = False
        self.local_ready = False
        
        self.groq_api_key = os.getenv("GROQ_KEY") or self.config.get("GROQ_KEY")
        
        # A verificação do Ollama é adiada para não travar o boot
        self.local_ready = False 

    def _conectar_sob_demanda(self):
        """Só conecta quando realmente precisar pensar."""
        if self.client and self.online: return True
        
        print("[BRAIN] Estabelecendo conexão neural (Lazy Connect)...")
        if not self.groq_api_key: return False
        
        try:
            self.client = Groq(api_key=self.groq_api_key)
            self.online = True
            print("[BRAIN] Conectado à Nuvem (Groq).")
            return True
        except Exception as e:
            print(f"[BRAIN] Falha de conexão: {e}")
            self.online = False
            return False

    def pensar(self, prompt: str, historico_txt: str = "", **kwargs) -> str:
        self._conectar_sob_demanda()
        
        system_prompt = f"""Você é o AEON.
        Data: {datetime.datetime.now().strftime("%d/%m/%Y")}.
        
        MODO DE RESPOSTA:
        1. CONVERSA: Responda apenas com texto se for papo furado.
        2. AÇÃO: Se o usuário pedir para usar uma ferramenta, responda EXATAMENTE um JSON:
           {{"tool": "Modulo.funcao", "param": "valor"}}
        """

        if self.client and self.online:
            try:
                comp = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6
                )
                resp = comp.choices[0].message.content.strip()
                return self._processar_resposta(resp)
            except:
                self.online = False

        try:
            r = ollama.chat(model="qwen2.5-coder:7b", messages=[{"role": "user", "content": prompt}])
            return self._processar_resposta(r['message']['content'])
        except:
            return "Estou sem cérebro (Conexão falhou e Ollama desligado)."

    def _processar_resposta(self, texto):
        if "{" in texto and "tool" in texto:
            try:
                clean = texto.replace("```json", "").replace("```", "").strip()
                start = clean.find("{")
                end = clean.rfind("}") + 1
                return json.loads(clean[start:end])
            except:
                pass
        return texto
    
    def ver(self, img_bytes):
        # A função ver é simplificada conforme a sugestão, 
        # para evitar qualquer processamento pesado que possa travar.
        return "Módulo de visão offline por enquanto."