from __future__ import annotations

from src.roi.region_of_interest import RegionOfInterest
from src.shared.point import Point


class RoiCollection:
    """First-class collection das zonas de trabalho (OC).

    Usa dict internamente (keyed por nome) para lookup O(1).
    Mutável durante a sessão de desenho; imutável durante análise.
    """

    def __init__(self) -> None:
        self._rois: dict[str, RegionOfInterest] = {}

    def add(self, roi: RegionOfInterest) -> None:
        """Adiciona ou substitui uma zona pelo nome."""
        self._rois[roi.name] = roi

    def remove(self, name: str) -> None:
        """Remove uma zona por nome — silencioso se não existir."""
        self._rois.pop(name, None)

    def find_zone_for_point(self, point: Point) -> RegionOfInterest | None:
        """Devolve a primeira zona que contém o ponto, ou None."""
        for roi in self._rois.values():
            if roi.contains(point):
                return roi
        return None

    def get(self, name: str) -> RegionOfInterest | None:
        """Devolve a zona com o nome dado, ou None."""
        return self._rois.get(name)

    def contains(self, name: str) -> bool:
        """Indica se existe uma zona com este nome na coleção."""
        return name in self._rois

    def is_empty(self) -> bool:
        return len(self._rois) == 0

    def all(self) -> list[RegionOfInterest]:
        return list(self._rois.values())
