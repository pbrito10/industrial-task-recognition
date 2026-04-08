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
    try:
        _ProjectionSession(config, workbenches_dir, active_path).execute(
            projection_queue, stop_event
        )
    except Exception as exc:
        import traceback
        print(f"[projector] ERRO: {exc}")
        traceback.print_exc()


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
        import queue as q_module
        import tkinter as tk
        import cv2
        from PIL import Image, ImageTk

        root = tk.Tk()
        try:
            # Evita que a janela roube foco ou bloqueie input nos outros monitores.
            # Nem todos os WMs suportam este atributo — o fallback é overrideredirect.
            root.wm_attributes('-type', 'splash')
        except tk.TclError:
            root.overrideredirect(True)
        root.geometry(f"{self._width}x{self._height}+{self._offset_x}+{self._offset_y}")
        root.configure(bg="black")

        label = tk.Label(root, bg="black", borderwidth=0)
        label.pack(fill="both", expand=True)

        active_zone: list[str | None] = [None]
        photo_ref:   list             = [None]   # evita garbage collection do PhotoImage

        _tick_count = [0]

        def tick() -> None:
            # Drena a queue — interessa só a última atualização
            try:
                while True:
                    active_zone[0] = projection_queue.get_nowait()
            except q_module.Empty:
                pass

            frame_bgr = self._renderer.render(active_zone[0])

            # Diagnóstico: imprime zona e brilho médio do frame a cada 90 ticks (~3s)
            _tick_count[0] += 1
            if _tick_count[0] % 90 == 1:
                brightness = int(frame_bgr.mean())
                print(f"[projector] zona={active_zone[0]}  brilho_frame={brightness}")

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            photo     = ImageTk.PhotoImage(Image.fromarray(frame_rgb))
            label.configure(image=photo)
            photo_ref[0] = photo

            if not stop_event.is_set():
                root.after(33, tick)   # ~30 fps
            else:
                root.quit()

        root.after(0, tick)
        root.mainloop()
        root.destroy()
