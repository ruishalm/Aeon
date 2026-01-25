import sys
import os
import threading

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
            from main_gui_logic import AeonGUI # Renomearemos o main interno para isso
            app = AeonGUI()
            app.mainloop()
        else:
            from PyQt6.QtWidgets import QApplication
            from core.gui_sphere import AeonSphere
            
            print("[BOOT] Iniciando Interface Neural (Esfera)...")
            qt_app = QApplication(sys.argv)
            sphere = AeonSphere()
            sphere.show()
            
            sys.exit(qt_app.exec())

    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Falha no Boot: {e}")
        print("[DICA] Verifique se as dependências estão instaladas.")