import pytest
from datetime import datetime, timedelta
from src.metrics.metrics_calculator import MetricsCalculator
from src.tracking.task_event import TaskEvent
from src.tracking.cycle_result import CycleResult

_T0 = datetime(2024, 1, 1, 12, 0, 0)


def _event(zone: str, duration_s: float, forced: bool = False) -> TaskEvent:
    start = _T0
    end   = _T0 + timedelta(seconds=duration_s)
    return TaskEvent.create(zone, start, end, cycle_number=1, was_forced=forced)


def _cycle(duration_s: float, in_order: bool = True) -> CycleResult:
    return CycleResult(
        start_time=_T0,
        end_time=_T0 + timedelta(seconds=duration_s),
        duration=timedelta(seconds=duration_s),
        cycle_number=1,
        sequence_in_order=in_order,
        actual_sequence=["Porca", "Saida"],
    )


@pytest.fixture
def calc():
    return MetricsCalculator(session_start=_T0, zone_names=["Porca", "Montagem", "Saida"])


def test_forced_event_goes_to_interruption(calc):
    calc.record(_event("Porca", 10.0, forced=True))
    snap = calc.snapshot()
    assert snap.interruption_time == timedelta(seconds=10)
    assert snap.productive_time == timedelta(0)


def test_normal_event_goes_to_productive(calc):
    calc.record(_event("Porca", 5.0))
    snap = calc.snapshot()
    assert snap.productive_time == timedelta(seconds=5)
    assert snap.interruption_time == timedelta(0)


def test_task_metrics_populated(calc):
    calc.record(_event("Porca", 3.0))
    calc.record(_event("Porca", 7.0))
    snap = calc.snapshot()
    tm = snap.task_metrics["Porca"]
    assert tm.count() == 2
    assert tm.minimum() == timedelta(seconds=3)
    assert tm.maximum() == timedelta(seconds=7)


def test_forced_event_not_in_task_metrics(calc):
    calc.record(_event("Porca", 10.0, forced=True))
    snap = calc.snapshot()
    assert snap.task_metrics["Porca"].count() == 0


def test_unknown_zone_creates_entry(calc):
    calc.record(_event("ZonaDesconhecida", 2.0))
    snap = calc.snapshot()
    assert "ZonaDesconhecida" in snap.task_metrics


def test_bottleneck_zone(calc):
    calc.record(_event("Porca",    2.0))
    calc.record(_event("Montagem", 10.0))
    snap = calc.snapshot()
    assert snap.bottleneck_zone == "Montagem"


def test_bottleneck_none_when_no_data(calc):
    snap = calc.snapshot()
    assert snap.bottleneck_zone is None


def test_percentages_sum_to_100(calc):
    calc.record(_event("Porca",    5.0))
    calc.record(_event("Montagem", 3.0, forced=True))
    snap = calc.snapshot()
    total = snap.productive_percentage + snap.transition_percentage + snap.interruption_percentage
    assert total == pytest.approx(100.0, abs=0.1)


def test_percentages_zero_when_session_duration_is_zero():
    # snapshot tirado exatamente no mesmo instante do session_start → duration = 0
    # não deve dividir por zero nem lançar exceção
    from unittest.mock import patch
    now = _T0
    calc = MetricsCalculator(session_start=now, zone_names=[])
    with patch("src.metrics.metrics_calculator.datetime") as mock_dt:
        mock_dt.now.return_value = now
        snap = calc.snapshot()
    assert snap.productive_percentage == 0.0
    assert snap.transition_percentage == 0.0
    assert snap.interruption_percentage == 0.0


def test_cycle_metrics_recorded(calc):
    calc.record_cycle(_cycle(60.0, in_order=True))
    calc.record_cycle(_cycle(70.0, in_order=False))
    snap = calc.snapshot()
    assert snap.cycle_metrics.count() == 2
    assert snap.cycle_metrics.count_in_order() == 1


def test_snapshot_task_metrics_are_frozen_by_value(calc):
    calc.record(_event("Porca", 3.0))
    snap = calc.snapshot()

    calc.record(_event("Porca", 7.0))

    assert snap.task_metrics["Porca"].count() == 1


def test_snapshot_task_metrics_mapping_is_read_only(calc):
    snap = calc.snapshot()

    with pytest.raises(TypeError):
        snap.task_metrics["Nova"] = snap.task_metrics["Porca"]
