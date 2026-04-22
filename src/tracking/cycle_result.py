from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class CycleResult:
    """Resultado de um ciclo completo de montagem.

    Produzido pelo CycleTracker quando a zona de saída é confirmada.
    Transporta a duração, o número do ciclo, se a sequência foi respeitada
    e as zonas visitadas — útil para debug e métricas.
    """

    duration:           timedelta
    cycle_number:       int
    sequence_in_order:  bool | None  # True/False se determinável; None se anomalia (deteção falhou)
    actual_sequence:    list[str]    # Sequência real de zonas visitadas neste ciclo
    is_anomaly:         bool = False # True se sequência incompleta e duração fora do intervalo histórico
