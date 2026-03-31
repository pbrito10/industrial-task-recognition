from __future__ import annotations

from datetime import datetime, timedelta

from src.metrics.cycle_metrics import CycleMetrics
from src.metrics.task_metrics import TaskMetrics
from src.output.metrics_snapshot import MetricsSnapshot
from src.tracking.task_event import TaskEvent


class MetricsCalculator:
    """Agrega TaskEvents em métricas online — atualiza a cada evento recebido.

    Separa automaticamente was_forced=True (interrupções) de was_forced=False
    (tarefas reais). O chamador não precisa de filtrar antes de chamar record().

    snapshot() pode ser chamado a qualquer momento — devolve o estado atual
    sem modificar o calculador.
    """

    def __init__(self, session_start: datetime, zone_names: list[str]) -> None:
        self._session_start = session_start

        # Uma instância de TaskMetrics por zona — só tarefas was_forced=False
        self._task_metrics: dict[str, TaskMetrics] = {
            name: TaskMetrics() for name in zone_names
        }
        self._cycle_metrics    = CycleMetrics()
        self._productive_time  = timedelta(0)
        self._interruption_time = timedelta(0)

    def record(self, event: TaskEvent) -> None:
        """Regista um TaskEvent e atualiza as métricas internas."""
        if event.was_forced:
            self._interruption_time += event.duration
            return

        self._productive_time += event.duration

        # Cria entrada para zonas não previstas inicialmente (robustez)
        if event.zone_name not in self._task_metrics:
            self._task_metrics[event.zone_name] = TaskMetrics()

        self._task_metrics[event.zone_name].add(event.duration)

    def record_cycle(self, duration: timedelta) -> None:
        """Regista a duração de um ciclo completo (chamado pelo CycleTracker)."""
        self._cycle_metrics.add(duration)

    def snapshot(self) -> MetricsSnapshot:
        """Devolve um snapshot imutável do estado atual das métricas."""
        now             = datetime.now()
        session_duration = now - self._session_start
        transition_time = self._transition_time(session_duration)
        percentages     = self._percentages(session_duration)

        return MetricsSnapshot(
            task_metrics=dict(self._task_metrics),
            cycle_metrics=self._cycle_metrics,
            productive_time=self._productive_time,
            transition_time=transition_time,
            interruption_time=self._interruption_time,
            productive_percentage=percentages[0],
            transition_percentage=percentages[1],
            interruption_percentage=percentages[2],
            bottleneck_zone=self._bottleneck_zone(),
            session_duration=session_duration,
            captured_at=now,
        )

    def _transition_time(self, session_duration: timedelta) -> timedelta:
        """Tempo em que a mão não estava em nenhuma zona ativa."""
        transition = session_duration - self._productive_time - self._interruption_time

        # Garante que não fica negativo por variações de timing
        return max(transition, timedelta(0))

    def _percentages(self, session_duration: timedelta) -> tuple[float, float, float]:
        """Devolve (produtivo%, transição%, interrupção%) — somam 100%."""
        total_seconds = session_duration.total_seconds()
        if total_seconds == 0:
            return 0.0, 0.0, 0.0

        productive   = self._productive_time.total_seconds()   / total_seconds * 100
        interruption = self._interruption_time.total_seconds() / total_seconds * 100
        transition   = max(0.0, 100.0 - productive - interruption)
        return productive, transition, interruption

    def _bottleneck_zone(self) -> str | None:
        """Zona com maior tempo médio — None se ainda não há dados."""
        zones_with_data = [
            (name, metrics)
            for name, metrics in self._task_metrics.items()
            if metrics.count() > 0
        ]

        if not zones_with_data:
            return None

        return max(zones_with_data, key=lambda pair: pair[1].average().total_seconds())[0]
