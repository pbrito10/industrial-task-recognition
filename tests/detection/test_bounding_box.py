import pytest
from src.detection.bounding_box import BoundingBox
from src.shared.point import Point


@pytest.fixture
def box():
    return BoundingBox(top_left=Point(10, 20), bottom_right=Point(50, 60))


def test_center(box):
    c = box.center()
    assert c == Point(30, 40)


def test_area(box):
    # (50-10) * (60-20) = 40 * 40 = 1600
    assert box.area() == 1600


def test_area_zero_width():
    b = BoundingBox(top_left=Point(5, 5), bottom_right=Point(5, 10))
    assert b.area() == 0


def test_contains_inside(box):
    assert box.contains(Point(30, 40))


def test_contains_on_border(box):
    assert box.contains(Point(10, 20))
    assert box.contains(Point(50, 60))


def test_contains_outside(box):
    assert not box.contains(Point(5, 5))
    assert not box.contains(Point(100, 100))
