"""Testes para src/roi/region_of_interest.py"""
from src.roi.region_of_interest import RegionOfInterest
from src.shared.point import Point


def _roi(name="Zona A", x1=0, y1=0, x2=100, y2=100) -> RegionOfInterest:
    return RegionOfInterest(name=name, top_left=Point(x1, y1), bottom_right=Point(x2, y2))


# -- contains -----------------------------------------------------------------

def test_contains_ponto_dentro():
    pass

def test_contains_ponto_fora():
    pass

def test_contains_ponto_na_borda():
    pass


# -- to_dict / from_dict ------------------------------------------------------

def test_to_dict_tem_campos_esperados():
    pass

def test_from_dict_reconstroi_corretamente():
    pass

def test_roundtrip_to_dict_from_dict():
    # to_dict seguido de from_dict deve devolver ROI equivalente
    pass
