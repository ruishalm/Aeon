import os
import sys
import threading
import warnings
import traceback
from dotenv import load_dotenv

# Arquivo de log para depuração de falhas silenciosas
LOG_FILE = r"C:\Users\rafac\.gemini\tmp\2c91490bc0deb49ac6cf35a915d7223b79a98ab5e8a8e5c03da4394f9d4c940b\error.log"

try:
    # Carrega as variáveis de ambiente do arquivo .env
    load_dotenv()

    warnings.filterwarnings("ignore", category=UserWarning, module='pygame')

    # Ajusta caminho para encontrar os módulos
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(ROOT_DIR)

    if __name__ == "__main__":
        print(f"=== AEON V85 SYSTEM BOOT (ROOT: {ROOT_DIR}) ===")
        
        # 1. Verifica se o usuário quer o Dashboard ou a Esfera (Padrão: Esfera)
        use_dashboard = "--gui" in sys.argv

        try:
            if use_dashboard:
                print("[BOOT] Iniciando Dashboard Cyberpunk (CustomTkinter)...")
                from core.main_gui_logic import AeonGUI 
                app = AeonGUI()
                app.mainloop()
            else:
                try:
                    from PyQt6.QtWidgets import QApplication
                    from core.gui_sphere import AeonSphere
                    
                    print("[BOOT] Iniciando Interface Neural (Esfera)...")
                    qt_app = QApplication(sys.argv)
                    sphere = AeonSphere()
                    sphere.show()
                    
                    sys.exit(qt_app.exec())
                except ImportError:
                    print("\n[ALERTA] A interface da Esfera (PyQt6) não pôde ser carregada.")
                    print("         Verifique se a dependência está instalada: pip install PyQt6")
                    raise

        except Exception as e:
            if not isinstance(e, ImportError):
                print(f"\n[ALERTA] Falha ao iniciar interface principal: {e}")
                traceback.print_exc()

            if not use_dashboard:
                print("[BOOT] Ativando Protocolo de Segurança: Iniciando GUI Clássica (Fallback)...")
                try:
                    from core.main_gui_logic import AeonGUI
                    app = AeonGUI()
                    app.mainloop()
                except Exception as e_fallback:
                    print(f"[ERRO CRÍTICO] Falha total no sistema de interface: {e_fallback}")
                    traceback.print_exc()

except Exception as e_top:
    # Este é o bloco que grava a "caixa-preta"
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"--- ERRO CRÍTICO NA INICIALIZAÇÃO ---\n")
        f.write(f"Exceção: {str(e_top)}\n\n")
        f.write("--- Traceback ---\\n")
        traceback.print_exc(file=f)
    # Re-levanta a exceção para que o comportamento de falha não mude
    raise
