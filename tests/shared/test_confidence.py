"""Testes para src/shared/confidence.py"""
import pytest
from src.shared.confidence import Confidence


# -- validação no construtor --------------------------------------------------

def test_valor_valido():
    # deve criar sem erro
    pass

def test_valor_zero_valido():
    pass

def test_valor_um_valido():
    pass

def test_valor_negativo_invalido():
    # deve lançar ValueError
    pass

def test_valor_acima_de_um_invalido():
    pass


# -- is_above -----------------------------------------------------------------

def test_is_above_true():
    pass

def test_is_above_false():
    pass

def test_is_above_igual_ao_threshold():
    # igual deve ser True (>=)
    pass


# -- as_percentage ------------------------------------------------------------

def test_as_percentage():
    # 0.87 → 87.0
    pass
