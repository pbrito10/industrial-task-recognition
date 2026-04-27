from __future__ import annotations

from datetime import timedelta

from src.metrics._duration_metrics import _DurationMetrics


class CycleMetrics(_DurationMetrics):
    """Agrega os tempos de ciclos completos e calcula estatísticas.

    Separado de TaskMetrics por SRP — um ciclo engloba múltiplas tarefas
    e tempos de transição, tendo semântica distinta de uma tarefa individual.
    """

    def __init__(self) -> None:
        super().__init__()
        self._in_order_count:     int             = 0
        self._anomaly_count:      int             = 0
        self._correct_durations:  list[timedelta] = []

    def add(self, duration: timedelta, sequence_in_order: bool, is_anomaly: bool = False) -> None:
        """Regista a duração de um ciclo completo e o resultado automático.

        sequence_in_order=True  → sequência registada em ordem
        sequence_in_order=False → sequência incompleta ou fora de ordem, a rever manualmente
        is_anomaly=True         → reservado para compatibilidade com dados antigos
        """
        self._add_duration(duration)
        if sequence_in_order is True:
            self._in_order_count += 1
            self._correct_durations.append(duration)
        if is_anomaly:
            self._anomaly_count += 1

    def correct_average(self) -> timedelta | None:
        """Média dos ciclos corretos (sequence_in_order=True). None se não houver nenhum."""
        if not self._correct_durations:
            return None
        total = sum((d.total_seconds() for d in self._correct_durations), 0.0)
        return timedelta(seconds=total / len(self._correct_durations))

    def count_in_order(self) -> int:
        """Ciclos com sequência completa e em ordem."""
        return self._in_order_count

    def count_to_review(self) -> int:
        """Ciclos que não ficaram em ordem e precisam de validação manual."""
        return self.count() - self._in_order_count

    def count_probably_complete(self) -> int:
        """Ciclos fora da ordem esperada, a rever manualmente."""
        return self.count() - self._in_order_count - self._anomaly_count

    def count_anomalies(self) -> int:
        """Contador preservado por compatibilidade com dados antigos."""
        return self._anomaly_count
