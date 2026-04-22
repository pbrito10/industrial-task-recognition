from datetime import timedelta
from src.metrics.cycle_metrics import CycleMetrics


def _td(s: float) -> timedelta:
    return timedelta(seconds=s)


def test_count_in_order():
    m = CycleMetrics()
    m.add(_td(10), sequence_in_order=True)
    m.add(_td(12), sequence_in_order=False)
    m.add(_td(11), sequence_in_order=True)
    assert m.count_in_order() == 2


def test_count_out_of_order():
    m = CycleMetrics()
    m.add(_td(10), sequence_in_order=True)
    m.add(_td(12), sequence_in_order=False)
    assert m.count_out_of_order() == 1


def test_total_count():
    m = CycleMetrics()
    m.add(_td(10), True)
    m.add(_td(10), False)
    assert m.count() == 2


def test_empty_counts_zero():
    m = CycleMetrics()
    assert m.count() == 0
    assert m.count_in_order() == 0
    assert m.count_out_of_order() == 0
