"""Testes para src/tracking/task_event.py"""
import pytest
from datetime import datetime, timedelta
from src.tracking.task_event import TaskEvent

T0 = datetime(2026, 1, 1, 10, 0, 0)


# -- create -------------------------------------------------------------------

def test_create_calcula_duracao():
    event = TaskEvent.create("Porca", T0, T0 + timedelta(seconds=5), 1, False)
    assert event.duration == timedelta(seconds=5)

def test_create_end_antes_de_start_invalido():
    with pytest.raises(ValueError):
        TaskEvent.create("Porca", T0 + timedelta(seconds=5), T0, 1, False)

def test_create_guarda_todos_os_campos():
    pass

def test_was_forced_true():
    pass
