"""
TypewriterModule (Datilografo)
==============================

Permite digitar em qualquer aplicativo COM SUPORTE A ACENTUACAO CORRETA.

Triggers: "modo ditado", "comecar a ditar"
Comando de parada: "sistema parar"

Como funciona:
1. Ativa: lock_focus(self) no ModuleManager
2. Avisa: clique na janela alvo em 5 segundos
3. Cada comando recebido: copia para clipboard + Ctrl+V
4. "sistema parar": release_focus() e encerra

Vantagem sobre TTS: funciona com acentuacao perfeita, nao depende de LLM
"""

import pyperclip
import pyautogui
import time
import threading
from typing import List, Dict
from modules.base_module import AeonModule


class TypewriterModule(AeonModule):
    """
    Modulo para digitar em aplicativos com suporte a acentuacao.
    Usa lock_focus para garantir que APENAS este modulo processa comandos.
    """
    
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Digitador"
        self.triggers = ["modo ditado", "comecar a ditar", "digitar"]
        self.is_active = False
        self.pending_break = False

    @property
    def dependencies(self) -> List[str]:
        """Digitador depende apenas do module_manager para lock_focus."""
        return []

    @property
    def metadata(self) -> Dict[str, str]:
        """Metadados do modulo."""
        return {
            "version": "1.0.0",
            "author": "Aeon Core",
            "description": "Digita com acentuacao correta usando clipboard + Ctrl+V"
        }

    def on_load(self) -> bool:
        """Inicializa o modulo."""
        self.is_active = False
        self.pending_break = False
        return True

    def on_unload(self) -> bool:
        """Limpa recursos ao descarregar."""
        if self.is_active:
            self._stop_typewriter()
        return True

    def process(self, command: str) -> str:
        """
        Processa comandos do Digitador.
        
        Se ja esta em modo ativo:
        - "sistema parar" -> sai do modo
        - Qualquer outro texto -> digita
        
        Se nao esta ativo:
        - "modo ditado" ou "comecar a ditar" -> ativa
        """
        
        command_lower = command.lower()
        
        # ===== Se ja esta em modo ativo =====
        if self.is_active:
            
            # Comando para parar
            if "sistema parar" in command_lower or "parar" in command_lower:
                return self._stop_typewriter()
            
            # Qualquer outro comando = digita
            return self._type_text(command)
        
        # ===== Se nao esta ativo, ativa primeiro =====
        if "modo ditado" in command_lower or "comecar a ditar" in command_lower or "digitar" in command_lower:
            return self._start_typewriter()
        
        return ""

    def _start_typewriter(self) -> str:
        """Ativa o modo ditado."""
        self.is_active = True
        
        # Adquirir foco no ModuleManager
        module_manager = self.core_context.get("module_manager")
        if module_manager:
            module_manager.lock_focus(self, timeout_seconds=600)  # 10 min timeout
        
        io_handler = self.core_context.get("io_handler")
        if io_handler:
            io_handler.falar("Modo ditado ativado. Clique na janela alvo em 5 segundos.")
        
        # Aguardar 5 segundos para o usuario clicar na janela
        time.sleep(5)
        
        if io_handler:
            io_handler.falar("Pronto! Comecando a digitar. Fale 'sistema parar' para sair.")
        
        return "OK Modo ditado ativado! Pronto para digitar."

    def _stop_typewriter(self) -> str:
        """Desativa o modo ditado."""
        self.is_active = False
        
        # Liberar foco no ModuleManager
        module_manager = self.core_context.get("module_manager")
        if module_manager:
            module_manager.release_focus()
        
        io_handler = self.core_context.get("io_handler")
        if io_handler:
            io_handler.falar("Modo ditado desativado. Voltando ao modo normal.")
        
        return "OK Modo ditado desativado."

    def _type_text(self, text: str) -> str:
        """
        Digita o texto em modo clipboard.
        
        Processo:
        1. Copia texto para clipboard
        2. Aguarda 50ms (buffer)
        3. Pressiona Ctrl+V para colar
        4. Adiciona espaco ao final (para separar palavras)
        """
        try:
            # Remover "digitar" do inicio se necessario
            text = text.replace("digitar", "", 1).strip()
            
            if not text:
                return ""
            
            # Copiar para clipboard (com espaco ao final)
            pyperclip.copy(text + " ")
            
            # Pequeno delay (buffer)
            time.sleep(0.05)
            
            # Colar
            pyautogui.hotkey("ctrl", "v")
            
            # Log visual (nao fala, apenas retorna vazio para nao confundir)
            print(f"[Digitador] Digitado: {text}")
            
            return ""  # Retorna vazio para nao ativar Brain
        
        except Exception as e:
            error_msg = f"Erro ao digitar: {e}"
            print(f"[Digitador] {error_msg}")
            return error_msg
