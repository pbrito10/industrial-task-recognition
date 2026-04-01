from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from src.metrics.cycle_metrics import CycleMetrics
from src.metrics.task_metrics import TaskMetrics


@dataclass(frozen=True)
class MetricsSnapshot:
    """Snapshot imutável de todas as métricas num dado momento.

    Transporta o estado calculado pelo MetricsCalculator para os
    consumidores (DashboardWriter, ExcelExporter) de forma tipada.

    Os três buckets de métricas por zona permitem distinguir o ciclo
    em curso, os ciclos corretos acumulados e os ciclos fora de ordem.
    """

    # Ciclo em curso — reseta quando o ciclo fecha
    current_cycle_metrics:  dict[str, TaskMetrics]

    # Acumulado de ciclos com ordem correta
    correct_cycle_metrics:  dict[str, TaskMetrics]

    # Acumulado de ciclos fora de ordem
    incorrect_cycle_metrics: dict[str, TaskMetrics]

    # Métricas de ciclos completos
    cycle_metrics: CycleMetrics

    # Decomposição do tempo da sessão
    productive_time:    timedelta
    transition_time:    timedelta
    interruption_time:  timedelta

    # Percentagens correspondentes (0.0–100.0)
    productive_percentage:    float
    transition_percentage:    float
    interruption_percentage:  float

    # Zona com maior tempo médio nos ciclos corretos; None se ainda não há dados
    bottleneck_zone: str | None

    session_duration: timedelta
    captured_at:      datetime
