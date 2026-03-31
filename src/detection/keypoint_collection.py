from __future__ import annotations
from dataclasses import dataclass, field

from src.detection.keypoint import Keypoint
from src.shared.point import Point

# Índices das pontas de dedo segundo a convenção MediaPipe
_FINGERTIP_INDICES = [4, 8, 12, 16, 20]

# Índices dos MCP (metacarpofalângicas) dos 4 dedos — excluindo o polegar.
# Os MCP são os nós na base dos dedos, sobre a palma.
# Excluímos o polegar (MCP = índice 2) porque se move num plano diferente
# dos restantes e introduziria desvio lateral no centróide.
_FINGER_MCP_INDICES = [5, 9, 13, 17]
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

    def finger_mcp_centroid(self) -> Point:
        """Centro geométrico dos MCP dos 4 dedos (índice, médio, anelar, mindinho).

        Ponto de referência preferido para classificação de zonas neste sistema.

        Porquê MCP e não pulso, fingertips ou centróide geral?
          - Pulso: demasiado afastado da peça — pode estar fora da caixa
            enquanto os dedos já estão dentro.
          - Fingertips: movem-se significativamente durante o grasping
            (mão a fechar), tornando o ponto instável exatamente quando
            interessa saber que a mão está a pegar.
          - Centróide dos 21: influenciado pelo pulso e pelos dedos,
            menos preciso para localizar "onde a mão está a trabalhar".
          - MCP dos 4 dedos: ficam na palma, sobre a zona de trabalho,
            e não se deslocam ao abrir/fechar a mão — o ponto mantém-se
            estável independentemente do estado do grasping.

        Caso de uso típico: operador estica o braço para uma caixa,
        o pulso fica fora da ROI mas os MCP estão dentro — a zona é
        corretamente detetada.
        """
        mcps  = [self._keypoints[i] for i in _FINGER_MCP_INDICES]
        avg_x = sum(kp.position.x for kp in mcps) // len(_FINGER_MCP_INDICES)
        avg_y = sum(kp.position.y for kp in mcps) // len(_FINGER_MCP_INDICES)
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
