# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSO: Câmara
#
# O que faz : captura frames da câmara e envia-os para o detector
# Recebe    : nada (é o primeiro bloco da pipeline)
# Envia     : frame  →  frame_queue
#             (numpy array em formato RGB, pronto para o MediaPipe)
#
# Porquê RGB?
#   O OpenCV captura sempre em BGR. O MediaPipe espera RGB.
#   Converter aqui, uma vez, mantém o detector limpo.
#
# Porquê descartar frames quando a queue está cheia?
#   Se o detector for mais lento que a câmara, a queue encheria com
#   frames antigos. O utilizador veria o que aconteceu há segundos.
#   Ao descartar, o detector processa sempre o frame mais recente.
# ═══════════════════════════════════════════════════════════════════════════════


def run(frame_queue, stop_event, config):
    import cv2

    from src.video.camera import Camera

    camera = Camera(
        index=config["camera"]["index"],
        width=config["camera"]["width"],
        height=config["camera"]["height"],
    )

    try:
        while not stop_event.is_set():
            frame = camera.read_frame()

            if frame is None:
                stop_event.set()
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.flip(frame_rgb,1)

            # Descarta o frame mais antigo se a queue estiver cheia
            if frame_queue.full():
                try:
                    frame_queue.get_nowait()
                except Exception:
                    pass

            frame_queue.put(frame_rgb)
    finally:
        camera.release()
