from __future__ import annotations

from src.tracking.cycle_result import CycleResult
from src.tracking.order_matching import matches_order
from src.tracking.task_event import TaskEvent


class CycleTracker:
    """Deteta ciclos completos acumulando TaskEvents até à zona de saída.

    Um ciclo só abre quando a primeira zona de expected_order é visitada —
    eventos anteriores (ex: mãos na Montagem antes de ir à Porca) são ignorados.
    Isto evita ciclos falsos no arranque e impede que ir direto à Saída feche
    um ciclo sem ter feito nenhum trabalho.

    Um ciclo só fecha quando a zona de saída é concluída normalmente
    (was_forced=False). Timeouts acumulam-se no ciclo mas não o fecham —
    uma interrupção não é uma saída real.

    Tarefas was_forced=True também são excluídas da validação de ordem,
    porque representam tempo de espera, não passos de montagem.
    """

    def __init__(self, exit_zone: str, expected_order: list[str]) -> None:
        self._exit_zone:        str              = exit_zone
        self._expected_order:   list[str]        = expected_order
        self._tasks_in_cycle:   list[TaskEvent]  = []
        self._completed_cycles: int              = 0
        # Sem ordem definida o ciclo abre imediatamente; caso contrário aguarda
        # a primeira zona (expected_order[0]) para garantir arranque correto.
        self._cycle_open:       bool             = not bool(expected_order)

    def record(self, event: TaskEvent) -> CycleResult | None:
        """Acumula o evento. Devolve CycleResult se o ciclo ficou completo."""
        if not self._cycle_open:
            # Só abre na primeira zona esperada (e nunca em eventos forçados)
            if event.was_forced or event.zone_name != self._expected_order[0]:
                return None
            self._cycle_open = True

        self._tasks_in_cycle.append(event)

        if self._is_cycle_complete(event):
            return self._try_close_cycle()

        return None

    def current_cycle_number(self) -> int:
        """Número do ciclo em curso (começa em 1; incrementa quando um ciclo fecha).

        Usado como callback nos construtores de OneHandStateMachine e TwoHandsStateMachine:
            machine = OneHandStateMachine(..., cycle_number_fn=tracker.current_cycle_number, ...)
        Cada TaskEvent produzido pela máquina regista o número do ciclo no momento da conclusão.
        """
        return self._completed_cycles + 1

    def _is_cycle_complete(self, event: TaskEvent) -> bool:
        return event.zone_name == self._exit_zone and not event.was_forced

    def _try_close_cycle(self) -> CycleResult:
        """Fecha o ciclo e regista se a sequência respeitou a ordem esperada."""
        actual_sequence   = [t.zone_name for t in self._tasks_in_cycle if not t.was_forced]
        sequence_in_order = matches_order(actual_sequence, self._expected_order)

        return self._close_cycle(actual_sequence, sequence_in_order)

    def _close_cycle(
        self,
        actual_sequence:   list[str],
        sequence_in_order: bool,
    ) -> CycleResult:
        """Fecha o ciclo e prepara o CycleResult."""
        duration     = self._tasks_in_cycle[-1].end_time - self._tasks_in_cycle[0].start_time
        cycle_number = self._completed_cycles + 1
        start_time   = self._tasks_in_cycle[0].start_time
        end_time     = self._tasks_in_cycle[-1].end_time

        self._tasks_in_cycle    = []
        self._completed_cycles += 1
        self._cycle_open        = not bool(self._expected_order)

        return CycleResult(
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            cycle_number=cycle_number,
            sequence_in_order=sequence_in_order,
            actual_sequence=actual_sequence,
            expected_sequence=self._expected_order,
        )
