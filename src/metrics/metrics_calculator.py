from __future__ import annotations

from datetime import datetime, timedelta

from src.metrics.cycle_metrics import CycleMetrics
from src.metrics.task_metrics import TaskMetrics
from src.output.metrics_snapshot import MetricsSnapshot
from src.tracking.cycle_result import CycleResult
from src.tracking.task_event import TaskEvent


class MetricsCalculator:
    """Agrega eventos em métricas online à medida que chegam do pipeline.

    A separação produtivo/interrupção é feita aqui com base em was_forced:
      - False → tarefa concluída normalmente → tempo produtivo
      - True  → tarefa fechada por timeout   → tempo de interrupção

    O tempo de transição não é medido diretamente — é o que sobra:
    sessão total − produtivo − interrupção. Pode incluir tempo entre zonas,
    hesitações do operador, ou qualquer período sem mão detetada.
    """

    def __init__(self, session_start: datetime, zone_names: list[str]) -> None:
        raise NotImplementedError

    def record(self, event: TaskEvent) -> None:
        raise NotImplementedError

    def record_cycle(self, cycle_result: CycleResult) -> None:
        """Regista as métricas de um ciclo completo (duração e se a sequência foi respeitada).

        Chamado pelo _MonitorSession sempre que o CycleTracker fecha um ciclo.
        """
        raise NotImplementedError

    def snapshot(self) -> MetricsSnapshot:
        raise NotImplementedError

    def _transition_time(self, session_duration: timedelta) -> timedelta:
        raise NotImplementedError

    def _percentages(self, session_duration: timedelta) -> tuple[float, float, float]:
        """Devolve (produtivo%, transição%, interrupção%) garantindo soma de 100%."""
        raise NotImplementedError

    def _bottleneck_zone(self) -> str | None:
        """Zona com maior tempo médio de tarefa — None se ainda não há dados."""
        raise NotImplementedError
