from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class CycleResult:
    """Resultado de um ciclo completo de montagem.

    Produzido pelo CycleTracker quando a zona de saída é confirmada.
    Transporta a duração, o número do ciclo, se a ordem foi respeitada
    e a sequência real de zonas visitadas — útil para debug e métricas.
    """

    duration:        timedelta
    cycle_number:    int
    order_ok:        bool
    actual_sequence: list[str]
