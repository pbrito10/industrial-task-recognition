from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """Par de coordenadas (x, y) em píxeis num frame de vídeo.

    Imutável — garante que nenhum código altera acidentalmente
    uma posição que já foi calculada.
    """

    x: int
    y: int

    def distance_to(self, other: Point) -> float:
        """Distância euclidiana até outro ponto — útil para filtros de ruído."""
        raise NotImplementedError
