# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSO: Detector de mãos (MediaPipe)
#
# O que faz : deteta mãos em cada frame e envia o resultado para o próximo bloco
# Recebe    : frame          ←  frame_queue      (numpy array RGB)
# Envia     : (frame, mãos)  →  detection_queue
#             onde "mãos" é uma lista de HandDetection
#
# Porquê enviar o frame junto com as deteções?
#   O bloco seguinte (display ou pipeline) precisa do frame para desenhar.
#   Agrupá-los aqui garante que frame e deteções são sempre do mesmo instante.
#
# Porquê timeout=0.1 no queue.get()?
#   Sem timeout, o get() bloquearia para sempre se a câmara parasse.
#   Com 100ms de timeout, o loop verifica o stop_event regularmente.
# ═══════════════════════════════════════════════════════════════════════════════


def run(frame_queue, detection_queue, stop_event, config):
    from src.detection.mediapipe_detector import MediapipeDetector

    detector = MediapipeDetector(
        model_path=config["detection"]["model_path"],
        max_num_hands=config["detection"]["max_num_hands"],
        min_detection_confidence=config["detection"]["min_detection_confidence"],
        min_tracking_confidence=config["detection"]["min_tracking_confidence"],
    )

    try:
        while not stop_event.is_set():
            try:
                frame = frame_queue.get(timeout=0.1)
            except Exception:
                continue

            maos = detector.detect(frame)
            detection_queue.put((frame, maos))
    finally:
        detector.release()
