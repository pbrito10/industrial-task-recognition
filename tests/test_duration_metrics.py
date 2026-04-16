"""Testes para src/metrics/_duration_metrics.py (via TaskMetrics)"""
from datetime import timedelta
import pytest
from src.metrics.task_metrics import TaskMetrics


def _segundos(s: float) -> timedelta:
    return timedelta(seconds=s)


# -- count --------------------------------------------------------------------

def test_count_inicial_zero():
    pass

def test_count_apos_adicionar():
    pass


# -- minimum / maximum --------------------------------------------------------

def test_minimum():
    pass

def test_maximum():
    pass


# -- average ------------------------------------------------------------------

def test_average_unico_valor():
    pass

def test_average_varios_valores():
    pass


# -- std_deviation ------------------------------------------------------------

def test_std_deviation_um_valor_e_zero():
    pass

def test_std_deviation_dois_valores_iguais_e_zero():
    pass

def test_std_deviation_valores_diferentes():
    pass
