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
    Modulo para interagir com o sistema operacional.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Sistema"
        self.dependencies = []
        self.pending_action = None
        self.waiting_exit_confirmation = False  # Flag para confirmar saida
        self.indexed_apps = self.indexar_programas()
        
        # O process() antigo fica mais simples, os gatilhos podem ser removidos
        # pois a IA vai chamar os metodos diretamente.
        self.triggers = ["sistema", "janela", "status", "desempenho", "abre", "abra", "instalar", "desligar", "offline", "online", "sair", "parar", "fechar", "exit", "quit", "listar modulos", "modulos", "qual", "modo oculto", "ficar invisivel", "modo terminal", "abrir terminal", "expandir"]

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "Sistema.alternar_terminal",
                    "description": "Alterna a interface entre o modo esfera e o modo terminal completo.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.toggle_stealth_mode",
                    "description": "Ativa ou desativa o modo oculto (invisível/privado). Quando ativo, o Aeon não salva históricos ou aprendizados da conversa.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.obter_status_sistema",
                    "description": "Retorna o uso atual da CPU e da memoria RAM do sistema.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.go_offline",
                    "description": "Forca o cerebro do Aeon a usar apenas o modelo de linguagem local, desativando a conexao com a nuvem.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.go_online",
                    "description": "Tenta reconectar o cerebro do Aeon a nuvem para usar o modelo de linguagem online.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.focar_janela",
                    "description": "Muda o foco do sistema para uma janela especifica pelo seu titulo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "titulo_janela": {
                                "type": "string",
                                "description": "O titulo ou parte do titulo da janela para focar. Ex: 'Google Chrome', 'Visual Studio Code'"
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
                    "description": "Inicia o processo de desligamento do computador do usuario.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Sistema.reiniciar_computador",
                    "description": "Inicia o processo de reinicializacao do computador do usuario.",
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
            ,
            {
                "type": "function",
                "function": {
                    "name": "Sistema.fechar_aplicativo",
                    "description": "Fecha um aplicativo pelo nome (tenta janela, depois mata processo).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nome_app": {"type": "string", "description": "Nome do app a fechar"}
                        },
                        "required": ["nome_app"]
                    }
                }
            }
        ]

    def process(self, command: str) -> str:
        # Este metodo agora e apenas um fallback para comandos de bypass,
        # tornando as verificacoes mais explicitas para evitar falsos positivos.
        cmd_lower = command.lower().strip()
        
        # Confirmacao de saida
        if self.waiting_exit_confirmation:
            if any(x in cmd_lower for x in ["sim", "confirmo", "confirmar", "yes", "ok", "sair de verdade", "sair mesmo"]):
                self.waiting_exit_confirmation = False
                import threading
                def exit_delayed():
                    import time
                    import os
                    time.sleep(0.5)
                    print("[SISTEMA] Encerrando...")
                    os._exit(0)
                t = threading.Thread(target=exit_delayed)
                t.start()
                return "Até logo! Encerrando Aeon..."
            else:
                self.waiting_exit_confirmation = False
                # Se havia foco no módulo, liberá-lo
                mm = self.core_context.get("module_manager")
                if mm:
                    try:
                        mm.release_focus()
                    except Exception:
                        pass
                return "Saida cancelada. Continuamos aqui!"
        
        # IMPORTANTE: diferencia "fechar [app]" (fechar aplicativo) de "sair" (sair do Aeon)
        # Se tem algo após "fechar", é para fechar um app específico
        if cmd_lower.startswith("fechar ") or cmd_lower.startswith("fecha "):
            import re
            app_name = re.sub(r'^(fechar|fecha)\s+(o|a|os|as)?\s*', '', cmd_lower, flags=re.IGNORECASE).strip()
            if app_name and app_name not in ["aeon", "o aeon", "o programa"]:
                return self.fechar_aplicativo(app_name)
        
        # Comandos de saida/parada - primeira vez pede confirmacao
        if any(x in cmd_lower for x in ["sair", "parar", "exit", "quit"]):
            self.waiting_exit_confirmation = True
            # Põe este módulo em foco para capturar a confirmação seguinte
            mm = self.core_context.get("module_manager")
            if mm:
                try:
                    mm.lock_focus(self)
                except Exception:
                    pass
            return "Tem certeza que quer sair? (diga 'sim' para confirmar)"
        
        # Listar modulos disponiveis
        if any(x in cmd_lower for x in ["listar modulos", "quais modulos", "modulos disponiveis", "que modulos", "quais sao os modulos"]):
            return self.listar_modulos_disponiveis()
        
        if any(x in cmd_lower for x in ["modo oculto", "ficar invisivel", "modo invisivel", "modo privado", "nao grave", "nao salve"]):
            return self.toggle_stealth_mode()
        
        if cmd_lower == "status do sistema": return self.obter_status_sistema()
        if cmd_lower == "desligar computador": return self.desligar_computador()
        if cmd_lower == "reiniciar computador": return self.reiniciar_computador()
        if cmd_lower == "ficar offline": return self.go_offline()

        if cmd_lower == "ficar online": return self.go_online()
        
        # Mantem o gatilho "abre/abra/abrir" flexivel para abrir aplicativos
        import re
        m = re.sub(r'^(abre|abra|abrir)\s+(o|a|os|as)?\s*', '', cmd_lower)
        if m and m != cmd_lower:
            app_name = m.strip()
            return self.abrir_aplicativo(app_name)

        return "" # Retorna vazio se nenhum comando de fallback exato for encontrado

    def listar_modulos_disponiveis(self) -> str:
        """Lista todos os modulos carregados e disponiveis."""
        module_manager = self.core_context.get("module_manager")
        if not module_manager:
            return "Gerenciador de modulos nao disponivel."
        
        modulos = module_manager.get_loaded_modules()
        if not modulos:
            return "Nenhum modulo carregado."
        
        lista = "Modulos disponiveis:\n"
        for mod in modulos:
            triggers = ", ".join(mod.triggers[:3]) if mod.triggers else "sem triggers"
            lista += f"- {mod.name}: {triggers}\n"
        
        return lista.strip()

    def go_offline(self) -> str:
        """Forca o cerebro a usar o modelo local."""
        brain = self.core_context.get("brain")
        if brain and hasattr(brain, 'force_offline'):
            return brain.force_offline()
        return "Nao foi possivel acessar o cerebro para forcar o modo offline."

    def go_online(self) -> str:
        """Tenta reconectar o cerebro ao modelo da nuvem."""
        brain = self.core_context.get("brain")
        if brain and hasattr(brain, 'force_online'):
            return brain.force_online()
        return "Nao foi possivel acessar o cerebro para forcar o modo online."

    def indexar_programas(self) -> dict:
        """Mapeia atalhos e nomes comuns de programas para seus caminhos/comandos."""
        apps = {
            "calculadora": "calc",
            "bloco de notas": "notepad",
            "notepad": "notepad",
            "cmd": "start cmd",
            "prompt": "start cmd",
            "explorer": "explorer",
            "arquivos": "explorer",
            "spotify": "spotify"  # Microsoft Store app
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
        
        # Adiciona suporte para apps do Microsoft Store (WindowsApps)
        try:
            windows_apps = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps")
            if os.path.exists(windows_apps):
                for file in os.listdir(windows_apps):
                    if file.endswith(".exe"):
                        app_name = file.lower().replace(".exe", "")
                        app_path = os.path.join(windows_apps, file)
                        apps[app_name] = app_path
        except Exception as e:
            print(f"[Sistema] Erro ao indexar WindowsApps: {e}")
        
        return apps

    def abrir_aplicativo(self, nome_app: str) -> str:
        """Abre um aplicativo pelo nome."""
        # Limpa cortesias/pedidos como 'por favor', 'para mim' que atrapalham o matching
        def _clean_name(n: str) -> str:
            s = n.strip()
            s = s.rstrip('.,')
            lower = s.lower()
            suffixes = ["por favor", "para mim", "por gentileza", "porfa", "pra mim", "por favor.", ", por favor", "por favor,"]
            for suf in suffixes:
                if lower.endswith(suf):
                    s = s[: -len(suf)].strip()
                    lower = s.lower()
            # remove leading articles
            lower = s.lower()
            s = re.sub(r'^(o |a |os |as |o\'|a\')', '', lower).strip()
            return s

        import re
        nome_app = _clean_name(nome_app)
        app_name_lower = nome_app.lower()
        path = self.indexed_apps.get(app_name_lower)

        if not path:
            # Tenta encontrar por correspondencia parcial
            for indexed_name, indexed_path in self.indexed_apps.items():
                if app_name_lower in indexed_name:
                    path = indexed_path
                    break

        if path:
            try:
                os.startfile(path)
                return f"Abrindo {nome_app}..."
            except Exception:
                try:
                    os.system(path) # Fallback para comandos como 'cmd'
                    return f"Iniciando {nome_app}..."
                except Exception as e:
                    return f"Falha ao iniciar {nome_app}: {e}"
        else:
            return f"Nao encontrei o aplicativo '{nome_app}'."

    def fechar_aplicativo(self, nome_app: str) -> str:
        """Tenta fechar um aplicativo pelo titulo da janela ou matando processos que correspondam."""
        target = nome_app.lower().strip()
        try:
            # Tenta fechar por janela
            for title in gw.getAllTitles():
                if target in (title or '').lower():
                    wins = gw.getWindowsWithTitle(title)
                    if wins:
                        win = wins[0]
                        try:
                            win.close()
                            return f"Fechando {nome_app}..."
                        except Exception:
                            pass
        except Exception:
            pass

        # Fallback: matar processos matching
        try:
            killed = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = (proc.info.get('name') or '').lower()
                    cmd = ' '.join(proc.info.get('cmdline') or []).lower()
                    if target in name or target in cmd:
                        proc.terminate()
                        killed.append(proc.pid)
                except Exception:
                    pass
            if killed:
                return f"Fechando {nome_app} (PIDs: {killed})"
        except Exception as e:
            return f"Erro ao fechar aplicativo: {e}"

        return f"Nao encontrei o aplicativo '{nome_app}'."

    def focar_janela(self, titulo_janela: str) -> str:
        """Muda o foco para uma janela com base no titulo."""
        try:
            # gw.getWindowsWithTitle e case-sensitive, entao iteramos para ser flexivel
            all_windows = gw.getAllTitles()
            target_win = None
            for title in all_windows:
                if titulo_janela.lower() in title.lower():
                    target_win = gw.getWindowsWithTitle(title)[0]
                    break
            
            if not target_win: return f"Nenhuma janela com o titulo '{titulo_janela}' encontrada."
            
            target_win.activate()
            return f"Foco alterado para a janela '{target_win.title[:30]}'."
        except Exception as e:
            return f"Ocorreu um erro ao focar na janela: {e}"

    def obter_status_sistema(self) -> str:
        """Retorna o uso de CPU e RAM."""
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        return f"No momento, o uso da CPU esta em {cpu}% e a memoria RAM em {ram}%."

    def desligar_computador(self) -> str:
        """Desliga o computador do usuario com um delay de 10 segundos."""
        os.system("shutdown /s /t 10")
        return "O computador sera desligado em 10 segundos."

    def reiniciar_computador(self) -> str:
        """Reinicia o computador do usuario com um delay de 10 segundos."""
        os.system("shutdown /r /t 10")
        return "O computador sera reiniciado em 10 segundos."

    def instalar_pacote(self, nome_pacote: str) -> str:
        """Instala um pacote Python usando pip em uma thread para nao bloquear."""
        import sys
        import threading
        
        io_handler = self.core_context.get("io_handler")
        
        def install_in_thread():
            try:
                io_handler.falar(f"Iniciando instalacao de {nome_pacote}.")
                subprocess.check_call([sys.executable, "-m", "pip", "install", nome_pacote])
                io_handler.falar(f"Pacote {nome_pacote} instalado com sucesso.")
            except Exception as e:
                print(f"[Sistema][ERRO] Falha ao instalar pacote: {e}")
                io_handler.falar(f"Desculpe, ocorreu um erro ao instalar o pacote {nome_pacote}.")
        
        threading.Thread(target=install_in_thread, daemon=True).start()
        return f"Certo. A instalacao de '{nome_pacote}' foi iniciada em segundo plano."

    def toggle_stealth_mode(self) -> str:
        """Ativa ou desativa o modo oculto, onde o Aeon não registra logs de conversa."""
        cm = self.core_context.get('context_manager')
        if not cm:
            return "Gerenciador de contexto não encontrado. Não é possível alterar o modo oculto."

        is_stealth = cm.get('stealth_mode', False)
        new_state = not is_stealth
        cm.set('stealth_mode', new_state)

        if new_state:
            return "Modo oculto ativado. As conversas não serão mais registradas."
        else:
            return "Modo oculto desativado. O aprendizado e os registros de conversa foram reativados."

    def alternar_terminal(self) -> str:
        """Alterna a visualização da GUI entre modo esfera e modo terminal."""
        gui = self.core_context.get('gui')
        if gui and hasattr(gui, 'toggle_terminal_mode'):
            gui.toggle_terminal_mode()
            return "Alternando modo do terminal."
        return "Não foi possível alternar a interface."

    # Funcoes de suporte que nao sao expostas como ferramentas diretas
    def _check_battery(self) -> str:
        if not hasattr(psutil, "sensors_battery"):
            return "Nao consigo ler sensores de bateria neste sistema."
        battery = psutil.sensors_battery()
        if battery:
            plugged = "conectado a energia" if battery.power_plugged else "usando bateria"
            percent = battery.percent
            return f"A bateria esta em {percent}% e {plugged}."
        return "Este computador nao parece ter uma bateria."