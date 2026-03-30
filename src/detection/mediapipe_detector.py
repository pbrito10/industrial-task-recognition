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

# Margem em píxeis adicionada à bounding box para não cortar a mão nas bordas
_BOUNDING_BOX_MARGIN = 10

# Mapeamento direto do label da Tasks API para o enum — evita if/else e facilita extensão
_HAND_SIDE_MAP: dict[str, HandSide] = {
    "Left": HandSide.LEFT,
    "Right": HandSide.RIGHT,
}


class MediapipeDetector(DetectorInterface):
    """Detector de mãos baseado na MediaPipe Tasks API (HandLandmarker).

    Usa o modo VIDEO para processamento frame-a-frame síncrono com timestamps
    crescentes — adequado para um pipeline de câmara em tempo real.

    Converte os landmarks normalizados (0.0–1.0) para píxeis e encapsula-os
    nos value objects do sistema.
    """

    def __init__(
        self,
        model_path: str,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.7,
    ) -> None:
        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            # presence_confidence controla se a mão "persiste" entre frames no tracking
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = mp_vision.HandLandmarker.create_from_options(options)

    def detect(self, frame: np.ndarray) -> list[HandDetection]:
        """Processa um frame RGB e devolve as mãos detetadas.

        Recebe o frame já em RGB — a conversão BGR→RGB é feita no processo
        da câmara (camera.py) antes de entrar na queue.

        VIDEO mode exige timestamps em ms monotonicamente crescentes —
        usamos time.monotonic() para garantir isso independentemente do relógio do sistema.
        """
        height, width = frame.shape[:2]

        # Tasks API exige imagem RGB — o frame já chega nesse formato
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

        timestamp_ms = int(time.monotonic() * 1000)
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.hand_landmarks:
            return []

        return [
            self._build_detection(landmarks, handedness, width, height)
            for landmarks, handedness in zip(result.hand_landmarks, result.handedness)
        ]

    def _build_detection(
        self,
        landmarks,
        handedness,
        width: int,
        height: int,
    ) -> HandDetection:
        """Converte os dados crus da Tasks API num HandDetection."""
        # handedness é uma lista de Category; o primeiro é sempre o mais provável
        category = handedness[0]
        confidence = Confidence(value=round(category.score, 4))

        keypoints = self._build_keypoints(landmarks, width, height, confidence)
        bounding_box = self._compute_bounding_box(keypoints, width, height)
        hand_side = _HAND_SIDE_MAP[category.category_name]

        return HandDetection(
            keypoints=keypoints,
            bounding_box=bounding_box,
            confidence=confidence,
            hand_side=hand_side,
        )

    def _build_keypoints(
        self,
        landmarks,
        width: int,
        height: int,
        confidence: Confidence,
    ) -> KeypointCollection:
        """Converte os 21 landmarks normalizados em Keypoints com coordenadas em píxeis."""
        # Tasks API não devolve confiança por landmark — usamos a confiança global
        keypoint_list = [
            Keypoint(
                index=index,
                position=self._to_pixel_point(landmark, width, height),
                confidence=confidence,
            )
            for index, landmark in enumerate(landmarks)
        ]
        return KeypointCollection(keypoint_list)

    @staticmethod
    def _to_pixel_point(landmark, width: int, height: int) -> Point:
        """Converte um landmark normalizado (0.0–1.0) para coordenadas em píxeis."""
        return Point(x=int(landmark.x * width), y=int(landmark.y * height))

    def _compute_bounding_box(
        self,
        keypoints: KeypointCollection,
        width: int,
        height: int,
    ) -> BoundingBox:
        """Calcula a bounding box a partir dos extremos dos 21 landmarks.

        A Tasks API não devolve bbox — derivamos do min/max dos pontos.
        """
        x_coords, y_coords = self._extract_coords(keypoints)
        min_x, max_x = self._clamp_range(x_coords, width)
        min_y, max_y = self._clamp_range(y_coords, height)
        return BoundingBox(
            top_left=Point(x=min_x, y=min_y),
            bottom_right=Point(x=max_x, y=max_y),
        )

    @staticmethod
    def _extract_coords(keypoints: KeypointCollection) -> tuple[list[int], list[int]]:
        """Separa as coordenadas x e y de todos os landmarks."""
        all_kp = keypoints.all()
        return [kp.position.x for kp in all_kp], [kp.position.y for kp in all_kp]

    @staticmethod
    def _clamp_range(values: list[int], frame_max: int) -> tuple[int, int]:
        """Aplica margem e clamp para não ultrapassar os limites do frame."""
        return (
            max(0, min(values) - _BOUNDING_BOX_MARGIN),
            min(frame_max - 1, max(values) + _BOUNDING_BOX_MARGIN),
        )

    def release(self) -> None:
        """Fecha o HandLandmarker e liberta os recursos."""
        self._landmarker.close()
