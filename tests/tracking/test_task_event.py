from datetime import datetime, timedelta
from src.tracking.task_event import TaskEvent


def test_create_calculates_duration():
    t0 = datetime(2024, 1, 1, 12, 0, 0)
    t1 = t0 + timedelta(seconds=5)
    event = TaskEvent.create("Porca", t0, t1, cycle_number=1, was_forced=False)
    assert event.duration == timedelta(seconds=5)


def test_create_fields():
    t0 = datetime(2024, 1, 1)
    t1 = t0 + timedelta(seconds=10)
    event = TaskEvent.create("Montagem", t0, t1, cycle_number=3, was_forced=True)
    assert event.zone_name == "Montagem"
    assert event.cycle_number == 3
    assert event.was_forced is True
    assert event.start_time == t0
    assert event.end_time == t1


def test_immutable():
    t0 = datetime(2024, 1, 1)
    t1 = t0 + timedelta(seconds=1)
    event = TaskEvent.create("Porca", t0, t1, 1, False)
    import pytest
    with pytest.raises(Exception):
        event.zone_name = "Outro"
