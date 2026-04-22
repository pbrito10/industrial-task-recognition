"""
Testa OneHandStateMachine, TwoHandsStateMachine e TaskStateMachine.

Usa TimeDwellStrategy para simplificar o controlo de timing.
Todos os frames têm timestamps explícitos para tornar o comportamento determinístico.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from tests.conftest import make_hand, make_roi
from src.shared.hand_side import HandSide
from src.shared.task_state import TaskState
from src.tracking.activation_strategy import TimeDwellStrategy
from src.tracking.task_state_machine import (
    OneHandStateMachine,
    TwoHandsStateMachine,
    TaskStateMachine,
)

_DWELL   = timedelta(seconds=0.5)
_TIMEOUT = timedelta(seconds=30.0)
_T0      = datetime(2024, 1, 1, 12, 0, 0)


def _make_one_hand_machine():
    return OneHandStateMachine(
        dwell_time=_DWELL,
        task_timeout=_TIMEOUT,
        cycle_number_fn=lambda: 1,
        strategy=TimeDwellStrategy(),
    )


def _make_two_hands_machine():
    return TwoHandsStateMachine(
        dwell_time=_DWELL,
        task_timeout=_TIMEOUT,
        cycle_number_fn=lambda: 1,
        strategy=TimeDwellStrategy(),
    )


def _classified(hand, zone_name, x1=0, y1=0, x2=200, y2=200):
    roi = make_roi(zone_name, x1, y1, x2, y2)
    return [(hand, roi)]


def _no_hand():
    return []


# --- OneHandStateMachine ---

class TestOneHandStateMachine:

    def test_initial_state_is_idle(self):
        m = _make_one_hand_machine()
        assert m.state() == TaskState.IDLE

    def test_hand_enters_zone_moves_to_dwelling(self):
        m = _make_one_hand_machine()
        hand = make_hand(mcp=(50, 50))
        m.update(_classified(hand, "Porca"), _T0)
        assert m.state() == TaskState.DWELLING

    def test_full_cycle_produces_event(self):
        m = _make_one_hand_machine()
        hand = make_hand(mcp=(50, 50))

        m.update(_classified(hand, "Porca"), _T0)                         # IDLE → DWELLING
        m.update(_classified(hand, "Porca"), _T0 + timedelta(seconds=0.1))  # dwell_start definido
        m.update(_classified(hand, "Porca"), _T0 + timedelta(seconds=0.7))  # → TASK_IN_PROGRESS

        event = m.update(_no_hand(), _T0 + timedelta(seconds=1.0))         # mão saiu → evento
        assert event is not None
        assert event.zone_name == "Porca"
        assert event.was_forced is False
        assert m.state() == TaskState.IDLE

    def test_exits_during_dwell_resets_to_idle(self):
        m = _make_one_hand_machine()
        hand = make_hand(mcp=(50, 50))
        m.update(_classified(hand, "Porca"), _T0)                         # DWELLING
        m.update(_no_hand(), _T0 + timedelta(seconds=0.1))                 # saiu cedo → IDLE
        assert m.state() == TaskState.IDLE

    def test_timeout_produces_forced_event(self):
        m = _make_one_hand_machine()
        hand = make_hand(mcp=(50, 50))

        m.update(_classified(hand, "Porca"), _T0)
        m.update(_classified(hand, "Porca"), _T0 + timedelta(seconds=0.1))
        m.update(_classified(hand, "Porca"), _T0 + timedelta(seconds=0.7))  # TASK_IN_PROGRESS

        event = m.update(
            _classified(hand, "Porca"),
            _T0 + timedelta(seconds=35),  # timeout expirou
        )
        assert event is not None
        assert event.was_forced is True

    def test_moving_hand_resets_dwell_timer(self):
        # Com StillnessDwellStrategy: mão em movimento durante DWELLING
        # deve reiniciar o dwell_start e manter estado DWELLING
        from src.tracking.activation_strategy import StillnessDwellStrategy
        m = OneHandStateMachine(
            dwell_time=_DWELL,
            task_timeout=_TIMEOUT,
            cycle_number_fn=lambda: 1,
            strategy=StillnessDwellStrategy(velocity_threshold_px_per_frame=5.0),
        )
        hand_still  = make_hand(wrist=(50, 50), mcp=(50, 50))
        hand_moving = make_hand(wrist=(70, 50), mcp=(50, 50))  # pulso moveu 20px

        m.update(_classified(hand_still, "Porca"), _T0)                        # IDLE → DWELLING (prev=None)
        m.update(_classified(hand_still, "Porca"), _T0 + timedelta(seconds=0.1))   # is_active(still,None)=False
        # Mão move-se: dwell_start deve ser anulado, estado mantém-se DWELLING
        m.update(_classified(hand_moving, "Porca"), _T0 + timedelta(seconds=0.2))  # is_active(moving,still)=False
        assert m.state() == TaskState.DWELLING
        # Mão para de novo — prev ainda é hand_moving, por isso mais um frame até estabilizar
        m.update(_classified(hand_still, "Porca"), _T0 + timedelta(seconds=0.3))   # is_active(still,moving)=False
        m.update(_classified(hand_still, "Porca"), _T0 + timedelta(seconds=0.4))   # is_active(still,still)=True → dwell_start=T0+0.4
        # Timer recomeçou: 0.3s ainda não chega a dwell(0.5s)
        m.update(_classified(hand_still, "Porca"), _T0 + timedelta(seconds=0.7))   # elapsed=0.3s < 0.5s
        assert m.state() == TaskState.DWELLING
        # Agora o elapsed atinge o dwell_time
        m.update(_classified(hand_still, "Porca"), _T0 + timedelta(seconds=1.0))   # elapsed=0.6s >= 0.5s
        assert m.state() == TaskState.TASK_IN_PROGRESS


# --- TwoHandsStateMachine ---

class TestTwoHandsStateMachine:

    def test_initial_state_is_idle(self):
        assert _make_two_hands_machine().state() == TaskState.IDLE

    def test_one_hand_moves_to_waiting(self):
        m = _make_two_hands_machine()
        hand = make_hand(mcp=(50, 50))
        m.update(_classified(hand, "Montagem"), _T0)
        assert m.state() == TaskState.WAITING_SECOND_HAND

    def test_two_hands_moves_to_dwelling(self):
        m = _make_two_hands_machine()
        h1 = make_hand(mcp=(50, 50), side=HandSide.RIGHT)
        h2 = make_hand(mcp=(50, 50), side=HandSide.LEFT)
        roi = make_roi("Montagem", 0, 0, 200, 200)
        hands = [(h1, roi), (h2, roi)]

        m.update(hands, _T0)  # IDLE → WAITING_SECOND_HAND (1 mão detectada primeiro)
        # Reinicia com as duas mãos desde o início para chegar a DWELLING_TWO_HANDS
        m2 = _make_two_hands_machine()
        m2.update([(h1, roi)], _T0)  # WAITING_SECOND_HAND
        m2.update([(h1, roi), (h2, roi)], _T0 + timedelta(seconds=0.1))  # → DWELLING_TWO_HANDS
        assert m2.state() == TaskState.DWELLING_TWO_HANDS

    def test_waiting_timeout_resets_to_idle(self):
        m = _make_two_hands_machine()
        hand = make_hand(mcp=(50, 50))
        roi = make_roi("Montagem", 0, 0, 200, 200)
        m.update([(hand, roi)], _T0)                                     # IDLE → WAITING_SECOND_HAND
        m.update([(hand, roi)], _T0 + timedelta(seconds=0.1))            # waiting_start definido
        # Segunda mão não chegou — timeout expira
        m.update([(hand, roi)], _T0 + timedelta(seconds=0.7))
        assert m.state() == TaskState.IDLE

    def test_full_two_hands_cycle_produces_event(self):
        m = _make_two_hands_machine()
        h1 = make_hand(mcp=(50, 50), side=HandSide.RIGHT)
        h2 = make_hand(mcp=(50, 50), side=HandSide.LEFT)
        roi = make_roi("Montagem", 0, 0, 200, 200)

        m.update([(h1, roi)], _T0)                                         # WAITING_SECOND_HAND
        m.update([(h1, roi), (h2, roi)], _T0 + timedelta(seconds=0.1))    # DWELLING_TWO_HANDS
        m.update([(h1, roi), (h2, roi)], _T0 + timedelta(seconds=0.2))    # dwell_start
        m.update([(h1, roi), (h2, roi)], _T0 + timedelta(seconds=0.8))    # TASK_IN_PROGRESS

        event = m.update([], _T0 + timedelta(seconds=1.0))                 # ambas saíram → evento
        assert event is not None
        assert event.zone_name == "Montagem"
        assert event.was_forced is False


# --- TaskStateMachine ---

class TestTaskStateMachine:

    def _make_orchestrator(self):
        one_hand  = _make_one_hand_machine()
        two_hands = _make_two_hands_machine()
        return TaskStateMachine(
            one_hand=one_hand,
            two_hands=two_hands,
            two_hands_zones=["Montagem"],
        )

    def test_initial_state_idle(self):
        assert self._make_orchestrator().current_state() == TaskState.IDLE

    def test_routes_one_hand_zone(self):
        tsm = self._make_orchestrator()
        hand = make_hand(mcp=(50, 50))
        roi = make_roi("Porca", 0, 0, 200, 200)
        tsm.update([(hand, roi)], _T0)
        assert tsm.current_state() == TaskState.DWELLING

    def test_ignores_new_zone_while_active(self):
        tsm = self._make_orchestrator()
        h1 = make_hand(mcp=(50, 50),   side=HandSide.RIGHT)
        h2 = make_hand(mcp=(300, 300), side=HandSide.LEFT)
        roi_porca  = make_roi("Porca",  0,   0,   200, 200)
        roi_chassi = make_roi("Chassi", 250, 250, 400, 400)

        # h1 ativa Porca
        tsm.update([(h1, roi_porca)], _T0)
        assert tsm.current_state() == TaskState.DWELLING

        # h2 entra em Chassi enquanto Porca está ativa — orquestrador ignora Chassi
        tsm.update([(h1, roi_porca), (h2, roi_chassi)], _T0 + timedelta(seconds=0.1))
        assert tsm.current_state() == TaskState.DWELLING

    def test_resets_after_task_completes(self):
        tsm = self._make_orchestrator()
        hand = make_hand(mcp=(50, 50))
        roi = make_roi("Porca", 0, 0, 200, 200)

        tsm.update([(hand, roi)], _T0)
        tsm.update([(hand, roi)], _T0 + timedelta(seconds=0.1))
        tsm.update([(hand, roi)], _T0 + timedelta(seconds=0.7))
        tsm.update([], _T0 + timedelta(seconds=1.0))  # task concluída

        assert tsm.current_state() == TaskState.IDLE
