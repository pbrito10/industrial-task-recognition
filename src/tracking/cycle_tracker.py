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

    O ciclo só começa quando o operador visita a zona de início — qualquer
    tarefa antes disso é descartada. Isto evita que tarefas acidentais no
    início da sessão (ex: ir a Montagem antes de ir buscar a Porca) entrem
    no ciclo e invalidem a sequência.

    Um ciclo só fecha quando a zona de saída é concluída normalmente
    (was_forced=False). Timeouts acumulam-se no ciclo mas não o fecham —
    uma interrupção não é uma saída real.

    Tarefas was_forced=True também são excluídas da validação de ordem,
    porque representam tempo de espera, não passos de montagem.
    """

    def __init__(self, start_zone: str, exit_zone: str, expected_order: list[str]) -> None:
        self._start_zone:       str             = start_zone
        self._exit_zone:        str             = exit_zone
        self._expected_order:   list[str]       = expected_order
        self._tasks_in_cycle:   list[TaskEvent] = []
        self._completed_cycles: int             = 0
        self._cycle_started:    bool            = False

    def record(self, event: TaskEvent) -> tuple[bool, CycleResult | None]:
        """Acumula o evento. Devolve (aceite, CycleResult | None).

        aceite=False → tarefa descartada (antes da zona de início).
        aceite=True  → tarefa registada; CycleResult preenchido se o ciclo fechou.
        """
        if not self._cycle_started:
            if event.zone_name == self._start_zone and not event.was_forced:
                self._cycle_started = True
            else:
                # Tarefa antes da zona de início — descarta sem registar métricas
                return False, None

        self._tasks_in_cycle.append(event)

        if self._is_cycle_complete(event):
            return True, self._close_cycle()

        return True, None

    def current_cycle_number(self) -> int:
        """Número do ciclo em curso (começa em 1)."""
        return self._completed_cycles + 1

    def next_zone(self) -> str | None:
        """Devolve a próxima zona esperada na sequência do ciclo.

        Antes do ciclo começar devolve a zona de início.
        Durante o ciclo avança o ponteiro pela ordem esperada com base nas
        tarefas já concluídas (exclui was_forced).
        Devolve None quando a sequência está completa ou indeterminada.
        """
        if not self._cycle_started:
            return self._start_zone

        expected = self._expected_order
        if not expected:
            return None

        # Replica o algoritmo de ponteiro do _matches_order para encontrar
        # a última zona concluída e inferir qual é a próxima.
        actual = [t.zone_name for t in self._tasks_in_cycle if not t.was_forced]

        ptr = 0
        for zone in actual:
            if zone == expected[ptr]:
                continue
            if ptr + 1 < len(expected) and zone == expected[ptr + 1]:
                ptr += 1
                continue
            # Sequência fora de ordem — posição indeterminada
            return None

        # ptr aponta para a última zona concluída; a seguinte é ptr+1
        if ptr + 1 < len(expected):
            return expected[ptr + 1]

        return None  # ciclo completo, aguarda próximo início

    def projection_target(self, in_progress_zone: str | None) -> str | None:
        """Zona a destacar no projetor em tempo real.

        Se o operador já está a trabalhar em 'in_progress_zone' (DWELLING ou
        TASK_IN_PROGRESS) e essa é a zona esperada, devolve a zona SEGUINTE na
        sequência — para guiar o operador para onde vai a seguir enquanto ainda
        está na zona atual.

        Se 'in_progress_zone' é None ou não é a zona esperada, comporta-se
        como next_zone() (mostra onde o operador deve ir agora).
        """
        next_z = self.next_zone()

        if in_progress_zone is None or in_progress_zone != next_z:
            return next_z

        # Operador está na zona certa. Devolve a zona que se segue a in_progress_zone.
        expected = self._expected_order

        # Ciclo ainda não começou: in_progress_zone é expected[0] (start_zone)
        if not self._cycle_started:
            return expected[1] if len(expected) > 1 else None

        # Ciclo em curso: recalcula o ptr para encontrar a posição exata
        # (necessário porque zonas como "Montagem" aparecem várias vezes)
        actual = [t.zone_name for t in self._tasks_in_cycle if not t.was_forced]

        ptr = 0
        for zone in actual:
            if zone == expected[ptr]:
                continue
            if ptr + 1 < len(expected) and zone == expected[ptr + 1]:
                ptr += 1
                continue
            return next_z  # fora de ordem — fallback

        # ptr = última concluída; ptr+1 = in_progress_zone; ptr+2 = seguinte
        next_idx = ptr + 1
        if next_idx + 1 < len(expected):
            return expected[next_idx + 1]

        return None  # in_progress_zone é a última da sequência

    def _is_cycle_complete(self, event: TaskEvent) -> bool:
        return event.zone_name == self._exit_zone and not event.was_forced

    def _close_cycle(self) -> CycleResult:
        actual_sequence = [t.zone_name for t in self._tasks_in_cycle if not t.was_forced]
        order_ok        = _matches_order(actual_sequence, self._expected_order)
        duration        = self._tasks_in_cycle[-1].end_time - self._tasks_in_cycle[0].start_time
        cycle_number    = self._completed_cycles + 1

        self._tasks_in_cycle    = []
        self._completed_cycles += 1
        self._cycle_started     = False  # aguarda nova zona de início

        return CycleResult(
            duration=duration,
            cycle_number=cycle_number,
            order_ok=order_ok,
            actual_sequence=actual_sequence,
        )
