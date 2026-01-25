import customtkinter as ctk
import psutil
import threading
import sys
import os
import subprocess
import shutil

# Importações do Core
from core.module_manager import ModuleManager
from core.io_handler import IOHandler
from core.config_manager import ConfigManager
from core.context_manager import ContextManager

# Tenta importar Brain de forma robusta
try:
    from core.brain import AeonBrain as Brain
except ImportError:
    try:
        from core.brain import Brain
    except ImportError:
        print("ERRO CRÍTICO: Classe Brain não encontrada.")

# CONFIGURAÇÕES DE TEMA (CYBERPUNK)
C = {
    "bg": "#0d1117", "panel_bg": "#161b22", "accent_primary": "#58a6ff", 
    "accent_secondary": "#238636", "accent_alert": "#da3633", "text_main": "#c9d1d9", 
    "text_dim": "#8b949e", "code_bg": "#000000", "user_bubble": "#1f6feb", "bot_bubble": "#21262d"
}

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class AeonGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.config_manager = ConfigManager()
        cfg = getattr(self.config_manager, 'config', {}) 
        self.io_handler = IOHandler(cfg, None)
        
        try:
            self.brain = Brain(self.config_manager)
        except Exception as e:
            print(f"[GUI] Erro ao iniciar Brain: {e}")
            self.brain = None

        self.context_manager = ContextManager() 
        
        # Ajuste de caminho: Como este arquivo está em /core, subimos um nível para achar a raiz
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.workspace_path = os.path.join(root_dir, "workspace")
        os.makedirs(self.workspace_path, exist_ok=True)

        self.core_context = {
            "config_manager": self.config_manager,
            "io_handler": self.io_handler,
            "brain": self.brain,
            "context": self.context_manager,
            "gui": self,
            "workspace": self.workspace_path
        }

        self.module_manager = ModuleManager(self.core_context)
        self.core_context["module_manager"] = self.module_manager
        self.module_manager.load_modules()

        self.title("AEON V85 // NEURAL INTERFACE")
        self.geometry("1200x700")
        self.configure(fg_color=C["bg"])
        self.minsize(1000, 600)

        self.grid_columnconfigure(0, weight=1, minsize=250) 
        self.grid_columnconfigure(1, weight=3, minsize=500) 
        self.grid_columnconfigure(2, weight=1, minsize=300) 
        self.grid_rowconfigure(0, weight=1)

        self.setup_left_panel()
        self.setup_center_panel()
        self.setup_right_panel()

        self.running = True
        
        # Configura limpeza automática ao fechar e ao abrir
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        threading.Thread(target=self.cleanup_temp_files, daemon=True).start()

        threading.Thread(target=self.loop_vitals, daemon=True).start()
        
        self.add_message("Sistema Online. V85 Estabilizada.", "SISTEMA")
        self.update_module_list()

    def setup_left_panel(self):
        self.frame_left = ctk.CTkFrame(self, fg_color=C["panel_bg"], corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nsew", padx=(0,1), pady=0)
        
        ctk.CTkLabel(self.frame_left, text="SYSTEM STATUS", font=("Consolas", 14, "bold"), text_color=C["text_dim"]).pack(pady=(20, 15), padx=20, anchor="w")

        self.status_frame = ctk.CTkFrame(self.frame_left, fg_color=C["panel_bg"])
        self.status_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.led_online = self._create_led(self.status_frame, "NUVEM (GROQ)", C["accent_alert"])
        self.led_online.pack(side="top", fill="x", pady=2)
        
        self.led_local = self._create_led(self.status_frame, "NEURAL (LOCAL)", C["accent_alert"])
        self.led_local.pack(side="top", fill="x", pady=2)

        ctk.CTkFrame(self.frame_left, height=2, fg_color="#30363d").pack(fill="x", padx=20, pady=10)
        
        self.lbl_cpu = ctk.CTkLabel(self.frame_left, text="CPU: 0%", font=("Consolas", 12), text_color=C["text_main"])
        self.lbl_cpu.pack(padx=20, anchor="w")
        self.bar_cpu = ctk.CTkProgressBar(self.frame_left, progress_color=C["accent_secondary"])
        self.bar_cpu.pack(padx=20, pady=(0, 15), fill="x")
        
        self.lbl_ram = ctk.CTkLabel(self.frame_left, text="RAM: 0%", font=("Consolas", 12), text_color=C["text_main"])
        self.lbl_ram.pack(padx=20, anchor="w")
        self.bar_ram = ctk.CTkProgressBar(self.frame_left, progress_color=C["accent_primary"])
        self.bar_ram.pack(padx=20, pady=(0, 20), fill="x")

        ctk.CTkFrame(self.frame_left, height=2, fg_color="#30363d").pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(self.frame_left, text="ACTIVE MODULES", font=("Consolas", 14, "bold"), text_color=C["text_dim"]).pack(pady=10, padx=20, anchor="w")
        
        self.scroll_modules = ctk.CTkScrollableFrame(self.frame_left, fg_color=C["panel_bg"])
        self.scroll_modules.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_led(self, parent, text, color):
        frame = ctk.CTkFrame(parent, fg_color=C["panel_bg"])
        canvas = ctk.CTkCanvas(frame, width=12, height=12, bg=C["panel_bg"], highlightthickness=0)
        canvas.pack(side="left", padx=(0, 10))
        led_id = canvas.create_oval(2, 2, 10, 10, fill=color, outline="")
        label = ctk.CTkLabel(frame, text=text, font=("Consolas", 11, "bold"), text_color=C["text_dim"])
        label.pack(side="left")
        frame.canvas = canvas
        frame.led = led_id
        return frame

    def update_module_list(self):
        for widget in self.scroll_modules.winfo_children():
            widget.destroy()
        try:
            modules = self.module_manager.get_loaded_modules()
            for mod in modules:
                self.add_module_status(mod.name, True)
        except Exception as e:
            print(f"[GUI_ERROR] Falha lista: {e}")

    def add_module_status(self, name, active):
        row = ctk.CTkFrame(self.scroll_modules, fg_color=C["panel_bg"])
        row.pack(fill="x", pady=2)
        color = C["accent_secondary"] if active else C["accent_alert"]
        status_text = "ONLINE" if active else "OFFLINE"
        canvas = ctk.CTkCanvas(row, width=10, height=10, bg=C["panel_bg"], highlightthickness=0)
        canvas.pack(side="left", padx=(5,10))
        canvas.create_oval(1, 1, 9, 9, fill=color, outline="")
        ctk.CTkLabel(row, text=name, font=("Consolas", 12), text_color=C["text_main"]).pack(side="left")
        ctk.CTkLabel(row, text=status_text, font=("Consolas", 10), text_color=C["text_dim"]).pack(side="right", padx=5)

    def setup_center_panel(self):
        self.frame_center = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self.frame_center.grid(row=0, column=1, sticky="nsew")
        self.frame_center.grid_rowconfigure(0, weight=1)
        self.frame_center.grid_columnconfigure(0, weight=1)

        self.chat_feed = ctk.CTkScrollableFrame(self.frame_center, fg_color=C["bg"])
        self.chat_feed.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self.input_container = ctk.CTkFrame(self.frame_center, fg_color=C["panel_bg"], height=60)
        self.input_container.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        self.entry_msg = ctk.CTkEntry(self.input_container, placeholder_text="Comando...", font=("Consolas", 14), border_width=0, fg_color=C["panel_bg"], text_color=C["text_main"])
        self.entry_msg.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        self.entry_msg.bind("<Return>", self.send_message_event)

        self.btn_shush = ctk.CTkButton(self.input_container, text="XIU", width=50, fg_color=C["accent_alert"], font=("Consolas", 12, "bold"), command=self.io_handler.calar_boca)
        self.btn_shush.pack(side="right", padx=15)

    def _prevent_typing(self, event): return "break"

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def add_message(self, text, sender="VOCÊ"):
        msg_frame = ctk.CTkFrame(self.chat_feed, fg_color=C["bg"])
        msg_frame.pack(fill="x", pady=5)
        align, bubble_color, text_color = ("e", C["user_bubble"], "white") if sender == "VOCÊ" else ("w", C["bot_bubble"], C["text_main"])

        ctk.CTkLabel(msg_frame, text=sender, font=("Consolas", 10, "bold"), text_color=C["text_dim"]).pack(anchor=align, padx=5)

        parts = text.split("```")
        for i, part in enumerate(parts):
            if not part.strip(): continue
            is_code = i % 2 != 0
            bg_color = C["code_bg"] if is_code else bubble_color
            border_c = "#30363d" if is_code else bg_color 

            parent_widget = msg_frame
            
            if is_code:
                code_container = ctk.CTkFrame(msg_frame, fg_color="transparent")
                code_container.pack(fill="x", pady=2, padx=5)
                header = ctk.CTkFrame(code_container, fg_color=bg_color, corner_radius=6, height=25)
                header.pack(fill="x", pady=(0,0))
                ctk.CTkButton(header, text="📋 Copiar", width=60, height=20, font=("Consolas", 10), fg_color="#238636", hover_color="#2ea043", command=lambda t=part.strip(): self.copy_to_clipboard(t)).pack(side="right", padx=5, pady=2)
                parent_widget = code_container

            textbox = ctk.CTkTextbox(parent_widget, 
                                     font=("Consolas" if is_code else "Roboto", 13 if is_code else 14), 
                                     fg_color=bg_color, 
                                     text_color="#3fb950" if is_code else text_color,
                                     border_width=1 if is_code else 0,
                                     border_color=border_c,
                                     corner_radius=12 if not is_code else 6,
                                     wrap="word" if not is_code else "none")
            
            textbox.insert("0.0", part.strip())
            num_lines = len(part.strip().split('\n'))
            height = min(num_lines * 22 + 20, 400 if is_code else 600)
            textbox.configure(height=height)
            textbox.bind("<KeyPress>", self._prevent_typing)
            textbox.bind("<KeyRelease>", self._prevent_typing)
            textbox.pack(anchor=align if not is_code else "center", pady=2 if not is_code else 0, padx=5 if not is_code else 0, ipady=5, fill="x" if is_code else "none")
            
        self.after(100, lambda: self.chat_feed._parent_canvas.yview_moveto(1.0))

    def send_message_event(self, event=None):
        txt = self.entry_msg.get()
        if txt:
            self.add_message(txt, "VOCÊ")
            self.entry_msg.delete(0, "end")
            threading.Thread(target=self.process_in_background, args=(txt,), daemon=True).start()

    def process_in_background(self, txt):
        try:
            response = self.module_manager.route_command(txt)
            self.after(0, lambda: self.add_message(response, "AEON"))
            self.after(0, lambda: self.io_handler.falar(response))
        except Exception as e:
            self.after(0, lambda: self.add_message(f"Erro Crítico: {e}", "SISTEMA"))

    def toggle_mic(self):
        threading.Thread(target=self.process_in_background, args=("ativar escuta",), daemon=True).start()

    def setup_right_panel(self):
        self.frame_right = ctk.CTkFrame(self, fg_color=C["panel_bg"], corner_radius=0)
        self.frame_right.grid(row=0, column=2, sticky="nsew", padx=(1,0), pady=0)
        
        self.tabs = ctk.CTkTabview(self.frame_right, fg_color=C["panel_bg"])
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabs.add("WORKSPACE")
        self.tabs.add("LOGS")

        self.workspace_frame = self.tabs.tab("WORKSPACE")
        self.workspace_frame.grid_columnconfigure(0, weight=1)
        self.workspace_frame.grid_rowconfigure(1, weight=1)

        button_frame = ctk.CTkFrame(self.workspace_frame, fg_color="transparent")
        button_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        refresh_btn = ctk.CTkButton(button_frame, text="Refresh", font=("Consolas", 12), command=self.refresh_workspace_view)
        refresh_btn.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        
        open_folder_btn = ctk.CTkButton(button_frame, text="Abrir Pasta", font=("Consolas", 12), command=self.open_workspace_folder)
        open_folder_btn.grid(row=0, column=1, sticky="ew", padx=(2, 0))

        self.workspace_tree_frame = ctk.CTkScrollableFrame(self.workspace_frame, fg_color="transparent")
        self.workspace_tree_frame.grid(row=1, column=0, sticky="nsew")

        self.after(200, self.refresh_workspace_view)

    def open_workspace_folder(self):
        try:
            if os.path.exists(self.workspace_path):
                os.startfile(self.workspace_path)
            else:
                print(f"[GUI_ERROR] Workspace não encontrado: {self.workspace_path}")
        except Exception as e:
            print(f"[GUI_ERROR] Erro ao abrir pasta: {e}")

    def refresh_workspace_view(self):
        for widget in self.workspace_tree_frame.winfo_children():
            widget.destroy()
        
        if os.path.exists(self.workspace_path):
            self._populate_workspace_tree(self.workspace_tree_frame, self.workspace_path, indent=0)

    def _populate_workspace_tree(self, parent, path, indent=0):
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                item_frame = ctk.CTkFrame(parent, fg_color="transparent")
                item_frame.pack(fill="x", anchor="w")
                icon = "📁" if os.path.isdir(item_path) else "📄"
                label_text = f"{' ' * indent * 2}{icon} {item}"
                ctk.CTkLabel(item_frame, text=label_text, font=("Consolas", 12), text_color=C["text_main"]).pack(side="left", padx=5, pady=2)
                if os.path.isdir(item_path):
                    self._populate_workspace_tree(parent, item_path, indent + 1)
        except: pass

    def cleanup_temp_files(self):
        """Limpa arquivos temporários (áudio e cache) para manter o pendrive leve."""
        try:
            # Ajuste de caminho: sobe um nível para achar a raiz
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # 1. Limpa Cache de Áudio (bagagem/temp)
            audio_temp = os.path.join(root_dir, "bagagem", "temp")
            if os.path.exists(audio_temp):
                for f in os.listdir(audio_temp):
                    fp = os.path.join(audio_temp, f)
                    try:
                        if os.path.isfile(fp):
                            os.remove(fp)
                    except: pass

            # 2. Limpa __pycache__ recursivamente
            for root, dirs, files in os.walk(root_dir):
                for d in list(dirs):
                    if d == "__pycache__":
                        try:
                            shutil.rmtree(os.path.join(root, d))
                            dirs.remove(d)
                        except: pass
            print("[SISTEMA] Limpeza automática concluída.")
        except Exception as e:
            print(f"[SISTEMA] Erro na limpeza automática: {e}")

    def on_closing(self):
        """Executa limpeza e encerra o programa."""
        self.running = False
        self.cleanup_temp_files()
        self.destroy()
        sys.exit(0)

    def loop_vitals(self):
        if not self.running: return
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            self.after(0, self.update_vitals, cpu, ram)
        except: pass
        self.after(1000, self.loop_vitals)

    def update_vitals(self, cpu, ram):
        try:
            self.bar_cpu.set(cpu / 100)
            self.lbl_cpu.configure(text=f"CPU: {cpu}%")
            self.bar_ram.set(ram / 100)
            self.lbl_ram.configure(text=f"RAM: {ram}%")
            if hasattr(self, 'brain') and self.brain:
                online = getattr(self.brain, 'online', False)
                cor_online = C["accent_primary"] if online else C["accent_alert"]
                self.led_online.canvas.itemconfig(self.led_online.led, fill=cor_online)
        except: pass