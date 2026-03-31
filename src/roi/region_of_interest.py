from __future__ import annotations
from dataclasses import dataclass

from src.shared.point import Point

# Chaves do formato JSON — constantes para evitar magic strings em to_dict/from_dict
_KEY_NAME = "name"
_KEY_X1   = "x1"
_KEY_Y1   = "y1"
_KEY_X2   = "x2"
_KEY_Y2   = "y2"


@dataclass(frozen=True)
class RegionOfInterest:
    """Zona de trabalho retangular na bancada — imutável após criação.

    O nome vem sempre do settings.yaml (via RoiDrawer), nunca de input livre,
    garantindo consistência com o cycle_zone_order.
    """

    name: str
    top_left: Point
    bottom_right: Point

    def contains(self, point: Point) -> bool:
        """Diz se um ponto está dentro da zona — usado frame a frame pelo ZoneClassifier."""
        return (
            self.top_left.x <= point.x <= self.bottom_right.x
            and self.top_left.y <= point.y <= self.bottom_right.y
        )

    def to_dict(self) -> dict:
        """Serialização para JSON — coordenadas como ints simples para legibilidade."""
        return {
            _KEY_NAME: self.name,
            _KEY_X1:   self.top_left.x,
            _KEY_Y1:   self.top_left.y,
            _KEY_X2:   self.bottom_right.x,
            _KEY_Y2:   self.bottom_right.y,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RegionOfInterest:
        """Reconstrói um RegionOfInterest a partir de um dict JSON."""
        return cls(
            name=data[_KEY_NAME],
            top_left=Point(x=data[_KEY_X1], y=data[_KEY_Y1]),
            bottom_right=Point(x=data[_KEY_X2], y=data[_KEY_Y2]),
        )
