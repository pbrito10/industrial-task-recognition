from datetime import datetime, timedelta
import pytest
from src.tracking.cycle_tracker import CycleTracker
from src.tracking.order_matching import (
    RESULT_IN_ORDER,
    RESULT_INCOMPLETE,
    RESULT_OUT_OF_ORDER,
    diagnose_order,
    matches_order,
)
from src.tracking.task_event import TaskEvent

_T0 = datetime(2024, 1, 1, 12, 0, 0)

_ORDER = ["Porca", "Montagem", "Chassi", "Saida"]
_WHEEL_ORDER = ["Porca", "Rodas", "Montagem", "Saida"]


def _event(zone: str, offset_s: float, duration_s: float = 2.0, forced: bool = False) -> TaskEvent:
    start = _T0 + timedelta(seconds=offset_s)
    return TaskEvent.create(zone, start, start + timedelta(seconds=duration_s), 1, forced)


# --- matches_order ---

class TestMatchesOrder:

    def test_correct_order(self):
        assert matches_order(["Porca", "Montagem", "Chassi", "Saida"], _ORDER)

    def test_repeated_zone_allowed(self):
        assert matches_order(["Porca", "Porca", "Montagem", "Chassi", "Saida"], _ORDER)

    def test_wheels_allowed_between_one_and_four_times(self):
        assert matches_order(["Porca", "Rodas", "Montagem", "Saida"], _WHEEL_ORDER)
        assert matches_order(["Porca", "Rodas", "Rodas", "Rodas", "Rodas", "Montagem", "Saida"], _WHEEL_ORDER)
        assert matches_order(["Porca", "Rodas", "Montagem", "Rodas", "Montagem", "Saida"], _WHEEL_ORDER)

    def test_more_than_four_wheels_fails(self):
        assert not matches_order(
            [
                "Porca",
                "Rodas",
                "Montagem",
                "Rodas",
                "Montagem",
                "Rodas",
                "Montagem",
                "Rodas",
                "Montagem",
                "Rodas",
                "Montagem",
                "Saida",
            ],
            _WHEEL_ORDER,
        )

    def test_skipped_zone_fails(self):
        assert not matches_order(["Porca", "Chassi", "Saida"], _ORDER)

    def test_out_of_order_fails(self):
        assert not matches_order(["Montagem", "Porca", "Chassi", "Saida"], _ORDER)

    def test_incomplete_sequence_fails(self):
        assert not matches_order(["Porca", "Montagem"], _ORDER)

    def test_empty_actual_fails(self):
        assert not matches_order([], _ORDER)

    def test_empty_expected_passes(self):
        assert matches_order(["qualquer"], [])


class TestDiagnoseOrder:

    def test_correct_order(self):
        diagnosis = diagnose_order(["Porca", "Montagem", "Chassi", "Saida"], _ORDER)

        assert diagnosis.result == RESULT_IN_ORDER
        assert diagnosis.problem == "Sem problema detetado."

    def test_skipped_zone_is_incomplete(self):
        diagnosis = diagnose_order(["Porca", "Chassi", "Saida"], _ORDER)

        assert diagnosis.result == RESULT_INCOMPLETE
        assert '"Montagem"' in diagnosis.problem

    def test_missing_tail_is_incomplete(self):
        diagnosis = diagnose_order(["Porca", "Montagem"], _ORDER)

        assert diagnosis.result == RESULT_INCOMPLETE
        assert '"Chassi"' in diagnosis.problem
        assert '"Saida"' in diagnosis.problem

    def test_returning_to_previous_zone_is_out_of_order(self):
        diagnosis = diagnose_order(["Porca", "Montagem", "Porca", "Saida"], _ORDER)

        assert diagnosis.result == RESULT_OUT_OF_ORDER
        assert 'Esperava "Chassi", mas apareceu "Porca".' == diagnosis.problem

    def test_unknown_zone_is_out_of_order(self):
        diagnosis = diagnose_order(["Porca", "Intruso", "Saida"], _ORDER)

        assert diagnosis.result == RESULT_OUT_OF_ORDER
        assert 'Esperava "Montagem", mas apareceu "Intruso".' == diagnosis.problem

    def test_more_than_four_wheels_is_out_of_order(self):
        diagnosis = diagnose_order(
            [
                "Porca",
                "Rodas",
                "Montagem",
                "Rodas",
                "Montagem",
                "Rodas",
                "Montagem",
                "Rodas",
                "Montagem",
                "Rodas",
                "Montagem",
                "Saida",
            ],
            _WHEEL_ORDER,
        )

        assert diagnosis.result == RESULT_OUT_OF_ORDER
        assert diagnosis.problem == 'A zona "Rodas" apareceu 5 vezes; o intervalo aceite é 1 a 4 presenças.'


# --- CycleTracker ---

class TestCycleTracker:

    @pytest.fixture
    def tracker(self):
        return CycleTracker(exit_zone="Saida", expected_order=_ORDER)

    def test_non_exit_event_returns_none(self, tracker):
        assert tracker.record(_event("Porca", 0)) is None

    def test_exit_event_closes_cycle(self, tracker):
        tracker.record(_event("Porca",    0))
        tracker.record(_event("Montagem", 2))
        tracker.record(_event("Chassi",   4))
        result = tracker.record(_event("Saida", 6))
        assert result is not None
        assert result.cycle_number == 1

    def test_cycle_number_increments(self, tracker):
        assert tracker.current_cycle_number() == 1
        for zone in ["Porca", "Montagem", "Chassi", "Saida"]:
            tracker.record(_event(zone, 0))
        assert tracker.current_cycle_number() == 2

    def test_forced_exit_does_not_close_cycle(self, tracker):
        tracker.record(_event("Porca", 0))
        result = tracker.record(_event("Saida", 2, forced=True))
        assert result is None

    def test_new_start_zone_closes_previous_incomplete_cycle(self, tracker):
        tracker.record(_event("Porca", 0))
        tracker.record(_event("Montagem", 2))

        result = tracker.record(_event("Porca", 10))

        assert result is not None
        assert result.cycle_number == 1
        assert result.sequence_in_order is False
        assert result.actual_sequence == ("Porca", "Montagem")
        assert tracker.current_cycle_number() == 2
        assert tracker.last_event_started_new_cycle() is True

        tracker.record(_event("Montagem", 12))
        assert tracker.last_event_started_new_cycle() is False
        tracker.record(_event("Chassi", 14))
        next_result = tracker.record(_event("Saida", 16))

        assert next_result is not None
        assert next_result.cycle_number == 2
        assert next_result.sequence_in_order is True
        assert next_result.actual_sequence == ("Porca", "Montagem", "Chassi", "Saida")

    def test_repeated_start_zone_before_progress_does_not_close_cycle(self, tracker):
        tracker.record(_event("Porca", 0))
        assert tracker.record(_event("Porca", 2)) is None
        assert tracker.last_event_started_new_cycle() is False

        tracker.record(_event("Montagem", 4))
        tracker.record(_event("Chassi", 6))
        result = tracker.record(_event("Saida", 8))

        assert result is not None
        assert result.sequence_in_order is True
        assert result.actual_sequence == ("Porca", "Porca", "Montagem", "Chassi", "Saida")

    def test_forced_start_zone_does_not_close_previous_cycle(self, tracker):
        tracker.record(_event("Porca", 0))
        tracker.record(_event("Montagem", 2))

        assert tracker.record(_event("Porca", 4, forced=True)) is None
        assert tracker.current_cycle_number() == 1

        tracker.record(_event("Chassi", 6))
        result = tracker.record(_event("Saida", 8))

        assert result is not None
        assert result.sequence_in_order is True

    def test_correct_order_flagged(self, tracker):
        for i, zone in enumerate(["Porca", "Montagem", "Chassi", "Saida"]):
            result = tracker.record(_event(zone, i * 2))
        assert result.sequence_in_order is True
        assert result.expected_sequence == tuple(_ORDER)

    def test_incorrect_order_flagged(self, tracker):
        for i, zone in enumerate(["Montagem", "Porca", "Chassi", "Saida"]):
            result = tracker.record(_event(zone, i * 2))
        assert result.sequence_in_order is False
        assert result.is_anomaly is False

    def test_forced_tasks_excluded_from_order_check(self, tracker):
        # Tarefa forçada no meio não deve influenciar a verificação de ordem
        tracker.record(_event("Porca",    0))
        tracker.record(_event("Intruso",  2, forced=True))
        tracker.record(_event("Montagem", 4))
        tracker.record(_event("Chassi",   6))
        result = tracker.record(_event("Saida", 8))
        assert result.sequence_in_order is True

    def test_cycle_duration(self, tracker):
        tracker.record(_event("Porca",    0))
        tracker.record(_event("Montagem", 2))
        tracker.record(_event("Chassi",   4))
        result = tracker.record(_event("Saida", 6, duration_s=2))
        # do início de Porca (t=0) ao fim de Saida (t=8)
        assert result.duration == timedelta(seconds=8)
