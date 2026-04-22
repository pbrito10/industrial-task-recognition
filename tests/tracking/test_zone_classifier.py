import pytest
from tests.conftest import make_hand, make_roi
from src.roi.roi_collection import RoiCollection
from src.shared.hand_side import HandSide
from src.tracking.zone_classifier import ZoneClassifier


@pytest.fixture
def classifier():
    rois = RoiCollection()
    rois.add(make_roi("Porca",    0,   0,  100, 100))
    rois.add(make_roi("Montagem", 200, 200, 400, 400))
    return ZoneClassifier(rois)


def test_hand_in_zone(classifier):
    # MCP centróide em (50,50) → dentro de Porca
    hand = make_hand(mcp=(50, 50))
    results = classifier.classify([hand])
    assert len(results) == 1
    _, zone = results[0]
    assert zone is not None
    assert zone.name == "Porca"


def test_hand_outside_all_zones(classifier):
    hand = make_hand(mcp=(150, 150))
    _, zone = classifier.classify([hand])[0]
    assert zone is None


def test_two_hands_different_zones(classifier):
    h1 = make_hand(mcp=(50, 50),   side=HandSide.RIGHT)
    h2 = make_hand(mcp=(300, 300), side=HandSide.LEFT)
    results = classifier.classify([h1, h2])
    zones = {zone.name for _, zone in results if zone}
    assert zones == {"Porca", "Montagem"}


def test_empty_detections(classifier):
    assert classifier.classify([]) == []
