# Processo dedicado ao projetor.
#
# Recebe o nome da zona ativa via Queue (enviado pelo monitor_process sempre
# que a próxima zona muda) e renderiza o guia em fullscreen no display do
# projetor.  O fundo é preto — o projetor só ilumina a zona que o operador
# deve visitar a seguir.
#
# Carregado como processo filho (spawn) — imports pesados ficam dentro das
# funções, igual aos outros processos do pipeline.


def run(projection_queue, stop_event, config, workbenches_dir, active_path):
    _ProjectionSession(config, workbenches_dir, active_path).execute(
        projection_queue, stop_event
    )


class _ProjectionSession:

    def __init__(self, config: dict, workbenches_dir: str, active_path: str) -> None:
        from pathlib import Path

        from src.projection import homography
        from src.projection.projector_renderer import ProjectorRenderer
        from src.roi.json_roi_repository import JsonRoiRepository
        from src.wizard.workbench_config import WorkbenchConfig

        proj_cfg    = config["projector"]
        active_name = WorkbenchConfig.active_name(Path(active_path))
        roi_path    = WorkbenchConfig.roi_path(Path(workbenches_dir), active_name)
        rois        = JsonRoiRepository(path=roi_path).load()

        cal_path = Path(proj_cfg["calibration_path"])
        H        = homography.load(cal_path)
        if H is None:
            raise RuntimeError(
                f"Homografia não encontrada em {cal_path}.\n"
                "Corre a calibração do projetor no Wizard antes de iniciar."
            )

        self._width    = proj_cfg["resolution_width"]
        self._height   = proj_cfg["resolution_height"]
        self._offset_x = proj_cfg["display_offset_x"]
        self._offset_y = proj_cfg["display_offset_y"]
        self._renderer = ProjectorRenderer(self._width, self._height, rois, H)

    def execute(self, projection_queue, stop_event) -> None:
        import queue
        import cv2

        win = "Projetor"
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cv2.moveWindow(win, self._offset_x, self._offset_y)
        cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        active_zone: str | None = None

        try:
            while not stop_event.is_set():
                # Drena a queue e fica com a atualização mais recente
                try:
                    while True:
                        active_zone = projection_queue.get_nowait()
                except queue.Empty:
                    pass

                frame = self._renderer.render(active_zone)
                cv2.imshow(win, frame)
                cv2.waitKey(33)  # ~30 fps
        finally:
            cv2.destroyWindow(win)
