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
            response = self.module_manager.route_command(text)

            # 2. Se for Texto Simples
            if isinstance(response, str):
                self.gui.add_message(response, "AEON")
                if self.io: self.io.falar(response)

            # 3. Se for uma Ferramenta (JSON/Dict)
            elif isinstance(response, dict):
                tool = response.get("tool")
                param = response.get("param")
                self.gui.add_message(f"Executando: {tool}...", "SISTEMA")
                
                # Executa a ação real
                res_tool = self.module_manager.executar_ferramenta(tool, param)
                
                self.gui.add_message(str(res_tool), "AEON")
                if self.io: self.io.falar(str(res_tool))
            
            # 4. Se não for nada (None), manda pro Cérebro genérico (LLM)
            elif response is None:
                 self.gui.add_message("Hmm...", "AEON")
                 # Aqui você poderia chamar o brain.pensar() se quisesse papo furado

        except Exception as e:
            self.gui.add_message(f"Erro de processamento: {e}", "ERRO")
            print(f"ERRO LOGIC: {e}")
        
        self.gui.set_status("ONLINE")