from __future__ import annotations

import json
from pathlib import Path

from src.roi.region_of_interest import RegionOfInterest
from src.roi.roi_collection import RoiCollection
from src.roi.roi_repository import RoiRepository


class JsonRoiRepository(RoiRepository):
    """Persiste ROIs em config/rois.json.

    Formato: lista de dicts com name, x1, y1, x2, y2.
    Se o ficheiro não existir, load() devolve collection vazia.
    """

    def __init__(self, path: Path) -> None:
        raise NotImplementedError

    def save(self, collection: RoiCollection) -> None:
        """Serializa e escreve todas as zonas com indentação legível."""
        raise NotImplementedError

    def load(self) -> RoiCollection:
        """Carrega zonas do ficheiro. Devolve vazio se o ficheiro não existir."""
        raise NotImplementedError
