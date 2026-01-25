import sys
import os
import math
import random
import ctypes
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLineEdit, QFrame, QLabel
from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QPainterPath
from pynput import keyboard as pynput_keyboard

# Importações do Core
from core.module_manager import ModuleManager
from core.io_handler import IOHandler
from core.config_manager import ConfigManager
from core.context_manager import ContextManager

# Tenta importar Brain de forma robusta
try:
    from core.brain import AeonBrain as Brain
except ImportError:
    try:
        from core.brain import Brain
    except ImportError:
        print("ERRO CRÍTICO: Classe Brain não encontrada.")

# --- CONFIGURAÇÕES DE CORES (PALETA ALTO CONTRASTE PARA DALTONISMO) ---
C_ACTIVE = QColor(255, 0, 0)       # Vermelho Puro (Ativo/Idle)
C_PROCESS = QColor(0, 191, 255)    # Deep Sky Blue (Processando)
C_BG_INPUT = "#000000"             # Preto Absoluto
C_BORDER = "#8B0000"               # Vermelho Escuro
C_TEXT = "#FFFFFF"                 # Branco
C_PASTEL = QColor(200, 150, 150, 40) # Vermelho Pastel Suave para Standby
C_AURA_ONLINE = QColor(0, 255, 0, 255)  # Verde Sólido (Online)
C_AURA_OFFLINE = QColor(255, 0, 0, 255) # Vermelho Sólido (Offline)

class AeonSphere(QMainWindow):
    activate_signal = pyqtSignal()  # Sinal para summon global
    timer_signal = pyqtSignal(int, object, tuple) # Sinal para timers seguros entre threads

    def __init__(self):
        super().__init__()
        
        self.hotkey_listener = None
        # --- Inicialização do Core ---
        self.config_manager = ConfigManager()
        cfg = getattr(self.config_manager, 'config', {})
        self.io_handler = IOHandler(cfg, None)
        
        try:
            self.brain = Brain(self.config_manager)
        except Exception as e:
            print(f"[SPHERE] Erro ao iniciar Brain: {e}")
            self.brain = None
            
        self.context_manager = ContextManager()
        
        # Garante que o workspace seja criado na raiz real do projeto
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.workspace_path = os.path.join(root_dir, "workspace")
        os.makedirs(self.workspace_path, exist_ok=True)

        self.core_context = {
            "config_manager": self.config_manager,
            "io_handler": self.io_handler,
            "brain": self.brain,
            "context": self.context_manager,
            "gui": self, 
            "workspace": self.workspace_path
        }
        self.module_manager = ModuleManager(self.core_context)
        self.core_context["module_manager"] = self.module_manager
        self.module_manager.load_modules()

        # Configuração da Janela Transparente e Sem Bordas
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Tamanho e Posição Inicial (Canto superior direito)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen.width() - 280, 50, 250, 250)
        
        # Estado da Animação
        self.state = "IDLE" 
        self.base_radius = 50
        self.current_radius = 50
        self.target_radius = 50
        self.pulse_phase = 0
        # Inicializa órbitas independentes (Posição, Velocidade e Distância aleatórias)
        self.orbit_angles = [random.uniform(0, 2 * math.pi) for _ in range(3)]
        self.orbit_speeds = [random.uniform(0.002, 0.004) for _ in range(3)]
        self.orbit_factors = [random.uniform(1.05, 1.15) for _ in range(3)]
        self.is_interactive = False
        self.drag_pos = None
        self.hidden_mode = False
        self.ring_angle = 0
        
        # --- Lógica de Presença (Wake Word) ---
        self.visual_mode = "STANDBY" # STANDBY ou ACTIVE
        self.sleep_timer = QTimer()
        self.sleep_timer.timeout.connect(self.go_to_sleep)

        # Widget Central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Balão de Resposta (Flutuante)
        self.response_label = QLabel(self.central_widget)
        self.response_label.setGeometry(10, 10, 230, 60)
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.response_label.setWordWrap(True)
        self.response_label.setStyleSheet(f"""
            color: {C_TEXT}; 
            font-family: 'Consolas'; 
            font-size: 11px; 
            background-color: rgba(0, 0, 0, 180); 
            border: 1px solid {C_BORDER};
            border-radius: 5px;
        """)
        self.response_label.hide()

        # Caixa de Input (Estilo Sith)
        self.input_frame = QFrame(self.central_widget)
        self.input_frame.setGeometry(25, 160, 200, 45)
        self.input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {C_BG_INPUT};
                border: 2px solid {C_BORDER};
                border-radius: 10px;
            }}
        """)
        
        self.input_box = QLineEdit(self.input_frame)
        self.input_box.setGeometry(10, 10, 180, 30)
        self.input_box.setPlaceholderText("Comando...")
        self.input_box.setStyleSheet(f"background: transparent; border: none; color: {C_TEXT}; font-family: Consolas; font-size: 14px;")
        self.input_box.returnPressed.connect(self.on_submit)

        # Timer de Animação (30 FPS)
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(30) 

        # Configura Atalho Global (Ctrl+Shift+A)
        self.activate_signal.connect(lambda: self.set_click_through(False))
        self.timer_signal.connect(self._handle_timer_signal)
        threading.Thread(target=self._setup_global_hotkey, daemon=True).start()

        # Inicia oculta (Modo Fantasma)
        self.set_click_through(True)
        self.after(3000, lambda: threading.Thread(target=self.process_command, args=("ativar escuta", True), daemon=True).start()) # silent=True mantém standby
        self.after(4000, lambda: threading.Thread(target=self.process_command, args=("ativar visão", True), daemon=True).start()) # Inicia a visão silenciosamente

    def set_click_through(self, enable: bool):
        """Controla se o mouse atravessa a janela ou interage com ela."""
        hwnd = int(self.winId())
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x80000
        WS_EX_TRANSPARENT = 0x20
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        
        if enable:
            style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            self.input_frame.hide()
            self.is_interactive = False
        else:
            style = style & ~WS_EX_TRANSPARENT
            self.input_frame.show()
            self.input_box.setFocus()
            self.is_interactive = True
            self.hidden_mode = False
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    def _setup_global_hotkey(self):
        """Escuta atalhos do sistema para invocar o Aeon."""
        self.hotkey_listener = pynput_keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+a': self.activate_signal.emit
        })
        self.hotkey_listener.start()

    def paintEvent(self, event):
        """Desenha a esfera com gradientes e a aura de status."""
        if self.hidden_mode and not self.is_interactive:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Define a cor base: Pastel se estiver em Standby
        color = C_PASTEL if self.visual_mode == "STANDBY" else (C_PROCESS if self.state == "PROCESSING" else C_ACTIVE)
        center = QPointF(self.width() / 2, 110.0) # Desce um pouco para dar espaço ao texto

        # --- DESENHO DAS BOLINHAS ORBITANTES (STATUS ONLINE/OFFLINE) ---
        is_online = self.brain.online if self.brain else False
        base_aura_color = C_AURA_ONLINE if is_online else C_AURA_OFFLINE

        painter.setPen(Qt.PenStyle.NoPen)

        # Só desenha bolinhas e anéis se NÃO estiver em standby
        if self.visual_mode == "ACTIVE":
            for i in range(3): # 3 mini bolinhas orbitando
                angle = self.orbit_angles[i]
                orbit_radius = self.current_radius * self.orbit_factors[i]
                bx = center.x() + orbit_radius * math.cos(angle)
                by = center.y() + orbit_radius * math.sin(angle)
                ball_center = QPointF(bx, by)
                
                ball_grad = QRadialGradient(ball_center, 5)
                ball_grad.setColorAt(0, QColor(base_aura_color.red(), base_aura_color.green(), base_aura_color.blue(), 100))
                ball_grad.setColorAt(1, Qt.GlobalColor.transparent)
                
                painter.setBrush(QBrush(ball_grad))
                painter.drawEllipse(ball_center, 5, 5)
            
            self._draw_rings(painter, center, color)
        
        # --- DESENHO DA ESFERA ONDULADA E TRANSLÚCIDA ---
        # Camada externa (mais suave)
        self._draw_undulating_sphere(painter, center, color, self.current_radius, 1.0)
        # Camada interna (mais brilhante para dar profundidade)
        self._draw_undulating_sphere(painter, center, color, self.current_radius * 0.8, 0.6)

    def _draw_undulating_sphere(self, painter, center, color, radius, opacity_mult):
        """Desenha uma forma orgânica ondulada e translúcida."""
        path = QPainterPath()
        num_points = 80
        
        # Aumenta a amplitude das ondas se estiver ativo. Em Standby, amp_factor é 0 (sem ondas).
        is_active = self.io_handler.is_busy() or self.state == "PROCESSING"
        amp_factor = 3.5 if is_active else (1.0 if self.visual_mode == "ACTIVE" else 0.0)

        for i in range(num_points + 1):
            angle = (i * 2 * math.pi) / num_points
            # Ondulações baseadas na fase da animação
            wave1 = math.sin(angle * 2 + self.pulse_phase * 1.2) * (radius * 0.03 * amp_factor)
            wave2 = math.sin(angle * 5 - self.pulse_phase * 1.5) * (radius * 0.02 * amp_factor)
            r = radius + wave1 + wave2
            x = center.x() + r * math.cos(angle)
            y = center.y() + r * math.sin(angle)
            if i == 0: path.moveTo(x, y)
            else: path.lineTo(x, y)

        # Gradiente com ponto focal deslocado para simular volume 3D
        focal_point = center - QPointF(radius * 0.2, radius * 0.2)
        grad = QRadialGradient(center, radius, focal_point)
        
        # Opacidade dinâmica: aumenta para ~50% (128) quando interativo
        alpha_center = 40 if self.is_interactive else 15
        alpha_edge = 128 if self.is_interactive else 80

        grad.setColorAt(0, QColor(color.red(), color.green(), color.blue(), int(alpha_center * opacity_mult)))
        grad.setColorAt(0.8, QColor(color.red(), color.green(), color.blue(), int(alpha_edge * opacity_mult)))
        grad.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

    def _draw_rings(self, painter, center, color):
        """Desenha anéis tecnológicos sutis e translúcidos."""
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Cor do anel com transparência bem alta (quase invisível)
        ring_color = QColor(color.red(), color.green(), color.blue(), 40)
        pen = QPen(ring_color)
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Salva o estado do painter para rotacionar
        painter.save()
        painter.translate(center)
        painter.rotate(self.ring_angle)
        
        # Desenha 2 anéis elípticos cruzados
        for i in range(2):
            painter.rotate(45 * i)
            r_w = self.current_radius * 1.4
            r_h = self.current_radius * 0.5
            painter.drawEllipse(QPointF(0, 0), r_w, r_h)
            
        painter.restore()

    def animate(self):
        """Gerencia as pulsações e vibrações."""
        # So vibra se estiver no modo visual ATIVO
        is_active = (self.io_handler.is_busy() or self.state == "PROCESSING") and self.visual_mode == "ACTIVE"
        
        # Incrementa a fase (mais lento em standby para a "respiração")
        phase_inc = 0.25 if is_active else (0.1 if self.visual_mode == "ACTIVE" else 0.05)
        self.pulse_phase += phase_inc
        self.ring_angle += 0.5 # Rotação lenta dos anéis

        if is_active:
            if self.io_handler.is_busy(): self.state = "SPEAKING"
            # Vibração errática no tamanho
            self.target_radius = self.base_radius + random.randint(-4, 8)
        else:
            # Pulsação suave senoidal (Respiração)
            pulse_amp = 2 if self.visual_mode == "ACTIVE" else 4
            self.target_radius = self.base_radius + math.sin(self.pulse_phase) * pulse_amp

        # Atualiza ângulos das órbitas de forma independente e lenta
        for i in range(3):
            self.orbit_angles[i] += self.orbit_speeds[i]

        # Suavização do movimento (Lerp)
        diff = self.target_radius - self.current_radius
        self.current_radius += diff * 0.2
        self.update() 

    def on_submit(self):
        """Envia o comando para o cérebro."""
        txt = self.input_box.text()
        if not txt: return
        
        if txt.lower() == "ocultar":
            self.set_click_through(True)
            self.input_box.clear()
            return
        if txt.lower() == "sair":
            QApplication.quit()
            return
            
        self.input_box.clear()
        self.state = "PROCESSING"
        self.update()
        self.response_label.hide()
        threading.Thread(target=self.process_command, args=(txt, False), daemon=True).start()

    def process_in_background(self, txt):
        """Compatibilidade com módulos de áudio."""
        threading.Thread(target=self.process_command, args=(txt,), daemon=True).start()

    def wake_up(self):
        """Acorda a esfera para o modo ativo."""
        self.visual_mode = "ACTIVE"
        self.sleep_timer.stop()
        self.update()

    def go_to_sleep(self):
        """Retorna a esfera para o modo standby (respiração)."""
        self.visual_mode = "STANDBY"
        self.state = "IDLE"
        self.update()

    def quit_app(self):
        """Fecha a aplicação, garantindo que os módulos parem."""
        print("[GUI] Recebido comando para encerrar. Parando módulos...")
        # 1. Parar módulos que rodam em threads
        try:
            audicao = self.module_manager.get_module("Audicao")
            if audicao and hasattr(audicao, 'stop'):
                audicao.stop()
                print("[GUI] Módulo Audicao parado.")

            gestos = self.module_manager.get_module("Gestos")
            if gestos and hasattr(gestos, 'stop_vision'):
                gestos.stop_vision()
                print("[GUI] Módulo Gestos parado.")
        except Exception as e:
            print(f"[GUI][ERRO] Erro ao parar módulos: {e}")

        # 2. Falar e agendar o fechamento
        self.io_handler.falar("Encerrando.")
        self.after(1000, QApplication.instance().quit)

    def process_command(self, txt, silent=False):
        try:
            cmd = txt.lower().strip()
            
            wake_words = ["aeon", "aion", "iron", "ion", "aon", "eion", "iniciar", "acordar"]
            
            # 1. Verifica se é APENAS a palavra de ativação
            if cmd in wake_words:
                self.after(0, self.wake_up)
                self.io_handler.falar("Chamou?")
                self.after(0, self.sleep_timer.start, 5000) # Volta a dormir em 5s se nada for dito
                return

            # 2. Verifica se o comando começa com a palavra de ativação (ex: "Aeon, horas")
            is_wake_call = any(cmd.startswith(w) for w in wake_words)
            
            # Se estiver em Standby e não for uma chamada direta ou comando silencioso, ignora
            if self.visual_mode == "STANDBY" and not is_wake_call and not silent:
                return

            # Se houver um comando e não for silencioso, cancela o timer de sono e acorda
            if not silent:
                self.after(0, self.wake_up)
                self.after(0, self.sleep_timer.start, 10000) # Volta a dormir após 10s de inatividade

            if cmd in ["ficar invisível", "modo invisível", "sumir", "desativar esfera", "esconder"]:
                self.hidden_mode = True
                self.set_click_through(True)
                self.io_handler.falar("Entendido. Entrando em modo invisível.")
                return
            
            if cmd in ["ficar visível", "modo visível", "aparecer", "ativar esfera", "mostrar"]:
                self.hidden_mode = False
                self.set_click_through(False) # Torna interativa novamente
                self.io_handler.falar("Modo visível ativado.")
                self.update()
                return

            if not silent: self.state = "PROCESSING"
            response = self.module_manager.route_command(txt)
            # Muda estado para IDLE antes de falar para permitir animação de fala
            self.after(0, lambda: setattr(self, 'state', 'IDLE'))
            # Exibe resposta na interface se não for comando silencioso
            if not silent: self.after(0, self.show_response, response)
            self.io_handler.falar(response)
        except Exception as e:
            print(f"Erro: {e}")

    def show_response(self, text):
        """Exibe o texto no balão flutuante."""
        # Desativado temporariamente para remover o balão de fala da interface
        # # Forçado para 300 caracteres conforme solicitado
        # display_text = text[:300] + "..." if len(text) > 300 else text
        # self.response_label.setText(display_text)
        # self.response_label.show()
        # # Tempo dinâmico: 1 segundo para cada 20 caracteres (mínimo 5s)
        # display_time = max(5000, len(display_text) * 50)
        # QTimer.singleShot(display_time, self.response_label.hide)
        pass

    def add_message(self, text, sender="SISTEMA"):
        """Compatibilidade com módulos que enviam mensagens de texto."""
        self.after(0, self.show_response, f"{sender}: {text}")
    
    def refresh_workspace_view(self):
        """Compatibilidade com DevFactory."""
        pass 
    
    def _handle_timer_signal(self, ms, func, args):
        """Executa o timer de forma segura na thread principal."""
        QTimer.singleShot(ms, lambda: func(*args))

    def after(self, ms, func, *args):
        """Dispara um evento após MS milissegundos, seguro para threads."""
        self.timer_signal.emit(ms, func, args)

    def mousePressEvent(self, event):
        """Inicia o arrasto da janela se estiver no modo interativo."""
        if self.is_interactive and event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Move a janela acompanhando o mouse."""
        if self.is_interactive and self.drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Finaliza o arrasto e torna a janela click-through novamente."""
        if self.is_interactive and self.drag_pos and event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = None
            event.accept()
            # Uma pequena pausa antes de voltar ao modo fantasma para evitar cliques acidentais
            self.after(100, self.set_click_through, True)

    def keyPressEvent(self, event):
        """Atalhos de teclado."""
        if event.key() == Qt.Key.Key_Escape:
            self.set_click_through(True)

    def closeEvent(self, event):
        """Garante que os processos parem ao fechar."""
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.io_handler.calar_boca()
        event.accept()