import os
import psutil
import pygetwindow as gw
import pyautogui
import shutil
import subprocess
import webbrowser
from typing import List, Dict, Any
from modules.base_module import AeonModule

class SistemaModule(AeonModule):
    """
    Módulo para interagir com o sistema operacional.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Sistema"
        self.dependencies = []
        self.pending_action = None
        self.indexed_apps = self.indexar_programas()
        
        # O process() antigo fica mais simples, os gatilhos podem ser removidos
        # pois a IA vai chamar os métodos diretamente.
        self.triggers = ["sistema", "janela", "status", "desempenho", "abre", "instalar", "desligar", "offline", "online"]

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "Sistema.obter_status_sistema",
                    "description": "Retorna o uso atual da CPU e da memória RAM do sistema.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.go_offline",
                    "description": "Força o cérebro do Aeon a usar apenas o modelo de linguagem local, desativando a conexão com a nuvem.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.go_online",
                    "description": "Tenta reconectar o cérebro do Aeon à nuvem para usar o modelo de linguagem online.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.focar_janela",
                    "description": "Muda o foco do sistema para uma janela específica pelo seu título.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "titulo_janela": {
                                "type": "string",
                                "description": "O título ou parte do título da janela para focar. Ex: 'Google Chrome', 'Visual Studio Code'"
                            }
                        },
                        "required": ["titulo_janela"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.instalar_pacote",
                    "description": "Instala um pacote Python usando pip.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome_pacote": {
                                "type": "string",
                                "description": "O nome do pacote a ser instalado. Ex: 'requests', 'numpy'"
                            }
                        },
                        "required": ["nome_pacote"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.desligar_computador",
                    "description": "Inicia o processo de desligamento do computador do usuário.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.reiniciar_computador",
                    "description": "Inicia o processo de reinicialização do computador do usuário.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.abrir_aplicativo",
                    "description": "Abre um aplicativo indexado no sistema, como 'calculadora' ou 'notepad'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome_app": {
                                "type": "string",
                                "description": "O nome do aplicativo a ser aberto. Ex: 'calculadora', 'bloco de notas', 'cmd'"
                            }
                        },
                        "required": ["nome_app"]
                    }
                }
            }
        ]

    def process(self, command: str) -> str:
        # Este método agora é apenas um fallback para comandos de bypass,
        # tornando as verificações mais explícitas para evitar falsos positivos.
        cmd_lower = command.lower()
        if cmd_lower == "status do sistema": return self.obter_status_sistema()
        if cmd_lower == "desligar computador": return self.desligar_computador()
        if cmd_lower == "reiniciar computador": return self.reiniciar_computador()
        if cmd_lower == "ficar offline": return self.go_offline()
        if cmd_lower == "ficar online": return self.go_online()
        
        # Mantém o gatilho "abre" um pouco mais flexível como exemplo de fallback
        if cmd_lower.startswith("abre "):
            app_name = command.replace("abre ", "").strip()
            return self.abrir_aplicativo(app_name)

        return "" # Retorna vazio se nenhum comando de fallback exato for encontrado

    def go_offline(self) -> str:
        """Força o cérebro a usar o modelo local."""
        brain = self.core_context.get("brain")
        if brain and hasattr(brain, 'force_offline'):
            return brain.force_offline()
        return "Não foi possível acessar o cérebro para forçar o modo offline."

    def go_online(self) -> str:
        """Tenta reconectar o cérebro ao modelo da nuvem."""
        brain = self.core_context.get("brain")
        if brain and hasattr(brain, 'force_online'):
            return brain.force_online()
        return "Não foi possível acessar o cérebro para forçar o modo online."

    def indexar_programas(self) -> dict:
        """Mapeia atalhos e nomes comuns de programas para seus caminhos/comandos."""
        apps = {
            "calculadora": "calc",
            "bloco de notas": "notepad",
            "notepad": "notepad",
            "cmd": "start cmd",
            "prompt": "start cmd",
            "explorer": "explorer",
            "arquivos": "explorer"
        }
        try:
            start_menu = os.path.join(os.environ["ProgramData"], r"Microsoft\Windows\Start Menu\Programs")
            for root, _, files in os.walk(start_menu):
                for file in files:
                    if file.endswith(".lnk"):
                        app_name = file.lower().replace(".lnk", "")
                        apps[app_name] = os.path.join(root, file)
        except Exception as e:
            print(f"[Sistema] Erro ao indexar programas: {e}")
        return apps

    def abrir_aplicativo(self, nome_app: str) -> str:
        """Abre um aplicativo pelo nome."""
        app_name_lower = nome_app.lower()
        path = self.indexed_apps.get(app_name_lower)
        
        if not path:
            # Tenta encontrar por correspondência parcial
            for indexed_name, indexed_path in self.indexed_apps.items():
                if app_name_lower in indexed_name:
                    path = indexed_path
                    break
        
        if path:
            try:
                os.startfile(path)
                return f"Abrindo {nome_app}..."
            except:
                os.system(path) # Fallback para comandos como 'cmd'
                return f"Iniciando {nome_app}..."
        else:
            return f"Não encontrei o aplicativo '{nome_app}'."

    def focar_janela(self, titulo_janela: str) -> str:
        """Muda o foco para uma janela com base no título."""
        try:
            # gw.getWindowsWithTitle é case-sensitive, então iteramos para ser flexível
            all_windows = gw.getAllTitles()
            target_win = None
            for title in all_windows:
                if titulo_janela.lower() in title.lower():
                    target_win = gw.getWindowsWithTitle(title)[0]
                    break
            
            if not target_win: return f"Nenhuma janela com o título '{titulo_janela}' encontrada."
            
            target_win.activate()
            return f"Foco alterado para a janela '{target_win.title[:30]}'."
        except Exception as e:
            return f"Ocorreu um erro ao focar na janela: {e}"

    def obter_status_sistema(self) -> str:
        """Retorna o uso de CPU e RAM."""
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        return f"No momento, o uso da CPU está em {cpu}% e a memória RAM em {ram}%."

    def desligar_computador(self) -> str:
        """Desliga o computador do usuário com um delay de 10 segundos."""
        os.system("shutdown /s /t 10")
        return "O computador será desligado em 10 segundos."

    def reiniciar_computador(self) -> str:
        """Reinicia o computador do usuário com um delay de 10 segundos."""
        os.system("shutdown /r /t 10")
        return "O computador será reiniciado em 10 segundos."

    def instalar_pacote(self, nome_pacote: str) -> str:
        """Instala um pacote Python usando pip em uma thread para não bloquear."""
        import sys
        import threading
        
        io_handler = self.core_context.get("io_handler")
        
        def install_in_thread():
            try:
                io_handler.falar(f"Iniciando instalação de {nome_pacote}.")
                subprocess.check_call([sys.executable, "-m", "pip", "install", nome_pacote])
                io_handler.falar(f"Pacote {nome_pacote} instalado com sucesso.")
            except Exception as e:
                print(f"[Sistema][ERRO] Falha ao instalar pacote: {e}")
                io_handler.falar(f"Desculpe, ocorreu um erro ao instalar o pacote {nome_pacote}.")
        
        threading.Thread(target=install_in_thread, daemon=True).start()
        return f"Certo. A instalação de '{nome_pacote}' foi iniciada em segundo plano."

    # Funções de suporte que não são expostas como ferramentas diretas
    def _check_battery(self) -> str:
        if not hasattr(psutil, "sensors_battery"):
            return "Não consigo ler sensores de bateria neste sistema."
        battery = psutil.sensors_battery()
        if battery:
            plugged = "conectado à energia" if battery.power_plugged else "usando bateria"
            percent = battery.percent
            return f"A bateria está em {percent}% e {plugged}."
        return "Este computador não parece ter uma bateria."