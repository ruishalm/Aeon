import os
import psutil
import pygetwindow as gw
import pyautogui
import shutil
import subprocess
import webbrowser
from typing import List, Dict
from modules.base_module import AeonModule

class SistemaModule(AeonModule):
    """
    Módulo para interagir com o sistema operacional:
    - Controle de janelas
    - Status do sistema (CPU/RAM)
    - Abrir aplicativos indexados
    - Gerenciamento de arquivos (criar/deletar pastas)
    - Controle de rolagem
    - Abrir e-mail
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Sistema"
        self.triggers = [
            "minimize", "minimizar", "maximize", "maximizar", "restaurar", "restore",
            "feche", "fechar", "close", "alterne para", "foco em", "janela",
            "status do sistema", "uso de cpu", "desempenho do pc",
            "abre", "iniciar", "role para", "scroll",
            "crie uma pasta", "delete", "apague", "exclua",
            "email", "sair", "desliga", "instalar pacote"
        ]
        self.pending_action = None
        self.indexed_apps = {}

    @property
    def dependencies(self) -> List[str]:
        """Sistema não depende de nenhum componente externo."""
        return []

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do módulo."""
        return {
            "version": "2.0.0",
            "author": "Aeon Core",
            "description": "Controla janelas, aplicativos e gerencia arquivos do sistema"
        }

    def on_load(self) -> bool:
        """Inicializa o módulo - indexa programas disponíveis."""
        try:
            self.indexed_apps = self.indexar_programas()
            return True
        except Exception as e:
            print(f"[SistemaModule] Erro ao carregar: {e}")
            return False

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        self.pending_action = None
        self.indexed_apps = {}
        return True

    def indexar_programas(self) -> dict:
        """Mapeia atalhos de programas do Menu Iniciar para seus caminhos."""
        apps = {"calc": "calc", "notepad": "notepad", "cmd": "start cmd", "explorer": "explorer"}
        start_menu = os.path.join(os.environ["ProgramData"], r"Microsoft\Windows\Start Menu\Programs")
        for root, _, files in os.walk(start_menu):
            for file in files:
                if file.endswith(".lnk"):
                    app_name = file.lower().replace(".lnk", "")
                    apps[app_name] = os.path.join(root, file)
        return apps

    def process(self, command: str) -> str:
        # Lógica de confirmação de ação pendente (Ex: deletar)
        if self.pending_action:
            action = self.pending_action
            self.pending_action = None # Limpa a ação
            if command in ["sim", "confirmo", "confirme", "pode"]:
                if action['type'] == 'delete':
                    return self.deletar_item(action['path'], confirmado=True)
            else:
                return "Ação cancelada."

        # Deleção
        delete_triggers = ["delete", "apague", "exclua"]
        if any(trigger in command for trigger in delete_triggers):
            item_name = command
            for trigger in delete_triggers:
                item_name = item_name.replace(trigger, "")
            item_name = item_name.replace("o arquivo", "").replace("a pasta", "").strip()
            if item_name:
                return self.deletar_item(item_name)
            else:
                return "Não entendi o que você quer deletar."

        # Controle de Janelas
        acoes_janela = {
            "minimize": "minimize", "minimizar": "minimize", "maximizar": "maximize",
            "restaurar": "restore", "feche": "close", "fechar": "close",
            "alterne para": "activate", "foco em": "activate"
        }
        for palavra, acao in acoes_janela.items():
            if palavra in command:
                partes = command.split(palavra)
                titulo = partes[1].strip() if len(partes) > 1 and partes[1].strip() else None
                return self.controlar_janela(acao, titulo)

        # Status do Sistema
        if any(t in command for t in ["status do sistema", "desempenho do pc"]):
            return self.obter_status_sistema()

        # Abrir Aplicativos
        if "abre" in command or "iniciar" in command:
            for name, path in self.indexed_apps.items():
                if name in command:
                    try:
                        os.startfile(path)
                        return f"Abrindo {name}..."
                    except:
                        os.system(path) # Fallback para comandos como 'cmd'
                        return f"Iniciando {name}..."

        # Criar Pasta
        if "crie uma pasta" in command:
            nome_pasta = command.split("crie uma pasta")[-1].strip()
            if nome_pasta:
                os.makedirs(nome_pasta, exist_ok=True)
                return f"Pasta '{nome_pasta}' criada."
            else:
                return "Qual nome você quer para a pasta?"
        
        # Rolagem
        if "role para cima" in command:
            pyautogui.scroll(300)
            return "" # Ação sem resposta verbal
        if "role para baixo" in command:
            pyautogui.scroll(-300)
            return ""

        # E-mail
        if "email" in command:
            webbrowser.open('mailto:')
            return "Abrindo seu cliente de e-mail."

        # Sair do programa
        if "sair" in command or "desliga" in command:
            io_handler = self.core_context.get("io_handler")
            if io_handler:
                io_handler.falar("Até logo.")
            import os as os_module
            os_module._exit(0)
            return ""

        # Instalar pacote Python
        if "instalar pacote" in command:
            pkg_name = command.split("instalar pacote")[-1].strip()
            if pkg_name:
                return self.instalar_pacote(pkg_name)
            else:
                return "Qual pacote você quer instalar?"

        return "" # Nenhum comando do módulo foi acionado

    def controlar_janela(self, acao: str, titulo_alvo: str = None) -> str:
        try:
            win = gw.getActiveWindow() if not titulo_alvo else gw.getWindowsWithTitle(titulo_alvo)[0]
            if not win: return "Nenhuma janela encontrada."
            
            if acao == 'minimize': win.minimize()
            elif acao == 'maximize': win.maximize()
            elif acao == 'restore': win.restore()
            elif acao == 'close': win.close()
            elif acao == 'activate': win.activate()
            
            return f"Janela '{win.title[:20]}...' {acao}."
        except Exception as e:
            return "Ocorreu um erro ao controlar a janela."

    def obter_status_sistema(self) -> str:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        return f"Uso da CPU em {cpu}% e memória RAM em {ram}%."

    def deletar_item(self, item_path: str, confirmado: bool = False) -> str:
        caminho_completo = os.path.abspath(item_path)
        if not os.path.exists(caminho_completo):
            return f"Desculpe, não encontrei '{item_path}'."

        if not confirmado:
            self.pending_action = {'type': 'delete', 'path': caminho_completo}
            return f"Atenção, esta ação é permanente. Você tem certeza que quer deletar '{os.path.basename(caminho_completo)}'?"
        else:
            try:
                if os.path.isfile(caminho_completo):
                    os.remove(caminho_completo)
                    return f"Arquivo '{os.path.basename(caminho_completo)}' deletado."
                elif os.path.isdir(caminho_completo):
                    shutil.rmtree(caminho_completo)
                    return f"A pasta '{os.path.basename(caminho_completo)}' foi deletada."
            except Exception as e:
                return f"Ocorreu um erro ao tentar deletar: {e}"
    def instalar_pacote(self, nome_pacote: str) -> str:
        """Instala um pacote Python usando pip em uma thread separada."""
        import sys
        import threading
        
        def install_in_thread():
            io_handler = self.core_context.get("io_handler")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", nome_pacote])
                if io_handler:
                    io_handler.falar(f"Pacote {nome_pacote} instalado com sucesso.")
            except Exception as e:
                if io_handler:
                    io_handler.falar(f"Erro ao instalar {nome_pacote}.")
        
        threading.Thread(target=install_in_thread, daemon=True).start()
        return f"Instalando o pacote {nome_pacote}. Aguarde..."