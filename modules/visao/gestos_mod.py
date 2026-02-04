# SAFE IMPORT V86
try:
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    GEAR_AVAILABLE = True
except ImportError:
    GEAR_AVAILABLE = False

import threading
import time
import os
import numpy as np
import math
import pyautogui
from modules.base_module import AeonModule

# Conexoes dos landmarks da mao para desenhar as linhas
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),         # Polegar
    (0, 5), (5, 6), (6, 7), (7, 8),         # Indicador
    (5, 9), (9, 10), (10, 11), (11, 12),     # Medio
    (9, 13), (13, 14), (14, 15), (15, 16),   # Anelar
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Mindinho e palma
]

class GestosModule(AeonModule):
    """
    Modulo de Visao Computacional para controle do Aeon via gestos.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Gestos"
        self.triggers = [
            "ativar gestos", "ligar gestos", "parar gestos", "desligar gestos",
            "modo gestos", "testar camera", "desligar camera"
        ]
        self.dependencies = ["gui", "io_handler", "installer"]

        self.detector = None
        self.detection_result = None
        self.model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'hand_landmarker.task'))
        self.running = False
        self.thread = None
        self.cap = None
        self.ultimo_gesto = "NADA"
        self.debug_mode = False
        self.tracking_gesture = None
        self.tracking_start_pos = None
        self.tracking_start_time = None
        self.debounce_gesture = None
        self.debounce_start_time = None
        self.DEBOUNCE_TIME = 0.5
        self.action_cooldown_end_time = 0
        self.ACTION_COOLDOWN_PERIOD = 2.0

    def check_dependencies(self):
        if not GEAR_AVAILABLE:
            print("[GEAR] Aviso: 'opencv-python' ou 'mediapipe' nao instalados. Modulo de gestos desativado.")
        return super().check_dependencies()

    def on_load(self) -> bool:
        """Verifica as dependencias criticas no momento do carregamento."""
        if not GEAR_AVAILABLE:
            print("[GEAR][ERRO] 'opencv-python' ou 'mediapipe' nao instalados. Modulo de gestos desativado.")
            return False
        
        # Se o modelo nao existir, tenta baixa-lo agora.
        if not os.path.exists(self.model_path) or os.path.getsize(self.model_path) < 1000:
            print(f"[GEAR] Modelo de gestos '{os.path.basename(self.model_path)}' ausente. Baixando...")
            installer = self.core_context.get("installer")
            if installer and hasattr(installer, 'download_file'):
                url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                success = installer.download_file(url, self.model_path)
                if not success:
                    print(f"[GEAR][ERRO] Falha ao baixar o modelo de gestos. Modulo desativado.")
                    return False
            else:
                print("[GEAR][ERRO] Installer nao disponivel para baixar o modelo. Modulo desativado.")
                return False
        
        print("[GEAR] Dependencias e modelo de gestos verificados com sucesso.")
        return True

    def process(self, command: str) -> str:
        cmd = command.lower()

        commands_start = ["modo gestos", "ativar gestos", "ligar gestos", "testar camera"]
        commands_stop = ["parar gestos", "desligar gestos", "desligar camera"]
        
        if any(c in cmd for c in commands_start):
            if not GEAR_AVAILABLE:
                return "O modo de gestos esta desativado. Instale 'opencv-python' e 'mediapipe'."
            if self.running:
                return "A visao de gestos ja esta operando."
            
            is_debug = "testar camera" in cmd
            self.start_gesture_vision(debug=is_debug)
            return "Visao de gestos iniciada." if not is_debug else "Modo de teste de camera ativado."

        if any(c in cmd for c in commands_stop):
            if not self.running:
                return "A visao de gestos nao esta ativa."
            self.stop_gesture_vision()
            return "Visao de gestos encerrada."

        return "" # Nenhum comando correspondente

    def _initialize_detector(self):
        """Inicializa o detector de maos do MediaPipe, baixando o modelo se necessario."""
        if not os.path.exists(self.model_path) or os.path.getsize(self.model_path) < 1000:
            print(f"[GEAR] Modelo de gestos ausente ou invalido. Baixando...")
            if os.path.exists(self.model_path):
                os.remove(self.model_path)
                
            installer = self.core_context.get("installer")
            if installer:
                url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                installer.download_file(url, self.model_path)
            
            if not os.path.exists(self.model_path):
                print(f"[GEAR][ERRO] Falha ao obter modelo de gestos.")
                self.detector = None
                return

        try:
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.LIVE_STREAM,
                num_hands=1, min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.5, min_tracking_confidence=0.5,
                result_callback=self._result_callback)
            self.detector = vision.HandLandmarker.create_from_options(options)
            print("[GEAR] Motor de Gestos (MediaPipe) inicializado.")
        except Exception as e:
            print(f"[GEAR][ERRO] Falha ao inicializar MediaPipe: {e}")
            self.detector = None

    def _result_callback(self, result: vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
        self.detection_result = result

    def start_gesture_vision(self, debug=False):
        if self.detector is None:
            print("[GEAR] Primeira execucao, inicializando o detector de gestos...")
            self._initialize_detector()

        if not self.detector:
            print("[GEAR][ERRO] Detector de gestos nao inicializado. Nao e possivel iniciar a visao.")
            io = self.core_context.get("io_handler")
            if io: io.falar("Desculpe, nao consegui iniciar o motor de gestos.")
            return

        self.running = True
        self.debug_mode = debug
        self.thread = threading.Thread(target=self._gesture_vision_loop, daemon=True)
        self.thread.start()

    def stop_gesture_vision(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        if GEAR_AVAILABLE and self.debug_mode:
            cv2.destroyAllWindows()
        self.debug_mode = False

    def _gesture_vision_loop(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("[GEAR][ERRO] Nao foi possivel acessar a camera.")
            self.running = False
            io = self.core_context.get("io_handler")
            if io: io.falar("Erro critico: nao consegui acessar sua camera.")
            return
        
        while self.running and self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                time.sleep(0.1)
                continue

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.detector.detect_async(mp_image, int(time.time() * 1000))
            
            if self.detection_result and self.detection_result.hand_landmarks:
                hand_landmarks = self.detection_result.hand_landmarks[0]
                dedos = self._contar_dedos(hand_landmarks)
                gesto_detectado = self._classificar_gesto(dedos, hand_landmarks)
                self._handle_gesture_logic(gesto_detectado, hand_landmarks)
                if self.debug_mode:
                    frame = self._draw_landmarks_on_image(frame, self.detection_result)
            else:
                self._reset_tracking_state()
            
            if self.debug_mode:
                cv2.putText(frame, f"Gesto: {self.ultimo_gesto}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow("Aeon Gestos Test", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop_gesture_vision()
                    break
            time.sleep(0.02)

        if self.cap: self.cap.release()
        if self.debug_mode: cv2.destroyAllWindows()

    def _draw_landmarks_on_image(self, bgr_image, detection_result):
        if not detection_result or not detection_result.hand_landmarks: return bgr_image
        annotated_image = np.copy(bgr_image)
        h, w, _ = annotated_image.shape
        for hand_landmarks in detection_result.hand_landmarks:
            for landmark in hand_landmarks:
                px, py = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(annotated_image, (px, py), 5, (0, 255, 0), -1)
            for connection in HAND_CONNECTIONS:
                start_idx, end_idx = connection
                if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                    start_lm = hand_landmarks[start_idx]
                    end_lm = hand_landmarks[end_idx]
                    start_pt = (int(start_lm.x * w), int(start_lm.y * h))
                    end_pt = (int(end_lm.x * w), int(end_lm.y * h))
                    cv2.line(annotated_image, start_pt, end_pt, (255, 0, 0), 2)
        return annotated_image

    def _contar_dedos(self, hand_landmarks):
        dedos, pontas, pips = [], [8, 12, 16, 20], [6, 10, 14, 18]
        dist_ref = math.hypot(hand_landmarks[0].x - hand_landmarks[9].x, hand_landmarks[0].y - hand_landmarks[9].y)
        dist_polegar = math.hypot(hand_landmarks[4].x - hand_landmarks[17].x, hand_landmarks[4].y - hand_landmarks[17].y)
        dedos.append(dist_polegar > dist_ref * 0.6)
        for ponta, pip in zip(pontas, pips):
            dedos.append(hand_landmarks[ponta].y < hand_landmarks[pip].y)
        return dedos

    def _classificar_gesto(self, dedos, hand_landmarks):
        if sum(dedos) == 0:
            dist_x = abs(hand_landmarks[5].x - hand_landmarks[17].x)
            dist_y = abs(hand_landmarks[5].y - hand_landmarks[17].y)
            return "AGARRAR" if dist_x < dist_y * 0.5 else "FECHA"
        if sum(dedos) >= 4: return "ABRE"
        if dedos[1] and not dedos[2] and not dedos[3] and not dedos[4]: return "XIU"
        if dedos[1] and dedos[2] and not dedos[0] and not dedos[3] and not dedos[4]: return "VITORIA"
        if dedos[0] and dedos[1] and dedos[4] and not dedos[2] and not dedos[3]: return "SAIR"
        return "DESCONHECIDO"

    def _reset_tracking_state(self):
        self.tracking_gesture = None
        self.tracking_start_pos = None
        self.tracking_start_time = None
        self.debounce_gesture = None
        self.debounce_start_time = None

    def _handle_gesture_logic(self, gesto, landmarks):
        if time.time() < self.action_cooldown_end_time:
            self._reset_tracking_state()
            return

        if self.tracking_gesture is None:
            if gesto != self.debounce_gesture:
                self.debounce_gesture = gesto
                self.debounce_start_time = time.time()
            if gesto == "FECHA":
                self.tracking_gesture = "FECHA_TRACKING"
                self.tracking_start_pos = (landmarks[0].x, landmarks[0].y)
                self.tracking_start_time = time.time()
                return
            if time.time() - self.debounce_start_time > self.DEBOUNCE_TIME:
                if self.debounce_gesture != self.ultimo_gesto and self.debounce_gesture not in ["DESCONHECIDO", "NADA", "FECHA"]:
                    self._executar_acao(self.debounce_gesture)
                self.ultimo_gesto = self.debounce_gesture
        elif self.tracking_gesture == "FECHA_TRACKING":
            if time.time() - self.tracking_start_time > 1.0:
                self._executar_acao("FECHA")
                self._reset_tracking_state()
            elif gesto == "ABRE":
                self._executar_acao("ABRIR_PAINEL")
                self._reset_tracking_state()
            elif gesto == "FECHA" and abs(landmarks[0].x - self.tracking_start_pos[0]) > 0.2:
                self._executar_acao("MODO_INVISIVEL")
                self._reset_tracking_state()
            elif gesto != "FECHA":
                self._reset_tracking_state()

    def _executar_acao(self, gesto):
        io = self.core_context.get("io_handler")
        gui = self.core_context.get("gui")
        print(f"[GEAR] Gesto '{gesto}' detectado, executando acao.")
        self.action_cooldown_end_time = time.time() + self.ACTION_COOLDOWN_PERIOD

        if gesto == "ABRIR_PAINEL":
            if io: io.falar("Abrindo o painel.")
            pyautogui.hotkey('ctrl', 'shift', 'a')
            return
        if not gui or not hasattr(gui, 'after'): return

        actions = {
            "XIU": lambda: io.calar_boca() if io else None,
            "AGARRAR": lambda: gui.set_click_through(False) if hasattr(gui, 'set_click_through') else None,
            "VITORIA": lambda: gui.process_command("modo visivel") if hasattr(gui, 'process_command') else None,
            "FECHA": lambda: gui.go_to_sleep() if hasattr(gui, 'go_to_sleep') else None,
            "ABRE": lambda: gui.wake_up() if hasattr(gui, 'wake_up') else None,
            "SAIR": lambda: gui.quit_app() if hasattr(gui, 'quit_app') else os._exit(0),
            "MODO_INVISIVEL": lambda: gui.process_command("modo invisivel") if hasattr(gui, 'process_command') else None,
        }
        if gesto in actions:
            gui.after(0, actions[gesto])

    def on_unload(self) -> bool:
        self.stop_gesture_vision()
        if self.detector:
            self.detector.close()
        return True