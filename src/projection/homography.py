"""Persistência e aplicação da homografia câmara → projetor.

A homografia H é calculada uma vez durante a calibração e guardada em JSON.
Em runtime, é usada para transformar as coordenadas dos ROIs (espaço câmara)
para coordenadas do projetor, permitindo iluminar a zona correta na bancada.
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from src.roi.region_of_interest import RegionOfInterest

_KEY_MATRIX = "homography_matrix"


def load(path: Path) -> np.ndarray | None:
    """Carrega H de JSON. Devolve None se o ficheiro não existir."""
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    return np.array(data[_KEY_MATRIX], dtype=np.float64)


def save(path: Path, H: np.ndarray) -> None:
    """Guarda H em JSON, criando o diretório se necessário."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({_KEY_MATRIX: H.tolist()}, f, indent=2)


def transform_roi(roi: RegionOfInterest, H: np.ndarray) -> tuple[tuple[int, int], tuple[int, int]]:
    """Transforma os dois cantos opostos de um ROI para coordenadas do projetor.

    Devolve (top_left, bottom_right) em píxeis do projetor.
    Usa perspectiveTransform, que lida corretamente com a projeção homogénea.
    """
    pts = np.array(
        [[roi.top_left.x, roi.top_left.y],
         [roi.bottom_right.x, roi.bottom_right.y]],
        dtype=np.float64,
    ).reshape(-1, 1, 2)

    transformed = cv2.perspectiveTransform(pts, H)

    tl = transformed[0][0]
    br = transformed[1][0]
    return (int(tl[0]), int(tl[1])), (int(br[0]), int(br[1]))
