"""Testes para src/tracking/activation_strategy.py"""
from src.tracking.activation_strategy import TimeDwellStrategy, StillnessDwellStrategy


# -- TimeDwellStrategy --------------------------------------------------------

def test_time_dwell_sempre_ativo():
    # TimeDwellStrategy deve devolver True independentemente da deteção
    pass


# -- StillnessDwellStrategy ---------------------------------------------------

def test_stillness_sem_frame_anterior_e_false():
    # primeiro frame sem referência anterior → False
    pass

def test_stillness_mao_parada_e_true():
    # velocidade < threshold → True
    pass

def test_stillness_mao_em_movimento_e_false():
    # velocidade >= threshold → False
    pass
