import cv2
import mediapipe as mp
import numpy as np
import time

# Usa a nova API de Tasks do MediaPipe
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Variaveis Globais
DETECTION_RESULT = None
MODEL_PATH = 'hand_landmarker.task'

# Conexoes dos landmarks da mao para desenhar as linhas
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),         # Polegar
    (0, 5), (5, 6), (6, 7), (7, 8),         # Indicador
    (5, 9), (9, 10), (10, 11), (11, 12),     # Medio
    (9, 13), (13, 14), (14, 15), (15, 16),   # Anelar
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Mindinho e palma
]


print("1. Iniciando script de teste...")
try:
    print(f"2. Carregando modelo de gestos de '{MODEL_PATH}'...")
    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    
    def result_callback(result: vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
        global DETECTION_RESULT
        DETECTION_RESULT = result

    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.LIVE_STREAM,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        result_callback=result_callback
    )
    
    detector = vision.HandLandmarker.create_from_options(options)
    print("3. Motor de Gestos (MediaPipe Task API) inicializado com sucesso.")

except Exception as e:
    print(f"ERRO: Falha ao inicializar MediaPipe Task API: {e}")
    print("O arquivo 'hand_landmarker.task' foi baixado? Ele deve estar neste diretorio.")
    exit()


def draw_landmarks_on_image(bgr_image, detection_result):
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


def test_camera():
    print("\n=== INICIANDO TESTE DE HARDWARE ===")
    
    print("4. Tentando abrir a camera (Index 0)...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 
    
    if not cap.isOpened():
        print("Aviso: CAP_DSHOW falhou, tentando modo padrao...")
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("\n[ERRO CRITICO] Nao foi possivel acessar nenhuma camera.")
        return

    print("5. SUCESSO: Camera aberta! Criando janela de video...")
    print("Pressione 'Q' na janela de video para fechar.")
    
    frame_timestamp_ms = 0
    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Erro ao ler frame.")
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            frame_timestamp_ms = int(time.time() * 1000)
            detector.detect_async(mp_image, frame_timestamp_ms)

            annotated_image = draw_landmarks_on_image(frame, DETECTION_RESULT)
            
            if DETECTION_RESULT and DETECTION_RESULT.hand_landmarks:
                 cv2.putText(annotated_image, "MAO DETECTADA!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow("Teste de Visao Aeon (Nova API)", annotated_image)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as e:
        print(f"Erro durante o loop de video: {e}")

    detector.close()
    cap.release()
    cv2.destroyAllWindows()
    print("6. Teste encerrado corretamente.")

if __name__ == "__main__":
    test_camera()