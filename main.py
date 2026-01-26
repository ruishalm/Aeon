import os
import sys
import threading
import warnings
import traceback

warnings.filterwarnings("ignore", category=UserWarning, module='pygame')

# Ajusta caminho para encontrar os módulos
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

if __name__ == "__main__":
    print(f"=== AEON V85 SYSTEM BOOT (ROOT: {ROOT_DIR}) ===")
    
    # 1. Verifica se o usuário quer o Dashboard ou a Esfera (Padrão: Esfera)
    # Se rodar 'python main.py --gui', abre o painel cyberpunk
    use_dashboard = "--gui" in sys.argv

    try:
        if use_dashboard:
            print("[BOOT] Iniciando Dashboard Cyberpunk (CustomTkinter)...")
            from main_gui_logic import AeonGUI 
            app = AeonGUI()
            app.mainloop()
        else:
            from PyQt6.QtWidgets import QApplication
            try:
                from core.gui_sphere import AeonSphere
            except ImportError:
                from gui_sphere import AeonSphere
            
            print("[BOOT] Iniciando Interface Neural (Esfera)...")
            qt_app = QApplication(sys.argv)
            sphere = AeonSphere()
            sphere.show()
            
            sys.exit(qt_app.exec())

    except Exception as e:
        print(f"\n[ALERTA] Falha ao iniciar interface principal: {e}")
        traceback.print_exc()
        if not use_dashboard:
            print("[BOOT] Ativando Protocolo de Segurança: Iniciando GUI Clássica (Fallback)...")
            try:
                from main_gui_logic import AeonGUI
                app = AeonGUI()
                app.mainloop()
            except Exception as e_fallback:
                print(f"[ERRO CRÍTICO] Falha total no sistema de interface: {e_fallback}")
                traceback.print_exc()