from __future__ import annotations

import math
from datetime import timedelta


class CycleMetrics:
    """Agrega os tempos de ciclos completos e calcula estatísticas.

    Separado de TaskMetrics por SRP — um ciclo engloba múltiplas tarefas
    e tempos de transição, tendo semântica distinta de uma tarefa individual.
    """

    def __init__(self) -> None:
        self._durations:     list[timedelta] = []
        self._in_order_count: int            = 0

    def add(self, duration: timedelta, order_ok: bool) -> None:
        """Regista a duração de um ciclo completo e se a ordem foi respeitada."""
        self._durations.append(duration)
        if order_ok:
            self._in_order_count += 1

    def count_in_order(self) -> int:
        """Ciclos que respeitaram a ordem definida em cycle_zone_order."""
        return self._in_order_count

    def count_out_of_order(self) -> int:
        """Ciclos com zonas visitadas fora da ordem esperada."""
        return self.count() - self._in_order_count

    def count(self) -> int:
        """Total de ciclos completos registados."""
        return len(self._durations)

    def minimum(self) -> timedelta:
        """Duração do ciclo mais rápido. Requer count() > 0."""
        return min(self._durations)

    def maximum(self) -> timedelta:
        """Duração do ciclo mais lento. Requer count() > 0."""
        return max(self._durations)

    def average(self) -> timedelta:
        """Tempo médio de ciclo. Requer count() > 0."""
        total = sum((d.total_seconds() for d in self._durations), 0.0)
        return timedelta(seconds=total / self.count())

    def std_deviation(self) -> timedelta:
        """Desvio padrão dos tempos de ciclo. Devolve timedelta(0) se count() < 2."""
        if self.count() < 2:
            return timedelta(0)

        mean = self.average().total_seconds()
        variance = sum((d.total_seconds() - mean) ** 2 for d in self._durations) / self.count()
        return timedelta(seconds=math.sqrt(variance))
