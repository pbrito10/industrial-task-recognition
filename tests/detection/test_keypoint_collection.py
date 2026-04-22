import pytest
from tests.conftest import make_keypoint_list
from src.detection.keypoint_collection import KeypointCollection
from src.detection.keypoint import Keypoint
from src.shared.confidence import Confidence
from src.shared.point import Point


def test_wrong_count_raises():
    with pytest.raises(ValueError):
        KeypointCollection([])


def test_wrong_count_20_raises():
    kps = make_keypoint_list()[:20]
    with pytest.raises(ValueError):
        KeypointCollection(kps)


def test_wrist_is_index_0():
    kps = make_keypoint_list(wrist=(100, 200))
    col = KeypointCollection(kps)
    assert col.wrist().position == Point(100, 200)


def test_finger_mcp_centroid_uses_mcp_positions():
    # MCPs em (100,100), pulso em (0,0) — o centróide deve ser (100,100)
    kps = make_keypoint_list(wrist=(0, 0), mcp=(100, 100))
    col = KeypointCollection(kps)
    centroid = col.finger_mcp_centroid()
    assert centroid == Point(100, 100)


def test_centroid_all_same():
    kps = [
        Keypoint(index=i, position=Point(10, 20), confidence=Confidence(0.9))
        for i in range(21)
    ]
    col = KeypointCollection(kps)
    assert col.centroid() == Point(10, 20)


def test_fingertips_returns_5():
    kps = make_keypoint_list()
    col = KeypointCollection(kps)
    tips = col.fingertips()
    assert len(tips) == 5
    assert {kp.index for kp in tips} == {4, 8, 12, 16, 20}


def test_by_index_valid():
    kps = make_keypoint_list(wrist=(7, 8))
    col = KeypointCollection(kps)
    assert col.by_index(0).position == Point(7, 8)


def test_by_index_invalid():
    kps = make_keypoint_list()
    col = KeypointCollection(kps)
    with pytest.raises(ValueError):
        col.by_index(21)
    with pytest.raises(ValueError):
        col.by_index(-1)


def test_all_returns_21():
    kps = make_keypoint_list()
    col = KeypointCollection(kps)
    assert len(col.all()) == 21
