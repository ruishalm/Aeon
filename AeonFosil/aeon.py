import warnings
warnings.filterwarnings("ignore")
import customtkinter as ctk
import threading
import time
import datetime
import sys
import os
import re
import json
import asyncio
import subprocess
from io import BytesIO
from PIL import Image, ImageGrab
import psutil
import random
import webbrowser
import base64
import zipfile
import urllib.request
import shutil

# ==============================================================================
#                       BOOTSTRAP
# ==============================================================================
def check_deps():
    DEPS = {
        "pygame": "pygame", "edge-tts": "edge_tts", "GPUtil": "GPUtil", 
        "ollama": "ollama", "packaging": "packaging", "Pillow": "PIL", 
        "SpeechRecognition": "speech_recognition", "pyautogui": "pyautogui", 
        "pyaudio": "pyaudio", "psutil": "psutil", "groq": "groq",
        "requests": "requests", "beautifulsoup4": "bs4", "googlesearch-python": "googlesearch",
        "feedparser": "feedparser", "PyGetWindow": "pygetwindow",
        "pyttsx3": "pyttsx3", "dateparser": "dateparser"
    }
    miss = [pip for pip, mod in DEPS.items() if import_safe(mod) is None]
    if miss:
        print(f">> [BOOT] Instalando: {miss}")
        try: subprocess.check_call([sys.executable, "-m", "pip", "install"] + miss)
        except: pass

def import_safe(name):
    try: return __import__(name)
    except ImportError: return None

check_deps()

import pygame
import edge_tts
import GPUtil
import ollama
import pyautogui
import speech_recognition as sr
import psutil
import pyttsx3
import dateparser
from groq import Groq
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import feedparser
import pygetwindow as gw

# ==============================================================================
#                               CONFIGURAÇÕES
# ==============================================================================

GROQ_KEY = "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"

CFG = {
    "mem": "memoria_aeon.json",
    "sys": "aeon_system.json",
    "aud": "temp_audio.mp3",
    "model_txt_cloud": "llama-3.3-70b-versatile",
    "model_vis_cloud": "llama-3.2-11b-vision-preview",
    "model_txt_local": "llama3.2",
    "model_vis_local": "moondream",
    # Configurações do Piper (Voz Offline Neural)
    "piper_url": "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip",
    "voice_onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx",
    "voice_json": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json"
}

C = {
    "bg": "#050505", "panel_log": "#000000", "panel_chat": "#101010",
    "log_text": "#004400", "user": "#00ffff", "bot": "#ffffff", 
    "sys": "#ffff00", "err": "#ff5555", "border": "#b30000",
    "led_off": "#1a1a1a", "led_cloud": "#0088ff", "led_local": "#ffaa00", "led_hybrid": "#00ff00"
}

TRIGGERS = ["aeon", "aion", "iron", "filho", "assistente", "computador"]
APP_REF = None
PARAR_FALA = False
RECALIBRAR_MIC = False

# ==============================================================================
#                     GESTOR DE INSTALAÇÃO (OLLAMA + PIPER)
# ==============================================================================

class InstallMgr:
    def __init__(self):
        self.piper_dir = os.path.join(os.getcwd(), "piper_tts")
        self.piper_exe = os.path.join(self.piper_dir, "piper.exe")
        self.voice_model = os.path.join(self.piper_dir, "voice.onnx")

    def limpar_lixo(self):
        for f in os.listdir("."):
            if f.startswith("fala_") and f.endswith(".mp3"):
                try: os.remove(f)
                except: pass

    def verificar_ollama(self):
        try:
            subprocess.run(["ollama", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except: return False

    def verificar_piper(self):
        return os.path.exists(self.piper_exe) and os.path.exists(self.voice_model)

    def download_file(self, url, dest):
        if APP_REF: APP_REF.log_display(f"Baixando: {url.split('/')[-1]}...")
        urllib.request.urlretrieve(url, dest)

    def instalar_piper(self):
        if self.verificar_piper():
            if APP_REF: APP_REF.chat_display("Piper já está instalado.", "SISTEMA", "sys")
            return

        if APP_REF: APP_REF.chat_display("Iniciando instalação da Voz Neural Offline (Piper)...", "SISTEMA", "sys")
        os.makedirs(self.piper_dir, exist_ok=True)
        
        try:
            # 1. Baixa o executável
            zip_path = "piper.zip"
            self.download_file(CFG["piper_url"], zip_path)
            
            # 2. Extrai
            if APP_REF: APP_REF.log_display("Extraindo Piper...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.getcwd()) # Extrai pasta 'piper'
            
            # Move para pasta correta se necessário e renomeia
            if os.path.exists("piper"):
                if os.path.exists(self.piper_dir): shutil.rmtree(self.piper_dir)
                os.rename("piper", "piper_tts")
            
            os.remove(zip_path)

            # 3. Baixa a voz
            self.download_file(CFG["voice_onnx"], self.voice_model)
            self.download_file(CFG["voice_json"], self.voice_model + ".json")
            
            if APP_REF: APP_REF.chat_display("Voz Offline Instalada com Sucesso!", "SISTEMA", "sys")
            
        except Exception as e:
            if APP_REF: APP_REF.chat_display(f"Erro ao instalar Piper: {e}", "SISTEMA", "err")

    def instalar_ollama_soft(self):
        try: subprocess.run(["winget", "install", "Ollama.Ollama"], check=True)
        except: webbrowser.open("https://ollama.com/download")

    def baixar_modelos_ollama(self):
        os.system(f"start cmd /k ollama pull {CFG['model_txt_local']}")
        os.system(f"start cmd /k ollama pull {CFG['model_vis_local']}")

INSTALLER = InstallMgr()

# ==============================================================================
#                     CÉREBRO HÍBRIDO
# ==============================================================================

class Brain:
    def __init__(self):
        self.client = None
        self.local_ready = False
        self.online = True
        
        if GROQ_KEY:
            try: 
                self.client = Groq(api_key=GROQ_KEY)
                self.client.models.list()
            except: self.online = False
            
        self.local_ready = INSTALLER.verificar_ollama()

    def reconectar(self):
        if not self.client: return "Sem chave API."
        try:
            self.client.models.list(); self.online = True
            if APP_REF: APP_REF.update_leds()
            return "Nuvem OK."
        except Exception as e: return f"Falha: {e}"

    def pensar(self, prompt, historico_txt):
        if self.client and self.online:
            try:
                if APP_REF: APP_REF.log_display("Groq Cloud...")
                comp = self.client.chat.completions.create(
                    model=CFG["model_txt_cloud"],
                    messages=[
                        {"role": "system", "content": f"""Você é Aeon, um assistente focado em respostas precisas.
Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}
Responda SEMPRE em Português do Brasil, de forma concisa.

CONTEXTO DE CONVERSAS ANTERIORES:
{historico_txt}

REGRAS IMPORTANTES:
1. Se o usuário perguntar sobre algo dito ANTES (ex: "o que eu disse?"), consulte o contexto acima
2. Use informações das conversas anteriores para responder com coerência
3. Se referenciarem algo anterior, mencione que você lembra
4. Se não souber, admita"""},
                        {"role": "user", "content": f"Pergunta atual: {prompt}"}
                    ], temperature=0.6, max_tokens=300
                )
                return comp.choices[0].message.content
            except Exception as e:
                self.online = False; 
                if APP_REF: APP_REF.log_display(f"Groq Off: {e}"); APP_REF.update_leds()

        if self.local_ready:
            if APP_REF: APP_REF.log_display("Ollama Local...")
            try:
                r = ollama.chat(model=CFG["model_txt_local"], messages=[
                    {'role':'system','content':"Você é Aeon. Responda curto em PT-BR. Lembre de conversas anteriores se perguntarem."}, 
                    {'role':'user','content':f"Contexto anterior: {historico_txt}\n\n{prompt}"}
                ])
                return r['message']['content']
            except: pass
        
        return "Sem cérebro. Diga 'instalar offline'."

    def ver(self, raw_bytes):
        try:
            pil = Image.open(BytesIO(raw_bytes)); pil.thumbnail((1024, 1024))
            buf = BytesIO(); pil.save(buf, "JPEG", quality=70); opt_bytes = buf.getvalue()
        except: opt_bytes = raw_bytes

        if self.client and self.online:
            try:
                if APP_REF: APP_REF.log_display("Groq Vision...")
                b64 = base64.b64encode(opt_bytes).decode('utf-8')
                comp = self.client.chat.completions.create(
                    model=CFG["model_vis_cloud"],
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": "Descreva PT-BR."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}], temperature=0.1, max_tokens=300
                )
                return comp.choices[0].message.content
            except: self.online = False; APP_REF.update_leds()
            
        if self.local_ready:
            try:
                if APP_REF: APP_REF.log_display("Moondream...")
                res = ollama.chat(model=CFG["model_vis_local"], messages=[{'role':'user','content':'Describe','images':[raw_bytes]}])
                return self.pensar(f"Traduza: {res['message']['content']}", "")
            except: pass
        return "Cego."

CEREBRO = Brain()

# ==============================================================================
#                     SISTEMA & MEMÓRIA
# ==============================================================================

class SysMgr:
    def __init__(self): self.data = self.load()
    def load(self): return json.load(open(CFG["sys"], encoding='utf-8')) if os.path.exists(CFG["sys"]) else {"apps": {}}
    def save(self): json.dump(self.data, open(CFG["sys"], 'w', encoding='utf-8'), indent=4)
    def get_apps(self): return self.data.get("apps", {})
    def set_apps(self, apps): self.data["apps"] = apps; self.save()

SISTEMA = SysMgr()

class TaskManager:
    def __init__(self, filepath="aeon_tasks.json"):
        self.filepath = filepath
        self.tasks = self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_tasks(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, indent=4)

    def add_task(self, text, deadline_str, priority):
        try:
            deadline = datetime.datetime.fromisoformat(deadline_str)
            task = {"id": len(self.tasks) + 1, "text": text, "deadline": deadline_str, "priority": priority, "done": False}
            self.tasks.append(task)
            self.save_tasks()
            return f"Lembrete '{text}' definido para {deadline.strftime('%d/%m/%Y %H:%M')}."
        except Exception as e:
            return f"Erro ao adicionar o lembrete: {e}"

    def list_tasks(self, include_done=False):
        
        active_tasks = [t for t in self.tasks if not t.get('done')]
        if not active_tasks:
            return "Você não tem lembretes ou tarefas pendentes."

        response = "Suas tarefas pendentes são:\n"
        # Ordena por prioridade (maior primeiro) e depois por prazo
        sorted_tasks = sorted(active_tasks, key=lambda x: (-x.get('priority', 0), x['deadline']))
        
        for task in sorted_tasks:
            deadline = datetime.datetime.fromisoformat(task['deadline'])
            response += f"- {task['text']} para {deadline.strftime('%d/%m %H:%M')} (Prioridade: {task.get('priority', 'Normal')})\n"
        return response

    def mark_task_done(self, task_text):
        found = False
        for task in self.tasks:
            if not task.get('done') and task_text.lower() in task['text'].lower():
                task['done'] = True
                found = True
                break # Marca apenas a primeira tarefa correspondente
        if found:
            self.save_tasks()
            return f"Tarefa '{task_text}' marcada como concluída."
        return f"Não encontrei a tarefa pendente '{task_text}'."

TASK_MANAGER = TaskManager()

def carregar_memoria():
    if not os.path.exists(CFG["mem"]): return []
    try: return [i for i in json.load(open(CFG["mem"], encoding='utf-8')) if 'user' in i]
    except: return []
def salvar_memoria(h): json.dump(h[-20:], open(CFG["mem"], 'w', encoding='utf-8'), indent=4)
def adicionar_memoria(u, a):
    global MEMORIA_RAM; MEMORIA_RAM.append({"user": u, "aeon": a}); salvar_memoria(MEMORIA_RAM)
MEMORIA_RAM = carregar_memoria()

# ==============================================================================
#                          LÓGICA DE ÁUDIO (PIPER + EDGE)
# ==============================================================================

def falar(texto):
    global PARAR_FALA
    if not texto: return
    PARAR_FALA = False
    if APP_REF: APP_REF.chat_display(texto, "AEON", "bot")
    
    clean = re.sub(r'[*_#`]', '', texto).replace('\n', ' ').strip()
    f_tmp = f"fala_{random.randint(1000,9999)}.wav"

    # 1. Tenta Online (Melhor Qualidade)
    try:
        asyncio.run(edge_tts.Communicate(texto, "pt-BR-AntonioNeural").save(f_tmp))
        tocar_audio(f_tmp)
        return
    except: pass # Falha silenciosa para tentar Piper

    # 2. Tenta Offline Neural (Piper)
    if INSTALLER.verificar_piper():
        if APP_REF: APP_REF.log_display("Usando Piper (Offline)...")
        try:
            cmd = f'echo {clean} | "{INSTALLER.piper_exe}" --model "{INSTALLER.voice_model}" --output_file "{f_tmp}"'
            subprocess.run(cmd, shell=True, check=True)
            tocar_audio(f_tmp)
            return
        except Exception as e: print(f"Piper erro: {e}")

    # 3. Fallback Robótico (Se tudo falhar)
    try:
        if APP_REF: APP_REF.log_display("Voz de Emergência...")
        e = pyttsx3.init()
        e.say(clean); e.runAndWait()
    except: pass

def tocar_audio(arquivo):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(arquivo)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if PARAR_FALA: pygame.mixer.music.stop(); break
            time.sleep(0.1)
        pygame.mixer.quit()
    except: pass
    threading.Thread(target=limpar_seguro, args=(arquivo,)).start()

def limpar_seguro(f): 
    time.sleep(0.5); 
    try: os.remove(f) 
    except: pass

def calar_boca():
    global PARAR_FALA; PARAR_FALA = True
    if APP_REF: APP_REF.chat_display(">> XIU!", "SISTEMA", "err")
    try: pygame.mixer.music.stop()
    except: pass

# ==============================================================================
#                          CORE
# ==============================================================================

def indexar_programas():
    if APP_REF: APP_REF.log_display("Indexando...")
    apps = {"calc": "calc", "notepad": "notepad", "cmd": "start cmd", "explorer": "explorer"}
    for r, d, f in os.walk(os.environ["ProgramData"] + r"\Microsoft\Windows\Start Menu\Programs"):
        for file in f:
            if file.endswith(".lnk"): apps[file.lower().replace(".lnk","")] = os.path.join(r, file)
    SISTEMA.set_apps(apps)

def processar_comando(texto):
    if not texto: return
    cmd = texto.lower()
    global RECALIBRAR_MIC
    
    if "sair" in cmd: falar("Até logo."); os._exit(0)
    if "conectar" in cmd: msg = CEREBRO.reconectar(); falar(msg); return
    if "sistema recalibrar" in cmd: falar("Silêncio..."); time.sleep(2); RECALIBRAR_MIC=True; return

    # Lógica de Tarefas e Lembretes (com dateparser)
    if "lembrete" in cmd or "tarefa" in cmd:
        if "listar" in cmd or "quais são" in cmd:
            falar(TASK_MANAGER.list_tasks())
            return
        
        if "concluído" in cmd or "concluída" in cmd:
            # Extrai o texto da tarefa para marcar como concluída
            task_text = re.split(r'concluído|concluída', cmd)[-1].strip()
            # Remove palavras-chave para isolar o texto da tarefa
            task_text = task_text.replace("marcar", "").replace("lembrete", "").replace("tarefa", "").strip()
            falar(TASK_MANAGER.mark_task_done(task_text))
            return

        # Criar lembrete
        try:
            # Extrai o texto principal e a string de data
            texto_principal = ""
            raw_date_str = ""
            
            # Tenta encontrar 'para' para separar o texto da data
            if " para " in cmd:
                parts = cmd.split(" para ")
                texto_principal = parts[0].replace("lembrete de", "").replace("me lembre de", "").replace("tarefa de", "").strip()
                raw_date_str = parts[1].split(" com prioridade")[0].strip()
            else:
                 raise ValueError("Não entendi o prazo. Tente usar 'para'. Ex: '... para amanhã às 10h'.")

            # Usa dateparser para interpretar a data
            deadline = dateparser.parse(raw_date_str, languages=['pt'])
            
            if not texto_principal or not deadline:
                raise ValueError("Não consegui entender o lembrete ou o prazo.")

            deadline_str = deadline.isoformat()

            # Extrair prioridade
            prioridade = 0 # Normal
            if "prioridade alta" in cmd: prioridade = 1
            if "prioridade baixa" in cmd: prioridade = -1
            
            resultado = TASK_MANAGER.add_task(texto_principal, deadline_str, prioridade)
            falar(resultado)
            
        except Exception as e:
            falar(f"Não consegui criar o lembrete. {e}")
            if APP_REF: APP_REF.log_display(f"Erro Lembrete: {e}")
        return

    # INSTALAÇÃO INTELIGENTE
    if "instalar" in cmd and ("piper" in cmd or "voz offline" in cmd):
        falar("Baixando voz neural offline. Aguarde...")
        threading.Thread(target=INSTALLER.instalar_piper).start()
        return

    if "instalar" in cmd and "offline" in cmd:
        falar("Instalando cérebro local...")
        if not INSTALLER.verificar_ollama(): INSTALLER.instalar_ollama_soft()
        INSTALLER.baixar_modelos_ollama()
        return

    if "instalar" in cmd:
        pkg = cmd.replace("instalar","").strip()
        try: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg]); falar("Ok.")
        except: falar("Erro.")
        return

    if "tela" in cmd:
        img = ImageGrab.grab(); buf = BytesIO(); img.save(buf, format="PNG")
        falar("Vendo..."); falar(CEREBRO.ver(buf.getvalue())); return

    apps = SISTEMA.get_apps()
    for n, p in apps.items():
        if n in cmd and "abre" in cmd:
            falar(f"Abrindo {n}..."); os.startfile(p); return

    hist = ""
    for i in MEMORIA_RAM[-2:]: hist += f"U: {i.get('user','')} | A: {i.get('aeon','')}\n"
    resp = CEREBRO.pensar(texto, hist)
    adicionar_memoria(texto, resp)
    falar(resp)

# ==============================================================================
#                          GUI (V72)
# ==============================================================================

class PrintRedirector:
    def __init__(self, app): self.app = app
    def write(self, msg): 
        if msg.strip() and self.app: self.app.log_display(msg.strip())
    def flush(self): pass

class AeonGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AEON V72 - PIPER EDITION")
        self.geometry("450x650"); self.configure(fg_color=C["bg"])
        ctk.set_appearance_mode("Dark")
        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(1, weight=1)

        self.status_frame = ctk.CTkFrame(self, fg_color="#080808", height=40, corner_radius=0)
        self.status_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        def mk_led(t, c):
            f = ctk.CTkFrame(self.status_frame, fg_color="transparent"); f.pack(side="left", padx=15)
            ctk.CTkLabel(f, text=t, font=("Arial",10,"bold"), text_color="#777").pack()
            cv = ctk.CTkCanvas(f, width=15, height=15, bg="#080808", highlightthickness=0); cv.pack()
            idc = cv.create_oval(3,3,13,13, fill=C["led_off"], outline="")
            return cv, idc

        self.cv_c, self.id_c = mk_led("CLOUD", 0); self.cv_l, self.id_l = mk_led("LOCAL", 1); self.cv_h, self.id_h = mk_led("HYBRID", 2)

        self.log_box = ctk.CTkTextbox(self, font=("Consolas",9), fg_color=C["panel_log"], text_color=C["log_text"])
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=5); self.log_box.configure(state="disabled")

        self.chat_box = ctk.CTkTextbox(self, font=("Consolas",12), fg_color=C["panel_chat"], text_color=C["bot"])
        self.chat_box.grid(row=1, column=1, sticky="nsew", padx=5, pady=5); self.chat_box.configure(state="disabled")
        self.chat_box._textbox.tag_config("bot", foreground="white"); self.chat_box._textbox.tag_config("user", foreground="cyan")
        self.chat_box._textbox.tag_config("err", foreground="red")

        sys.stdout = PrintRedirector(self)

        f = ctk.CTkFrame(self, fg_color="#111111"); f.grid(row=2, columnspan=2, sticky="ew", padx=5, pady=5)
        self.inp = ctk.CTkEntry(f); self.inp.pack(side="left", fill="x", expand=True, padx=5)
        self.inp.bind("<Return>", self.on_send)
        self.btn_mode = ctk.CTkButton(f, text="DIRETO", width=60, fg_color="green", command=self.toggle_mode); self.btn_mode.pack(side="left")
        ctk.CTkButton(f, text="XIU", width=40, fg_color="red", command=calar_boca).pack(side="right")

        self.mode_call = False; threading.Thread(target=self.boot, daemon=True).start()

    def boot(self):
        print(">> Boot V72...")
        INSTALLER.limpar_lixo()
        if not SISTEMA.get_apps(): indexar_programas()
        self.update_leds(); self.chat_display("Aeon Online.", "SISTEMA", "sys")
        threading.Thread(target=self.loop_voz, daemon=True).start()
        threading.Thread(target=self.loop_alarm, daemon=True).start()

    def update_leds(self):
        off = C["led_off"]
        self.cv_c.itemconfig(self.id_c, fill=off); self.cv_l.itemconfig(self.id_l, fill=off); self.cv_h.itemconfig(self.id_h, fill=off)
        hc = CEREBRO.client and CEREBRO.online; hl = CEREBRO.local_ready
        if hc: self.cv_c.itemconfig(self.id_c, fill=C["led_cloud"])
        if hl: self.cv_l.itemconfig(self.id_l, fill=C["led_local"])
        if hc and hl: self.cv_h.itemconfig(self.id_h, fill=C["led_hybrid"])

    def log_display(self, m):
        self.log_box.configure(state="normal"); self.log_box.insert("end", f"> {m}\n"); self.log_box.configure(state="disabled"); self.log_box.see("end")

    def chat_display(self, m, s, t="bot"):
        self.chat_box.configure(state="normal"); self.chat_box.insert("end", f"\n[{s}]: {m}\n", t); self.chat_box.configure(state="disabled"); self.chat_box.see("end")

    def on_send(self, e=None):
        t = self.inp.get(); self.inp.delete(0, "end"); self.chat_display(t, "VOCÊ", "user")
        threading.Thread(target=processar_comando, args=(t,)).start()

    def toggle_mode(self):
        self.mode_call = not self.mode_call
        c, t = ("#e6b800", "CHAMAR") if self.mode_call else ("green", "DIRETO")
        self.btn_mode.configure(fg_color=c, text=t)

    def loop_alarm(self):
        while True:
            now = datetime.datetime.now()
            # Itera sobre uma cópia da lista para poder modificar a original
            for task in TASK_MANAGER.tasks[:]:
                if not task.get('done'):
                    deadline = datetime.datetime.fromisoformat(task['deadline'])
                    if now >= deadline:
                        # Pausa a mídia, avisa e despausa
                        pyautogui.press("playpause")
                        time.sleep(0.5)
                        falar(f"Atenção, lembrete: {task['text']}")
                        time.sleep(1)
                        pyautogui.press("playpause")
                        
                        # Marca a tarefa como "feita" para não notificar novamente
                        task['done'] = True 
                        TASK_MANAGER.save_tasks()
            
            time.sleep(10) # Verifica a cada 10 segundos para não sobrecarregar

    def loop_voz(self):
        global RECALIBRAR_MIC
        r = sr.Recognizer(); r.pause_threshold = 0.8
        with sr.Microphone() as s:
            self.log_display("Calibrando..."); r.adjust_for_ambient_noise(s); self.log_display("OK.")
            while True:
                if RECALIBRAR_MIC: r.adjust_for_ambient_noise(s, duration=2); RECALIBRAR_MIC = False; falar("Recalibrado.")
                try:
                    a = r.listen(s, timeout=5, phrase_time_limit=10)
                    t = r.recognize_google(a, language="pt-BR").lower()
                    if self.mode_call and not any(w in t for w in TRIGGERS): continue
                    self.chat_display(t, "VOCÊ (Voz)", "user"); processar_comando(t)
                except: pass

if __name__ == "__main__":
    app = AeonGUI(); APP_REF = app; app.mainloop()