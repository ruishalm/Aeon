import sys
import threading
import time

# Defer all imports to see which one hangs

def log(msg):
    """Função de log com timestamp para depuração."""
    print(f"[{time.time():.2f}] [MAIN] {msg}")

if __name__ == "__main__":
    log("Iniciando importações uma a uma...")

    log("Importando QApplication...")
    from PyQt5.QtWidgets import QApplication
    log("Importou QApplication.")

    log("Importando SphereUI...")
    from core.gui_sphere import SphereUI
    log("Importou SphereUI.")

    log("Importando ConfigManager...")
    from core.config_manager import ConfigManager
    log("Importou ConfigManager.")
    
    log("Importando IOHandler...")
    from core.io_handler import IOHandler
    log("Importou IOHandler.")

    log("Importando AeonBrain...")
    from core.brain import AeonBrain
    log("Importou AeonBrain.")

    log("Importando ModuleManager...")
    from core.module_manager import ModuleManager
    log("Importou ModuleManager.")

    log("Importando ContextManager...")
    from core.context_manager import ContextManager
    log("Importou ContextManager.")

    log("Importando MainLogic...")
    from core.main_gui_logic import MainLogic
    log("Importou MainLogic.")

    log("Todas as importações foram concluídas.")

    # --- O CÓDIGO ORIGINAL COMEÇA AQUI ---

    def boot_sequence(esfera_ui, logic_controller, context_manager):
        """Carrega o sistema pesado em Background"""
        log("Thread de boot iniciada.")
        try:
            log("Carregando snapshot de contexto...")
            context_manager.load_snapshot()
            log("Snapshot carregado.")

            log("Carregando ConfigManager...")
            config = ConfigManager()
            log("ConfigManager Carregado.")
            esfera_ui.add_message("Sistema de Áudio...", "BOOT")
            
            log("Carregando IOHandler...")
            io = IOHandler(config.system_data, context_manager)
            io.cleanup_temp_files() # LIMPEZA NO BOOT
            log("IOHandler Carregado.")
            
            log("Carregando AeonBrain...")
            brain = AeonBrain(config)
            log("AeonBrain Carregado.")
            esfera_ui.add_message("Conectando Neural...", "BOOT")
            
            log("Carregando ModuleManager...")
            context = {
                "config_manager": config,
                "io_handler": io,
                "brain": brain,
                "gui": esfera_ui,
                "context": context_manager 
            }
            mods = ModuleManager(context)
            mods.load_modules()
            log("ModuleManager Carregado e módulos escaneados.")
            
            # ATUALIZA A GUI COM A LISTA DE MÓDULOS
            try:
                module_names = [m.name for m in mods.get_loaded_modules()]
                esfera_ui.set_module_list(module_names)
            except Exception as e:
                log(f"Falha ao atualizar lista de módulos na GUI: {e}")

            log("Registrando módulos na lógica principal...")
            logic_controller.register_modules(mods, io)
            log("Módulos registrados.")
            
            esfera_ui.set_status("ONLINE")
            esfera_ui.add_message("Sistema Online.", "AEON")
            
            log("Boot sequence concluída. Chamando io.falar().")
            io.falar("Estou pronto.")
            log("Chamada para io.falar() retornou.")

        except Exception as e:
            log(f"!!!!!! ERRO FATAL NA THREAD DE BOOT: {e} !!!!!!")
            import traceback
            traceback.print_exc()

    log("=== AEON V85 BOOT ===")
    
    log("Criando QApplication...")
    app = QApplication(sys.argv)
    log("QApplication criada.")

    log("Criando ContextManager...")
    context_manager = ContextManager()
    log("ContextManager criado.")
    
    log("Criando SphereUI e MainLogic...")
    esfera = SphereUI()
    logic = MainLogic(esfera)
    log("SphereUI e MainLogic criados.")
    
    log("Conectando GUI à Lógica...")
    esfera.set_logic_callback(logic.process_user_input)
    log("GUI conectada.")
    
    # A esfera é mostrada após o boot para evitar que a UI congele vazia.
    # log("Mostrando a esfera (esfera.show()).")
    # esfera.show()
    # log("Chamada para esfera.show() retornou.")
    
    log("Iniciando boot sequence na thread principal...")
    # Executa o boot na thread principal para garantir estabilidade com o PyQt
    boot_sequence(esfera, logic, context_manager)
    log("Boot sequence finalizada.")

    # Mostra a esfera agora que tudo está carregado
    esfera.show()
    
    # Cria uma função de limpeza para ser chamada no final
    def cleanup_routine():
        log("Iniciando rotina de limpeza ao sair...")
        if hasattr(logic, 'io') and logic.io:
            logic.io.cleanup_temp_files()
        context_manager.save_snapshot()

    log("Conectando o sinal aboutToQuit para a rotina de limpeza.")
    app.aboutToQuit.connect(cleanup_routine)
    log("Sinal conectado.")

    log("Iniciando loop de eventos da GUI (app.exec_())...")
    sys.exit(app.exec_())