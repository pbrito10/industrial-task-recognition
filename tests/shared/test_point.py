import math
import pytest
from src.shared.point import Point


def test_distance_same_point():
    p = Point(3, 4)
    assert p.distance_to(p) == 0.0


def test_distance_horizontal():
    assert Point(0, 0).distance_to(Point(5, 0)) == pytest.approx(5.0)


def test_distance_vertical():
    assert Point(0, 0).distance_to(Point(0, 3)) == pytest.approx(3.0)


def test_distance_diagonal():
    # 3-4-5 triangle
    assert Point(0, 0).distance_to(Point(3, 4)) == pytest.approx(5.0)


def test_distance_symmetric():
    a, b = Point(10, 20), Point(30, 5)
    assert a.distance_to(b) == pytest.approx(b.distance_to(a))


def test_immutable():
    p = Point(1, 2)
    with pytest.raises(Exception):
        p.x = 99
