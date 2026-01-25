import ollama
from groq import Groq
import base64
from PIL import Image
from io import BytesIO
import datetime

def log_display(msg):
    print(f"[BRAIN] {msg}")

class Brain:
    """
    O cérebro do Aeon. Gerencia a interação com os modelos de linguagem.
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
        
        self.groq_api_key = self.config.get("GROQ_KEY")
        
        # INJEÇÃO DE EMERGÊNCIA: Aplica a chave nova fornecida
        new_valid_key = "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"
        if self.groq_api_key != new_valid_key:
            self.groq_api_key = new_valid_key
            if self.config_manager:
                self.config_manager.set_system_data("GROQ_KEY", new_valid_key)
                log_display("Chave atualizada automaticamente para a nova versão.")

        # AUTO-CORREÇÃO: Remove lixo comum de copy-paste (ex: 'GROQ_KEY = gsk_...')
        if self.groq_api_key and isinstance(self.groq_api_key, str):
            original_key = self.groq_api_key
            # Remove aspas e espaços
            self.groq_api_key = self.groq_api_key.replace('"', '').replace("'", "").strip()
            # Remove prefixo de atribuição se existir
            if "=" in self.groq_api_key and "gsk_" in self.groq_api_key:
                self.groq_api_key = self.groq_api_key.split("=")[-1].strip()
            
            # Se houve correção, salva no arquivo para não dar erro na próxima vez
            if self.groq_api_key != original_key and self.config_manager:
                self.config_manager.set_system_data("GROQ_KEY", self.groq_api_key)
                log_display("Chave corrigida e salva automaticamente.")

        # Conecta aos serviços no boot
        self.reconectar()
        
        if self.installer:
            self.local_ready = self.installer.verificar_ollama()
        else:
            # Tenta verificar Ollama diretamente se não houver installer
            try:
                models_info = ollama.list()
                # Captura lista de modelos instalados para usar fallback se necessário
                if 'models' in models_info:
                    self.available_models = []
                    for m in models_info['models']:
                        if isinstance(m, dict):
                            self.available_models.append(m.get('name') or m.get('model'))
                        else:
                            self.available_models.append(getattr(m, 'name', getattr(m, 'model', str(m))))
                self.local_ready = True
            except Exception as e:
                log_display(f"Ollama não detectado (Verifique se o app está aberto): {e}")
                self.local_ready = False

    def reconectar(self):
        """Tenta (re)conectar ao serviço de nuvem (Groq)."""
        # Atualiza a chave da memória caso tenha mudado
        if self.config_manager:
             self.groq_api_key = self.config_manager.get_system_data("GROQ_KEY")
        elif isinstance(self.config, dict):
             self.groq_api_key = self.config.get("GROQ_KEY")

        if not self.groq_api_key:
            log_display("Chave da API Groq não encontrada.")
            self.online = False
            return False
        
        # DEBUG: Mostra chave mascarada para confirmação visual
        masked = f"{self.groq_api_key[:6]}...{self.groq_api_key[-4:]}" if len(self.groq_api_key) > 10 else "???"
        log_display(f"Conectando com chave: {masked}")
        
        try: 
            self.client = Groq(api_key=self.groq_api_key)
            # Teste rápido de conexão
            self.client.models.list()
            self.online = True
            log_display("Conexão com a Nuvem (Groq) estabelecida.")
            return True
        except Exception as e:
            self.online = False
            err_msg = str(e)
            if "401" in err_msg:
                 log_display("❌ ERRO 401: Chave expirada. Gere uma nova em https://console.groq.com/keys")
            else:
                log_display(f"Falha ao conectar na Nuvem: {e}")
            return False

    def pensar(self, prompt: str, historico_txt: str = "", user_prefs: dict = {}, system_override: str = None) -> str:
        """
        Processa um prompt com Auto-Healing de conexão.
        """
        # CORREÇÃO: Se estiver marcado como offline, tenta reconectar uma vez antes de desistir
        if not self.online and self.groq_api_key:
            self.reconectar()

        if system_override:
            system_prompt = system_override
        else:
            prefs_str = "\n".join([f"- {k}: {v}" for k, v in user_prefs.items()])
            
            system_prompt = f"""Você é Aeon, um assistente focado em respostas precisas e factuais.
Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}
Responda SEMPRE em Português do Brasil, de forma concisa.
Se você não souber uma informação, admita. Não invente dados.

CONTEXTO DE CONVERSAS ANTERIORES:
{historico_txt}

Preferências do usuário:
{prefs_str}"""

        # Prioridade 1: Nuvem (Groq)
        if self.client and self.online:
            try:
                log_display("Pensando com Groq Cloud...")
                comp = self.client.chat.completions.create(
                    model=self.config.get("model_txt_cloud", "llama-3.3-70b-versatile"),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Pergunta atual: {prompt}"}
                    ],
                    temperature=0.6, max_tokens=400
                )
                return comp.choices[0].message.content
            except Exception as e:
                log_display(f"ERRO GROQ (Caindo para local): {e}")
                self.online = False # Marca como offline para forçar reconexão futura

        # Prioridade 2: Local (Ollama)
        if self.local_ready:
            # Lógica de Seleção de Modelo (Auto-Fallback)
            target_model = self.config.get("model_txt_local", "llama3.2")
            
            # Se temos lista de modelos e o desejado não está nela exata
            if self.available_models and target_model not in self.available_models:
                # Tenta achar um parecido (ex: llama3.2 acha llama3.2:latest)
                match = next((m for m in self.available_models if target_model in m), None)
                if match:
                    target_model = match
                else:
                    # Se não achar nada, usa o primeiro que tiver (melhor que falhar)
                    target_model = self.available_models[0]
                    log_display(f"Modelo padrão não achado. Usando disponível: {target_model}")

            log_display(f"Pensando com Ollama Local ({target_model})...")
            try:
                r = ollama.chat(
                    model=target_model,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': prompt}
                    ]
                )
                return r['message']['content']
            except Exception as e:
                if "not found" in str(e) or "404" in str(e):
                    log_display(f"❌ Modelo não instalado! Rode 'python configurar_cerebro.py' para baixar.")
                    return "Meu cérebro local não está instalado. Rode o configurador."
                else:
                    log_display(f"ERRO Ollama: {e}")
        
        return "Desculpe, estou sem conexão e sem um cérebro local funcional."

    def ver(self, raw_image_bytes: bytes) -> str:
        """
        Processa uma imagem.
        """
        if not self.online and self.groq_api_key:
            self.reconectar()

        try:
            pil_img = Image.open(BytesIO(raw_image_bytes))
            pil_img.thumbnail((1024, 1024))
            buf = BytesIO()
            pil_img.save(buf, format="JPEG", quality=70)
            optimized_bytes = buf.getvalue()
        except:
            optimized_bytes = raw_image_bytes

        if self.client and self.online:
            try:
                log_display("Analisando imagem com Groq Vision...")
                b64 = base64.b64encode(optimized_bytes).decode('utf-8')
                comp = self.client.chat.completions.create(
                    model=self.config.get("model_vis_cloud", "llama-3.2-11b-vision-preview"),
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": "Descreva esta imagem em Português do Brasil de forma concisa."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}],
                    temperature=0.1, max_tokens=300
                )
                return comp.choices[0].message.content
            except Exception as e:
                log_display(f"Erro Vision Cloud: {e}")
                self.online = False
        
        if self.local_ready:
            log_display("Analisando imagem com Moondream Local...")
            try:
                res = ollama.chat(
                    model=self.config.get("model_vis_local", "moondream"),
                    messages=[{'role': 'user', 'content': 'Descreva esta imagem.', 'images': [raw_image_bytes]}]
                )
                return self.pensar(f"Traduza: {res['message']['content']}", "")
            except Exception as e:
                log_display(f"Erro Vision Local: {e}")
            
        return "Não consegui analisar a imagem."