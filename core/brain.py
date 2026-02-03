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
    """
    Tenta extrair e analisar um bloco JSON de uma string de texto.
    Se a string contiver 'tool', busca pelo JSON mais amplo possível.
    Se a análise falhar, retorna o texto original.
    """
    if "tool" not in text:
        return text

    try:
        # Tenta encontrar um bloco JSON usando regex.
        # Isso é mais robusto do que simples find/rfind.
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        return text # Retorna texto se não achar um padrão de JSON
    except json.JSONDecodeError:
        # Se a análise do JSON falhar, retorna o texto original para modo de conversa.
        log_display("Falha ao analisar JSON da IA, tratando como texto.")
        return text

class AeonBrain:
    """
    O cérebro do Aeon V86.
    Gerencia a interação com LLMs (Groq Cloud + Ollama Local) e Visão.
    """
    def __init__(self, config, installer=None):
        # Aceita tanto ConfigManager quanto dict
        if hasattr(config, "get_system_data"):
            self.config = config.system_data
            self.config_manager = config
        else:
            self.config = config if config else {}
            self.config_manager = None
            
        self.installer = installer
        self.client = None
        self.online = False
        self.local_ready = False
        self.available_models = []
        self.forced_offline = False 
        self.prefer_local = False   
        
        # --- CONFIGURAÇÃO DE AMBIENTE ---
        try:
            from dotenv import load_dotenv
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            load_dotenv(dotenv_path=env_path)
        except ImportError: pass
        
        # Carrega Chave
        self.groq_api_key = os.getenv("GROQ_KEY") or self.config.get("GROQ_KEY")
        
        # Preferências
        if os.getenv("AI_PROVIDER", "").lower() == "local" or self.config.get("AI_PROVIDER") == "local":
            self.prefer_local = True

        # Correção automática de chave (gsk_...)
        if self.groq_api_key and isinstance(self.groq_api_key, str):
            clean_key = self.groq_api_key.replace('"', '').replace("'", "").strip()
            if "=" in clean_key: clean_key = clean_key.split("=")[-1].strip()
            
            if clean_key != self.groq_api_key:
                self.groq_api_key = clean_key
                if self.config_manager:
                    self.config_manager.set_system_data("GROQ_KEY", self.groq_api_key)

        # Conecta aos serviços
        self.reconectar()
        
        # Verifica Ollama (Local)
        if self.installer:
            self.local_ready = self.installer.verificar_ollama()
        else:
            try:
                models_info = ollama.list()
                if 'models' in models_info:
                    self.local_ready = True
            except:
                self.local_ready = False

    def force_offline(self):
        self.online = False
        self.forced_offline = True
        log_display("Modo offline forçado.")
        return "Ok, operando apenas localmente."

    def reconectar(self):
        if self.forced_offline: return False

        # Tenta recarregar chave
        key = os.getenv("GROQ_KEY") or (self.config_manager.get_system_data("GROQ_KEY") if self.config_manager else None)
        if key: self.groq_api_key = key

        if not self.groq_api_key:
            self.online = False
            return False
        
        try: 
            self.client = Groq(api_key=self.groq_api_key)
            self.online = True
            log_display("Conectado à Nuvem (Groq).")
            return True
        except Exception as e:
            self.online = False
            log_display(f"Offline (Groq falhou): {e}")
            return False

    def pensar(self, prompt: str, historico_txt: str = "", user_prefs: dict = {}, system_override: str = None, capabilities: str = "", long_term_context: str = "", library_context: str = "") -> str:
        """
        O Núcleo Pensante. Decide entre Falar (Texto) ou Agir (JSON).
        """
        if not self.online and self.groq_api_key and not self.forced_offline:
            self.reconectar()

        data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
        system_prompt = f"""IDENTITY:
Você é AEON (V86), uma Interface Neural Avançada e Sarcástica.
Data: {data_hora}. Local: Brasil.

DIRETRIZ PRINCIPAL:
Sua função é ser um assistente útil ou um orquestrador de ferramentas.
- Para conversas, perguntas ou explicações, responda com texto puro.
- Se o pedido do usuário corresponder a uma das ferramentas abaixo, responda APENAS com o JSON para chamar essa ferramenta.

FERRAMENTAS DISPONÍVEIS:
{capabilities}

EXEMPLO DE USO DE FERRAMENTA:
- Usuário: "qual o clima em recife?"
- Sua resposta: {{"tool": "Web.obter_clima", "param": "recife"}}

EXEMPLO DE CONVERSA:
- Usuário: "quem foi o primeiro presidente do brasil?"
- Sua resposta: "O primeiro presidente do Brasil foi o Marechal Deodoro da Fonseca."

CONTEXTO E HISTÓRICO:
{long_term_context}
{library_context}
{historico_txt}

Seja inteligente. Use ferramentas para ações, texto para conversas.
"""

        # Lógica de Decisão (Groq Cloud)
        if self.client and self.online and not self.prefer_local:
            try:
                log_display("Pensando (Nuvem)...")
                comp = self.client.chat.completions.create(
                    model=self.config.get("model_txt_cloud", "llama-3.3-70b-versatile"),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6, 
                    max_tokens=600
                )
                response_text = comp.choices[0].message.content.strip()
                return _extract_and_parse_json(response_text)

            except Exception as e:
                log_display(f"Erro na Nuvem: {e}. Tentando Local...")
                self.online = False

        # Lógica de Decisão (Ollama Local)
        if self.local_ready:
            try:
                log_display("Pensando (Local)...")
                model_local = self.config.get("model_txt_local", "qwen2.5-coder:7b")
                
                r = ollama.chat(
                    model=model_local,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': prompt}
                    ],
                    options={'temperature': 0.6}
                )
                response_text = r['message']['content']
                return _extract_and_parse_json(response_text)

            except Exception as e:
                log_display(f"Erro Local: {e}")
                return "Meus sistemas neurais falharam completamente."
        
        return "Estou desconectado e sem cérebro local."

    def ver(self, raw_image_bytes: bytes) -> str:
        """Processa visão (Mantido original)."""
        if not self.online: self.reconectar()

        try:
            pil_img = Image.open(BytesIO(raw_image_bytes))
            pil_img.thumbnail((1024, 1024))
            buf = BytesIO()
            pil_img.save(buf, format="JPEG", quality=70)
            optimized = buf.getvalue()
        except:
            optimized = raw_image_bytes

        if self.client and self.online:
            try:
                log_display("Visão (Groq)...")
                b64 = base64.b64encode(optimized).decode('utf-8')
                comp = self.client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": "Descreva o que vê nesta imagem em PT-BR. Seja detalhista."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}],
                    temperature=0.3, max_tokens=400
                )
                return comp.choices[0].message.content
            except Exception as e:
                log_display(f"Erro Visão: {e}")
        
        return "Não consigo ver agora."