from __future__ import annotations

from datetime import datetime, timedelta

from src.metrics.cycle_metrics import CycleMetrics
from src.metrics.task_metrics import TaskMetrics
from src.output.metrics_snapshot import MetricsSnapshot
from src.tracking.cycle_result import CycleResult
from src.tracking.task_event import TaskEvent


class MetricsCalculator:
    """Agrega eventos em métricas online à medida que chegam do pipeline.

    Mantém três buckets de métricas por zona:
      - current_cycle   — tarefas do ciclo em curso (reseta ao fechar)
      - correct_cycles  — tarefas acumuladas de ciclos com ordem correta
      - incorrect_cycles — tarefas acumuladas de ciclos fora de ordem

    A separação produtivo/interrupção é feita aqui com base em was_forced:
      - False → tarefa concluída normalmente → tempo produtivo
      - True  → tarefa fechada por timeout   → tempo de interrupção
    """

    def __init__(self, session_start: datetime, zone_names: list[str]) -> None:
        self._session_start = session_start

        self._current_cycle:    dict[str, TaskMetrics] = {}
        self._correct_cycles:   dict[str, TaskMetrics] = {}
        self._incorrect_cycles: dict[str, TaskMetrics] = {}

        self._cycle_metrics     = CycleMetrics()
        self._productive_time   = timedelta(0)
        self._interruption_time = timedelta(0)

    def record(self, event: TaskEvent) -> None:
        if event.was_forced:
            self._interruption_time += event.duration
            return

        self._productive_time += event.duration

        if event.zone_name not in self._current_cycle:
            self._current_cycle[event.zone_name] = TaskMetrics()
        self._current_cycle[event.zone_name].add(event.duration)

    def record_cycle(self, cycle_result: CycleResult) -> None:
        self._cycle_metrics.add(cycle_result.duration, cycle_result.order_ok)

        # Move as tarefas do ciclo fechado para o bucket correto e reseta o ciclo atual
        target = self._correct_cycles if cycle_result.order_ok else self._incorrect_cycles
        for zone, metrics in self._current_cycle.items():
            if zone not in target:
                target[zone] = TaskMetrics()
            for d in metrics.durations():
                target[zone].add(d)

        self._current_cycle = {}

    def snapshot(self) -> MetricsSnapshot:
        now              = datetime.now()
        session_duration = now - self._session_start
        transition_time  = self._transition_time(session_duration)
        percentages      = self._percentages(session_duration)

        return MetricsSnapshot(
            current_cycle_metrics=dict(self._current_cycle),
            correct_cycle_metrics=dict(self._correct_cycles),
            incorrect_cycle_metrics=dict(self._incorrect_cycles),
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
        transition = session_duration - self._productive_time - self._interruption_time
        return max(transition, timedelta(0))

    def _percentages(self, session_duration: timedelta) -> tuple[float, float, float]:
        """Devolve (produtivo%, transição%, interrupção%) garantindo soma de 100%."""
        total_seconds = session_duration.total_seconds()
        if total_seconds == 0:
            return 0.0, 0.0, 0.0

        productive   = self._productive_time.total_seconds()   / total_seconds * 100
        interruption = self._interruption_time.total_seconds() / total_seconds * 100
        transition   = max(0.0, 100.0 - productive - interruption)
        return productive, transition, interruption

    def _bottleneck_zone(self) -> str | None:
        """Zona com maior tempo médio nos ciclos corretos — None se ainda não há dados."""
        zones_with_data = [
            (name, metrics)
            for name, metrics in self._correct_cycles.items()
            if metrics.count() > 0
        ]

        if not zones_with_data:
            return None

        return max(zones_with_data, key=lambda pair: pair[1].average().total_seconds())[0]
