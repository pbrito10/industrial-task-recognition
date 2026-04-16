"""Testes para src/roi/json_roi_repository.py"""
import pytest
from pathlib import Path
from src.roi.json_roi_repository import JsonRoiRepository
from src.roi.region_of_interest import RegionOfInterest
from src.roi.roi_collection import RoiCollection
from src.shared.point import Point


def _collection_com_zonas() -> RoiCollection:
    col = RoiCollection()
    col.add(RegionOfInterest("Porca", Point(0, 0), Point(100, 100)))
    col.add(RegionOfInterest("Montagem", Point(200, 0), Point(300, 100)))
    return col


# -- save / load --------------------------------------------------------------

def test_save_e_load_roundtrip(tmp_path):
    # tmp_path é um diretório temporário criado pelo pytest
    path = tmp_path / "rois.json"
    repo = JsonRoiRepository(path)
    repo.save(_collection_com_zonas())
    loaded = repo.load()
    assert len(loaded.all()) == 2

def test_load_ficheiro_inexistente_devolve_vazio(tmp_path):
    path = tmp_path / "nao_existe.json"
    repo = JsonRoiRepository(path)
    assert repo.load().is_empty()

def test_nomes_preservados_apos_roundtrip(tmp_path):
    pass
