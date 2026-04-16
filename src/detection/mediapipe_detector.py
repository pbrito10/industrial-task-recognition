from __future__ import annotations

import time

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from src.detection.bounding_box import BoundingBox
from src.detection.detector_interface import DetectorInterface
from src.detection.hand_detection import HandDetection
from src.detection.keypoint import Keypoint
from src.detection.keypoint_collection import KeypointCollection
from src.shared.confidence import Confidence
from src.shared.hand_side import HandSide
from src.shared.point import Point

# Margem adicionada à bounding box calculada a partir dos landmarks, em píxeis
_BOUNDING_BOX_MARGIN_PX = 10

# Dict de mapeamento evita um if/elif por cada label que a API possa devolver
_HAND_SIDE_MAP: dict[str, HandSide] = {
    "Left": HandSide.LEFT,
    "Right": HandSide.RIGHT,
}


class MediapipeDetector(DetectorInterface):
    """Detector de mãos via MediaPipe Tasks API (HandLandmarker).

    Usa o modo VIDEO porque o pipeline processa frames de forma síncrona e sequencial.
    O modo LIVE_STREAM seria assíncrono (callbacks), o que complicaria a pipeline.
    O modo IMAGE trata cada frame como independente e perde o benefício do tracking.

    VIDEO requer timestamps em milissegundos monotonicamente crescentes —
    usamos time.monotonic() e não datetime.now() para garantir isso mesmo
    quando o relógio do sistema é ajustado.
    """

    def __init__(
        self,
        model_path: str,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.7,
    ) -> None:
        raise NotImplementedError

    def detect(self, frame: np.ndarray) -> list[HandDetection]:
        """Processa um frame RGB e devolve as mãos detetadas.

        Recebe: frame em RGB (convertido em capture_process antes de entrar na queue).
        Devolve: lista de HandDetection, uma por mão; lista vazia se nenhuma for detetada.
        """
        raise NotImplementedError

    def _build_detection(self, landmarks, handedness, width: int, height: int) -> HandDetection:
        """Converte a saída bruta do MediaPipe num HandDetection do domínio.

        Extrai confiança e lado do objeto handedness, constrói os keypoints
        em píxeis e calcula a bounding box a partir dos landmarks.
        """
        raise NotImplementedError

    def _build_keypoints(self, landmarks, width: int, height: int, confidence: Confidence) -> KeypointCollection:
        """Converte os 21 landmarks normalizados [0,1] para KeypointCollection em píxeis."""
        raise NotImplementedError

    @staticmethod
    def _to_pixel_point(landmark, width: int, height: int) -> Point:
        raise NotImplementedError

    def _compute_bounding_box(self, keypoints: KeypointCollection, width: int, height: int) -> BoundingBox:
        """Calcula a bounding box a partir dos extremos dos landmarks, com margem.

        A Tasks API não devolve bounding box — é calculada aqui a partir dos
        landmarks mínimos e máximos, com _BOUNDING_BOX_MARGIN_PX de padding.
        """
        raise NotImplementedError

    @staticmethod
    def _extract_coords(keypoints: KeypointCollection) -> tuple[list[int], list[int]]:
        """Devolve (lista_x, lista_y) com as coordenadas em píxeis de todos os keypoints."""
        raise NotImplementedError

    @staticmethod
    def _clamp_range(values: list[int], frame_max: int) -> tuple[int, int]:
        """Aplica margem e limita ao intervalo [0, frame_max-1].

        Recebe: lista de coordenadas inteiras, dimensão máxima do frame.
        Devolve: (min_com_margem, max_com_margem) clampado ao frame.
        """
        raise NotImplementedError

    def release(self) -> None:
        raise NotImplementedError
