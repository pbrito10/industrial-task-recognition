"""Testes para src/metrics/cycle_metrics.py"""
from datetime import timedelta
from src.metrics.cycle_metrics import CycleMetrics


def _s(seconds: float) -> timedelta:
    return timedelta(seconds=seconds)


def test_count_inicial_zero():
    pass

def test_add_incrementa_count():
    pass

def test_count_in_order():
    pass

def test_count_out_of_order():
    pass

def test_in_order_mais_out_of_order_igual_count():
    # invariante: in_order + out_of_order == count
    pass
