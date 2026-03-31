from __future__ import annotations

from datetime import timedelta

from src.tracking.cycle_result import CycleResult
from src.tracking.task_event import TaskEvent


def _matches_order(actual: list[str], expected: list[str]) -> bool:
    """Verifica se a sequência real segue a ordem esperada.

    Regras:
      - Cada zona esperada deve ser visitada antes de avançar para a seguinte.
      - Uma zona pode ser visitada múltiplas vezes consecutivas antes de avançar
        (ex: "Zona das Rodas" visitada 3 vezes antes da zona seguinte).
      - Saltar uma zona ou ir a uma zona errada devolve False.
    """
    if not expected:
        return True
    if not actual:
        return False

    ptr             = 0
    entered_current = False  # a zona expected[ptr] foi visitada pelo menos uma vez?

    for zone in actual:
        if zone == expected[ptr]:
            entered_current = True
        elif entered_current and ptr + 1 < len(expected) and zone == expected[ptr + 1]:
            ptr            += 1
            entered_current = True
        else:
            return False

    return entered_current and ptr == len(expected) - 1


class CycleTracker:
    """Deteta ciclos completos de montagem a partir dos TaskEvents.

    Um ciclo fecha quando a zona de saída é concluída (was_forced=False).
    A duração é medida desde o início da primeira tarefa do ciclo até ao
    fim da tarefa de saída.

    Tarefas was_forced=True são acumuladas no ciclo mas não o fecham —
    uma interrupção não equivale a uma saída real — e não entram na
    verificação de ordem.
    """

    def __init__(self, exit_zone: str, expected_order: list[str]) -> None:
        self._exit_zone:        str             = exit_zone
        self._expected_order:   list[str]       = expected_order
        self._tasks_in_cycle:   list[TaskEvent] = []
        self._completed_cycles: int             = 0

    def record(self, event: TaskEvent) -> CycleResult | None:
        """Regista um TaskEvent. Devolve CycleResult se o ciclo ficou completo."""
        self._tasks_in_cycle.append(event)

        if self._is_cycle_complete(event):
            return self._close_cycle()

        return None

    def current_cycle_number(self) -> int:
        """Número do ciclo em curso (começa em 1)."""
        return self._completed_cycles + 1

    def _is_cycle_complete(self, event: TaskEvent) -> bool:
        return event.zone_name == self._exit_zone and not event.was_forced

    def _close_cycle(self) -> CycleResult:
        actual_sequence = [t.zone_name for t in self._tasks_in_cycle if not t.was_forced]
        order_ok        = _matches_order(actual_sequence, self._expected_order)
        duration        = self._tasks_in_cycle[-1].end_time - self._tasks_in_cycle[0].start_time
        cycle_number    = self._completed_cycles + 1

        self._tasks_in_cycle    = []
        self._completed_cycles += 1

        return CycleResult(
            duration=duration,
            cycle_number=cycle_number,
            order_ok=order_ok,
            actual_sequence=actual_sequence,
        )
