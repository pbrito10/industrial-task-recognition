import json
import pytest
from tests.conftest import make_roi
from src.roi.json_roi_repository import JsonRoiRepository
from src.roi.roi_collection import RoiCollection


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "rois.json"
    repo = JsonRoiRepository(path)

    col = RoiCollection()
    col.add(make_roi("Porca",    10, 10, 100, 100))
    col.add(make_roi("Montagem", 200, 200, 400, 400))

    repo.save(col)
    loaded = repo.load()

    assert loaded.contains("Porca")
    assert loaded.contains("Montagem")
    assert loaded.get("Porca").top_left.x == 10


def test_load_missing_file_returns_empty(tmp_path):
    repo = JsonRoiRepository(tmp_path / "nao_existe.json")
    col = repo.load()
    assert col.is_empty()


def test_save_creates_valid_json(tmp_path):
    path = tmp_path / "rois.json"
    repo = JsonRoiRepository(path)

    col = RoiCollection()
    col.add(make_roi("Zona", 5, 5, 50, 50))
    repo.save(col)

    data = json.loads(path.read_text())
    assert isinstance(data, list)
    assert data[0]["name"] == "Zona"


def test_save_empty_collection(tmp_path):
    path = tmp_path / "rois.json"
    repo = JsonRoiRepository(path)
    repo.save(RoiCollection())
    loaded = repo.load()
    assert loaded.is_empty()


def test_load_preserves_coordinates(tmp_path):
    path = tmp_path / "rois.json"
    repo = JsonRoiRepository(path)

    col = RoiCollection()
    col.add(make_roi("Saida", 300, 400, 500, 600))
    repo.save(col)

    loaded = repo.load()
    roi = loaded.get("Saida")
    assert roi.top_left.x == 300
    assert roi.top_left.y == 400
    assert roi.bottom_right.x == 500
    assert roi.bottom_right.y == 600
