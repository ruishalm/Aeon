import threading

class MainLogic:
    def __init__(self, gui):
        self.gui = gui
        self.module_manager = None
        self.io = None
        
        # Memória de Curto Prazo (Para o aprendizado)
        self.last_user_text = ""
        self.last_ai_response = ""

    def register_modules(self, module_manager, io_handler):
        self.module_manager = module_manager
        self.io = io_handler
        
        # Injeta a memória no contexto para os módulos acessarem
        if self.module_manager:
            self.module_manager.core_context['short_term_memory'] = self

    def process_user_input(self, text):
        if not text: return

        self.gui.add_message(text, "VOCÊ")
        self.gui.set_status("PROCESSANDO...")

        if not self.module_manager:
            self.gui.add_message("Estou acordando...", "AEON")
            return

        threading.Thread(target=self._process_background, args=(text,), daemon=True).start()

    def _process_background(self, text):
        try:
            # Atualiza o status da conexão na GUI a cada interação
            if self.module_manager:
                brain = self.module_manager.core_context.get('brain')
                if brain:
                    self.gui.set_online_status(brain.online)

            # 1. Roteamento (Módulos ou Cérebro)
            response = self.module_manager.route_command(text)

            # --- LÓGICA DE RESPOSTA ---
            final_response_text = ""

            # Caso 1: Texto Simples
            if isinstance(response, str):
                final_response_text = response
                self.gui.add_message(response, "AEON")
                if self.io: self.io.falar(response)

            # Caso 2: Ferramenta (JSON)
            elif isinstance(response, dict):
                tool = response.get("tool")
                param = response.get("param")
                self.gui.add_message(f"Executando: {tool}...", "SISTEMA")
                
                res_tool = self.module_manager.executar_ferramenta(tool, param)
                final_response_text = str(res_tool)
                
                self.gui.add_message(final_response_text, "AEON")
                if self.io: self.io.falar(final_response_text)
            
            # Caso 3: Cérebro (Se nenhum módulo pegou e não é comando de aprendizado)
            elif response is None:
                 # Aqui o Brain entraria, mas para simplificar o exemplo, vamos assumir que o route_command
                 # já lidou com isso ou retornou None. Se retornou None, o Brain processa.
                 # (Assumindo que o Brain está conectado no module_manager ou aqui)
                 if self.module_manager.core_context.get('brain'):
                     final_response_text = self.module_manager.core_context['brain'].pensar(text)
                     self.gui.add_message(final_response_text, "AEON")
                     if self.io: self.io.falar(final_response_text)

            # --- ATUALIZAÇÃO DA MEMÓRIA (O Pulo do Gato) ---
            # Só salvamos se NÃO for um elogio (para não salvar o próprio elogio como exemplo)
            # O módulo de aprendizado vai decidir se salva a ANTERIOR baseado no texto atual.
            
            # Atualiza para a próxima vez
            self.last_user_text = text
            self.last_ai_response = final_response_text

        except Exception as e:
            self.gui.add_message(f"Erro: {e}", "ERRO")
            print(f"ERRO LOGIC: {e}")
        
        self.gui.set_status("ONLINE")