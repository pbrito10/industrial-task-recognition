from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from types import TracebackType

from src.events.zone_event import ZoneEvent

_COLUMNS = [
    "timestamp_iso",
    "relative_time_s",
    "event_type",
    "zone",
    "hand",
    "x_px",
    "y_px",
    "confidence",
    "frame_idx",
    "was_forced",
]


class EventLogger:
    """Escreve ZoneEvents num CSV em tempo real, linha a linha.

    O flush imediato após cada linha garante que os dados chegam ao disco
    mesmo se o programa fechar inesperadamente — essencial para debug.

    Uso como context manager garante que o ficheiro é sempre fechado:
        with EventLogger(output_dir, session_start) as logger:
            logger.log(event)
    """

    def __init__(self, output_dir: Path, session_start: datetime) -> None:
        filename  = f"events_{session_start.strftime('%Y-%m-%d_%Hh%M')}.csv"
        self._path = output_dir / filename

        output_dir.mkdir(parents=True, exist_ok=True)
        self._file   = self._path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=_COLUMNS)
        self._writer.writeheader()
        self._file.flush()

    def log(self, event: ZoneEvent) -> None:
        """Escreve uma linha no CSV e faz flush imediato."""
        self._writer.writerow({
            "timestamp_iso":   event.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
            "relative_time_s": round(event.relative_time.total_seconds(), 3),
            "event_type":      event.event_type.value,
            "zone":            event.zone,
            "hand":            event.hand.value,
            "x_px":            event.position.x,
            "y_px":            event.position.y,
            "confidence":      round(event.confidence.value, 4),
            "frame_idx":       event.frame_idx,
            "was_forced":      "true" if event.was_forced else "false",
        })
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> EventLogger:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val:  BaseException | None,
        exc_tb:   TracebackType | None,
    ) -> None:
        self.close()
