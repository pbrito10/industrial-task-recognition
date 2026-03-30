# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSO: Visualização (modo "Testar Câmara")
#
# O que faz : mostra o feed ao vivo com keypoints e bounding boxes das mãos
# Recebe    : (frame, mãos)  ←  detection_queue
# Envia     : nada (é o último bloco neste modo)
#
# Usado em  : Testar Câmara
#             camera → detector → [display]
#
# Porquê converter RGB→BGR antes de mostrar?
#   O frame chegou em RGB (convertido na câmara para o MediaPipe).
#   O OpenCV (imshow) espera BGR — sem esta conversão as cores ficam invertidas.
# ═══════════════════════════════════════════════════════════════════════════════


def run(detection_queue, stop_event):
    import time

    import cv2

    from src.video import frame_annotator

    window_name = "Teste de Câmara  |  q para sair"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    prev_time = time.perf_counter()

    try:
        while not stop_event.is_set():
            try:
                frame_rgb, maos = detection_queue.get(timeout=0.1)
            except Exception:
                continue

            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            frame_annotator.draw_detections(frame_bgr, maos)

            now = time.perf_counter()
            fps = 1.0 / (now - prev_time) if now != prev_time else 0.0
            prev_time = now

            frame_annotator.draw_fps(frame_bgr, fps)
            cv2.imshow(window_name, frame_bgr)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                stop_event.set()
    finally:
        cv2.destroyAllWindows()
