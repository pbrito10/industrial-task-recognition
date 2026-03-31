from __future__ import annotations

from src.detection.hand_detection import HandDetection
from src.roi.region_of_interest import RegionOfInterest
from src.roi.roi_collection import RoiCollection

# Par (deteção, zona) — zona é None se a mão estiver em trânsito
ClassifiedHand = tuple[HandDetection, RegionOfInterest | None]


class ZoneClassifier:
    """Mapeia cada mão detetada para a zona em que se encontra.

    Reporta apenas o que vê — não interpreta nem acumula estado.
    Dois resultados None num frame significa duas mãos em trânsito;
    interpretar isso é responsabilidade da TaskStateMachine.
    """

    def __init__(self, rois: RoiCollection) -> None:
        self._rois = rois

    def classify(self, detections: list[HandDetection]) -> list[ClassifiedHand]:
        """Devolve cada deteção emparelhada com a sua zona (ou None)."""
        return [self._classify_one(detection) for detection in detections]

    def _classify_one(self, detection: HandDetection) -> ClassifiedHand:
        """Localiza a mão usando o centro da bounding box."""
        point = detection.bounding_box.center()
        zone  = self._rois.find_zone_for_point(point)
        return detection, zone
