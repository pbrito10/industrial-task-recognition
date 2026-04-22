from datetime import datetime, timedelta
import pytest
from src.tracking.cycle_tracker import CycleTracker, _matches_order
from src.tracking.task_event import TaskEvent

_T0 = datetime(2024, 1, 1, 12, 0, 0)

_ORDER = ["Porca", "Montagem", "Chassi", "Saida"]


def _event(zone: str, offset_s: float, duration_s: float = 2.0, forced: bool = False) -> TaskEvent:
    start = _T0 + timedelta(seconds=offset_s)
    return TaskEvent.create(zone, start, start + timedelta(seconds=duration_s), 1, forced)


# --- _matches_order ---

class TestMatchesOrder:

    def test_correct_order(self):
        assert _matches_order(["Porca", "Montagem", "Chassi", "Saida"], _ORDER)

    def test_repeated_zone_allowed(self):
        assert _matches_order(["Porca", "Porca", "Montagem", "Chassi", "Saida"], _ORDER)

    def test_skipped_zone_fails(self):
        assert not _matches_order(["Porca", "Chassi", "Saida"], _ORDER)

    def test_out_of_order_fails(self):
        assert not _matches_order(["Montagem", "Porca", "Chassi", "Saida"], _ORDER)

    def test_incomplete_sequence_fails(self):
        assert not _matches_order(["Porca", "Montagem"], _ORDER)

    def test_empty_actual_fails(self):
        assert not _matches_order([], _ORDER)

    def test_empty_expected_passes(self):
        assert _matches_order(["qualquer"], [])


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

    def test_correct_order_flagged(self, tracker):
        for i, zone in enumerate(["Porca", "Montagem", "Chassi", "Saida"]):
            result = tracker.record(_event(zone, i * 2))
        assert result.sequence_in_order is True

    def test_incorrect_order_flagged(self, tracker):
        # Sem histórico (<2 referências) a ordem fica como "não determinada" (None)
        for i, zone in enumerate(["Montagem", "Porca", "Chassi", "Saida"]):
            result = tracker.record(_event(zone, i * 2))
        assert result.sequence_in_order is None
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
