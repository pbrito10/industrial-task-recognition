from __future__ import annotations

from datetime import timedelta

from src.tracking.cycle_result import CycleResult
from src.tracking.task_event import TaskEvent


def _matches_order(actual: list[str], expected: list[str]) -> bool:
    """Verifica se a sequência real respeita a ordem esperada.

    Permite repetições consecutivas da mesma zona (ex: o operador vai três
    vezes às Rodas antes de avançar) mas não permite saltar zonas nem
    visitá-las fora de ordem.

    Algoritmo de ponteiro único: ptr aponta para a zona esperada atual.
    Ao encontrar a zona seguinte, avança o ptr. Qualquer outra zona falha.
    """
    if not expected:
        return True
    if not actual:
        return False

    ptr             = 0
    entered_current = False

    for zone in actual:
        if zone == expected[ptr]:
            entered_current = True
            continue
        if entered_current and ptr + 1 < len(expected) and zone == expected[ptr + 1]:
            ptr            += 1
            entered_current = True
            continue
        return False

    return entered_current and ptr == len(expected) - 1


class CycleTracker:
    """Deteta ciclos completos acumulando TaskEvents até à zona de saída.

    Um ciclo só abre quando a primeira zona de expected_order é visitada —
    eventos anteriores (ex: mãos na Montagem antes de ir à Porca) são ignorados.
    Isto evita ciclos falsos no arranque e impede que ir direto à Saída feche
    um ciclo sem ter feito nenhum trabalho.

    Um ciclo só fecha quando a zona de saída é concluída normalmente
    (was_forced=False). Timeouts acumulam-se no ciclo mas não o fecham —
    uma interrupção não é uma saída real.

    Para sequências incompletas (zonas em falta ou fora de ordem), o ciclo
    só é aceite se a duração estiver dentro do intervalo [min, max] dos ciclos
    já registados — filtra falsos positivos de "Porca → Saída direto" sem
    precisar de um valor fixo. Enquanto não há histórico, aceita sempre
    (os primeiros ciclos estabelecem a referência).

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
        self._min_recorded:     timedelta | None = None
        self._max_recorded:     timedelta | None = None
        self._reference_count:  int              = 0  # ciclos não-anómalos usados como referência

    def record(self, event: TaskEvent) -> CycleResult | None:
        """Acumula o evento. Devolve CycleResult se o ciclo ficou completo."""
        if not self._cycle_open:
            # Só abre na primeira zona esperada (e nunca em eventos forçados)
            if event.was_forced or event.zone_name != self._expected_order[0]:
                return None
            self._cycle_open = True

        self._tasks_in_cycle.append(event)

        if self._is_cycle_complete(event):
            return self._try_close_cycle(event)

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

    def _try_close_cycle(self, closing_event: TaskEvent) -> CycleResult:
        """Fecha o ciclo, marcando-o como anomalia se aplicável.

        Sequência correta e completa → fecha normalmente.
        Sequência incompleta + duração fora do intervalo histórico → anomalia.
        Sequência incompleta + sem histórico ainda → aceita (primeiros ciclos
        estabelecem a referência).
        """
        actual_sequence   = [t.zone_name for t in self._tasks_in_cycle if not t.was_forced]
        sequence_in_order = _matches_order(actual_sequence, self._expected_order)

        if sequence_in_order:
            return self._close_cycle(actual_sequence, True, False)

        # Sequência incompleta: só classifica como anomalia com >= 2 referências
        is_anomaly = False
        if self._reference_count >= 2:
            duration = closing_event.end_time - self._tasks_in_cycle[0].start_time
            if not (self._min_recorded <= duration <= self._max_recorded):
                is_anomaly = True

        return self._close_cycle(actual_sequence, False, is_anomaly)

    def _close_cycle(
        self,
        actual_sequence:   list[str],
        sequence_in_order: bool,
        is_anomaly:        bool,
    ) -> CycleResult:
        """Fecha o ciclo e atualiza o intervalo histórico (apenas ciclos não-anómalos)."""
        duration     = self._tasks_in_cycle[-1].end_time - self._tasks_in_cycle[0].start_time
        cycle_number = self._completed_cycles + 1

        # Anomalias não actualizam o intervalo nem a contagem de referência
        if not is_anomaly:
            if self._min_recorded is None or duration < self._min_recorded:
                self._min_recorded = duration
            if self._max_recorded is None or duration > self._max_recorded:
                self._max_recorded = duration
            self._reference_count += 1

        self._tasks_in_cycle    = []
        self._completed_cycles += 1
        self._cycle_open        = not bool(self._expected_order)

        return CycleResult(
            duration=duration,
            cycle_number=cycle_number,
            sequence_in_order=sequence_in_order,
            actual_sequence=actual_sequence,
            is_anomaly=is_anomaly,
        )
