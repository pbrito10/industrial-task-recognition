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
        self._in_order_count: int = 0
        self._anomaly_count:  int = 0

    def add(self, duration: timedelta, sequence_in_order: bool | None, is_anomaly: bool = False) -> None:
        """Regista a duração de um ciclo completo, a classificação e se é anomalia.

        sequence_in_order=True  → em ordem
        sequence_in_order=None  → provavelmente completo (ordem não determinável)
        is_anomaly=True         → anomalia (sequência incompleta + duração suspeita)
        """
        self._add_duration(duration)
        if sequence_in_order is True:
            self._in_order_count += 1
        if is_anomaly:
            self._anomaly_count += 1

    def count_in_order(self) -> int:
        """Ciclos com sequência completa e em ordem."""
        return self._in_order_count

    def count_probably_complete(self) -> int:
        """Ciclos com sequência incompleta mas duração dentro do intervalo histórico."""
        return self.count() - self._in_order_count - self._anomaly_count

    def count_anomalies(self) -> int:
        """Ciclos com sequência incompleta e duração fora do intervalo histórico."""
        return self._anomaly_count
