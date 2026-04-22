import pytest
from src.roi.region_of_interest import RegionOfInterest
from src.shared.point import Point


@pytest.fixture
def roi():
    return RegionOfInterest(
        name="Porca",
        top_left=Point(10, 10),
        bottom_right=Point(100, 100),
    )


def test_contains_inside(roi):
    assert roi.contains(Point(50, 50))


def test_contains_on_border(roi):
    assert roi.contains(Point(10, 10))
    assert roi.contains(Point(100, 100))


def test_contains_outside(roi):
    assert not roi.contains(Point(5, 5))
    assert not roi.contains(Point(200, 50))


def test_to_dict(roi):
    d = roi.to_dict()
    assert d["name"] == "Porca"
    assert d["x1"] == 10
    assert d["y1"] == 10
    assert d["x2"] == 100
    assert d["y2"] == 100


def test_from_dict_round_trip(roi):
    restored = RegionOfInterest.from_dict(roi.to_dict())
    assert restored == roi
