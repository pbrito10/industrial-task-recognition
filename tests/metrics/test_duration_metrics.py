import pytest
from datetime import timedelta
from src.metrics.task_metrics import TaskMetrics  # usa TaskMetrics como proxy de _DurationMetrics


def _td(s: float) -> timedelta:
    return timedelta(seconds=s)


@pytest.fixture
def metrics():
    m = TaskMetrics()
    for s in [2.0, 4.0, 6.0]:
        m.add(_td(s))
    return m


def test_count(metrics):
    assert metrics.count() == 3


def test_minimum(metrics):
    assert metrics.minimum() == _td(2.0)


def test_maximum(metrics):
    assert metrics.maximum() == _td(6.0)


def test_average(metrics):
    assert metrics.average() == pytest.approx(_td(4.0), abs=_td(0.001))


def test_std_deviation(metrics):
    # desvio padrão de [2, 4, 6] = sqrt(((4+0+4)/3)) = sqrt(8/3) ≈ 1.633
    import math
    expected = math.sqrt(8 / 3)
    assert metrics.std_deviation().total_seconds() == pytest.approx(expected, rel=1e-3)


def test_std_deviation_single_entry_is_zero():
    m = TaskMetrics()
    m.add(_td(5.0))
    assert m.std_deviation() == timedelta(0)


def test_empty_count_zero():
    assert TaskMetrics().count() == 0
