from __future__ import annotations

import math
from datetime import timedelta


class CycleMetrics:
    """Agrega os tempos de ciclos completos e calcula estatísticas.

    Separado de TaskMetrics por SRP — um ciclo engloba múltiplas tarefas
    e tempos de transição, tendo semântica distinta de uma tarefa individual.
    """

    def __init__(self) -> None:
        self._durations: list[timedelta] = []

    def add(self, duration: timedelta) -> None:
        """Regista a duração de um ciclo completo."""
        self._durations.append(duration)

    def count(self) -> int:
        return len(self._durations)

    def minimum(self) -> timedelta:
        return min(self._durations)

    def maximum(self) -> timedelta:
        return max(self._durations)

    def average(self) -> timedelta:
        total = sum((d.total_seconds() for d in self._durations), 0.0)
        return timedelta(seconds=total / self.count())

    def std_deviation(self) -> timedelta:
        """Desvio padrão dos tempos de ciclo. Devolve timedelta(0) se count() < 2."""
        if self.count() < 2:
            return timedelta(0)

        mean = self.average().total_seconds()
        variance = sum((d.total_seconds() - mean) ** 2 for d in self._durations) / self.count()
        return timedelta(seconds=math.sqrt(variance))
