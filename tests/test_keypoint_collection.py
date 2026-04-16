"""Testes para src/detection/keypoint_collection.py"""
import pytest
from src.detection.keypoint_collection import KeypointCollection
from src.detection.keypoint import Keypoint
from src.shared.point import Point
from src.shared.confidence import Confidence


def _make_keypoints(n: int = 21) -> list[Keypoint]:
    """Helper: cria n keypoints com posições simples para testes."""
    conf = Confidence(0.9)
    return [Keypoint(index=i, position=Point(i * 10, i * 10), confidence=conf) for i in range(n)]


# -- validação no construtor --------------------------------------------------

def test_numero_correto_de_keypoints():
    pass

def test_numero_errado_lanca_erro():
    # menos de 21 deve lançar ValueError
    pass


# -- wrist --------------------------------------------------------------------

def test_wrist_e_indice_zero():
    pass


# -- centroid -----------------------------------------------------------------

def test_centroid_pontos_simetricos():
    pass


# -- finger_mcp_centroid ------------------------------------------------------

def test_finger_mcp_centroid_usa_indices_corretos():
    # deve usar índices 5, 9, 13, 17
    pass


# -- by_index -----------------------------------------------------------------

def test_by_index_valido():
    pass

def test_by_index_invalido_lanca_erro():
    pass
