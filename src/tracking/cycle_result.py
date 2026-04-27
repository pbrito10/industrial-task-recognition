from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class CycleResult:
    """Resultado de um ciclo completo de montagem.

    Produzido pelo CycleTracker quando a zona de saída é confirmada.
    Transporta timestamps, duração, número do ciclo, se a sequência foi
    respeitada e as zonas visitadas — útil para debug, métricas e exportação.
    """

    start_time:         datetime
    end_time:           datetime
    duration:           timedelta
    cycle_number:       int
    sequence_in_order:  bool         # True se todas as zonas na ordem correta; False caso contrário
    actual_sequence:    Sequence[str]  # Sequência real de zonas visitadas neste ciclo
    is_anomaly:         bool = False # True se sequência incompleta e duração fora do intervalo histórico

    def __post_init__(self) -> None:
        object.__setattr__(self, "actual_sequence", tuple(self.actual_sequence))
