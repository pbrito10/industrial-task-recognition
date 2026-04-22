from enum import Enum


class EventType(Enum):
    """Tipos de evento escritos no CSV de debug pelo DebugLogger.

    Enum em vez de strings livres — um conjunto fixo de valores deve ser
    um tipo, não magic strings duplicadas em vários ficheiros.
    """

    ZONE_ENTER     = "ZONE_ENTER"
    ZONE_EXIT      = "ZONE_EXIT"
    TASK_COMPLETE  = "TASK_COMPLETE"
    TASK_TIMEOUT   = "TASK_TIMEOUT"
    CYCLE_COMPLETE = "CYCLE_COMPLETE"
    DETECTION_GAP  = "DETECTION_GAP"
