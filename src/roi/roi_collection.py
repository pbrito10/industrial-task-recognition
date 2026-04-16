from __future__ import annotations

from src.roi.region_of_interest import RegionOfInterest
from src.shared.point import Point


class RoiCollection:
    """Coleção de zonas de trabalho com lookup O(1) por nome.

    Mutável durante a sessão de desenho (RoiDrawer adiciona e remove zonas).
    Durante a análise, depois de carregada do JSON, não é modificada.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    def add(self, roi: RegionOfInterest) -> None:
        """Adiciona ou substitui uma zona — uma zona por nome."""
        raise NotImplementedError

    def remove(self, name: str) -> None:
        raise NotImplementedError

    def find_zone_for_point(self, point: Point) -> RegionOfInterest | None:
        """Primeira zona que contém o ponto, ou None. Ordem = ordem de inserção."""
        raise NotImplementedError

    def get(self, name: str) -> RegionOfInterest | None:
        """Devolve a zona com o nome indicado, ou None se não existir."""
        raise NotImplementedError

    def contains(self, name: str) -> bool:
        """True se existe uma zona com este nome na coleção."""
        raise NotImplementedError

    def is_empty(self) -> bool:
        """True se a coleção não tem nenhuma zona definida."""
        raise NotImplementedError

    def all(self) -> list[RegionOfInterest]:
        """Devolve todas as zonas por ordem de inserção."""
        raise NotImplementedError
