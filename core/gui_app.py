import sys
import os
import math
import threading
import psutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QTextEdit, QLineEdit, QPushButton, QLabel, QFrame, 
                             QProgressBar, QListWidget, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, pyqtSignal, QObject, QEvent, QRect
from PyQt5.QtGui import QColor, QPainter, QRadialGradient, QPen, QBrush, QTextCursor, QFont

# Garante que a raiz do projeto esteja no path ANTES de importar o Core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.module_manager import ModuleManager
from core.io_handler import IOHandler
from core.config_manager import ConfigManager
from core.context_manager import ContextManager
try:
    from core.brain import AeonBrain as Brain
except ImportError:
    from core.brain import Brain

class BigSphere(QWidget):
    """Esfera Visual Gigante para o Modo Terminal"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.pulse_phase = 0.0
        self.rotation_angle = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16) # 60 FPS
        self.state = "IDLE"
        
    def animate(self):
        self.pulse_phase += 0.05
        self.rotation_angle += 1.0
        if self.rotation_angle >= 360: self.rotation_angle = 0
        self.update()

    def set_state(self, state):
        self.state = state
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        center = QPoint(w // 2, h // 2)
        
        # Tamanho dobrado (aprox 100 radius base * 2 = 200px visual)
        base_radius = 90
        
        # Cores baseadas no estado (Padrão Aeon)
        if self.state == "SPEAKING":
            pulse = math.sin(self.pulse_phase * 4) * 8
            main_color = QColor(0, 255, 255, 200) # Ciano
            glow_color = QColor(0, 200, 255, 100)
        elif self.state == "LISTENING":
            pulse = math.sin(self.pulse_phase * 2) * 5
            main_color = QColor(0, 255, 100, 200) # Verde
            glow_color = QColor(50, 255, 50, 100)
        else: # IDLE (Padrão)
            pulse = math.sin(self.pulse_phase) * 3
            main_color = QColor(185, 28, 28, 180) # Vermelho Sangue
            glow_color = QColor(185, 28, 28, 70)

        radius = base_radius + pulse
        
        # 1. Glow Externo
        painter.setBrush(Qt.NoBrush)
        pen_glow = QPen(glow_color)
        pen_glow.setWidth(20)
        painter.setPen(pen_glow)
        painter.drawEllipse(center, int(radius + 10), int(radius + 10))

        # 2. Esfera Principal
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0, main_color)
        gradient.setColorAt(0.7, main_color.darker(150))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, int(radius), int(radius))
        
        # 3. Anéis Tecnológicos (Rotação)
        painter.save()
        painter.translate(center)
        painter.rotate(self.rotation_angle)
        
        arc_pen = QPen(QColor(255, 255, 255, 100))
        arc_pen.setWidth(3)
        painter.setPen(arc_pen)
        painter.setBrush(Qt.NoBrush)
        
        r_arc = radius + 20
        painter.drawArc(QRectF(-r_arc, -r_arc, r_arc*2, r_arc*2), 0, 60 * 16)
        painter.drawArc(QRectF(-r_arc, -r_arc, r_arc*2, r_arc*2), 180 * 16, 60 * 16)
        
        painter.restore()

class CyberToggle(QWidget):
    """Chave seletora vertical (Estilo Aviação/Cyberpunk)."""
    state_changed = pyqtSignal(bool)

    def __init__(self, label, initial=True, parent=None):
        super().__init__(parent)
        self.label = label
        self.state = initial
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(40)

    def mousePressEvent(self, event):
        if self.isEnabled():
            self.state = not self.state
            self.state_changed.emit(self.state)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Cores
        active_color = QColor(0, 255, 0) if self.isEnabled() else QColor(50, 50, 50)
        off_color = QColor(255, 0, 0) if self.isEnabled() else QColor(30, 30, 30)
        text_color = active_color if self.state else off_color
        
        # Desenha Label (Esquerda)
        painter.setPen(text_color)
        painter.setFont(self.font())
        w_text = max(0, self.width() - 35) # Proteção contra largura negativa
        painter.drawText(QRect(0, 0, w_text, self.height()), Qt.AlignRight | Qt.AlignVCenter, self.label)
        
        # Desenha Switch (Direita)
        sw_x = self.width() - 30
        sw_h = 40
        sw_y = (self.height() - sw_h) // 2
        
        # Slot (Fundo)
        painter.setBrush(QColor(0, 0, 0))
        painter.setPen(QPen(active_color if self.state else QColor(100, 100, 100), 1))
        painter.drawRoundedRect(sw_x, sw_y, 20, sw_h, 3, 3)
        
        # Alavanca (Handle)
        handle_color = active_color if self.state else off_color
        painter.setBrush(handle_color)
        
        # Posição: Cima (Ligado) ou Baixo (Desligado)
        handle_y = sw_y + 2 if self.state else sw_y + sw_h - 18
        painter.drawRoundedRect(sw_x + 3, handle_y, 14, 16, 2, 2)

class CyberButton(QWidget):
    """Botão customizado desenhado via código (sem estilo padrão de OS)."""
    clicked = pyqtSignal()

    def __init__(self, icon_type="X", color=QColor(0, 255, 0), parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.base_color = color
        self.hover = False
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(60, 60)

    def enterEvent(self, event):
        self.hover = True
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        center = rect.center()
        # Raio baseado no menor lado para garantir que caiba
        radius = min(rect.width(), rect.height()) // 2 - 8
        
        # Cor dinâmica (brilha no hover)
        color = self.base_color.lighter(130) if self.hover else self.base_color
        bg_color = QColor(0, 20, 0, 100) if self.hover else QColor(0, 0, 0, 200)

        # 1. Fundo e Borda
        painter.setBrush(bg_color)
        painter.setPen(QPen(color, 2))
        painter.drawEllipse(center, radius, radius)
        
        # 2. Ícone
        painter.setPen(QPen(color, 3))
        
        if self.icon_type == "X":
            r = radius // 2
            painter.drawLine(center.x() - r, center.y() - r, center.x() + r, center.y() + r)
            painter.drawLine(center.x() + r, center.y() - r, center.x() - r, center.y() + r)
        elif self.icon_type == "MIC":
            painter.drawRoundedRect(center.x()-6, center.y()-10, 12, 20, 5, 5)
            painter.drawLine(center.x()-10, center.y()+5, center.x()+10, center.y()+5)
        elif self.icon_type == "CFG":
            painter.drawEllipse(center, radius//3, radius//3) # Engrenagem simples
        elif self.icon_type == "SPHERE":
            # Mini esfera
            painter.setBrush(self.base_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius//2, radius//2)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(self.base_color, 1))
            painter.drawEllipse(center, radius-2, radius-2)
        elif self.icon_type == "SKULL":
            # Caveira simplificada
            painter.setPen(QPen(self.base_color, 2))
            # Cranio
            painter.drawEllipse(center.x()-8, center.y()-10, 16, 14)
            # Mandibula
            painter.drawRect(center.x()-5, center.y()+4, 10, 6)
            # Olhos
            painter.drawPoint(center.x()-3, center.y()-4)
            painter.drawPoint(center.x()+3, center.y()-4)

class AeonTerminal(QMainWindow):
    closed_signal = pyqtSignal()

    def __init__(self, context=None):
        super().__init__()
        self.setWindowTitle("AEON V86 // TERMINAL MODE")
        self.resize(1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Estilo Global (CSS PyQt)
        # Fundo preto, letras verdes, bordas verdes
        self.setStyleSheet("""
            QWidget { color: #00FF00; font-family: 'Consolas'; font-size: 14px; }
            QFrame { background-color: #000000; border: 1px solid #00FF00; }
            QTextEdit { background-color: #000000; border: 1px solid #00FF00; color: #00FF00; }
            QLineEdit { background-color: #000000; border: 1px solid #00FF00; color: #00FF00; padding: 5px; }
            QListWidget { background-color: #000000; border: 1px solid #00FF00; color: #00FF00; }
            QLabel { border: none; background: transparent; color: #00FF00; }
            QProgressBar { border: 1px solid #00FF00; background: #000000; height: 10px; }
            QProgressBar::chunk { background: #00FF00; }
        """)

        if context:
            # Usa o contexto já carregado da Esfera (Rápido e sem crash)
            self.core_context = context
            self.config_manager = context.get('config_manager')
            self.io_handler = context.get('io_handler')
            self.brain = context.get('brain')
            self.context_manager = context.get('context')
            self.module_manager = context.get('module_manager')
            # Atualiza a referência da GUI no contexto para este terminal
            self.core_context['gui'] = self
        else:
            # Modo Standalone (Carrega tudo do zero)
            self.config_manager = ConfigManager()
            self.io_handler = IOHandler(self.config_manager.system_data, None)
            self.brain = Brain(self.config_manager)
            self.context_manager = ContextManager()
            self.module_manager = None
            self.core_context = {
                "config_manager": self.config_manager,
                "io_handler": self.io_handler,
                "brain": self.brain,
                "context": self.context_manager,
                "gui": self
            }

        # --- Layout ---
        central = QWidget()
        # Fundo geral quase sólido (~95% opaco)
        central.setStyleSheet("background-color: rgba(0, 0, 0, 240); border: 1px solid #00FF00;")
        self.setCentralWidget(central)
        
        # GRID LAYOUT (3 Colunas x 2 Linhas)
        grid = QGridLayout(central)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setSpacing(15)

        # --- LINHA 0 (Superior - 2/3 da tela) ---
        
        # 0,0: Log do Sistema (Retangular Alto)
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setPlaceholderText("AGUARDANDO LOGS DO SISTEMA...")
        grid.addWidget(self.log_display, 0, 0)

        # 0,1: Esfera (Centralizada)
        self.sphere_container = QFrame()
        self.sphere_container.setStyleSheet("border: none; background: transparent;")
        sphere_layout = QVBoxLayout(self.sphere_container)
        self.sphere = BigSphere()
        sphere_layout.addWidget(self.sphere)
        grid.addWidget(self.sphere_container, 0, 1)

        # 0,2: Placeholder (Vazio)
        self.placeholder = QFrame()
        lbl_place = QLabel("PLACEHOLDER", self.placeholder)
        lbl_place.setAlignment(Qt.AlignCenter)
        ph_layout = QVBoxLayout(self.placeholder)
        ph_layout.addWidget(lbl_place)
        grid.addWidget(self.placeholder, 0, 2)

        # --- LINHA 1 (Inferior - 1/3 da tela) ---

        # 1,0: Módulos (Quadrado)
        self.module_list = QListWidget()
        grid.addWidget(self.module_list, 1, 0)

        # 1,1: Chat/Input (Abaixo da Esfera)
        self.chat_container = QFrame()
        chat_layout = QVBoxLayout(self.chat_container)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("border: none; background: transparent;")
        chat_layout.addWidget(self.chat_display)
        
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Digite aqui...")
        self.input_box.returnPressed.connect(self.on_submit)
        chat_layout.addWidget(self.input_box)
        
        grid.addWidget(self.chat_container, 1, 1)

        # 1,2: Painel de Controle (Botões Customizados)
        self.back_panel = QFrame()
        ctrl_layout = QGridLayout(self.back_panel)
        ctrl_layout.setContentsMargins(10, 10, 10, 10)
        ctrl_layout.setSpacing(5)
        
        # --- Toggles Verticais ---
        self.tog_mic = CyberToggle("MIC", True)
        self.tog_mic.state_changed.connect(self.on_mic_toggle)
        
        self.tog_speech = CyberToggle("VOZ", True)
        self.tog_speech.state_changed.connect(self.on_speech_toggle)
        
        self.tog_dummy = CyberToggle("---", False)
        self.tog_dummy.setEnabled(False) # Desativado
        
        self.tog_online = CyberToggle("ONLINE", True)
        self.tog_online.state_changed.connect(self.on_online_toggle)
        
        # Posicionamento no Grid
        # Linha 0: Toggles menores
        ctrl_layout.addWidget(self.tog_mic, 0, 0)
        ctrl_layout.addWidget(self.tog_speech, 0, 1)
        ctrl_layout.addWidget(self.tog_dummy, 0, 2)
        
        # Coluna 3 (Direita): Toggle Offline ocupando 2 linhas (Vertical)
        ctrl_layout.addWidget(self.tog_online, 0, 3, 2, 1)
        
        # --- Botões Inferiores (Esfera e Caveira) ---
        self.btn_sphere = CyberButton("SPHERE", QColor(0, 255, 255))
        self.btn_sphere.clicked.connect(self.return_to_sphere)

        self.btn_kill = CyberButton("SKULL", QColor(255, 0, 0))
        self.btn_kill.clicked.connect(self.force_quit)
        
        # Linha 1: Botões
        ctrl_layout.addWidget(self.btn_sphere, 1, 0)
        ctrl_layout.addWidget(self.btn_kill, 1, 1)
        # (1, 2) fica vazio para espaçamento
        
        grid.addWidget(self.back_panel, 1, 2)

        # Configuração de proporção da Grade
        grid.setRowStretch(0, 2) # Linha de cima (2/3)
        grid.setRowStretch(1, 1) # Linha de baixo (1/3)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        # Timers
        self.timer_vitals = QTimer(self)
        self.timer_vitals.timeout.connect(self.update_vitals)
        self.timer_vitals.start(1000)
        
        # Init Modules Delayed
        if not self.module_manager:
            QTimer.singleShot(100, self.init_modules)
        else:
            self.refresh_module_list()

    def append_log(self, text):
        self.log_display.moveCursor(QTextCursor.End)
        # Adiciona timestamp simples
        self.log_display.insertPlainText(text)
        self.log_display.moveCursor(QTextCursor.End)

    def init_modules(self):
        self.add_message("Carregando módulos...", "SISTEMA")
        try:
            self.module_manager = ModuleManager(self.core_context)
            self.core_context["module_manager"] = self.module_manager
            self.module_manager.load_modules()
            self.refresh_module_list()
            self.add_message("Módulos carregados.", "SISTEMA")
        except Exception as e:
            self.add_message(f"Erro: {e}", "ERRO")

    def refresh_module_list(self):
        self.module_list.clear()
        if self.module_manager:
            for mod in self.module_manager.get_loaded_modules():
                self.module_list.addItem(f"• {mod.name}")

    def update_vitals(self):
        cpu = psutil.cpu_percent()
        # self.cpu_bar.setValue(int(cpu)) # Removido temporariamente

    def add_message(self, text, sender="VOCÊ"):
        # Log no painel superior esquerdo (Manual, seguro)
        self.append_log(f"[{sender}] {text}\n")
        
        # Adiciona no Chat Visual (Tela do meio)
        color = "#00FF00"
        if sender == "VOCÊ": color = "#FFFFFF"
        if sender == "AEON": color = "#00FFFF"
        if sender == "ERRO": color = "#FF0000"
        
        self.chat_display.append(f"<span style='color:{color}'><b>{sender}:</b> {text}</span>")
        # Auto scroll
        sb = self.chat_display.verticalScrollBar()
        sb.setValue(sb.maximum())
        
        if sender == "AEON":
            self.sphere.set_state("SPEAKING")
            # Volta para IDLE após um tempo estimado
            QTimer.singleShot(max(2000, len(text) * 50), lambda: self.sphere.set_state("IDLE"))

    def on_submit(self):
        txt = self.input_box.text().strip()
        if not txt: return
        
        self.add_message(txt, "VOCÊ")
        self.input_box.clear()
        
        threading.Thread(target=self.process_command, args=(txt,), daemon=True).start()

    def process_command(self, txt):
        if not self.module_manager: return
        try:
            response = self.module_manager.route_command(txt)
            # Usa QTimer para atualizar GUI da thread principal
            QTimer.singleShot(0, lambda: self.add_message(response, "AEON"))
            QTimer.singleShot(0, lambda: self.io_handler.falar(response))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.add_message(str(e), "ERRO"))

    def set_status(self, status):
        pass # Compatibilidade

    def set_online_status(self, online):
        pass # Compatibilidade

    def on_mic_toggle(self, state):
        # state = True (ON) -> Mic Ativado
        if self.context_manager:
            self.context_manager.set('mic_enabled', state)
        self.add_message(f"Microfone {'ATIVADO' if state else 'MUTADO'}.", "SISTEMA")

    def on_speech_toggle(self, state):
        # state = True (ON) -> Voz Ativada
        if self.io_handler:
            self.io_handler.muted = not state
            if not state: self.io_handler.calar_boca()
        self.add_message(f"Voz {'ATIVADA' if state else 'DESATIVADA'}.", "SISTEMA")

    def on_online_toggle(self, state):
        # state = True (ON) -> ONLINE (Verde/Cima)
        # state = False (OFF) -> OFFLINE (Vermelho/Baixo)
        if self.brain:
            if state:
                self.brain.online = True
                self.brain._conectar()
                status = "ONLINE" if self.brain.online else "OFFLINE (Falha)"
                self.add_message(f"Modo {status} ativado.", "SISTEMA")
            else:
                self.brain.online = False
                self.add_message("Modo OFFLINE forçado.", "SISTEMA")

    def force_quit(self):
        QApplication.quit()

    def return_to_sphere(self):
        self.hide()
        self.closed_signal.emit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.closed_signal.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AeonTerminal()
    window.show()
    sys.exit(app.exec_())