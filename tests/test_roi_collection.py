"""Testes para src/roi/roi_collection.py"""
from src.roi.region_of_interest import RegionOfInterest
from src.roi.roi_collection import RoiCollection
from src.shared.point import Point


def _roi(name, x1=0, y1=0, x2=100, y2=100) -> RegionOfInterest:
    return RegionOfInterest(name=name, top_left=Point(x1, y1), bottom_right=Point(x2, y2))


# -- add / all / is_empty -----------------------------------------------------

def test_collection_vazia():
    pass

def test_add_uma_zona():
    pass

def test_add_substitui_zona_com_mesmo_nome():
    pass


# -- remove -------------------------------------------------------------------

def test_remove_zona_existente():
    pass

def test_remove_zona_inexistente_nao_falha():
    pass


# -- find_zone_for_point ------------------------------------------------------

def test_find_ponto_dentro_de_zona():
    pass

def test_find_ponto_fora_de_todas_as_zonas():
    pass

def test_find_ponto_em_zona_sobreposta_devolve_primeira():
    pass


# -- contains / get -----------------------------------------------------------

def test_contains_zona_existente():
    pass

def test_contains_zona_inexistente():
    pass
