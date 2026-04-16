from __future__ import annotations
from dataclasses import dataclass

from src.shared.point import Point

# Chaves do JSON — definidas aqui para que from_dict e to_dict usem a mesma fonte
_KEY_NAME = "name"
_KEY_X1   = "x1"
_KEY_Y1   = "y1"
_KEY_X2   = "x2"
_KEY_Y2   = "y2"


@dataclass(frozen=True)
class RegionOfInterest:
    """Zona retangular na bancada, identificada por nome.

    O nome vem sempre do settings.yaml (via RoiDrawer), nunca de input livre,
    o que garante consistência com cycle_zone_order e two_hands_zones.
    """

    name: str
    top_left: Point
    bottom_right: Point

    def contains(self, point: Point) -> bool:
        """True se o ponto está dentro dos limites da zona."""
        raise NotImplementedError

    def to_dict(self) -> dict:
        """Serializa para o formato JSON de persistência."""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict) -> RegionOfInterest:
        """Constrói uma RegionOfInterest a partir de um dict carregado do JSON."""
        raise NotImplementedError
