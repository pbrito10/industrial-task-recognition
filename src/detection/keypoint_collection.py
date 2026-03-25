from __future__ import annotations
from dataclasses import dataclass, field

from src.detection.keypoint import Keypoint
from src.shared.point import Point

# Índices das pontas de dedo segundo a convenção MediaPipe
_FINGERTIP_INDICES = [4, 8, 12, 16, 20]
_EXPECTED_COUNT = 21


@dataclass(frozen=True)
class KeypointCollection:
    """First-class collection dos 21 keypoints de uma mão.

    Encapsula a lista e centraliza as operações sobre ela —
    evita que código externo itere ou indexe diretamente.
    """

    _keypoints: list[Keypoint] = field(repr=False)

    def __post_init__(self) -> None:
        if len(self._keypoints) != _EXPECTED_COUNT:
            raise ValueError(
                f"KeypointCollection exige {_EXPECTED_COUNT} keypoints, "
                f"recebidos {len(self._keypoints)}"
            )

    def wrist(self) -> Keypoint:
        """Pulso (índice 0) — ponto de referência mais estável da mão."""
        return self._keypoints[0]

    def centroid(self) -> Point:
        """Centro geométrico dos 21 pontos — mais robusto que o pulso em posições extremas."""
        avg_x = sum(kp.position.x for kp in self._keypoints) // _EXPECTED_COUNT
        avg_y = sum(kp.position.y for kp in self._keypoints) // _EXPECTED_COUNT
        return Point(x=avg_x, y=avg_y)

    def fingertips(self) -> list[Keypoint]:
        """As 5 pontas de dedo (índices 4, 8, 12, 16, 20)."""
        return [self._keypoints[i] for i in _FINGERTIP_INDICES]

    def by_index(self, index: int) -> Keypoint:
        """Acesso por índice (0–20) com validação."""
        if not (0 <= index < _EXPECTED_COUNT):
            raise ValueError(f"Índice de keypoint inválido: {index} (deve ser 0–20)")
        return self._keypoints[index]

    def all(self) -> list[Keypoint]:
        """Devolve todos os keypoints — usado para desenhar ou iterar externamente."""
        return list(self._keypoints)
