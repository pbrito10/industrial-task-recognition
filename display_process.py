# detection_queue → janela OpenCV com esqueleto das mãos e FPS
#
# Usado apenas no modo "Testar Câmara" — não há state machine nem métricas.
# O frame chega em RGB (convertido na câmara); o imshow espera BGR.


def run(detection_queue, stop_event):
    import os
    import queue
    import time

    import cv2

    # Processos filhos arrancam sem herdar o ambiente do pai (spawn)
    if not os.environ.get("DISPLAY"):
        os.environ["DISPLAY"] = ":0"

    from src.video import frame_annotator

    window_name = "Teste de Câmara  |  q para sair"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    prev_time = time.perf_counter()

    try:
        while not stop_event.is_set():
            try:
                frame_rgb, maos = detection_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            frame_annotator.draw_detections(frame_bgr, maos)

            now     = time.perf_counter()
            elapsed = now - prev_time
            fps     = 0.0
            if elapsed > 0:
                fps = 1.0 / elapsed
            prev_time = now

            frame_annotator.draw_fps(frame_bgr, fps)
            cv2.imshow(window_name, frame_bgr)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                stop_event.set()
    finally:
        cv2.destroyAllWindows()
