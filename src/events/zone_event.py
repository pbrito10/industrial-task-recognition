from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from src.shared.confidence import Confidence
from src.shared.event_type import EventType
from src.shared.hand_side import HandSide
from src.shared.point import Point


@dataclass(frozen=True)
class ZoneEvent:
    """Value object que representa um evento de entrada ou saída de uma zona.

    É o átomo de informação do sistema — cada transição detetada
    (mão entra, mão sai, timeout) origina um ZoneEvent.

    was_forced=True num EXIT indica que a saída foi forçada por timeout,
    não física. Para eventos ENTER é sempre False.
    """

    timestamp:     datetime
    relative_time: timedelta
    event_type:    EventType
    zone:          str
    hand:          HandSide
    position:      Point
    confidence:    Confidence
    frame_idx:     int
    was_forced:    bool
