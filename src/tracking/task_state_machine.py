from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Callable

from src.detection.hand_detection import HandDetection
from src.shared.hand_side import HandSide
from src.shared.task_state import TaskState
from src.tracking.activation_strategy import ActivationStrategy
from src.tracking.task_event import TaskEvent
from src.tracking.zone_classifier import ClassifiedHand


class StateMachineInterface(ABC):
    """Interface mínima que o orquestrador precisa de ambas as máquinas.

    state() existe porque a máquina pode regressar a IDLE sem emitir evento
    (ex: mão sai durante o dwell). O orquestrador precisa de detetar isso
    para limpar o ponteiro _active — caso contrário a próxima zona usaria
    a máquina errada.
    """

    @abstractmethod
    def update(
        self,
        classified_hands: list[ClassifiedHand],
        frame_time: datetime,
    ) -> TaskEvent | None: ...

    @abstractmethod
    def state(self) -> TaskState: ...


class _BaseStateMachine(StateMachineInterface):
    """Lógica partilhada pelas máquinas de estados de uma e duas mãos.

    Encapsula parâmetros de construção comuns, state() e _complete_task(),
    eliminando duplicação entre OneHandStateMachine e TwoHandsStateMachine.

    _reset_to_idle() é abstracto porque cada máquina tem campos de estado
    diferentes que precisam de ser limpos de forma específica.
    """

    def __init__(
        self,
        dwell_time:       timedelta,
        task_timeout:     timedelta,
        cycle_number_fn:  Callable[[], int],
        strategy:         ActivationStrategy,
    ) -> None:
        raise NotImplementedError

    def state(self) -> TaskState:
        raise NotImplementedError

    def _complete_task(self, end_time: datetime, was_forced: bool) -> TaskEvent:
        """Cria o TaskEvent, chama _reset_to_idle() e devolve o evento ao orquestrador."""
        raise NotImplementedError

    @abstractmethod
    def _reset_to_idle(self) -> None:
        """Repõe todos os campos de estado a None/IDLE. Implementado por cada subclasse."""
        ...


class OneHandStateMachine(_BaseStateMachine):
    """Máquina de estados para zonas que exigem apenas uma mão.

    IDLE → DWELLING → TASK_IN_PROGRESS → IDLE

    O critério de "mão confirmada na zona" é delegado na ActivationStrategy
    (injeção por construtor) — trocar de stillness para tempo fixo não toca aqui.
    """

    def __init__(
        self,
        dwell_time:       timedelta,
        task_timeout:     timedelta,
        cycle_number_fn:  Callable[[], int],
        strategy:         ActivationStrategy,
    ) -> None:
        raise NotImplementedError

    def update(self, classified_hands: list[ClassifiedHand], frame_time: datetime) -> TaskEvent | None:
        raise NotImplementedError

    def _handle_idle(self, classified_hands: list[ClassifiedHand]) -> None:
        # Fixa a primeira zona encontrada e avança — ignora as restantes
        # (o orquestrador garante que só chegamos aqui com _active a apontar para nós).
        raise NotImplementedError

    def _handle_dwelling(self, classified_hands: list[ClassifiedHand], frame_time: datetime) -> None:
        raise NotImplementedError

    def _handle_in_progress(self, classified_hands: list[ClassifiedHand], frame_time: datetime) -> TaskEvent | None:
        raise NotImplementedError

    def _hand_in_tracked_zone(self, classified_hands: list[ClassifiedHand]) -> HandDetection | None:
        raise NotImplementedError

    def _reset_to_idle(self) -> None:
        raise NotImplementedError


class TwoHandsStateMachine(_BaseStateMachine):
    """Máquina de estados para zonas que exigem as duas mãos simultaneamente.

    IDLE → WAITING_SECOND_HAND → DWELLING_TWO_HANDS → TASK_IN_PROGRESS → IDLE

    O dwell só começa quando ambas as mãos estão paradas ao mesmo tempo.
    Se qualquer mão sair durante TASK_IN_PROGRESS, a tarefa fecha imediatamente
    — a lógica de montagem assume cooperação contínua de ambas as mãos.

    _prev_detections é um dict por HandSide para que cada mão tenha a sua
    referência de frame anterior independente no cálculo de velocidade.

    WAITING_SECOND_HAND tem timeout igual a dwell_time: se a segunda mão não
    chegar (ou uma mão ficar presa na zona sem a outra), a máquina regressa a
    IDLE e desbloqueia o sistema. Ajustável via tracking.dwell_time_seconds.
    """

    def __init__(
        self,
        dwell_time:       timedelta,
        task_timeout:     timedelta,
        cycle_number_fn:  Callable[[], int],
        strategy:         ActivationStrategy,
    ) -> None:
        raise NotImplementedError

    def update(self, classified_hands: list[ClassifiedHand], frame_time: datetime) -> TaskEvent | None:
        raise NotImplementedError

    def _handle_idle(self, classified_hands: list[ClassifiedHand]) -> None:
        raise NotImplementedError

    def _handle_waiting_second_hand(self, classified_hands: list[ClassifiedHand], frame_time: datetime) -> None:
        raise NotImplementedError

    def _handle_dwelling_two_hands(self, classified_hands: list[ClassifiedHand], frame_time: datetime) -> None:
        raise NotImplementedError

    def _handle_in_progress(self, classified_hands: list[ClassifiedHand], frame_time: datetime) -> TaskEvent | None:
        raise NotImplementedError

    def _hands_in_tracked_zone(self, classified_hands: list[ClassifiedHand]) -> list[HandDetection]:
        raise NotImplementedError

    def _reset_to_idle(self) -> None:
        raise NotImplementedError


class TaskStateMachine:
    """Orquestrador: escolhe a máquina certa e impõe a regra de uma tarefa de cada vez.

    Enquanto _active não é None, entradas noutras zonas são ignoradas —
    o operador tem de terminar o que começou antes de o sistema reconhecer
    uma nova zona.

    _active é limpo quando a máquina interna regressa a IDLE, quer por
    conclusão de tarefa quer por saída antecipada. Sem este check, uma saída
    durante o dwell deixaria _active a apontar para a máquina errada e a
    próxima zona podia ser tratada com os requisitos errados (ex: Montagem
    exigia two-hands mas receberia one-hand, ou vice-versa).
    """

    def __init__(
        self,
        one_hand:        OneHandStateMachine,
        two_hands:       TwoHandsStateMachine,
        two_hands_zones: list[str],
    ) -> None:
        raise NotImplementedError

    def update(
        self,
        classified_hands: list[ClassifiedHand],
        frame_time: datetime,
    ) -> TaskEvent | None:
        raise NotImplementedError

    def _activate_best_zone(
        self,
        classified_hands: list[ClassifiedHand],
        frame_time: datetime,
    ) -> TaskEvent | None:
        raise NotImplementedError

    def _machine_for_zone(self, zone_name: str, hand_count: int) -> StateMachineInterface | None:
        """Devolve a máquina adequada se o critério de ativação da zona está cumprido.

        Ponto de extensão OCP: para adicionar um novo tipo de zona, adiciona a lógica
        aqui sem modificar _activate_best_zone.
        """
        raise NotImplementedError

    def current_state(self) -> TaskState:
        raise NotImplementedError
