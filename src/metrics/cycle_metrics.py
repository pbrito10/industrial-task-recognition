from __future__ import annotations

from datetime import timedelta

from src.metrics._duration_metrics import _DurationMetrics


class CycleMetrics(_DurationMetrics):
    """Agrega os tempos de ciclos completos e calcula estatísticas.

    Separado de TaskMetrics por SRP — um ciclo engloba múltiplas tarefas
    e tempos de transição, tendo semântica distinta de uma tarefa individual.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    def add(self, duration: timedelta, sequence_in_order: bool) -> None:
        """Regista a duração de um ciclo completo e se a sequência de zonas foi respeitada."""
        raise NotImplementedError

    def count_in_order(self) -> int:
        """Ciclos em que as zonas foram visitadas na ordem definida em cycle_zone_order."""
        raise NotImplementedError

    def count_out_of_order(self) -> int:
        """Ciclos com zonas visitadas fora da ordem esperada."""
        raise NotImplementedError
