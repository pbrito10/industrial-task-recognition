# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSO: Monitor principal
#
# O que faz : classifica zonas, atualiza a state machine, calcula métricas
#             e mostra o feed com ROIs e keypoints
# Recebe    : (frame, mãos)  ←  detection_queue
# Envia     : nada (é o último bloco neste modo)
#
# Usado em  : Correr Programa
#             capture_process → detection_process → [monitor_process]
#
# No final da sessão (q ou Ctrl+C): exporta Excel e atualiza dashboard.
# ═══════════════════════════════════════════════════════════════════════════════


def run(detection_queue, stop_event, config, roi_path):
    import queue
    from datetime import datetime, timedelta
    from pathlib import Path

    import cv2

    from src.events.event_logger import EventLogger
    from src.events.zone_event import ZoneEvent
    from src.metrics.metrics_calculator import MetricsCalculator
    from src.output.dashboard_writer import DashboardWriter
    from src.output.excel_exporter import ExcelExporter
    from src.roi.json_roi_repository import JsonRoiRepository
    from src.shared.event_type import EventType
    from src.tracking.activation_strategy import StillnessDwellStrategy
    from src.tracking.cycle_tracker import CycleTracker
    from src.tracking.task_state_machine import (
        OneHandStateMachine, TaskStateMachine, TwoHandsStateMachine,
    )
    from src.tracking.zone_classifier import ZoneClassifier
    from src.video import frame_annotator

    _MonitorSession(config, roi_path).execute(detection_queue, stop_event)


class _MonitorSession:
    """Encapsula o estado e o comportamento de uma sessão de monitorização.

    Cada método tem uma responsabilidade única — a complexidade do pipeline
    fica distribuída em peças pequenas em vez de concentrada num único run().
    """

    def __init__(self, config: dict, roi_path: str) -> None:
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

        self._config        = config
        self._session_start = datetime.now()
        self._frame_idx     = 0
        self._last_dashboard_write  = datetime.min
        self._last_detection_per_zone: dict = {}

        rois                     = JsonRoiRepository(path=Path(roi_path)).load()
        self._rois               = rois
        self._zone_classifier    = ZoneClassifier(rois)

        dwell_time    = timedelta(seconds=config["tracking"]["dwell_time_seconds"])
        task_timeout  = timedelta(seconds=config["tracking"]["task_timeout_seconds"])
        strategy      = StillnessDwellStrategy(config["tracking"]["stillness_threshold_px"])
        self._refresh_interval = timedelta(seconds=config["dashboard"]["refresh_seconds"])

        self._cycle_tracker        = CycleTracker(exit_zone=config["tracking"]["exit_zone"])
        self._metrics              = MetricsCalculator(self._session_start, config["tracking"]["zones"])
        self._dashboard_writer     = DashboardWriter(Path(config["dashboard"]["data_path"]))
        self._excel_exporter       = ExcelExporter(Path(config["output"]["excel_output_dir"]), self._session_start)

        one_hand   = OneHandStateMachine(dwell_time, task_timeout, self._cycle_tracker.current_cycle_number, strategy)
        two_hands  = TwoHandsStateMachine(dwell_time, task_timeout, self._cycle_tracker.current_cycle_number, strategy)
        self._state_machine = TaskStateMachine(one_hand, two_hands, config["tracking"]["two_hands_zones"])

    def execute(self, detection_queue, stop_event) -> None:
        from pathlib import Path
        from src.events.event_logger import EventLogger

        output_dir = Path(self._config["output"]["excel_output_dir"])
        with EventLogger(output_dir, self._session_start) as event_logger:
            self._loop(detection_queue, stop_event, event_logger)

    def _loop(self, detection_queue, stop_event, event_logger) -> None:
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

                self._process_frame(frame_rgb, maos, event_logger)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    stop_event.set()
        finally:
            self._finalise()
            cv2.destroyAllWindows()

    def _process_frame(self, frame_rgb, maos, event_logger) -> None:
        from datetime import datetime
        import cv2
        from src.video import frame_annotator

        self._frame_idx += 1
        now = datetime.now()

        classified_hands = self._zone_classifier.classify(maos)
        self._update_last_detections(classified_hands)

        task_event = self._state_machine.update(classified_hands, now)
        if task_event is not None:
            self._handle_task_event(task_event, event_logger)

        self._maybe_refresh_dashboard(now)

        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        frame_annotator.draw_detections(frame_bgr, maos)
        frame_annotator.draw_rois(frame_bgr, self._rois)
        cv2.imshow("Monitor  |  q para sair", frame_bgr)

    def _update_last_detections(self, classified_hands) -> None:
        for detection, zone in classified_hands:
            if zone is not None:
                self._last_detection_per_zone[zone.name] = detection

    def _handle_task_event(self, task_event, event_logger) -> None:
        _log_zone_events(task_event, self._session_start, self._frame_idx,
                         self._last_detection_per_zone, event_logger)

        cycle_duration = self._cycle_tracker.record(task_event)
        self._metrics.record(task_event)
        self._excel_exporter.add_event(task_event)

        if cycle_duration is not None:
            self._metrics.record_cycle(cycle_duration)

    def _maybe_refresh_dashboard(self, now) -> None:
        from datetime import datetime
        if now - self._last_dashboard_write >= self._refresh_interval:
            self._dashboard_writer.write(self._metrics.snapshot())
            self._last_dashboard_write = now

    def _finalise(self) -> None:
        snapshot = self._metrics.snapshot()
        self._dashboard_writer.write(snapshot)
        self._excel_exporter.write(snapshot)


def _log_zone_events(task_event, session_start, frame_idx, last_detection_per_zone, event_logger) -> None:
    """Gera ENTER + EXIT ZoneEvents a partir de um TaskEvent para o CSV de debug.

    Usa a última deteção conhecida para preencher posição, lado e confiança.
    Não regista se não houver deteção guardada para a zona.
    """
    from src.events.zone_event import ZoneEvent
    from src.shared.event_type import EventType

    detection = last_detection_per_zone.get(task_event.zone_name)
    if detection is None:
        return

    event_logger.log(ZoneEvent(
        timestamp=task_event.start_time,
        relative_time=task_event.start_time - session_start,
        event_type=EventType.ENTER,
        zone=task_event.zone_name,
        hand=detection.hand_side,
        position=detection.bounding_box.center(),
        confidence=detection.confidence,
        frame_idx=frame_idx,
        was_forced=False,
    ))
    event_logger.log(ZoneEvent(
        timestamp=task_event.end_time,
        relative_time=task_event.end_time - session_start,
        event_type=EventType.EXIT,
        zone=task_event.zone_name,
        hand=detection.hand_side,
        position=detection.bounding_box.center(),
        confidence=detection.confidence,
        frame_idx=frame_idx,
        was_forced=task_event.was_forced,
    ))
