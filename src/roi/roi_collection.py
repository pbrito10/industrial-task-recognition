from __future__ import annotations

from src.roi.region_of_interest import RegionOfInterest
from src.shared.point import Point


class RoiCollection:
    """Coleção de zonas de trabalho com lookup O(1) por nome.

    Mutável durante a sessão de desenho (RoiDrawer adiciona e remove zonas).
    Durante a análise, depois de carregada do JSON, não é modificada.
    """

    def __init__(self) -> None:
        self._rois: dict[str, RegionOfInterest] = {}

    def add(self, roi: RegionOfInterest) -> None:
        """Adiciona ou substitui uma zona — uma zona por nome."""
        self._rois[roi.name] = roi

    def remove(self, name: str) -> None:
        self._rois.pop(name, None)

    def find_zone_for_point(self, point: Point) -> RegionOfInterest | None:
        """Primeira zona que contém o ponto, ou None. Ordem = ordem de inserção."""
        for roi in self._rois.values():
            if roi.contains(point):
                return roi
        return None

    def get(self, name: str) -> RegionOfInterest | None:
        return self._rois.get(name)

    def contains(self, name: str) -> bool:
        return name in self._rois

    def is_empty(self) -> bool:
        return len(self._rois) == 0

    def all(self) -> list[RegionOfInterest]:
        return list(self._rois.values())
