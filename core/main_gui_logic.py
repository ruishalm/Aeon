import threading

class MainLogic:
    def __init__(self, gui):
        self.gui = gui
        self.module_manager = None
        self.io = None

    def register_modules(self, module_manager, io_handler):
        """Recebe os módulos depois que eles carregam"""
        self.module_manager = module_manager
        self.io = io_handler

    def process_user_input(self, text):
        """Chamado quando você fala ou digita"""
        if not text: return

        # Mostra o que você disse
        self.gui.add_message(text, "VOCÊ")
        self.gui.set_status("PROCESSANDO...")

        # Proteção se os módulos ainda não carregaram
        if not self.module_manager:
            self.gui.add_message("Estou acordando, aguarde...", "AEON")
            return

        # Processa em outra thread para não travar a animação
        threading.Thread(target=self._process_background, args=(text,), daemon=True).start()

    def _process_background(self, text):
        try:
            # 1. Tenta achar o comando nos módulos
            module_response = self.module_manager.route_command(text)

            # Se encontrou um módulo (resposta != None)
            if module_response is not None:
                if isinstance(module_response, str):
                    self.gui.add_message(module_response, "AEON")
                    if self.io: self.io.falar(module_response)
                elif isinstance(module_response, dict):
                    tool = module_response.get("tool")
                    param = module_response.get("param")
                    self.gui.add_message(f"Executando: {tool}...", "SISTEMA")
                    res_tool = self.module_manager.executar_ferramenta(tool, param)
                    self.gui.add_message(str(res_tool), "AEON")
                    if self.io: self.io.falar(str(res_tool))
            
            # Se retornou None, não tem trigger - tenta conversa natural com Brain
            else:
                brain = self.module_manager.core_context.get("brain")
                if brain:
                    # Pede ao Brain uma conversa natural (não comando)
                    response = brain.pensar(
                        prompt=text,
                        modo="conversa"  # Indica que é conversa, não comando
                    )
                    
                    if response:
                        self.gui.add_message(response, "AEON")
                        if self.io: self.io.falar(response)
                        
                        # Salva na história
                        if self.module_manager:
                            with self.module_manager.history_lock:
                                self.module_manager.chat_history.append({"role": "user", "content": text})
                                self.module_manager.chat_history.append({"role": "assistant", "content": response})
                    else:
                        self.gui.add_message("Hmm, não consegui processar...", "AEON")
                else:
                    self.gui.add_message("Cérebro indisponível.", "AEON")

        except Exception as e:
            self.gui.add_message(f"Erro de processamento: {e}", "ERRO")
            print(f"ERRO LOGIC: {e}")
        
        self.gui.set_status("ONLINE")