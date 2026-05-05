from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Mapping

from src.metrics.cycle_metrics import CycleMetrics
from src.metrics.task_metrics import TaskMetrics


@dataclass(frozen=True)
class TaskMetricSnapshot:
    """Valores congelados das métricas de uma zona num instante."""

    _count: int
    _minimum: timedelta | None = None
    _average: timedelta | None = None
    _maximum: timedelta | None = None
    _std_deviation: timedelta = timedelta(0)

    @classmethod
    def from_metrics(cls, metrics: TaskMetrics) -> TaskMetricSnapshot:
        """Cria snapshot imutável a partir das métricas vivas de uma zona."""
        if metrics.count() == 0:
            return cls(_count=0)
        return cls(
            _count=metrics.count(),
            _minimum=metrics.minimum(),
            _average=metrics.average(),
            _maximum=metrics.maximum(),
            _std_deviation=metrics.std_deviation(),
        )

    def count(self) -> int:
        """Número de tarefas registadas nesta zona."""
        return self._count

    def minimum(self) -> timedelta:
        """Menor duração registada; exige pelo menos uma ocorrência."""
        if self._minimum is None:
            raise ValueError("Sem durações registadas.")
        return self._minimum

    def average(self) -> timedelta:
        """Duração média; exige pelo menos uma ocorrência."""
        if self._average is None:
            raise ValueError("Sem durações registadas.")
        return self._average

    def maximum(self) -> timedelta:
        """Maior duração registada; exige pelo menos uma ocorrência."""
        if self._maximum is None:
            raise ValueError("Sem durações registadas.")
        return self._maximum

    def std_deviation(self) -> timedelta:
        """Desvio padrão das durações, ou zero com menos de duas ocorrências."""
        return self._std_deviation


@dataclass(frozen=True)
class CycleMetricSnapshot:
    """Valores congelados das métricas de ciclos num instante."""

    _count: int
    _minimum: timedelta | None = None
    _average: timedelta | None = None
    _maximum: timedelta | None = None
    _std_deviation: timedelta = timedelta(0)
    _correct_average: timedelta | None = None
    _count_in_order: int = 0
    _count_to_review: int = 0
    _count_probably_complete: int = 0
    _count_anomalies: int = 0
    _recent_durations: tuple[timedelta, ...] = ()

    @classmethod
    def from_metrics(cls, metrics: CycleMetrics) -> CycleMetricSnapshot:
        """Cria snapshot imutável a partir das métricas vivas de ciclos."""
        if metrics.count() == 0:
            return cls(_count=0)
        return cls(
            _count=metrics.count(),
            _minimum=metrics.minimum(),
            _average=metrics.average(),
            _maximum=metrics.maximum(),
            _std_deviation=metrics.std_deviation(),
            _correct_average=metrics.correct_average(),
            _count_in_order=metrics.count_in_order(),
            _count_to_review=metrics.count_to_review(),
            _count_probably_complete=metrics.count_probably_complete(),
            _count_anomalies=metrics.count_anomalies(),
            _recent_durations=tuple(metrics.recent_durations()),
        )

    def count(self) -> int:
        """Número de ciclos fechados."""
        return self._count

    def minimum(self) -> timedelta:
        """Menor duração de ciclo; exige pelo menos um ciclo."""
        if self._minimum is None:
            raise ValueError("Sem ciclos registados.")
        return self._minimum

    def average(self) -> timedelta:
        """Duração média de todos os ciclos; exige pelo menos um ciclo."""
        if self._average is None:
            raise ValueError("Sem ciclos registados.")
        return self._average

    def maximum(self) -> timedelta:
        """Maior duração de ciclo; exige pelo menos um ciclo."""
        if self._maximum is None:
            raise ValueError("Sem ciclos registados.")
        return self._maximum

    def std_deviation(self) -> timedelta:
        """Desvio padrão das durações de ciclo."""
        return self._std_deviation

    def correct_average(self) -> timedelta | None:
        """Média apenas dos ciclos com sequência em ordem."""
        return self._correct_average

    def count_in_order(self) -> int:
        """Número de ciclos classificados automaticamente como em ordem."""
        return self._count_in_order

    def count_to_review(self) -> int:
        """Número de ciclos que precisam de validação manual."""
        return self._count_to_review

    def count_probably_complete(self) -> int:
        """Contador antigo de ciclos fora de ordem, preservado por compatibilidade."""
        return self._count_probably_complete

    def count_anomalies(self) -> int:
        """Contador antigo de anomalias, preservado por compatibilidade."""
        return self._count_anomalies

    def recent_durations(self) -> tuple[timedelta, ...]:
        """Durações dos últimos ciclos usados pelo gráfico do dashboard."""
        return self._recent_durations


@dataclass(frozen=True)
class MetricsSnapshot:
    """Snapshot imutável de todas as métricas num dado momento.

    Transporta o estado calculado pelo MetricsCalculator para os
    consumidores (DashboardWriter, ExcelExporter) de forma tipada —
    sem dicts genéricos cujas chaves e tipos são desconhecidos.

    As três percentagens somam 100% (dentro de margem de arredondamento).
    """

    # Métricas por zona — só tarefas was_forced=False
    task_metrics: Mapping[str, TaskMetricSnapshot]

    # Métricas de ciclos completos
    cycle_metrics: CycleMetricSnapshot

    # Decomposição do tempo da sessão
    productive_time:    timedelta
    transition_time:    timedelta
    interruption_time:  timedelta

    # Percentagens correspondentes (0.0–100.0)
    productive_percentage:    float
    transition_percentage:    float
    interruption_percentage:  float

    # Zona que mais atrasa o ciclo; None se ainda não há dados suficientes
    bottleneck_zone: str | None

    session_duration: timedelta
    captured_at:      datetime

    def __post_init__(self) -> None:
        task_metrics = {
            name: _freeze_task_metric(metrics)
            for name, metrics in self.task_metrics.items()
        }
        object.__setattr__(self, "task_metrics", MappingProxyType(task_metrics))
        object.__setattr__(self, "cycle_metrics", _freeze_cycle_metric(self.cycle_metrics))


def _freeze_task_metric(metrics: TaskMetrics | TaskMetricSnapshot) -> TaskMetricSnapshot:
    if isinstance(metrics, TaskMetricSnapshot):
        return metrics
    return TaskMetricSnapshot.from_metrics(metrics)


def _freeze_cycle_metric(metrics: CycleMetrics | CycleMetricSnapshot) -> CycleMetricSnapshot:
    if isinstance(metrics, CycleMetricSnapshot):
        return metrics
    return CycleMetricSnapshot.from_metrics(metrics)
