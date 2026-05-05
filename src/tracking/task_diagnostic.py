from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


REASON_LEFT_BEFORE_VALIDATION_TIME = "SAIU_ANTES_DO_TEMPO_DE_VALIDACAO"
REASON_LEFT_BEFORE_STILLNESS = "LEFT_BEFORE_STILLNESS"
REASON_LEFT_BEFORE_SECOND_HAND = "LEFT_BEFORE_SECOND_HAND"
REASON_SECOND_HAND_TIMEOUT = "SECOND_HAND_TIMEOUT"


@dataclass(frozen=True)
class TaskDiagnostic:
    """Diagnóstico de uma tentativa de tarefa que não chegou a TASK_COMPLETE."""

    zone_name: str
    timestamp: datetime
    duration: timedelta
    cycle_number: int
    reason: str
