from __future__ import annotations

import math
from datetime import timedelta


class TaskMetrics:
    """Agrega as durações de uma tarefa específica e calcula estatísticas.

    Cada instância corresponde a uma zona — o MetricsCalculator mantém
    uma por cada ROI definida.

    Só recebe durações de tarefas was_forced=False — a filtragem é
    responsabilidade do MetricsCalculator, não desta classe.
    """

    def __init__(self) -> None:
        self._durations: list[timedelta] = []

    def add(self, duration: timedelta) -> None:
        """Regista uma nova duração observada."""
        self._durations.append(duration)

    def count(self) -> int:
        """Número de ocorrências registadas para esta zona."""
        return len(self._durations)

    def minimum(self) -> timedelta:
        """Duração mínima observada. Requer count() > 0."""
        return min(self._durations)

    def maximum(self) -> timedelta:
        """Duração máxima observada. Requer count() > 0."""
        return max(self._durations)

    def average(self) -> timedelta:
        """Média aritmética das durações. Requer count() > 0."""
        total = sum((d.total_seconds() for d in self._durations), 0.0)
        return timedelta(seconds=total / self.count())

    def std_deviation(self) -> timedelta:
        """Desvio padrão das durações. Devolve timedelta(0) se count() < 2."""
        if self.count() < 2:
            return timedelta(0)

        mean = self.average().total_seconds()
        variance = sum((d.total_seconds() - mean) ** 2 for d in self._durations) / self.count()
        return timedelta(seconds=math.sqrt(variance))
