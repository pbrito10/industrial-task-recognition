import pytest
from src.shared.confidence import Confidence


def test_valid_boundaries():
    Confidence(0.0)
    Confidence(1.0)
    Confidence(0.5)


def test_invalid_below():
    with pytest.raises(ValueError):
        Confidence(-0.01)


def test_invalid_above():
    with pytest.raises(ValueError):
        Confidence(1.01)


def test_is_above_true():
    assert Confidence(0.8).is_above(Confidence(0.7))


def test_is_above_equal():
    assert Confidence(0.7).is_above(Confidence(0.7))


def test_is_above_false():
    assert not Confidence(0.6).is_above(Confidence(0.7))


def test_as_percentage():
    assert Confidence(0.87).as_percentage() == pytest.approx(87.0)


def test_as_percentage_extremes():
    assert Confidence(0.0).as_percentage() == pytest.approx(0.0)
    assert Confidence(1.0).as_percentage() == pytest.approx(100.0)
