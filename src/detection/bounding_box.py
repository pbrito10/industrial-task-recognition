from __future__ import annotations
from dataclasses import dataclass

from src.shared.point import Point


@dataclass(frozen=True)
class BoundingBox:
    """Retângulo envolvente de uma mão detetada.

    Definido por dois pontos em vez de quatro ints soltos,
    tornando explícito que formam um retângulo.
    """

    top_left: Point
    bottom_right: Point

    def center(self) -> Point:
        """Ponto central do retângulo, calculado como média dos dois cantos.

        Não é usado pelo ZoneClassifier (que usa finger_mcp_centroid).
        Disponível para consumidores externos que precisem do centro geométrico da bbox.
        """
        raise NotImplementedError

    def area(self) -> int:
        """Área do retângulo em píxeis quadrados (largura × altura).

        Atualmente não usado pelo pipeline — disponível para análises externas
        ou para filtrar deteções por tamanho mínimo da mão.
        """
        raise NotImplementedError

    def contains(self, point: Point) -> bool:
        """Verifica se um ponto está dentro do retângulo."""
        raise NotImplementedError
