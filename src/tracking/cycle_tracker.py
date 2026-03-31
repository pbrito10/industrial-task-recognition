from __future__ import annotations

from datetime import timedelta

from src.tracking.task_event import TaskEvent


class CycleTracker:
    """Deteta ciclos completos de montagem a partir dos TaskEvents.

    Um ciclo fecha quando a zona de saída é concluída (was_forced=False).
    A duração é medida desde o início da primeira tarefa do ciclo até ao
    fim da tarefa de saída.

    Tarefas was_forced=True são acumuladas no ciclo mas não o fecham —
    uma interrupção não equivale a uma saída real.
    """

    def __init__(self, exit_zone: str) -> None:
        self._exit_zone:         str            = exit_zone
        self._tasks_in_cycle:    list[TaskEvent] = []
        self._completed_cycles:  int            = 0

    def record(self, event: TaskEvent) -> timedelta | None:
        """Regista um TaskEvent. Devolve a duração do ciclo se este ficou completo."""
        self._tasks_in_cycle.append(event)

        if self._is_cycle_complete(event):
            return self._close_cycle()

        return None

    def current_cycle_number(self) -> int:
        """Número do ciclo em curso (começa em 1)."""
        return self._completed_cycles + 1

    def _is_cycle_complete(self, event: TaskEvent) -> bool:
        """Ciclo completo: saída real (não forçada) da zona de saída."""
        return event.zone_name == self._exit_zone and not event.was_forced

    def _close_cycle(self) -> timedelta:
        """Calcula a duração do ciclo e reinicia o acumulador."""
        duration = self._tasks_in_cycle[-1].end_time - self._tasks_in_cycle[0].start_time
        self._tasks_in_cycle    = []
        self._completed_cycles += 1
        return duration
