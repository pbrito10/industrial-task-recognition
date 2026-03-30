# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSO: Pipeline principal
#
# O que faz : mostra o feed com ROIs e keypoints; futuramente classificará
#             zonas, atualizará o estado da tarefa e calculará métricas
# Recebe    : (frame, mãos)  ←  detection_queue
# Envia     : nada (é o último bloco neste modo)
#
# Usado em  : Correr Programa
#             camera → detector → [pipeline]
#
# As funções de desenho vêm do frame_annotator — não há lógica visual aqui.
# ═══════════════════════════════════════════════════════════════════════════════


def run(detection_queue, stop_event, config, roi_path):
    import cv2
    from pathlib import Path

    from src.roi.json_roi_repository import JsonRoiRepository
    from src.video import frame_annotator

    rois       = JsonRoiRepository(path=Path(roi_path)).load()
    zone_names = config["tracking"]["cycle_zone_order"]

    # TODO: inicializar ZoneClassifier, TaskStateMachine e CycleTracker

    window_name = "Pipeline  |  q para sair"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    try:
        while not stop_event.is_set():
            try:
                frame_rgb, maos = detection_queue.get(timeout=0.1)
            except Exception:
                continue

            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            frame_annotator.draw_detections(frame_bgr, maos)
            frame_annotator.draw_rois(frame_bgr, rois, zone_names)

            # TODO: classificar zonas → atualizar state machine → mostrar métricas

            cv2.imshow(window_name, frame_bgr)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                stop_event.set()
    finally:
        cv2.destroyAllWindows()
