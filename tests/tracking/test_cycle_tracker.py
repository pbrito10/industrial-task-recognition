"""Testes para src/tracking/cycle_tracker.py"""
import pytest
from datetime import datetime, timedelta
from src.tracking.cycle_tracker import CycleTracker, _matches_order
from src.tracking.task_event import TaskEvent

ORDER = ["Porca", "Montagem", "Chassi", "Saida"]
T0    = datetime(2026, 1, 1, 10, 0, 0)


def _event(zone: str, start_s: float, end_s: float, forced: bool = False) -> TaskEvent:
    return TaskEvent.create(
        zone_name=zone,
        start_time=T0 + timedelta(seconds=start_s),
        end_time=T0 + timedelta(seconds=end_s),
        cycle_number=1,
        was_forced=forced,
    )


# -- _matches_order -----------------------------------------------------------

def test_ordem_correta():
    assert _matches_order(["Porca", "Montagem", "Chassi", "Saida"], ORDER) is True

def test_ordem_errada():
    assert _matches_order(["Montagem", "Porca", "Chassi", "Saida"], ORDER) is False

def test_repeticao_consecutiva_permitida():
    # visitar a mesma zona várias vezes antes de avançar é permitido
    assert _matches_order(["Porca", "Porca", "Montagem", "Chassi", "Saida"], ORDER) is True

def test_saltar_zona_invalido():
    assert _matches_order(["Porca", "Chassi", "Saida"], ORDER) is False

def test_lista_vazia_false():
    assert _matches_order([], ORDER) is False


# -- CycleTracker.record ------------------------------------------------------

def test_ciclo_completo_fecha():
    pass

def test_ciclo_incompleto_nao_fecha():
    pass

def test_timeout_nao_fecha_ciclo():
    # was_forced=True na zona de saída não deve fechar o ciclo
    pass

def test_ciclo_fora_de_ordem_marca_sequence_in_order_false():
    pass

def test_current_cycle_number_incrementa_apos_ciclo():
    pass
