import pyautogui
import pygetwindow as gw
import os
import time
import threading
from typing import List, Dict
from modules.base_module import AeonModule

class MidiaModule(AeonModule):
    """
    Módulo para controlar a reprodução de mídia e o Spotify.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Mídia"
        # Gatilhos gerais de mídia e gatilhos específicos do Spotify
        self.triggers = [
            "tocar", "pausar", "continuar", "play",
            "próxima", "avançar", "next",
            "anterior", "voltar", "previous",
            "spotify"
        ]

    @property
    def dependencies(self) -> List[str]:
        """Mídia não depende de componentes do core."""
        return []

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do módulo."""
        return {
            "version": "2.0.0",
            "author": "Aeon Core",
            "description": "Controla reprodução de mídia e Spotify"
        }

    def on_load(self) -> bool:
        """Inicializa o módulo."""
        return True

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        return True

    def process(self, command: str) -> str:
        # Lógica de Controle de Mídia Genérico
        media_play = ["tocar", "pausar", "continuar", "retomar", "play"]
        media_next = ["próxima", "avançar", "next", "proxima"]
        media_prev = ["anterior", "voltar", "previous"]

        # Evita que "tocar no spotify" acione o play/pause genérico
        if "spotify" not in command:
            if any(t in command for t in media_play):
                pyautogui.press('playpause')
                return "Ok."
            if any(t in command for t in media_next):
                pyautogui.press('nexttrack')
                return "Próxima."
            if any(t in command for t in media_prev):
                pyautogui.press('prevtrack')
                return "Voltando."

        # Lógica do Spotify
        if "spotify" in command:
            if "tocar" in command:
                song_name = command.split("tocar")[-1].replace("no spotify", "").strip()
                if song_name:
                    self.tocar_no_spotify(song_name)
                    return f"Entendido. Vou tocar {song_name} no Spotify."
                else:
                    return "Não entendi o nome da música que você quer tocar."
        
        return "" # Nenhum gatilho específico do módulo foi acionado

    def tocar_no_spotify(self, song_name: str):
        """
        Abre o Spotify, busca pela música e a toca.
        Executa em uma thread para não bloquear o assistente.
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
                
                # 4. Digita a música
                pyautogui.write(song_name, interval=0.05)
                time.sleep(1)
                pyautogui.press('enter')
                time.sleep(2) # Espera a busca
                
                # 5. Pressiona Enter para tocar o primeiro resultado
                pyautogui.press('enter')
            except Exception as e:
                # Idealmente, logar isso
                print(f"Erro no módulo Spotify: {e}")
                io_handler = self.core_context.get("io_handler")
                if io_handler:
                    io_handler.falar("Não consegui controlar o Spotify. Verifique se ele está instalado.")

        # Inicia a automação em uma thread separada
        threading.Thread(target=spotify_thread).start()
