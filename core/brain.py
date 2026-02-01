import ollama
from groq import Groq
import base64
from PIL import Image
from io import BytesIO
import datetime
import os

def log_display(msg):
    print(f"[BRAIN] {msg}")

class AeonBrain:
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
        self.forced_offline = False # Flag para forçar modo offline
        self.prefer_local = False   # Flag para preferir processamento local
        
        # Tenta carregar variáveis de ambiente do arquivo .env
        try:
            from dotenv import load_dotenv
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            load_dotenv(dotenv_path=env_path)
        except ImportError:
            pass # Se o pacote não estiver instalado ainda, segue sem ele
        
        # Prioridade: Variável de Ambiente (.env) > Configuração JSON
        self.groq_api_key = os.getenv("GROQ_KEY") or self.config.get("GROQ_KEY")
        
        # Verifica preferência por IA Local
        if os.getenv("AI_PROVIDER", "").lower() == "local" or self.config.get("AI_PROVIDER") == "local":
            self.prefer_local = True

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

    def force_offline(self):
        """Força o cérebro a operar em modo offline."""
        self.online = False
        self.forced_offline = True
        log_display("Modo offline forçado. Usando apenas cérebro local.")
        return "Ok, operando em modo offline."

    def force_online(self):
        """Tenta voltar a operar em modo online."""
        self.forced_offline = False
        log_display("Tentando reconectar ao modo online...")
        if self.reconectar():
            return "Conexão com a nuvem reestabelecida."
        else:
            return "Não foi possível reconectar. Verifique sua chave e conexão."

    def reconectar(self):
        """Tenta (re)conectar ao serviço de nuvem (Groq)."""
        if self.forced_offline:
            log_display("Reconexão bloqueada pelo modo offline forçado.")
            return False

        # Atualiza a chave da memória caso tenha mudado
        # Recarrega .env para permitir troca de chave sem reiniciar e garantir leitura
        try:
            from dotenv import load_dotenv
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            load_dotenv(dotenv_path=env_path, override=True)
        except ImportError: pass

        # Prioridade: .env > ConfigManager > Config Dict
        if os.getenv("GROQ_KEY"):
             self.groq_api_key = os.getenv("GROQ_KEY")
        elif self.config_manager:
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

    def pensar(self, prompt: str, historico_txt: str = "", user_prefs: dict = {}, system_override: str = None, capabilities: str = "", long_term_context: str = "", library_context: str = "") -> str:
        """
        Processa um prompt, decidindo se deve chamar uma ferramenta ou responder diretamente.
        Retorna um dicionário (tool_call) ou uma string (resposta de conversação).
        Suporta Tool Use local (Qwen) e nuvem (Groq).
        """
        import json
        
        if not self.online and self.groq_api_key and not self.forced_offline:
            self.reconectar()

        # O system_override é para casos especiais onde um módulo força um comportamento.
        # Se não houver, usamos nosso novo prompt de decisão de ferramentas.
        if system_override:
            system_prompt = system_override
        else:
            # TODO: O 'capabilities' precisa ser um JSON Schema para ser realmente eficaz.
            # Por agora, a IA vai tentar extrair dos gatilhos listados.
            system_prompt = f"""Você é um despachante de funções de IA para o sistema AEON. Seu trabalho é analisar o prompt do usuário e a lista de ferramentas disponíveis e retornar um objeto JSON para chamar a ferramenta apropriada.

REGRAS:
1.  **SAÍDA JSON OBRIGATÓRIA:** Sua resposta DEVE ser um dos dois seguintes formatos:
    a) Um objeto JSON para chamada de ferramenta:
       ```json
       {{
         "tool_name": "NomeDoModulo.nome_da_funcao",
         "parameters": {{ "param1": "valor1" }}
       }}
       ```
    b) Se NENHUMA ferramenta for adequada, use este JSON para uma resposta de conversação:
       ```json
       {{
         "fallback": "Não tenho uma ferramenta para isso, mas..."
       }}
       ```
2.  **NÃO CONVERSE:** Sua saída deve ser APENAS o JSON. Sem texto antes ou depois.
3.  **ANÁLISE:** Use o prompt do usuário, o histórico e o contexto para tomar sua decisão.

### FERRAMENTAS DISPONÍVEIS:
{capabilities}

### CONTEXTO ADICIONAL:
{long_term_context}
{library_context}

### HISTÓRICO DA CONVERSA:
{historico_txt}
---
Analise o PROMPT DO USUÁRIO abaixo e retorne o objeto JSON apropriado.

### PROMPT DO USUÁRIO:
{prompt}
"""

        # Prioridade 1: Nuvem (Groq) - Apenas se não estiver forçado local
        if self.client and self.online and not self.prefer_local and not self.forced_offline:
            try:
                log_display("Decidindo ação com Groq Cloud...")
                comp = self.client.chat.completions.create(
                    model=self.config.get("model_txt_cloud", "llama-3.3-70b-versatile"),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt} # O prompt já está no system prompt, mas reforça aqui.
                    ],
                    temperature=0.1, # Baixa temperatura para ser mais determinístico
                    max_tokens=500,
                    # Força a resposta a ser um objeto JSON válido
                    response_format={"type": "json_object"},
                )
                response_text = comp.choices[0].message.content
                
                # Tenta decodificar o JSON. Se a IA desobedeceu e não mandou JSON,
                # o bloco 'except' vai tratar como texto normal.
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    log_display(f"WARN: IA não retornou JSON válido. Tratando como fallback: {response_text}")
                    return response_text # Retorna o texto puro como fallback

            except Exception as e:
                log_display(f"ERRO GROQ (Caindo para local): {e}")
                self.online = False

        # Prioridade 2: Local (Ollama) - Agora com tentativa de Tool Use (JSON)
        if self.local_ready:
            model_local = self.config.get("model_txt_local", "qwen2.5-coder:7b")
            log_display(f"Pensando com Ollama Local ({model_local})...")
            
            try:
                # Tenta usar o prompt de sistema JSON para modelos locais inteligentes (como Qwen)
                r = ollama.chat(
                    model=model_local,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': prompt}
                    ],
                    options={'temperature': 0.1}
                )
                response_text = r['message']['content']
                
                # Tenta extrair JSON da resposta local
                try:
                    # Limpeza básica caso o modelo coloque markdown ```json ... ```
                    clean_text = response_text.replace("```json", "").replace("```", "").strip()
                    if "{" in clean_text and "}" in clean_text:
                        # Pega apenas o primeiro objeto JSON encontrado
                        start = clean_text.find("{")
                        end = clean_text.rfind("}") + 1
                        json_str = clean_text[start:end]
                        return json.loads(json_str)
                    else:
                        return response_text # Retorna texto se não for JSON
                except json.JSONDecodeError:
                    return response_text

            except Exception as e:
                log_display(f"ERRO Ollama: {e}")
                return "Cérebro local com problemas."
        
        return {"fallback": "Desculpe, estou sem conexão e sem um cérebro local funcional."}

    def ver(self, raw_image_bytes: bytes) -> str:
        """
        Processa uma imagem.
        """
        if not self.online and self.groq_api_key and not self.forced_offline:
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