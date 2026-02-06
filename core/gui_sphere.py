import sys
import math
from pynput import keyboard
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QApplication, 
                             QLineEdit, QDialog, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRectF
from PyQt5.QtGui import (QPainter, QColor, QRadialGradient, QPen, 
                         QFont, QBrush, QLinearGradient)

from core.gui_app import AeonTerminal

class SphereUI(QWidget):
    # Sinal para atualizar a GUI de forma segura (Thread-Safe)
    update_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(str)
    hotkey_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AEON V85")
        
        # Configuração da Janela
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(450, 450)
        self.center_screen()

        # --- Variáveis de Estado ---
        self.logic_callback = None
        self.is_speaking = False
        self.is_listening = False
        self.pulse_phase = 0.0
        self.rotation_angle = 0.0
        self.terminal_window = None
        self.status_text = "BOOT"
        
        # --- Layout de Texto ---
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        
        # 1. Status (Topo da Esfera)
        self.lbl_status = QLabel(self.status_text)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: rgba(255,255,255,180); font-weight: bold; font-family: Segoe UI; letter-spacing: 2px;")
        self.layout.addWidget(self.lbl_status)
        
        # 2. Legenda (Balao de fala) - criada como widget filho e posicionada dinamicamente
        self.lbl_caption = QLabel("", self)
        self.lbl_caption.setAlignment(Qt.AlignCenter)
        self.lbl_caption.setStyleSheet("""
            color: #00FFFF; 
            font-size: 11pt; 
            background-color: rgba(0,0,0,180); 
            border-radius: 10px; 
            padding: 6px 12px;
        """)
        self.lbl_caption.setWordWrap(True)
        self.lbl_caption.setMaximumWidth(320)
        self.lbl_caption.hide() # Começa escondido
        # Mantemos o spacer abaixo para posicionamento visual
        self.layout.addStretch()
        
        self.setLayout(self.layout)

        # Mic visualizer level
        self.mic_level = 0.0

        # --- Timer de Animação (60 FPS) ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)
        
        # Conecta sinais
        self.update_signal.connect(self._update_gui_thread)
        self.status_signal.connect(self._update_status_thread)

        # Configura Hotkey Global (Restauração)
        self.hotkey_signal.connect(self.open_terminal)
        self._setup_global_hotkey()

    def center_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def set_logic_callback(self, callback):
        self.logic_callback = callback

    def _setup_global_hotkey(self):
        """Inicia o listener global de teclado em uma thread separada."""
        try:
            self.hotkey_listener = keyboard.GlobalHotKeys({'<ctrl>+<shift>+a': self.hotkey_signal.emit})
            self.hotkey_listener.start()
        except Exception as e:
            print(f"Erro ao iniciar hotkey global: {e}")

    # --- INPUT DO TECLADO (FARMING) ---
    def keyPressEvent(self, event):
        # Atalho: Ctrl + Shift + A
        if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.key() == Qt.Key_A:
            self.open_terminal()
        # Atalho: ESC para fechar
        elif event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        if hasattr(self, 'hotkey_listener') and self.hotkey_listener:
            self.hotkey_listener.stop()
        event.accept()

    # --- MODO TERMINAL ---
    def open_terminal(self):
        """Abre a interface completa (AeonTerminal) no mesmo processo."""
        print("[GUI] Abrindo terminal...")
        if self.terminal_window and self.terminal_window.isVisible():
            return

        # Context retrieval logic
        context = None
        if self.logic_callback and hasattr(self.logic_callback, '__self__'):
            logic = self.logic_callback.__self__
            if hasattr(logic, 'module_manager') and logic.module_manager:
                context = logic.module_manager.core_context
            
        try:
            if not self.terminal_window:
                self.terminal_window = AeonTerminal(context)
                self.terminal_window.closed_signal.connect(self.on_terminal_closed)
            
            self.hide()
            self.terminal_window.show()
            self.terminal_window.raise_()
            self.terminal_window.activateWindow()
            self.set_status("TERMINAL")
        except Exception as e:
            print(f"[GUI] ERRO AO ABRIR TERMINAL: {e}")
            import traceback
            traceback.print_exc()
            self.show() # Restaura a esfera se falhar

    def on_terminal_closed(self):
        """Chamado quando o terminal é fechado (botão voltar)."""
        # Restaura o contexto da GUI para a Esfera (para o IOHandler falar aqui)
        if self.terminal_window and hasattr(self.terminal_window, 'core_context'):
             if self.terminal_window.core_context:
                 self.terminal_window.core_context['gui'] = self
        
        self.show()
        self.activateWindow()
        self.set_status("ONLINE")

    # --- Métodos de Atualização ---
    def set_status(self, text):
        self.status_signal.emit(text)

    def _update_status_thread(self, text):
        self.status_text = text.upper()
        self.lbl_status.setText(self.status_text)
        
        # Lógica visual baseada no texto
        if "OUVINDO" in self.status_text or "ESCUTA" in self.status_text:
            self.is_listening = True
        else:
            self.is_listening = False

    def set_module_list(self, modules):
        """Recebe a lista de módulos (compatibilidade)."""
        pass 

    def add_message(self, text, sender="SISTEMA"):
        self.update_signal.emit(text, sender)

    def _update_gui_thread(self, text, sender):
        prefix = f"{sender}: " if sender != "SISTEMA" else ""
        self.lbl_caption.setText(f"{prefix}{text}")
        self.lbl_caption.adjustSize()
        # Posiciona o balao acima da esfera (como quadrinho)
        center_x = self.width() // 2
        center_y = self.height() // 2
        base_radius = 45
        lbl_w = self.lbl_caption.width()
        lbl_h = self.lbl_caption.height()
        # Move para ficar centrado e acima da esfera
        self.lbl_caption.move(center_x - lbl_w // 2, center_y - base_radius - lbl_h - 12)
        self.lbl_caption.show()
        
        if sender == "AEON":
            self.is_speaking = True
            # Para de "falar" visualmente após um tempo estimado (baseado no tamanho do texto)
            tempo_leitura = max(2000, len(text) * 80)
            QTimer.singleShot(tempo_leitura, lambda: setattr(self, 'is_speaking', False))

    def animate(self):
        self.pulse_phase += 0.05
        self.rotation_angle += 1.0
        if self.rotation_angle >= 360: self.rotation_angle = 0
        self.update() # Redesenha

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = QPoint(self.width() // 2, self.height() // 2)
        base_radius = 45  # reduzido em 50%
        
        # --- Definição de Cores por Estado ---
        if self.is_speaking:
            # Estado: FALANDO (Ciano Pulsante Rápido)
            pulse = math.sin(self.pulse_phase * 4) * 8
            main_color = QColor(0, 255, 255, 200)
            glow_color = QColor(0, 200, 255, 100)
            status_dot = Qt.cyan
        elif self.is_listening:
            # Estado: OUVINDO (Verde/Amarelo Pulsante Médio)
            pulse = math.sin(self.pulse_phase * 2) * 5
            main_color = QColor(0, 255, 100, 200)
            glow_color = QColor(50, 255, 50, 100)
            status_dot = Qt.green
        else:
            # Estado: IDLE (Vermelho Profundo Lento)
            pulse = math.sin(self.pulse_phase) * 3
            main_color = QColor(185, 28, 28, 180) # Vermelho Sangue
            glow_color = QColor(185, 28, 28, 70)  # Brilho Vermelho
            status_dot = Qt.red # Offline/Idle

        radius = base_radius + pulse

        # 1. Glow Externo (Aura)
        painter.setBrush(Qt.NoBrush)
        pen_glow = QPen(glow_color)
        pen_glow.setWidth(15)
        painter.setPen(pen_glow)
        painter.drawEllipse(center, int(radius + 5), int(radius + 5))

        # 2. Esfera Principal (Gradiente)
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0, main_color)
        gradient.setColorAt(0.7, main_color.darker(150))
        gradient.setColorAt(1, QColor(0, 0, 0, 0)) # Transparente na borda
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, int(radius), int(radius))
        
        # 3. Anéis Tecnológicos (Rotação)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle)
        
        arc_pen = QPen(QColor(255, 255, 255, 100))
        arc_pen.setWidth(2)
        painter.setPen(arc_pen)
        painter.setBrush(Qt.NoBrush)
        
        # Desenha arcos giratórios
        r_arc = radius + 10
        painter.drawArc(QRectF(-r_arc, -r_arc, r_arc*2, r_arc*2), 0, 60 * 16)
        painter.drawArc(QRectF(-r_arc, -r_arc, r_arc*2, r_arc*2), 180 * 16, 60 * 16)
        
        painter.restore()

        # 4. Mic visualizer: anel oscilante em torno da esfera
        try:
            amp = max(0.0, min(1.0, float(self.mic_level)))
        except Exception:
            amp = 0.0
        mic_ring_radius = int(radius + 18 + amp * 18)
        mic_pen = QPen(QColor(0, 200, 255, 120)) if self.is_listening else QPen(QColor(200, 200, 200, 60))
        mic_pen.setWidth(4)
        painter.setPen(mic_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, mic_ring_radius, mic_ring_radius)

        # 5. Marcador Visual (Online/Offline) - Pequeno ponto no canto
        painter.setBrush(status_dot)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.width() - 40, 40, 8, 8)

    def set_mic_level(self, level: float):
        """Atualiza o nivel do microfone (0.0-1.0) para a visualizacao."""
        try:
            self.mic_level = max(0.0, min(1.0, float(level)))
        except Exception:
            self.mic_level = 0.0

    # Arastar janela
    def mousePressEvent(self, event): self.oldPos = event.globalPos()
    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def toggle_visibility(self):
        """Alterna entre modo oculto e visível."""
        if self.isVisible():
            self.hide_sphere()
        else:
            self.show_sphere()

    def hide_sphere(self):
        """Esconde a esfera (modo oculto)."""
        self.hide()

    def show_sphere(self):
        """Mostra a esfera (modo visível)."""
        self.show()
        self.raise_()
        self.activateWindow()