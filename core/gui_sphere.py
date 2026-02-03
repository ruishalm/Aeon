import os
import math
import random
import ctypes
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLineEdit, QFrame, QLabel, QMenu
from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF, pyqtSignal, QRectF, QObject
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QPainterPath
from pynput import keyboard as pynput_keyboard

# As importações do Core agora são injetadas, não criadas aqui.

# --- CONFIGURAÇÕES DE CORES ---
C_ACTIVE = QColor(255, 0, 0)
C_PROCESS = QColor(0, 191, 255)
C_LOADING = QColor(255, 165, 0)
C_BG_INPUT = "#000000"
C_BORDER = "#8B0000"
C_TEXT = "#FFFFFF"
C_PASTEL = QColor(200, 150, 150, 40)
C_AURA_ONLINE = QColor(0, 255, 0, 255)
C_AURA_OFFLINE = QColor(255, 0, 0, 255)

class SpeechBubble(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"color: {C_TEXT}; font-family: 'Consolas'; font-size: 11px; background-color: transparent; border: 0px; padding: 10px;")
        self._text = ""
    def setText(self, text): self._text = text; super().setText(text); self.update()
    def paintEvent(self, event):
        if not self._text: return
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(5, 5, -5, -5); rect.setHeight(rect.height() - 10)
        path = QPainterPath(); path.addRoundedRect(float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height()), 8.0, 8.0)
        center_x = rect.center().x(); tail = QPainterPath(); tail.moveTo(center_x - 10, rect.bottom()); tail.lineTo(center_x, rect.bottom() + 10); tail.lineTo(center_x + 10, rect.bottom()); tail.lineTo(center_x - 10, rect.bottom()); path.addPath(tail)
        painter.setBrush(QColor(0, 0, 0, 190)); painter.setPen(QPen(QColor(C_BORDER), 1.5)); painter.drawPath(path)
        super().paintEvent(event)

class AeonSphere(QMainWindow):
    activate_signal = pyqtSignal()
    timer_signal = pyqtSignal(int, object, tuple)
    modules_loaded_signal = pyqtSignal()

    def __init__(self, core_context: dict):
        super().__init__()
        print("[SPHERE] Iniciando Interface Neural...")

        # --- INJEÇÃO DE DEPENDÊNCIA ---
        self.core_context = core_context
        self.config_manager = core_context.get("config_manager")
        self.io_handler = core_context.get("io_handler")
        self.brain = core_context.get("brain")
        self.context_manager = core_context.get("context_manager")
        self.module_manager = core_context.get("module_manager")
        
        # Registra um callback no ModuleManager
        if self.module_manager:
            self.module_manager.on_all_modules_loaded = self.modules_loaded_signal.emit

        self.hotkey_listener = None

        # --- CONFIGURAÇÃO DA JANELA ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geo.width() - 280, 50, 250, 250)
        
        self.state = "LOADING"
        self.base_radius = 50; self.current_radius = 50; self.target_radius = 50; self.pulse_phase = 0; self.orbit_angles = [random.uniform(0, 2 * math.pi) for _ in range(3)]; self.orbit_speeds = [random.uniform(0.002, 0.004) for _ in range(3)]; self.orbit_factors = [random.uniform(1.05, 1.15) for _ in range(3)]; self.is_interactive = False; self.drag_pos = None; self.hidden_mode = False; self.ring_angle = 0
        self.visual_mode = "ACTIVE"; self.sleep_timer = QTimer(); self.sleep_timer.timeout.connect(self.go_to_sleep)
        
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.response_label = SpeechBubble(self.central_widget); self.response_label.setGeometry(10, -10, 230, 80); self.response_label.hide()
        self.input_frame = QFrame(self.central_widget); self.input_frame.setGeometry(25, 160, 200, 45); self.input_frame.setStyleSheet(f"QFrame {{ background-color: {C_BG_INPUT}; border: 2px solid {C_BORDER}; border-radius: 10px; }}")
        
        self.input_box = QLineEdit(self.input_frame); self.input_box.setGeometry(10, 10, 180, 30); self.input_box.setPlaceholderText("Carregando..."); self.input_box.setStyleSheet(f"background: transparent; border: none; color: {C_TEXT}; font-family: Consolas;"); self.input_box.returnPressed.connect(self.on_submit); self.input_box.setEnabled(False)
        
        # --- TIMERS E HOTKEYS ---
        self.anim_timer = QTimer(); self.anim_timer.timeout.connect(self.animate); self.anim_timer.start(30)
        self.activate_signal.connect(lambda: self.set_click_through(False))
        self.timer_signal.connect(self._handle_timer_signal)
        threading.Thread(target=self._setup_global_hotkey, daemon=True).start()
        
        # Conecta o sinal de módulos carregados ao slot
        self.modules_loaded_signal.connect(self.on_modules_loaded)
        
        # Feedback inicial
        self.io_handler.falar("Iniciando Aeon.")
        print("[SPHERE] Sequência de inicialização da GUI concluída. Aguardando módulos...")

    def on_modules_loaded(self):
        """Slot executado quando todos os módulos terminam de carregar."""
        print("[SPHERE] Módulos carregados. Sistema pronto.")
        self.state = "IDLE"
        self.input_box.setEnabled(True)
        self.input_box.setPlaceholderText("Comando...")

        try:
            self.io_handler.falar("Sistema online.")
        except Exception as e:
            print(f"[SPHERE] Aviso: Falha ao falar 'Sistema online': {e}")

        self.show_response("Sistema pronto.")
        self.after(2000, self.response_label.hide)
        
        # Ativa os módulos de background
        print("[SPHERE] Ativando módulos de inicialização (Audição)...")
        self.after(500, lambda: threading.Thread(target=self.process_command, args=("ativar escuta", True), daemon=True).start())
        
        self.after(1000, lambda: self.sleep_timer.start(120000))

    def set_click_through(self, enable: bool):
        try:
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20; WS_EX_LAYERED = 0x80000; WS_EX_TRANSPARENT = 0x20
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if enable: style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT; self.input_frame.hide(); self.is_interactive = False
            else: style = style & ~WS_EX_TRANSPARENT; self.input_frame.show(); self.input_box.setFocus(); self.is_interactive = True; self.hidden_mode = False; self.wake_up()
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception as e: print(f"[ERRO ctypes] {e}")

    def _setup_global_hotkey(self):
        try:
            self.hotkey_listener = pynput_keyboard.GlobalHotKeys({'<ctrl>+<shift>+a': self.activate_signal.emit})
            self.hotkey_listener.start()
        except Exception as e: print(f"[ERRO pynput] {e}")

    def paintEvent(self, event):
        if self.hidden_mode and not self.is_interactive: return
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.state == "LOADING": color = C_LOADING
        else: color = C_PASTEL if self.visual_mode == "STANDBY" else (C_PROCESS if self.state == "PROCESSING" else C_ACTIVE)
        center = QPointF(self.width() / 2, 110.0)
        is_online = self.brain.online if hasattr(self, 'brain') and self.brain else False
        base_aura_color = C_AURA_ONLINE if is_online else C_AURA_OFFLINE
        painter.setPen(Qt.PenStyle.NoPen)
        if self.visual_mode == "ACTIVE":
            if self.state != "LOADING":
                for i in range(3):
                    angle = self.orbit_angles[i]; orbit_radius = self.current_radius * self.orbit_factors[i]; bx = center.x() + orbit_radius * math.cos(angle); by = center.y() + orbit_radius * math.sin(angle); ball_center = QPointF(bx, by); ball_grad = QRadialGradient(ball_center, 5); ball_grad.setColorAt(0, QColor(base_aura_color.red(), base_aura_color.green(), base_aura_color.blue(), 100)); ball_grad.setColorAt(1, Qt.GlobalColor.transparent); painter.setBrush(QBrush(ball_grad)); painter.drawEllipse(ball_center, 5, 5)
            self._draw_rings(painter, center, color)
        self._draw_undulating_sphere(painter, center, color, self.current_radius, 1.0)
        self._draw_undulating_sphere(painter, center, color, self.current_radius * 0.8, 0.6)

    def _draw_undulating_sphere(self, painter, center, color, radius, opacity_mult):
        path = QPainterPath(); num_points = 80
        is_active = self.io_handler.is_busy() or self.state == "PROCESSING" or self.state == "LOADING"
        amp_factor = 3.5 if is_active else (1.0 if self.visual_mode == "ACTIVE" else 0.0)
        for i in range(num_points + 1):
            angle = (i * 2 * math.pi) / num_points; wave1 = math.sin(angle * 2 + self.pulse_phase * 1.2) * (radius * 0.03 * amp_factor); wave2 = math.sin(angle * 5 - self.pulse_phase * 1.5) * (radius * 0.02 * amp_factor); r = radius + wave1 + wave2; x = center.x() + r * math.cos(angle); y = center.y() + r * math.sin(angle)
            if i == 0: path.moveTo(x, y)
            else: path.lineTo(x, y)
        focal_point = center - QPointF(radius * 0.2, radius * 0.2); grad = QRadialGradient(center, radius, focal_point); alpha_center = 40 if self.is_interactive else 15; alpha_edge = 128 if self.is_interactive else 80
        grad.setColorAt(0, QColor(color.red(), color.green(), color.blue(), int(alpha_center * opacity_mult))); grad.setColorAt(0.8, QColor(color.red(), color.green(), color.blue(), int(alpha_edge * opacity_mult))); grad.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QBrush(grad)); painter.drawPath(path)

    def _draw_rings(self, painter, center, color):
        painter.setBrush(Qt.BrushStyle.NoBrush); ring_color = QColor(color.red(), color.green(), color.blue(), 40); pen = QPen(ring_color); pen.setWidth(1); painter.setPen(pen); painter.save(); painter.translate(center); painter.rotate(self.ring_angle)
        for i in range(2): painter.rotate(45 * i); r_w = self.current_radius * 1.4; r_h = self.current_radius * 0.5; painter.drawEllipse(QPointF(0, 0), r_w, r_h)
        painter.restore()

    def animate(self):
        is_active = (self.io_handler.is_busy() or self.state == "PROCESSING" or self.state == "LOADING") and self.visual_mode == "ACTIVE"
        phase_inc = 0.4 if self.state == "LOADING" else (0.25 if is_active else (0.1 if self.visual_mode == "ACTIVE" else 0.05))
        self.pulse_phase += phase_inc; self.ring_angle += 0.5
        if self.state == "LOADING": self.target_radius = self.base_radius + math.sin(self.pulse_phase * 2) * 5
        elif is_active:
            if self.io_handler.is_busy(): self.state = "SPEAKING"; self.target_radius = self.base_radius + random.randint(-4, 8)
        else: pulse_amp = 2 if self.visual_mode == "ACTIVE" else 4; self.target_radius = self.base_radius + math.sin(self.pulse_phase) * pulse_amp
        for i in range(3): self.orbit_angles[i] += self.orbit_speeds[i]
        diff = self.target_radius - self.current_radius; self.current_radius += diff * 0.2; self.update() 

    def on_submit(self):
        if not self.input_box.isEnabled(): return
        txt = self.input_box.text()
        if not txt: return
        if txt.lower() == "sair": self.quit_app(); return
        self.input_box.clear(); self.state = "PROCESSING"; self.update(); self.response_label.hide()
        threading.Thread(target=self.process_command, args=(txt, False), daemon=True).start()

    def wake_up(self): self.visual_mode = "ACTIVE"; self.sleep_timer.stop(); self.update()
    def go_to_sleep(self):
        if self.visual_mode == "STANDBY": return
        self.visual_mode = "STANDBY"; self.state = "IDLE"
        self.update()

    def quit_app(self):
        print("[GUI] Encerrando Aeon...")
        
        # 1. Avisa os módulos para desligarem
        try:
            audicao_mod = self.module_manager.get_module("audicao")
            if audicao_mod and hasattr(audicao_mod, 'stop'):
                print("[GUI] Desligando módulo de audição...")
                audicao_mod.stop()
        except Exception as e:
            print(f"[GUI] Erro ao parar módulo de audição: {e}")
            
        # 2. Para o listener de hotkey de forma segura
        if self.hotkey_listener and self.hotkey_listener.is_alive():
            print("[GUI] Parando listener de hotkey...")
            self.hotkey_listener.stop()
            # Não é ideal chamar join() na thread principal da GUI,
            # mas o stop() do pynput geralmente é rápido.
            # Se isso causar bloqueios, uma abordagem de sinal seria melhor.

        # 3. Dá um feedback final sonoro
        self.io_handler.falar("Encerrando.")
        
        # 4. Encerra a aplicação Qt
        # O 'after' aqui agenda o quit para ocorrer após o processamento dos eventos atuais.
        self.after(200, QApplication.instance().quit)

    def process_command(self, txt, silent=False):
        try:
            cmd = txt.lower().strip()
            if self.visual_mode == "STANDBY" and not silent:
                if any(w in cmd for w in ["acordar", "aeon", "ativar", "oi", "olá", "acorde", "escuta"]): self.wake_up()
                else: return
            if not silent: self.after(0, self.wake_up); self.after(0, self.sleep_timer.start, 120000) 
            if cmd in ["ficar invisível", "ocultar"]: self.hidden_mode = True; self.set_click_through(True); self.io_handler.falar("Ok."); return
            if cmd in ["ficar visível", "mostrar"]: self.hidden_mode = False; self.set_click_through(False); self.io_handler.falar("Ok."); self.update(); return
            if not silent: self.state = "PROCESSING"
            response = self.module_manager.route_command(txt)
            self.after(0, lambda: setattr(self, 'state', 'IDLE'))
            if not silent: self.after(0, self.show_response, response); self.io_handler.falar(response)
        except Exception as e:
            # Mesmo em modo silencioso, um erro deve ser reportado.
            error_message = f"Erro em segundo plano: {e}"
            print(f"[SPHERE][ERRO] {error_message}")
            self.after(0, self.show_response, error_message)
            # Garante que o estado de processamento seja resetado.
            self.after(0, lambda: setattr(self, 'state', 'IDLE'))

    def show_response(self, text):
        display_text = text[:300] + "..." if len(text) > 300 else text; self.response_label.setText(display_text); self.response_label.show()
        display_time = max(4000, len(display_text) * 50); QTimer.singleShot(display_time, self.response_label.hide)

    def add_message(self, text, sender="SISTEMA"): self.after(0, self.show_response, f"{sender}: {text}")
    def _handle_timer_signal(self, ms, func, args): QTimer.singleShot(ms, lambda: func(*args))
    def after(self, ms, func, *args): self.timer_signal.emit(ms, func, args)
    def mousePressEvent(self, event):
        if self.is_interactive and event.button() == Qt.MouseButton.LeftButton: self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft(); event.accept()
    def mouseMoveEvent(self, event):
        if self.is_interactive and self.drag_pos and event.buttons() == Qt.MouseButton.LeftButton: self.move(event.globalPosition().toPoint() - self.drag_pos); event.accept()
    def mouseReleaseEvent(self, event):
        if self.is_interactive and self.drag_pos and event.button() == Qt.MouseButton.LeftButton: self.drag_pos = None; event.accept(); self.after(100, self.set_click_through, True)
    def contextMenuEvent(self, event):
        menu = QMenu(self); menu.setStyleSheet(f"background-color: {C_BG_INPUT}; color: {C_TEXT}; border: 1px solid {C_BORDER};"); action_visivel = menu.addAction("Alternar Visibilidade"); action_visivel.triggered.connect(lambda: self.set_click_through(not self.is_interactive)); action_sair = menu.addAction("Encerrar Aeon"); action_sair.triggered.connect(self.quit_app); menu.exec(event.globalPos())
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape: self.set_click_through(True)
    def closeEvent(self, event): self.quit_app(); event.accept()