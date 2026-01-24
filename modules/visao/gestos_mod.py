
import cv2
import mediapipe as mp
import threading
import time
import os
import numpy as np
import math
import pyautogui
from modules.base_module import AeonModule
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

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
    Módulo de Visão Computacional para controle do Aeon via gestos.
    Usa a nova API MediaPipe Tasks.
    """
    def __init__(self, core_context):
        super().__init__(core_context)
        self.name = "Gestos"
        self.triggers = ["ativar visão", "ligar câmera", "parar visão", "desligar câmera", "modo gestos", "testar câmera", "ver pela câmera", "acessar câmera"]
        
        self.detector = None
        self.detection_result = None
        self.model_path = 'hand_landmarker.task' # ATENCAO: O arquivo deve estar no diretorio raiz do projeto

        # Estado da Thread
        self.running = False
        self.thread = None
        self.cap = None
        self.ultimo_gesto = "NADA"
        self.debug_mode = False
        
        # Estado para gestos compostos
        self.tracking_gesture = None
        self.tracking_start_pos = None
        self.tracking_start_time = None
        
        # Debounce para estabilizar a detecção
        self.debounce_gesture = None
        self.debounce_start_time = None
        self.DEBOUNCE_TIME = 0.5 # 500ms de estabilidade necessária

        # Cooldown para evitar ações repetidas
        self.action_cooldown_end_time = 0
        self.ACTION_COOLDOWN_PERIOD = 2.0 # 2 segundos de espera após uma ação
        
        self._initialize_detector()

    def _initialize_detector(self):
        """Inicializa o detector de maos do MediaPipe."""
        try:
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.LIVE_STREAM,
                num_hands=1,
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
                result_callback=self._result_callback
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
            print("[GEAR] Motor de Gestos (MediaPipe Task API) inicializado.")
        except Exception as e:
            print(f"[GEAR][ERRO] Falha ao inicializar MediaPipe Task API: {e}")
            print(f"[GEAR][ERRO] Verifique se o arquivo '{self.model_path}' existe no diretorio raiz.")
            self.detector = None

    def _result_callback(self, result: vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
        """Callback para armazenar o resultado da deteccao."""
        self.detection_result = result

    @property
    def metadata(self) -> dict:
        return {
            "description": "Permite ao Aeon acessar a câmera física, ver o usuário e reconhecer gestos manuais (XIU, VITORIA, ABRE, FECHA) para controle do sistema.",
            "version": "1.2.0"
        }

    def on_load(self) -> bool:
        return self.detector is not None

    def process(self, command: str) -> str:
        cmd = command.lower()
        
        # Comando para testar a camera em modo debug
        if "testar câmera" in cmd or "testar camera" in cmd:
            self.debug_mode = True
            if not self.running:
                self.start_vision(debug=True)
                return "Modo de teste de câmera ativado. Verifique a janela de vídeo."
            return "Modo de teste de câmera já está ativo."

        # Comandos para ativar a visao normal
        if any(k in cmd for k in ["ativar visão", "ligar câmera", "modo gestos", "ver pela câmera", "acessar câmera"]):
            if self.running:
                return "A visão de gestos já está operando."
            
            self.start_vision()
            return "Visão de gestos iniciada. Agora posso ver seus comandos."

        # Comandos para desativar a visao
        if any(k in cmd for k in ["parar visão", "desligar câmera"]):
            self.stop_vision()
            return "Câmera desligada e visão de gestos encerrada."
            
        return ""

    def start_vision(self, debug=False):
        if not self.detector:
            print("[GESTOS][ERRO] Detector não inicializado. Impossível iniciar a visão.")
            return
        self.running = True
        self.debug_mode = debug
        self.thread = threading.Thread(target=self._vision_loop, daemon=True)
        self.thread.start()

    def stop_vision(self):
        self.running = False
        self.debug_mode = False
        # Dá um tempo para a thread terminar
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        
        if self.cap and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()

    def _vision_loop(self):
        # Lógica de fallback para abertura da câmera
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print("[GESTOS][AVISO] Backend CAP_DSHOW falhou. Tentando modo padrão...")
            self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            print("[GESTOS][ERRO] Não foi possível acessar a câmera com nenhum backend.")
            self.running = False
            # Opcional: Notificar o usuário via TTS
            io = self.core_context.get("io_handler")
            if io: io.falar("Erro crítico: não consegui acessar sua câmera.")
            return
        
        frame_timestamp_ms = 0
        while self.running and self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                time.sleep(0.1)
                continue

            # Processamento MediaPipe com a nova API
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            frame_timestamp_ms = int(time.time() * 1000)
            self.detector.detect_async(mp_image, frame_timestamp_ms)
            
            gesto_detectado = "NADA"

            if self.detection_result and self.detection_result.hand_landmarks:
                # Usa apenas a primeira mão detectada
                hand_landmarks = self.detection_result.hand_landmarks[0]
                dedos = self._contar_dedos(hand_landmarks)
                gesto_detectado = self._classificar_gesto(dedos, hand_landmarks)

                # A nova lógica de máquina de estados para gestos
                self._handle_gesture_logic(gesto_detectado, hand_landmarks)
                
                if self.debug_mode:
                    frame = self._draw_landmarks_on_image(frame, self.detection_result)
            else:
                # Se nenhuma mão for detectada, reseta o estado de rastreamento
                self._reset_tracking_state()
            
            # Se o gesto mudou, executa a ação no Core (REMOVIDO - agora dentro de _handle_gesture_logic)
            # if gesto_detectado != self.ultimo_gesto:
            #     if gesto_detectado != "DESCONHECIDO" and gesto_detectado != "NADA":
            #         self._executar_acao(gesto_detectado)
            #     self.ultimo_gesto = gesto_detectado

            if self.debug_mode:
                cv2.putText(frame, f"Gesto: {self.ultimo_gesto}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow("Aeon Vision Test", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop_vision()
                    break

            time.sleep(0.02) # Reduzido para melhor responsividade

        if self.cap:
            self.cap.release()
        if self.debug_mode:
            cv2.destroyAllWindows()

    def _draw_landmarks_on_image(self, bgr_image, detection_result):
        """Desenha os landmarks e conectores na imagem BGR usando OpenCV."""
        if detection_result is None or not detection_result.hand_landmarks:
            return bgr_image

        annotated_image = np.copy(bgr_image)
        h, w, _ = annotated_image.shape

        for hand_landmarks in detection_result.hand_landmarks:
            # Desenha os pontos (landmarks)
            for landmark in hand_landmarks:
                px, py = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(annotated_image, (px, py), 5, (0, 255, 0), -1)

            # Desenha as linhas (conexoes)
            for connection in HAND_CONNECTIONS:
                start_idx = connection[0]
                end_idx = connection[1]
                if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                    start_landmark = hand_landmarks[start_idx]
                    end_landmark = hand_landmarks[end_idx]
                    start_point = (int(start_landmark.x * w), int(start_landmark.y * h))
                    end_point = (int(end_landmark.x * w), int(end_landmark.y * h))
                    cv2.line(annotated_image, start_point, end_point, (255, 0, 0), 2)
                    
        return annotated_image

    def _contar_dedos(self, hand_landmarks):
        """Lógica de detecção de dedos."""
        dedos = []
        # hand_landmarks já é a lista de landmarks de uma mão
        
        # Polegar: Lógica proporcional à distância entre o pulso (0) e a base do dedo médio (9)
        dist_referencia = math.hypot(hand_landmarks[0].x - hand_landmarks[9].x, hand_landmarks[0].y - hand_landmarks[9].y)
        dist_polegar = math.hypot(hand_landmarks[4].x - hand_landmarks[17].x, hand_landmarks[4].y - hand_landmarks[17].y)

        if dist_polegar > dist_referencia * 0.6:
            dedos.append(True)
        else:
            dedos.append(False)

        # Outros 4 dedos
        pontas = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        for ponta, pip in zip(pontas, pips):
            if hand_landmarks[ponta].y < hand_landmarks[pip].y:
                dedos.append(True)
            else:
                dedos.append(False)
        return dedos

    def _classificar_gesto(self, dedos, hand_landmarks):
        """
        Classificação de gestos.
        AGARRAR (mão fechada de lado) agora é um gesto direto.
        """
        # Mão Fechada
        if sum(dedos) == 0:
            # Verifica se está de lado (AGARRAR)
            # Compara a distância horizontal (x) com a vertical (y) entre a base do indicador e do mindinho
            dist_x = abs(hand_landmarks[5].x - hand_landmarks[17].x)
            dist_y = abs(hand_landmarks[5].y - hand_landmarks[17].y)
            # Se a distância horizontal for muito menor que a vertical, está de lado
            if dist_x < dist_y * 0.5:
                return "AGARRAR"
            else:
                return "FECHA"

        if sum(dedos) >= 4:
            return "ABRE"
        # Xiu: Indicador levantado, outros abaixados (exceto polegar que pode variar)
        if dedos[1] and not dedos[2] and not dedos[3] and not dedos[4]:
             return "XIU"
        # Gesto de Vitoria/Paz (Indicador e Medio levantados)
        if dedos[1] and dedos[2] and not dedos[0] and not dedos[3] and not dedos[4]:
            return "VITORIA"
        # Gesto para Sair (I Love You sign: polegar, indicador e mindinho)
        if dedos[0] and dedos[1] and dedos[4] and not dedos[2] and not dedos[3]:
            return "SAIR"
        return "DESCONHECIDO"

    def _reset_tracking_state(self):
        """Reseta o estado de rastreamento de gestos compostos."""
        self.tracking_gesture = None
        self.tracking_start_pos = None
        self.tracking_start_time = None
        # self.ultimo_gesto = "NADA" # Não resetar o último gesto aqui para o debounce funcionar corretamente
        # Reseta o debounce também
        self.debounce_gesture = None
        self.debounce_start_time = None

    def _handle_gesture_logic(self, gesto, landmarks):
        """
        Máquina de estados simplificada para identificar gestos compostos
        e passar a ação para _executar_acao.
        """
        # Se estiver em cooldown de ação, ignora tudo para evitar acionamentos múltiplos
        if time.time() < self.action_cooldown_end_time:
            # Mantém o estado de rastreamento resetado durante o cooldown
            self._reset_tracking_state()
            return

        # Constantes
        DRAG_THRESHOLD_X = 0.2
        TRACKING_TIMEOUT = 1.0

        # --- Estado: Não rastreando ---
        if self.tracking_gesture is None:
            # Lógica de Debounce para gestos
            if gesto != self.debounce_gesture:
                self.debounce_gesture = gesto
                self.debounce_start_time = time.time()
            
            # Inicia rastreamento para gestos que podem ser compostos (apenas FECHA)
            if gesto == "FECHA":
                self.tracking_gesture = "FECHA_TRACKING"
                self.tracking_start_pos = (landmarks[0].x, landmarks[0].y)
                self.tracking_start_time = time.time()
                return

            # Processa gestos simples após o debounce
            if time.time() - self.debounce_start_time > self.DEBOUNCE_TIME:
                if self.debounce_gesture != self.ultimo_gesto:
                    # Gestos que iniciam rastreamento são ignorados aqui
                    if self.debounce_gesture not in ["DESCONHECIDO", "NADA", "FECHA"]:
                        self._executar_acao(self.debounce_gesture)
                    self.ultimo_gesto = self.debounce_gesture

        # --- Estado: Rastreando após um 'FECHA' ---
        elif self.tracking_gesture == "FECHA_TRACKING":
            # Se ficar segurando a mão fechada por muito tempo, executa a ação padrão de 'FECHA'
            if time.time() - self.tracking_start_time > TRACKING_TIMEOUT:
                self._executar_acao("FECHA")
                self._reset_tracking_state()
                return

            # Se abrir a mão, é um gesto composto
            if gesto == "ABRE":
                self._executar_acao("ABRIR_PAINEL")
                self._reset_tracking_state()
            # Se continuar com a mão fechada e arrastar para o lado
            elif gesto == "FECHA":
                delta_x = landmarks[0].x - self.tracking_start_pos[0]
                if abs(delta_x) > DRAG_THRESHOLD_X:
                    self._executar_acao("MODO_INVISIVEL")
                    self._reset_tracking_state()
            # Se o gesto mudar para qualquer outra coisa, cancela o rastreamento
            elif gesto != "FECHA":
                self._reset_tracking_state()


    def _executar_acao(self, gesto):
        """Conecta os gestos às funções reais da GUI (AeonSphere) de forma segura para threads."""
        io = self.core_context.get("io_handler")
        gui = self.core_context.get("gui")

        print(f"[GESTOS] Gesto '{gesto}' detectado, executando ação.")
        # Ativa o cooldown para não processar outro gesto logo em seguida
        self.action_cooldown_end_time = time.time() + self.ACTION_COOLDOWN_PERIOD

        # Ação que não depende da GUI
        if gesto == "ABRIR_PAINEL":
            print("[GESTOS] Gesto 'FECHA-ABRE' recebido! Abrindo caixa de texto.")
            if io: io.falar("Abrindo o painel.")
            pyautogui.hotkey('ctrl', 'shift', 'a')
            return

        if not gui or not hasattr(gui, 'after'):
            print("[GESTOS][ERRO] A interface gráfica (GUI) não está disponível ou não suporta 'after'.")
            return

        # Ações que dependem da GUI (agora usando 'after' para segurança de thread)
        if gesto == "XIU":
            if io: io.calar_boca()
        
        elif gesto == "AGARRAR":
            if hasattr(gui, 'set_click_through'):
                if io: io.falar("Modo de reposicionamento.")
                gui.after(0, gui.set_click_through, False)

        elif gesto == "VITORIA":
            if hasattr(gui, 'process_command'):
                 if io: io.falar("Modo visível.")
                 gui.after(0, gui.process_command, "modo visível")

        elif gesto == "FECHA":
            if hasattr(gui, 'go_to_sleep'):
                gui.after(0, gui.go_to_sleep)

        elif gesto == "ABRE":
            if hasattr(gui, 'wake_up'):
                gui.after(0, gui.wake_up)

        elif gesto == "SAIR":
            if hasattr(gui, 'quit_app'):
                print("[GESTOS] Gesto de SAIR recebido! Encerrando...")
                if io: io.falar("Encerrando.")
                gui.after(0, gui.quit_app)
            else:
                os._exit(0)

        elif gesto == "MODO_INVISIVEL":
            if hasattr(gui, 'process_command'):
                if io: io.falar("Ativando modo invisível.")
                gui.after(0, gui.process_command, "modo invisível")


    def on_unload(self) -> bool:
        self.stop_vision()
        if self.detector:
            self.detector.close()
        return True


    def on_unload(self) -> bool:
        self.stop_vision()
        if self.detector:
            self.detector.close()
        return True
