import pyautogui
import pygetwindow as gw
import os
import time
import threading
from typing import List, Dict
from modules.base_module import AeonModule

class MidiaModule(AeonModule):
    """
    Modulo para controlar a reproducao de midia e o Spotify.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Midia"
        # Gatilhos gerais de midia (spotify deveria ser aberto via Sistema.abrir_aplicativo)
        self.triggers = [
            "tocar", "toca", "pausar", "continuar", "play",
            "proxima", "avancar", "next",
            "anterior", "voltar", "previous"
        ]

    @property
    def dependencies(self) -> List[str]:
        """Midia nao depende de componentes do core."""
        return []

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do modulo."""
        return {
            "version": "2.0.0",
            "author": "Aeon Core",
            "description": "Controla reproducao de midia e Spotify"
        }

    def on_load(self) -> bool:
        """Inicializa o modulo."""
        return True

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        return True

    def get_tools(self) -> List[Dict[str, any]]:
        """Expõe ferramentas de mídia para o Brain."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "Midia.play_pause",
                    "description": "Reproduz ou pausa a mídia atual.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Midia.proxima_faixa",
                    "description": "Toca a próxima faixa de música.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Midia.faixa_anterior",
                    "description": "Volta à faixa anterior de música.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Midia.tocar_no_spotify",
                    "description": "Toca uma música específica no Spotify.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "song_name": {"type": "string", "description": "Nome da música a tocar."}
                        },
                        "required": ["song_name"]
                    }
                }
            }
        ]

    def play_pause(self) -> str:
        """Ferramenta: play/pause."""
        pyautogui.press('playpause')
        return "Mídia pausada/retomada."

    def proxima_faixa(self) -> str:
        """Ferramenta: próxima faixa."""
        pyautogui.press('nexttrack')
        return "Próxima faixa."

    def faixa_anterior(self) -> str:
        """Ferramenta: faixa anterior."""
        pyautogui.press('prevtrack')
        return "Faixa anterior."

    def process(self, command: str) -> str:
        # Logica de Controle de Midia Generico
        media_play = ["tocar", "toca", "pausar", "continuar", "retomar", "play"]
        media_next = ["proxima", "avancar", "next", "proxima"]
        media_prev = ["anterior", "voltar", "previous"]

        # Evita que "tocar no spotify" acione o play/pause generico
        if "spotify" not in command:
            if any(t in command for t in media_play):
                pyautogui.press('playpause')
                return "Ok."
            if any(t in command for t in media_next):
                pyautogui.press('nexttrack')
                return "Proxima."
            if any(t in command for t in media_prev):
                pyautogui.press('prevtrack')
                return "Voltando."

        # Logica do Spotify
        if "spotify" in command:
            if "tocar" in command:
                song_name = command.split("tocar")[-1].replace("no spotify", "").strip()
                if song_name:
                    self.tocar_no_spotify(song_name)
                    return f"Tocando {song_name} no Spotify."
                else:
                    return "Nao entendi o nome da musica que voce quer tocar."
        
        return "" # Nenhum gatilho especifico do modulo foi acionado

    def tocar_no_spotify(self, song_name: str):
        """
        Abre o Spotify, busca pela musica e a toca.
        Executa em uma thread para nao bloquear o assistente.
        """
        def spotify_thread():
            try:
                # 1. Ativa a janela do Spotify se aberta
                spotify_wins = gw.getWindowsWithTitle('Spotify')
                if spotify_wins:
                    spotify_wins[0].activate()
                    time.sleep(0.5)
                else:
                    # 2. Abre o app se fechado
                    os.startfile("spotify:")
                    time.sleep(4) # Espera o app abrir

                # 3. Atalho de busca (Ctrl+L)
                pyautogui.hotkey('ctrl', 'l')
                time.sleep(0.5)
                
                # 4. Digita a musica
                pyautogui.write(song_name, interval=0.05)
                time.sleep(1)
                pyautogui.press('enter')
                time.sleep(2) # Espera a busca
                
                # 5. Pressiona Enter para tocar o primeiro resultado
                pyautogui.press('enter')
            except Exception as e:
                # Idealmente, logar isso
                print(f"Erro no modulo Spotify: {e}")
                io_handler = self.core_context.get("io_handler")
                if io_handler:
                    io_handler.falar("Nao consegui controlar o Spotify. Verifique se ele esta instalado.")

        # Inicia a automacao em uma thread separada
        threading.Thread(target=spotify_thread).start()
