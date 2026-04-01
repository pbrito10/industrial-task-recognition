from __future__ import annotations

# Ferramenta interativa para desenhar ROIs sobre o feed da câmera.
#
# Controlos: 1-9 selecionar zona | Del apagar | s guardar | q sair
#
# O estado da sessão está dividido em dois objetos:
#   _rois     — os dados (zonas desenhadas)
#   _session  — o estado de interação (zona selecionada, drag, avisos)
# Esta separação facilita raciocinar sobre o que muda e quando.

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

import cv2
import numpy as np

from src.roi.region_of_interest import RegionOfInterest
from src.roi.roi_collection import RoiCollection
from src.shared.point import Point
from src.video import frame_annotator
from src.video.camera import Camera

_WINDOW_NAME    = "Definir ROIs  |  1-7 zona  |  Del apagar  |  s guardar  |  q sair"
_MIN_ROI_PIXELS = 15
_FONT           = cv2.FONT_HERSHEY_SIMPLEX

_DELETE_KEYS = {127, 255, 65535}


class _Signal(Enum):
    CONTINUE = "continue"
    SAVE     = "save"
    QUIT     = "quit"


@dataclass(frozen=True)
class _IdleState:
    """Sem drag em curso. Pode ter um aviso pendente (zona em falta, etc.)."""
    warning: str | None = None


@dataclass(frozen=True)
class _DrawingState:
    """Drag ativo — o utilizador está a desenhar um retângulo a partir de `start`."""
    start: Point


_DragState = _IdleState | _DrawingState


@dataclass
class _ZoneSelection:
    names: list[str]
    index: int | None = None


@dataclass
class _MouseState:
    position: Point | None = None
    drag: _DragState = field(default_factory=_IdleState)


@dataclass
class _SessionState:
    selection: _ZoneSelection
    mouse: _MouseState = field(default_factory=_MouseState)


def _compute_drawing_roi(name: str, start: Point, end: Point) -> RegionOfInterest:
    """Normaliza os dois pontos do drag para top-left/bottom-right corretos."""
    return RegionOfInterest(
        name=name,
        top_left=Point(x=min(start.x, end.x), y=min(start.y, end.y)),
        bottom_right=Point(x=max(start.x, end.x), y=max(start.y, end.y)),
    )


def _has_minimum_size(roi: RegionOfInterest) -> bool:
    return (
        roi.bottom_right.x - roi.top_left.x >= _MIN_ROI_PIXELS
        and roi.bottom_right.y - roi.top_left.y >= _MIN_ROI_PIXELS
    )


def _draw_preview(frame: np.ndarray, session: _SessionState) -> None:
    """Retângulo a tracejado enquanto o drag está em curso."""
    current = session.mouse.position
    drag    = session.mouse.drag

    if current is None or not isinstance(drag, _DrawingState):
        return

    roi   = _compute_drawing_roi("preview", drag.start, current)
    color = frame_annotator.zone_color(
        session.selection.names[session.selection.index],
    )
    cv2.rectangle(
        frame,
        (roi.top_left.x, roi.top_left.y),
        (roi.bottom_right.x, roi.bottom_right.y),
        color, 2,
    )


def _draw_ui_overlay(frame: np.ndarray, session: _SessionState) -> None:
    if session.selection.index is not None:
        zone  = session.selection.names[session.selection.index]
        color = frame_annotator.zone_color(zone)
        cv2.putText(frame, f"Zona: {zone}", (10, 30), _FONT, 0.8, color, 2)

    warning = None
    if isinstance(session.mouse.drag, _IdleState):
        warning = session.mouse.drag.warning
    if warning:
        h = frame.shape[0]
        cv2.putText(frame, warning, (10, h - 15), _FONT, 0.6, (0, 0, 255), 2)


def _render(frame: np.ndarray, rois: RoiCollection, session: _SessionState) -> None:
    selected_name = None
    if session.selection.index is not None:
        selected_name = session.selection.names[session.selection.index]

    frame_annotator.draw_rois(frame, rois, selected_name=selected_name)
    _draw_preview(frame, session)
    _draw_ui_overlay(frame, session)


class _DrawingSession:
    """Gere estado e interação da sessão de desenho."""

    def __init__(self, zone_names: list[str], rois: RoiCollection) -> None:
        self._rois    = rois
        self._session = _SessionState(selection=_ZoneSelection(names=zone_names))

    @property
    def rois(self) -> RoiCollection:
        return self._rois

    def render(self, frame: np.ndarray) -> None:
        _render(frame, self._rois, self._session)

    def handle_mouse(self, event: int, x: int, y: int, flags: int, param) -> None:
        point = Point(x=x, y=y)
        self._session.mouse.position = point

        handlers = {
            cv2.EVENT_LBUTTONDOWN: self._on_mouse_down,
            cv2.EVENT_LBUTTONUP:   self._on_mouse_up,
        }
        handler = handlers.get(event)
        if handler is not None:
            handler(point)

    def handle_key(self, key: int) -> _Signal:
        if key == ord('q'):
            return _Signal.QUIT
        if key == ord('s'):
            return self._try_save()
        if key in _DELETE_KEYS:
            self._delete_selected()
            return _Signal.CONTINUE
        if ord('1') <= key <= ord('9'):
            self._select_zone(key - ord('1'))
            return _Signal.CONTINUE
        return _Signal.CONTINUE

    def _on_mouse_down(self, point: Point) -> None:
        if self._session.selection.index is None:
            return
        self._session.mouse.drag = _DrawingState(start=point)

    def _on_mouse_up(self, point: Point) -> None:
        if not isinstance(self._session.mouse.drag, _DrawingState):
            return
        self._finish_drawing(point)

    def _finish_drawing(self, point: Point) -> None:
        drag      = self._session.mouse.drag
        zone_name = self._selected_zone_name()
        if zone_name is None or not isinstance(drag, _DrawingState):
            self._to_idle()
            return
        roi = _compute_drawing_roi(zone_name, drag.start, point)
        if _has_minimum_size(roi):
            self._rois.add(roi)
        self._to_idle()

    def _select_zone(self, index: int) -> None:
        if index >= len(self._session.selection.names):
            return
        self._session.selection.index = index
        self._to_idle()

    def _delete_selected(self) -> None:
        name = self._selected_zone_name()
        if name is None:
            return
        self._rois.remove(name)
        self._to_idle()

    def _try_save(self) -> _Signal:
        missing = self._missing_zones()
        if missing:
            self._session.mouse.drag = _IdleState(warning=f"Faltam: {', '.join(missing)}")
            return _Signal.CONTINUE
        return _Signal.SAVE

    def _missing_zones(self) -> list[str]:
        return [
            name for name in self._session.selection.names
            if not self._rois.contains(name)
        ]

    def _selected_zone_name(self) -> str | None:
        index = self._session.selection.index
        if index is None:
            return None
        return self._session.selection.names[index]

    def _to_idle(self) -> None:
        self._session.mouse.drag = _IdleState()


class RoiDrawer:
    """Abre a câmera e permite definir ROIs interativamente.

    Devolve a RoiCollection atualizada ao guardar, ou None se o utilizador
    sair sem guardar (ROIs anteriores são mantidas pelo chamador).
    """

    def __init__(
        self,
        camera_factory: Callable[[], Camera],
        zone_names: list[str],
    ) -> None:
        self._camera_factory = camera_factory
        self._zone_names     = zone_names

    def draw(self, initial_rois: RoiCollection) -> RoiCollection | None:
        camera  = self._camera_factory()
        session = _DrawingSession(self._zone_names, initial_rois)

        cv2.namedWindow(_WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(_WINDOW_NAME, session.handle_mouse)

        try:
            return self._run_loop(camera, session)
        finally:
            camera.release()
            cv2.destroyAllWindows()
            cv2.waitKey(1)  # flush de eventos X11 pendentes antes de sair

    def _run_loop(self, camera: Camera, session: _DrawingSession) -> RoiCollection | None:
        while True:
            frame = camera.read_frame()
            if frame is None:
                return None

            frame = cv2.flip(frame, -1)
            session.render(frame)

            cv2.imshow(_WINDOW_NAME, frame)

            signal = session.handle_key(cv2.waitKey(1))
            if signal == _Signal.QUIT:
                return None
            if signal == _Signal.SAVE:
                return session.rois
