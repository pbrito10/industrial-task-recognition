from __future__ import annotations
from dataclasses import dataclass

from src.detection.bounding_box import BoundingBox
from src.detection.keypoint import Keypoint
from src.detection.keypoint_collection import KeypointCollection
from src.shared.confidence import Confidence
from src.shared.hand_side import HandSide
from src.shared.point import Point


@dataclass(frozen=True)
class HandDetection:
    """Todos os dados de uma mão detetada num frame.

    Agrupa keypoints, bounding box, confiança e lado numa estrutura
    imutável — o detector produz-a, o resto do sistema consome-a.
    """

    keypoints: KeypointCollection
    bounding_box: BoundingBox
    confidence: Confidence
    hand_side: HandSide

    # Atalhos que delegam na KeypointCollection para não forçar
    # o código externo a aceder sempre a .keypoints.xxx

    def centroid(self) -> Point:
        """Centro geométrico dos 21 keypoints."""
        return self.keypoints.centroid()

    def wrist(self) -> Keypoint:
        """Pulso — ponto de referência principal da mão."""
        return self.keypoints.wrist()
