import os
import sys
import threading
import warnings
import traceback
from dotenv import load_dotenv

# Arquivo de log para depuração de falhas silenciosas
LOG_FILE = "error.log" 
# Usar um nome de arquivo simples para portabilidade

try:
    # Carrega as variáveis de ambiente do arquivo .env
    load_dotenv()

    warnings.filterwarnings("ignore", category=UserWarning, module='pygame')

    # Ajusta caminho para encontrar os módulos
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(ROOT_DIR)
    
    # --- IMPORTAÇÕES CENTRALIZADAS DO CORE ---
    from core.config_manager import ConfigManager
    from core.context_manager import ContextManager
    from core.io_handler import IOHandler
    from core.brain import AeonBrain
    from core.module_manager import ModuleManager

    if __name__ == "__main__":
        print(f"=== AEON V86 SYSTEM BOOT (ROOT: {ROOT_DIR}) ===")
        
        # 1. --- INICIALIZAÇÃO CENTRAL DO CORE ---
        print("[BOOT] Inicializando subsistemas do Core...")
        config_manager = ConfigManager()
        context_manager = ContextManager()
        io_handler = IOHandler(config_manager.config, None)
        brain = AeonBrain(config_manager)
        
        core_context = {
            "config_manager": config_manager,
            "context_manager": context_manager,
            "io_handler": io_handler,
            "brain": brain,
            "gui": None,
            "workspace": os.path.join(ROOT_DIR, "workspace")
        }
        
        module_manager = ModuleManager(core_context)
        core_context["module_manager"] = module_manager
        
        # 2. --- SELEÇÃO E CRIAÇÃO DA GUI ---
        # A GUI é criada ANTES da thread de módulos para evitar race condition.
        use_dashboard = "--gui" in sys.argv
        gui_app = None
        qt_app = None

        try:
            if use_dashboard:
                print("[BOOT] Criando instância do Dashboard Cyberpunk...")
                from core.main_gui_logic import AeonGUI
                gui_app = AeonGUI(core_context) 
            else:
                try:
                    from PyQt6.QtWidgets import QApplication
                    from core.gui_sphere import AeonSphere
                    print("[BOOT] Criando instância da Interface Neural (Esfera)...")
                    qt_app = QApplication(sys.argv)
                    gui_app = AeonSphere(core_context)
                except ImportError:
                    print("\n[ALERTA] A interface da Esfera (PyQt6) não pôde ser carregada.")
                    raise
            
            if gui_app:
                core_context["gui"] = gui_app
                
                # 3. --- CARREGAMENTO DE MÓDULOS EM SEGUNDO PLANO ---
                # A thread só é iniciada DEPOIS que a GUI existe e registrou seus callbacks.
                print("[BOOT] Disparando carregamento de módulos em segundo plano...")
                module_loader_thread = threading.Thread(target=module_manager.load_modules, daemon=True)
                module_loader_thread.start()

                # 4. --- LANÇAMENTO DA GUI ---
                if use_dashboard:
                    gui_app.mainloop()
                else:
                    gui_app.show()
                    sys.exit(qt_app.exec())

        except Exception as e:
            # ... (código de fallback permanece o mesmo)
            if not isinstance(e, ImportError):
                print(f"\n[ALERTA] Falha ao iniciar interface principal: {e}")
                traceback.print_exc()

            if not use_dashboard:
                print("[BOOT] Ativando Protocolo de Segurança: Iniciando GUI Clássica (Fallback)...")
                try:
                    from core.main_gui_logic import AeonGUI
                    gui_app = AeonGUI(core_context)
                    core_context["gui"] = gui_app
                    # Inicia a thread de módulos também para o fallback
                    module_loader_thread = threading.Thread(target=module_manager.load_modules, daemon=True)
                    module_loader_thread.start()
                    gui_app.mainloop()
                except Exception as e_fallback:
                    print(f"[ERRO CRÍTICO] Falha total no sistema de interface: {e_fallback}")
                    traceback.print_exc()

except Exception as e_top:
    # Grava o erro fatal na "caixa-preta"
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"--- ERRO CRÍTICO NA INICIALIZAÇÃO ---\n")
        f.write(f"Exceção: {str(e_top)}\n\n")
        f.write("--- Traceback ---\n")
        traceback.print_exc(file=f)
    raise
