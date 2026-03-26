from __future__ import annotations
from dataclasses import dataclass

from src.shared.point import Point


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
            "name": self.name,
            "x1": self.top_left.x,
            "y1": self.top_left.y,
            "x2": self.bottom_right.x,
            "y2": self.bottom_right.y,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RegionOfInterest:
        """Reconstrói um RegionOfInterest a partir de um dict JSON."""
        return cls(
            name=data["name"],
            top_left=Point(x=data["x1"], y=data["y1"]),
            bottom_right=Point(x=data["x2"], y=data["y2"]),
        )
