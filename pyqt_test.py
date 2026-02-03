print("Attempting to import PyQt5...")
try:
    from PyQt5.QtWidgets import QApplication
    print("PyQt5 imported successfully.")
    import sys
    app = QApplication(sys.argv)
    print("QApplication instantiated successfully.")
except Exception as e:
    print(f"Failed to import or use PyQt5: {e}")
