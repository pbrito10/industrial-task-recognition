from __future__ import annotations

# Pipeline principal: classifica zonas, atualiza a state machine,
# calcula métricas e escreve outputs em tempo real.
#
# Este módulo é carregado num processo filho (spawn) — todos os imports
# ficam dentro das funções/métodos para evitar carregar dependências pesadas
# (OpenCV, MediaPipe) no processo pai sem necessidade.

_WINDOW_NAME = "Monitor  |  q para sair"


def run(detection_queue, stop_event, config, roi_path):
    _MonitorSession(config, roi_path).execute(detection_queue, stop_event)


class _ZoneTransitionTracker:
    """Deteta transições de zona frame a frame e delega o registo no DebugLogger.

    Isola o estado de zona anterior e a última deteção por zona — antes
    espalhados em _MonitorSession — separando esta responsabilidade do orquestrador.
    """

    def __init__(self, session_start) -> None:  # session_start: datetime
        self._session_start                     = session_start
        self._prev_zones: dict[str, str | None] = {}
        self._last_detection_per_zone: dict     = {}

    def track(self, classified_hands, now, frame_idx: int, debug_logger) -> None:
        """Atualiza deteções e regista transições de entrada/saída de zonas."""
        self._update_last_detections(classified_hands)
        self._log_transitions(classified_hands, now, frame_idx, debug_logger)

    def _update_last_detections(self, classified_hands) -> None:
        for detection, zone in classified_hands:
            if zone is not None:
                self._last_detection_per_zone[zone.name] = detection

    def _log_transitions(self, classified_hands, now, frame_idx, debug_logger) -> None:
        current = {}
        for detection, zone in classified_hands:
            zone_name = zone.name if zone is not None else None
            current[detection.hand_side.value] = (zone_name, detection)

        relative = now - self._session_start

        # A união dos dois conjuntos de chaves apanha entradas E saídas:
        # chaves só em prev → mão saiu; chaves só em current → mão entrou.
        for key in set(self._prev_zones) | set(current):
            self._check_transition(key, current, now, relative, frame_idx, debug_logger)

        self._prev_zones = {k: v[0] for k, v in current.items()}

    def _check_transition(self, key, current, now, relative, frame_idx, debug_logger) -> None:
        prev_zone            = self._prev_zones.get(key)
        curr_zone, detection = current.get(key, (None, None))

        if prev_zone == curr_zone:
            return

        if prev_zone is not None:
            last_det = self._last_detection_per_zone.get(prev_zone)
            if last_det is not None:
                debug_logger.log_zone_exit(now, relative, prev_zone, last_det, frame_idx)

        if curr_zone is not None and detection is not None:
            debug_logger.log_zone_enter(now, relative, curr_zone, detection, frame_idx)


class _DetectionGapTracker:
    """Deteta períodos sem deteção de mãos e regista-os no DebugLogger.

    Um gap só é registado quando as mãos reaparecem (ou no fim da sessão),
    porque só então se conhece a duração real. Gaps abaixo do threshold
    são ignorados — correspondem a falhas de deteção pontuais inevitáveis.

    Quando o gap excede o threshold, guarda também o primeiro frame sem deteção
    como JPEG — permite confirmar visualmente se a mão estava lá (falha do
    MediaPipe) ou genuinamente ausente (abandono/interrupção).
    """

    def __init__(self, threshold_s: float, session_start, output_dir, cycle_number_fn) -> None:
        from datetime import timedelta
        self._threshold        = timedelta(seconds=threshold_s)
        self._session_start    = session_start
        self._output_dir       = output_dir
        self._cycle_number_fn  = cycle_number_fn
        self._gap_start        = None  # datetime | None
        self._gap_frame        = None  # primeiro frame RGB sem deteção
        self._gaps_per_cycle:  dict[int, int] = {}  # ciclo → nº de gaps já guardados

    def update(self, has_detections: bool, now, frame_rgb, debug_logger) -> None:
        """Chama por frame. has_detections=True se pelo menos uma mão foi detetada."""
        if not has_detections:
            if self._gap_start is None:
                self._gap_start = now
                self._gap_frame = frame_rgb  # guarda o primeiro frame do gap
            return

        if self._gap_start is not None:
            self._flush(now, debug_logger)

    def flush(self, now, debug_logger) -> None:
        """Chama no fim da sessão para fechar um gap ainda em aberto."""
        if self._gap_start is not None:
            self._flush(now, debug_logger)

    def _flush(self, now, debug_logger) -> None:
        duration = now - self._gap_start
        if duration >= self._threshold:
            relative = self._gap_start - self._session_start
            debug_logger.log_detection_gap(self._gap_start, relative, duration)
            self._save_frame()
        self._gap_start = None
        self._gap_frame = None

    def _save_frame(self) -> None:
        """Guarda o primeiro frame do gap como JPEG nomeado pelo ciclo atual."""
        import cv2
        import numpy as np

        if self._gap_frame is None:
            return

        cycle = self._cycle_number_fn()
        count = self._gaps_per_cycle.get(cycle, 0) + 1
        self._gaps_per_cycle[cycle] = count

        # gap_ciclo_002.jpg  ou  gap_ciclo_002_2.jpg se houver mais do que um no mesmo ciclo
        suffix   = f"_{count}" if count > 1 else ""
        filename = self._output_dir / f"gap_ciclo_{cycle:03d}{suffix}.jpg"

        frame_bgr = cv2.cvtColor(np.asarray(self._gap_frame), cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(filename), frame_bgr)


class _MonitorSession:
    """Orquestrador da sessão de monitorização.

    Coordena os componentes do pipeline — cada componente com estado próprio
    está isolado na sua classe, e cada método trata de uma responsabilidade.
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
        from src.tracking.zone_classifier import ZoneClassifier

        self._config        = config
        self._session_start = datetime.now()
        self._frame_idx     = 0
        self._last_dashboard_write = datetime.min
        self._refresh_interval     = timedelta(seconds=config["dashboard"]["refresh_seconds"])

        rois                     = JsonRoiRepository(path=Path(roi_path)).load()
        self._rois               = rois
        self._zone_classifier    = ZoneClassifier(rois)
        self._transition_tracker = _ZoneTransitionTracker(self._session_start)

        dwell_time   = timedelta(seconds=config["tracking"]["dwell_time_seconds"])
        task_timeout = timedelta(seconds=config["tracking"]["task_timeout_seconds"])
        strategy     = StillnessDwellStrategy(config["tracking"]["stillness_threshold_px"])

        self._cycle_tracker    = CycleTracker(
            exit_zone=config["tracking"]["exit_zone"],
            expected_order=config["tracking"]["cycle_zone_order"],
        )

        self._gap_tracker = _DetectionGapTracker(
            threshold_s=config["tracking"]["detection_gap_threshold_s"],
            session_start=self._session_start,
            output_dir=Path(config["output"]["excel_output_dir"]),
            cycle_number_fn=self._cycle_tracker.current_cycle_number,
        )
        self._metrics          = MetricsCalculator(self._session_start, config["tracking"]["zones"])
        self._dashboard_writer = DashboardWriter(Path(config["dashboard"]["data_path"]))
        self._excel_exporter   = ExcelExporter(Path(config["output"]["excel_output_dir"]), self._session_start)
        self._state_machine    = self._build_state_machine(dwell_time, task_timeout, strategy)

    def _build_state_machine(self, dwell_time, task_timeout, strategy):
        """Monta as duas máquinas de estado e o orquestrador TaskStateMachine.

        Separado do __init__ para isolar a lógica de construção — os imports
        são locais porque os de __init__ não estão em scope neste método.
        """
        from src.tracking.task_state_machine import (
            OneHandStateMachine, TaskStateMachine, TwoHandsStateMachine,
        )
        one_hand  = OneHandStateMachine(dwell_time, task_timeout, self._cycle_tracker.current_cycle_number, strategy)
        two_hands = TwoHandsStateMachine(dwell_time, task_timeout, self._cycle_tracker.current_cycle_number, strategy)
        return TaskStateMachine(one_hand, two_hands, self._config["tracking"]["two_hands_zones"])

    def execute(self, detection_queue, stop_event) -> None:
        from pathlib import Path
        from src.events.debug_logger import DebugLogger

        output_dir = Path(self._config["output"]["excel_output_dir"])
        with DebugLogger(output_dir, self._session_start) as debug_logger:
            self._loop(detection_queue, stop_event, debug_logger)

    def _loop(self, detection_queue, stop_event, debug_logger) -> None:
        import queue
        import cv2

        cv2.namedWindow(_WINDOW_NAME, cv2.WINDOW_NORMAL)

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
            self._finalise(debug_logger)
            cv2.destroyAllWindows()

    def _process_frame(self, frame_rgb, maos, debug_logger) -> None:
        from datetime import datetime

        self._frame_idx += 1
        now = datetime.now()

        self._gap_tracker.update(bool(maos), now, frame_rgb, debug_logger)

        classified_hands = self._zone_classifier.classify(maos)
        self._transition_tracker.track(classified_hands, now, self._frame_idx, debug_logger)

        task_event = self._state_machine.update(classified_hands, now)
        if task_event is not None:
            self._handle_task_event(task_event, debug_logger)

        self._maybe_refresh_dashboard(now)
        self._display_frame(frame_rgb, maos)

    def _display_frame(self, frame_rgb, maos) -> None:
        import cv2
        from src.video import frame_annotator

        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        frame_annotator.draw_detections(frame_bgr, maos)
        frame_annotator.draw_rois(frame_bgr, self._rois)
        cv2.imshow(_WINDOW_NAME, frame_bgr)

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
        if now - self._last_dashboard_write >= self._refresh_interval:
            self._dashboard_writer.write(self._metrics.snapshot())
            self._last_dashboard_write = now

    def _finalise(self, debug_logger) -> None:
        from datetime import datetime
        self._gap_tracker.flush(datetime.now(), debug_logger)
        snapshot = self._metrics.snapshot()
        self._dashboard_writer.write(snapshot)
        self._excel_exporter.write(snapshot)
