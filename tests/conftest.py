from __future__ import annotations

from src.detection.bounding_box import BoundingBox
from src.detection.hand_detection import HandDetection
from src.detection.keypoint import Keypoint
from src.detection.keypoint_collection import KeypointCollection
from src.roi.region_of_interest import RegionOfInterest
from src.shared.confidence import Confidence
from src.shared.hand_side import HandSide
from src.shared.point import Point

_CONF = Confidence(0.9)

# Índices dos MCP dos 4 dedos usados em finger_mcp_centroid()
_MCP_INDICES = {5, 9, 13, 17}


def make_keypoint_list(
    wrist: tuple[int, int] = (0, 0),
    mcp: tuple[int, int] | None = None,
) -> list[Keypoint]:
    """21 keypoints com pulso e MCPs em posições controláveis; resto em (0,0)."""
    mcp_pos = mcp if mcp is not None else wrist
    return [
        Keypoint(
            index=i,
            position=Point(*mcp_pos) if i in _MCP_INDICES else Point(*wrist) if i == 0 else Point(0, 0),
            confidence=_CONF,
        )
        for i in range(21)
    ]


def make_hand(
    wrist: tuple[int, int] = (50, 50),
    mcp: tuple[int, int] | None = None,
    side: HandSide = HandSide.RIGHT,
) -> HandDetection:
    """HandDetection com pulso e centróide MCP em posições controláveis."""
    kps = make_keypoint_list(wrist, mcp)
    col = KeypointCollection(kps)
    return HandDetection(
        keypoints=col,
        bounding_box=BoundingBox(top_left=Point(0, 0), bottom_right=Point(10, 10)),
        confidence=_CONF,
        hand_side=side,
    )


def make_roi(name: str, x1: int, y1: int, x2: int, y2: int) -> RegionOfInterest:
    return RegionOfInterest(
        name=name,
        top_left=Point(x1, y1),
        bottom_right=Point(x2, y2),
    )
