import ollama
from groq import Groq
import base64
from PIL import Image
from io import BytesIO
import datetime
import os
import json

def log_display(msg):
    print(f"[BRAIN] {msg}")

class AeonBrain:
    """
    O cérebro do Aeon V85.
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
            # Teste leve de conexão
            # self.client.models.list() 
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
        
        # Reconecta se necessário
        if not self.online and self.groq_api_key and not self.forced_offline:
            self.reconectar()

        # Prompt de Sistema Híbrido (A CORREÇÃO ESTÁ AQUI)
        data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
        system_prompt = f"""IDENTITY:
Você é AEON (V85), uma Interface Neural Avançada e Sarcástica.
Data: {data_hora}. Local: Brasil.

MODO DE OPERAÇÃO (IMPORTANTE):
Você tem dois modos de resposta. Escolha sabiamente:

1. MODO CONVERSA (Padrão):
   - Se o usuário disser "Oi", "Tudo bem", "Me explique X", "Quem é você?":
   - Responda APENAS com texto puro. Seja direto, cínico e útil.
   - NÃO retorne JSON.

2. MODO FERRAMENTA (Apenas se solicitado):
   - Se o usuário pedir uma ação explícita (ex: "Abra o navegador", "Pesquise no PDF", "Crie um lembrete"):
   - Retorne APENAS um JSON neste formato exato:
     {{"tool": "NomeDoModulo.funcao", "param": "valor"}}

FERRAMENTAS DISPONÍVEIS:
{capabilities}

CONTEXTO:
{long_term_context}
{library_context}

HISTÓRICO:
{historico_txt}

Seja inteligente. Não use ferramentas para perguntas simples.
"""

        # Lógica de Decisão (Groq Cloud)
        if self.client and self.online and not self.prefer_local:
            try:
                log_display("Pensando (Nuvem)...")
                # Removemos o response_format={"type": "json_object"} para permitir texto livre!
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
                
                # Tenta detectar se é JSON
                if "{" in response_text and "}" in response_text and "tool" in response_text:
                    try:
                        clean = response_text.replace("```json", "").replace("```", "").strip()
                        return json.loads(clean) # Retorna Dict (Ação)
                    except:
                        return response_text # Retorna Texto (Conversa)
                
                return response_text # Retorna Texto (Conversa)

            except Exception as e:
                log_display(f"Erro na Nuvem: {e}. Tentando Local...")
                self.online = False # Falha temporária, tenta local

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
                
                # Mesma detecção de JSON para o local
                if "{" in response_text and "tool" in response_text:
                    try:
                        clean = response_text.replace("```json", "").replace("```", "").strip()
                        start = clean.find("{")
                        end = clean.rfind("}") + 1
                        return json.loads(clean[start:end])
                    except:
                        pass
                        
                return response_text

            except Exception as e:
                log_display(f"Erro Local: {e}")
                return "Meus sistemas neurais falharam completamente."
        
        return "Estou desconectado e sem cérebro local."

    def ver(self, raw_image_bytes: bytes) -> str:
        """Processa visão (Mantido original)."""
        if not self.online: self.reconectar()

        # Otimização de imagem
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
                    model="llama-3.2-11b-vision-preview", # Modelo fixo para visão
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