# Pipeline principal: classifica zonas, atualiza a state machine,
# calcula métricas e escreve outputs em tempo real.
#
# Este módulo é carregado num processo filho (spawn) — todos os imports
# ficam dentro das funções para evitar carregar dependências pesadas
# (OpenCV, MediaPipe) no processo pai sem necessidade.


def run(detection_queue, stop_event, config, roi_path, workbench_path):
    _MonitorSession(config, roi_path, workbench_path).execute(detection_queue, stop_event)


class _MonitorSession:
    """Encapsula o estado de uma sessão de monitorização.

    Cada método trata de uma responsabilidade — o loop principal fica
    limpo e cada peça pode ser testada isoladamente.
    """

    def __init__(self, config: dict, roi_path: str, workbench_path: str) -> None:
        from datetime import datetime, timedelta
        from pathlib import Path

        from src.metrics.metrics_calculator import MetricsCalculator
        from src.output.dashboard_writer import DashboardWriter
        from src.output.excel_exporter import ExcelExporter
        from src.roi.json_roi_repository import JsonRoiRepository
        from src.tracking.activation_strategy import StillnessDwellStrategy
        from src.tracking.cycle_tracker import CycleTracker
        from src.tracking.task_state_machine import (
            OneHandStateMachine, TaskStateMachine, TwoHandsStateMachine,
        )
        from src.tracking.zone_classifier import ZoneClassifier
        from src.wizard.workbench_config import WorkbenchConfig

        self._config        = config
        self._session_start = datetime.now()
        self._frame_idx     = 0
        self._last_dashboard_write  = datetime.min
        self._last_detection_per_zone: dict = {}

        workbench = WorkbenchConfig.load(Path(workbench_path), Path(__file__).parent / "config" / "settings.yaml")

        rois                  = JsonRoiRepository(path=Path(roi_path)).load()
        self._rois            = rois
        self._zone_classifier = ZoneClassifier(rois)

        dwell_time    = timedelta(seconds=config["tracking"]["dwell_time_seconds"])
        task_timeout  = timedelta(seconds=config["tracking"]["task_timeout_seconds"])
        strategy      = StillnessDwellStrategy(config["tracking"]["stillness_threshold_px"])
        self._refresh_interval = timedelta(seconds=config["dashboard"]["refresh_seconds"])

        self._cycle_tracker    = CycleTracker(
            exit_zone=workbench.exit_zone,
            expected_order=workbench.cycle_zone_order,
        )
        self._metrics          = MetricsCalculator(self._session_start, workbench.zones)
        self._dashboard_writer = DashboardWriter(Path(config["dashboard"]["data_path"]))
        self._excel_exporter   = ExcelExporter(Path(config["output"]["excel_output_dir"]), self._session_start)

        self._prev_zones: dict[str, str | None] = {}

        one_hand  = OneHandStateMachine(dwell_time, task_timeout, self._cycle_tracker.current_cycle_number, strategy)
        two_hands = TwoHandsStateMachine(dwell_time, task_timeout, self._cycle_tracker.current_cycle_number, strategy)
        self._state_machine = TaskStateMachine(one_hand, two_hands, workbench.two_hands_zones)

    def execute(self, detection_queue, stop_event) -> None:
        from pathlib import Path
        from src.events.debug_logger import DebugLogger

        output_dir = Path(self._config["output"]["excel_output_dir"])
        with DebugLogger(output_dir, self._session_start) as debug_logger:
            self._loop(detection_queue, stop_event, debug_logger)

    def _loop(self, detection_queue, stop_event, debug_logger) -> None:
        import queue
        import cv2

        window_name = "Monitor  |  q para sair"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        try:
            while not stop_event.is_set():
                try:
                    frame_rgb, maos = detection_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                self._process_frame(frame_rgb, maos, debug_logger)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    stop_event.set()
        finally:
            self._finalise()
            cv2.destroyAllWindows()

    def _process_frame(self, frame_rgb, maos, debug_logger) -> None:
        from datetime import datetime
        import cv2
        from src.video import frame_annotator

        self._frame_idx += 1
        now = datetime.now()

        classified_hands = self._zone_classifier.classify(maos)
        self._update_last_detections(classified_hands)
        self._log_zone_transitions(classified_hands, now, debug_logger)

        task_event = self._state_machine.update(classified_hands, now)
        if task_event is not None:
            self._handle_task_event(task_event, debug_logger)

        self._maybe_refresh_dashboard(now)

        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        frame_annotator.draw_detections(frame_bgr, maos)
        frame_annotator.draw_rois(frame_bgr, self._rois)
        cv2.imshow("Monitor  |  q para sair", frame_bgr)

    def _update_last_detections(self, classified_hands) -> None:
        for detection, zone in classified_hands:
            if zone is not None:
                self._last_detection_per_zone[zone.name] = detection

    def _log_zone_transitions(self, classified_hands, now, debug_logger) -> None:
        # Constrói o mapa de zona atual por lado da mão
        current = {}
        for detection, zone in classified_hands:
            zone_name = None
            if zone is not None:
                zone_name = zone.name
            current[detection.hand_side.value] = (zone_name, detection)

        relative = now - self._session_start

        # A união dos dois conjuntos de chaves apanha entradas E saídas:
        # chaves só em prev → mão saiu; chaves só em current → mão entrou.
        for key in set(self._prev_zones) | set(current):
            self._check_zone_transition(key, current, now, relative, debug_logger)

        self._prev_zones = {k: v[0] for k, v in current.items()}

    def _check_zone_transition(self, key, current, now, relative, debug_logger) -> None:
        prev_zone            = self._prev_zones.get(key)
        curr_zone, detection = current.get(key, (None, None))

        if prev_zone == curr_zone:
            return

        if prev_zone is not None:
            last_det = self._last_detection_per_zone.get(prev_zone)
            if last_det is not None:
                debug_logger.log_zone_exit(now, relative, prev_zone, last_det, self._frame_idx)

        if curr_zone is not None and detection is not None:
            debug_logger.log_zone_enter(now, relative, curr_zone, detection, self._frame_idx)

    def _handle_task_event(self, task_event, debug_logger) -> None:
        self._log_task(task_event, debug_logger)

        cycle_result = self._cycle_tracker.record(task_event)
        self._metrics.record(task_event)
        self._excel_exporter.add_event(task_event)

        if cycle_result is not None:
            self._metrics.record_cycle(cycle_result)
            self._excel_exporter.add_cycle_result(cycle_result)
            debug_logger.log_cycle_complete(cycle_result)

    def _log_task(self, task_event, debug_logger) -> None:
        if task_event.was_forced:
            debug_logger.log_task_timeout(task_event)
            return
        debug_logger.log_task_complete(task_event)

    def _maybe_refresh_dashboard(self, now) -> None:
        from datetime import datetime
        if now - self._last_dashboard_write >= self._refresh_interval:
            self._dashboard_writer.write(self._metrics.snapshot())
            self._last_dashboard_write = now

    def _finalise(self) -> None:
        snapshot = self._metrics.snapshot()
        self._dashboard_writer.write(snapshot)
        self._excel_exporter.write(snapshot)
