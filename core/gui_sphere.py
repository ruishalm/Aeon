import sys
import math
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QApplication, 
                             QLineEdit, QDialog, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRectF
from PyQt5.QtGui import (QPainter, QColor, QRadialGradient, QPen, 
                         QFont, QBrush, QLinearGradient)

class InputDialog(QDialog):
    """
    Caixa de Texto Flutuante (Estilo Cyberpunk).
    Ativada por Ctrl + Shift + A.
    """
    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.callback = callback
        
        # Remove bordas e deixa transparente
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(500, 80)
        
        layout = QVBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Digite um comando para o Aeon...")
        
        # Estilo CSS da caixa
        self.input_field.setStyleSheet("""
            QLineEdit { 
                background-color: rgba(10, 10, 20, 230); 
                color: #00FFFF; 
                border: 2px solid #00FFFF; 
                border-radius: 10px; 
                padding: 10px; 
                font-family: 'Segoe UI';
                font-size: 16px;
                selection-background-color: #00FFFF;
                selection-color: black;
            }
        """)
        
        # Efeito de brilho (Glow)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 255, 255))
        shadow.setOffset(0, 0)
        self.input_field.setGraphicsEffect(shadow)

        self.input_field.returnPressed.connect(self.send_text)
        layout.addWidget(self.input_field)
        self.setLayout(layout)
        
        # Foca no texto assim que abre
        self.input_field.setFocus()

    def send_text(self):
        text = self.input_field.text()
        if text and self.callback:
            self.callback(text)
        self.close()

class SphereUI(QWidget):
    # Sinal para atualizar a GUI de forma segura (Thread-Safe)
    update_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(str)

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
        self.status_text = "BOOT"
        
        # --- Layout de Texto ---
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        
        # 1. Status (Topo da Esfera)
        self.lbl_status = QLabel(self.status_text)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: rgba(255,255,255,180); font-weight: bold; font-family: Segoe UI; letter-spacing: 2px;")
        self.layout.addWidget(self.lbl_status)
        
        # Espaçador
        self.layout.addStretch()
        
        # 2. Legenda (Embaixo da Esfera)
        self.lbl_caption = QLabel("")
        self.lbl_caption.setAlignment(Qt.AlignCenter)
        self.lbl_caption.setStyleSheet("""
            color: #00FFFF; 
            font-size: 11pt; 
            background-color: rgba(0,0,0,150); 
            border-radius: 8px; 
            padding: 5px 10px;
        """)
        self.lbl_caption.setWordWrap(True)
        self.lbl_caption.setMaximumWidth(380)
        self.lbl_caption.hide() # Começa escondido
        self.layout.addWidget(self.lbl_caption)
        
        self.setLayout(self.layout)

        # --- Timer de Animação (60 FPS) ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)
        
        # Conecta sinais
        self.update_signal.connect(self._update_gui_thread)
        self.status_signal.connect(self._update_status_thread)

    def center_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def set_logic_callback(self, callback):
        self.logic_callback = callback

    # --- INPUT DO TECLADO (FARMING) ---
    def keyPressEvent(self, event):
        # Atalho: Ctrl + Shift + A
        if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.key() == Qt.Key_A:
            self.open_input_box()
        # Atalho: ESC para fechar
        elif event.key() == Qt.Key_Escape:
            self.close()

    def open_input_box(self):
        dialog = InputDialog(self, self.logic_callback)
        # Posiciona a caixa um pouco abaixo da esfera
        dialog.move(self.x() + 25, self.y() + 350)
        dialog.exec_()

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

    def add_message(self, text, sender="SISTEMA"):
        self.update_signal.emit(text, sender)

    def _update_gui_thread(self, text, sender):
        prefix = f"{sender}: " if sender != "SISTEMA" else ""
        self.lbl_caption.setText(f"{prefix}{text}")
        self.lbl_caption.show()
        self.lbl_caption.adjustSize()
        
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
        base_radius = 90
        
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

        # 4. Marcador Visual (Online/Offline) - Pequeno ponto no canto
        painter.setBrush(status_dot)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.width() - 40, 40, 8, 8)

    # Arrastar janela
    def mousePressEvent(self, event): self.oldPos = event.globalPos()
    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()