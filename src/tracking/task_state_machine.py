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


# ── Interface comum ───────────────────────────────────────────────────────────

class StateMachineInterface(ABC):
    """Contrato partilhado entre OneHandStateMachine e TwoHandsStateMachine."""

    @abstractmethod
    def update(
        self,
        classified_hands: list[ClassifiedHand],
        frame_time: datetime,
    ) -> TaskEvent | None:
        """Processa um frame. Devolve TaskEvent se uma tarefa terminou."""

    @abstractmethod
    def state(self) -> TaskState:
        """Estado atual da máquina."""


# ── Máquina para zonas one_hand ───────────────────────────────────────────────

class OneHandStateMachine(StateMachineInterface):
    """Gere o ciclo de vida de tarefas em zonas que exigem uma mão.

    Fluxo: IDLE → DWELLING → TASK_IN_PROGRESS → IDLE
    O dwell timer só avança quando a estratégia de ativação confirma
    que a mão está parada (ou outro critério configurado).
    """

    def __init__(
        self,
        dwell_time:       timedelta,
        task_timeout:     timedelta,
        cycle_number_fn:  Callable[[], int],
        strategy:         ActivationStrategy,
    ) -> None:
        self._dwell_time      = dwell_time
        self._task_timeout    = task_timeout
        self._cycle_number_fn = cycle_number_fn
        self._strategy        = strategy

        self._task_state:    TaskState            = TaskState.IDLE
        self._tracked_zone:  str | None           = None
        self._prev_detection: HandDetection | None = None
        self._dwell_start:   datetime | None      = None
        self._task_start:    datetime | None      = None

    def state(self) -> TaskState:
        return self._task_state

    def update(self, classified_hands: list[ClassifiedHand], frame_time: datetime) -> TaskEvent | None:
        if self._task_state == TaskState.IDLE:
            return self._handle_idle(classified_hands)
        if self._task_state == TaskState.DWELLING:
            return self._handle_dwelling(classified_hands, frame_time)
        if self._task_state == TaskState.TASK_IN_PROGRESS:
            return self._handle_in_progress(classified_hands, frame_time)
        return None

    def _handle_idle(self, classified_hands: list[ClassifiedHand]) -> None:
        """Aguarda que uma mão entre numa zona; ao entrar, avança para DWELLING."""
        for detection, zone in classified_hands:
            if zone is None:
                continue
            self._tracked_zone   = zone.name
            self._prev_detection = None
            self._dwell_start    = None
            self._task_state     = TaskState.DWELLING
            return
        return

    def _handle_dwelling(
        self,
        classified_hands: list[ClassifiedHand],
        frame_time: datetime,
    ) -> None:
        """Corre o dwell timer; avança para TASK_IN_PROGRESS quando expirar."""
        hand = self._hand_in_tracked_zone(classified_hands)

        if hand is None:
            # Saiu antes do dwell — descarta sem emitir evento
            self._reset_to_idle()
            return

        if self._strategy.is_active(hand, self._prev_detection):
            if self._dwell_start is None:
                self._dwell_start = frame_time
            elif frame_time - self._dwell_start >= self._dwell_time:
                self._task_state = TaskState.TASK_IN_PROGRESS
                self._task_start = frame_time
        else:
            # Mão em movimento — reinicia o dwell timer
            self._dwell_start = None

        self._prev_detection = hand

    def _handle_in_progress(
        self,
        classified_hands: list[ClassifiedHand],
        frame_time: datetime,
    ) -> TaskEvent | None:
        """Fecha a tarefa quando a mão sai ou o timeout expira."""
        if frame_time - self._task_start >= self._task_timeout:
            return self._complete_task(frame_time, was_forced=True)

        if self._hand_in_tracked_zone(classified_hands) is None:
            return self._complete_task(frame_time, was_forced=False)

        return None

    def _hand_in_tracked_zone(
        self,
        classified_hands: list[ClassifiedHand],
    ) -> HandDetection | None:
        """Devolve a deteção da mão que está na zona rastreada, ou None."""
        for detection, zone in classified_hands:
            if zone is not None and zone.name == self._tracked_zone:
                return detection
        return None

    def _complete_task(self, end_time: datetime, was_forced: bool) -> TaskEvent:
        """Cria o TaskEvent, emite-o e repõe a máquina em IDLE."""
        event = TaskEvent.create(
            zone_name=self._tracked_zone,
            start_time=self._task_start,
            end_time=end_time,
            cycle_number=self._cycle_number_fn(),
            was_forced=was_forced,
        )
        self._reset_to_idle()
        return event

    def _reset_to_idle(self) -> None:
        """Apaga todo o estado transitório e volta a IDLE."""
        self._task_state     = TaskState.IDLE
        self._tracked_zone   = None
        self._prev_detection = None
        self._dwell_start    = None
        self._task_start     = None


# ── Máquina para zonas two_hands ──────────────────────────────────────────────

class TwoHandsStateMachine(StateMachineInterface):
    """Gere o ciclo de vida de tarefas em zonas que exigem as duas mãos.

    Fluxo: IDLE → WAITING_SECOND_HAND → DWELLING_TWO_HANDS → TASK_IN_PROGRESS → IDLE
    O dwell timer só arranca quando AMBAS as mãos estão na zona.
    Qualquer mão a sair durante TASK_IN_PROGRESS fecha a tarefa.
    """

    def __init__(
        self,
        dwell_time:       timedelta,
        task_timeout:     timedelta,
        cycle_number_fn:  Callable[[], int],
        strategy:         ActivationStrategy,
    ) -> None:
        self._dwell_time      = dwell_time
        self._task_timeout    = task_timeout
        self._cycle_number_fn = cycle_number_fn
        self._strategy        = strategy

        self._task_state:     TaskState                      = TaskState.IDLE
        self._tracked_zone:   str | None                     = None
        self._prev_detections: dict[HandSide, HandDetection] = {}
        self._dwell_start:    datetime | None                = None
        self._task_start:     datetime | None                = None

    def state(self) -> TaskState:
        return self._task_state

    def update(self, classified_hands: list[ClassifiedHand], frame_time: datetime) -> TaskEvent | None:
        if self._task_state == TaskState.IDLE:
            return self._handle_idle(classified_hands)
        if self._task_state == TaskState.WAITING_SECOND_HAND:
            return self._handle_waiting_second_hand(classified_hands)
        if self._task_state == TaskState.DWELLING_TWO_HANDS:
            return self._handle_dwelling_two_hands(classified_hands, frame_time)
        if self._task_state == TaskState.TASK_IN_PROGRESS:
            return self._handle_in_progress(classified_hands, frame_time)
        return None

    def _handle_idle(self, classified_hands: list[ClassifiedHand]) -> None:
        """Aguarda a primeira mão entrar na zona; avança para WAITING_SECOND_HAND."""
        for detection, zone in classified_hands:
            if zone is None:
                continue
            self._tracked_zone    = zone.name
            self._prev_detections = {}
            self._dwell_start     = None
            self._task_state      = TaskState.WAITING_SECOND_HAND
            return
        return

    def _handle_waiting_second_hand(self, classified_hands: list[ClassifiedHand]) -> None:
        """Aguarda a segunda mão; avança para DWELLING_TWO_HANDS quando ambas estiverem na zona."""
        hands = self._hands_in_tracked_zone(classified_hands)

        if len(hands) == 0:
            self._reset_to_idle()
            return

        if len(hands) >= 2:
            self._dwell_start = None
            self._task_state  = TaskState.DWELLING_TWO_HANDS

    def _handle_dwelling_two_hands(
        self,
        classified_hands: list[ClassifiedHand],
        frame_time: datetime,
    ) -> None:
        """Corre o dwell timer com ambas as mãos paradas; avança para TASK_IN_PROGRESS."""
        hands = self._hands_in_tracked_zone(classified_hands)

        if len(hands) < 2:
            # Uma mão saiu — reinicia completamente
            self._reset_to_idle()
            return

        # Ambas as mãos devem estar paradas para avançar o timer
        both_still = all(
            self._strategy.is_active(hand, self._prev_detections.get(hand.hand_side))
            for hand in hands
        )

        if both_still:
            if self._dwell_start is None:
                self._dwell_start = frame_time
            elif frame_time - self._dwell_start >= self._dwell_time:
                self._task_state = TaskState.TASK_IN_PROGRESS
                self._task_start = frame_time
        else:
            self._dwell_start = None

        for hand in hands:
            self._prev_detections[hand.hand_side] = hand

    def _handle_in_progress(
        self,
        classified_hands: list[ClassifiedHand],
        frame_time: datetime,
    ) -> TaskEvent | None:
        """Fecha a tarefa quando qualquer mão sai ou o timeout expira."""
        if frame_time - self._task_start >= self._task_timeout:
            return self._complete_task(frame_time, was_forced=True)

        if len(self._hands_in_tracked_zone(classified_hands)) < 2:
            return self._complete_task(frame_time, was_forced=False)

        return None

    def _hands_in_tracked_zone(
        self,
        classified_hands: list[ClassifiedHand],
    ) -> list[HandDetection]:
        """Devolve as deteções de mãos presentes na zona rastreada."""
        return [
            detection for detection, zone in classified_hands
            if zone is not None and zone.name == self._tracked_zone
        ]

    def _complete_task(self, end_time: datetime, was_forced: bool) -> TaskEvent:
        """Cria o TaskEvent, emite-o e repõe a máquina em IDLE."""
        event = TaskEvent.create(
            zone_name=self._tracked_zone,
            start_time=self._task_start,
            end_time=end_time,
            cycle_number=self._cycle_number_fn(),
            was_forced=was_forced,
        )
        self._reset_to_idle()
        return event

    def _reset_to_idle(self) -> None:
        """Apaga todo o estado transitório e volta a IDLE."""
        self._task_state      = TaskState.IDLE
        self._tracked_zone    = None
        self._prev_detections = {}
        self._dwell_start     = None
        self._task_start      = None


# ── Orquestrador ──────────────────────────────────────────────────────────────

class TaskStateMachine:
    """Orquestra as máquinas de estado por tipo de zona.

    Regra "uma tarefa de cada vez": enquanto uma máquina está ativa,
    entradas noutras zonas são ignoradas.

    Sabe quais zonas são two_hands (via settings) e ativa a máquina certa.
    """

    def __init__(
        self,
        one_hand:        OneHandStateMachine,
        two_hands:       TwoHandsStateMachine,
        two_hands_zones: list[str],
    ) -> None:
        self._one_hand        = one_hand
        self._two_hands       = two_hands
        self._two_hands_zones = set(two_hands_zones)
        self._active:         StateMachineInterface | None = None

    def update(
        self,
        classified_hands: list[ClassifiedHand],
        frame_time: datetime,
    ) -> TaskEvent | None:
        if self._active is not None:
            event = self._active.update(classified_hands, frame_time)
            if event is not None:
                # Máquina voltou a IDLE internamente — desativa o orquestrador
                self._active = None
            return event

        # IDLE — verifica se alguma mão entrou numa zona
        for _, zone in classified_hands:
            if zone is None:
                continue
            self._active = (
                self._two_hands if zone.name in self._two_hands_zones
                else self._one_hand
            )
            return self._active.update(classified_hands, frame_time)

        return None

    def current_state(self) -> TaskState:
        """Estado atual do orquestrador (IDLE se nenhuma máquina estiver ativa)."""
        if self._active is None:
            return TaskState.IDLE
        return self._active.state()
