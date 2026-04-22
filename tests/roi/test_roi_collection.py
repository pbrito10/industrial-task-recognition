import pytest
from tests.conftest import make_roi
from src.roi.roi_collection import RoiCollection
from src.shared.point import Point


@pytest.fixture
def collection():
    c = RoiCollection()
    c.add(make_roi("Porca",     0,   0,  100, 100))
    c.add(make_roi("Montagem", 200, 200, 400, 400))
    return c


def test_initially_empty():
    assert RoiCollection().is_empty()


def test_add_and_contains(collection):
    assert collection.contains("Porca")
    assert collection.contains("Montagem")


def test_add_overwrites_same_name():
    c = RoiCollection()
    c.add(make_roi("Porca", 0, 0, 50, 50))
    c.add(make_roi("Porca", 10, 10, 90, 90))
    assert c.get("Porca").top_left == Point(10, 10)


def test_remove_existing(collection):
    collection.remove("Porca")
    assert not collection.contains("Porca")


def test_remove_nonexistent_is_safe(collection):
    collection.remove("NaoExiste")  # não deve lançar


def test_find_zone_for_point_match(collection):
    zone = collection.find_zone_for_point(Point(50, 50))
    assert zone is not None
    assert zone.name == "Porca"


def test_find_zone_for_point_no_match(collection):
    assert collection.find_zone_for_point(Point(500, 500)) is None


def test_find_returns_first_match():
    c = RoiCollection()
    c.add(make_roi("A", 0, 0, 100, 100))
    c.add(make_roi("B", 0, 0, 100, 100))  # sobreposição total
    assert c.find_zone_for_point(Point(50, 50)).name == "A"


def test_get_returns_none_for_missing(collection):
    assert collection.get("NaoExiste") is None


def test_all_returns_all(collection):
    names = {roi.name for roi in collection.all()}
    assert names == {"Porca", "Montagem"}
