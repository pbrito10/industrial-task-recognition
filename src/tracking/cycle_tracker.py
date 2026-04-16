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
    raise NotImplementedError


class CycleTracker:
    """Deteta ciclos completos acumulando TaskEvents até à zona de saída.

    Um ciclo só fecha quando a zona de saída é concluída normalmente
    (was_forced=False). Timeouts acumulam-se no ciclo mas não o fecham —
    uma interrupção não é uma saída real.

    Tarefas was_forced=True também são excluídas da validação de ordem,
    porque representam tempo de espera, não passos de montagem.
    """

    def __init__(self, exit_zone: str, expected_order: list[str]) -> None:
        raise NotImplementedError

    def record(self, event: TaskEvent) -> CycleResult | None:
        """Acumula o evento. Devolve CycleResult se o ciclo ficou completo."""
        raise NotImplementedError

    def current_cycle_number(self) -> int:
        """Número do ciclo em curso (começa em 1; incrementa quando um ciclo fecha).

        Usado como callback nos construtores de OneHandStateMachine e TwoHandsStateMachine:
            machine = OneHandStateMachine(..., cycle_number_fn=tracker.current_cycle_number, ...)
        Cada TaskEvent produzido pela máquina regista o número do ciclo no momento da conclusão.
        """
        raise NotImplementedError

    def _is_cycle_complete(self, event: TaskEvent) -> bool:
        raise NotImplementedError

    def _close_cycle(self) -> CycleResult:
        """Fecha o ciclo atual, valida a ordem, reinicia o acumulador e devolve o resultado."""
        raise NotImplementedError
